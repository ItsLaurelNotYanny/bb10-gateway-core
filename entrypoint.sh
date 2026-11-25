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
from presets import load_preset, preset_scale
p = load_preset()
print(f"EFF_RUNTIME={p.runtime!r}")
print(f"EFF_TARGET_URL={p.target_url!r}")
print(f"EFF_WIN_W={p.win_w}")
print(f"EFF_WIN_H={p.win_h}")
print(f"EFF_LOCK_H={p.lock_win_h}")
print(f"EFF_SCALE={preset_scale(p)}")
')"

XVFB_H=1080
if [ "${EFF_LOCK_H}" = "True" ]; then
    XVFB_H="${EFF_WIN_H}"
fi
PHYS_WIN_W=$((EFF_WIN_W * EFF_SCALE))
PHYS_WIN_H=$((EFF_WIN_H * EFF_SCALE))
PHYS_XVFB_H=$((XVFB_H * EFF_SCALE))
Xvfb "$DISPLAY" -screen 0 "${PHYS_WIN_W}x${PHYS_XVFB_H}x24" -ac -nolisten tcp -noreset >/dev/null 2>&1 &
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
if [ -d "/etc/X11/Xresources" ]; then
    for res in /etc/X11/Xresources/*; do
        [ -f "$res" ] && xrdb -merge "$res" 2>/dev/null || true
    done
elif [ -f "/etc/X11/Xresources" ]; then
    xrdb -merge "/etc/X11/Xresources" 2>/dev/null || true
fi
if [ "$EFF_SCALE" -gt 1 ]; then
    export QT_SCALE_FACTOR="$EFF_SCALE"
    export QT_AUTO_SCREEN_SCALE_FACTOR=0
    export GDK_SCALE="$EFF_SCALE"
    export GDK_DPI_SCALE=1
    printf "Xft.dpi: %d\n" $((96 * EFF_SCALE)) | xrdb -merge 2>/dev/null || true
fi
if [ -f "$HOME/.Xresources" ]; then
    xrdb -merge "$HOME/.Xresources" 2>/dev/null || true
fi

APP_LOOP_PID=""
if [ "$EFF_RUNTIME" = "xterm" ]; then
    XTERM_ARGS=(-u8 -geometry 71x35+0+0)
    if ! grep -q 'XTerm\*faceName' "$HOME/.Xresources" 2>/dev/null; then
        XTERM_ARGS+=(-fa "Noto Sans Mono" -fd "Noto Sans Mono CJK SC" -fs 10 -bg "#000000" -fg "#e7e9ea")
    fi
    (
        while true; do
            xterm "${XTERM_ARGS[@]}" -e /app/term_session.sh >/dev/null 2>&1 || true
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
                --disable-gpu \
                --password-store=basic \
                --no-first-run \
                --no-default-browser-check \
                --disable-notifications \
                --disable-smooth-scrolling \
                --force-prefers-reduced-motion \
                --user-data-dir=/data/profile \
                --window-position=0,0 \
                --window-size="${EFF_WIN_W},${EFF_WIN_H}" \
                --force-device-scale-factor="${EFF_SCALE}" \
                --app="${EFF_TARGET_URL}" \
                >/tmp/chromium.log 2>&1 || true
            sleep 0.5
        done
    ) &
    APP_LOOP_PID=$!
elif [ "$EFF_RUNTIME" = "native_gui" ]; then
    GUI_BIN="$EFF_TARGET_URL"
    if [ -x "$GUI_BIN" ] || command -v "$GUI_BIN" >/dev/null 2>&1; then
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
    for _ in $(seq 1 50); do
        if xdotool search --onlyvisible --name . windowmove 0 0 windowsize "$PHYS_WIN_W" "$PHYS_WIN_H" windowfocus 2>/dev/null; then
            break
        elif wmctrl -r ":ACTIVE:" -e "0,0,0,${PHYS_WIN_W},${PHYS_WIN_H}" 2>/dev/null; then
            break
        fi
        sleep 0.2
    done
) &

cleanup() {
    [ -z "$APP_LOOP_PID" ] || kill -TERM "$APP_LOOP_PID" 2>/dev/null || true
    kill -TERM "$OPENBOX_PID" "$XVFB_PID" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

exec python3 /app/gateway.py
