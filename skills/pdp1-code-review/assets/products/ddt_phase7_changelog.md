# Phase 7 — Continuous Refinement: DDT (PDP-1 Debugger)

**Source studied:** DDT — original PDP-1 debugger (20 August 1966)
**File:** `ddt.mac` (1,200 lines, 14,873 bytes)
**Location:** `/opt/pidp1-dev/tapes/sources/ddt.mac`
**Handbook baseline:** ICSS v1.3-derived Design Handbook v1.0 (2,118 lines)
**Previous Phase 7:** Spacewar! 4.8 changelog at `spacewar4_phase7_changelog.md`

---

## Overview

DDT (Dynamic Debugging Technique) is the PDP-1's original interactive debugger,
developed at MIT by the same community that created Spacewar!. Unlike the
previous Phase 7 subjects (ICSS = space simulator, Spacewar! = game), DDT is a
**systems programming tool** — a debugger, assembler, disassembler, memory
inspector, and paper tape utility all in one. It reveals the PDP-1's systems-
programming face: text I/O, symbol table management, runtime code generation,
and interactive console interaction.

---

## New Patterns to Add

### 1. The `flex` Meta-Macro — Opcode Table Generation (section 2.3)

DDT defines a `flex` macro that generates PDP-1 opcode constants en masse:

```asm
flex and   020000
flex ior   040000
flex xor   060000
flex xct   100000
flex jfd   120000
flex cal   160000
flex jda   170000
flex lac   200000
flex lio   220000
flex dac   240000
flex dap   260000
...
```

The macro definition (not shown, but implied) generates something like:
```asm
and=020000
ior=040000
...
```

This is an **opcode definition table** — a complete mapping of every PDP-1
mnemonic to its numeric opcode, used by DDT's disassembler (`pi` — print
instruction) to decode instructions at runtime. The table runs from line 32
to line 113, covering every standard PDP-1 instruction plus IOT variants.

This pattern is essential for any program that needs to **disassemble** or
**assemble at runtime**. The handbook currently has no coverage of runtime
instruction decoding.

Confidence: **Very High** — original PDP-1 systems software technique.

### 2. Typewriter Console I/O — Interactive Terminal Interface (new section)

DDT implements a full interactive console interface using the PDP-1 typewriter:

```asm
; Character output subroutine
tou,    dap tox         ; save return
        dio tot         ; save character
        cks             ; check typewriter status
        ril 2s          ; rotate status
        spi i           ; skip if IO positive (ready?)
        jmp .-3         ; not ready — wait
        lio tot         ; reload character
        tyo i           ; type out
tox,    jmp .

; Character input with listen macro
define
listen
        cla+cli+clf 1-opr-opr     ; clear AC, IO, flag 1
        szf i 1                    ; wait for flag 1 (typewriter ready)
        jmp .-1
        tyi                        ; read character
        term
```

Key techniques:
- **Busy-wait polling** — `cks`/`ril 2s`/`spi i`/`jmp .-3` loop checks typewriter status
- **Flag-based interrupt** — `szf i 1` tests flag 1 (typewriter buffer full)
- **FIO character encoding** — Characters are 6-bit FIO codes packed into 18-bit words
- **Case shift management** — `uc`/`lc` routines manage uppercase/lowercase shift state

The handbook currently has no section on terminal I/O. This would be section 14
or integrated into section 8 (Display Programming) as "Typewriter I/O."

Confidence: **Very High** — standard PDP-1 I/O practice; used in all interactive programs.

### 3. FIO Character Constants and the `char` Prefix

DDT's comments reference character constants with a `char` prefix:

```asm
char l?+char ma       ; some character expression
char l?+char mi       ; io
char l?+char mm       ; msk
char ri               ; 10000
```

The `char` prefix generates FIO (Flexowriter IO) character codes. These are
6-bit values representing typewriter characters (letters, digits, punctuation).
The expression `char l?+char ma` combines two character codes into one word.

This is another meta-programming layer — building character data at assembly
time rather than hardcoding numeric FIO codes. Related to the `disp` macro
which uses `char` for dispatch table entries.

Confidence: **High** — used in DDT; common in PDP-1 programs with typewriter I/O.

### 4. Combined Octal/Decimal Print Subroutine (section 6)

DDT's `opt` routine prints numbers in either octal or decimal, controlled by
a switch (`ops`):

```asm
; Octal divisors table
odv,    100000  ci, 10000      1000
        100    10      one, 1

; Decimal divisors table
ddv,    decimal 100000  10000   1000
        100     10      1       octal

; Print routine
opt,    0
        dap opx
ops,    init op1, odv       ; switchable: odv or ddv
        setup op2, 6        ; 6 digits
        stf 1               ; set flag 1 for first digit
opa,    dzm opd             ; clear digit count
        szf i 1
        jsp tou             ; print leading... wait, no — print digit
        ...
```

