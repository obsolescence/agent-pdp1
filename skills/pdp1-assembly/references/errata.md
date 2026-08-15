# Errata

Claims that appeared in earlier PDP-1 notes and are wrong. Recorded because the
old material may still be in circulation, and because several of these are
*plausible* — they will be rediscovered otherwise.

There is a pattern worth naming up front: **most of these blame the emulator or
the assembler for a misunderstanding.** When a tool as well-exercised as
blincolnlights or `macro1_1` appears to deviate from documented behaviour, the
prior should be strongly against the tool. Every case below resolved the other
way.

The second pattern: **PDP-8 knowledge leaking into PDP-1 work.** The machines
are adjacent in DEC's history, the assemblers share ancestry, and a model
trained on both will interpolate. Any claim involving pages, the link bit,
`jms`, `isz` or `tad` is PDP-8.

The third, visible only once the debugging notes are read next to the
programming notes: **the same body of notes contradicted itself across files.**
`lat` is described correctly in one and backwards in another (item 17); the
port number in one contradicts the spec it cites (item 18). Notes accumulated
per-session drift apart, and nothing reconciles them. That is the single
strongest argument for keeping a distilled reference like this one and deleting
the session notes rather than adding to them.

---

## 1. "JSP writes the return address into the subroutine entry word"

**Claimed:** the DEC hardware manual says `jsp Y` deposits PC in the address
field of Y, so `sub, 0 / jmp i sub` is the textbook pattern; blincolnlights
"differs from the manual" by putting PC in AC instead, so the ICSS `dap` pattern
is an emulator-specific workaround.

**Actually:** `jsp` puts PC in AC on the real PDP-1 too. The handbook shipped
alongside those very notes says so:

> The contents of the Program Counter are transferred to bits 6 through 17 of
> the AC. […] The Program Counter is then reset to Address Y.

The emulator matches this exactly. The `sub, 0 / jmp i sub` pattern is the
**PDP-8 `jms` convention**. The PDP-1 instruction that deposits into memory is
`jda Y` — equivalent to `dac Y` followed by `jsp Y+1`.

So the `dap ret` / `ret, jmp .` convention is not a workaround; it is the
standard PDP-1 calling convention, which is why ICSS and Spacewar! both use it.

This error propagated into three separate reference files and a "corrected
understanding" document, each reinforcing the others.

---

## 2. The `macro1_1` manual page is half PDP-8

`MACRO1_PROGRAMMING_GUIDE.md` descends from MACRO8 and was never fully
rewritten. Wrong in it:

- **"Current page addressing — addresses 0-177 on the current page […] Page 0 is
  always accessible"** and **"PDP-1 uses 4096-word pages; keep data and
  subroutines on the same page"**. The PDP-1 has a full 12-bit address field.
  There is no page-zero addressing.
- The worked error example is `TAD I DUMMY`. `tad` is a PDP-8 instruction.
- Error code **"IR — address not on current page or page zero"**: same
  inheritance.
- **`clc` = "clear link"**. The PDP-1 has no link register. `clc` (`761200`) is
  `cla` plus `cma` — clear AC then complement it, giving all ones.
- **`idx` = "add one to memory, skip if zero"**. That is the PDP-8's `isz`.
  `idx` does not skip at all; `isp` is the one that skips, and it skips on
  *positive*.
- **`rpa`/`rpb` = "read printer A/B"**. They are the paper tape reader
  (alphanumeric / binary). `ppa`/`ppb` are the punch.
- **`lem`/`eem` = "load/enter end mode"**. They are Leave and Enter **Extend**
  Mode — 16-bit addressing. The handbook is explicit.
- **`lsm` = "load sequence mode"**. Leave Sequence Mode.
- **`cks` = "checksum"**. Check Status.

The opcode *numbers* in that guide are mostly right; the prose describing them
frequently is not.

---

## 3. "The assembler doesn't know `spa` — use `760200`"

**Actually:** `spa` is in both permanent symbol tables as `0640200`. **[src]**

```c
{ DEFFIX, "spa", 0640200 },
```

`760200` is `cla`. Substituting it does not skip — it silently clears the
accumulator, which is about the most destructive possible way to be wrong. The
same notes list `SPA 640200` correctly in their own opcode table two files away.

---

