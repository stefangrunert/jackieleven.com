#!/bin/sh
# macOS user service for the local Go website. Run from any directory.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
LABEL=com.stefan.jackieleven.go
DOMAIN="gui/$(id -u)"
AGENT="$HOME/Library/LaunchAgents/$LABEL.plist"
BINARY="$ROOT/.dev/bin/jackieleven-local"

build() (
    cd "$ROOT"
    mkdir -p .dev/bin
    build_tmp=$(mktemp "$ROOT/.dev/bin/jackieleven-local.XXXXXX")
    trap 'rm -f "$build_tmp"' EXIT HUP INT TERM
    go build -trimpath -o "$build_tmp" ./cmd/jackieleven
    chmod 755 "$build_tmp"
    mv -f "$build_tmp" "$BINARY"
)
stop() {
    if launchctl print "$DOMAIN/$LABEL" >/dev/null 2>&1; then
        launchctl bootout "$DOMAIN/$LABEL"
    fi
}
start() {
    test -f "$AGENT" && test -x "$BINARY" || {
        echo 'Run ops/go-local.sh install first.' >&2
        exit 1
    }
    launchctl enable "$DOMAIN/$LABEL"
    if ! launchctl print "$DOMAIN/$LABEL" >/dev/null 2>&1; then
        launchctl bootstrap "$DOMAIN" "$AGENT"
    fi
}
install() {
    build
    mkdir -p "$ROOT/.dev/logs" "$ROOT/.dev/runtime/local-contact"
    chmod 700 "$ROOT/.dev/runtime/local-contact"
    stop
    python3 - "$ROOT" "$AGENT" "$LABEL" <<'PY'
import os, pathlib, plistlib, sys, tempfile
root, target, label = sys.argv[1:]
p = pathlib.Path(target)
p.parent.mkdir(parents=True, exist_ok=True)
config = {
    'Label': label,
    'ProgramArguments': [root+'/.dev/bin/jackieleven-local', '-root', root,
                         '-listen', '127.0.0.1:8080', '-trust-proxy'],
    'WorkingDirectory': root,
    'EnvironmentVariables': {
        'JACKIE_RESEND_API_KEY': '', 'JACKIE_TURNSTILE_SITEKEY': '',
        'JACKIE_TURNSTILE_SECRET': '',
        'JACKIE_CONTACT_STATE_DIR': root+'/.dev/runtime/local-contact',
    },
    'RunAtLoad': True, 'KeepAlive': True, 'ThrottleInterval': 5,
    'ExitTimeOut': 35,
    'StandardOutPath': root+'/.dev/logs/go-local.out.log',
    'StandardErrorPath': root+'/.dev/logs/go-local.err.log',
}
with tempfile.NamedTemporaryFile(dir=p.parent, prefix=label+'.', delete=False) as f:
    temporary = pathlib.Path(f.name)
    plistlib.dump(config, f)
try:
    temporary.chmod(0o644)
    os.replace(temporary, p)
finally:
    temporary.unlink(missing_ok=True)
PY
    plutil -lint "$AGENT"
    start
}
case "${1:-status}" in
    install) install ;;
    build) build ;;
    restart) build; stop; start ;;
    reload) stop; start ;;
    start) start ;;
    stop) stop ;;
    status) launchctl print "$DOMAIN/$LABEL" ;;
    logs) tail -n 60 "$ROOT/.dev/logs/go-local.err.log" ;;
    *) echo 'Usage: ops/go-local.sh install|build|restart|reload|start|stop|status|logs' >&2; exit 2 ;;
esac