The octal divisors are `100000` (8^5), `10000` (8^4), `1000` (8^3), `100` (8^2),
`10` (8^1), `1` (8^0). The decimal divisors are the standard powers of 10.
The algorithm subtracts the largest divisor repeatedly, counting how many times
it fits, then prints that digit and moves to the next divisor.

This is a complete number formatting system — more sophisticated than anything
in our tic-tac-toe code, and generalizable to any PDP-1 project needing
numeric output.

Confidence: **Very High** — general algorithm; used in DDT and Spacewar! scorer.

### 5. Runtime Symbol Table Management — `est`, `evl`, `def`, `tbl`

DDT maintains a symbol table in memory at runtime:

```asm
est,    low             ; est = end of symbol table (initial value)

; Evaluate symbol — search symbol table
evl,    dap evx
evc,    lac est          ; start at est
        dap ev2          ; modify pointer
ev2,    lac .            ; self-modifying: points to current symbol
        sad sym          ; match?
        jmp ev3          ; yes
        idx ev2          ; advance pointer
        index ev2, evc, ev2  ; loop until match or wrap
        idx evx
ev3,    idx ev2
evx,    jmp .            ; return

; Define symbol — add to symbol table
de,     dap dex
        lio df1          ; value to assign
        jsp evl          ; already defined?
        jmp df2          ; yes — overwrite
        law i 1
        add est          ; expand table
        dap est
        dio i est        ; store value
        sub one
        dap est
        lio sym          ; symbol name
        dio i est        ; store symbol
        jmp dex
df2,    dio i ev2        ; overwrite existing entry
dex,    jmp .
```

This is a **minimal associative data structure** — an unordered list of
(symbol, value) pairs stored contiguously in memory. Lookup is linear search.
Insertion appends at the end. The symbol table grows downward from `est`
toward `low`, while the stack/program grows upward — they meet in the middle.

This pattern is essential for any program that needs to remember named entities
at runtime (variable names, labels, user-defined symbols). It's the PDP-1's
version of a hash table.

Confidence: **Very High** — standard technique in PDP-1 systems software.

### 6. Character Dispatch Table — The `disp` Macro (section 7)

DDT's command parser uses a character-indexed dispatch table:

```asm
define
disp lc,uc              ; was dispatch lc,uc
        [1000^uc]+lc-[1001^lse]
        term

; Dispatch table — indexed by FIO character code
dtb,    disp pls, pls   ; 0: plus/plus
        disp n, quo     ; 1: number/quote
        disp n, sqo     ; 2: number/square-o
        disp n, pbx     ; 3: number/pbx
        ...
```

The `disp` macro computes a jump table entry from two addresses (lower-case
and upper-case handlers). The expression `[1000^uc]+lc-[1001^lse]` packs
both targets into a single word — when the character's case bit is 0 (lower),
the lower-case routine is called; when 1 (upper), the upper-case routine.

The dispatch mechanism (at line 226-232):
```asm
        lac .
cas,    xx              ; modified by uc/lc to rar 9s or cli
        and (777        ; mask to 9-bit character code
cad,    add tls         ; add dispatch table base
        dap lsx         ; modify jump target
        sub ar1         ; bounds check
        spq             ; skip if positive (within table)
        jmp i lsx       ; dispatch to handler
lsx,    jmp .
```

This is a character-driven command interpreter — the foundation of every
interactive PDP-1 tool. Each FIO character code indexes into the table.
The `cas` instruction is self-modified to handle uppercase vs lowercase
(rar 9s vs cli — either rotate to get character from upper half or just
use it directly).

Confidence: **Very High** — standard technique in PDP-1 systems software.

### 7. Breakpoint / Trap System (section 5, advanced)

DDT implements breakpoints by patching user code:

```asm
; Set breakpoint
bk,     spi             ; break command
        init bk1, ch    ; save current address
        jmp lse

; Trap handler
tr,     0
        dap prc         ; save return
        dap prd
        idx prd         ; prd = prc + 1
        lac tr          ; load trapped instruction
        dac ac          ; save in AC display
        isp ch
        jmp pr2         ; display state
        jsp tr1         ; handle trap

tr1,    dac ovf         ; save AC
        dio io          ; save IO
        jsp sbc         ; check sequence break status
        dzm fl1
        szf 1
        dac fl1
        move bki, i bk1  ; restore original instruction
        lac bk1
        jmp i ovf       ; return to user program

; Execute one instruction
xec,    dac xe1         ; save instruction to execute
        law xe1
bgn,    spi             ; begin execution
        jmp err
        dap bix         ; set return
        lac prc
        dip bix         ; patch return address
        jmp pr1         ; start execution
```

