"""Tests for TOML preset loading, schema validation, inheritance, and overrides."""

from __future__ import annotations

from pathlib import Path

import pytest

from presets import Preset, load_preset, load_presets


def test_load_builtins() -> None:
    presets = load_presets()
    assert "example" in presets
    assert "x" in presets

    example = presets["example"]
    assert example.name == "example"
    assert example.runtime == "chromium"
    assert example.port == 2443
    assert example.layout == "direct"
    assert example.jpeg_quality == 85
    assert example.icon_style == "slate"
    assert isinstance(example.passthrough_keys, frozenset)
    assert isinstance(example.send_keys, tuple)
    assert isinstance(example.paste_keys, tuple)
    assert example.paste_keys == ("ctrl+v",)

    x = presets["x"]
    assert x.name == "x"
    assert x.runtime == "chromium"
    assert x.port == 2444
    assert x.target_url == "https://x.com/home"
    assert "slash" in x.passthrough_keys


def test_extra_dir_override(tmp_path: Path) -> None:
    override_file = tmp_path / "x.toml"
    override_file.write_text(
        """
name = "x"
base = "x"
title = "Overridden X"
port = 2499
"""
    )
    # With extra_dirs, x should have the overridden port and title,
    # but keep other fields from builtin x
    presets = load_presets([tmp_path])
    assert presets["x"].title == "Overridden X"
    assert presets["x"].port == 2499
    assert presets["x"].target_url == "https://x.com/home"
    assert presets["x"].runtime == "chromium"


def test_base_inheritance_new_preset(tmp_path: Path) -> None:
    custom_file = tmp_path / "custom.toml"
    custom_file.write_text(
        """
name = "custom"
base = "x"
title = "Custom App"
port = 3000
target_url = "https://example.org/custom"
"""
    )
    presets = load_presets([tmp_path])
    assert "custom" in presets
    custom = presets["custom"]
    assert custom.name == "custom"
    assert custom.title == "Custom App"
    assert custom.port == 3000
    assert custom.target_url == "https://example.org/custom"
    assert custom.runtime == "chromium"
    assert custom.layout == "direct"
    assert custom.cookie_name == "bb10_x_auth"
    assert "slash" in custom.passthrough_keys


def test_base_inheritance_chain(tmp_path: Path) -> None:
    child_file = tmp_path / "child.toml"
    child_file.write_text(
        """
name = "child"
base = "x"
title = "Child App"
port = 3001
"""
    )
    grandchild_file = tmp_path / "grandchild.toml"
    grandchild_file.write_text(
        """
name = "grandchild"
base = "child"
title = "Grandchild App"
port = 3002
"""
    )
    presets = load_presets([tmp_path])
    assert presets["grandchild"].title == "Grandchild App"
    assert presets["grandchild"].port == 3002
    assert presets["grandchild"].runtime == "chromium"
    assert presets["grandchild"].target_url == "https://x.com/home"


