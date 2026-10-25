#!/bin/sh
# Resolve the release once so code, templates, content and assets stay together.
set -eu
release=$(readlink -f /var/www/jackieleven/go-current)
case "$release" in
  /var/www/jackieleven/go-releases/*) ;;
  *) echo 'Invalid Go release target' >&2; exit 1 ;;
esac
exec "$release/bin/jackieleven" -root "$release" -listen 127.0.0.1:18765 -trust-proxy
