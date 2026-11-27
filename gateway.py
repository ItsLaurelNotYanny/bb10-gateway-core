"""BB10 Gateway Core: TLS 1.2 aiohttp server, 4:4:4 dirty-rect encoder, and X11 bridge."""

from __future__ import annotations

import asyncio
import hmac
import inspect
import io
import json
import logging
import os
import re
import secrets
import signal
import ssl
import struct
import subprocess
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aiohttp import WSMsgType, web
from PIL import Image, ImageChops, ImageGrab, UnidentifiedImageError

from icon_gen import generate_icon_bytes
from presets import Preset, load_preset, preset_scale

LOG = logging.getLogger("bb10_gateway")

FRAME_MAGIC = 0x42
HEADER_STRUCT = struct.Struct(">BBHHHH")
FLAG_PATCH = 0
FLAG_FULL = 1
DIRTY_FULL_THRESHOLD = 0.40
MIN_WIN_H = 420
MAX_WIN_H = 1080
DEFAULT_WIN_H = 720
DEFAULT_IDLE_SLEEP_SECONDS = 30.0
MAX_UPLOAD_BYTES = 8 * 1024 * 1024
TYPE_MODE_KEYS = frozenset({"Return", "BackSpace", "Tab", "Escape", "space"})
SAFE_TERMINAL_KEYS = frozenset(
    {
        "Up",
        "Down",
        "Left",
        "Right",
        "Home",
        "End",
        "Page_Up",
        "Page_Down",
        "Insert",
        "Delete",
        "slash",
        "bar",
        "minus",
        "asciitilde",
        "underscore",
        "grave",
        "backslash",
        *(f"F{i}" for i in range(1, 13)),
    }
)
SAFE_MODIFIER_RE = re.compile(r"^(?:ctrl|alt)\+[a-z0-9]$")
_CAPTURE_LOCK = asyncio.Lock()


def is_allowed_key(key_name: str, preset: Preset) -> bool:
    """Validate whether an X11 keysym or combo is permitted for input."""
    if not key_name or not isinstance(key_name, str):
        return False
    if (
        key_name in preset.passthrough_keys
        or key_name in TYPE_MODE_KEYS
        or key_name in SAFE_TERMINAL_KEYS
    ):
        return True
    return bool(SAFE_MODIFIER_RE.match(key_name))


def resolve_token(
    env: Mapping[str, str] | None = None,
    default_paths: Sequence[str | Path] = ("/data/token.txt", "./token.txt"),
) -> str:
    """Resolve access token from env, token file, or auto-generate 12-byte hex."""
    source_env = os.environ if env is None else env
    env_tok = source_env.get("ACCESS_TOKEN", "").strip()
    if env_tok:
        return env_tok

    explicit_file = source_env.get("ACCESS_TOKEN_FILE", "").strip()
    search_paths: list[Path] = []
    if explicit_file:
        search_paths.append(Path(explicit_file))
    search_paths.extend(Path(p) for p in default_paths)

    for path in search_paths:
        try:
            if path.is_file():
                val = path.read_text(encoding="utf-8").strip()
                if val:
                    return val
        except OSError:
            continue

    generated = secrets.token_hex(12)
    write_targets = [Path(explicit_file)] if explicit_file else [Path(p) for p in default_paths]
    for target in write_targets:
        try:
            if target.parent.exists() and os.access(target.parent, os.W_OK):
                target.write_text(generated + "\n", encoding="utf-8")
                os.chmod(target, 0o600)
                break
        except OSError:
            continue
    return generated


def check_auth(request: web.Request, expected_token: str, cookie_name: str) -> bool:
    """Constant-time check of ?t= query parameter or HTTP-only auth cookie."""
    if not expected_token:
        return False
    query_tok = request.query.get("t", "")
    cookie_tok = request.cookies.get(cookie_name, "")
    q_ok = bool(query_tok) and hmac.compare_digest(query_tok, expected_token)
    c_ok = bool(cookie_tok) and hmac.compare_digest(cookie_tok, expected_token)
    return q_ok or c_ok


def _safe_int(val: Any, default: int = 0) -> int:
    """Convert arbitrary JSON scalar to int without raising on malformed values."""
    try:
        return int(float(val)) if val is not None else default
    except (TypeError, ValueError):
        return default


def clamp_win_h(h: int | float | str | None, default: int = DEFAULT_WIN_H, scale: int = 1) -> int:
    """Clamp dynamic client viewport height into [420 * scale, 1080 * scale]."""
    val = _safe_int(h, default=int(default))
    return max(MIN_WIN_H * scale, min(MAX_WIN_H * scale, val))


