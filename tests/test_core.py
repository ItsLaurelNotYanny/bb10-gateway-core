"""Unit tests for BB10 Gateway Core presets, 144x144 icon spec, dirty-rect, and clipboard."""

from __future__ import annotations

import asyncio
import io
import struct
from pathlib import Path

import pytest
from aiohttp import WSMsgType
from aiohttp.test_utils import TestClient, TestServer
from PIL import Image, ImageDraw

from gateway import (
    FLAG_FULL,
    FLAG_PATCH,
    FRAME_MAGIC,
    HEADER_STRUCT,
    MAX_UPLOAD_BYTES,
    clamp_win_h,
    create_app,
    detect_chat_x,
    encode_dirty_frame,
    is_allowed_key,
    resolve_chat_x,
    resolve_idle_sleep_seconds,
    resolve_token,
    safe_filename,
    x11_paste_file,
    x11_paste_png,
    x11_paste_text,
)
from icon_gen import generate_icon_bytes
from presets import (
    PRESETS,
    PortAllocation,
    load_preset,
    validate_port_registry,
)

TEST_PRESETS_DIR = str(Path(__file__).parent / "presets.d")


def test_port_registry_collision_detection() -> None:
    with pytest.raises(ValueError, match="Port collision"):
        validate_port_registry(
            (
                PortAllocation("a", 2445, "198.51.100.1", 2445, "A"),
                PortAllocation("b", 2445, "198.51.100.2", 2445, "B"),
            )
        )


def test_presets_defaults_and_overrides() -> None:
    example_preset = load_preset(env={})
    assert example_preset.name == "example"
    assert example_preset.runtime == "chromium"
    assert example_preset.port == 2443

    term_preset = load_preset(env={"PRESET": "term", "PRESETS_DIR": TEST_PRESETS_DIR})
    assert term_preset.name == "term"
    assert term_preset.runtime == "xterm"
    assert term_preset.port == 2445
    assert term_preset.win_w == 720
    assert term_preset.enable_term_bar is True
    assert term_preset.default_type_mode is True
    assert list(term_preset.paste_keys) == ["ctrl+shift+v"]

    wx_preset = load_preset("wechat", env={"ICON_STYLE": "badge", "PRESETS_DIR": TEST_PRESETS_DIR})
    assert wx_preset.name == "wechat"
    assert wx_preset.runtime == "native_gui"
    assert wx_preset.port == 2446
    assert wx_preset.enable_term_bar is False
    assert wx_preset.icon_style == "badge"

    x_preset = load_preset(env={"PRESET": "x"})
    assert x_preset.name == "x"
    assert x_preset.runtime == "chromium"
    assert x_preset.port == 2444
    assert list(x_preset.send_keys) == ["ctrl+Return"]

    dc_preset = load_preset(env={"PRESET": "discord", "PRESETS_DIR": TEST_PRESETS_DIR})
    assert dc_preset.name == "discord"
    assert dc_preset.port == 2443
    assert dc_preset.win_w == 1023
    assert dc_preset.layout == "slim_rail"

    with pytest.raises(ValueError, match="Unknown preset"):
        load_preset("invalid_app", env={})


@pytest.mark.parametrize("app_name", ["term", "wechat", "discord", "x"])
@pytest.mark.parametrize("style", ["slate", "badge"])
def test_icon_144x144_squircle_footprint_spec(app_name: str, style: str) -> None:
    png_bytes = generate_icon_bytes(app_name, style)
    assert png_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    with Image.open(io.BytesIO(png_bytes)) as im:
        assert im.size == (144, 144)
        assert im.mode == "RGBA"
        alpha = im.getchannel("A")
        bbox = alpha.getbbox()
        assert bbox is not None
        # Exact 14px transparent margin on all four sides -> (14, 14, 130, 130)
        assert bbox == (14, 14, 130, 130)
        # Corners of the 144x144 canvas must be 100% transparent
        assert im.getpixel((0, 0))[3] == 0
        assert im.getpixel((13, 13))[3] == 0
        assert im.getpixel((143, 143))[3] == 0
        # Center of the squircle must be opaque
        assert im.getpixel((72, 72))[3] == 255


