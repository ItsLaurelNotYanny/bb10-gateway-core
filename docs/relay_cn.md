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
      │ 1. 频率控制 (iptables: 单 IP 每 60 秒最多 45 次新建连接)
      │ 2. TLS 首包防护盾: 深度检查首包前 2 字节 (0x16 0x03)
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

### iptables 频率限制
网关监听端口具备防爆破和防连接耗尽保护：
```bash
ACTIVE_PORTS="2443,2444,2445,2446"
sudo iptables -I INPUT 1 -p tcp -m multiport --dports "$ACTIVE_PORTS" \
    -m state --state NEW -m recent --name bb10_rate --set
sudo iptables -I INPUT 2 -p tcp -m multiport --dports "$ACTIVE_PORTS" \
    -m state --state NEW -m recent --name bb10_rate --update --seconds 60 --hitcount 45 -j DROP
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
