---
name: pdp1-tutor
description: |-
  Guided tours of the PDP-1 — in-machine assembly with ET/MACRO/DDT,
  cross-assembly from Linux, PDP-1 Lisp, games and demos. Run in
  drive mode (agent operates and narrates) or coach mode (user
  operates, agent reveals one step at a time). Use when taking a
  user through a guided PDP-1 session or coaching hands-on work.
---

# PDP-1 Guided Tours

This skill runs the guided tours: sequences of small steps that take a
user from "machine is up" to "I wrote, assembled, ran and debugged a
program on a 1959 computer" — or just to "look at the pretty display
hacks". It sequences and narrates; the mechanics live in the reference
skills (pdp1-plumbing, pdp1-assembly, pdp1-debugging, pdp1-type30-vision)
and are pointed to, never duplicated.

## Step shape

Every step has the same three-part shape, which is what makes a tour
drivable in any mode:

    DO      what to do (or type)
    SEE     what you should observe if it worked
    IF NOT  the common failure and its fix

## Running modes

Agree the mode at tour start — one line: "drive, coach, or assist?"

- **drive** — the agent operates the machine and narrates. The
  narration is the deliverable: say what you are about to do and why
  before each DO, and read the SEE out loud. Never run a silent magic
  show.
- **coach** — the user operates. Reveal one DO at a time, never the
  whole script. Ask for the SEE ("what do you see?") and only advance
  on a match. On an IF NOT, diagnose — don't skip.
- **assist** — split: the agent does the fiddly parts (mount tapes,
  deposit words, drive the ports), the user does the fun parts (panel,
  display, typing at ET). This is the normal co-driving setup: user at
  vpanel, agent on ports 1040/1050.

If a human is at the machine (!panel), stop and let them drive.

## Tour map

| Tour | What | Pace |
|---|---|---|
| 1 | Assembly on the PDP-1 — ET → MACRO → DDT, the classical 1961 cycle | slow, authentic (45-90m coach / 20m drive) |
| 2 | Cross-assemble on Linux, test on the PDP-1 — the practical fast path | fast (15-30m) |
| 3 | PDP-1 Lisp — bring up, REPL, load/save, a demo program | medium (30-60m) |
| 4 | Games and demos — display hacks, Spacewar | light, fun (20-40m) |

Quick start: if the user only has 15 minutes, do Tour 2.

## Before any tour: prerequisites and machine vocabulary

Machine running; nobody else on it (`ps aux | grep '[p]dp1'`). Ports:
1040 debug, 1041 shared typewriter, 1042 tape reader, 1050 periph
mount, 3400 display (never raw — use pdp1_dpy). Details in
pdp1-plumbing — not repeated here.

Machine vocabulary (exact protocol semantics in pdp1-debugging):

| You say | On the PiDP-1 |
|---|---|
| mount tape X | human: `printf 'r %s\n' <path> \| ncat -w 1 localhost 1050` (periph GUI shows it); agent: `r tapes/<file>` + READ IN |
| READ IN / CONT / START / STOP | `key readin` / `key cont` / `key start` / `key stop` (or vpanel / front panel) |
| start at address N | `w pc N` + `go` (while halted) |
| quick core load | `l tapes/<file>.rim` — pure RIM only, no start (block tapes are misloaded) |
| set a switch | `panel on` + `sw <name> <val>`; names: `ta tw ss sstep sinst extend power` |
| sense switch N | bit `040 >> (N-1)`: SS2\|SS6 = 021, SS3 = 010, SS5 = 004 |
| type into a machine program | shared typewriter, port 1041 |
| watch the display | periph GUI or pdp1_dpy (pdp1-type30-vision) |
| verify a load | `pdp1dbg.py --lst <file>.lst 'check'` → "0 of N words differ" |

`sw` requires the switch override (`panel on`). Keep it armed while a
running program depends on the values — Extend during Lisp bring-up,
TW before start — and `panel off` when done: disarming hands the panel
back to its physical state, which then rules.

Tape paths are relative to the emulator's cwd: `tapes/<name>.rim`.
A failed mount leaves the reader unmounted — it is closed before the
path is checked; after a `?file`, re-mount before READ IN. [src, via
pdp1-plumbing]

Bounded runs only. 0 is not HLT (760400 is).

## Tour 1 — Assembly on the PDP-1: ET, MACRO, DDT

Goal: the full 1959 development cycle on the machine itself — write a
program in the ET editor, assemble it with MACRO, run the binary, then
load it under DDT and debug it. Ends with a saved, self-loading program
tape.

