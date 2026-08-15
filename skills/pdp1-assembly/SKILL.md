---
name: pdp1-assembly
description: Writing and assembling PDP-1 assembly language — instruction set, MACRO-1/monas assembler syntax, subroutine linkage, Type 30 display programming, typewriter and paper-tape I/O, EAE multiply/divide. Use for any PDP-1 coding or assembly task. For debugging the running machine see pdp1-debugging.
---

# PDP-1 Assembly Programming

The PDP-1 is an 18-bit, ones'-complement machine with 4096 words of directly
addressable core (up to 65536 with the memory extension), one accumulator (AC),
one I/O register (IO), and no index registers or stack. Self-modifying code is
not a hack here — it is the intended mechanism for indexing, dispatch and
subroutine return.

## Read this first: the five things that actually bite

1. **The PDP-1 is not a PDP-8.** 
   PDP-8 facts leak into PDP-1 material sometimes. The PDP-1 has **no link
   bit, no page-zero/current-page addressing, no `tad`, no `isz`, no `jms`**.
   Its address field is a full 12 bits — every location is directly reachable.
   If a claim mentions pages, the link, or `jms`, it is PDP-8 contamination.
   See `references/errata.md`.

2. **`jsp` puts the return address in AC. It does not write to memory.** The
   subroutine's first instruction executes normally and must save AC itself:

   ```asm
           jsp sub
   sub,    dap ret         / AC holds return address; splice it into ret
           ...
   ret,    jmp .           / dap rewrote this into jmp <caller>
   ```

   The PDP-8-style `sub, 0 / jmp i sub` does **not** work with `jsp`. On the
   PDP-1 the instruction that deposits into memory is `jda`.
   See `references/subroutines-and-dispatch.md`.

3. **`dpy` reads the top 10 bits of AC and IO**, not the low bits. `lac (100`
   puts 100 in the *low* bits and plots at the centre of the screen. Coordinates
   must be pre-shifted: `pixel_offset << 8`.
   See `references/type30-display.md`.

4. **Ones' complement has two zeros.** `+0` is `000000`, `-0` is `777777`.
   Arithmetic that lands on `-0` compares unequal to `+0` under `sza`, and plots
   one pixel away from `+0` on the display. `sub` producing "zero" may give
   either.

5. **Symbols truncate to 6 characters** (in `macro1_1`; `SYMLEN 7` = 6 chars plus
   NUL). `dwdiag1` and `dwdiag2` are the same symbol. This is the single most
   common cause of "impossible" assembler behaviour.

## Which assembler are you targeting?

Claims about syntax, mnemonics and output format are **assembler-specific**.
Establish which one is in play before trusting any of them.

| Assembler | Source | Character | Output |
|---|---|---|---|
| `macro1_1` | `pidp1/src/macro/macro1_1.c` | The common one. Lowercase mnemonics, 6-char symbols, first line eaten as tape banner | block tape by default, pure RIM with `-r` |
| `monas` | `pidp1/src/monas/monas.c` | Angelo's own, ~1k lines. Case-insensitive, no banner rule, macros via m4 | BIN with built-in RIM loader — load with `r` + READ-IN, not `l` |
| `am1` | `pidp1/Tools/AM1/` | C-preprocessor syntax: `#define`, `//` comments, `;` terminators | binary with loader; `-m` for macro1-compatible |
| `macro1_0`, `macro1old`, `macro1_1alt` | same dir | older/variant | assume nothing carries over |

Both `macro1_1` and `monas` define `mul`/`div` **and** `mus`/`dis` as mnemonics
for `0540000`/`0560000`. The `mul=mus` equate that older notes insist on is a
no-op — harmless, but not required, and not evidence of anything.

See `references/macro1-assembler.md`.

## Reference files

| File | Covers |
|---|---|
| `references/instruction-set.md` | Full opcode map, skip group, operate group, shift group, indirection — verified against the emulator's decoder |
| `references/macro1-assembler.md` | Syntax, pseudo-ops, literals, the banner line, what `start` really does, reading a `.lst` |
| `references/subroutines-and-dispatch.md` | `jsp`/`jda`/`cal` linkage, computed GOTO, `dap` self-modification, re-entrancy limits |
| `references/arithmetic.md` | Ones' complement, shifts vs rotates, EAE `mul`/`div`, product packing, overflow, fixed point |
| `references/type30-display.md` | Coordinate encoding, `dpy` variants and `ioh`, display idioms from Spacewar!/ICSS, the protocol on the wire |
| `references/io-and-fio.md` | FIO character codes, `cks` polling, `tyi`/`tyo`, paper tape reader/punch |
| `references/tape-formats.md` | RIM vs block format, `readrim`, READ-IN, what `-r` changes |
| `references/debug-protocol.md` | The port-1040 debug service: breakpoints, watchpoints, `trace`, the call ring, the panel override, and the semantics that bite |
| `references/debugging.md` | Sense-switch breakpoints, reading the panel after a halt, predict-and-compare, reloading after a crash |
| `references/errata.md` | Claims from earlier notes that are wrong, and why — read if you have inherited material |

`pdp1dbg.py` (in the pdp1-debugging skill) is a stdlib client for the debug service that also reads a
`macro1_1` listing, so you can say `b chkwin` instead of `b 1165` and get
`pc=000110(deci)` and annotated `trace` lines back. It adds two listing-only
commands: `where` (source around PC) and `check` (every word of core that
differs from the listing).