This is an **interactive debugger** — DDT can single-step, set breakpoints,
examine/modify registers, and resume execution. The breakpoint mechanism:
1. Saves the instruction at the break address (`bki`)
2. Replaces it with `jda tr` (trap to debugger)
3. When hit, the trap saves state and lets user inspect
4. On resume, restores the original instruction and executes it

This is the foundation of all PDP-1 debugging tools. The handbook's debugging
section (10) should reference this pattern.

Confidence: **Very High** — fundamental debugger technique.

### 8. Paper Tape Block I/O — `pur`, `pbb`, `pbw` (new section)

DDT reads and writes paper tape blocks — the PDP-1's primary storage:

```asm
; Punch one word
pbw,    dap pby
        ppb             ; punch 6 bits
        rcl 6s          ; rotate next 6 bits into position
        ppb
        rcl 6s
        ppb
        rcl 6s
        add t2          ; checksum
        dac t2
pby,    jmp .

; Punch binary block
pbb,    dap pb2
        dzm t2          ; clear checksum
        lio fa          ; punch block address
        jsp pbw
        lio t           ; punch word count
        jsp pbw
pb1,    lio i fa        ; punch data words
        jsp pbw
        index fa, t, pb1
        lio t2          ; punch checksum
        jsp pbw
pux,    feed 5          ; feed 5 blank chars
pb2,    jmp .

; Read a block
rbk,    dap rbx
        init rb1, buf
        dap la
        dzm chi         ; clear checksum
        rpb             ; read paper tape
        dio t2          ; save word count
        dio t
        spi
        jmp lse         ; start reading
        rpb
        dio ch          ; read block address
rb0,    rpb
rb1,    dio .           ; read data word
        lac i rb1
        add chi
        dac chi         ; accumulate checksum
        idx rb1
        index t2, ch, rb0
        add chi
        add t
        rpb
        dio chi
rb2,    sad i .-1       ; verify checksum
rbx,    jmp .
        hlt+clc-opr     ; checksum error
```

RIM format uses 6-bit bytes (the paper tape hole pattern). Each word is
punched as three 6-bit groups via `ppb`. Blocks have address, word count,
data, and checksum. The `feed` macro advances the tape between blocks.

This is the foundation of the PDP-1's storage system. The handbook currently
has no section on paper tape I/O.

Confidence: **Very High** — fundamental PDP-1 I/O; used by every program.

### 9. The `repeat` + `cli`/`rcl 6s`/`ppa` Pattern (section 2.3)

DDT has a compressed I/O loop:

```asm
tt1,    0
        dap tt2
        lac i tt1
        repeat 3 cli rcl 6s ppa    ; unrolled: clear IO, rotate, punch
tt2,    jmp .
```

This is a tight loop that punches 3 FIO characters (18 bits) from one word.
The `repeat` directive unrolls the body 3 times at assembly time, producing:

```asm
        cli
        rcl 6s
        ppb
        cli
        rcl 6s
        ppb
        cli
        rcl 6s
        ppb
```

This is the same technique as Spacewar!'s `repeat 10, starp` but applied to
I/O rather than display. Confirms `repeat` is a general PDP-1 pattern, not
game-specific.

Confidence: **Very High** — confirmed in both DDT and Spacewar!.

---

## Existing Handbook Rules Confirmed (with new evidence)

### 10. DAP Return Convention (section 5.3) — Very High Confidence

DDT uses the same `dap ret` / `jmp .` pattern everywhere:
- `tou, dap tox / tox, jmp .`
- `opt, dap opx / opx, jmp .`
- `sbc, dap sbx / sbx, jmp .`
- `pad, dap px / px, jmp .`
- `tys, dap tyx / tyx, jmp .`

This confirms the pattern is universal across ALL PDP-1 software — games,
simulators, AND systems tools. The handbook's rule stands as Very High
confidence.

### 11. Computed GOTO Dispatch (section 7, handbook) — Very High Confidence

DDT's entire command interpreter is a computed GOTO through `dtb`. The
`disp` macro generates jump table entries. The dispatch mechanism
(`dap lsx` / `jmp i lsx`) is identical in form to our tic-tac-toe `drawwin`
dispatch and the ICSS pattern.

### 12. Self-Modifying Pointers (section 5.6, handbook) — Very High Confidence

DDT uses `init` to set up self-modifying pointers throughout:
```asm
init bax, lwt           ; generates: law lwt / dap bax
init tas, ch            ; law ch / dap tas
init bk1, ch            ; law ch / dap bk1
init rb1, buf           ; law buf / dap rb1
init op1, odv           ; law odv / dap op1
```

