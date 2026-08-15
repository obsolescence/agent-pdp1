The frozen pdp1 skill set lives here (six skills).

update.sh: run to get the latest skills from github. Unprotects, pulls, re-protects.
curate.sh: remove write protection so the maintainer can edit these canonical skills.
protect.sh: write-protect again, so confused agents will not mess up the skills.

pdp1-learnings is NOT in this directory on purpose. It is a local,
per-agent file: setup-hermes.sh copies it into the agent's home, and
the agent appends to it freely. It must never be symlinked, protected,
or pulled over.