Tapes needed: `et.rim`, `macro.rim`, `ddt.rim` (all in
`/opt/pidp1/tapes`). Full listings and keystroke details:
`references/programming-introduction.md`.

On a real PDP-1 every one of these actions is a physical switch — that
is the point of this tour. (Vocabulary: "Before any tour".)

### Part A — edit with ET

DO: mount `et.rim`, set sense switches 2 and 6 (line numbers on; parity
errors suppressed), READ IN.
SEE: ET loads; typing `w` prints one empty line — its text buffer.
IF NOT: `?file` means the tape path is wrong (`tapes/...` relative to
the emulator cwd); READ IN doing nothing means the periph stream (1042)
is not connected — see pdp1-plumbing.

DO: type `a` to enter text mode, then type the CIRCLE program below.
TAB puts the instruction in column 2. ET is modal like VIM; backspace
deletes the last character and overtypes it.
SEE: each line prints as you type it.
IF NOT: nothing echoes — ET talks to the typewriter; check the periph
typewriter connection.

    CIRCLE
    100/
    go, lac x
    lup, cma
     sar 4s
     add y
     dac y
     lio y
     sar 4s
     add x
     dac x
     dpy
     jmp lup

    x, 200000
    y, 0
    start go

DO: backspace at the start of a new line to leave text mode. `w` prints
the buffer for review; `nc` replaces line n, `nd` deletes it, `ni`
inserts before line i, `a` resumes appending.
SEE: the review print shows the corrected text.

DO: with sense switch 6 set, punch the source: `p`, then `s` (appends
the STOP code — MACRO will not read a source tape without it).
SEE: the punch runs; on the PiDP-1 the tape image file appears in the
periph's output directory — note its name.
IF NOT: no STOP punched → MACRO won't know when the source ends.
Re-punch ending with `s`.

DO: test the tape: `k` (kill the buffer), mount the punched tape,
`r` (read it), `w` (print it).
SEE: the full source prints out.
IF NOT: garbled or empty — the tape is damaged or missing the STOP
block; re-punch from the buffer.

### Part B — assemble with MACRO

DO: all switches off — 18 Test Word, 17 Address, 6 Sense; they are
input to MACRO (`sw tw 0`, `sw ss 0`; address row on the panel). Mount
`macro.rim`, READ IN.
DO: mount the source tape, CONT.
SEE: `Pass 1` on the typewriter.
DO: mount the source tape again, CONT.
SEE: `Pass 2`, then the punch outputs the binary tape.
DO: CONT once more — punches the start block. Save the binary tape
image.
SEE: punch output ends; you hold a self-loading `.rim` tape.

### Part C — run it

DO: mount the binary tape, READ IN.
SEE: the Type 30 draws a circle. It is an endless loop — the machine
will not come back by itself.
IF NOT: no display → pdp1-type30-vision; or the tape is bad → re-check
Part B.
DO: stop it with the front panel STOP.

### Part D — debug under DDT

DO: mount `ddt.rim`, READ IN.
DO: mount the MACRO binary tape. Type `Z` (clear memory), then `Y`
(read the binary tape).
SEE: DDT loads the program.
DO: `100/` to inspect.
SEE: DDT prints `lac 113` — the first instruction at 100. Backspace
reads on; at 112 you hit the `jmp` that loops back.
DO: `100G` to run. Stop with the front panel STOP. Set address 6000 on
the front panel and START — DDT lives at 6000, so this returns you to
it.
SEE: DDT responds again after the restart.

### Part E (stretch) — write a program inside DDT

The helloworld program, entered directly in DDT: `lac i 212` / `cli` /
`rcl 77` / `tyo` / `sza` / `jmp` / `idx` / `sas` / `hlt` at addresses
200-211, the `"` three-character trick for the string, fiodec `640000`
for the final `d`, `~` to view a string, `200G` to run, saving with
`L hello` / `200<216D` / `200J`. Full keystroke walk-through:
`references/programming-introduction.md`. Excellent coach-mode material.

### Tour 1 verification

- Circle draws on the Type 30, machine stopped by the panel.
- helloworld prints and halts; DDT restarts from 6000.
- A self-loading tape was saved that READ-INs on its own.

## Tour 2 — Cross-assemble on Linux, test on the PDP-1

Goal: skip ET and MACRO on the machine entirely — edit on Linux,
cross-assemble with `macro1_1` into a self-loading `.rim`, load and run
on the PDP-1; move text both ways with `encode_fiodec`/`decode_fiodec`;
inspect tapes with `tape_visualizer`; disassemble with
`disassemble_tape`.

