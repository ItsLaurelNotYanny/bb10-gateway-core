# 版本变更记录

[English](CHANGELOG.md) | 简体中文

本文档记录 `bb10-gateway-core` 的重要版本演进与故障修复原因。

---

## [1.1.0] - 2026-11-27

### 变更背景与根因分析
在外出使用不稳定手机热点 Wi-Fi（蜂窝公网 IP 多次切换、丢包抖动）的场景下，三个因素叠加导致 BlackBerry 10 上所有已打开的网关应用持续卡在 `Off` / `Conn` 循环，无法恢复为 `Live`：

1. **VPS `iptables` `xt_recent` 限流自锁**：原有两条 `xt_recent` 规则（先 `--set` 再 `--update --seconds 60 --hitcount 45 -j DROP`）在所有中继端口间共用同一个 60 秒计数桶，命中丢包时会产生双倍时间戳记录，并在客户端/内核 TCP SYN 重传期间持续刷新窗口，导致正常用户被黑洞丢包。
2. **客户端固定频率重连风暴与旧页面卡死**：`client_html.py` 原先每 `1800ms` 无退避固定重连且切后台不停止，3–4 个应用同时断线不到 30 秒即可打满 45 次限流阈值；同时 BB10 老版本 WebKit 的已打开页面在剧烈网络切换后，仅靠 JS `new WebSocket()` 重连可能持续失败，需整页重新加载（`GET /`）才能重置上下文。
3. **弱网下 TLS 首包超时过严**：`contrib/relay/tcp_relay.py` 默认 `first_packet_timeout=3.0s`，在高抖动热点下容易在 `ClientHello` 到达前误杀正常连接。

此外，本次还定位并修复了一项终端网关（`bb10-term`）的**架构迁移遗漏**问题：

4. **终端网关宿主机 `tmux` 套接字被容器抢占**：从旧版独立终端网关迁移至 `bb10-gateway-core` 时，切换脚本遗漏了“先在宿主机启动 `tmux` server”的前置步骤，而容器内的 `term_session.sh` 会无条件执行 `tmux new-session -A`。只要宿主机当时尚未启动 `tmux` server（例如切流时或机器重启后 Docker 先于用户会话启动），容器就会抢占共享挂载的 `/tmp/tmux-1000` 套接字并在容器命名空间内拉起 `tmux` server，导致终端落入 `appuser@<container-id>` 与容器内 `$APP_HOME`，而非宿主机真实开发环境。

### 变更内容
- **终端网关宿主机 `tmux` 归属防护与开机持久化**（`deploy/compose.term.yml`、`docs/modules_cn.md`）：
  - 在 `deploy/compose.term.yml` 中透传 `HOST_WORKSPACE` 并默认注入 `REQUIRE_HOST_TMUX=1`。
  - 加固终端会话启动脚本：启用 `REQUIRE_HOST_TMUX=1` 时，容器仅通过 `tmux list-sessions` 探测已有宿主机服务端并等待就绪，绝不在共享套接字上自行拉起容器内 `tmux` server。
  - 在宿主机配置 `systemd --user` 持久化服务（`bb10-tmux.service`，基于 `tmux -D` 与 user lingering），补全切换脚本的宿主机 `tmux` 前置拉起与异常归属自愈，并在终端健康检查中增加宿主机归属断言，一旦出现容器抢占立即报错阻断。
- **VPS 防火墙改为令牌桶限流**（`contrib/relay/deploy_vps_relay.sh`、`docs/relay_cn.md`）：
  - 用单条 Linux 原生 `iptables -m hashlimit` 令牌桶规则（`--hashlimit-mode srcip --hashlimit-above 30/minute --hashlimit-burst 45 -j DROP`）替换原有的两条 `xt_recent` 规则，并在部署时自动清理旧规则。令牌按恒定速率恢复，兼顾防扫描/防滥用与免自锁。
- **放宽 VPS 中继 TLS 首包等待窗口**（`contrib/relay/tcp_relay.py`）：
  - 将 `first_packet_timeout` 从 `3.0s` 放宽至 `10.0s`，严格保持 TLS ClientHello（`0x16 0x03 0x00..0x04`）首包校验及单 IP/全局并发上限不变。
- **前端重连退避与一键重置**（`client_html.py`）：
  - 将固定 `1800ms` 重连改为指数退避加随机抖动（`2s → 4s → 8s → 16s → 30s`，连上即重置）。
  - 页面切入后台时暂停重连，切回前台且处于断线状态时立即重连。
  - 为 `Conn` 建连阶段增加 `8s` 超时保护，避免弱网半开连接长时间假死。
  - 复用顶部栏刷新按钮（`↻`）与左上角状态指示（`#dot`/`#stat`）：在线（`Live`）时照常刷新帧，非 `Live`（`Off`/`Conn`）时点击直接触发 `window.location.reload()` 一键整页硬重置，便于网络稳定后快速恢复。
- **网关鉴权失败日志**（`gateway.py`）：
  - `/ws` 鉴权失败返回 `401` 时输出 `LOG.warning`（仅记录来源地址与 cookie/query 令牌是否存在，绝不输出明文密钥），便于快速区分鉴权与网络故障。

---

## [1.0.0] - 2026-11-11

### 新增
- 发布统一的 `bb10-gateway-core` 核心平台：TLS 1.2+ `aiohttp` 网关、4:4:4 脏矩形 JPEG 推流、严格 ES5 前端与 BlackBerry Passport 双轨输入引擎、声明式 TOML 预设、2x HiDPI 缩放、空闲 Chromium `SIGSTOP`/`SIGCONT` 自动休眠及可选加固型 VPS L4 TCP 中继。