def test_unknown_base_raises(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad.toml"
    bad_file.write_text(
        """
name = "bad"
base = "nonexistent_preset"
title = "Bad"
"""
    )
    with pytest.raises(ValueError, match="unknown base 'nonexistent_preset'"):
        load_presets([tmp_path])


def test_circular_base_raises(tmp_path: Path) -> None:
    a_file = tmp_path / "a.toml"
    b_file = tmp_path / "b.toml"
    a_file.write_text('name = "a"\nbase = "b"\n')
    b_file.write_text('name = "b"\nbase = "a"\n')

    with pytest.raises(ValueError, match="Circular base chain"):
        load_presets([tmp_path])

    # Self-reference
    self_file = tmp_path / "self.toml"
    self_file.write_text('name = "self"\nbase = "self"\n')
    with pytest.raises(ValueError, match="Circular base chain"):
        load_presets([tmp_path])


def test_unknown_keys_rejection(tmp_path: Path) -> None:
    bad_file = tmp_path / "extra_key.toml"
    bad_file.write_text(
        """
name = "extra_key"
base = "x"
unrecognized_field = "oops"
"""
    )
    with pytest.raises(ValueError, match="unknown preset keys"):
        load_presets([tmp_path])


def test_missing_required_keys_without_base(tmp_path: Path) -> None:
    bad_file = tmp_path / "incomplete.toml"
    bad_file.write_text(
        """
name = "incomplete"
title = "Incomplete"
port = 2443
"""
    )
    with pytest.raises(ValueError, match="missing required keys"):
        load_presets([tmp_path])


@pytest.mark.parametrize("port", [0, -1, 65536, 100000])
def test_port_out_of_range(tmp_path: Path, port: int) -> None:
    f = tmp_path / "bad_port.toml"
    f.write_text(
        f"""
name = "bad_port"
base = "x"
port = {port}
"""
    )
    with pytest.raises(ValueError, match="port out of range"):
        load_presets([tmp_path])


def test_invalid_runtime_and_layout(tmp_path: Path) -> None:
    f1 = tmp_path / "bad_rt.toml"
    f1.write_text(
        """
name = "bad_rt"
base = "x"
runtime = "unsupported_runtime"
"""
    )
    with pytest.raises(ValueError, match="invalid runtime"):
        load_presets([tmp_path])

    f1.unlink()
    f2 = tmp_path / "bad_layout.toml"
    f2.write_text(
        """
name = "bad_layout"
base = "x"
layout = "unsupported_layout"
"""
    )
    with pytest.raises(ValueError, match="invalid layout"):
        load_presets([tmp_path])


def test_invalid_icon_style(tmp_path: Path) -> None:
    f = tmp_path / "bad_icon.toml"
    f.write_text(
        """
name = "bad_icon"
base = "x"
icon_style = "neon"
"""
    )
    with pytest.raises(ValueError, match="invalid icon_style"):
        load_presets([tmp_path])


def test_invalid_list_fields(tmp_path: Path) -> None:
    f = tmp_path / "bad_list.toml"
    f.write_text(
        """
name = "bad_list"
base = "x"
send_keys = "not_a_list"
"""
    )
    with pytest.raises(ValueError, match="send_keys must be a list of strings"):
        load_presets([tmp_path])

    f.write_text(
        """
name = "bad_list"
base = "x"
send_keys = [123, 456]
"""
    )
    with pytest.raises(ValueError, match="send_keys must be a list of strings"):
        load_presets([tmp_path])


def test_jpeg_quality_clamping(tmp_path: Path) -> None:
    f1 = tmp_path / "clamp_low.toml"
    f1.write_text(
        """
name = "clamp_low"
base = "x"
jpeg_quality = 1
"""
    )
    presets = load_presets([tmp_path])
    assert presets["clamp_low"].jpeg_quality == 10

    f2 = tmp_path / "clamp_high.toml"
    f2.write_text(
        """
name = "clamp_high"
base = "x"
jpeg_quality = 150
"""
    )
    presets = load_presets([tmp_path])
    assert presets["clamp_high"].jpeg_quality == 95


def test_load_preset_env_overrides(tmp_path: Path) -> None:
    # Test load_preset with PRESETS_DIR set to tmp_path
    f = tmp_path / "custom.toml"
    f.write_text(
        """
name = "custom"
base = "x"
port = 2500
"""
    )
    env = {
        "PRESETS_DIR": str(tmp_path),
        "PRESET": "custom",
        "PORT": "2501",
        "TARGET_URL": "https://overridden.url",
        "WIN_W": "800",
        "WIN_H": "600",
        "JPEG_QUALITY": "90",
        "ICON_STYLE": "badge",
        "UPSTREAM_HOST": "198.51.100.99",
    }
    p = load_preset(env=env)
    assert isinstance(p, Preset)
    assert p.name == "custom"
    assert p.port == 2501
    assert p.target_url == "https://overridden.url"
    assert p.win_w == 800
    assert p.win_h == 600
    assert p.jpeg_quality == 90
    assert p.icon_style == "badge"
    assert p.upstream_host == "198.51.100.99"


def test_scalar_type_validation_rejects_malformed_values(tmp_path: Path) -> None:
    # win_w as string instead of int
    f1 = tmp_path / "str_w.toml"
    f1.write_text('name = "str_w"\nbase = "x"\nwin_w = "720"\n')
    with pytest.raises(TypeError, match="win_w must be an integer"):
        load_presets([tmp_path])
    f1.unlink()

    # port as float instead of int
    f2 = tmp_path / "float_port.toml"
    f2.write_text('name = "float_port"\nbase = "x"\nport = 2444.5\n')
    with pytest.raises(TypeError, match="port must be an integer"):
        load_presets([tmp_path])
    f2.unlink()

    # enable_term_bar as string instead of bool
    f3 = tmp_path / "str_bool.toml"
    f3.write_text('name = "str_bool"\nbase = "x"\nenable_term_bar = "false"\n')
    with pytest.raises(TypeError, match="enable_term_bar must be a boolean"):
        load_presets([tmp_path])
    f3.unlink()


def test_explicit_env_isolates_from_ambient_process_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Ambient process environment exports PORT and TARGET_URL
    monkeypatch.setenv("PORT", "5555")
    monkeypatch.setenv("TARGET_URL", "https://ambient.example")

    # Explicit empty env must NOT inherit ambient overrides
    p = load_preset("x", env={})
    assert p.port == 2444
    assert p.target_url == "https://x.com/home"


def test_preset_name_validation_and_omitted_inference(tmp_path: Path) -> None:
    # 1. Non-string name (int, bool, list, table)
    for bad_name in ("123", "true", "['bad']", "{ key = 'val' }"):
        f = tmp_path / "bad.toml"
        f.write_text(f"name = {bad_name}\nbase = 'x'\n")
        with pytest.raises(TypeError, match="preset name must be a string"):
            load_presets([tmp_path])
        f.unlink()

    # 2. Empty string name
    f = tmp_path / "empty_name.toml"
    f.write_text("name = '   '\nbase = 'x'\n")
    with pytest.raises(ValueError, match="preset name cannot be empty"):
        load_presets([tmp_path])
    f.unlink()

    # 3. Omitted name -> infers from filename stem
    f = tmp_path / "inferred_name.toml"
    f.write_text("base = 'x'\ntitle = 'Inferred'\n")
    presets = load_presets([tmp_path])
    assert "inferred_name" in presets
    assert presets["inferred_name"].name == "inferred_name"
    f.unlink()


def test_presets_dir_environment_isolation_and_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Setup ambient PRESETS_DIR with an overridden x
    (tmp_path / "x.toml").write_text('name = "x"\nbase = "x"\nport = 5555\n')
    monkeypatch.setenv("PRESETS_DIR", str(tmp_path))

    # 1. env=None -> ambient discovery from os.environ
    p_ambient = load_preset("x")
    assert p_ambient.port == 5555

    # 2. env={} -> explicit mapping isolates from ambient PRESETS_DIR
    p_explicit_empty = load_preset("x", env={})
    assert p_explicit_empty.port == 2444

    # 3. env={"PRESETS_DIR": ""} -> explicitly selects empty directory (built-in only)
    p_empty_dir = load_preset("x", env={"PRESETS_DIR": ""})
    assert p_empty_dir.port == 2444
