#!/bin/bash
# Publish only the static holding page and its two fonts.
set -euo pipefail
cd "$(dirname "$0")/.."
SERVER=root@77.42.46.154
PORT=29742
STORE=/var/www/jackieleven/releases
SSH=(ssh -o BatchMode=yes -p "$PORT" "$SERVER")
stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT
release="$(date -u +%Y%m%d%H%M%S)-$RANDOM"
mkdir -p "$stage/assets/fonts"
cp interim/index.html interim/robots.txt "$stage/"
cp assets/fonts/newsreader-normal.woff2 assets/fonts/space-grotesk-normal.woff2 \
   assets/fonts/newsreader-OFL.txt assets/fonts/spacegrotesk-OFL.txt "$stage/assets/fonts/"
printf '%s\n' "$release" > "$stage/release-id.txt"
find "$stage" -type d -exec chmod 755 {} +
find "$stage" -type f -exec chmod 644 {} +
if [ "${1:-}" = --prepare ]; then
    echo "Interim package prepared: $release"
    exit
fi
if [ "$#" -ne 0 ]; then
    echo 'Usage: bash ops/deploy-interim.sh [--prepare]' >&2
    exit 2
fi
"${SSH[@]}" "mkdir -p '$STORE'; mkdir '$STORE/$release'"
rsync -az --no-owner --no-group -e "ssh -p $PORT" "$stage/" "$SERVER:$STORE/$release/"
"${SSH[@]}" bash -s -- "$release" <<'REMOTE'
set -euo pipefail
release=$1
cd /var/www/jackieleven
if [ -L current ]; then
    ln -sfn "$(readlink current)" previous.next
    mv -Tf previous.next previous
elif [ -e current ]; then
    echo 'Refusing to replace a non-symlink current path' >&2
    exit 1
fi
ln -s "releases/$release" current.next
mv -Tf current.next current
REMOTE
echo "Interim release activated: $release"
