# SOUL.md — PiDP-1 agent instructions

## pdp1 skills
- The pdp1 skills are a frozen, curated set. NEVER edit them.
- New knowledge goes to pdp1-learnings — load it with every pdp1 skill.
- Learnings: PUBLISHABLE (generic) or LOCAL (machine-specific);
  format date, TARGET, CLAIM, WHY. When in doubt: LOCAL.
- Factual error in a skill: tell the user NOW, then file it.
- Curation scan is done on request: propose changes, never apply them.

## Machine rules
- Drive the PDP-1 via port 1040. Octal words, decimal counts.
- Never read port 3400 raw — use pdp1_dpy.
- /dev/shm/pidp1 and /tmp/pdp1_panel: prohibited.
- Bounded runs only. 0 is not HLT (760400 is).
- Human at the machine (!panel) → stop, let them drive.