## 4. "A label resolves differently depending on how many times it was forward-referenced"

**Claimed:** the same label assembled to its correct address on the 1st, 3rd and
4th reference but to the current location counter on the 2nd; and elsewhere a
subroutine label resolved four words past its entry. The suggested workaround was
to call `label+1` to skip the "broken" first instruction.

**Actually:** a two-pass assembler resolves a symbol to one value. What was
almost certainly happening is a misread listing. The columns are:

```
  83 00114 700015      go,     law pstr
   |    |      |
   |    |      +-- assembled word
   |    +--------- address of this word
   +-------------- source line number
```

The reported evidence — "`dwvline, dac dwlret` at 1053 assembled as `DAC 1053`" —
is exactly what reading the *address* column as the operand produces.

This one is worth flagging loudly because the recommended workaround would
corrupt working code: calling `label+1` skips the subroutine's `dap ret`, so it
never saves its return address.

If a label genuinely appears to resolve wrongly, the real candidates are
six-character truncation (see below) and a symbol undefined for an unrelated
reason. Check the symbol table at the end of the listing — undefined symbols are
prefixed `?`, redefined ones `#`.

---

## 5. "`sar` is really a rotate, not an arithmetic shift"

**Actually** the decoder is unambiguous: **[src]**

```c
case 015:  // SAR
        ac = (AC&B0) | AC>>1;           /* sign preserved */
case 011:  // RAR
        ac = (AC&B17)<<17 | AC>>1;      /* LSB wraps to MSB */
```

`sar` is arithmetic. `rar` rotates. The masking dance the notes prescribe after
every `sar` is unnecessary; it is needed after `rar` when a logical shift was
intended.

Related in the same document: "IO state corruption in `rcl`/`rcr`". Those
instructions rotate the combined 36-bit AC:IO pair. Changing IO is their purpose.

---

## 6. Instructions claimed to be missing or unreliable

All of these are present in the emulator's decoder and in both assemblers'
symbol tables. **[src]**

| Claim | Reality |
|---|---|
| "`sas` may not be available; some emulators don't implement it" | `sas` = `520000`, IR 025, implemented |
| "`law` may not execute reliably; if the program halts at a `law`, switch to a data word" | `law` = `700000`, IR 034, implemented. `law i N` gives −N |
| "`dzm i` is not supported and causes IR_INCORR" | `dzm` = `340000`, IR 016; the deferral test applies to it like any memory-reference instruction. `IR_INCORR` covers IR 0, 5, 6, 017 and 036 — not 016 |

A program halting at one of these instructions is a program bug, not a missing
instruction.

---

## 7. "`mul=mus` and `div=dis` must be defined at the top of every source"

**Actually** both assemblers define all four mnemonics. **[src]**

```c
{ DEFFIX, "mul", 0540000 },
{ DEFFIX, "mus", 0540000 },      /* for spacewar */
```

The equate is a harmless no-op. `mus`/`dis` are the aliases, kept for Spacewar!
sources — not the other way round.

Whether `540000` *behaves* as a full multiply or a multiply step is a property
of the machine's EAE configuration at run time, not of the assembler. The
accompanying explanation — "MACRO-1's internal opcode for `mus` is 0o54, which
the emulator extracts as 0o26" — describes the ordinary opcode field (bits 0-4,
`MB>>13`) as though it were a special case.

---

## 8. `div` and `jmp .+1`

**Claimed:** `div` skips the next instruction on success, so absorb the skip with
`jmp .+1`.

**Actually** `jmp .+1` jumps to the next instruction, which is where the skip
lands anyway. It is a no-op that silently discards the overflow case — the one
thing the skip exists to signal.

```asm
        div divisor
        jmp ovflow              / executed ONLY on overflow
        dac quotient
```

The notes do show this form once, then recommend `jmp .+1` everywhere else.

---

## 9. Display Y direction

The inherited notes contradict themselves inside a single file: "adding a
positive value to Y moves the beam UP" against "positive raw Y → pixel > 512 →
lower on screen", about forty lines apart.

**Larger Y is higher on the physical screen.** The "lower on screen" reading is
an artifact of the SVG capture tool, which writes the protocol's Y straight into
an SVG `cy` attribute — and SVG's Y axis points **down**. Captured images are
vertically mirrored relative to the real display.

