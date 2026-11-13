#!/usr/bin/env bash
# Verify a built core image: dependency minimums and the real health command.
# Usage: scripts/check_image.sh [image]   (default: bb10-gateway-core:latest)
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
IMAGE=${1:-bb10-gateway-core:latest}

docker run --rm -i --network none --entrypoint python3 "$IMAGE" - <<'PY'
import aiohttp
import PIL


def ver(v):
    return tuple(int(p) for p in v.split(".")[:2])


assert ver(aiohttp.__version__) >= (3, 9), aiohttp.__version__
assert ver(PIL.__version__) >= (10, 0), PIL.__version__
print("deps ok: aiohttp", aiohttp.__version__, "pillow", PIL.__version__)
PY

probe() {
    local name=$1 port=$2
    shift 2
    local cid
    cid=$(docker run -d --network none "$@" "$IMAGE")
    trap 'docker rm -f "$cid" >/dev/null 2>&1 || true' RETURN
    for _ in $(seq 1 40); do
        sleep 1
        if docker exec "$cid" python3 /app/healthcheck.py >/dev/null 2>&1; then
            echo "health ok: $name (port $port)"
            return 0
        fi
    done
    echo "health FAILED: $name" >&2
    docker logs "$cid" 2>&1 | tail -20 >&2
    return 1
}
probe example 2443 -e PRESET=example
probe x-default 2444 -e PRESET=x
probe port-override 3999 -e PRESET=example -e PORT=3999
