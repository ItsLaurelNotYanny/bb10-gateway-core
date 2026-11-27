#!/usr/bin/env python3
"""
Hardened Stateless Layer-4 TCP Relay for BB10 Multi-Gateway Ecosystem (VPS -> Tailscale peers).

Security features:
1. Zero-Trust End-to-End TLS: Terminates zero TLS on VPS; private keys stay inside LAN.
2. TLS First-Packet Handshake Shield (Option B): Validates that incoming connections send a
   valid TLS ClientHello record header (0x16 0x03 0x00..0x04) within first_packet_timeout
   BEFORE opening any upstream Tailscale connection. Port scans, empty TCP probes, and plain
   HTTP/SSH scanners are dropped in VPS memory with 0 bytes reaching internal home nodes.
3. Per-IP Concurrency & Global Semaphore Protection: Prevents socket exhaustion.
"""

from __future__ import annotations

import argparse
import asyncio
import collections
import logging
import os
import signal
import socket
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
LOG = logging.getLogger("vps-relay")


def is_tls_client_hello(data: bytes) -> bool:
    """Return True if data begins with a valid TLS Handshake record header."""
    return len(data) >= 3 and data[0] == 0x16 and data[1] == 0x03 and 0x00 <= data[2] <= 0x04


def configure_keepalive(sock: socket.socket) -> None:
    """Enable TCP_NODELAY and OS-level TCP keepalive to detect dead mobile Wi-Fi peers."""
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    for opt_name, val in (("TCP_KEEPIDLE", 60), ("TCP_KEEPINTVL", 15), ("TCP_KEEPCNT", 4)):
        opt = getattr(socket, opt_name, None)
        if opt is not None:
            try:
                sock.setsockopt(socket.IPPROTO_TCP, opt, val)
            except OSError:
                pass


async def pipe_stream(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    idle_timeout: float,
) -> None:
    try:
        while True:
            chunk = await asyncio.wait_for(reader.read(32768), timeout=idle_timeout)
            if not chunk:
                break
            writer.write(chunk)
            await writer.drain()
    except (TimeoutError, ConnectionError, OSError):
        pass
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


class TcpRelay:
    """Stateless L4 TCP relay with optional TLS first-packet shield and per-IP limits."""

    def __init__(
        self,
        target_host: str = "",
        mappings: list[tuple[str, int, str, int]] | list[Any] | None = None,
        max_conns: int = 64,
        max_per_ip: int = 16,
        connect_timeout: float = 10.0,
        idle_timeout: float = 1800.0,
        tls_guard: bool = False,
        first_packet_timeout: float = 10.0,
    ) -> None:
        self.target_host = target_host
        self.mappings: list[Any] = mappings or []
        self.sem = asyncio.Semaphore(max_conns)
        self.max_per_ip = max_per_ip
        self.connect_timeout = connect_timeout
        self.idle_timeout = idle_timeout
        self.tls_guard = tls_guard
        self.first_packet_timeout = first_packet_timeout
        self.ip_counts: dict[str, int] = collections.defaultdict(int)
        self.servers: list[asyncio.AbstractServer] = []

    async def _handle_client(
        self,
        target_host: str,
        upstream_port: int,
        client_reader: asyncio.StreamReader,
        client_writer: asyncio.StreamWriter,
    ) -> None:
        peer = client_writer.get_extra_info("peername")
        peer_ip = peer[0] if peer else "unknown"

        if self.ip_counts[peer_ip] >= self.max_per_ip or self.sem.locked():
            LOG.warning("Dropping connection from %s (rate/concurrency limit)", peer_ip)
            client_writer.close()
            return

        self.ip_counts[peer_ip] += 1
        try:
            async with self.sem:
                csock = client_writer.get_extra_info("socket")
                if csock is not None:
                    configure_keepalive(csock)

                first_chunk = b""
                if self.tls_guard:
                    try:
                        first_chunk = await asyncio.wait_for(
                            client_reader.read(4096),
                            timeout=self.first_packet_timeout,
                        )
                    except (TimeoutError, ConnectionError, OSError):
                        first_chunk = b""

                    if not is_tls_client_hello(first_chunk):
                        LOG.warning(
                            "TLS shield blocked non-TLS/idle probe from %s (%d bytes)",
                            peer_ip,
                            len(first_chunk),
                        )
                        client_writer.close()
                        try:
                            await client_writer.wait_closed()
                        except Exception:
                            pass
                        return

                try:
                    up_reader, up_writer = await asyncio.wait_for(
                        asyncio.open_connection(target_host, upstream_port),
                        timeout=self.connect_timeout,
                    )
                except Exception as exc:
                    LOG.error(
                        "Upstream %s:%d unreachable for %s: %s",
                        target_host,
                        upstream_port,
                        peer_ip,
                        exc,
                    )
                    client_writer.close()
                    return

                usock = up_writer.get_extra_info("socket")
                if usock is not None:
                    configure_keepalive(usock)

                if first_chunk:
                    try:
                        up_writer.write(first_chunk)
                        await up_writer.drain()
                    except (ConnectionError, OSError):
                        up_writer.close()
                        client_writer.close()
                        return

                LOG.info("Relaying %s -> %s:%d", peer_ip, target_host, upstream_port)
                await asyncio.gather(
                    pipe_stream(client_reader, up_writer, self.idle_timeout),
                    pipe_stream(up_reader, client_writer, self.idle_timeout),
                )
        finally:
            self.ip_counts[peer_ip] -= 1
            if self.ip_counts[peer_ip] <= 0:
                self.ip_counts.pop(peer_ip, None)

    async def start(self) -> None:
        for mapping in self.mappings:
            if len(mapping) == 4:
                bind_host, listen_port, target_host, upstream_port = mapping
            else:
                bind_host, listen_port, upstream_port = mapping
                target_host = self.target_host
            srv = await asyncio.start_server(
                lambda r, w, th=target_host, up=upstream_port: self._handle_client(th, up, r, w),
                host=bind_host,
                port=listen_port,
                reuse_address=True,
            )
            self.servers.append(srv)
            LOG.info(
                "Listening on %s:%d -> %s:%d (tls_guard=%s)",
                bind_host,
                listen_port,
                target_host,
                upstream_port,
                self.tls_guard,
            )

    async def stop(self) -> None:
        for srv in self.servers:
            srv.close()
        for srv in self.servers:
            await srv.wait_closed()
        self.servers.clear()