def _encode_jpeg(img: Image.Image, quality: int) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=False, subsampling=0)
    return buf.getvalue()


def encode_dirty_frame(
    prev_img: Image.Image | None,
    curr_img: Image.Image,
    quality: int = 70,
) -> bytes | None:
    """Encode dirty rectangle or full frame with a 10-byte big-endian binary header."""
    curr_rgb = curr_img.convert("RGB") if curr_img.mode != "RGB" else curr_img
    win_w, win_h = curr_rgb.size

    if prev_img is not None and prev_img.size == curr_rgb.size:
        prev_rgb = prev_img.convert("RGB") if prev_img.mode != "RGB" else prev_img
        bbox = ImageChops.difference(curr_rgb, prev_rgb).getbbox()
        if bbox is None:
            return None
        x1, y1, x2, y2 = bbox
        bbox_w = x2 - x1
        bbox_h = y2 - y1
        if (bbox_w * bbox_h) <= DIRTY_FULL_THRESHOLD * (win_w * win_h):
            patch = curr_rgb.crop((x1, y1, x2, y2))
            jpeg_bytes = _encode_jpeg(patch, quality)
            header = HEADER_STRUCT.pack(FRAME_MAGIC, FLAG_PATCH, x1, y1, bbox_w, bbox_h)
            return header + jpeg_bytes

    jpeg_bytes = _encode_jpeg(curr_rgb, quality)
    header = HEADER_STRUCT.pack(FRAME_MAGIC, FLAG_FULL, 0, 0, win_w, win_h)
    return header + jpeg_bytes


def detect_chat_x(im: Image.Image, default_x: int = 375, scale: int = 1) -> int:
    """Locate vertical sidebar/chat split in Discord's slim_rail layout."""
    w, h = im.size
    if w <= max(default_x, 260 * scale) or h < 40 * scale:
        return default_x

    rgb = im.convert("RGB") if im.mode != "RGB" else im
    sample_ys = tuple(int(h * f) for f in (0.15, 0.30, 0.45, 0.60, 0.75, 0.90))
    lo_x = max(240 * scale, default_x - 65 * scale)
    hi_x = min(default_x + 65 * scale, w - 2)
    best_x = default_x
    best_score = 0

    for x in range(lo_x, hi_x):
        diffs = []
        left_px = []
        for y in sample_ys:
            p1 = rgb.getpixel((x - 1, y))
            p2 = rgb.getpixel((x, y))
            left_px.append(p1)
            diffs.append(abs(p2[0] - p1[0]) + abs(p2[1] - p1[1]) + abs(p2[2] - p1[2]))
        # True column boundary must consistently change contrast and have a uniform left border
        if sum(1 for d in diffs if d >= 8) >= 5:
            uniform = max(
                sum(
                    1
                    for p in left_px
                    if abs(p[0] - ref[0]) + abs(p[1] - ref[1]) + abs(p[2] - ref[2]) <= 12
                )
                for ref in left_px[:2]
            )
            if uniform >= 5:
                score = sum(diffs)
                if score > best_score:
                    best_score = score
                    best_x = x

    return best_x if best_score >= 40 else default_x


def resolve_chat_x(im: Image.Image, preset: Preset) -> int:
    """Compute chat_x in physical pixels only when preset.layout == 'slim_rail'."""
    scale = preset_scale(preset)
    default_phys = preset.default_chat_x * scale
    if preset.layout != "slim_rail":
        return default_phys
    return detect_chat_x(im, default_phys, scale=scale)


