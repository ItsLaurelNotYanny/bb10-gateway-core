#!/usr/bin/env bash
# Project-gate: configure stack checks before use. Checks must not modify source.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
FAST=0
case "${1:-}" in
    "") [ "$#" -eq 0 ] || { echo "ERROR: unexpected arguments" >&2; exit 2; } ;;
    --fast) [ "$#" -eq 1 ] || { echo "ERROR: unexpected arguments" >&2; exit 2; }; FAST=1 ;;
    *) echo "Usage: ./check.sh [--fast]" >&2; exit 2 ;;
esac
MODE=full
[ "$FAST" -eq 0 ] || MODE=fast
umask 077
LOG=$(mktemp "${TMPDIR:-/tmp}/project-gate.XXXXXX")
trap 'echo "ERROR: gate interrupted; log=$LOG" >&2; exit 2' INT TERM
need() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "ERROR: missing required tool: $1; log=$LOG" >&2
        exit 2
    fi
}
COUNT=0
run() {
    local label=$1 status
    shift
    printf '\n--- %s ---\n' "$label" >>"$LOG"
    if "$@" >>"$LOG" 2>&1; then
        COUNT=$((COUNT + 1))
    else
        status=$?
        printf 'FAIL: %s (exit=%s); log=%s\n' "$label" "$status" "$LOG" >&2
        tail -n 60 "$LOG" | { head -c 8000; cat >/dev/null; } >&2
        printf '\n' >&2
        case "$status" in 126|127) exit 2 ;; *) exit 1 ;; esac
    fi
}
# --- stack checks (Python 3.11+: Ruff format/lint + pytest) ---
export PATH="$PWD/.venv/bin:$HOME/.local/bin:$PATH"
need ruff
run "Python format" ruff format --check .
run "Python lint" ruff check .
if [ "$FAST" -eq 0 ]; then
    need node
    need pytest
    run "Python tests" pytest -q
fi
# --- custom checks (preserve during refresh) ---
shopt -s nullglob
sh_files=(*.sh .githooks/* contrib/relay/*.sh scripts/*.sh)
shopt -u nullglob
if [ "${#sh_files[@]}" -gt 0 ]; then
    run "Shell syntax" bash -n "${sh_files[@]}"
fi
check_no_tracked_secrets() {
    local bad
    bad=$(git ls-files | grep -E '^(certs|data)/|(^|/)token\.txt$|\.(key|crt|cer|tar\.gz)$' || true)
    if [ -n "$bad" ]; then
        printf 'Forbidden secret/artifact files tracked in git:\n%s\n' "$bad" >&2
        return 1
    fi
}
need git
check_no_private_strings() {
    local hits
    hits=$(git ls-files -z -- . ':!check.sh' | xargs -0 grep -nIE \
        -e '(^|[^0-9.])(10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|192\.168\.[0-9]{1,3}\.[0-9]{1,3}|172\.(1[6-9]|2[0-9]|3[01])\.[0-9]{1,3}\.[0-9]{1,3})([^0-9]|$)' \
        -e '100\.(6[4-9]|[7-9][0-9]|1[01][0-9]|12[0-7])\.[0-9]{1,3}\.[0-9]{1,3}([^0-9]|$)' \
        -e '/home/[a-z]+/|ellery@|ssh-key-[0-9]|nas-au|eq12pro|EmailProxy Root' \
        || true)
    if [ -n "$hits" ]; then
        printf 'Private strings found in tracked files:\n%s\n' "$hits" >&2
        return 1
    fi
}
run "Tracked secret exclusion" check_no_tracked_secrets
run "Private string leak scan" check_no_private_strings
[ "$COUNT" -gt 0 ] || { echo "ERROR: no checks ran; log=$LOG" >&2; exit 2; }
printf 'OK: project-gate (%s, checks=%s)\n' "$MODE" "$COUNT"
rm -f -- "$LOG"
