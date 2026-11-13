"""Declarative application presets for BB10 Gateway Core."""

from __future__ import annotations

import os
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import MISSING, dataclass, fields, replace
from pathlib import Path
from typing import Any

RESERVED_PORT_RANGE = range(2447, 2451)


@dataclass(frozen=True)
class PortAllocation:
    """Single source of truth for a VPS L4 TCP relay port assignment."""

    service: str
    listen_port: int
    target_host: str
    upstream_port: int
    host_label: str
    protocol: str = "tls"
    active: bool = True


@dataclass(frozen=True)
class Preset:
    """Declarative configuration for a BB10 WebKit Gateway application.

    All BB10 display, DPR=2 canvas compositing, dirty-rect streaming, screen-lock
    pause lifecycle, Dual-Track Input Engine, X11 sandbox, and 144x144 squircle icon
    specs are normalized in the core engine; only the fields below vary per app.
    """

    name: str
    title: str
    short_title: str
    runtime: str
    target_url: str
    port: int
    win_w: int
    win_h: int
    layout: str
    rail_w: int
    default_chat_x: int
    send_keys: tuple[str, ...]
    cookie_name: str
    passthrough_keys: frozenset[str]
    paste_keys: tuple[str, ...] = ("ctrl+v",)
    default_type_mode: bool = False
    enable_term_bar: bool = False
    lock_win_h: bool = False
    jpeg_quality: int = 85
    icon_style: str = "slate"
    upstream_host: str = ""


VALID_RUNTIMES = ("chromium", "xterm", "native_gui")
VALID_LAYOUTS = ("direct", "slim_rail")
VALID_ICON_STYLES = ("slate", "badge")
_LIST_FIELDS = ("send_keys", "paste_keys", "passthrough_keys")
_FIELD_NAMES = frozenset(f.name for f in fields(Preset))
_REQUIRED = frozenset(
    f.name
    for f in fields(Preset)
    if f.default is MISSING and f.default_factory is MISSING  # type: ignore[misc]
)

BUILTIN_DIR = Path(__file__).resolve().parent / "presets"
DEFAULT_EXTRA_DIR = "/app/presets.d"


def _read_toml_dir(directory: Path) -> dict[str, dict[str, Any]]:
    """Read every *.toml in a directory into raw dicts keyed by preset name."""
    raw: dict[str, dict[str, Any]] = {}
    if not directory.is_dir():
        return raw
    for path in sorted(directory.glob("*.toml")):
        with path.open("rb") as fh:
            data = tomllib.load(fh)
        if "name" in data:
            if not isinstance(data["name"], str):
                raise TypeError(
                    f"{path}: preset name must be a string, got {type(data['name']).__name__}"
                )
            name = data["name"].strip().lower()
            if not name:
                raise ValueError(f"{path}: preset name cannot be empty")
        else:
            name = path.stem.strip().lower()
        data["name"] = name
        raw[name] = data
    return raw


_INT_FIELDS = ("port", "win_w", "win_h", "rail_w", "default_chat_x")
_BOOL_FIELDS = ("default_type_mode", "enable_term_bar", "lock_win_h")
_STR_FIELDS = ("name", "title", "short_title", "target_url", "cookie_name", "upstream_host")


def _build(raw: dict[str, Any], source: str) -> Preset:
    unknown = set(raw) - _FIELD_NAMES - {"base"}
    if unknown:
        raise ValueError(f"{source}: unknown preset keys: {sorted(unknown)}")
    data = {k: v for k, v in raw.items() if k != "base"}
    missing = _REQUIRED - set(data)
    if missing:
        raise ValueError(f"{source}: missing required keys: {sorted(missing)}")

    for key in _STR_FIELDS:
        if key in data and not isinstance(data[key], str):
            raise TypeError(f"{source}: {key} must be a string, got {type(data[key]).__name__}")
    for key in _INT_FIELDS:
        if key in data:
            if not isinstance(data[key], int) or isinstance(data[key], bool):
                raise TypeError(
                    f"{source}: {key} must be an integer, got {type(data[key]).__name__}"
                )
    for key in _BOOL_FIELDS:
        if key in data and not isinstance(data[key], bool):
            raise TypeError(f"{source}: {key} must be a boolean, got {type(data[key]).__name__}")

    for key in _LIST_FIELDS:
        if key in data:
            if not isinstance(data[key], list) or not all(isinstance(x, str) for x in data[key]):
                raise ValueError(f"{source}: {key} must be a list of strings")
            data[key] = frozenset(data[key]) if key == "passthrough_keys" else tuple(data[key])
    if not 1 <= data["port"] <= 65535:
        raise ValueError(f"{source}: port out of range: {data['port']}")
    if data["win_w"] <= 0 or data["win_h"] <= 0:
        raise ValueError(f"{source}: window dimensions must be positive")
    if data["rail_w"] < 0 or data["default_chat_x"] < 0:
        raise ValueError(f"{source}: rail_w and default_chat_x cannot be negative")
    if data["runtime"] not in VALID_RUNTIMES:
        raise ValueError(f"{source}: invalid runtime {data['runtime']!r}")
    if data["layout"] not in VALID_LAYOUTS:
        raise ValueError(f"{source}: invalid layout {data['layout']!r}")
    if data.get("icon_style", "slate") not in VALID_ICON_STYLES:
        raise ValueError(f"{source}: invalid icon_style {data['icon_style']!r}")
    if "jpeg_quality" in data:
        if not isinstance(data["jpeg_quality"], int) or isinstance(data["jpeg_quality"], bool):
            actual = type(data["jpeg_quality"]).__name__
            raise TypeError(f"{source}: jpeg_quality must be an integer, got {actual}")
        data["jpeg_quality"] = max(10, min(95, data["jpeg_quality"]))
    return Preset(**data)