def parse_mappings(
    spec: str,
    bind_host: str = "0.0.0.0",
    default_target: str = "",
) -> list[tuple[str, int, str, int]]:
    """Parse port mappings supporting both listen:upstream and listen:target_host:upstream."""
    result: list[tuple[str, int, str, int]] = []
    for item in spec.split(","):
        item = item.strip()
        if not item:
            continue
        parts = item.split(":")
        if len(parts) == 1:
            lp = int(parts[0])
            up = lp
            th = default_target
        elif len(parts) == 2:
            lp = int(parts[0])
            up = int(parts[1])
            th = default_target
        elif len(parts) == 3:
            lp = int(parts[0])
            th = parts[1].strip()
            up = int(parts[2])
        else:
            raise ValueError(f"Invalid port mapping format: {item}")

        if not (1 <= lp <= 65535 and 1 <= up <= 65535 and th):
            raise ValueError(f"Invalid port or host in mapping: {item}")
        result.append((bind_host, lp, th, up))
    if not result:
        raise ValueError("At least one port mapping is required")
    return result


async def run_forever(relay: TcpRelay) -> None:
    await relay.start()
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            pass
    await stop_event.wait()
    await relay.stop()


def main() -> int:
    parser = argparse.ArgumentParser(description="Hardened stateless TCP relay to Tailscale peers.")
    parser.add_argument("--bind", default=os.environ.get("BIND_HOST", "0.0.0.0"))
    parser.add_argument("--target", default=os.environ.get("TARGET_HOST", ""))
    parser.add_argument(
        "--listen",
        type=int,
        default=int(os.environ["LISTEN_PORT"]) if os.environ.get("LISTEN_PORT") else None,
        help="Single listen port for template systemd unit",
    )
    parser.add_argument(
        "--upstream",
        type=int,
        default=int(os.environ["UPSTREAM_PORT"]) if os.environ.get("UPSTREAM_PORT") else None,
        help="Single upstream port for template systemd unit",
    )
    parser.add_argument(
        "--tls-guard",
        action="store_true",
        default=os.environ.get("TLS_GUARD", "1").strip() not in ("0", "false", "no"),
        help="Require TLS ClientHello (0x16 0x03) on first packet before connecting upstream",
    )
    parser.add_argument(
        "--no-tls-guard",
        action="store_false",
        dest="tls_guard",
        help="Disable TLS first-packet handshake verification",
    )
    parser.add_argument(
        "--ports",
        default=os.environ.get("RELAY_PORTS", ""),
        help="Comma-separated port mappings (listen:target:upstream)",
    )
    args = parser.parse_args()

    if args.listen is not None:
        up_port = args.upstream if args.upstream is not None else args.listen
        mappings = [(args.bind, args.listen, args.target, up_port)]
    else:
        mappings = parse_mappings(args.ports, bind_host=args.bind, default_target=args.target)

    relay = TcpRelay(
        target_host=args.target,
        mappings=mappings,
        tls_guard=args.tls_guard,
    )
    asyncio.run(run_forever(relay))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