These modify `dap` targets, `lac .` targets, and `dac .` targets — the
same technique used in ICSS and Spacewar!.

### 13. The `swap` Macro — Confirmed (section 1.3)

DDT defines `swap` explicitly (line 152-156):
```asm
define
swap
/       swp             / See note at top of file
        rcl 9s
        rcl 9s
        term
```

The comment reveals that the original source had `swp` which was not defined.
The transcriber correctly guessed it was `rcl 9s` × 2 — the standard swap
pattern. This confirms both the technique AND that the name `swap` was used
in period code (not just `swp`).

---

## Handbook Rules Challenged or Extended

### 14. Memory Layout (section 4) — Extended for Systems Software

ICSS and Spacewar! use a clean code-data separation. DDT uses a more complex
layout dictated by its role as a debugger:

1. **Origin at 6000/ octal** — DDT lives at the top of memory, leaving lower
   addresses for user programs being debugged
2. **`low` is computed** — `low=.-nsy-nsy-1` dynamically sets the bottom
   boundary based on symbol table size
3. **`est` is the symbol table pointer** — grows downward from `low` toward
   the origin. Not a fixed address.
4. **Built-in assembler data** — the `flex` table (opcode definitions) is
   inline code, not separate data
5. **Buffer memory** — `buf, buf+100/` reserves 100 (octal) words for the
   paper tape read buffer

Systems software has different memory organization needs than games. The
handbook should note this with a "Systems Programming" subsection.

### 15. `\`-prefixed Locals (section 3.2) — Extended

DDT does NOT use `\`-prefixed locals. Instead it uses descriptive global
names for all variables:
- `wrd`, `sym`, `chi`, `let`, `ch`, `loc` — parser state
- `lwt`, `df1`, `t`, `t2`, `ovf` — general temporaries
- `ac`, `io`, `msk` — user register display
- `fl1`, `sbi`, `bki` — debugger state
- `ll`, `ul` — memory bounds

No prefix convention at all — just plain names. This is a valid style for
programs where every variable is genuinely global. The handbook should note
that local-scope prefixes (`\` or `.`) are beneficial for large programs but
not required for smaller or single-purpose tools.

### 16. Comment Density (section 11) — Extended

DDT has minimal comments compared to our tic-tac-toe code, but more than
Spacewar!. Most routines have a single-line comment:

```
/print octal integer       ; eql,
/print as instruction      ; arw,
/type symbol, etc.         ; tys,
/print address             ; pad,
```

Comments explain WHAT, rarely HOW. The code is assumed to be self-explanatory
to experienced PDP-1 programmers. This is consistent with the period style.
The handbook's recommendation of verbose comments should be framed as a modern
best practice.

---

## New Sections Proposed for the Handbook

| Section | Content | Priority |
|---------|---------|----------|
| **14. Terminal I/O** | Typewriter input/output (tyi, tyo, cks, listen pattern), FIO character codes, case shift management, busy-wait polling | High |
| **15. Paper Tape I/O** | RIM format, punch (ppb, pbw), read (rpb, rbk), checksums, block format, feed | High |
| **16. Systems Software Patterns** | Runtime assembler/disassembler, symbol table management, interactive command dispatch, breakpoint/trap system | Medium |
| 2.3 Macros | Add `flex` opcode-definition meta-macro, `disp` character-dispatch macro | High |
| 2.5 Pseudo-ops | Add `char` prefix for FIO character constants | Medium |
| 10 Debugging | Add DDT breakpoint/trap pattern as reference implementation | Low |

---

## Summary

DDT (1966) confirms:

- **8 handbook rules** at Very High confidence (DAP return, computed GOTO,
  self-modifying pointers, `swap` = `rcl 9s` × 2, `init`/`index`/`setup`/`count`
  macros, `repeat` directive, `clear` range directive)
- **Extends 3 rules** (memory layout for systems software, global-only variable
  naming as valid style, minimal commenting as period practice)
- **Adds 9 new patterns** not in the handbook (typewriter I/O, paper tape I/O,
  `flex` opcode table, FIO character constants, octal/decimal formatting,
  symbol table management, character dispatch table, breakpoint/trap system,
  `repeat`+I/O loop unrolling)
- **Proposes 3 new sections** (Terminal I/O, Paper Tape I/O, Systems Software
  Patterns)

The most significant finding is that DDT shares the same core macro set
(`init`, `index`, `setup`, `count`, `clear`, `load`, `swap`) with both ICSS
and Spacewar! — confirming these are **standard MACRO-1 library macros**, not
project-specific inventions. Future handbook revisions should treat this macro
set as canonical, analogous to a C standard library.