Corroboration: the display client sends light-pen coordinates back as
`cmd |= 1023-peny`, an explicit flip. **[src]** `p7sim/main.c`

Consequences recorded downstream — "for a landing simulator use positive raw Y
so the runway appears below the horizon", and a warning against negating the Y
offset — are inverted along with it.

---

## 10. "The handbook says `dpy` reads AC bits 8-17, but the emulator uses the full 18-bit value"

**Actually** the emulator takes the top ten bits: **[src]**

```c
pdp->dbx |= AC>>8;
pdp->dby |= IO>>8;
```

which in DEC's MSB-first numbering is bits 0-9 — what the handbook says. The
notes' own formula, `((signed_18bit >> 8) + 512) & 1023`, is arithmetically the
same thing, so the *results* were right and only the explanation was wrong. But
"the emulator disagrees with the handbook" is what gets remembered.

The reproduction of `mapcoord` in those notes is genuinely incomplete:

```c
int mapcoord(int x) {
        if(x & 01000) x++;      /* omitted in the notes */
        return (x+01000)&01777;
}
```

The dropped line is the ones'-complement sign correction — the negative-zero
handling. Without it the mapping is off by one across the whole negative half.

---

## 11. Address field described as "bits 12-17"

Appears throughout the `dap` material, sometimes alongside "the low 12 bits" in
the same paragraph. Bits 12-17 is six bits. The address field is **bits 6-17**,
twelve bits, in DEC's MSB-first numbering — which *is* the low twelve bits, so
the second half of each sentence is right and the first half is wrong.

Worth fixing rather than shrugging at, because `dip` deposits bits 0-5 and the
two are complementary.

---

## 12. `start` "is treated as end-of-file"

**Claimed:** assembly stops at `start`; data placed after it produces "undefined
symbol".

**Actually** `pseudo()` returns FALSE and the caller **discards the return
value** (`macro1_1.c:1310`). Assembly continues. What actually happens: **[src]**

- `start` punches the JMP transfer word *at that point on the tape*;
- it sets `list_title_set = FALSE`, so the **next line is eaten as a new tape
  title** (the mechanism for concatenating tapes in one file);
- subsequent lines assemble normally and are punched *after* the transfer word,
  where `readrim` never reaches them.

The practical advice ("put `start` last") is right. The mechanism matters
because it predicts the symptom: not an assembler error, but a program whose
trailing tables read as zero at run time — and exactly one vanished line
immediately after `start`.

---

## 13. Unresolved: `add (label` resolving to address 1