@dataclass
class StreamSession:
    """Per-client WebSocket streaming state including visibility pause control."""

    preset: Preset
    win_h: int = DEFAULT_WIN_H
    paused: bool = False
    prev_img: Image.Image | None = None
    chat_x: int = 0
    resized_once: bool = False
    wake_event: asyncio.Event = field(default_factory=asyncio.Event)

    @property
    def scale(self) -> int:
        return preset_scale(self.preset)

    @property
    def phys_w(self) -> int:
        return self.preset.win_w * self.scale

    def __post_init__(self) -> None:
        self.win_h = clamp_win_h(
            self.win_h, default=self.preset.win_h * self.scale, scale=self.scale
        )
        self.chat_x = self.preset.default_chat_x * self.scale

    def set_paused(self, paused: bool) -> bool:
        """Update pause state; returns True when resuming to trigger immediate check."""
        was_paused = self.paused
        self.paused = bool(paused)
        if was_paused and not self.paused:
            self.wake_event.set()
            return True
        return False

    def request_full_frame(self) -> None:
        """Invalidate previous frame cache and wake capture loop immediately."""
        self.prev_img = None
        self.wake_event.set()

    async def capture_once(
        self,
        capture_fn: Callable[[], Image.Image | Awaitable[Image.Image]],
    ) -> tuple[bytes | None, int | None]:
        """Run one capture/encode cycle; skips X11 capture entirely while paused."""
        if self.paused:
            return None, None

        res = capture_fn()
        curr_img = await res if inspect.isawaitable(res) else res
        new_chat_x = resolve_chat_x(curr_img, self.preset)
        chat_delta = new_chat_x if new_chat_x != self.chat_x else None
        self.chat_x = new_chat_x

        packet = encode_dirty_frame(self.prev_img, curr_img, quality=self.preset.jpeg_quality)
        self.prev_img = curr_img
        return packet, chat_delta


def convert_image_to_png(raw_bytes: bytes) -> bytes:
    """Validate and convert arbitrary uploaded image bytes to PNG."""
    with Image.open(io.BytesIO(raw_bytes)) as im:
        im.load()
        target_mode = "RGBA" if "A" in im.getbands() else "RGB"
        converted = im.convert(target_mode) if im.mode != target_mode else im
        out = io.BytesIO()
        converted.save(out, format="PNG")
        return out.getvalue()


def safe_filename(raw_name: str, default: str = "attachment.bin") -> str:
    """Sanitize an uploaded filename to a safe basename without path traversal."""
    base = Path(raw_name or "").name.strip()
    cleaned = re.sub(r"[^\w.\- ()\u4e00-\u9fff]+", "_", base)
    cleaned = cleaned.strip(" .")
    if not cleaned or cleaned in (".", ".."):
        return default
    return cleaned[:120]


def resolve_upload_dir() -> Path:
    """Resolve writable directory for uploaded attachments ($HOME/Downloads or /tmp)."""
    candidates = [
        Path(os.environ.get("BB10_UPLOAD_DIR", "")) if os.environ.get("BB10_UPLOAD_DIR") else None,
        Path.home() / "Downloads",
        Path("/tmp/bb10_uploads"),
    ]
    for cand in candidates:
        if cand is None:
            continue
        try:
            cand.mkdir(parents=True, exist_ok=True)
            if os.access(cand, os.W_OK):
                return cand
        except OSError:
            continue
    fallback = Path("/tmp")
    return fallback


def resolve_idle_sleep_seconds(
    preset: Preset,
    env: Mapping[str, str] | None = None,
) -> float:
    """Resolve idle auto-sleep timeout in seconds; 0 disables auto-sleep."""
    source_env = os.environ if env is None else env
    raw = source_env.get("IDLE_SLEEP_SECONDS", "").strip()
    if raw:
        try:
            return max(0.0, float(raw))
        except ValueError:
            LOG.warning("Invalid IDLE_SLEEP_SECONDS=%r; falling back to default", raw)
    return DEFAULT_IDLE_SLEEP_SECONDS if preset.runtime == "chromium" else 0.0


def _signal_chromium_processes(sig: int) -> int:
    """Send a signal (e.g. SIGSTOP/SIGCONT) to Chromium processes via /proc."""
    proc_root = Path("/proc")
    if not proc_root.is_dir():
        return 0
    signaled = 0
    self_pid = os.getpid()
    for entry in proc_root.iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        if pid == self_pid:
            continue
        try:
            cmdline = (entry / "cmdline").read_bytes()
        except OSError:
            continue
        if b"/usr/lib/chromium/chromium" in cmdline:
            try:
                os.kill(pid, sig)
                signaled += 1
            except OSError:
                continue
    return signaled


