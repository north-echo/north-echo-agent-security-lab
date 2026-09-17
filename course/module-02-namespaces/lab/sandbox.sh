#!/bin/sh
set -eu

if [ "$#" -eq 0 ]; then
  echo "usage: $0 COMMAND [ARG ...]" >&2
  exit 2
fi

# Intentional starter flaw: this does not create any isolation.
exec "$@"
