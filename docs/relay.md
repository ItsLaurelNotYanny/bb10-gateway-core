# Hardened VPS L4 Relay Architecture

The optional VPS relay in `contrib/relay/` allows accessing self-hosted BlackBerry 10 gateways over public cellular networks without exposing private NAS ports or home IP addresses directly to the internet.

---

## 1. Network Topology

```
BlackBerry Passport (Cellular)
      │
      │ HTTPS (TLS 1.2+ ClientHello)
      ▼
Public VPS (:2443..:2446)
      │
      │ 1. Rate-limit check (iptables: max 45 new connections / 60s per IP)
      │ 2. TLS First-Packet Shield: inspects first 2 bytes (0x16 0x03)
      │    Non-TLS scanners dropped immediately without opening upstream hop
      ▼
Tailscale / WireGuard Mesh VPN
      │
      ▼
Private NAS / Workstation (Listening on LAN/Tailscale IP)
```

---

## 2. Key Security Mechanisms

### TLS First-Packet Shield (`TLS_GUARD=1`)
Web crawlers, shodan probes, and automated port scanners routinely scan exposed VPS ports with plain HTTP or random binary payloads.
The relay inspects the initial socket buffer:
- Byte 0 must equal `0x16` (`Handshake` record).
- Byte 1 must equal `0x03` (`SSL 3.0 / TLS 1.x` protocol version).
If the payload does not start with a valid TLS ClientHello, the connection is instantly closed without opening an upstream socket to the private network.

### Rate Limiting via `iptables`
Active gateway ports are protected against brute-force and connection-exhaustion attacks:
```bash
ACTIVE_PORTS="2443,2444,2445,2446"
sudo iptables -I INPUT 1 -p tcp -m multiport --dports "$ACTIVE_PORTS" \
    -m state --state NEW -m recent --name bb10_rate --set
sudo iptables -I INPUT 2 -p tcp -m multiport --dports "$ACTIVE_PORTS" \
    -m state --state NEW -m recent --name bb10_rate --update --seconds 60 --hitcount 45 -j DROP
```

---

## 3. Deployment

Run the automated deployment helper on a local workstation with SSH access to the relay VPS:

```bash
VPS_HOST="vps.example.org" \
VPS_USER="ubuntu" \
SSH_KEY="$HOME/.ssh/id_rsa" \
./contrib/relay/deploy_vps_relay.sh
```

The script installs:
- Executable: `/usr/local/bin/tcp-relay`
- Systemd template: `/etc/systemd/system/tcp-relay@.service`
- Per-application environment configurations in `/etc/tcp-relay/<app>.env`