def test_is_allowed_key_whitelist_and_security() -> None:
    term_preset = PRESETS["term"]
    for safe_key in ("Up", "Down", "Left", "Right", "Return", "BackSpace", "Tab", "Escape", "F1"):
        assert is_allowed_key(safe_key, term_preset) is True
    for safe_combo in ("ctrl+c", "ctrl+b", "alt+b", "ctrl+1"):
        assert is_allowed_key(safe_combo, term_preset) is True
    for bad_key in ("rm -rf /", "$(whoami)", "; reboot", "ctrl+cc", "", None):
        assert is_allowed_key(bad_key, term_preset) is False  # type: ignore[arg-type]


def test_token_resolution_and_clamp(tmp_path: Path) -> None:
    fallback = tmp_path / "token.txt"
    tok = resolve_token(env={}, default_paths=(fallback,))
    assert len(tok) == 24
    assert clamp_win_h(100) == 420
    assert clamp_win_h(2000) == 1080
    assert clamp_win_h("720") == 720


def test_encode_dirty_frame_and_chat_x() -> None:
    base = Image.new("RGB", (200, 100), (20, 20, 20))
    first_pkt = encode_dirty_frame(None, base, quality=70)
    assert first_pkt is not None
    assert HEADER_STRUCT.unpack_from(first_pkt, 0) == (FRAME_MAGIC, FLAG_FULL, 0, 0, 200, 100)

    assert encode_dirty_frame(base, base.copy(), quality=70) is None

    small = base.copy()
    ImageDraw.Draw(small).rectangle([30, 40, 49, 54], fill=(240, 80, 40))
    patch_pkt = encode_dirty_frame(base, small, quality=70)
    assert patch_pkt is not None
    assert struct.unpack(">BBHHHH", patch_pkt[:10]) == (FRAME_MAGIC, FLAG_PATCH, 30, 40, 20, 15)

    from dataclasses import replace

    im = Image.new("RGB", (1064, 680), (30, 31, 34))
    ImageDraw.Draw(im).rectangle([340, 0, 1063, 679], fill=(49, 51, 56))
    assert detect_chat_x(im, default_x=375) == 340
    assert resolve_chat_x(im, replace(PRESETS["discord"], hidpi=False)) == 340
    assert resolve_chat_x(im, PRESETS["term"]) == 0


def test_x11_paste_helpers_invocation(monkeypatch: pytest.MonkeyPatch) -> None:
    async def run_scenario() -> None:
        cmds_run: list[list[str]] = []

        async def fake_run_cmd(*args: str, **kwargs: object) -> None:
            cmds_run.append(list(args))

        monkeypatch.setattr("gateway._run_cmd", fake_run_cmd)
        await x11_paste_png(b"fake_png", paste_keys=("ctrl+shift+v",))
        assert any("ctrl+shift+v" in cmd for cmd in cmds_run)

        cmds_run.clear()
        await x11_paste_text("hello", send_keys=("Return",), paste_keys=("ctrl+shift+v",))
        assert any("ctrl+shift+v" in cmd for cmd in cmds_run)
        assert any("Return" in cmd for cmd in cmds_run)

    asyncio.run(run_scenario())


