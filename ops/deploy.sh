#!/bin/bash
# Build an allowlisted PHP release; uploading requires --deploy explicitly.
set -euo pipefail
cd "$(dirname "$0")/.."
SERVER=root@77.42.46.154
PORT=29742
BASE=/var/www/jackieleven
SSH=(ssh -o BatchMode=yes -p "$PORT" "$SERVER")

if [ "$#" -eq 2 ] && [ "$1" = --prepare ]; then
    exec php ops/prepare-release.php "$2"
fi
if [ "$#" -ne 1 ] || [ "$1" != --deploy ]; then
    echo 'Usage: bash ops/deploy.sh --prepare NEW_DIRECTORY | --deploy' >&2
    exit 2
fi

stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT
release="$(date -u +%Y%m%d%H%M%S)-$RANDOM"
php ops/prepare-release.php "$stage/release"
# This uses separate links from the holding page. The vhost is configured separately.
"${SSH[@]}" "mkdir -p '$BASE/site-releases'; mkdir '$BASE/site-releases/$release'"
rsync -az --no-owner --no-group -e "ssh -o BatchMode=yes -p $PORT" \
    "$stage/release/" "$SERVER:$BASE/site-releases/$release/"
"${SSH[@]}" bash -s -- "$release" <<'REMOTE'
set -euo pipefail
release=$1
cd /var/www/jackieleven
cd "site-releases/$release"
sha256sum --check --status release-manifest.sha256
php -r 'if (PHP_VERSION_ID < 80100) exit(1); foreach (["curl", "mbstring", "session", "iconv"] as $ext) if (!extension_loaded($ext)) { fwrite(STDERR, "Missing PHP extension: $ext\n"); exit(1); }'
while IFS= read -r -d '' file; do php -l "$file" >/dev/null; done < <(find . -name '*.php' -print0)
# Runtime smoke checks before switching the active release; never submit a contact form.
php -d display_errors=stderr -r '$_SERVER["REQUEST_URI"]="/de/"; require "public/index.php";' >/dev/null
php -d display_errors=stderr -r '$_SERVER["REQUEST_URI"]="/en/deep-pool"; require "public/index.php";' >/dev/null
cd ../..
if [ -L site-current ]; then
    ln -sfn "$(readlink site-current)" site-previous.next
    mv -Tf site-previous.next site-previous
elif [ -e site-current ]; then
    echo 'Refusing to replace a non-symlink site-current path' >&2
    exit 1
fi
ln -s "site-releases/$release" site-current.next
mv -Tf site-current.next site-current
REMOTE
echo "PHP release activated: $release"
echo "Required vhost DocumentRoot: $BASE/site-current/public (see ops/nginx-site.conf)"
