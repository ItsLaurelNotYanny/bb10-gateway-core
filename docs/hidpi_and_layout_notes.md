# HiDPI Display & Layout Stabilization Notes

[简体中文](hidpi_and_layout_notes_cn.md)

## 1. 2x HiDPI Scaling Switch (`hidpi` / `HIDPI`)

To support native Retina rendering on 1440×1440 square displays while keeping bandwidth-friendly 1x mode available, `bb10-gateway-core` provides a universal `2x` scaling toggle:

- **Preset Configuration**: Set `hidpi = true` in a preset `.toml` file, or override at runtime with `HIDPI=1` / `HIDPI=0` (passed through [deploy/compose.yml](../deploy/compose.yml)).
- **Scale Factor Calculation**: [presets.py](../presets.py) exposes `preset_scale(preset)` returning `2` when `hidpi` is enabled and `1` otherwise.
- **Container Display Environment** ([entrypoint.sh](../entrypoint.sh)):
  - Starts `Xvfb` at `win_w * scale` × `xvfb_h * scale` physical pixels.
  - Exports `QT_SCALE_FACTOR=2`, `QT_AUTO_SCREEN_SCALE_FACTOR=0`, `GDK_SCALE=2`, `GDK_DPI_SCALE=1`, and merges `Xft.dpi: 192` for native GUI and Xft-based applications.
  - Passes `--force-device-scale-factor=2` to Chromium.
- **Streaming & Coordinate Mapping** ([gateway.py](../gateway.py) & [client_html.py](../client_html.py)):
  - Physical viewport bounds, dirty-rect capture, `clamp_win_h`, `detect_chat_x`, and canvas/pointer coordinate mapping scale uniformly by `scale`.
  - Setting `win_w = 720, win_h = 720` with `hidpi = true` produces an exact `1440×1440` 1:1 physical pixel stream.

---

## 2. Slim-Rail Split Stability & 1:1 Width Alignment

- **Multi-Point Vertical Border Verification**: `detect_chat_x` in [gateway.py](../gateway.py) samples 6 vertical scanlines (`0.15h`–`0.90h`) and requires both consistent horizontal contrast and vertical color uniformity along `x - 1`. This prevents avatars, embeds, or long messages from shifting the split coordinate during scrolling.
- **Exact 1:1 Slim Width**: For `slim_rail` presets (`rail_w = 72`, `default_chat_x = 375`), setting `win_w = 1023` yields `72 + (1023 - 375) = 720` logical pixels (`1440` physical pixels at `2x`), avoiding fractional nearest-neighbor downscaling.

---

## 3. Native GUI & Terminal Rendering Fixes

- **Locked Window Height (`lock_win_h = true`)**:
  - [entrypoint.sh](../entrypoint.sh) sizes `Xvfb` height to `EFF_WIN_H * scale` when `lock_win_h` is enabled, preventing Openbox `<maximized>yes</maximized>` from stretching fixed-layout native GUI apps vertically off-screen.
  - `handle_ws` in [gateway.py](../gateway.py) enforces `preset.win_h * scale` on initial WebSocket handshake whenever `lock_win_h` is enabled.
- **Terminal Font & `.Xresources` Handling**:
  - [entrypoint.sh](../entrypoint.sh) checks whether `$HOME/.Xresources` defines `XTerm*faceName` before applying fallback `-fa` CLI flags, allowing extended terminal images to customize font family, weight, and `faceSize` cleanly.
  - On 1440×1440 HiDPI displays (`192 DPI`), wider-proportioned monospace fonts (such as `DejaVu Sans Mono` at `faceSize: 12`) avoid the tall-and-narrow appearance of condensed fonts.

---

## 4. Deployment Notes

- Recreating containers after `docker load` requires `docker compose ... up -d --force-recreate` (not `docker restart`) so running containers switch to the newly loaded image digest.
- **Future Optimization (Split-Horizon DNS)**: Pointing the gateway hostname to the LAN host IP on the local router/DNS allows zero-hop WLAN direct streaming at home while seamlessly falling back to the VPS relay on external networks.
