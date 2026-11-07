#!/usr/bin/env bash
# Compatibility with past one-command releases; one installer handles all modes.
set -Eeuo pipefail
exec bash "$(dirname "$0")/install.sh" "$@"