Tools (all on PATH in /usr/local/bin): `macro1_1`, `encode_fiodec`,
`decode_fiodec`, `disassemble_tape`, `tape_visualizer`. Source
directory: `/opt/pidp1/tapes/sources/` (circle.mac already there).

### Part A — assemble on Linux

DO: in /opt/pidp1/tapes/sources (or a scratch dir), write circle.mac —
the CIRCLE source is in `references/programming-introduction.md`; a
working copy already exists there.
DO: `macro1_1 -r circle.mac`
SEE: `circle.rim` and `circle.lst` appear **next to the source**, not
in the cwd — macro1_1 derives output names from the input path.
IF NOT: "illegal character at column N" → macro1_1 is strict about
fields: `INSTRUCTION<TAB>OPERAND<TAB><TAB>/<SPACE>COMMENT`, and labels
are truncated to 6 characters (`references/learnings.md`, agent-side).
Note: `-r` is REQUIRED — the default output is a block tape that `l`
misloads (it loads the RIM bootstrap as data and reports success with
the program absent).

### Part B — load and run

DO: `cp circle.rim /opt/pidp1/tapes/`
DO (agent, drive mode): stop the machine first, then
`pdp1dbg.py 'l tapes/circle.rim'`; verify with
`pdp1dbg.py --lst circle.lst 'check'` — "0 of N words differ" means it
landed; entry from the listing: `grep 'go,' circle.lst` (100 for the
stock circle); `pdp1dbg.py 'w pc 100' 'go'`.
SEE: the Type 30 draws the circle — the same program as Tour 1, with
zero machine-side editing.
IF NOT: `check` reports differences → reload; nothing on the display →
pdp1-type30-vision.
DO (user, assist mode): `printf 'r %s\n' tapes/circle.rim | ncat -w 1
localhost 1050`, then READ IN — the periph GUI shows the mount and the
human presses READ IN themselves.
SEE: the reader runs the tape; the circle displays.

### Part C — iterate

DO: change something in circle.mac on Linux (a different constant, a
faster rotation), re-run `macro1_1 -r`, reload, run.
SEE: the change appears on the display.
IF NOT: no change → the old program is still running; stop it first
(`key stop`), then reload — `l` loads core only and does not stop the
machine.

### Part D — text both ways

DO: `encode_fiodec circle.mac circle.pt` — answer **y** to the STOP
trailer question (MACRO will not know when to stop reading without
it).
SEE: `circle.pt`, an alphanumeric tape image.
DO: `tape_visualizer circle.pt` — decodes it back to readable text.
DO: with MACRO loaded (Tour 1 Part B), mount `circle.pt` (1050) and
press CONT as in Tour 1 — machine-side MACRO assembles a PC-edited
source: "skip ET", edit on PC, punch on the PDP-1.
DO: `decode_fiodec circle.pt back.txt` — pull a machine-punched tape's
text onto Linux.
IF NOT: garbage characters → FIODEC is 6-bit, not ASCII; a parity
problem on the punching side.

### Part E — inspect binaries

DO: `disassemble_tape circle.rim` (run bare to see its options).
SEE: the assembled instructions come back.
DO: `tape_visualizer circle.rim` — RIM blocks in blue, BIN in red; `R`
marks the `dio` + load address, the three tape lines per word visible.
(`tape_visualizer` needs a graphical display — run it on the desktop,
not through the agent.)

### Tour 2 verification

- circle assembled on Linux runs on the PDP-1, `check` reports 0 words
  differing.
- A source tape (`circle.pt`) feeds machine-side MACRO.
- A machine tape decodes back to text on Linux.

## Tour 3 — PDP-1 Lisp basics + demo

Goal: bring up PDP-1 Lisp — the first REPL, Peter Deutsch, 1960 —
drive it, load functions from tape, save a function with `pdef`, run a
small demo. Octal arithmetic throughout: 4+4=10.

Tapes: `lisp.rim`, `lisp-defs.pt` (in /opt/pidp1/tapes). Background:
`references/lisp-introduction.md`. Agent-side expertise:
`references/lisp.md` (PDP-1 Lisp from the DECUS document),
`references/lisp1_5.md` (Lisp 1.5).

### Part A — bring up Lisp