class IdleSleepController:
    """Suspend managed app processes when no unpaused WebSocket clients are active."""

    def __init__(
        self,
        *,
        idle_seconds: float,
        suspend_fn: Callable[[], Awaitable[None]],
        resume_fn: Callable[[], Awaitable[None]],
    ) -> None:
        self.idle_seconds = max(0.0, float(idle_seconds))
        self._suspend_fn = suspend_fn
        self._resume_fn = resume_fn
        self._sessions: dict[int, StreamSession] = {}
        self._sleep_task: asyncio.Task[None] | None = None
        self.sleeping = False

    def has_active_clients(self) -> bool:
        """Return True if at least one connected client is not paused."""
        return any(not s.paused for s in self._sessions.values())

    def _cancel_timer(self) -> None:
        if self._sleep_task is not None and not self._sleep_task.done():
            self._sleep_task.cancel()
        self._sleep_task = None

    def _schedule_sleep_if_idle(self) -> None:
        if self.idle_seconds <= 0 or self.sleeping or self.has_active_clients():
            return
        if self._sleep_task is not None and not self._sleep_task.done():
            return

        async def _wait_and_sleep() -> None:
            try:
                await asyncio.sleep(self.idle_seconds)
                if not self.has_active_clients() and not self.sleeping:
                    self.sleeping = True
                    LOG.info("No active clients for %.1fs; suspending app", self.idle_seconds)
                    await self._suspend_fn()
            except asyncio.CancelledError:
                return

        self._sleep_task = asyncio.create_task(_wait_and_sleep())

    def start(self) -> None:
        """Start initial idle countdown if no clients are active."""
        self._schedule_sleep_if_idle()

    async def wake(self) -> None:
        """Cancel pending sleep and resume app processes if currently suspended."""
        self._cancel_timer()
        if self.sleeping:
            self.sleeping = False
            LOG.info("Client activity detected; resuming app")
            await self._resume_fn()
        if not self.has_active_clients():
            self._schedule_sleep_if_idle()

    async def register_session(self, session: StreamSession) -> None:
        """Register a connected WebSocket session and wake the app."""
        self._sessions[id(session)] = session
        await self.wake()

    def unregister_session(self, session: StreamSession) -> None:
        """Unregister a disconnected WebSocket session and schedule sleep if idle."""
        self._sessions.pop(id(session), None)
        if not self.has_active_clients():
            self._schedule_sleep_if_idle()

    async def on_pause_changed(self) -> None:
        """React to a session pause/resume state change."""
        if self.has_active_clients():
            await self.wake()
        else:
            self._schedule_sleep_if_idle()

    async def shutdown(self) -> None:
        """Cancel pending sleep timer and ensure app processes are resumed on exit."""
        self._cancel_timer()
        if self.sleeping:
            self.sleeping = False
            await self._resume_fn()


async def _run_cmd(*args: str, stdin_bytes: bytes | None = None, timeout: float = 5.0) -> None:
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdin=subprocess.PIPE if stdin_bytes is not None else subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if stdin_bytes is not None and proc.stdin is not None:
        proc.stdin.write(stdin_bytes)
        await proc.stdin.drain()
        proc.stdin.close()
    await asyncio.wait_for(proc.wait(), timeout=timeout)


async def x11_paste_png(
    png_bytes: bytes,
    paste_keys: Sequence[str] = ("ctrl+v",),
) -> None:
    """Copy PNG bytes into X11 clipboard via xclip and trigger paste keys via xdotool."""
    await _run_cmd(
        "xclip", "-selection", "clipboard", "-t", "image/png", "-i", stdin_bytes=png_bytes
    )
    await asyncio.sleep(0.05)
    for k in paste_keys:
        await _run_cmd("xdotool", "key", "--clearmodifiers", k)


async def x11_paste_file(
    file_bytes: bytes,
    filename: str,
    paste_keys: Sequence[str] = ("ctrl+v",),
) -> Path:
    """Save uploaded attachment to Downloads, copy file:// URI to X11 clipboard, and paste."""
    clean_name = safe_filename(filename)
    dest_dir = resolve_upload_dir()
    dest_path = dest_dir / clean_name
    dest_path.write_bytes(file_bytes)
    uri_payload = f"{dest_path.resolve().as_uri()}\r\n".encode()
    await _run_cmd(
        "xclip",
        "-selection",
        "clipboard",
        "-t",
        "text/uri-list",
        "-i",
        stdin_bytes=uri_payload,
    )
    await asyncio.sleep(0.05)
    for k in paste_keys:
        await _run_cmd("xdotool", "key", "--clearmodifiers", k)
    return dest_path


async def x11_paste_text(
    text: str,
    send_keys: Sequence[str] | None = None,
    paste_keys: Sequence[str] = ("ctrl+v",),
) -> None:
    """Copy UTF-8 text into X11 clipboard, paste via paste_keys, and optionally send."""
    await _run_cmd(
        "xclip",
        "-selection",
        "clipboard",
        "-t",
        "UTF8_STRING",
        "-i",
        stdin_bytes=text.encode("utf-8"),
    )
    await asyncio.sleep(0.04)
    for k in paste_keys:
        await _run_cmd("xdotool", "key", "--clearmodifiers", k)
    if send_keys:
        await asyncio.sleep(0.08)
        for key_spec in send_keys:
            await _run_cmd("xdotool", "key", "--clearmodifiers", key_spec)


