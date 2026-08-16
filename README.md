# agent-pdp1

AI copilot skills and tools for the PiDP-1. This package turns an AI
agent (Hermes Agent, Claude Code, OpenCode, or any agent that reads markdown
skills) into a helpful copilot for your PDP-1: 
- writing and assembling programs, debugging code, 
- handling the front panel, and the whole machine,
- reading and visually interpreting the Type 30 display. 

Or, much more fun: 
- Let it be your tutor, interactive guide through the PDP-1 world.
- Let it review source code. The Code Review skill is an amazing teacher!

Works on a PiDP-1 (needs 4, perhaps 2 GB of RAM) or any regular Linux  
that has the pidp1 package already installed. 

## Eye candy

<Tic-tac-toe> <Rotating-cube> <dodecahedron> <hello-world-typewriter>

## Install

    git clone https://github.com/obsolescence/agent-pdp1.git /opt/agent-pdp1
    cd /opt/agent-pdp1
    ./install.sh        # updates the emulator, 
						# and installs agent tools
    ./setup-hermes.sh   # explains/helps with installing Hermes Agent,
                        #   then wires the skills into Hermes Agent 
                        #   (explains getting an API key and install guidance)

Both scripts explain each step as they run; every step can be declined.
The setup-hermes script will guide you through obtaining a Deepseek API key.
There is no particular reason to use Deepseek-v4-Flash. It is just, at the 
time of writing, the cheapest. And very much good enough. But Hermes will
let you use any model, up to Fable if you feel like spending the money.
But: not necessary. Hermes is good with cheaper models, try that first,
add other models later on. It can be done 'on the fly'.

## What's inside

skills/ — the six skills, frozen and human-curated. Instead of editing these
skills, agents are instructed to write what they learn to their own 
pdp1-learnings skill file. 

You can decide otherwise, we noticed that it 
is better to go through the isolated learnings text file rather than have
the 'canonical knowledge' polluted by agents in their moments of confusion.


- pdp1-assembly      — instruction set, MACRO-1, patterns
- pdp1-debugging     — the port-1040 protocol, recipes, the pdp1dbg helper client
- pdp1-plumbing      — ports, copilot etiquette, building/starting/loading/updating
- pdp1-type30-vision — reading the screen (pdp1_dpy tool)
- pdp1-tutor         — guided tours of PDP-1 applications (in preparation)
- pdp1-code-review   — structured code review workflow

hermes-specific/ — SOUL.md (the rules file Hermes reads on every
request) and the pdp1-learnings template (the agent's own learning
file, copied per install, never shared).

If you are new to this, using Hermes as your agent is probably the best
idea. It has been carefully set up so as to actively learn from new
experience, without messing up the 'canonical knowledge base'.

## Updating

    ./skills/update.sh    # unprotect, git pull, re-protect

