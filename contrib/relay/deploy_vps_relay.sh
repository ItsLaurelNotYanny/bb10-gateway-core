#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

# Required environment (no defaults on purpose):
#   VPS_HOST, VPS_USER, SSH_KEY
#   RELAY_SERVICES: space-separated "name:listen_port:target_host:upstream_port" entries
: "${VPS_HOST:?set VPS_HOST}"
: "${VPS_USER:?set VPS_USER}"
: "${SSH_KEY:?set SSH_KEY}"
: "${RELAY_SERVICES:?set RELAY_SERVICES}"

echo "[*] Deploying hardened L4 TCP relay to VPS ($VPS_HOST)..."

if [ ! -f "$SSH_KEY" ]; then
    echo "ERROR: SSH key not found at $SSH_KEY" >&2
    exit 1
fi

SSH_CMD=(ssh -i "$SSH_KEY" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 "$VPS_USER@$VPS_HOST")
SCP_CMD=(scp -i "$SSH_KEY" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10)

echo "[*] Uploading tcp_relay.py and tcp-relay@.service..."
"${SCP_CMD[@]}" tcp_relay.py "$VPS_USER@$VPS_HOST:/tmp/emailproxy-tcp-relay.py"
"${SCP_CMD[@]}" tcp-relay@.service "$VPS_USER@$VPS_HOST:/tmp/tcp-relay@.service"

echo "[*] Configuring isolated units, TLS first-packet shield, and selective firewall rules..."
"${SSH_CMD[@]}" bash -s "$RELAY_SERVICES" <<'EOF'
set -euo pipefail
SERVICES="$*"

# 1. Install relay executable and symlink
sudo install -m 0755 /tmp/emailproxy-tcp-relay.py /usr/local/bin/emailproxy-tcp-relay.py
sudo ln -sf /usr/local/bin/emailproxy-tcp-relay.py /usr/local/bin/tcp-relay
rm -f /tmp/emailproxy-tcp-relay.py

# 2. Install systemd template unit
sudo install -m 0644 /tmp/tcp-relay@.service /etc/systemd/system/tcp-relay@.service
rm -f /tmp/tcp-relay@.service

# 3. Create decoupled environment directory with TLS_GUARD=1 enabled
sudo mkdir -p /etc/tcp-relay

write_env() {
    local name="$1"
    local listen="$2"
    local target="$3"
    local upstream="$4"
    cat <<ENV | sudo tee "/etc/tcp-relay/${name}.env" >/dev/null
BIND_HOST=0.0.0.0
LISTEN_PORT=${listen}
TARGET_HOST=${target}
UPSTREAM_PORT=${upstream}
TLS_GUARD=1
ENV
}

# 4. Global port allocation contract
ACTIVE_PORTS=""
UNITS=()
for entry in $SERVICES; do
    IFS=: read -r svc lport thost uport <<<"$entry"
    write_env "$svc" "$lport" "$thost" "$uport"
    ACTIVE_PORTS="${ACTIVE_PORTS:+$ACTIVE_PORTS,}$lport"
    UNITS+=("tcp-relay@${svc}.service")
done

sudo chmod 0644 /etc/tcp-relay/*.env

# 5. Deactivate legacy monolithic unit if present
sudo systemctl stop emailproxy-relay.service 2>/dev/null || true
sudo systemctl disable emailproxy-relay.service 2>/dev/null || true

# 6. Enable and restart isolated systemd template units
sudo systemctl daemon-reload
for unit in "${UNITS[@]}"; do
    sudo systemctl enable "$unit" >/dev/null 2>&1 || true
    sudo systemctl restart "$unit"
done

# 7. Firewall Hardening (Option A: Selective Active Ports Only + Option C: Token-Bucket Rate Limit)

# Remove legacy xt_recent rules (double-counted --set/--update could self-lockout on reconnect)
while sudo iptables -D INPUT -p tcp -m multiport --dports "$ACTIVE_PORTS" -m state --state NEW -m recent --name bb10_rate --set 2>/dev/null; do :; done
while sudo iptables -D INPUT -p tcp -m multiport --dports "$ACTIVE_PORTS" -m state --state NEW -m recent --name bb10_rate --update --seconds 60 --hitcount 45 -j DROP 2>/dev/null; do :; done

# Per-IP token-bucket limit (30/min sustained, burst 45; steady token refill avoids lockout)
if ! sudo iptables -C INPUT -p tcp -m multiport --dports "$ACTIVE_PORTS" -m state --state NEW -m hashlimit --hashlimit-name bb10_rate --hashlimit-mode srcip --hashlimit-above 30/minute --hashlimit-burst 45 -j DROP 2>/dev/null; then
    sudo iptables -I INPUT 1 -p tcp -m multiport --dports "$ACTIVE_PORTS" -m state --state NEW -m hashlimit --hashlimit-name bb10_rate --hashlimit-mode srcip --hashlimit-above 30/minute --hashlimit-burst 45 -j DROP
fi

if ! sudo iptables -C INPUT -p tcp -m multiport --dports "$ACTIVE_PORTS" -m state --state NEW -j ACCEPT 2>/dev/null; then
    sudo iptables -I INPUT 2 -p tcp -m multiport --dports "$ACTIVE_PORTS" -m state --state NEW -j ACCEPT
fi

if command -v netfilter-persistent >/dev/null 2>&1; then
    sudo netfilter-persistent save >/dev/null 2>&1 || true
fi

# 8. Verify active listeners
echo "[*] Active listeners on VPS:"
ss -tulpn | grep -E ":(${ACTIVE_PORTS//,/|})\b" || true
EOF

echo "================================================================================"
echo "[OK] Hardened VPS TCP relay deployed!"
echo "  - Option A (Selective Ports): Only configured ports are exposed"
echo "  - Option B (TLS Shield):      0x16 0x03 ClientHello required before LAN hop"
echo "  - Option C (Rate Limiting):   Per-IP connection burst protection enabled"
echo "================================================================================"
