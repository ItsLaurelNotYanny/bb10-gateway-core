"""Strict ES5 HTML/CSS/JS frontend template for BlackBerry 10.3.3 WebKit."""

from __future__ import annotations

import json

from presets import Preset


def render_client_html(preset: Preset) -> str:
    """Render self-contained ES5 gateway client page for the given preset."""
    has_term_bar = bool(preset.enable_term_bar)
    cfg_json = json.dumps(
        {
            "preset": preset.name,
            "title": preset.title,
            "winW": preset.win_w,
            "winH": preset.win_h,
            "layout": preset.layout,
            "railW": preset.rail_w,
            "chatX": preset.default_chat_x,
            "defaultTypeMode": preset.default_type_mode,
            "enableTermBar": has_term_bar,
        }
    )
    post_label = "Post" if preset.name == "x" else "Send"
    slim_btns = (
        '<button type="button" id="mSlim" class="tb active">Slim</button>'
        '<button type="button" id="mDraw" class="tb">Drawer</button>'
        '<button type="button" id="mChat" class="tb">Chat</button>'
        '<button type="button" id="mFull" class="tb">Full</button>'
        if preset.layout == "slim_rail"
        else ""
    )

    stage_top = "64px" if has_term_bar else "34px"
    num_bar_top = "64px" if has_term_bar else "34px"
    term_bar_html = (
        """<div id="termBar">
  <button type="button" id="kCtrl" class="tb">Ctrl</button>
  <button type="button" id="kAlt" class="tb">Alt</button>
  <button type="button" id="kEsc" class="tb">Esc</button>
  <button type="button" id="kTab" class="tb">Tab</button>
  <button type="button" id="kCtrlC" class="tb">^C</button>
  <button type="button" id="kCtrlB" class="tb">^B</button>
  <button type="button" id="kFontUp" class="tb">A+</button>
  <button type="button" id="kFontDn" class="tb">A-</button>
  <button type="button" id="kUp" class="tb">&#8593;</button>
  <button type="button" id="kDn" class="tb">&#8595;</button>
  <button type="button" id="kLt" class="tb">&#8592;</button>
  <button type="button" id="kRt" class="tb">&#8594;</button>
  <button type="button" id="kPipe" class="tb">|</button>
  <button type="button" id="kDash" class="tb">-</button>
  <button type="button" id="kSlash" class="tb">/</button>
  <button type="button" id="kTilde" class="tb">~</button>
</div>"""
        if has_term_bar
        else ""
    )
    num_bar_html = """<div id="numBar">
  <button type="button" class="tb nb" data-val="1">1</button>
  <button type="button" class="tb nb" data-val="2">2</button>
  <button type="button" class="tb nb" data-val="3">3</button>
  <button type="button" class="tb nb" data-val="4">4</button>
  <button type="button" class="tb nb" data-val="5">5</button>
  <button type="button" class="tb nb" data-val="6">6</button>
  <button type="button" class="tb nb" data-val="7">7</button>
  <button type="button" class="tb nb" data-val="8">8</button>
  <button type="button" class="tb nb" data-val="9">9</button>
  <button type="button" class="tb nb" data-val="0">0</button>
  <button type="button" class="tb nb" data-val=",">,</button>
  <button type="button" class="tb nb" data-val=".">.</button>
  <button type="button" class="tb nb" data-val="?">?</button>
  <button type="button" class="tb nb" data-val="!">!</button>
  <button type="button" class="tb nb" data-val="@">@</button>
  <button type="button" class="tb nb" data-val=":">:</button>
  <button type="button" class="tb nb" data-val="-">-</button>
  <button type="button" class="tb nb" data-val="_">_</button>
  <button type="button" class="tb nb" data-val="/">/</button>
  <button type="button" class="tb nb" data-val="+">+</button>
  <button type="button" class="tb nb" data-val="=">=</button>
  <button type="button" class="tb nb" data-val="#">#</button>
</div>"""

    return (
        """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<meta name="apple-mobile-web-app-title" content=\""""
        + preset.short_title
        + """\">
<meta name="application-name" content=\""""
        + preset.short_title
        + """\">
<meta name="mobile-web-app-capable" content="yes">
<meta name="theme-color" content="#0d1117">
<link rel="apple-touch-icon" sizes="144x144" href="/icon.png">
<link rel="apple-touch-icon-precomposed" sizes="144x144" href="/icon.png">
<link rel="icon" type="image/png" sizes="144x144" href="/icon.png">
<title>"""
        + preset.title
        + """</title>
<style>
* { box-sizing: border-box; -webkit-tap-highlight-color: rgba(0,0,0,0); }
html, body {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  margin: 0; padding: 0; width: 100%; height: 100%;
  background: #000; color: #e7e9ea;
  font-family: sans-serif; overflow: hidden;
  -webkit-user-select: none; user-select: none;
}
#top {
  position: fixed; top: 0; left: 0; right: 0; height: 34px;
  background: #11161d; border-bottom: 1px solid #26303d;
  display: block; padding: 3px 6px; z-index: 20; white-space: nowrap;
}
#termBar {
  position: fixed; top: 34px; left: 0; right: 0; height: 30px;
  background: #151b23; border-bottom: 1px solid #26303d;
  display: block; padding: 2px 4px; z-index: 20; white-space: nowrap;
  overflow-x: auto; -webkit-overflow-scrolling: touch;
}
#termBar .tb { padding: 3px 6px; margin-right: 2px; }
#numBar {
  position: fixed; top: """
        + num_bar_top
        + """; left: 0; right: 0; height: 30px;
  background: #0d1117; border-bottom: 1px solid #21262d;
  display: none; padding: 2px 4px; z-index: 19; white-space: nowrap;
  overflow-x: auto; -webkit-overflow-scrolling: touch;
}
#numBar.open { display: block; }
#numBar .nb {
  padding: 3px 8px; margin-right: 2px; font-weight: bold;
  background: #21262d; color: #58a6ff; border-color: #30363d;
}
#dot {
  display: inline-block; width: 10px; height: 10px; border-radius: 5px;
  background: #d97706; vertical-align: middle; margin-right: 5px;
}
#stat {
  display: inline-block; font-size: 12px; color: #9ca3af;
  vertical-align: middle; margin-right: 6px;
}
.tb {
  background: #1d2633; color: #e5e7eb; border: 1px solid #334155;
  border-radius: 4px; padding: 3px 7px; font-size: 12px;
  margin-right: 3px; vertical-align: middle; cursor: pointer;
}
.tb.active { background: #1d9bf0; border-color: #1d9bf0; color: #fff; }
.tr { float: right; }
#stage {
  position: fixed; top: """
        + stage_top
        + """; left: 0; right: 0; bottom: 0;
  background: #000; overflow: hidden;
}
#cv { display: block; width: 100%; height: 100%; background: #000; }
#buf { display: none; }
#bar {
  position: fixed; left: 0; right: 0; top: """
        + stage_top
        + """;
  background: #11161d; border-bottom: 2px solid #1d9bf0;
  padding: 5px 6px 7px 6px; z-index: 40; display: none;
  box-shadow: 0 4px 16px rgba(0,0,0,0.8);
}
#bar.open { display: block; }
#barHead {
  overflow: hidden; margin-bottom: 5px; line-height: 28px; white-space: nowrap;
}
.ab.closeBtn {
  float: right; margin-right: 0; padding: 4px 9px;
  background: #374151; border-color: #4b5563; color: #f87171;
  font-weight: bold; font-size: 12px; cursor: pointer;
}
#msg {
  width: 100%; height: 56px; background: #05080c; color: #ffffff;
  border: 1px solid #3b495e; border-radius: 4px; padding: 6px 8px;
  font-size: 15px; line-height: 1.35; resize: none;
  -webkit-user-select: text; user-select: text;
}
.ab {
  background: #1f2937; color: #f3f4f6; border: 1px solid #374151;
  border-radius: 4px; padding: 4px 7px; font-size: 13px;
  margin-right: 3px; cursor: pointer; display: inline-block;
  vertical-align: middle;
}
.ab.pri { background: #1d9bf0; border-color: #1d9bf0; color: #fff; font-weight: bold; }
.ab.on { background: #059669; border-color: #059669; color: #fff; }
#imgIn, #fileIn { position: absolute; left: -9999px; width: 1px; height: 1px; opacity: 0; }
#typeTrap {
  position: fixed; top: 0; left: -9999px; width: 10px; height: 10px;
  opacity: 0.01; border: none; padding: 0; margin: 0; z-index: -1;
  pointer-events: none; resize: none; overflow: hidden;
}
</style>
</head>
<body>
<div id="top">
  <span id="dot"></span><span id="stat">Conn</span>"""
        + slim_btns
        + """<div class="tr">
    <button type="button" id="bFs" class="tb" title="Fullscreen">&#9974;</button>
    <button type="button" id="bType" class="tb">Type</button>
    <button type="button" id="bNum" class="tb">123</button>
    <button type="button" id="bUp" class="tb">&#9650;</button>
    <button type="button" id="bDn" class="tb">&#9660;</button>
    <button type="button" id="bRef" class="tb">&#8635;</button>
    <button type="button" id="bInp" class="tb">&#9998;</button>
  </div>
</div>
"""
        + term_bar_html
        + num_bar_html
        + """<div id="stage">
  <canvas id="cv"></canvas>
  <canvas id="buf"></canvas>
  <textarea id="typeTrap" rows="1" autocapitalize="off" autocorrect="off"
    autocomplete="off" spellcheck="false"></textarea>
</div>
<div id="bar">
  <div id="barHead">
    <button type="button" id="btnPost" class="ab pri">"""
        + post_label
        + """ ↵</button>
    <button type="button" id="btnPaste" class="ab">Paste</button>
    <button type="button" id="btnSync" class="ab" title="Pull remote clipboard">Sync</button>
    <label for="imgIn" id="btnCam" class="ab" title="Upload Photo">&#128247;</label>
    <input type="file" id="imgIn" accept="image/*">
    <label for="fileIn" id="btnFile" class="ab" title="Upload Attachment">&#128206;</label>
    <input type="file" id="fileIn">
    <button type="button" id="btnBksp" class="ab">Bksp</button>
    <button type="button" id="btnClear" class="ab">Clear</button>
    <button type="button" id="btnPin" class="ab">Pin</button>
    <button type="button" id="btnHide" class="ab closeBtn">&#10005; Close</button>
  </div>
  <textarea id="msg" rows="2" placeholder="Type Pinyin / English... Enter = Send ↵"></textarea>
</div>
<script>
(function () {
  var CFG = """
        + cfg_json
        + """;
  var winW = CFG.winW || 720;
  var winH = CFG.winH || 720;
  var layout = CFG.layout || 'direct';
  var railW = CFG.railW || 0;
  var chatX = CFG.chatX || 0;
  var hasTermBar = !!CFG.enableTermBar;
  var viewMode = layout === 'slim_rail' ? 'slim' : 'direct';

  var cv = document.getElementById('cv');
  var ctx = cv.getContext('2d');
  var buf = document.getElementById('buf');
  var bufCtx = buf.getContext('2d');
  buf.width = winW;
  buf.height = winH;

  var stage = document.getElementById('stage');
  var bar = document.getElementById('bar');
  var msgEl = document.getElementById('msg');
  var dotEl = document.getElementById('dot');
  var statEl = document.getElementById('stat');
  var btnPin = document.getElementById('btnPin');
  var btnType = document.getElementById('bType');
  var imgIn = document.getElementById('imgIn');
  var fileIn = document.getElementById('fileIn');
  var typeTrap = document.getElementById('typeTrap');
  var bInp = document.getElementById('bInp');

  var kCtrl = document.getElementById('kCtrl');
  var kAlt = document.getElementById('kAlt');
  var bNum = document.getElementById('bNum');
  var numBar = document.getElementById('numBar');
  var numBarOpen = false;
  var NUM_MAP = {
    q: '1', w: '2', e: '3', r: '4', t: '5',
    y: '6', u: '7', i: '8', o: '9', p: '0'
  };
  var ctrlArmed = false;
  var altArmed = false;

  var ws = null;
  var reconnTimer = null;
  var barOpen = false;
  var pinned = false;
  var typeMode = !!CFG.defaultTypeMode;
  if (typeMode && btnType) {
    btnType.className = 'tb active';
  }
  var TRAP_BASE = '    ';
  var lastTrapVal = TRAP_BASE;
  var suppressKeypress = false;

  function resetTypeTrap() {
    if (!typeTrap) { return; }
    typeTrap.value = TRAP_BASE;
    lastTrapVal = TRAP_BASE;
    try {
      typeTrap.setSelectionRange(TRAP_BASE.length, TRAP_BASE.length);
    } catch (e) {}
  }

  function focusTypeTrap() {
    if (!typeTrap || !typeMode || barOpen) { return; }
    resetTypeTrap();
    try {
      typeTrap.focus();
      typeTrap.setSelectionRange(TRAP_BASE.length, TRAP_BASE.length);
    } catch (e) {}
    window.scrollTo(0, 0);
  }

  function blurTypeTrap() {
    if (!typeTrap) { return; }
    try { typeTrap.blur(); } catch (e) {}
    window.scrollTo(0, 0);
  }
  var pausedState = false;
  var frameQueue = [];
  var decoding = false;
  var hasFrame = false;

  function setStatus(color, label) {
    dotEl.style.background = color;
    statEl.textContent = label;
  }

  function setCtrlArmed(val) {
    ctrlArmed = !!val;
    if (kCtrl) {
      kCtrl.className = ctrlArmed ? 'tb active' : 'tb';
    }
  }

  function setAltArmed(val) {
    altArmed = !!val;
    if (kAlt) {
      kAlt.className = altArmed ? 'tb active' : 'tb';
    }
  }

  function wsSend(obj) {
    if (ws && ws.readyState === 1) {
      try {
        ws.send(JSON.stringify(obj));
      } catch (e) {}
    }
  }

  function clampH(h) {
    var v = Math.round(h || 720);
    if (v < 420) { return 420; }
    if (v > 1080) { return 1080; }
    return v;
  }

  function getHeaderHeight() {
    var baseH = hasTermBar ? 64 : 34;
    return numBarOpen ? (baseH + 30) : baseH;
  }

  function calcTargetWinH() {
    var topH = getHeaderHeight();
    var sw = stage.clientWidth || window.innerWidth || winW;
    var sh = stage.clientHeight || (window.innerHeight - topH) || 720;
    if (sw <= 0) { sw = winW; }
    var activeSrcW = winW;
    if (layout === 'slim_rail') {
      var splitX = chatX > railW ? chatX : 375;
      var rw = railW > 0 ? railW : 72;
      if (viewMode === 'drawer') {
        activeSrcW = splitX;
      } else if (viewMode === 'chat') {
        activeSrcW = winW - splitX;
      } else if (viewMode === 'full') {
        activeSrcW = winW;
      } else {
        activeSrcW = rw + (winW - splitX);
      }
    }
    if (activeSrcW <= 0) { activeSrcW = winW; }
    return clampH(Math.round((sh * activeSrcW) / sw));
  }

  function syncStageLayout() {
    stage.style.bottom = '0px';
    stage.style.top = getHeaderHeight() + 'px';
    var dpr = window.devicePixelRatio || 1;
    var cw = stage.clientWidth || window.innerWidth || winW;
    var ch = stage.clientHeight || 480;
    var targetW = Math.round(cw * dpr);
    var targetH = Math.round(ch * dpr);
    if (targetW > 0 && targetH > 0 && (cv.width !== targetW || cv.height !== targetH)) {
      cv.width = targetW;
      cv.height = targetH;
    }
    drawFrame();
  }

  function sendResize() {
    syncStageLayout();
    var targetH = calcTargetWinH();
    wsSend({ type: 'resize', win_h: targetH });
  }

  function openBar() {
    barOpen = true;
    bar.className = 'open';
    if (bInp) { bInp.className = 'tb active'; }
    bar.style.top = getHeaderHeight() + 'px';
    syncStageLayout();
    window.scrollTo(0, 0);
    setTimeout(function () {
      try { msgEl.focus(); } catch (e) {}
      window.scrollTo(0, 0);
    }, 20);
  }

  function closeBar() {
    barOpen = false;
    bar.className = '';
    if (bInp) { bInp.className = 'tb'; }
    try { msgEl.blur(); } catch (e) {}
    window.scrollTo(0, 0);
    syncStageLayout();
    if (typeMode) {
      focusTypeTrap();
    }
  }

  function drawFrame() {
    if (!hasFrame || cv.width <= 0 || cv.height <= 0) {
      return;
    }
    ctx.imageSmoothingEnabled = false;
    ctx.webkitImageSmoothingEnabled = false;
    ctx.fillStyle = '#000';
    ctx.fillRect(0, 0, cv.width, cv.height);

    if (layout !== 'slim_rail' || viewMode === 'direct' || viewMode === 'full') {
      ctx.drawImage(buf, 0, 0, winW, winH, 0, 0, cv.width, cv.height);
      return;
    }

    var splitX = chatX > railW ? chatX : 375;
    if (viewMode === 'drawer') {
      ctx.drawImage(buf, 0, 0, splitX, winH, 0, 0, cv.width, cv.height);
    } else if (viewMode === 'chat') {
      var cw = winW - splitX;
      if (cw > 0) {
        ctx.drawImage(buf, splitX, 0, cw, winH, 0, 0, cv.width, cv.height);
      }
    } else {
      var rw = railW > 0 ? railW : 72;
      var chatW = winW - splitX;
      var totalSrcW = rw + chatW;
      var destRailW = Math.round((rw * cv.width) / totalSrcW);
      ctx.drawImage(buf, 0, 0, rw, winH, 0, 0, destRailW, cv.height);
      ctx.drawImage(
        buf,
        splitX,
        0,
        chatW,
        winH,
        destRailW,
        0,
        cv.width - destRailW,
        cv.height
      );
    }
  }

  function mapClientToRemote(clientX, clientY) {
    var rect = cv.getBoundingClientRect();
    var w = rect.width || cv.width || 1;
    var h = rect.height || cv.height || 1;
    var lx = clientX - rect.left;
    var ly = clientY - rect.top;
    var ry = Math.round((ly * winH) / h);
    var rx = 0;

    if (layout !== 'slim_rail' || viewMode === 'direct' || viewMode === 'full') {
      rx = Math.round((lx * winW) / w);
    } else {
      var splitX = chatX > railW ? chatX : 375;
      if (viewMode === 'drawer') {
        rx = Math.round((lx * splitX) / w);
      } else if (viewMode === 'chat') {
        rx = splitX + Math.round((lx * (winW - splitX)) / w);
      } else {
        var rw = railW > 0 ? railW : 72;
        var chatW = winW - splitX;
        var destRailW = (rw * w) / (rw + chatW);
        if (lx < destRailW) {
          rx = Math.round((lx * rw) / destRailW);
        } else {
          rx = splitX + Math.round(((lx - destRailW) * chatW) / (w - destRailW));
        }
      }
    }

    if (rx < 0) { rx = 0; }
    if (rx >= winW) { rx = winW - 1; }
    if (ry < 0) { ry = 0; }
    if (ry >= winH) { ry = winH - 1; }
    return { x: rx, y: ry };
  }

  function slicePayloadBuffer(ab, offset) {
    if (ab.slice) {
      return ab.slice(offset);
    }
    var src = new Uint8Array(ab, offset);
    var copy = new Uint8Array(src.length);
    var i = 0;
    for (i = 0; i < src.length; i++) {
      copy[i] = src[i];
    }
    return copy.buffer;
  }

  function uint8ToBase64(u8) {
    var CHUNK = 32768;
    var parts = [];
    var i = 0;
    var end = 0;
    var sub = null;
    for (i = 0; i < u8.length; i += CHUNK) {
      end = i + CHUNK;
      if (end > u8.length) { end = u8.length; }
      sub = u8.subarray(i, end);
      parts.push(String.fromCharCode.apply(null, sub));
    }
    return window.btoa(parts.join(''));
  }

  function processNextFrame() {
    if (decoding || frameQueue.length === 0) {
      return;
    }
    var item = frameQueue.shift();
    decoding = true;

    var img = new Image();
    var urlApi = window.URL || window.webkitURL;
    var objUrl = null;
    if (urlApi && urlApi.createObjectURL && typeof Blob !== 'undefined') {
      try {
        var blob = new Blob([item.buf], { type: 'image/jpeg' });
        objUrl = urlApi.createObjectURL(blob);
      } catch (e) {
        objUrl = null;
      }
    }

    img.onload = function () {
      if (objUrl && urlApi && urlApi.revokeObjectURL) {
        try { urlApi.revokeObjectURL(objUrl); } catch (e) {}
      }
      if (item.flags === 1 && item.x === 0 && item.y === 0) {
        if (buf.width !== item.w || buf.height !== item.h) {
          winW = item.w;
          winH = item.h;
          buf.width = winW;
          buf.height = winH;
        }
      }
      bufCtx.drawImage(img, item.x, item.y, item.w, item.h);
      hasFrame = true;
      drawFrame();
      decoding = false;
      processNextFrame();
    };

    img.onerror = function () {
      if (objUrl && urlApi && urlApi.revokeObjectURL) {
        try { urlApi.revokeObjectURL(objUrl); } catch (e) {}
      }
      decoding = false;
      processNextFrame();
    };

    if (objUrl) {
      img.src = objUrl;
    } else {
      img.src = 'data:image/jpeg;base64,' + uint8ToBase64(new Uint8Array(item.buf));
    }
  }

  function onBinaryFrame(ab) {
    var bytes = new Uint8Array(ab);
    if (bytes.length <= 10 || bytes[0] !== 0x42) {
      return;
    }
    var flags = bytes[1];
    var rx = (bytes[2] << 8) | bytes[3];
    var ry = (bytes[4] << 8) | bytes[5];
    var rw = (bytes[6] << 8) | bytes[7];
    var rh = (bytes[8] << 8) | bytes[9];
    var payload = slicePayloadBuffer(ab, 10);

    if (flags === 1 && frameQueue.length > 2) {
      frameQueue = [];
    }
    frameQueue.push({ flags: flags, x: rx, y: ry, w: rw, h: rh, buf: payload });
    processNextFrame();
  }

  function updatePauseState(forceHidden) {
    var hidden = forceHidden === true ? true : !!(document.hidden || document.webkitHidden);
    if (forceHidden === false) {
      hidden = !!(document.hidden || document.webkitHidden);
    }
    if (hidden !== pausedState) {
      pausedState = hidden;
      wsSend({ type: 'pause', paused: pausedState });
      if (ws && ws.readyState === 1) {
        setStatus(pausedState ? '#6b7280' : '#10b981', pausedState ? 'Sleep' : 'Live');
      }
    }
  }

  function connectWs() {
    if (reconnTimer) {
      clearTimeout(reconnTimer);
      reconnTimer = null;
    }
    var proto = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    var hParam = calcTargetWinH();
    var q = window.location.search || '';
    var sep = q ? '&' : '?';
    var wsUrl = proto + window.location.host + '/ws' + q + sep + 'h=' + hParam;

    setStatus('#d97706', 'Conn');
    try {
      ws = new WebSocket(wsUrl);
    } catch (e) {
      reconnTimer = setTimeout(connectWs, 2000);
      return;
    }
    ws.binaryType = 'arraybuffer';

    ws.onopen = function () {
      pausedState = !!(document.hidden || document.webkitHidden);
      setStatus(pausedState ? '#6b7280' : '#10b981', pausedState ? 'Sleep' : 'Live');
      sendResize();
      if (pausedState) {
        wsSend({ type: 'pause', paused: true });
      }
    };

    ws.onmessage = function (ev) {
      if (typeof ev.data === 'string') {
        try {
          var meta = JSON.parse(ev.data);
          if (meta.type === 'meta') {
            if (meta.win_w) { winW = meta.win_w; }
            if (meta.win_h) { winH = meta.win_h; }
            if (typeof meta.chat_x === 'number') { chatX = meta.chat_x; }
            if (buf.width !== winW || buf.height !== winH) {
              buf.width = winW;
              buf.height = winH;
            }
            drawFrame();
          } else if (meta.type === 'clip_data') {
            msgEl.value = meta.text || '';
            if (!barOpen) { openBar(); }
            try {
              msgEl.focus();
              msgEl.select();
            } catch (e) {}
          }
        } catch (e) {}
      } else if (ev.data) {
        onBinaryFrame(ev.data);
      }
    };

    ws.onclose = function () {
      setStatus('#ef4444', 'Off');
      reconnTimer = setTimeout(connectWs, 1800);
    };

    ws.onerror = function () {
      try { ws.close(); } catch (e) {}
    };
  }

  // Pointer / touch handling on canvas
  var touchStart = null;
  var suppressClickUntil = 0;

  cv.addEventListener('touchstart', function (ev) {
    if (barOpen && !pinned) {
      closeBar();
      ev.preventDefault();
      touchStart = null;
      return;
    }
    if (!ev.touches || ev.touches.length !== 1) { return; }
    var t = ev.touches[0];
    touchStart = { x: t.clientX, y: t.clientY, lastY: t.clientY, dragged: false };
  }, false);

  cv.addEventListener('touchmove', function (ev) {
    if (!touchStart) { return; }
    ev.preventDefault();
    if (!ev.touches || ev.touches.length !== 1) { return; }
    var t = ev.touches[0];
    var dyTotal = t.clientY - touchStart.y;
    var stepDy = touchStart.lastY - t.clientY;
    if (Math.abs(dyTotal) > 16 && Math.abs(stepDy) >= 24) {
      touchStart.dragged = true;
      touchStart.lastY = t.clientY;
      var pt = mapClientToRemote(t.clientX, t.clientY);
      wsSend({ type: 'wheel', x: pt.x, y: pt.y, dy: stepDy > 0 ? 180 : -180 });
    }
  }, false);

  cv.addEventListener('touchend', function (ev) {
    if (!touchStart) { return; }
    var ts = touchStart;
    touchStart = null;
    suppressClickUntil = new Date().getTime() + 450;
    if (!ts.dragged) {
      var pt = mapClientToRemote(ts.x, ts.y);
      wsSend({ type: 'click', x: pt.x, y: pt.y, button: 1 });
      if (typeMode && !barOpen) {
        focusTypeTrap();
      }
    }
    ev.preventDefault();
  }, false);

  cv.addEventListener('click', function (ev) {
    if (barOpen && !pinned) {
      closeBar();
      ev.preventDefault();
      return;
    }
    if (new Date().getTime() < suppressClickUntil) { return; }
    var pt = mapClientToRemote(ev.clientX, ev.clientY);
    wsSend({ type: 'click', x: pt.x, y: pt.y, button: 1 });
    if (typeMode && !barOpen) {
      focusTypeTrap();
    }
  }, false);

  var wheelAccDy = 0;
  var wheelTimer = null;
  var wheelLastPt = null;

  function flushWheel() {
    wheelTimer = null;
    if (!wheelAccDy) { return; }
    var dy = wheelAccDy;
    wheelAccDy = 0;
    var pt = wheelLastPt || { x: Math.round(winW / 2), y: Math.round(winH / 2) };
    wsSend({ type: 'wheel', x: pt.x, y: pt.y, dy: dy });
  }

  function handleWheelEvt(ev) {
    var rawDy = 0;
    if (typeof ev.wheelDelta === 'number') {
      rawDy = -ev.wheelDelta;
    } else if (typeof ev.deltaY === 'number') {
      rawDy = ev.deltaY;
    } else if (ev.detail) {
      rawDy = ev.detail * 40;
    }
    if (!rawDy) { return; }
    var cx = (typeof ev.clientX === 'number' && ev.clientX > 0)
      ? ev.clientX
      : Math.round((stage.clientWidth || winW) / 2);
    var cy = (typeof ev.clientY === 'number' && ev.clientY > 0)
      ? ev.clientY
      : Math.round((stage.clientHeight || winH) / 2);
    wheelLastPt = mapClientToRemote(cx, cy);
    wheelAccDy += rawDy;
    if (!wheelTimer) {
      wheelTimer = setTimeout(flushWheel, 40);
    }
    if (ev.preventDefault) { ev.preventDefault(); }
  }
  window.addEventListener('mousewheel', handleWheelEvt, false);
  if (!('onmousewheel' in window)) {
    window.addEventListener('wheel', handleWheelEvt, false);
  }

  // Toolbar controls
  function setMode(m) {
    viewMode = m;
    var ids = ['mSlim', 'mDraw', 'mChat', 'mFull'];
    var map = { mSlim: 'slim', mDraw: 'drawer', mChat: 'chat', mFull: 'full' };
    var i = 0;
    var el = null;
    for (i = 0; i < ids.length; i++) {
      el = document.getElementById(ids[i]);
      if (el) {
        el.className = map[ids[i]] === m ? 'tb active' : 'tb';
      }
    }
    drawFrame();
    sendResize();
  }

  function bindModeBtn(id, mode) {
    var el = document.getElementById(id);
    if (el) {
      el.onclick = function () { setMode(mode); };
    }
  }
  bindModeBtn('mSlim', 'slim');
  bindModeBtn('mDraw', 'drawer');
  bindModeBtn('mChat', 'chat');
  bindModeBtn('mFull', 'full');

  var bFs = document.getElementById('bFs');
  function checkFsActive() {
    return !!(
      document.webkitIsFullScreen ||
      document.webkitFullscreenElement ||
      document.fullscreenElement
    );
  }
  function updateFsState() {
    if (bFs) {
      bFs.className = checkFsActive() ? 'tb active' : 'tb';
    }
  }
  if (bFs) {
    bFs.onclick = function () {
      if (checkFsActive()) {
        if (document.webkitCancelFullScreen) { document.webkitCancelFullScreen(); }
        else if (document.webkitExitFullscreen) { document.webkitExitFullscreen(); }
        else if (document.exitFullscreen) { document.exitFullscreen(); }
      } else {
        var el = document.documentElement || document.body;
        if (el.webkitRequestFullScreen) {
          try {
            el.webkitRequestFullScreen(Element.ALLOW_KEYBOARD_INPUT);
          } catch (e) {
            el.webkitRequestFullScreen();
          }
        } else if (el.requestFullscreen) {
          el.requestFullscreen();
        }
      }
    };
  }
  document.addEventListener('webkitfullscreenchange', function () {
    updateFsState();
    syncStageLayout();
    setTimeout(sendResize, 380);
  }, false);
  document.addEventListener('fullscreenchange', function () {
    updateFsState();
    syncStageLayout();
    setTimeout(sendResize, 380);
  }, false);

  btnType.onclick = function () {
    typeMode = !typeMode;
    btnType.className = typeMode ? 'tb active' : 'tb';
    if (typeMode) {
      focusTypeTrap();
    } else {
      blurTypeTrap();
    }
  };

  if (typeTrap) {
    resetTypeTrap();
    typeTrap.addEventListener('input', function () {
      if (!typeMode || barOpen) {
        resetTypeTrap();
        return;
      }
      var cur = typeTrap.value || '';
      var prev = lastTrapVal;
      var p = 0;
      var minLen = prev.length < cur.length ? prev.length : cur.length;
      while (p < minLen && prev.charCodeAt(p) === cur.charCodeAt(p)) {
        p++;
      }
      var delCount = prev.length - p;
      var added = cur.substring(p);
      var i = 0;
      for (i = 0; i < delCount; i++) {
        wsSend({ type: 'key', key: 'BackSpace' });
      }
      if (added) {
        var asciiOnly = true;
        for (i = 0; i < added.length; i++) {
          var code = added.charCodeAt(i);
          if (code < 32 || code > 126) {
            asciiOnly = false;
            break;
          }
        }
        if (asciiOnly && added.length <= 64) {
          wsSend({ type: 'type', text: added });
        } else {
          wsSend({ type: 'paste_only', text: added });
        }
      }
      resetTypeTrap();
    }, false);
  }

  document.getElementById('bUp').onclick = function () {
    wsSend({ type: 'wheel', x: Math.round(winW / 2), y: Math.round(winH / 2), dy: -260 });
  };
  document.getElementById('bDn').onclick = function () {
    wsSend({ type: 'wheel', x: Math.round(winW / 2), y: Math.round(winH / 2), dy: 260 });
  };
  document.getElementById('bRef').onclick = function () {
    wsSend({ type: 'refresh' });
  };
  document.getElementById('bInp').onclick = function () {
    if (barOpen) { closeBar(); } else { openBar(); }
  };

  // Optional terminal bar buttons
  if (kCtrl) {
    kCtrl.onclick = function () { setCtrlArmed(!ctrlArmed); };
  }
  if (kAlt) {
    kAlt.onclick = function () { setAltArmed(!altArmed); };
  }
  if (bNum) {
    bNum.onclick = function () {
      numBarOpen = !numBarOpen;
      bNum.className = numBarOpen ? 'tb active' : 'tb';
      if (numBar) {
        numBar.className = numBarOpen ? 'open' : '';
      }
      if (barOpen) {
        bar.style.top = getHeaderHeight() + 'px';
      }
      syncStageLayout();
      sendResize();
      if (typeMode && !barOpen) {
        focusTypeTrap();
      }
    };
  }
  if (numBar) {
    numBar.onclick = function (ev) {
      var target = ev.target || ev.srcElement;
      if (target && target.getAttribute) {
        var val = target.getAttribute('data-val');
        if (val) {
          if (barOpen && msgEl) {
            msgEl.value += val;
            try { msgEl.focus(); } catch (e) {}
          } else {
            wsSend({ type: 'type', text: val });
            if (typeMode) {
              focusTypeTrap();
            }
          }
          if (ev.preventDefault) { ev.preventDefault(); }
        }
      }
    };
  }
  function bindKeyBtn(id, keyName) {
    var el = document.getElementById(id);
    if (el) {
      el.onclick = function () { wsSend({ type: 'key', key: keyName }); };
    }
  }
  bindKeyBtn('kEsc', 'Escape');
  bindKeyBtn('kTab', 'Tab');
  bindKeyBtn('kCtrlC', 'ctrl+c');
  bindKeyBtn('kCtrlB', 'ctrl+b');
  bindKeyBtn('kUp', 'Up');
  bindKeyBtn('kDn', 'Down');
  bindKeyBtn('kLt', 'Left');
  bindKeyBtn('kRt', 'Right');
  bindKeyBtn('kPipe', 'bar');
  bindKeyBtn('kDash', 'minus');
  bindKeyBtn('kSlash', 'slash');
  bindKeyBtn('kTilde', 'asciitilde');

  var kFontUp = document.getElementById('kFontUp');
  if (kFontUp) {
    kFontUp.onclick = function () { wsSend({ type: 'font', dir: 'up' }); };
  }
  var kFontDn = document.getElementById('kFontDn');
  if (kFontDn) {
    kFontDn.onclick = function () { wsSend({ type: 'font', dir: 'down' }); };
  }

  // Top-anchored native input drawer controls
  function submitText(msgType) {
    var text = msgEl.value;
    if (!text) { return; }
    wsSend({ type: msgType, text: text });
    msgEl.value = '';
    if (!pinned) {
      closeBar();
    } else {
      try { msgEl.focus(); } catch (e) {}
    }
  }

  document.getElementById('btnPost').onclick = function () { submitText('paste_send'); };
  document.getElementById('btnPaste').onclick = function () { submitText('paste_only'); };
  var btnSync = document.getElementById('btnSync');
  if (btnSync) {
    btnSync.onclick = function () { wsSend({ type: 'clip_get' }); };
  }
  document.getElementById('btnBksp').onclick = function () {
    wsSend({ type: 'key', key: 'BackSpace' });
  };
  btnPin.onclick = function () {
    pinned = !pinned;
    btnPin.className = pinned ? 'ab on' : 'ab';
  };
  var btnClear = document.getElementById('btnClear');
  if (btnClear) {
    btnClear.onclick = function () {
      msgEl.value = '';
      try { msgEl.focus(); } catch (e) {}
    };
  }
  document.getElementById('btnHide').onclick = function () { closeBar(); };

  imgIn.onchange = function () {
    if (!imgIn.files || !imgIn.files[0]) { return; }
    var file = imgIn.files[0];
    var xhr = new XMLHttpRequest();
    var q = window.location.search || '';
    xhr.open('POST', '/upload' + q, true);
    xhr.setRequestHeader('Content-Type', file.type || 'application/octet-stream');
    setStatus('#3b82f6', 'Up...');
    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4) {
        setStatus(xhr.status === 200 ? '#10b981' : '#ef4444', xhr.status === 200 ? 'Live' : 'Err');
        imgIn.value = '';
      }
    };
    xhr.send(file);
  };

  if (fileIn) {
    fileIn.onchange = function () {
      if (!fileIn.files || !fileIn.files[0]) { return; }
      var file = fileIn.files[0];
      var xhr = new XMLHttpRequest();
      var q = window.location.search || '';
      var sep = q ? '&' : '?';
      var fname = encodeURIComponent(file.name || 'attachment.bin');
      xhr.open('POST', '/upload' + q + sep + 'mode=file&name=' + fname, true);
      xhr.setRequestHeader('Content-Type', file.type || 'application/octet-stream');
      setStatus('#3b82f6', 'Up...');
      xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
          var ok = xhr.status === 200;
          setStatus(ok ? '#10b981' : '#ef4444', ok ? 'Live' : 'Err');
          fileIn.value = '';
          if (!pinned && barOpen) {
            closeBar();
          }
        }
      };
      xhr.send(file);
    };
  }

  // Physical keyboard handling (BlackBerry Passport Dual-Track Engine)
  var X_DIRECT_KEYS = {
    l: 'l', n: 'n', r: 'r', u: 'u', x: 'x', g: 'g', h: 'h', m: 'm'
  };

  document.addEventListener('keydown', function (ev) {
    var active = document.activeElement;
    var tag = active ? active.tagName : '';
    var inTrap = !!(typeTrap && active === typeTrap);
    var inInput = !inTrap && (active === msgEl || tag === 'TEXTAREA' || tag === 'INPUT');
    var kc = ev.keyCode || ev.which || 0;

    if (inInput) {
      if (kc === 13) {
        if (!ev.shiftKey) {
          setCtrlArmed(false);
          setAltArmed(false);
          submitText('paste_send');
          ev.preventDefault();
          return;
        }
        return;
      } else if (kc === 27) {
        closeBar();
        ev.preventDefault();
        return;
      } else if (kc === 8 && !msgEl.value) {
        closeBar();
        ev.preventDefault();
        return;
      }
      return;
    }

    if (ev.ctrlKey || ev.altKey || ev.metaKey) {
      return;
    }

    // Armed one-shot modifiers (Ctrl / Alt)
    if (ctrlArmed || altArmed) {
      var modCh = '';
      if (ev.key && ev.key.length === 1 && /^[a-zA-Z0-9]$/.test(ev.key)) {
        modCh = ev.key.toLowerCase();
      } else if ((kc >= 65 && kc <= 90) || (kc >= 48 && kc <= 57)) {
        modCh = String.fromCharCode(kc).toLowerCase();
      }
      if (modCh) {
        var modPrefix = ctrlArmed ? 'ctrl+' : 'alt+';
        wsSend({ type: 'key', key: modPrefix + modCh });
        setCtrlArmed(false);
        setAltArmed(false);
        suppressKeypress = true;
        ev.preventDefault();
        return;
      }
      if (kc === 27) {
        setCtrlArmed(false);
        setAltArmed(false);
        suppressKeypress = true;
        ev.preventDefault();
        return;
      }
    }

    // Number bar keyboard translation for Passport physical keyboard (Q..P -> 1..0)
    if (numBarOpen) {
      var numCh = '';
      if (ev.key && ev.key.length === 1) {
        numCh = ev.key.toLowerCase();
      } else if (kc >= 65 && kc <= 90) {
        numCh = String.fromCharCode(kc + 32);
      }
      if (numCh && NUM_MAP[numCh]) {
        wsSend({ type: 'type', text: NUM_MAP[numCh] });
        if (inTrap) { resetTypeTrap(); }
        suppressKeypress = true;
        ev.preventDefault();
        return;
      }
    }

    suppressKeypress = false;
    if (typeMode) {
      if (kc === 13) {
        wsSend({ type: 'key', key: 'Return' });
        if (inTrap) { resetTypeTrap(); }
        suppressKeypress = true;
        ev.preventDefault();
      } else if (kc === 9) {
        wsSend({ type: 'key', key: 'Tab' });
        if (inTrap) { resetTypeTrap(); }
        suppressKeypress = true;
        ev.preventDefault();
      } else if (kc === 27) {
        wsSend({ type: 'key', key: 'Escape' });
        if (inTrap) { resetTypeTrap(); }
        suppressKeypress = true;
        ev.preventDefault();
      } else if (kc === 38) {
        wsSend({ type: 'key', key: 'Up' });
        if (inTrap) { resetTypeTrap(); }
        suppressKeypress = true;
        ev.preventDefault();
      } else if (kc === 40) {
        wsSend({ type: 'key', key: 'Down' });
        if (inTrap) { resetTypeTrap(); }
        suppressKeypress = true;
        ev.preventDefault();
      } else if (kc === 37) {
        wsSend({ type: 'key', key: 'Left' });
        if (inTrap) { resetTypeTrap(); }
        suppressKeypress = true;
        ev.preventDefault();
      } else if (kc === 39) {
        wsSend({ type: 'key', key: 'Right' });
        if (inTrap) { resetTypeTrap(); }
        suppressKeypress = true;
        ev.preventDefault();
      } else if (!inTrap) {
        if (kc === 8) {
          wsSend({ type: 'key', key: 'BackSpace' });
          suppressKeypress = true;
          ev.preventDefault();
        } else if (kc === 32) {
          wsSend({ type: 'key', key: 'space' });
          suppressKeypress = true;
          ev.preventDefault();
        } else if (ev.key && ev.key.length === 1) {
          var ac = ev.key.charCodeAt(0);
          if (ac >= 33 && ac <= 126) {
            wsSend({ type: 'type', text: ev.key });
            suppressKeypress = true;
            ev.preventDefault();
          }
        }
      }
      return;
    }

    var ch = '';
    if (ev.key && ev.key.length === 1) {
      ch = ev.key.toLowerCase();
    } else if (kc >= 65 && kc <= 90) {
      ch = String.fromCharCode(kc + 32);
    } else if (kc === 191) {
      ch = '/';
    }

    if (layout === 'slim_rail') {
      if (kc === 13 || ch === 'i') {
        openBar();
        suppressKeypress = true;
        ev.preventDefault();
      } else if (kc === 32) {
        if (ev.shiftKey) {
          wsSend({ type: 'key', key: 'Page_Up' });
        } else {
          wsSend({ type: 'key', key: 'Page_Down' });
        }
        suppressKeypress = true;
        ev.preventDefault();
      } else if (ch === 'j') {
        wsSend({ type: 'wheel', x: Math.round(winW / 2), y: Math.round(winH / 2), dy: 240 });
        suppressKeypress = true;
        ev.preventDefault();
      } else if (ch === 'k') {
        wsSend({ type: 'wheel', x: Math.round(winW / 2), y: Math.round(winH / 2), dy: -240 });
        suppressKeypress = true;
        ev.preventDefault();
      } else if (ch === 'p') {
        wsSend({ type: 'key', key: 'Page_Up' });
        suppressKeypress = true;
        ev.preventDefault();
      } else if (ch === 't') {
        wsSend({ type: 'key', key: 'Home' });
        suppressKeypress = true;
        ev.preventDefault();
      } else if (ch === 'b') {
        wsSend({ type: 'key', key: 'End' });
        suppressKeypress = true;
        ev.preventDefault();
      } else if (ch === 's') {
        setMode(viewMode === 'drawer' ? 'slim' : 'drawer');
        suppressKeypress = true;
        ev.preventDefault();
      } else if (kc === 27) {
        wsSend({ type: 'key', key: 'Escape' });
        suppressKeypress = true;
        ev.preventDefault();
      }
      return;
    }

    // Navigation mode shortcuts (direct layout)
    if (ch === 'i') {
      openBar();
      suppressKeypress = true;
      ev.preventDefault();
      return;
    }
    if (ch === 'j') {
      wsSend({ type: 'wheel', x: Math.round(winW / 2), y: Math.round(winH / 2), dy: 260 });
      suppressKeypress = true;
      ev.preventDefault();
      return;
    }
    if (ch === 'k') {
      wsSend({ type: 'wheel', x: Math.round(winW / 2), y: Math.round(winH / 2), dy: -260 });
      suppressKeypress = true;
      ev.preventDefault();
      return;
    }
    if (kc === 32) {
      if (ev.shiftKey) {
        wsSend({ type: 'key', key: 'Page_Up' });
      } else {
        wsSend({ type: 'key', key: 'Page_Down' });
      }
      suppressKeypress = true;
      ev.preventDefault();
      return;
    }
    if (ch === 'p') {
      wsSend({ type: 'key', key: 'Page_Up' });
      suppressKeypress = true;
      ev.preventDefault();
      return;
    }
    if (ch === 't') {
      wsSend({ type: 'key', key: 'Home' });
      suppressKeypress = true;
      ev.preventDefault();
      return;
    }
    if (ch === 'b') {
      wsSend({ type: 'key', key: 'End' });
      suppressKeypress = true;
      ev.preventDefault();
      return;
    }
    if (ch === '/' || kc === 191) {
      wsSend({ type: 'key', key: 'slash' });
      suppressKeypress = true;
      ev.preventDefault();
      return;
    }
    if (CFG.preset === 'x' && X_DIRECT_KEYS[ch]) {
      wsSend({ type: 'key', key: X_DIRECT_KEYS[ch] });
      if (ch === 'n' || ch === 'r') {
        setTimeout(openBar, 180);
      }
      suppressKeypress = true;
      ev.preventDefault();
      return;
    } else if (kc === 13) {
      wsSend({ type: 'key', key: 'Return' });
      suppressKeypress = true;
      ev.preventDefault();
    } else if (kc === 27) {
      wsSend({ type: 'key', key: 'Escape' });
      suppressKeypress = true;
      ev.preventDefault();
    } else if (kc === 8) {
      wsSend({ type: 'key', key: 'BackSpace' });
      suppressKeypress = true;
      ev.preventDefault();
    } else if (kc === 9) {
      wsSend({ type: 'key', key: 'Tab' });
      suppressKeypress = true;
      ev.preventDefault();
    }
  }, false);

  document.addEventListener('keypress', function (ev) {
    if (!typeMode || suppressKeypress) { return; }
    var active = document.activeElement;
    var tag = active ? active.tagName : '';
    if (active === msgEl || tag === 'TEXTAREA' || tag === 'INPUT') { return; }
    if (ev.ctrlKey || ev.altKey || ev.metaKey) { return; }
    var cc = ev.charCode || ev.which || ev.keyCode || 0;
    if (cc >= 33 && cc <= 126) {
      wsSend({ type: 'type', text: String.fromCharCode(cc) });
      ev.preventDefault();
    }
  }, false);

  // Visibility & lifecycle sleep hooks
  function onVisChange() { updatePauseState(null); }
  document.addEventListener('visibilitychange', onVisChange, false);
  document.addEventListener('webkitvisibilitychange', onVisChange, false);
  window.addEventListener('pagehide', function () { updatePauseState(true); }, false);
  window.addEventListener('pageshow', function () { updatePauseState(false); }, false);
  window.addEventListener('resize', function () { sendResize(); }, false);
  window.addEventListener('scroll', function () {
    if (window.pageXOffset !== 0 || window.pageYOffset !== 0) {
      window.scrollTo(0, 0);
    }
  }, false);

  syncStageLayout();
  connectWs();
})();
</script>
</body>
</html>
"""
    )
