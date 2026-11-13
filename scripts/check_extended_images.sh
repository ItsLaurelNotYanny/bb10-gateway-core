#!/usr/bin/env bash
# Verify built extended images (bb10-term, bb10-wechat):
# - uid/gid matching expectations
# - gateway health endpoint (/healthz)
# - application runtime readiness (xterm+tmux for term, wechat process+window for wechat)
# Usage: scripts/check_extended_images.sh [term_image] [wechat_image]
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."

if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: docker command not found" >&2
    exit 2
fi

TERM_IMAGE=${1:-bb10-term:latest}
WECHAT_IMAGE=${2:-bb10-wechat:latest}

PRESETS_DIR="$PWD/tests/presets.d"
if [ -d "$PWD/private/presets.d" ]; then
    PRESETS_DIR="$PWD/private/presets.d"
fi

check_term_runtime() {
    local cid=$1
    docker exec "$cid" pgrep -x xterm >/dev/null 2>&1 && \
    docker exec "$cid" tmux has-session -t bb10 >/dev/null 2>&1
}

check_wechat_runtime() {
    local cid=$1
    docker exec "$cid" pgrep -f '/opt/wechat/wechat' >/dev/null 2>&1 && \
    docker exec "$cid" env DISPLAY=:99 wmctrl -l 2>/dev/null | grep -qiE 'weixin|wechat'
}

probe_extended() {
    local name=$1 image=$2 port=$3 expected_id=$4 runtime_check_fn=$5
    shift 5

    if ! docker image inspect "$image" >/dev/null 2>&1; then
        echo "ERROR: required image '$image' is not available or Docker inspect failed" >&2
        return 1
    fi

    local cid
    cid=$(docker run -d --network none -e "PRESET=$name" -v "$PRESETS_DIR:/app/presets.d:ro" "$@" "$image")
    trap 'docker rm -f "$cid" >/dev/null 2>&1 || true' RETURN

    local actual_id
    actual_id=$(docker exec "$cid" id 2>/dev/null || echo "")
    if [[ "$actual_id" != *"$expected_id"* ]]; then
        echo "FAIL: $name expected id to contain '$expected_id', got '$actual_id'" >&2
        return 1
    fi

    local saw_gateway_ok=0
    local saw_app_ok=0
    for _ in $(seq 1 40); do
        sleep 1
        local current_gateway_ok=0
        local current_app_ok=0

        if docker exec "$cid" python3 /app/healthcheck.py >/dev/null 2>&1; then
            current_gateway_ok=1
            saw_gateway_ok=1
        fi
        if "$runtime_check_fn" "$cid"; then
            current_app_ok=1
            saw_app_ok=1
        fi

        if [ "$current_gateway_ok" -eq 1 ] && [ "$current_app_ok" -eq 1 ]; then
            echo "health ok: $name ($image on port $port, id matches '$expected_id', runtime ready)"
            return 0
        fi
    done

    if [ "$saw_gateway_ok" -eq 0 ]; then
        echo "FAIL: $name gateway health probe failed on port $port" >&2
    fi
    if [ "$saw_app_ok" -eq 0 ]; then
        echo "FAIL: $name application runtime readiness check failed" >&2
    fi
    if [ "$saw_gateway_ok" -eq 1 ] && [ "$saw_app_ok" -eq 1 ]; then
        echo "FAIL: $name gateway and application runtime were never ready in the same poll iteration" >&2
    fi
    docker logs "$cid" 2>&1 | tail -20 >&2
    return 1
}

probe_extended term "$TERM_IMAGE" 2445 "uid=1000(appuser) gid=1000(appuser)" check_term_runtime
probe_extended wechat "$WECHAT_IMAGE" 2446 "uid=1000(appuser) gid=100(users)" check_wechat_runtime
