#!/usr/bin/env bash
set -euo pipefail

export DISPLAY="${DISPLAY:-:99}"
export LANG="${LANG:-C.UTF-8}"
export LC_ALL="${LC_ALL:-C.UTF-8}"

mkdir -p /data/profile 2>/dev/null || true

# Normalized Sandbox & Lock Cleanup: remove stale X11 locks and Chromium singleton locks
rm -f "/tmp/.X${DISPLAY#:}-lock" "/tmp/.X11-unix/X${DISPLAY#:}" \
      /data/profile/SingletonLock \
      /data/profile/SingletonCookie \
      /data/profile/SingletonSocket 2>/dev/null || true

eval "$(python3 -c '
from presets import load_preset
p = load_preset()
print(f"EFF_RUNTIME={p.runtime!r}")
print(f"EFF_TARGET_URL={p.target_url!r}")
print(f"EFF_WIN_W={p.win_w}")
print(f"EFF_WIN_H={p.win_h}")
')"

Xvfb "$DISPLAY" -screen 0 1280x1080x24 -ac -nolisten tcp -noreset >/dev/null 2>&1 &
XVFB_PID=$!

for _ in $(seq 1 30); do
    if [ -S "/tmp/.X11-unix/X${DISPLAY#:}" ]; then
        break
    fi
    sleep 0.1
done

if command -v dbus-daemon >/dev/null 2>&1; then
    mkdir -p /tmp/dbus
    DBUS_ADDR=$(dbus-daemon --session --fork --print-address)
    export DBUS_SESSION_BUS_ADDRESS="$DBUS_ADDR"
fi

openbox >/dev/null 2>&1 &
OPENBOX_PID=$!
sleep 0.2

xsetroot -solid "#000000" 2>/dev/null || true
if [ -f "$HOME/.Xresources" ]; then
    xrdb -merge "$HOME/.Xresources" 2>/dev/null || true
fi

APP_LOOP_PID=""
if [ "$EFF_RUNTIME" = "xterm" ]; then
    (
        while true; do
            xterm -u8 -fa "Noto Sans Mono" -fd "Noto Sans Mono CJK SC" -fs 10 \
                -bg "#000000" -fg "#e7e9ea" -geometry 71x35+0+0 \
                -e /app/term_session.sh >/dev/null 2>&1 || true
            sleep 0.5
        done
    ) &
    APP_LOOP_PID=$!
elif [ "$EFF_RUNTIME" = "chromium" ]; then
    (
        while true; do
            chromium \
                --no-sandbox \
                --test-type \
                --disable-infobars \
                --noerrdialogs \
                --disable-session-crashed-bubble \
                --disable-dev-shm-usage \
                --use-gl=angle \
                --use-angle=gl-egl \
                --ignore-gpu-blocklist \
                --password-store=basic \
                --no-first-run \
                --no-default-browser-check \
                --disable-notifications \
                --disable-smooth-scrolling \
                --force-prefers-reduced-motion \
                --user-data-dir=/data/profile \
                --window-position=0,0 \
                --window-size="${EFF_WIN_W},${EFF_WIN_H}" \
                --app="${EFF_TARGET_URL}" \
                >/tmp/chromium.log 2>&1 || true
            sleep 0.5
        done
    ) &
    APP_LOOP_PID=$!
elif [ "$EFF_RUNTIME" = "native_gui" ]; then
    GUI_BIN="$EFF_TARGET_URL"
    if [ ! -x "$GUI_BIN" ] && [ -x "/usr/bin/wechat" ]; then
        GUI_BIN="/usr/bin/wechat"
    fi
    if [ -x "$GUI_BIN" ]; then
        (
            while true; do
                "$GUI_BIN" >/tmp/native_gui.log 2>&1 || true
                sleep 0.5
            done
        ) &
        APP_LOOP_PID=$!
    fi
fi

(
    for _ in $(seq 1 30); do
        if xdotool search --onlyvisible --name . windowmove 0 0 windowsize "$EFF_WIN_W" "$EFF_WIN_H" windowfocus 2>/dev/null; then
            break
        fi
        sleep 0.1
    done
) &

cleanup() {
    [ -z "$APP_LOOP_PID" ] || kill -TERM "$APP_LOOP_PID" 2>/dev/null || true
    kill -TERM "$OPENBOX_PID" "$XVFB_PID" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

exec python3 /app/gateway.py
