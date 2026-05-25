#!/bin/sh
# Repair permissions on mounted volumes so host-side git can read all files.
# Directories need +x, files need +r. This is a no-op if already correct.
chmod -R a+rX /repo/infra 2>/dev/null || true
if [ -f /repo/theme.yml ]; then chmod a+r /repo/theme.yml 2>/dev/null || true; fi

# Set umask so every file the backend creates is readable by all (644/755).
umask 0022

exec "$@"
