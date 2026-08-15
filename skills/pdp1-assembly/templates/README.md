# Templates

Working PDP-1 programs, inherited from the PiDP-1 sessions and audited against
the references in this skill. Read the caveats before copying a pattern.

| File | Demonstrates | Status |
|---|---|---|
| `tic-2.mac` | Complete tic-tac-toe: grid drawing, board rendering, subroutine linkage, counted line loops | **Best starting point.** Structurally sound |
| `tic-1.mac` | Earlier step — draws the empty 3×3 field only | Sound; good minimal display program |
| `siggy-square.mac` | Counted loops for line drawing, four edges from one body | Sound (see fix below) |
| `siggy-circle.mac` | Smallest useful `dpy` program | Sound (see fix below) |
| `siggy-animate.mac` | Frame loop with moving geometry | Sound (see fix below) |
| `siggy-rotate.mac` | Rotation applied to a point set | Sound (see fix below) |
| `siggy-type.mac` | Typewriter I/O — `cks` polling, FIO codes, string output, buffered input | Sound (see fix below) |
| `lander.mac` | Perspective projection with hardware `mul`/`div`, scale table, interactive controls | **Read the caveats** |

## Fix applied to the `siggy-*.mac` files

All five arrived with `start go` as the **first line** of the source. Under
`macro1_1` the first line is consumed as the tape title and never assembled
(`macro1_1.c` `processLine`, see `references/macro1-assembler.md`), so the
`start` directive silently vanished and the tapes carried no transfer word —
they could not auto-start on READ-IN.

Each now opens with a `/` comment and carries `start go` as its last line. No
other change was made; the program bodies are untouched.

They are exercises written by Siggy, Oscar's Hermes agent, during the PiDP-1
sessions.

## Caveats on `lander.mac`

The program works, but it encodes two beliefs the references now contradict.
Left in place rather than edited blind, because verifying a change needs the
program run on real hardware.

**1. `jmp .+1` after `div` (lines 92, 97).** `div` skips the following
instruction on *success*, so that slot is the overflow handler. `jmp .+1` jumps
to the next instruction — which is where the skip lands anyway — so it is a
no-op that discards the overflow signal. The perspective divide is exactly the
place where overflow is plausible: it occurs when `(dividend >> 17) >= divisor`,
and the divisor here is the distance to the runway, which gets small on
approach. Consider:

```asm
        div dz
        jmp ovflow              / only reached on overflow
        dac result
```

See `references/arithmetic.md`.

**2. The `cma` negations of the Y offset (lines 100, 103, 109).** These follow
from the inherited claim that positive raw Y appears *below* screen centre. That
claim came from reading SVG display captures, whose Y axis points down — the
capture is mirrored relative to the real CRT. On the physical display, larger Y
is higher. If the runway renders upside down, this is the first place to look.
See `references/type30-display.md` and item 9 of `references/errata.md`.

**3. `mul=mus` / `div=dis` (lines 12-13).** Harmless. Both mnemonics are already
in the assembler's permanent symbol table, so these equates are no-ops. Left
alone since removing them changes nothing.

## Conventions worth copying

`tic-2.mac` uses the `dac ret` / `jmp i ret` return convention throughout:

```asm
grid4,  dac gr4ret
        ...
        jmp i gr4ret
```

This is correct. The `dap ret` / `ret, jmp .` form documented in
`references/subroutines-and-dispatch.md` is equivalent, marginally faster on
return, and is what ICSS and Spacewar! use — but there is no reason to convert
working code. What matters is not mixing the halves of the two conventions.