Recorded as an assembler quirk with a confident root cause ("how MACRO-1 resolves
label values in parenthesised expressions"). The mechanism was never established
and I could not reproduce it from the source.

It is left in `references/macro1-assembler.md` marked **[observed]**. The
workarounds (`law label`, or a data word plus plain `add`) are cheap and
correct, so nothing is lost by not knowing — but it should not be repeated as
established behaviour. Six-character truncation is the more likely explanation
and is worth ruling out first.

---

# Debugging: what the old stack got wrong

Items 14-19 come from the `pdp1-ai-debug` and `pdp1-debug-protocol` notes,
which described a shared-memory control channel that has since been replaced by
the debug service on port 1040. Most of this is not *wrong so much as
obsolete* — but two items were actively harmful at the time, and one is a plain
factual error that will still mislead.

## 14. "Set PC with HLT-at-entry, START, restore, EXAMINE"

The old recipe for starting a program at an address:

```
deposit 0o04 0        # HLT at entry
start 0o04            # RUN, hits HLT, halts at entry+1
deposit 0o04 700005   # restore the original instruction
examine 0o03          # EXAM at entry-1 -> PC = entry
```

**Four things wrong with it.** `w pc <addr>` does the whole job, and
additionally clears `cyc`/`df1`/`df2`/`bc`/`hsc` so the machine resumes at a
fetch boundary instead of into the middle of the instruction it was already
executing.

- Depositing `0` is not a HLT (item 16).
- The panel EXAMINE and DEPOSIT keys are **destructive**: `spec()`→`sc()`
  clears PC, IR, OV and the sequence-break state. The protocol's `e`/`d` touch
  `core[]` and nothing else.
- EXAMINE sets PC to the examined address **exactly** (SP1 `clr_pc`, SP2
  `PC |= ta`), not to address+1, so the "examine entry−1" step was wrong on
  this emulator anyway.
- It writes into core, so it fails on a subroutine entry (item 15).

## 15. Breakpoints by depositing `0` over an instruction

The most expensive mistake in the inherited material, because it *usually*
works and then destroys a specific case.

Depositing `0` on the **first instruction of a `jsp` subroutine** overwrites
the `dap ret` that saves the return address. AC is zeroed by the trap, the
`dap` never runs, the return cell keeps whatever it had — and the routine
returns to address 0, marches through the constant pool executing data, and
corrupts core on the way. In the session that produced these notes the RIM tape
had to be reloaded twice.

Breakpoints on port 1040 are **PC comparisons inside the emulator**. Nothing is
written into core, nothing needs restoring, and a breakpoint on a subroutine's
first instruction is safe. If you ever must deposit one by hand, place it
*after* the `dap ret`.

The `szs`/`hlt` source-level pair has the same property and is documented in
`references/debugging.md`.

## 16. "Deposit 0 to halt"

Opcode 0 is an **undefined instruction**, not a halt. Real `hlt` is `760400`.
`IR_INCORR` covers IR 0, 5, 6, 017 and 036. The machine does stop, but with an
inconsistent PC and a mid-cycle signature (`cyc=1`), and the debug service
names it `stop=illegal` rather than `stop=halt`. Told apart, these two say very
different things: one is your breakpoint, the other is a program that ran off
the end of itself.

## 17. "`lat` is an OR, not a load — clear AC first"

Recorded as `lat` = `762000` with `AC |= tw`.

**`lat` is `762200`** in both `macro1_1` and `monas` **[src]**, and its two
operate bits act in order: bit 10 clears AC, then bit 7 ORs in the test word.
Verified live: AC = `777777`, `lat` with `tw` = `123456`, AC = `123456`
exactly. **[live]**

The bare word `762000` *is* the OR half alone, and does accumulate — which is
what was actually being tested. The advice is right for `762000` and wrong for
`lat`, and since `lat` is what you write, the note as recorded would have you
emit a pointless `cla` forever.

Note that the *programming* notes had this right while the *debugging* notes
had it backwards. Neither knew about the other.

## 18. "Spec §4 mandates port 1044"

It did once; it does not now. The debug language is a superset of port 1040's,
so the two were merged and the port count went down instead of up:
`dbginit(pdp, 1040)` in `main.c:171`.

The general lesson is worth more than the fact: **the spec document and the
implementation drift**, in both directions. `DEBUG_PROTOCOL_SPEC.md` currently
lags `dbg.c` on the `e <addr>-<addr>` range form, on the program-flag warning
lamps, and on the tape reader key releasing the override. `help` over the
connection is generated from the code and is the more current of the two.

## 19. `ma=` in the spec's worked example

`DEBUG_PROTOCOL_SPEC.md` §9 shows `trace` lines carrying `ma=000015`. Against
the real emulator every one of them reads `ma=000000`, because `clr_ma()` runs
at the end of each instruction while the machine is running and the debugger
stops at instruction boundaries. **[live]**

The example was written against `test/pdp1dbg_mock.py`, which is an
instruction-level stand-in rather than a TP-level emulator. The spec says
plainly that where the two disagree the emulator wins — worth remembering,
because the mock is the more convenient thing to test against and its
divergences are invisible until they matter.

---

## What was right

Worth saying, since this list is one-sided. The inherited notes were correct and
useful on: Type 30 coordinate encoding and the pre-shifted constant technique;
the packed 9+9 star format; `dpy`/`dpy-i`/`dpy-4000` and `ioh`; the `isp` frame
budget and every-other-frame dimming; the 34-bit `mul` product packing; the
`div` overflow condition; counter-versus-`sad` loop termination; the `dap`
self-modification patterns and the cell-chaining control-flow trap; FIO codes
and the `021` = `/` or `?` shift hazard; the space-separated-values buffer trap;
`lat`'s clear-then-OR ordering; the RIM tape format; and the six-character
symbol limit.

That is a substantial body of correct, hard-won material. The corrections above
are worth making precisely because the rest is worth keeping.
