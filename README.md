# agent-pdp1

AI copilot skills and tools for the PiDP-1. This package turns an AI
agent (Hermes Agent, Claude Code, or any agent that reads markdown
skills) into a helpful copilot for your PDP-1: writing and assembling
programs, debugging a running machine over the debug port, operating
the emulator, and reading the Type 30 display.

Works on a Raspberry Pi or a regular Linux machine running the
blincolnlights PDP-1 emulator (dbg branch). The dbg update lets the
simulator handle the user and an AI agent concurrently.

## Install

    git clone https://github.com/obsolescence/agent-pdp1.git /opt/agent-pdp1
    cd /opt/agent-pdp1
    ./install.sh        # updates the emulator to the dbg branch, installs
                        # the agent tools, runs a smoke test
    ./setup-hermes.sh   # wires the skills into Hermes Agent (API key and
                        # install guidance included)

Both scripts explain each step as they run; every step can be declined.

## What's inside

skills/ — the six skills, frozen and human-curated. Agents write what
they learn to their own pdp1-learnings file instead of editing these:

- pdp1-assembly      — instruction set, MACRO-1, patterns
- pdp1-debugging     — the port-1040 protocol, recipes, the pdp1dbg helper client
- pdp1-plumbing      — ports, copilot etiquette, building/starting/loading/updating
- pdp1-type30-vision — reading the screen (pdp1_dpy tool)
- pdp1-tutor         — guided tours of PDP-1 applications (in preparation)
- pdp1-code-review   — structured code review workflow

hermes-specific/ — SOUL.md (the rules file Hermes reads on every
request) and the pdp1-learnings template (the agent's own learning
file, copied per install, never shared).

## Updating

    ./skills/update.sh    # unprotect, git pull, re-protect

## License

MIT