def load_presets(extra_dirs: Sequence[Path] = ()) -> dict[str, Preset]:
    """Load built-in presets, then each extra directory; later entries replace earlier ones."""
    layers: list[dict[str, dict[str, Any]]] = [_read_toml_dir(BUILTIN_DIR)]
    for directory in extra_dirs:
        layers.append(_read_toml_dir(Path(directory)))

    all_names: list[str] = []
    for layer in layers:
        for name in layer:
            if name not in all_names:
                all_names.append(name)

    memo: dict[tuple[int, str], Preset] = {}

    def resolve_in_layer(
        name: str, layer_idx: int, stack: tuple[tuple[int, str], ...] = ()
    ) -> Preset:
        key = (layer_idx, name)
        if key in memo:
            return memo[key]
        if key in stack:
            chain_names = [n for _, n in stack] + [name]
            raise ValueError(f"Circular base chain: {' -> '.join(chain_names)}")

        raw = dict(layers[layer_idx][name])
        base = raw.get("base")
        if base:
            base = str(base).strip().lower()
            target_layer = None
            if base == name:
                for l_idx in range(layer_idx - 1, -1, -1):
                    if base in layers[l_idx]:
                        target_layer = l_idx
                        break
                if target_layer is None:
                    chain_names = [n for _, n in stack] + [name, base]
                    raise ValueError(f"Circular base chain: {' -> '.join(chain_names)}")
            else:
                for l_idx in range(len(layers) - 1, -1, -1):
                    if base in layers[l_idx]:
                        target_layer = l_idx
                        break
                if target_layer is None:
                    raise ValueError(f"Preset {name!r}: unknown base {base!r}")

            base_preset = resolve_in_layer(base, target_layer, (*stack, key))
            merged = {f.name: getattr(base_preset, f.name) for f in fields(Preset)}
            for k in ("passthrough_keys", "send_keys", "paste_keys"):
                merged[k] = sorted(merged[k]) if k == "passthrough_keys" else list(merged[k])
            merged.update({k: v for k, v in raw.items() if k != "base"})
            raw = merged

        preset = _build(raw, f"preset {name!r}")
        memo[key] = preset
        return preset

    result: dict[str, Preset] = {}
    for name in all_names:
        for l_idx in range(len(layers) - 1, -1, -1):
            if name in layers[l_idx]:
                result[name] = resolve_in_layer(name, l_idx)
                break

    return result


def _extra_dirs(env: Mapping[str, str] | None = None) -> list[Path]:
    if env is None:
        custom = os.environ.get("PRESETS_DIR", "").strip()
        if not custom:
            return [Path(DEFAULT_EXTRA_DIR)]
        return [Path(p.strip()) for p in custom.split(":") if p.strip()]

    if "PRESETS_DIR" in env:
        custom = env["PRESETS_DIR"].strip()
        if not custom:
            return []
        return [Path(p.strip()) for p in custom.split(":") if p.strip()]

    return [Path(DEFAULT_EXTRA_DIR)]


PRESETS: dict[str, Preset] = load_presets(_extra_dirs(None))


def validate_port_registry(
    registry: tuple[PortAllocation, ...],
) -> None:
    """Verify zero port or service-name collisions across the ecosystem."""
    seen_ports: dict[int, str] = {}
    seen_services: set[str] = set()
    for entry in registry:
        if entry.service in seen_services:
            raise ValueError(f"Duplicate service name in registry: {entry.service}")
        if entry.listen_port in seen_ports:
            other = seen_ports[entry.listen_port]
            raise ValueError(f"Port collision on {entry.listen_port}: {entry.service} vs {other}")
        if not (1 <= entry.listen_port <= 65535 and 1 <= entry.upstream_port <= 65535):
            raise ValueError(f"Invalid port number for {entry.service}: {entry.listen_port}")
        seen_services.add(entry.service)
        seen_ports[entry.listen_port] = entry.service


def load_preset(
    preset_name: str | None = None,
    env: Mapping[str, str] | None = None,
) -> Preset:
    """Load a named preset (PRESET env, default 'example') and apply env overrides."""
    source_env = os.environ if env is None else env
    key = (preset_name or source_env.get("PRESET", "example")).strip().lower() or "example"
    if key == "terminal":
        key = "term"

    extra = _extra_dirs(env)
    presets = load_presets(extra)

    if key not in presets:
        raise ValueError(f"Unknown preset: {key!r} (expected one of {sorted(presets)})")

    preset = presets[key]
    target_url = source_env.get("TARGET_URL", "").strip() or preset.target_url
    port = int(source_env["PORT"]) if source_env.get("PORT", "").strip() else preset.port
    win_w = int(source_env["WIN_W"]) if source_env.get("WIN_W", "").strip() else preset.win_w
    win_h = int(source_env["WIN_H"]) if source_env.get("WIN_H", "").strip() else preset.win_h
    jpeg_quality = (
        max(10, min(95, int(source_env["JPEG_QUALITY"])))
        if source_env.get("JPEG_QUALITY", "").strip()
        else preset.jpeg_quality
    )
    icon_style = source_env.get("ICON_STYLE", "").strip().lower() or preset.icon_style
    if icon_style not in ("slate", "badge"):
        icon_style = preset.icon_style

    upstream_host = source_env.get("UPSTREAM_HOST", "").strip() or preset.upstream_host

    return replace(
        preset,
        upstream_host=upstream_host,
        target_url=target_url,
        port=port,
        win_w=win_w,
        win_h=win_h,
        jpeg_quality=jpeg_quality,
        icon_style=icon_style,
    )
