"""Unified BB10 144x144 native squircle icon generator (Slate & Badge editions).

Follows the exact launcher visual specification from LocalSend-BB10, Passport Weather,
and Todoist on Passport:
- Canvas: 144x144 RGBA transparent PNG.
- Margin: 14px transparent inset on all four sides (active base at 14..130).
- Base Footprint: 116x116 squircle with 26px corner radius.
- Supersampling: 4x vector rasterization (576x576) downsampled via Lanczos to 144x144.
- Styles:
  1. 'slate': Matte dark slate-gray vertical gradient (#262C32 -> #14181C) with flat
     color iconography (LocalSend / Passport Weather family style).
  2. 'badge': Brand vertical gradient squircle with white iconography and bottom-right
     BlackBerry 7-dot fruit emblem (< 1/4 area, Todoist community port style).
"""

from __future__ import annotations

import argparse
import io
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw

CANVAS_SIZE = 144
BASE_OFFSET = 14
BASE_SIZE = 116
BASE_RADIUS = 26
SCALE = 4
SS_SIZE = CANVAS_SIZE * SCALE
TRANSPARENT = (0, 0, 0, 0)


def _hex_rgb(hex_str: str) -> tuple[int, int, int]:
    h = hex_str.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _hex_rgba(hex_str: str, alpha: int = 255) -> tuple[int, int, int, int]:
    r, g, b = _hex_rgb(hex_str)
    return (r, g, b, alpha)


def _create_vertical_gradient(size: int, top_hex: str, bottom_hex: str) -> Image.Image:
    """Create a vertical linear gradient RGBA image of size x size."""
    top_r, top_g, top_b = _hex_rgb(top_hex)
    bot_r, bot_g, bot_b = _hex_rgb(bottom_hex)
    grad = Image.new("RGBA", (1, size))
    pixels = []
    b0 = BASE_OFFSET * SCALE
    b1 = (BASE_OFFSET + BASE_SIZE) * SCALE
    span = max(1, b1 - b0)
    for y in range(size):
        t = max(0.0, min(1.0, (y - b0) / span))
        r = int(top_r + (bot_r - top_r) * t)
        g = int(top_g + (bot_g - top_g) * t)
        b = int(top_b + (bot_b - top_b) * t)
        pixels.append((r, g, b, 255))
    grad.putdata(pixels)
    return grad.resize((size, size), Image.Resampling.NEAREST)