def test_x11_paste_file_and_safe_filename(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    assert safe_filename("../../etc/passwd") == "passwd"
    assert safe_filename("  ../季度报告 (2026).pdf ") == "季度报告 (2026).pdf"
    assert safe_filename("...") == "attachment.bin"

    async def run_scenario() -> None:
        cmds_run: list[list[str]] = []
        stdin_captured: list[bytes] = []

        async def fake_run_cmd(
            *args: str, stdin_bytes: bytes | None = None, **kwargs: object
        ) -> None:
            cmds_run.append(list(args))
            if stdin_bytes is not None:
                stdin_captured.append(stdin_bytes)

        monkeypatch.setenv("BB10_UPLOAD_DIR", str(tmp_path))
        monkeypatch.setattr("gateway._run_cmd", fake_run_cmd)
        saved = await x11_paste_file(b"%PDF-1.7-test", "../report.pdf", paste_keys=("ctrl+v",))
        assert saved == tmp_path / "report.pdf"
        assert saved.read_bytes() == b"%PDF-1.7-test"
        assert any("text/uri-list" in cmd for cmd in cmds_run)
        assert any("ctrl+v" in cmd for cmd in cmds_run)
        assert stdin_captured and stdin_captured[0].startswith(b"file://")

    asyncio.run(run_scenario())


def test_gateway_ws_clipboard_sync_and_icons() -> None:
    async def run_scenario() -> None:
        sent_keys: list[str] = []
        typed_texts: list[str] = []
        pasted_pngs: list[bytes] = []
        resizes: list[tuple[int, int]] = []

        async def fake_capture(win_w: int, win_h: int) -> Image.Image:
            return Image.new("RGB", (win_w, win_h), (10, 10, 10))

        async def fake_key(key_name: str) -> None:
            sent_keys.append(key_name)

        async def fake_type(text: str) -> None:
            typed_texts.append(text)

        async def fake_paste_png(png_bytes: bytes) -> None:
            pasted_pngs.append(png_bytes)

        async def fake_read_clipboard() -> str:
            return "copied-from-x11-server"

        async def fake_resize(win_w: int, win_h: int) -> None:
            resizes.append((win_w, win_h))

        app = create_app(
            preset=PRESETS["term"],
            token="core-secret-999",
            capture_fn=fake_capture,
            key_fn=fake_key,
            type_fn=fake_type,
            paste_png_fn=fake_paste_png,
            read_clipboard_fn=fake_read_clipboard,
            resize_fn=fake_resize,
            frame_interval=0.05,
        )

        async with TestClient(TestServer(app)) as client:
            hz = await client.get("/healthz")
            assert hz.status == 200
            assert (await hz.json()) == {"ok": True, "preset": "term"}

            unauth = await client.get("/")
            assert unauth.status == 401

            authed = await client.get("/?t=core-secret-999")
            assert authed.status == 200
            assert PRESETS["term"].cookie_name in authed.cookies

            async with client.ws_connect("/ws") as ws:
                meta = await ws.receive_json(timeout=2.0)
                assert meta["type"] == "meta"
                bin_frame = await ws.receive(timeout=2.0)
                assert bin_frame.type == WSMsgType.BINARY

                # Request remote clipboard sync
                await ws.send_json({"type": "clip_get"})
                clip_msg = await ws.receive_json(timeout=2.0)
                assert clip_msg == {"type": "clip_data", "text": "copied-from-x11-server"}

                await ws.send_json({"type": "font", "dir": "up"})
                await ws.send_json({"type": "key", "key": "ctrl+c"})
                await ws.send_json({"type": "type", "text": "echo ok"})
                await asyncio.sleep(0.12)

                assert "shift+KP_Add" in sent_keys
                assert "ctrl+c" in sent_keys
                assert typed_texts == ["echo ok"]

            # Unauthenticated icon endpoints (both slate and badge styles)
            for url in ("/icon.png", "/icon.png?style=badge", "/favicon.ico"):
                icon_resp = await client.get(url)
                assert icon_resp.status == 200
                raw_icon = await icon_resp.read()
                with Image.open(io.BytesIO(raw_icon)) as icon_im:
                    assert icon_im.size == (144, 144)

            # Image upload
            img = Image.new("RGB", (8, 8), (255, 0, 0))
            buf = io.BytesIO()
            img.save(buf, format="JPEG")
            up = await client.post("/upload", data=buf.getvalue())
            assert up.status == 200
            assert len(pasted_pngs) == 1

            # Arbitrary attachment file upload (mode=file)
            pasted_files: list[tuple[bytes, str]] = []

            async def fake_paste_file(raw: bytes, fname: str) -> Path:
                pasted_files.append((raw, fname))
                return Path("/tmp") / fname

            app["paste_file_fn"] = fake_paste_file
            up_file = await client.post(
                "/upload?mode=file&name=invoice_2026.pdf",
                data=b"%PDF-1.7-mock",
            )
            assert up_file.status == 200
            up_json = await up_file.json()
            assert up_json["ok"] is True
            assert up_json["mode"] == "file"
            assert up_json["filename"] == "invoice_2026.pdf"
            assert pasted_files == [(b"%PDF-1.7-mock", "invoice_2026.pdf")]

            too_big = await client.post("/upload", data=b"x" * (MAX_UPLOAD_BYTES + 1))
            assert too_big.status == 413

    asyncio.run(run_scenario())


def test_hidpi_scaling_behavior() -> None:
    from client_html import render_client_html
    from presets import load_preset, preset_scale

    base = load_preset("term", {"PRESETS_DIR": "tests/presets.d"})
    assert base.hidpi is False
    assert preset_scale(base) == 1

    scaled = load_preset("wechat", {"PRESETS_DIR": "tests/presets.d"})
    assert scaled.hidpi is True
    assert preset_scale(scaled) == 2

    forced_off = load_preset("wechat", {"PRESETS_DIR": "tests/presets.d", "HIDPI": "0"})
    assert forced_off.hidpi is False
    assert preset_scale(forced_off) == 1

    assert clamp_win_h(1440, default=1440, scale=2) == 1440
    assert clamp_win_h(3000, default=1440, scale=2) == 2160
    assert clamp_win_h(500, default=1440, scale=2) == 840

    im_2x = Image.new("RGB", (2128, 1360), (30, 31, 34))
    ImageDraw.Draw(im_2x).rectangle([680, 0, 2127, 1359], fill=(49, 51, 56))
    assert detect_chat_x(im_2x, default_x=750, scale=2) == 680

    html = render_client_html(scaled)
    assert '"winW": 1440' in html
    assert '"winH": 1440' in html
    assert '"scale": 2' in html


def test_ws_unauthenticated_logs_warning(caplog: pytest.LogCaptureFixture) -> None:
    async def _run() -> None:
        app = create_app(preset=PRESETS["term"], token="secret-ws-tok", idle_sleep_seconds=0.0)
        async with TestClient(TestServer(app)) as client:
            with caplog.at_level("WARNING", logger="bb10_gateway"):
                resp = await client.get("/ws")
                assert resp.status == 401
        assert any("Rejected unauthenticated /ws" in rec.message for rec in caplog.records)
        assert not any("secret-ws-tok" in rec.message for rec in caplog.records)

    asyncio.run(_run())


def test_idle_sleep_resolution() -> None:
    assert resolve_idle_sleep_seconds(PRESETS["x"], {}) == 30.0
    assert resolve_idle_sleep_seconds(PRESETS["term"], {}) == 0.0
    assert resolve_idle_sleep_seconds(PRESETS["x"], {"IDLE_SLEEP_SECONDS": "0"}) == 0.0
    assert resolve_idle_sleep_seconds(PRESETS["term"], {"IDLE_SLEEP_SECONDS": "15"}) == 15.0
    assert resolve_idle_sleep_seconds(PRESETS["x"], {"IDLE_SLEEP_SECONDS": "bad"}) == 30.0


def test_idle_sleep_and_wake_lifecycle() -> None:
    async def _run() -> None:
        events: list[str] = []

        async def fake_capture(win_w: int, win_h: int) -> Image.Image:
            return Image.new("RGB", (win_w, win_h), (0, 0, 0))

        async def fake_suspend() -> None:
            events.append("suspend")

        async def fake_resume() -> None:
            events.append("resume")

        app = create_app(
            preset=PRESETS["x"],
            token="idle-secret-123",
            capture_fn=fake_capture,
            frame_interval=0.05,
            idle_sleep_seconds=0.08,
            suspend_fn=fake_suspend,
            resume_fn=fake_resume,
        )

        async with TestClient(TestServer(app)) as client:
            # 1. No clients on startup -> suspends after idle timeout
            await asyncio.sleep(0.14)
            assert events == ["suspend"]
            assert app["idle_ctrl"].sleeping is True

            # 2. Authenticated GET / wakes the app before /ws connects
            resp = await client.get("/?t=idle-secret-123")
            assert resp.status == 200
            assert events == ["suspend", "resume"]
            assert app["idle_ctrl"].sleeping is False

            # 3. Active WS keeps app awake past the idle timeout
            async with client.ws_connect("/ws") as ws:
                await ws.receive_json(timeout=2.0)
                await asyncio.sleep(0.12)
                assert events == ["suspend", "resume"]

                # 4. Pausing the only client suspends after idle timeout
                await ws.send_json({"type": "pause", "paused": True})
                await asyncio.sleep(0.14)
                assert events == ["suspend", "resume", "suspend"]

                # 5. Unpausing resumes immediately
                await ws.send_json({"type": "pause", "paused": False})
                await asyncio.sleep(0.04)
                assert events == ["suspend", "resume", "suspend", "resume"]

            # 6. Disconnecting WS suspends again after idle timeout
            await asyncio.sleep(0.25)
            assert events == ["suspend", "resume", "suspend", "resume", "suspend"]

        # 7. Server shutdown while sleeping resumes processes cleanly
        assert events == ["suspend", "resume", "suspend", "resume", "suspend", "resume"]

    asyncio.run(_run())
