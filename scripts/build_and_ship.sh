#!/usr/bin/env bash
# Build container images locally and ship to a remote destination host (e.g. NAS).
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."

LOAD_ENV=1
for arg in "$@"; do
    if [ "$arg" = "--no-env" ]; then
        LOAD_ENV=0
        break
    fi
done

# Source optional deployment environment if present
if [ "$LOAD_ENV" -eq 1 ] && [ -f "private/deploy.env" ]; then
    # shellcheck disable=SC1091
    source "private/deploy.env"
fi

LOCAL_TAR=""
cleanup_local_tar() {
    local rc=$?
    if [ -n "${LOCAL_TAR:-}" ] && [ -f "$LOCAL_TAR" ]; then
        rm -f "$LOCAL_TAR"
        LOCAL_TAR=""
    fi
    exit "$rc"
}
trap cleanup_local_tar EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

DEPLOY_HOST="${DEPLOY_HOST:-${NAS_HOST:-}}"
DEPLOY_USER="${DEPLOY_USER:-${NAS_USER:-}}"
REMOTE_STAGING_DIR="${REMOTE_STAGING_DIR:-/tmp}"
SKIP_BUILD=0
DRY_RUN=0
NO_LOAD=0
SHIP_MODE="auto" # auto, direct, stage
IMAGES=()

usage() {
    cat <<'EOF'
Usage: ./scripts/build_and_ship.sh [options] [image...]

Build images locally and ship them to a remote target host via SSH.

Options:
  --host <host>        Target host IP or hostname (or env DEPLOY_HOST / NAS_HOST)
  --user <user>        Remote SSH username (or env DEPLOY_USER / NAS_USER)
  --image <name>       Image name to build and ship (repeatable)
  --all                Ship core image and all available extended images
  --skip-build         Skip docker build; ship existing local image(s) only
  --no-load            Transfer image tar to remote host without invoking docker load (takes precedence over --direct)
  --direct             Force direct streaming: docker save | ssh docker load (ignored when --no-load is set)
  --stage              Force file staging: save tar, copy via scp, load remotely
  --remote-dir <dir>   Remote staging directory for tar transfers (default: /tmp)
  --dry-run            Print commands without executing them
  -h, --help           Show this help message and exit

Examples:
  ./scripts/build_and_ship.sh --host <HOST_IP>
  ./scripts/build_and_ship.sh --host nas.example.org --user admin --all
  ./scripts/build_and_ship.sh --host nas.example.org --image bb10-gateway-core:latest --direct
EOF
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --host)
            [ "$#" -ge 2 ] || { echo "ERROR: --host requires an argument" >&2; exit 2; }
            DEPLOY_HOST="$2"; shift 2 ;;
        --user)
            [ "$#" -ge 2 ] || { echo "ERROR: --user requires an argument" >&2; exit 2; }
            DEPLOY_USER="$2"; shift 2 ;;
        --image)
            [ "$#" -ge 2 ] || { echo "ERROR: --image requires an argument" >&2; exit 2; }
            IMAGES+=("$2"); shift 2 ;;
        --all)
            IMAGES=("bb10-gateway-core:latest")
            if [ -f "private/extended/wechat/Dockerfile" ]; then
                IMAGES+=("bb10-wechat:latest")
            fi
            if [ -f "private/extended/term/Dockerfile" ]; then
                IMAGES+=("bb10-term:latest")
            fi
            shift ;;
        --skip-build)
            SKIP_BUILD=1; shift ;;
        --no-load)
            NO_LOAD=1; shift ;;
        --no-env)
            LOAD_ENV=0; shift ;;
        --direct)
            SHIP_MODE="direct"; shift ;;
        --stage)
            SHIP_MODE="stage"; shift ;;
        --remote-dir)
            [ "$#" -ge 2 ] || { echo "ERROR: --remote-dir requires an argument" >&2; exit 2; }
            REMOTE_STAGING_DIR="$2"; shift 2 ;;
        --dry-run)
            DRY_RUN=1; shift ;;
        -h|--help)
            usage; exit 0 ;;
        --)
            shift; while [ "$#" -gt 0 ]; do IMAGES+=("$1"); shift; done; break ;;
        -*)
            echo "ERROR: unknown option: $1" >&2; usage >&2; exit 2 ;;
        *)
            IMAGES+=("$1"); shift ;;
    esac
done

if [ -z "$DEPLOY_HOST" ]; then
    echo "ERROR: target host is required (pass --host <host> or set DEPLOY_HOST / NAS_HOST)" >&2
    exit 2
fi

if [ "${#IMAGES[@]}" -eq 0 ]; then
    IMAGES=("bb10-gateway-core:latest")
fi

REMOTE_TARGET="${DEPLOY_HOST}"
if [ -n "$DEPLOY_USER" ]; then
    REMOTE_TARGET="${DEPLOY_USER}@${DEPLOY_HOST}"
fi

# Build images
for img in "${IMAGES[@]}"; do
    if [ "$SKIP_BUILD" -eq 1 ]; then
        echo "Skipping build for $img (--skip-build)"
        continue
    fi

    echo "=== Building $img ==="
    case "$img" in
        bb10-gateway-core|bb10-gateway-core:latest)
            BUILD_CMD=(docker build -t bb10-gateway-core:latest .)
            ;;
        bb10-wechat|bb10-wechat:latest)
            BUILD_CMD=(docker build -t bb10-wechat:latest -f private/extended/wechat/Dockerfile private/extended/wechat)
            ;;
        bb10-term|bb10-term:latest)
            BUILD_CMD=(docker build -t bb10-term:latest -f private/extended/term/Dockerfile private/extended/term)
            ;;
        *)
            echo "Custom image $img: verifying existence..."
            BUILD_CMD=()
            ;;
    esac

    if [ "${#BUILD_CMD[@]}" -gt 0 ]; then
        if [ "$DRY_RUN" -eq 1 ]; then
            printf '[dry-run] %s\n' "${BUILD_CMD[*]}"
        else
            "${BUILD_CMD[@]}"
        fi
    elif [ "$DRY_RUN" -eq 0 ]; then
        if ! docker image inspect "$img" >/dev/null 2>&1; then
            echo "ERROR: image $img not found locally and no Dockerfile known" >&2
            exit 1
        fi
    fi