def _draw_squircle_base(
    top_hex: str,
    bottom_hex: str,
    rim_hex: str | None = None,
) -> tuple[Image.Image, Image.Image]:
    """Render 576x576 supersampled squircle base within (56, 56, 520, 520)."""
    canvas = Image.new("RGBA", (SS_SIZE, SS_SIZE), TRANSPARENT)
    x0 = BASE_OFFSET * SCALE
    y0 = BASE_OFFSET * SCALE
    x1 = (BASE_OFFSET + BASE_SIZE) * SCALE - 1
    y1 = (BASE_OFFSET + BASE_SIZE) * SCALE - 1
    rad = BASE_RADIUS * SCALE

    mask = Image.new("L", (SS_SIZE, SS_SIZE), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([x0, y0, x1, y1], radius=rad, fill=255)

    grad = _create_vertical_gradient(SS_SIZE, top_hex, bottom_hex)
    canvas.paste(grad, (0, 0), mask)

    if rim_hex:
        draw = ImageDraw.Draw(canvas)
        draw.rounded_rectangle(
            [x0 + 2, y0 + 2, x1 - 2, y1 - 2],
            radius=rad - 2,
            outline=_hex_rgba(rim_hex, 110),
            width=SCALE,
        )
    return canvas, mask


def _draw_bb_emblem(draw: ImageDraw.ImageDraw, bx: float, by: float, scale: float) -> None:
    """Draw the authentic 7-dot BlackBerry fruit emblem in logical 144x144 coordinates."""
    dots = (
        (0.0, 1.8),
        (0.0, 5.6),
        (4.8, 0.6),
        (4.8, 4.4),
        (4.8, 8.2),
        (9.6, 2.5),
        (9.6, 6.3),
    )
    w = 3.5 * scale * SCALE
    h = 2.4 * scale * SCALE
    r = 0.9 * scale * SCALE
    for dx, dy in dots:
        px = (bx + dx * scale) * SCALE
        py = (by + dy * scale) * SCALE
        draw.rounded_rectangle(
            [px, py, px + w, py + h],
            radius=r,
            fill=(255, 255, 255, 248),
        )


def _draw_term_motif(draw: ImageDraw.ImageDraw, style: str) -> None:
    s = SCALE
    if style == "slate":
        draw.ellipse([28 * s, 28 * s, 36 * s, 36 * s], fill=_hex_rgba("#F85149"))
        draw.ellipse([42 * s, 28 * s, 50 * s, 36 * s], fill=_hex_rgba("#D29922"))
        draw.ellipse([56 * s, 28 * s, 64 * s, 36 * s], fill=_hex_rgba("#3FB950"))
        draw.line([24 * s, 44 * s, 120 * s, 44 * s], fill=_hex_rgba("#38414A"), width=2 * s)
        chevron_color = _hex_rgba("#3FB950")
        cursor_color = _hex_rgba("#58A6FF")
        y_shift = 6
    else:
        chevron_color = (255, 255, 255, 255)
        cursor_color = _hex_rgba("#56F068")
        y_shift = -4

    pts_top = [
        (36 * s, (58 + y_shift) * s),
        (43 * s, (51 + y_shift) * s),
        (72 * s, (76 + y_shift) * s),
        (65 * s, (83 + y_shift) * s),
    ]
    pts_bot = [
        (65 * s, (69 + y_shift) * s),
        (72 * s, (76 + y_shift) * s),
        (43 * s, (101 + y_shift) * s),
        (36 * s, (94 + y_shift) * s),
    ]
    draw.polygon(pts_top, fill=chevron_color)
    draw.polygon(pts_bot, fill=chevron_color)

    cx0, cy0 = 76 * s, (86 + y_shift) * s
    cx1, cy1 = 108 * s, (98 + y_shift) * s
    draw.rounded_rectangle([cx0, cy0, cx1, cy1], radius=3 * s, fill=cursor_color)


def _draw_wechat_motif(draw: ImageDraw.ImageDraw, style: str) -> None:
    s = SCALE
    back_color = _hex_rgba("#07C160") if style == "slate" else (255, 255, 255, 255)
    front_color = (255, 255, 255, 255) if style == "slate" else _hex_rgba("#E8FFF1")

    # Back bubble (upper-left)
    bx0, by0, bx1, by1 = 26 * s, 34 * s, 90 * s, 84 * s
    draw.ellipse([bx0, by0, bx1, by1], fill=back_color)
    draw.polygon([(34 * s, 76 * s), (28 * s, 90 * s), (48 * s, 80 * s)], fill=back_color)
    # True transparent negative-space eyes on back bubble
    draw.ellipse([44 * s, 50 * s, 51 * s, 57 * s], fill=TRANSPARENT)
    draw.ellipse([64 * s, 50 * s, 71 * s, 57 * s], fill=TRANSPARENT)

    # True transparent negative-space cutout around front bubble
    fx0, fy0, fx1, fy1 = 58 * s, 56 * s, 116 * s, 102 * s
    pad = 4 * s
    draw.ellipse([fx0 - pad, fy0 - pad, fx1 + pad, fy1 + pad], fill=TRANSPARENT)

    # Front bubble (lower-right)
    draw.ellipse([fx0, fy0, fx1, fy1], fill=front_color)
    draw.polygon([(106 * s, 94 * s), (114 * s, 107 * s), (94 * s, 98 * s)], fill=front_color)
    # True transparent negative-space eyes on front bubble
    draw.ellipse([73 * s, 72 * s, 79 * s, 78 * s], fill=TRANSPARENT)
    draw.ellipse([93 * s, 72 * s, 99 * s, 78 * s], fill=TRANSPARENT)


def _draw_discord_motif(draw: ImageDraw.ImageDraw, style: str) -> None:
    s = SCALE
    fg = _hex_rgba("#5865F2") if style == "slate" else (255, 255, 255, 255)
    eye = (255, 255, 255, 255) if style == "slate" else TRANSPARENT

    # Outer chat/controller visor body
    draw.rounded_rectangle([32 * s, 42 * s, 112 * s, 96 * s], radius=22 * s, fill=fg)
    # Lower controller grips
    draw.ellipse([30 * s, 72 * s, 58 * s, 104 * s], fill=fg)
    draw.ellipse([86 * s, 72 * s, 114 * s, 104 * s], fill=fg)
    # True transparent cutouts revealing the underlying squircle gradient cleanly
    draw.ellipse([54 * s, 88 * s, 90 * s, 114 * s], fill=TRANSPARENT)
    draw.ellipse([58 * s, 32 * s, 86 * s, 46 * s], fill=TRANSPARENT)

    # Crisp visor eyes
    draw.ellipse([48 * s, 58 * s, 64 * s, 76 * s], fill=eye)
    draw.ellipse([80 * s, 58 * s, 96 * s, 76 * s], fill=eye)


def _draw_x_motif(draw: ImageDraw.ImageDraw) -> None:
    s = SCALE
    fg = (255, 255, 255, 255)

    # Diagonal 1: Top-right to bottom-left
    draw.polygon(
        [
            (96 * s, 36 * s),
            (106 * s, 36 * s),
            (48 * s, 108 * s),
            (38 * s, 108 * s),
        ],
        fill=fg,
    )
    # Diagonal 2: Top-left to bottom-right with true transparent core cutout
    outer = [
        (36 * s, 36 * s),
        (58 * s, 36 * s),
        (108 * s, 108 * s),
        (86 * s, 108 * s),
    ]
    inner = [
        (45 * s, 42 * s),
        (53 * s, 42 * s),
        (99 * s, 102 * s),
        (91 * s, 102 * s),
    ]
    draw.polygon(outer, fill=fg)
    draw.polygon(inner, fill=TRANSPARENT)


@lru_cache(maxsize=32)
def generate_icon_bytes(preset_name: str = "term", style: str = "slate") -> bytes:
    """Render 144x144 RGBA PNG icon bytes for a preset ('slate' or 'badge' style)."""
    key = preset_name.strip().lower()
    if key == "terminal":
        key = "term"
    mode = style.strip().lower() if style in ("slate", "badge") else "slate"

    if mode == "slate":
        top_hex, bot_hex, rim_hex = "#262C32", "#14181C", "#38414A"
    else:
        palettes = {
            "term": ("#153022", "#0A1710", "#2EA043"),
            "wechat": ("#1AD66C", "#059E4C", "#52E593"),
            "discord": ("#6E7BF2", "#4752C4", "#8B96F8"),
            "x": ("#272C33", "#0B0D10", "#3D444D"),
        }
        top_hex, bot_hex, rim_hex = palettes.get(key, ("#262C32", "#14181C", "#38414A"))

    base_canvas, mask = _draw_squircle_base(top_hex, bot_hex, rim_hex=rim_hex)

    # Render motif onto an isolated transparent layer so negative-space cutouts
    # reveal the exact vertical gradient of base_canvas without flat patches.
    motif_layer = Image.new("RGBA", (SS_SIZE, SS_SIZE), TRANSPARENT)
    motif_draw = ImageDraw.Draw(motif_layer)

    if key == "wechat":
        _draw_wechat_motif(motif_draw, mode)
    elif key == "discord":
        _draw_discord_motif(motif_draw, mode)
    elif key == "x":
        _draw_x_motif(motif_draw)
    else:
        _draw_term_motif(motif_draw, mode)

    if mode == "badge":
        # Carve negative-space halo in motif_layer for bottom-right BlackBerry emblem
        motif_draw.rounded_rectangle(
            [91 * SCALE, 93 * SCALE, 127 * SCALE, 125 * SCALE],
            radius=8 * SCALE,
            fill=TRANSPARENT,
        )
        _draw_bb_emblem(motif_draw, bx=96.0, by=97.0, scale=1.95)

    base_canvas.alpha_composite(motif_layer)

    # Re-apply squircle mask so no motif or badge bleeds outside the 116x116 squircle
    clipped = Image.new("RGBA", (SS_SIZE, SS_SIZE), TRANSPARENT)
    clipped.paste(base_canvas, (0, 0), mask)

    final_img = clipped.resize((CANVAS_SIZE, CANVAS_SIZE), Image.Resampling.LANCZOS)
    # Strip any 1-2px Lanczos ringing outside the strict (14..130) 116x116 footprint
    bounds_mask = Image.new("L", (CANVAS_SIZE, CANVAS_SIZE), 0)
    ImageDraw.Draw(bounds_mask).rectangle(
        [BASE_OFFSET, BASE_OFFSET, BASE_OFFSET + BASE_SIZE - 1, BASE_OFFSET + BASE_SIZE - 1],
        fill=255,
    )
    clean_img = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), TRANSPARENT)
    clean_img.paste(final_img, (0, 0), bounds_mask)

    buf = io.BytesIO()
    clean_img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def export_icon_suite(output_dir: str | Path) -> list[Path]:
    """Export all 4 presets in both 'slate' and 'badge' styles plus a comparison board."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    apps = ("term", "wechat", "discord", "x")
    styles = ("slate", "badge")

    board = Image.new("RGBA", (4 * 168 + 24, 2 * 168 + 24), _hex_rgba("#0D1117"))

    for row_idx, st in enumerate(styles):
        for col_idx, app in enumerate(apps):
            png_bytes = generate_icon_bytes(app, st)
            file_path = out_path / f"{app}_{st}_144.png"
            file_path.write_bytes(png_bytes)
            written.append(file_path)

            icon_im = Image.open(io.BytesIO(png_bytes))
            px = 24 + col_idx * 168
            py = 24 + row_idx * 168
            board.alpha_composite(icon_im, (px, py))

    board_path = out_path / "comparison_slate_vs_badge.png"
    board.save(board_path, format="PNG")
    written.append(board_path)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate BB10 144x144 squircle icons.")
    parser.add_argument("--output-dir", default="./icons_preview")
    args = parser.parse_args()
    paths = export_icon_suite(args.output_dir)
    for p in paths:
        print(f"Generated: {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
