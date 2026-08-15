#!/bin/sh
# Write-protect the frozen pdp1 skills in this directory.
# pdp1-learnings is intentionally NOT here — it lives in the agent's
# home (installed by setup-hermes.sh) and must stay writable.
cd "$(dirname "$0")" || exit 1
chmod -R -w .
echo "skills are write-protected"