done

# Detect remote execution mode
HAS_DIRECT_DOCKER=0
REMOTE_DOCKER_BIN="docker"

if [ "$NO_LOAD" -eq 1 ]; then
    if [ "$SHIP_MODE" = "direct" ]; then
        echo "Notice: --no-load takes precedence over --direct; using staging mode for transfer without remote docker load." >&2
    fi
    USE_DIRECT=0
else
    if [ "$DRY_RUN" -eq 0 ] && [ "$SHIP_MODE" != "stage" ]; then
        if ssh -o BatchMode=yes "$REMOTE_TARGET" "command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1" 2>/dev/null; then
            HAS_DIRECT_DOCKER=1
            REMOTE_DOCKER_BIN="docker"
        elif ssh -o BatchMode=yes "$REMOTE_TARGET" "sudo -n docker info >/dev/null 2>&1" 2>/dev/null; then
            HAS_DIRECT_DOCKER=1
            REMOTE_DOCKER_BIN="sudo docker"
        elif ssh -o BatchMode=yes "$REMOTE_TARGET" "sudo -n /usr/local/bin/docker info >/dev/null 2>&1" 2>/dev/null; then
            HAS_DIRECT_DOCKER=1
            REMOTE_DOCKER_BIN="sudo /usr/local/bin/docker"
        fi
    fi

    USE_DIRECT=0
    if [ "$SHIP_MODE" = "direct" ]; then
        USE_DIRECT=1
    elif [ "$SHIP_MODE" = "auto" ] && [ "$HAS_DIRECT_DOCKER" -eq 1 ]; then
        USE_DIRECT=1
    fi
fi

# Ship images
for img in "${IMAGES[@]}"; do
    echo "=== Shipping $img to $REMOTE_TARGET ==="
    if [ "$USE_DIRECT" -eq 1 ]; then
        if [ "$DRY_RUN" -eq 1 ]; then
            printf '[dry-run] docker save %s | ssh %s "%s load"\n' "$img" "$REMOTE_TARGET" "$REMOTE_DOCKER_BIN"
        else
            echo "Direct streaming: docker save $img | ssh $REMOTE_TARGET '$REMOTE_DOCKER_BIN load'..."
            docker save "$img" | ssh "$REMOTE_TARGET" "$REMOTE_DOCKER_BIN load"
            echo "Successfully loaded $img on $REMOTE_TARGET"
        fi
    else
        # Staging mode: save tar, scp, and load
        SAFE_NAME=$(echo "$img" | tr '/:' '_')
        REMOTE_FILE="${REMOTE_STAGING_DIR}/${SAFE_NAME}.tar"
        if [ "$DRY_RUN" -eq 1 ]; then
            printf '[dry-run] docker save %s -o /tmp/%s.tar\n' "$img" "$SAFE_NAME"
            printf '[dry-run] scp -O /tmp/%s.tar %s:%s\n' "$SAFE_NAME" "$REMOTE_TARGET" "$REMOTE_FILE"
            if [ "$NO_LOAD" -eq 0 ]; then
                printf '[dry-run] ssh -t %s "sudo /usr/local/bin/docker load -i %s && rm -f %s"\n' "$REMOTE_TARGET" "$REMOTE_FILE" "$REMOTE_FILE"
            else
                printf '[dry-run] (transfer-only) Suggested manual import: ssh -t %s "sudo /usr/local/bin/docker load -i %s && rm -f %s"\n' "$REMOTE_TARGET" "$REMOTE_FILE" "$REMOTE_FILE"
            fi
        else
            LOCAL_TAR=$(mktemp "${TMPDIR:-/tmp}/bb10-ship-XXXXXX.tar")
            echo "Saving $img to temporary file..."
            docker save "$img" -o "$LOCAL_TAR"
            echo "Copying to $REMOTE_TARGET:$REMOTE_FILE..."
            if ! scp -O -q "$LOCAL_TAR" "$REMOTE_TARGET:$REMOTE_FILE" 2>/dev/null; then
                scp -q "$LOCAL_TAR" "$REMOTE_TARGET:$REMOTE_FILE"
            fi
            rm -f "$LOCAL_TAR"
            LOCAL_TAR=""
            echo "Image transferred to $REMOTE_TARGET:$REMOTE_FILE"
            if [ "$NO_LOAD" -eq 0 ] && [ -t 0 ] && [ -t 1 ]; then
                echo "Running docker load on $REMOTE_TARGET (sudo password may be required)..."
                ssh -t "$REMOTE_TARGET" "sudo /usr/local/bin/docker load -i '$REMOTE_FILE' && rm -f '$REMOTE_FILE'"
            else
                echo "To complete import on $REMOTE_TARGET, run:"
                echo "  ssh -t $REMOTE_TARGET \"sudo /usr/local/bin/docker load -i '$REMOTE_FILE' && rm -f '$REMOTE_FILE'\""
            fi
        fi
    fi
done

echo "=== All image shipping operations finished ==="
