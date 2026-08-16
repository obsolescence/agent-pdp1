---
name: pdp1-plumbing
description: operating the PiDP-1 — unserstanding the setup: connections, typewriter, the display rule, the copilot model, starting/loading. Details on the control protocol itself lives in pdp1-debugging.
---

# PiDP-1 Plumbing — how the setup works

Your role is to be assistant to and programmer for the user of this 
PDP-1 replica, called a PiDP-1. 

4 ports connect you to the PDP-1. Only port 1041 should be used directly.
Important: the other three must be used through the specified helper programs
(pdp1_dpy, pdp1dbg.py and pdp1ctl tools).

| Port | Surface | Who uses it |
| ---- | ------- | ----------- |
| 1040 | debug interface (line protocol) | agent drives the machine here, including control over front panel |
| 1041 | typewriter telnet (fan-out) | agent AND the user share the same typewriter |
| 1050 | paper-tape control (pdp1_periph) | pdp1ctl + GUI tools; the human-visible mount path |
| 3400 | Type 30 display stream (fan-out) | agent and pdp1_periph can watch concurrently |

Connection limits: 1040 up to 8, typewriter 4, display 4, reader/punch 1.

## 1041 — shared typewriter

Acts as user terminal. Telnet, FIO-DEC/ASCII translation built in. Output fans out to every
client; input from any client reaches the machine. Don't type into a
program that is waiting for the user; don't assume a prompt came from
you.

## 3400 — shared Type 30 display

A graphics display. You are NEVER allowed to read this stream directly. It wastes tokens.
Use the pdp1_dpy tool to analyse snapshots of Type 30 input. Details
in the pdp1-type30-vision skill! Fan-out means an agent capture does
not disturb pdp1_periph's picture.

## 1040 — debug interface

This is where the agent controls the machine: memory, registers, run
control, breakpoints, watchpoints, stepping, tape devices, the light
pen, and the front panel (you can override the actual front panel
under your control). **The full protocol — every command, every
semantics — is in the pdp1-debugging skill; load it before driving.**

**You are not supposed to connect to this port raw.**. Use the 
`pdp1dbg.py` helper from pdp1-debugging — one command per
invocation, or stdin batch mode for sequences that must share one
connection. A raw socket means reimplementing the framing (read until
`+` or `-`, skip `!` events) and getting pending commands wrong;
one-shot `ncat` is only for humans poking and for instant-reply verbs
(`hello`, `load`, `muldiv on`); NEVER use it for `step`/`run`/
`until`/`go`/`wait` — those withhold their reply until the machine
stops, and a closing connection cancels them (and their temporary
breakpoints).

## Copilot model

- Machine state is global and shared; run control is last-write-wins.
- `claim` is advisory and rarely needed; breakpoints are global with
  an owner, temporary ones die with their connection.
- On disconnect the server cancels your pending command and clears
  your override bits (no SINST residue).
- `!panel` events report human activity at the panel — when the human
  is at the machine, stop and let them drive.
- Access to `/dev/shm/pidp1` or `/tmp/pdp1_panel` is deprecated and
  prohibited. All front panel operations must go through port 1040.

## Gotchas (one line each)

- Opcode 0 is **not** HLT; real HLT is `760400`.
- Panel EXAMINE/DEPOSIT keys are destructive — use `e`/`d` on 1040.
- Always use bounded runs (`run 1000`, `until x 1000`).
- `w pc <addr>` while halted sets PC cleanly (no EXAMINE/START dance).
- Octal addresses/words, decimal counts — always.

## Building and starting

The emulator source lives in the production tree at
`/opt/pidp1/src/blincolnlights/pdp1` — a nested git repo; check
`git remote -v` before assuming which repo you are in.

```bash
cd /opt/pidp1/src/blincolnlights/pdp1
make                    # builds pdp1 + pdp1_b18
```

Start headless and deterministic for scripts and tests:

```bash
./pdp1 -t               # no coremem load/dump, POWER forced on
```

Normal use — the emulator is a service on your machine:

```bash
pdp1control start       # start it (launches the panel driver too:
                        #   vpanel for the virtual panel,
                        #   panel_pidp1 for hardware)
pdp1control stat        # is it running?
pdp1control stop        # stop it
```

The Type 30 GUI (pdp1_periph) connects directly to 1040/3400; it needs
no port flags.

Sanity check: `pdp1dbg.py 'hello'` → `+ proto=1 machine=pdp1 …`.
(Humans may use `echo hello | ncat -w 1 localhost 1040` — hello is
instant-reply.)

Nothing answering? The helper's connection error says "is the emulator
running?" — check `pdp1control stat`; if it is not running,
`pdp1control start`, then try again.

## Loading a program

Assemble with `macro1_1 -r program.mac` (details in pdp1-assembly;
`-r` is REQUIRED for the `l` command, `start` must be the last line, 
and the assembler will eat the first line as a header).
The `.rim` and `.lst` land in the current directory — copy the tape
to where the emulator can see it (network filenames are confined to
the tape directory, relative paths only).

```bash
pdp1dbg.py 'l program.rim'    # quick load into core, no start
pdp1dbg.py 'r program.rim'    # mount in reader (for READ-IN)
```

**Three load routes — pick by who is watching:**

| route | command | periph | panel | speed |
| ----- | ------- | ------ | ----- | ----- |
| core load | `l <file>` (1040) | — | — | instant |
| reader mount | `r <file>` (1040) | — | reader | instant |
| human mount | `pdp1ctl r <path>` (1050) | shows | shows | realistic |

`l` is the fastest for pure-RIM tapes (`macro1_1 -r`) but loads
core only — no start, no panel, no periph; set the entry
(`w pc <entry>` + `go`). `r` (1040) mounts in the reader, any
format, needs a READ-IN push (`key readin`). 1050 is the human's
lane: real mount at real speed, visible everywhere, the human
presses READ-IN — use it when the USER asked for the load.

**`l` lies on block tapes:** it parses RIM only — on a block tape
it loads the RIM bootstrap as data and reports success with the
program absent. macro1_1's default output is a block tape; only
`-r` emits pure RIM. When in doubt, verify with
`pdp1dbg.py --lst prog.lst 'check'` — "0 of N words differ".

  The tape directory is the emulator's working directory unless it was
  started with -D <tapedir>. pdp1control passes no -D, so on the
  default install tapes under /opt/pidp1/tapes mount as
  tapes/<name>.rim — not as <name>.rim.

Entry point from the listing: `grep 'go,' program.lst` — the address
field. Then over 1040: `pdp1dbg.py 'w pc <entry>' 'go'` (or
`go <entry>`).

The verified quick-load sequence (agent's own output):

    macro1_1 -r line.mac              # pure RIM (see block-tape warning)
    cp line.rim /opt/pidp1/tapes/
    # stop the machine first
    pdp1dbg.py 'l tapes/line.rim'
    pdp1dbg.py --lst line.lst 'check'     # "0 of N words differ" = landed
    pdp1dbg.py 'w pc 4' 'go'          # entry from the listing

## Where things live

- pdp1-debugging — the port-1040 protocol, recipes, the pdp1dbg helper client
- pdp1-assembly — writing programs: instruction set, MACRO-1, patterns
- pdp1-type30-vision — reading the screen (pdp1_dpy tool)
- pdp1-tutor — guided tours of PDP-1 applications (in preparation)
- pdp1-code-review — structured code review / design-handbook workflow (in preparation)
- pdp1-learnings — the local, per-agent bucket; load it with any pdp1 skill
