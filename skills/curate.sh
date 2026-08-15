#!/bin/sh
# Remove write protection so the maintainer can edit the canonical skills.
# Run protect.sh afterwards to restore.
cd "$(dirname "$0")" || exit 1
chmod -R +w .
echo "skills are writable (curate, then run protect.sh)"