`templates/` holds working programs: `tic-1.mac`/`tic-2.mac` (tic-tac-toe on the
Type 30), `siggy-*.mac` (display and typewriter exercises), `lander.mac`
(perspective projection). Read `templates/README.md` first — it records what
each one demonstrates and which carry known-questionable idioms.

## Primary sources

Not duplicated here; consult them directly when a detail matters.

- **PDP-1 Handbook** — the authority on instruction semantics, timing and the
  peripherals. Worth reading in full on `jsp`/`jda`/`cal`, the skip and operate
  groups, extend mode, and the Type 30. Machine-converted copies carry OCR
  artifacts (`$\mu$sec` for µsec); the text is sound.
- **PDP-1D supplement** — the later variant's memory-reference and cycle
  descriptions.
- **ICSS** (Norbert Landsteiner, `masswerk.at/rc2016/10/`) — the best worked
  tutorial in existence for Type 30 programming. Episodes 2 (stars and frame
  sync), 3 (rotation, coordinate system) and 9 (compiled character outlines) are
  the ones cited throughout these references.
- **Spacewar! 4.8 source** and `masswerk.at/spacewar/inside/` — the canonical
  idiom set: frame budgeting, `dap` dispatch, the sine/cosine routine.
- **`blincolnlights/pdp1/DEBUG_PROTOCOL_SPEC.md`** — normative for the debug
  service, with `DEBUG_PROTOCOL.md` for rationale and `test/pdp1dbg_test.py` as
  the executable definition of conformance. The spec drifts behind `dbg.c`;
  `help` over the connection is generated from the code and is more current.

When source and note disagree, the source wins. When the handbook and a
well-tested emulator appear to disagree, re-read both before concluding
anything — see `references/errata.md`.

## Running and debugging

The emulator carries a debug service on **port 1040**. Before anything else:

```sh
ps aux | grep '[p]dp1'      # never start a second one; it will silently fail
```

The machine is global — one PDP-1, shared by every connection, run control
last-write-wins. If someone else is on it, your `run` will be cut short by
their `step`. For unattended work start your own with `./pdp1 -t`.

The whole loop, with labels from the listing (pdp1dbg.py lives in the
pdp1-debugging skill):

```sh
macro1_1 -r prog.mac
python3 /opt/agent-pdp1/skills/pdp1-debugging/scripts/pdp1dbg.py --lst prog.lst \
    'l prog.rim' 'w pc go' 'b chkwin' 'run 100000' 'where' 'back'
```

`w pc <addr>` while halted is all it takes to start somewhere. Breakpoints are
PC comparisons inside the emulator, so nothing is written into core and a
breakpoint on a `jsp` subroutine's first instruction is safe. Addresses and
words are octal; counts and timeouts are decimal.

Three things that will confuse you once each:

- **The instruction at PC executes before the debugger looks at anything**, so
  a breakpoint at the address you are continuing *from* does not fire there.
- **`ma` reads `000000` at every debugger stop** — MA is cleared at the end of
  each instruction. It is only meaningful on `stop=halt` and `stop=illegal`.
- **Sense switch N is bit `040>>(N-1)`**, so `sw ss 40` raises switch 1.

See `references/debug-protocol.md`. **The debugging skill (pdp1-debugging)
owns the protocol, the recipes and the helper client — load it for real
debugging work.** Source-level techniques that need no socket — chiefly
`szs`/`hlt` breakpoint channels — are in `references/debugging.md`; they
are still the right tool on real hardware and inside a display frame.

## Working method

**Suspect your own code first.** The assembler and the emulator are far better
tested than the program being written. Before concluding that a tool is broken,
check the `.lst` listing, trace the path with real addresses, and reload the tape
(a crash that ran through address 0 will have corrupted core, and the corruption
outlives the crash — `pdp1dbg.py --lst prog.lst check` will tell you whether it
did).

**Predict, then execute, then compare.** Reading registers without an expectation
is looking, not debugging. State what AC/PC/memory *should* be after the next
instruction, step, and compare. A mismatch is the bug; a match means the mental
model is good for one more instruction.

**Plant breakpoints in the source, not in core.** A `szs 10 / hlt` pair costs two
words, is armed and disarmed by flipping a sense switch on the front panel, and
survives reassembly and reloading. Six sense switches give six independently
toggleable breakpoint channels. See `references/debugging.md` — including why
`szs 1` does not mean sense switch 1.

**Read the listing, not the source, for addresses.** The `.lst` gives the
assembled word and the address for every line. Nearly every "the assembler
resolved my label wrong" report dissolves once the listing's columns are read in
the right order: `line-number  address  assembled-word  source-text`. The address
column is *not* the operand.

**Do not cycle through syntax variants.** If a construct does not assemble,
find out what it means — check this skill, check the listing, grep a known-good
source (ICSS, Spacewar!) for the same construct. Trying three spellings in the
hope that one sticks wastes the session and teaches nothing.

## Verification status

Statements in these references are marked where they were checked:

- **[src]** — read out of the emulator or assembler source on this machine.
  Paths are given inline. Note that source layout varies between machines; a
  missing path does not mean the claim is stale.
- **[handbook]** — from the PDP-1 Handbook or the PDP-1D supplement.
- **[live]** — exercised against a running emulator over the debug service, not
  merely read. The strongest mark here; where it contradicts a spec document,
  believe it.
- **[observed]** — seen in practice but with no mechanism established. Treat as a
  lead, not a law.

Unmarked statements are ordinary PDP-1 background. If something matters to a
decision, verify it and mark it.
