"""Validate strict ES5 compatibility of client_html.py across all presets."""

from __future__ import annotations

import re
import subprocess

import pytest

from client_html import render_client_html
from presets import PRESETS

SCRIPT_RE = re.compile(r"<script>(.*?)</script>", re.DOTALL)
FORBIDDEN_ES6_PATTERNS = (
    (r"\b(let|const)\b", "block-scoped variable declaration"),
    (r"=>", "arrow function"),
    (r"`", "template literal"),
    (r"\bfetch\s*\(", "fetch API"),
    (r"\bPromise\b", "Promise API"),
    (r"\bclass\s+[A-Za-z_]", "ES6 class"),
)


@pytest.mark.parametrize("preset_name", ["term", "wechat", "x", "discord"])
def test_client_html_strict_es5_and_normalized_elements(preset_name: str) -> None:
    preset = PRESETS[preset_name]
    html = render_client_html(preset)

    assert '<canvas id="cv"></canvas>' in html
    assert '<canvas id="buf"></canvas>' in html
    assert 'id="bFs"' in html
    assert 'id="bType"' in html
    assert 'id="bNum"' in html
    assert '<div id="numBar">' in html
    assert 'id="barHead"' in html
    assert 'id="btnPost"' in html
    assert 'id="btnPaste"' in html
    assert 'id="btnSync"' in html
    assert 'id="btnFile"' in html
    assert 'id="fileIn"' in html
    assert 'id="typeTrap"' in html
    assert 'id="btnHide"' in html
    assert 'id="btnClear"' in html
    assert '<textarea id="msg" rows="2"' in html
    assert 'sizes="144x144" href="/icon.png"' in html
    assert "imageSmoothingEnabled = false" in html
    assert "visibilitychange" in html
    assert "webkitvisibilitychange" in html
    assert "clip_data" in html
    assert "RECONN_MAX" in html
    assert "CONN_TIMEOUT" in html
    assert "window.location.reload()" in html

    if preset.enable_term_bar:
        assert '<div id="termBar">' in html
        assert 'id="kCtrl"' in html
    else:
        assert '<div id="termBar">' not in html

    match = SCRIPT_RE.search(html)
    assert match is not None, "Missing <script> block in rendered HTML"
    script_src = match.group(1)

    for pattern, reason in FORBIDDEN_ES6_PATTERNS:
        assert re.search(pattern, script_src) is None, f"Forbidden ES6+ {reason} in {preset_name}"

    node_check = (
        "const fs = require('fs'), vm = require('vm');"
        "const code = fs.readFileSync(0, 'utf8');"
        "new vm.Script(code, { filename: 'client.js' });"
    )
    proc = subprocess.run(
        ["node", "-e", node_check],
        input=script_src,
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0, f"Node vm.Script syntax error: {proc.stderr}"
