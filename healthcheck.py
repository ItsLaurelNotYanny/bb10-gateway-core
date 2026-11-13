"""Container health probe: query /healthz on the port resolved by load_preset()."""

from __future__ import annotations

import os
import ssl
import sys
import urllib.request
from collections.abc import Mapping
from pathlib import Path

from presets import load_preset


def health_url(env: Mapping[str, str] | None = None) -> str:
    """Return the /healthz URL matching how gateway.py serves (TLS only with cert and key)."""
    source = os.environ if env is None else env
    # Pass the original env (None = ambient) so the loader resolves presets exactly as gateway.py.
    port = load_preset(env=env).port
    cert = Path(source.get("CERT_FILE", "/certs/server.crt"))
    key = Path(source.get("KEY_FILE", "/certs/server.key"))
    tls = source.get("DISABLE_TLS", "0") != "1" and cert.is_file() and key.is_file()
    return f"{'https' if tls else 'http'}://127.0.0.1:{port}/healthz"


def main() -> int:
    url = health_url()
    context = ssl._create_unverified_context() if url.startswith("https") else None
    try:
        with urllib.request.urlopen(url, timeout=4, context=context) as resp:  # noqa: S310
            return 0 if resp.status == 200 else 1
    except Exception as exc:
        print(f"unhealthy: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
