# HiDPI 显示与布局稳定性说明

[English](hidpi_and_layout_notes.md)

## 1. 2x HiDPI 缩放开关（`hidpi` / `HIDPI`）

为了在 1440×1440 方形高分屏上支持原生 Retina 级渲染，同时保留低带宽的 1x 标清模式，`bb10-gateway-core` 提供了通用的 `2x` 缩放开关：

- **预设与环境变量控制**：在预设 `.toml` 中设置 `hidpi = true`，或通过环境变量 `HIDPI=1` / `HIDPI=0` 运行时动态覆盖（已通过 [deploy/compose.yml](../deploy/compose.yml) 透传）。
- **缩放因子计算**：[presets.py](../presets.py) 提供 `preset_scale(preset)`，开启 `hidpi` 时返回 `2`，否则返回 `1`。
- **容器显示环境**（[entrypoint.sh](../entrypoint.sh)）：
  - 按 `win_w * scale` × `xvfb_h * scale` 物理像素启动 `Xvfb`。
  - 自动导出 `QT_SCALE_FACTOR=2`、`QT_AUTO_SCREEN_SCALE_FACTOR=0`、`GDK_SCALE=2`、`GDK_DPI_SCALE=1`，并合并 `Xft.dpi: 192` 给原生 GUI 与 Xft 应用。
  - 为 Chromium 传入 `--force-device-scale-factor=2`。
- **推流与坐标映射**（[gateway.py](../gateway.py) 与 [client_html.py](../client_html.py)）：
  - 物理抓屏尺寸、脏矩形编码、`clamp_win_h`、`detect_chat_x` 以及前端 Canvas 与鼠标点击坐标均按 `scale` 统一对齐。
  - 当 `win_w = 720, win_h = 720` 且开启 `hidpi = true` 时，直接输出 `1440×1440` 1:1 物理像素点对点画面。

---

## 2. Slim-Rail 分栏稳定性与 1:1 宽度对齐

- **多点垂直边框校验**：[gateway.py](../gateway.py) 中的 `detect_chat_x` 采用 6 条纵向扫描线（`0.15h`–`0.90h`）采样，要求同时满足跨线反差与 `x - 1` 左侧边框的垂直颜色一致性，彻底避免滚动聊天记录时头像、Embed 卡片或长文本引发分栏位置跳变。
- **Slim 模式 1:1 点对点宽度**：对于 `slim_rail` 预设（`rail_w = 72`、`default_chat_x = 375`），将 `win_w` 设为 `1023` 可使合并宽度恰好等于 `72 + (1023 - 375) = 720` 逻辑像素（`2x` 下为 `1440` 物理像素），避免非整数缩放带来的锐度损失。

---

## 3. 原生 GUI 与终端渲染修正

- **锁定窗口高度（`lock_win_h = true`）**：
  - [entrypoint.sh](../entrypoint.sh) 在 `lock_win_h` 开启时按 `EFF_WIN_H * scale` 启动 `Xvfb`，防止 Openbox `<maximized>yes</maximized>` 将固定布局原生桌面应用纵向拉伸出屏幕。
  - [gateway.py](../gateway.py) 中的 `handle_ws` 在初始 WebSocket 握手时强制遵循 `preset.win_h * scale`。
- **终端字体与 `.Xresources` 优先级**：
  - [entrypoint.sh](../entrypoint.sh) 在启动 `xterm` 前检查 `$HOME/.Xresources` 是否已定义 `XTerm*faceName`，有定义时不再用命令行 `-fa` 参数强行覆盖，从而允许终端扩展镜像自定义字体、字重与默认字号。
  - 在 1440×1440（`192 DPI`）下选用字宽更舒展的等宽字体（如 `DejaVu Sans Mono` 搭配 `faceSize: 12`）可避免窄高型字体显得“瘦高”。

---

## 4. 部署与后续优化提示

- 执行 `docker load` 导入新镜像后，必须使用 `docker compose ... up -d --force-recreate` 重建容器以切换到新镜像摘要（仅执行 `docker restart` 仍会运行旧容器）。
- **后续分流方向（Split-Horizon DNS）**：在家庭路由器或内网 DNS 中将网关域名解析至局域网宿主机 IP，即可实现“在家直连 WLAN、出门无缝走 VPS 中继”。
