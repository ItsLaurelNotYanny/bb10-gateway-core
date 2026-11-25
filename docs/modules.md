# Gateway Architecture & Module Internals

[简体中文](modules_cn.md)

This document provides in-depth technical details on the core architectural components of `bb10-gateway-core`.

---

## 1. Display Base (`client_html.py` & `gateway.py`)

- **Resolution & DPR**: The BlackBerry Passport features a physical 1440×1440 screen with Device Pixel Ratio (DPR) 2. Rendering at native 1440×1440 would strain the legacy WebKit engine (`AppleWebKit/537.35+`). The gateway renders at `720×720` logical pixels (`DPR=2`), scaling to the full physical panel with zero blur (`imageSmoothingEnabled = false`).
- **Double-Buffered Canvas**: Frame rendering utilizes an offscreen buffer canvas (`#buf`) composited onto the visible presentation canvas (`#cv`).
- **10-Byte Dirty-Rect Protocol**:
  Each frame transmission starts with a 10-byte binary header followed by raw JPEG bytes:
  - Byte 0..1: uint16 `x` coordinate
  - Byte 2..3: uint16 `y` coordinate
  - Byte 4..5: uint16 `w` width
  - Byte 6..7: uint16 `h` height
  - Byte 8..9: uint16 reserved / flags
  - Trailing: 4:4:4 subsampled JPEG payload
- **Power & Bandwidth Guard**:
  When the Passport screen locks or the browser tab is hidden (`document.hidden` or `webkitHidden`), the client dispatches `{type: "pause", paused: true}` over WebSocket. The server suspends JPEG capture and transmission, dropping network traffic to `0 B/s`.

---

## 2. Dual-Track Input Engine

The dual-track engine resolves the conflict between BlackBerry 10's software keyboard / IME and physical hardware typing.

### Track 1: Top-Anchored Write Drawer (`#msg`)
- Dedicated to composition: Chinese Pinyin, predictive English dictionaries, flick-up selection, and full punctuation strips.
- Anchored at the **top of the screen** (`top: 34px/64px`). When the BB10 OS software candidate bar appears at the bottom of the screen, it never occludes the typing target.
- Physical `Enter` dispatches immediately without touching the screen.

### Track 2: Type Mode (`#typeTrap` + `#numBar`)
- Direct pass-through for terminal navigation, vim commands, and shortcuts.
- **The Zero-Buffer Trap**: BB10 hardware keyboard drivers only trigger long-press uppercase conversion (`a` held -> `BackSpace` + `A`) when a DOM input holds focus. However, letting typed characters accumulate in `#typeTrap` causes the OS prediction engine to overlay an unwanted black bar. The client immediately resets `#typeTrap` to 4 base spaces after dispatching each key, keeping the text buffer empty and eliminating the prediction overlay while preserving uppercase conversion and Backspace handling.

---

## 3. Sandbox & Watchdog Lifecycle (`entrypoint.sh`)

Unattended container stability is guaranteed by pre-launch cleanup and active process supervision:
1. **Lock Cleanup**: Automatically removes stale X11 sockets (`/tmp/.X99-lock`, `/tmp/.X11-unix/X99`) and Chromium `Singleton*` locks caused by sudden container restarts.
2. **RAM-Disk Shm**: Allocates `shm_size: 1gb` for `/dev/shm` to prevent Chromium IPC crashes under heavy DOM rendering.
3. **Supervisor Loop**: Starts `Xvfb :99`, window manager (`openbox`), virtual input daemon (`xdotool`), and target runtime. A background loop checks process health and auto-heals if the target application exits unexpectedly.
4. **Headless GPU Guard (`--disable-gpu`)**:
   - **Why**: Previously, launching Chromium with `--use-gl=angle --use-angle=gl-egl --ignore-gpu-blocklist` forced software ANGLE/SwiftShader GPU rasterization on headless NAS hosts without hardware GPUs, causing `chromium --type=gpu-process` to burn >150% CPU continuously on 2-core NAS devices and starve co-located containers.
   - **Change**: `entrypoint.sh` now launches Chromium with `--disable-gpu` (`--use-gl=disabled`, `--disable-gpu-compositing`), preventing runaway software GPU spin.
5. **In-Process Idle Auto-Sleep (`IdleSleepController` in `gateway.py`)**:
   - **Why**: Even with `--disable-gpu`, idle Chromium web apps (such as Discord or X) continue background DOM/JS activity when no client is connected. Stopping the entire container via external orchestrators introduces cold-start latency and false "unexpected stop" alerts on NAS platforms.
   - **Mechanism**: Controlled by `IDLE_SLEEP_SECONDS` (defaults to `30s` for `chromium` runtimes; `0` disables). When no unpaused WebSocket clients remain active for the timeout window, `gateway.py` sends `SIGSTOP` to `/usr/lib/chromium/chromium` processes, dropping idle CPU to near zero while keeping container state intact. The next authenticated `GET /` or `/ws` resume immediately sends `SIGCONT` for millisecond-level wake-up.

---

## 4. Media & Clipboard Sync (`gateway.py`)

- **Upstream Upload**:
  - `📷` (Photo): Captures or selects an image from BBP storage, uploads via `POST /upload`, transforms to PNG, and pastes into the server X11 clipboard.
  - `📎` (File attachment): Uploads to `$HOME/Downloads` and sets the X11 `text/uri-list` clipboard selection.
- **Downstream Sync**:
  - The client UI features a dedicated `Sync` button.
  - Tapping `Sync` calls the server `clip_get` endpoint to pull current X11 selection text into the BBP `#msg` field, enabling native phone copy/paste.

---

## 5. Native 144×144 Icon Engine (`icon_gen.py`)

The unauthenticated `/icon.png` endpoint serves dynamic 144×144 home screen launcher icons matching BB10 design specifications:
- Canvas: 144×144 RGBA PNG with 14px outer transparent inset.
- Squircle: 116×116 rounded box with 26px corner radius.
- Supersampling: Rendered at 4x resolution and downsampled via Lanczos filtering.
- Two styles available via `ICON_STYLE` or `?style=`:
  - `slate`: Matte dark slate-gray vertical gradient (`#262C32` -> `#14181C`).
  - `badge`: Vertical brand gradient with the BlackBerry 7-dot emblem in the lower right.