async def x11_read_clipboard() -> str:
    """Read UTF-8 text from X11 CLIPBOARD (falling back to PRIMARY selection)."""
    for sel in ("clipboard", "primary"):
        try:
            proc = await asyncio.create_subprocess_exec(
                "xclip",
                "-selection",
                sel,
                "-o",
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=2.0)
            if proc.returncode == 0 and stdout:
                return stdout.decode("utf-8", errors="replace")[:16384]
        except Exception:
            continue
    return ""


async def x11_click(x: int, y: int, btn: int) -> None:
    """Move cursor and click mouse button via xdotool."""
    await _run_cmd("xdotool", "mousemove", "--sync", str(x), str(y), "click", str(btn))


async def x11_wheel(x: int, y: int, steps: int, btn: str) -> None:
    """Move cursor and emit scroll wheel clicks via xdotool."""
    await _run_cmd(
        "xdotool",
        "mousemove",
        str(x),
        str(y),
        "click",
        "--repeat",
        str(steps),
        "--delay",
        "6",
        btn,
    )


async def x11_send_key(key_name: str) -> None:
    """Send an X11 keysym via xdotool key."""
    await _run_cmd("xdotool", "key", "--clearmodifiers", key_name)


async def x11_type_text(text: str) -> None:
    """Type printable ASCII characters directly via xdotool type."""
    await _run_cmd("xdotool", "type", "--clearmodifiers", "--delay", "0", "--", text)


async def x11_capture_screen(win_w: int, win_h: int) -> Image.Image:
    """Capture X11 root display using in-process ImageGrab with scrot RAM-disk fallback."""
    xdisplay = os.environ.get("DISPLAY", ":99")
    tmp_path = Path("/dev/shm/bb10_frame.bmp")
    async with _CAPTURE_LOCK:
        try:
            im_grab = ImageGrab.grab(xdisplay=xdisplay)
            if im_grab is not None:
                return im_grab.convert("RGB").crop((0, 0, win_w, win_h))
        except Exception:
            pass

        await _run_cmd("scrot", "--overwrite", "--silent", str(tmp_path), timeout=3.0)
        with Image.open(tmp_path) as im:
            im.load()
            return im.convert("RGB").crop((0, 0, win_w, win_h))


