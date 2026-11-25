# 网关架构与核心模块内部实现

[English](modules.md)

本文档详细说明 `bb10-gateway-core` 核心架构与各模块的技术实现细节。

---

## 1. 显示基座 (`client_html.py` 与 `gateway.py`)

- **分辨率与设备像素比 (DPR)**：BlackBerry Passport 拥有 1440×1440 物理屏幕，设备像素比为 2。直接按 1440×1440 进行全量 DOM 渲染会对老旧 WebKit 引擎 (`AppleWebKit/537.35+`) 造成较大负载。网关统一采用 `720×720` 逻辑像素渲染，并在客户端缩放到全屏面板，抗锯齿平滑关闭以保障字体清晰锐利 (`imageSmoothingEnabled = false`)。
- **双缓冲 Canvas**：使用离屏缓冲 Canvas (`#buf`) 承载实时脏矩形绘制，完成后一次性整帧贴图至呈现 Canvas (`#cv`)。
- **10 字节脏矩形二进制协议**：
  每帧图像传输均以 10 字节二进制包头开头，后接原始 JPEG 字节：
  - 字节 0..1：uint16 `x` 坐标
  - 字节 2..3：uint16 `y` 坐标
  - 字节 4..5：uint16 `w` 宽度
  - 字节 6..7：uint16 `h` 高度
  - 字节 8..9：uint16 保留位 / 标志位
  - 后续载荷：4:4:4 色度抽样的 JPEG 图像流
- **功耗与网络守护**：
  当 Passport 锁屏或浏览器标签页处于后台隐藏状态时 (`document.hidden` 或 `webkitHidden`)，客户端通过 WebSocket 自动发送 `{type: "pause", paused: true}`。服务端暂停 JPEG 捕获与编码，网络吞吐降至 `0 B/s`。

---

## 2. 双轨输入引擎

双轨输入引擎彻底解决了 BlackBerry 10 虚拟软键盘 / 输入法与物理全键盘操作之间的冲突。

### 轨道 1：顶部锚定输入抽屉 (`#msg`)
- 专职于输入法混输：中文拼音、英文预测词库、向上滑动选词以及完整标点栏。
- 抽屉固定在**屏幕顶部** (`top: 34px/64px`)。当 BB10 系统的候选词条在屏幕底部弹出时，绝不遮挡正在输入的文字目标。
- 按压物理回车键 `Enter` 即可瞬间发送，无需手指点按屏幕。

### 轨道 2：直通输入模式 (`#typeTrap` + `#numBar`)
- 专职于终端操作、vim 快捷键以及连续单键导航。
- **零缓冲捕获机制 (Zero-Buffer Trap)**：BB10 硬件键盘驱动仅在 DOM 输入控件获得焦点时才触发长按大写转换（如长按 `a` $\rightarrow$ `BackSpace` + `A`）。若任由字符在 `#typeTrap` 中堆积，系统英文联想引擎会弹出黑色的空白建议条。客户端在每次按键分发后立即将 `#typeTrap` 重置为 4 个基础空格，保持输入框内无有效文本，彻底消除黑条遮挡，同时完整保留长按大写和退格逻辑。

---

## 3. 沙箱与看门狗生命周期 (`entrypoint.sh`)

通过容器启动前清理与前台守护进程循环保证无人值守稳定运行：
1. **清理残留锁文件**：自动清除容器异常退出遗留的 X11 套接字锁 (`/tmp/.X99-lock`、`/tmp/.X11-unix/X99`) 以及 Chromium `Singleton*` 单例锁。
2. **共享内存分配**：为 `/dev/shm` 分配 `1gb` 空间，防止复杂网页渲染时 Chromium IPC 崩溃。
3. **看门狗循环**：顺序拉起 `Xvfb :99`、窗口管理器 (`openbox`)、虚拟输入守护进程 (`xdotool`) 和目标运行时，后台常驻进程定时巡检并在异常时自愈拉起。
4. **无显卡环境 GPU 防护 (`--disable-gpu`)**：
   - **改动原因**：此前 Chromium 启用了 `--use-gl=angle --use-angle=gl-egl --ignore-gpu-blocklist`，在没有硬件 GPU 的无头 NAS 上会回退为软件 ANGLE/SwiftShader 光栅化，导致 `chromium --type=gpu-process` 在双核 NAS 上持续占满 150%+ CPU 并拖慢同机其他容器。
   - **实现方式**：`entrypoint.sh` 改为显式传入 `--disable-gpu`（禁用 GL 与 GPU 合成），消除软件 GPU 空转。
5. **进程内空闲自动挂起 (`gateway.py` 中的 `IdleSleepController`)**：
   - **改动原因**：即便禁用 GPU，Discord/X 等网页应用在无人访问时仍会持续执行后台 JS/DOM 轮询消耗 CPU；而引入外部容器休眠编排器会带来冷启动延迟与 NAS 异常停止误报。
   - **实现机制**：由环境变量 `IDLE_SLEEP_SECONDS` 控制（`chromium` 运行时默认 `30s`，设为 `0` 可关闭）。当所有 WebSocket 客户端断开或锁屏暂停超过阈值后，`gateway.py` 向 `/usr/lib/chromium/chromium` 进程发送 `SIGSTOP` 冻结，使空闲 CPU 降至接近 0 且保留完整内存会话；下次收到已认证的 `GET /` 或 `/ws` 恢复请求时立即发送 `SIGCONT` 毫秒级唤醒。

---

## 4. 媒体与双向剪贴板同步 (`gateway.py`)

- **上行上传**：
  - `📷` (照片)：从 Passport 本地存储拍照或选图，通过 `POST /upload` 上传，转换为 PNG 后粘贴至服务端 X11 剪贴板。
  - `📎` (附件文件)：上传至 `$HOME/Downloads` 并设置 X11 `text/uri-list` 剪贴板。
- **下行同步**：
  - 界面提供专属 `Sync` 按钮。
  - 点按 `Sync` 调用服务端 `clip_get` 接口，拉取服务端 X11 选中内容回填至手机端 `#msg`，便于直接复制到手机本地。

---

## 5. 原生 144×144 图标引擎 (`icon_gen.py`)

无需认证的 `/icon.png` 接口根据 BB10 规范生成 144×144 桌面启动图标：
- 画布：144×144 RGBA PNG，外围 14px 透明边距。
- 连续曲率圆角：116×116 矩形，圆角半径 26px。
- 超采样平滑：4 倍分辨率渲染并通过 Lanczos 滤波器降采样。
- 支持两种风格：`slate`（冷灰深色渐变）与 `badge`（品牌底色搭配右下角黑莓 7 点微标）。
