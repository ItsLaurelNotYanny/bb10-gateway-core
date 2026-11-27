# Changelog

English | [简体中文](CHANGELOG_cn.md)

All notable changes to `bb10-gateway-core` are documented in this file.

---

## [1.1.0] - 2026-11-27

### Incident Context & Motivation
During field usage over an unstable mobile hotspot Wi-Fi connection (frequent cellular IP rotations and packet loss), three compounding issues caused all open gateway apps on BlackBerry 10 to get stuck alternating between `Off` and `Conn` without recovering to `Live`:

1. **VPS `iptables` `xt_recent` self-lockout**: The legacy 2-rule `xt_recent` pair (`--set` followed by `--update --seconds 60 --hitcount 45 -j DROP`) shared a single bucket across all relay ports, double-recorded blocked SYN packets, and extended the block window while retries/SYN retransmissions continued.
2. **Client fixed-interval reconnect storm**: `client_html.py` retried every `1800ms` with no backoff and kept retrying while backgrounded; 3-4 open apps easily exceeded 45 new connections in under 30 seconds. Additionally, after severe network transitions, existing BB10 WebKit tabs could remain wedged in a rapid WebSocket failure loop until the page itself was reloaded (`GET /`).
3. **Aggressive TLS first-packet timeout on lossy links**: `contrib/relay/tcp_relay.py` enforced a `3.0s` `first_packet_timeout`, dropping legitimate TLS handshakes on slow/jittery cellular hotspots before `ClientHello` arrived.

Additionally, a separate **migration omission** surfaced in the terminal gateway (`bb10-term`):

4. **Terminal gateway host `tmux` socket hijacking**: When migrating the terminal app from the standalone legacy deployment into `bb10-gateway-core`, the pre-launch host `tmux` bootstrap step was omitted from the cutover script, while the container's `term_session.sh` unconditionally executed `tmux new-session -A`. Whenever the host `tmux` server was absent (during cutover or after a host reboot where Docker started before a user shell), the container won the race on the shared `/tmp/tmux-1000` socket and spawned a container-local `tmux` server (`appuser@<container-id>` in `$APP_HOME`) instead of attaching to the host user environment.

### Changed
- **Terminal Gateway Host `tmux` Ownership Guard & Boot Persistence** (`deploy/compose.term.yml`, `docs/modules.md`):
  - Forwarded `HOST_WORKSPACE` and `REQUIRE_HOST_TMUX=1` (by default) in `deploy/compose.term.yml`.
  - Hardened the terminal session launcher so that when `REQUIRE_HOST_TMUX=1` is active, the container polls `tmux list-sessions` and waits for an existing host `tmux` server instead of ever spawning a container-owned `tmux` server on the shared socket.
  - Added host `systemd --user` persistence (`bb10-tmux.service` with `tmux -D` and lingering enabled), restored host `tmux` bootstrap/mismatch recovery in the cutover script, and added mechanical host-ownership verification to the terminal health check so container hijacking fails checks immediately.
- **VPS Firewall Rate Limiting** (`contrib/relay/deploy_vps_relay.sh`, `docs/relay.md`):
  - Replaced the 2-line `xt_recent` (`--set` + `--update`) rules with a single Linux native `iptables -m hashlimit` token-bucket rule (`--hashlimit-mode srcip --hashlimit-above 30/minute --hashlimit-burst 45 -j DROP`), removing legacy `xt_recent` rules automatically during deployment. Steady token refill prevents 60-second blackouts while preserving abuse protection.
- **VPS Relay TLS First-Packet Window** (`contrib/relay/tcp_relay.py`):
  - Relaxed `first_packet_timeout` from `3.0s` to `10.0s` while keeping strict TLS ClientHello (`0x16 0x03 0x00..0x04`) validation and per-IP/global concurrency caps unchanged.
- **Client Reconnect Resilience & One-Tap Reset** (`client_html.py`):
  - Replaced fixed `1800ms` retries with exponential backoff + random jitter (`2s -> 4s -> 8s -> 16s -> 30s`, reset on `onopen`).
  - Paused reconnect attempts while the page is hidden/backgrounded and triggered immediate reconnect on returning to foreground.
  - Added an `8s` WebSocket connecting timeout (`Conn`) to avoid hanging indefinitely on half-open mobile sockets.
  - Repurposed the top-bar refresh button (`↻`) and status indicator (`#dot`/`#stat`) so tapping them while not `Live` performs a one-tap `window.location.reload()` hard reset to recover wedged BB10 WebKit page contexts once the network stabilizes.
- **Gateway Diagnostics** (`gateway.py`):
  - Logged a warning on rejected unauthenticated `/ws` upgrades (recording only peer address and presence booleans for cookie/query token, never secrets).

---

## [1.0.0] - 2026-11-11

### Added
- Initial unified `bb10-gateway-core` platform: TLS 1.2+ `aiohttp` gateway, 4:4:4 dirty-rect JPEG streamer, strict ES5 client UI with dual-track BB10 Passport input, declarative TOML preset system, HiDPI 2x scaling, idle Chromium `SIGSTOP`/`SIGCONT` auto-sleep, and optional hardened VPS L4 TCP relay.