DO: set the Extend switch (`panel on`, `sw extend 1`) — Lisp needs
the extended instruction set. Keep the override armed through
bring-up; `panel off` only when the physical panel already has Extend
up.
DO: mount `lisp.rim`, READ IN.
DO: `sw tw 7750` (upper memory address for Lisp storage), CONT.
DO: `sw tw 400` (length of the push-down list), CONT.
DO: `sw ss 004` (sense switch 5 — typewriter input), CONT.
SEE: Lisp is up; the typewriter is live.
IF NOT: READ IN did nothing → the periph stream (1042) isn't
connected; Lisp halts immediately → the TW/SS sequence didn't match,
redo from the top. **After bring-up: `sw extend 0` — READ IN fails
for every normal program while Extend is set.**

### Part B — REPL basics

DO: `w pc 4` — always, before and after running things; START/CONT
then returns to Lisp.
DO: type `nil` followed by a **space**.
SEE: Lisp echoes `nil` on a new line — it is alive. Make it a habit
before anything else; it is also the best way to start a new line.
IF NOT: no echo → Lisp halted; `w pc 4`, `go`, try again.
DO: `oblist` + space.
SEE: the defined atomic symbols.
DO: `(plus 1 2)` + space.
SEE: `3` — note 'plus', not '+'.
DO: `(times 4 4)` + space.
SEE: `20` — octal: 20 octal is 16 decimal.
DO: enter the demo program (Return and TAB as shown), closed with a
space:

    (prog (a b)
     (setq a 4)
     (setq b 4)
     (plus a b)
     (return (plus a b)))

SEE: `10` — 4+4 in octal.
IF NOT: gibberish or a halt → a line was not closed with a space;
errors halt Lisp, that is normal: `w pc 4`, `go`, re-enter the line.

### Part C — load functions from tape

DO: mount `lisp-defs.pt` (an alphanumeric tape), set SS5 down
(`sw ss 0`) — straight away the tape reads in.
SEE: the typewriter lists the loaded functions: `zerop`, `pdef`,
`count`.
DO: SS5 up again (`sw ss 004`), `w pc 4`, `go`.
DO: make your own test tape: write test.lisp on Linux (the
rplacd/quote/tt example in `references/lisp-introduction.md` — last
line must end with a space), `encode_fiodec test.lisp test.pt`, mount
it, SS5 down, read in, SS5 up, `w pc 4`, `go`.
SEE: `tt`, `hello`, `5` printed. Inspect: `(print (cdr (quote tt)))`.
IF NOT: nothing reads in → the tape is missing the trailing space or
the STOP trailer; re-encode.

### Part D — save a function

DO: SS3 up (`sw ss 010` — output goes to the punch), type `(pdef tt)`
+ space.
SEE: your function punches out to tape.
DO: SS3 down (`sw ss 0`), save the punched tape.
IF NOT: no punch output → SS3 was down; `pdef` not defined → reload
lisp-defs.pt (Part C).

### Tour 3 verification

- Lisp answers `(plus 1 2)` → 3 and the prog demo → 10.
- lisp-defs.pt loads (zerop, pdef, count).
- A function is saved with `pdef` and read back from tape.
- Extend is off again and a normal program still READ-INs (e.g.
  circle).

Note: core memory is non-volatile — after a power cycle everything is
still in memory; just `w pc 4` + START/CONT, no need to re-bring-up
Lisp from tape.

## Tour 4 — Games and demos

Goal: the display hacks and Spacewar — the birth of democoding and
videogames — with the TW switches as the interactive control. Light,
visual, history-rich.

Tapes: `dpys5-demo.rim` (Snowflake, Munching Squares, Minskytron),
`spacewar48.rim`, `pong.rim`, `lunar_lander.rim`, `mapes.rim`,
`minskytron.rim`, `minskytron_ii.rim`, `munch.rim` (all in
/opt/pidp1/tapes). Background: `references/democoding-and-gaming.md`;
the definitive writing is on masswerk.at (Minskytron, Snowflake
archaeology, Mapes, spacewar history, Inside spacewar, ICSS) and
Levy's *Hackers*.

### Part A — the display hacks (dpys5-demo.rim)

DO: mount `dpys5-demo.rim`, READ IN — it is self-loading; its start
block launches one program.
DO: stop it (`key stop`), `w pc 0` + go — **Snowflake**.
SEE: crystalline figures building on the slow-phosphor Type 30.
DO: stop, set TW switches (`panel on`, `sw tw <bits>` — keep armed),
`w pc 500` + go — **Minskytron**. It reads the TW switches at start;
their values shape the feedback pattern.
SEE: Minsky's feedback-loop geometry.
DO: stop, `w pc 0` + go — **Munching Squares**; flip TW switches
WHILE it runs (`sw tw <bits>`) and watch the pattern change live.
SEE: the bitwise squares morph as the TW switches change.
IF NOT: nothing on the display → mount/readin path (pdp1-plumbing) or
the display read (pdp1-type30-vision); wrong pattern → TW timing:
before start for Minskytron, during the run for Munching Squares.

