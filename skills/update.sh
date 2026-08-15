#!/bin/sh
# Pull the latest skills from github, then write-protect again.
cd "$(dirname "$0")" || exit 1
chmod -R +w .
if git rev-parse --git-dir >/dev/null 2>&1; then
    git pull
else
    echo "no git repository here — nothing to pull"
fi
chmod -R -w .
echo "skills are write-protected again"