async def x11_resize_window(win_w: int, win_h: int) -> None:
    """Resize and focus visible window on X11 display using xdotool with fallback to wmctrl."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "xdotool",
            "search",
            "--onlyvisible",
            "--name",
            ".",
            "windowmove",
            "0",
            "0",
            "windowsize",
            str(win_w),
            str(win_h),
            "windowfocus",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        rc = await asyncio.wait_for(proc.wait(), timeout=5.0)
        if rc != 0:
            await _run_cmd("wmctrl", "-r", ":ACTIVE:", "-e", f"0,0,0,{win_w},{win_h}")
    except Exception:
        await _run_cmd("wmctrl", "-r", ":ACTIVE:", "-e", f"0,0,0,{win_w},{win_h}")


async def handle_index(request: web.Request) -> web.Response:
    preset: Preset = request.app["preset"]
    token: str = request.app["token"]
    if not check_auth(request, token, preset.cookie_name):
        return web.Response(status=401, text="Unauthorized\n")

    idle_ctrl: IdleSleepController | None = request.app.get("idle_ctrl")
    if idle_ctrl is not None:
        await idle_ctrl.wake()

    try:
        from client_html import render_client_html

        body = render_client_html(preset)
    except ImportError:
        body = f"<!doctype html><title>{preset.title}</title><canvas id='cv'></canvas>"

    resp = web.Response(text=body, content_type="text/html", charset="utf-8")
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    if request.query.get("t"):
        resp.set_cookie(
            preset.cookie_name,
            token,
            httponly=True,
            secure=request.secure,
            samesite="Lax",
            max_age=86400 * 90,
            path="/",
        )
    return resp


async def handle_healthz(request: web.Request) -> web.Response:
    preset: Preset = request.app["preset"]
    return web.json_response({"ok": True, "preset": preset.name})


async def handle_icon(request: web.Request) -> web.Response:
    """Serve unauthenticated 144x144 squircle app icon for BB10 home screen shortcut."""
    preset: Preset = request.app["preset"]
    style_q = request.query.get("style", "").strip().lower()
    style = style_q if style_q in ("slate", "badge") else preset.icon_style
    png_bytes = generate_icon_bytes(preset.name, style)
    return web.Response(
        body=png_bytes,
        content_type="image/png",
        headers={"Cache-Control": "public, max-age=864000"},
    )


async def handle_upload(request: web.Request) -> web.Response:
    """Accept raw image or attachment bytes up to 8 MB, stage to X11 clipboard, and paste."""
    preset: Preset = request.app["preset"]
    token: str = request.app["token"]
    if not check_auth(request, token, preset.cookie_name):
        return web.json_response({"ok": False, "error": "unauthorized"}, status=401)

    if request.content_length is not None and request.content_length > MAX_UPLOAD_BYTES:
        return web.json_response({"ok": False, "error": "payload_too_large"}, status=413)

    chunks: list[bytes] = []
    total = 0
    async for chunk in request.content.iter_chunked(65536):
        total += len(chunk)
        if total > MAX_UPLOAD_BYTES:
            return web.json_response({"ok": False, "error": "payload_too_large"}, status=413)
        chunks.append(chunk)

    raw_bytes = b"".join(chunks)
    if not raw_bytes:
        return web.json_response({"ok": False, "error": "empty_body"}, status=400)

    mode = request.query.get("mode", "").strip().lower()
    raw_name = request.query.get("name", "").strip()
    if mode == "file":
        clean_name = safe_filename(raw_name or "attachment.bin")
        paste_file_fn = request.app["paste_file_fn"]
        saved_path = await paste_file_fn(raw_bytes, clean_name)
        return web.json_response(
            {
                "ok": True,
                "mode": "file",
                "filename": clean_name,
                "path": str(saved_path) if saved_path is not None else clean_name,
                "file_bytes": len(raw_bytes),
            }
        )

    try:
        png_bytes = convert_image_to_png(raw_bytes)
    except (UnidentifiedImageError, OSError, ValueError):
        return web.json_response({"ok": False, "error": "invalid_image"}, status=400)

    paste_fn = request.app["paste_png_fn"]
    await paste_fn(png_bytes)
    return web.json_response({"ok": True, "png_bytes": len(png_bytes)})


async def _dispatch_ws_msg(
    session: StreamSession,
    data: dict[str, Any],
    app: web.Application,
    ws: web.WebSocketResponse | None = None,
) -> None:
    preset: Preset = app["preset"]
    msg_type = data.get("type")

    if msg_type == "pause":
        session.set_paused(bool(data.get("paused", False)))
        idle_ctrl: IdleSleepController | None = app.get("idle_ctrl")
        if idle_ctrl is not None:
            await idle_ctrl.on_pause_changed()
        return

    if msg_type == "refresh":
        session.request_full_frame()
        return

    if msg_type == "resize":
        if preset.lock_win_h:
            new_h = preset.win_h * session.scale
        else:
            new_h = clamp_win_h(
                data.get("win_h", data.get("h")),
                default=session.win_h,
                scale=session.scale,
            )
        if new_h != session.win_h or not session.resized_once:
            session.win_h = new_h
            session.resized_once = True
            await app["resize_fn"](session.phys_w, new_h)
        session.request_full_frame()
        return

    if msg_type == "click":
        x = max(0, min(session.phys_w - 1, _safe_int(data.get("x"), 0)))
        y = max(0, min(session.win_h - 1, _safe_int(data.get("y"), 0)))
        btn = _safe_int(data.get("button"), 1)
        if btn in (1, 2, 3):
            await app["click_fn"](x, y, btn)
            session.wake_event.set()
        return

    if msg_type == "wheel":
        x = max(0, min(session.phys_w - 1, _safe_int(data.get("x"), session.phys_w // 2)))
        y = max(0, min(session.win_h - 1, _safe_int(data.get("y"), session.win_h // 2)))
        dy = _safe_int(data.get("dy"), 120)
        btn = "5" if dy > 0 else "4"
        steps = max(1, min(8, abs(dy) // 80 or 3))
        await app["wheel_fn"](x, y, steps, btn)
        session.wake_event.set()
        return

    if msg_type == "key":
        key_name = str(data.get("key", ""))
        if is_allowed_key(key_name, preset):
            await app["key_fn"](key_name)
            session.wake_event.set()
        return

    if msg_type == "font":
        direction = str(data.get("dir", ""))
        if direction in ("up", "down"):
            key_sym = "shift+KP_Add" if direction == "up" else "shift+KP_Subtract"
            await app["key_fn"](key_sym)
            await asyncio.sleep(0.05)
            await app["resize_fn"](session.phys_w, session.win_h)
            session.request_full_frame()
        return

    if msg_type == "type":
        text = str(data.get("text", ""))
        if 1 <= len(text) <= 64 and all(0x20 <= ord(ch) <= 0x7E for ch in text):
            await app["type_fn"](text)
            session.wake_event.set()
        return

    if msg_type in ("paste_send", "paste_only"):
        text = str(data.get("text", ""))
        if text:
            send = preset.send_keys if msg_type == "paste_send" else None
            await app["paste_text_fn"](text, send)
            session.wake_event.set()
        return

    if msg_type == "clip_get":
        clip_text = await app["read_clipboard_fn"]()
        if ws is not None and not ws.closed:
            await ws.send_json({"type": "clip_data", "text": clip_text})


async def handle_ws(request: web.Request) -> web.WebSocketResponse:
    preset: Preset = request.app["preset"]
    token: str = request.app["token"]
    if not check_auth(request, token, preset.cookie_name):
        LOG.warning(
            "Rejected unauthenticated /ws from %s (cookie=%s, query_token=%s)",
            request.remote,
            preset.cookie_name in request.cookies,
            bool(request.query.get("t")),
        )
        raise web.HTTPUnauthorized(text="Unauthorized\n")

    ws = web.WebSocketResponse(heartbeat=25.0, max_msg_size=1024 * 1024)
    await ws.prepare(request)

    scale = preset_scale(preset)
    if preset.lock_win_h:
        init_h = preset.win_h * scale
    else:
        init_h = clamp_win_h(
            request.query.get("h"),
            default=preset.win_h * scale,
            scale=scale,
        )
    session = StreamSession(preset=preset, win_h=init_h)
    idle_ctrl: IdleSleepController | None = request.app.get("idle_ctrl")
    if idle_ctrl is not None:
        await idle_ctrl.register_session(session)

    await ws.send_json(
        {
            "type": "meta",
            "win_w": session.phys_w,
            "win_h": session.win_h,
            "chat_x": session.chat_x,
            "rail_w": preset.rail_w * scale,
            "layout": preset.layout,
        }
    )

    capture_base = request.app["capture_fn"]
    interval = float(request.app.get("frame_interval", 0.20))

    async def streamer() -> None:
        while not ws.closed:
            if session.paused:
                session.wake_event.clear()
                await session.wake_event.wait()
                continue

            try:
                packet, chat_delta = await session.capture_once(
                    lambda: capture_base(session.phys_w, session.win_h)
                )
                if chat_delta is not None and not ws.closed:
                    await ws.send_json({"type": "meta", "chat_x": chat_delta})
                if packet is not None and not ws.closed:
                    await ws.send_bytes(packet)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                LOG.warning("Frame capture error: %s", exc)

            session.wake_event.clear()
            try:
                await asyncio.wait_for(session.wake_event.wait(), timeout=interval)
            except TimeoutError:
                pass

    stream_task = asyncio.create_task(streamer())
    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    payload = json.loads(msg.data)
                except ValueError:
                    continue
                if isinstance(payload, dict):
                    await _dispatch_ws_msg(session, payload, request.app, ws=ws)
            elif msg.type in (WSMsgType.ERROR, WSMsgType.CLOSE):
                break
    finally:
        if idle_ctrl is not None:
            idle_ctrl.unregister_session(session)
        stream_task.cancel()
        await asyncio.gather(stream_task, return_exceptions=True)

    return ws


def create_app(
    preset: Preset | None = None,
    token: str | None = None,
    *,
    capture_fn: Callable[[int, int], Awaitable[Image.Image]] = x11_capture_screen,
    paste_png_fn: Callable[[bytes], Awaitable[None]] | None = None,
    paste_file_fn: Callable[[bytes, str], Awaitable[Path | None]] | None = None,
    paste_text_fn: Callable[[str, Sequence[str] | None], Awaitable[None]] | None = None,
    read_clipboard_fn: Callable[[], Awaitable[str]] = x11_read_clipboard,
    resize_fn: Callable[[int, int], Awaitable[None]] = x11_resize_window,
    click_fn: Callable[[int, int, int], Awaitable[None]] = x11_click,
    wheel_fn: Callable[[int, int, int, str], Awaitable[None]] = x11_wheel,
    key_fn: Callable[[str], Awaitable[None]] = x11_send_key,
    type_fn: Callable[[str], Awaitable[None]] = x11_type_text,
    frame_interval: float = 0.20,
    idle_sleep_seconds: float | None = None,
    suspend_fn: Callable[[], Awaitable[None]] | None = None,
    resume_fn: Callable[[], Awaitable[None]] | None = None,
) -> web.Application:
    """Build configured aiohttp Application instance."""
    resolved_preset = preset or load_preset()
    resolved_token = token or resolve_token()
    resolved_idle = (
        resolve_idle_sleep_seconds(resolved_preset)
        if idle_sleep_seconds is None
        else max(0.0, float(idle_sleep_seconds))
    )

    async def _default_suspend() -> None:
        if resolved_preset.runtime == "chromium":
            _signal_chromium_processes(signal.SIGSTOP)

    async def _default_resume() -> None:
        if resolved_preset.runtime == "chromium":
            _signal_chromium_processes(signal.SIGCONT)

    idle_ctrl = IdleSleepController(
        idle_seconds=resolved_idle,
        suspend_fn=suspend_fn or _default_suspend,
        resume_fn=resume_fn or _default_resume,
    )

    app = web.Application(client_max_size=MAX_UPLOAD_BYTES + 65536)
    app["preset"] = resolved_preset
    app["token"] = resolved_token
    app["capture_fn"] = capture_fn
    app["paste_png_fn"] = (
        paste_png_fn
        if paste_png_fn is not None
        else (lambda b: x11_paste_png(b, paste_keys=resolved_preset.paste_keys))
    )
    app["paste_file_fn"] = (
        paste_file_fn
        if paste_file_fn is not None
        else (lambda b, n: x11_paste_file(b, n, paste_keys=resolved_preset.paste_keys))
    )
    app["paste_text_fn"] = (
        paste_text_fn
        if paste_text_fn is not None
        else (
            lambda t, s=None: x11_paste_text(t, send_keys=s, paste_keys=resolved_preset.paste_keys)
        )
    )
    app["read_clipboard_fn"] = read_clipboard_fn
    app["resize_fn"] = resize_fn
    app["click_fn"] = click_fn
    app["wheel_fn"] = wheel_fn
    app["key_fn"] = key_fn
    app["type_fn"] = type_fn
    app["frame_interval"] = frame_interval
    app["idle_ctrl"] = idle_ctrl

    async def _on_startup(_app: web.Application) -> None:
        idle_ctrl.start()

    async def _on_shutdown(_app: web.Application) -> None:
        await idle_ctrl.shutdown()

    app.on_startup.append(_on_startup)
    app.on_shutdown.append(_on_shutdown)
    app.router.add_get("/", handle_index)
    app.router.add_get("/healthz", handle_healthz)
    app.router.add_get("/icon.png", handle_icon)
    app.router.add_get("/apple-touch-icon.png", handle_icon)
    app.router.add_get("/apple-touch-icon-precomposed.png", handle_icon)
    app.router.add_get("/favicon.ico", handle_icon)
    app.router.add_get("/ws", handle_ws)
    app.router.add_post("/upload", handle_upload)
    return app


def build_ssl_context(cert_file: str | Path, key_file: str | Path) -> ssl.SSLContext:
    """Build TLS 1.2+ server SSL context compatible with BlackBerry 10.3.3."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(certfile=str(cert_file), keyfile=str(key_file))
    return ctx


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    preset = load_preset()
    token = resolve_token()
    app = create_app(preset=preset, token=token)

    cert_file = Path(os.environ.get("CERT_FILE", "/certs/server.crt"))
    key_file = Path(os.environ.get("KEY_FILE", "/certs/server.key"))
    ssl_ctx: ssl.SSLContext | None = None
    if os.environ.get("DISABLE_TLS", "0") != "1" and cert_file.is_file() and key_file.is_file():
        ssl_ctx = build_ssl_context(cert_file, key_file)

    host = os.environ.get("HOST", "0.0.0.0")
    LOG.info(
        "Starting %s on %s:%d (layout=%s, tls=%s)",
        preset.title,
        host,
        preset.port,
        preset.layout,
        bool(ssl_ctx),
    )
    web.run_app(
        app,
        host=host,
        port=preset.port,
        ssl_context=ssl_ctx,
        print=None,
        access_log=None,
    )


if __name__ == "__main__":
    main()