### Part B — Spacewar

DO: mount `spacewar48.rim`, READ IN.
SEE: the game is up on the display; the PiDP-1 game controllers drive
the ships (if wired up — otherwise this is a watching tour).
DO: play a round and tell the story — the first videogame, the Hacker
ethic, the slow-phosphor aesthetic
(`references/democoding-and-gaming.md`).
IF NOT: no response from the controllers → they may not be connected
to this emulator session; say so and fall back to watching.

### Part C — the rest (optional)

DO: `pong.rim`, `lunar_lander.rim`, `mapes.rim`, `minskytron.rim`,
`munch.rim` — each is self-loading: READ IN and go.
SEE: each runs; most respond to the TW switches.

### Tour 4 verification

- Snowflake, Minskytron and Munching Squares all run from
  dpys5-demo.rim, with TW control.
- Spacewar runs; controllers work or are explicitly out of scope for
  the session.
- The user can name the three display hacks and their start addresses
  (0 / 500 / 0).

## Cross-tour pitfalls

- Octal everywhere: 4+4=10. Lisp answers are octal; MACRO addresses
  are octal.
- One machine, global state: check `ps aux | grep '[p]dp1'` before
  starting; bounded runs; 0 is not HLT.
- The Extend switch (Tour 3) left on breaks READ IN for every other
  program.
- `macro1_1` without `-r` emits a block tape that `l` misloads — pure
  RIM only (Tour 2).
- DDT lives at 6000: front-panel restart from 6000 returns to DDT.
- Lisp input lines end with a space, not Return (Tour 3).
- MACRO demands the STOP block at the end of the source tape (punch
  `s` in ET).
- Tape paths are relative to the emulator's cwd: `tapes/<name>.rim`.

## References

| File | Covers |
|---|---|
| `references/programming-introduction.md` | obso-site programming-introduction page, converted: the classical cycle, ET, MACRO, DDT, cross-compiling, tape tools, paper-tape formats |
| `references/paper-tape.md` | obso-site paper-tape page, converted: alphanumeric vs binary tapes, RIM vs BIN blocks, STOP blocks |
| `references/lisp-introduction.md` | obso-site lisp-introduction page, converted: bring-up, REPL, load/save, `pdef`, DDT mixing |
| `references/democoding-and-gaming.md` | obso-site democoding page, converted: display hacks, Spacewar, masswerk pointers, dpys5 tape |

Agent-side expertise (copied from the read-only pidp1-sw dir — **not
user-facing tour material**, agent reference only):

| File | Covers |
|---|---|
| `references/PDP1.md` | Assembly programming assistant: architecture, complete instruction reference, patterns, AI rules |
| `references/lisp.md` | PDP-1 Lisp (from the 1964 DECUS document by Deutsch & Berkeley) |
| `references/lisp1_5.md` | Lisp 1.5 (IBM 7090) programming guide |
| `references/learnings.md` | macro1_1 assembly learnings: TAB comment rules, 6-char labels, FIODEC I/O |

Canonical sources: `/home/x/Documents/obso-site/*.html` (the
obsolescence.dev site pages) and the `.md` files in
`/home/x/Documents/obso-site/pidp1-sw/` (**read-only — never edit
there**). The references are working copies; regenerate them if a
source changes.

## Verification status

- Tour 1's keystroke-level ET/MACRO/DDT steps come from the obso-site
  page (the author's hands-on experience) and are not yet exercised
  live on this emulator. The machine mapping they sit on (1050 mount,
  `key readin`, panel control) is [live] via pdp1-learnings.
- Tours 2-4 are written from the converted references plus the
  pdp1-plumbing / debug-protocol machine mapping. **No tour has yet
  been run end to end on this emulator**; the ET/MACRO/DDT keystroke
  details (Tour 1) and the Lisp bring-up sequence (Tour 3) in
  particular remain unverified live. The switch verbs (`sw extend`,
  `sw tw`, `sw ss`) are from the debug-protocol reference [src]; the
  sense-switch bit math is [live].
- When a tour is first run, verify each step on the live machine and
  file corrections in pdp1-learnings (LOCAL or PUBLISHABLE per the
  filing rules).
