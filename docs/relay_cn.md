# 加固型 VPS L4 中继架构

`contrib/relay/` 中的可选 VPS 中继组件允许在移动蜂窝网络下直接访问自建 BlackBerry 10 网关，无需将 NAS 私网端口或公网 IP 直接暴露至公网。

---

## 1. 网络拓扑

```
BlackBerry Passport (蜂窝网络)
      │
      │ HTTPS (TLS 1.2+ ClientHello)
      ▼
公网 VPS (:2443..:2446)
      │
      │ 1. 频率控制 (iptables hashlimit 令牌桶: 单 IP 持续 30/分钟，突发 45)
      │ 2. TLS 首包防护盾: 检查首包前 3 字节 (0x16 0x03 0x00..0x04，10 秒首包窗口)
      │    非合规扫描连接直接切断，绝不向内网建立连接
      ▼
Tailscale / WireGuard 虚拟内网
      │
      ▼
私有 NAS / 工作站 (监听内网/Tailscale IP)
```

---

## 2. 关键防护机制

### TLS 首包防护盾 (`TLS_GUARD=1`)
公网扫描器和爬虫常用明文 HTTP 或探测数据包随机扫描公网端口。
中继直接检查入站套接字前两个字节：
- 字节 0 必须等于 `0x16` (Handshake 记录)。
- 字节 1 必须等于 `0x03` (SSL 3.0 / TLS 1.x 协议版本)。
若数据包首部不符合合规 TLS ClientHello，连接立即被丢弃，保护内网主机免遭无效打扰。

### iptables 频率限制（`hashlimit` 令牌桶）
网关监听端口采用按源 IP 的令牌桶防护（令牌按固定速率匀速恢复，既能防爆破与连接耗尽，又避免正常移动弱网重连时自锁）：
```bash
ACTIVE_PORTS="2443,2444,2445,2446"
sudo iptables -I INPUT 1 -p tcp -m multiport --dports "$ACTIVE_PORTS" \
    -m state --state NEW -m hashlimit --hashlimit-name bb10_rate \
    --hashlimit-mode srcip --hashlimit-above 30/minute --hashlimit-burst 45 -j DROP
```

---

## 3. 部署步骤

在具备中继 VPS SSH 免密访问权限的工作站上运行部署脚本：

```bash
VPS_HOST="vps.example.org" \
VPS_USER="ubuntu" \
SSH_KEY="$HOME/.ssh/id_rsa" \
./contrib/relay/deploy_vps_relay.sh
```

脚本将自动部署：
- 可执行文件：`/usr/local/bin/tcp-relay`
- Systemd 模板单元：`/etc/systemd/system/tcp-relay@.service`
- 各独立应用的配置环境：`/etc/tcp-relay/<app>.env`
