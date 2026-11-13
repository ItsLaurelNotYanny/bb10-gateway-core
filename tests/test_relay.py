"""Unit tests for contrib/relay/tcp_relay.py including TLS first-packet handshake shield."""

from __future__ import annotations

import asyncio
import os
import subprocess
from pathlib import Path

import pytest

from contrib.relay.tcp_relay import TcpRelay, is_tls_client_hello, parse_mappings


def test_is_tls_client_hello() -> None:
    # Valid TLS 1.0, 1.1, 1.2, 1.3 ClientHello record headers
    assert is_tls_client_hello(b"\x16\x03\x01\x02\x00\x01") is True
    assert is_tls_client_hello(b"\x16\x03\x03\x00\xa5\x01") is True
    # Invalid / scanner payloads (HTTP, SSH, empty, short)
    assert is_tls_client_hello(b"GET / HTTP/1.1\r\n") is False
    assert is_tls_client_hello(b"SSH-2.0-OpenSSH\r\n") is False
    assert is_tls_client_hello(b"\x16\x03") is False
    assert is_tls_client_hello(b"") is False


def test_parse_mappings_multi_target() -> None:
    mappings = parse_mappings(
        "2993:2993,2445:198.51.100.2:2445,2446",
        bind_host="127.0.0.1",
        default_target="198.51.100.1",
    )
    assert mappings == [
        ("127.0.0.1", 2993, "198.51.100.1", 2993),
        ("127.0.0.1", 2445, "198.51.100.2", 2445),
        ("127.0.0.1", 2446, "198.51.100.1", 2446),
    ]

    with pytest.raises(ValueError):
        parse_mappings("invalid:a:b:c")


def test_tcp_relay_tls_guard_blocks_scanners_and_passes_tls() -> None:
    async def run_scenario() -> None:
        upstream_hits = 0

        async def handle_upstream(
            reader: asyncio.StreamReader, writer: asyncio.StreamWriter
        ) -> None:
            nonlocal upstream_hits
            upstream_hits += 1
            data = await reader.read(1024)
            writer.write(b"ACK:" + data)
            await writer.drain()
            writer.close()
            await writer.wait_closed()

        up_srv = await asyncio.start_server(handle_upstream, "127.0.0.1", 0)
        up_port = up_srv.sockets[0].getsockname()[1]

        relay = TcpRelay(
            target_host="127.0.0.1",
            mappings=[("127.0.0.1", 0, "127.0.0.1", up_port)],
            tls_guard=True,
            first_packet_timeout=0.5,
        )
        await relay.start()
        relay_port = relay.servers[0].sockets[0].getsockname()[1]

        try:
            # 1. Plain HTTP scanner -> blocked at VPS relay, 0 hits on upstream!
            r1, w1 = await asyncio.open_connection("127.0.0.1", relay_port)
            w1.write(b"GET / HTTP/1.1\r\nHost: scanner\r\n\r\n")
            await w1.drain()
            resp1 = await r1.read(1024)
            assert resp1 == b""
            w1.close()
            assert upstream_hits == 0

            # 2. Valid TLS ClientHello -> forwarded to upstream!
            r2, w2 = await asyncio.open_connection("127.0.0.1", relay_port)
            tls_hello = b"\x16\x03\x03\x00\x05HELLO"
            w2.write(tls_hello)
            await w2.drain()
            resp2 = await asyncio.wait_for(r2.read(1024), timeout=2.0)
            assert resp2 == b"ACK:" + tls_hello
            w2.close()
            assert upstream_hits == 1
        finally:
            await relay.stop()
            up_srv.close()
            await up_srv.wait_closed()

    asyncio.run(run_scenario())


def test_deploy_vps_relay_preserves_multiple_services_across_ssh(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    key_file = tmp_path / "fake.key"
    key_file.touch()

    # Fake ssh interceptor to capture the remote bash command arguments
    fake_ssh = tmp_path / "ssh"
    fake_ssh.write_text(
        """#!/usr/bin/env python3
import json, subprocess, sys
args = sys.argv[1:]
# Find the remote command arguments after the target host
idx = -1
for i, arg in enumerate(args):
    if "@" in arg:
        idx = i
        break
command = " ".join(args[idx + 1:])
# Intercept remote script preamble before sudo installation
body = sys.stdin.read().split("# 1.", 1)[0]
body += "\\nprintf 'SERVICES=%s\\\\n' \\"$SERVICES\\"\\n"
p = subprocess.run(["bash", "-c", command], input=body, capture_output=True, text=True)
print(p.stdout.strip())
sys.exit(p.returncode)
"""
    )
    fake_ssh.chmod(0o755)

    fake_scp = tmp_path / "scp"
    fake_scp.write_text("#!/bin/sh\nexit 0\n")
    fake_scp.chmod(0o755)

    services = "app1:2443:upstream1.example:2443 app2:2444:upstream2.example:2444"
    env = dict(
        os.environ,
        PATH=f"{tmp_path}:{os.environ['PATH']}",
        VPS_HOST="198.51.100.254",
        VPS_USER="testuser",
        SSH_KEY=str(key_file),
        RELAY_SERVICES=services,
    )
    res = subprocess.run(
        ["bash", str(repo_root / "contrib/relay/deploy_vps_relay.sh")],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert f"SERVICES={services}" in res.stdout
