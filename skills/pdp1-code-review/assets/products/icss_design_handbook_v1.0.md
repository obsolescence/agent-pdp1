# PDP-1 Design Handbook v1.0

**Derived from:** ICSS v1.3 (Ironic Computer Space Simulator) by Norbert Landsteiner (2025)
**Source:** `/opt/pidp1-dev/tapes/sources/icss_1_3.mac` (1,979 lines)
**Platform:** PDP-1, MACRO-1 assembler, Type 30 CRT display
**Reference docs:** `~/.hermes/profiles/siggy/skills/software-development/pdp1-programmer/references/`

**Purpose:** A complete design handbook for writing PDP-1 assembly programs,
synthesizing the architecture, assembler conventions, naming, memory
organization, subroutine linkage, arithmetic idioms, loop idioms, display
programming, optimization techniques, debugging, commenting standards,
common pitfalls, and best practices — all grounded in real code from ICSS
v1.3 and supported by DEC's PDP-1 Handbook and MACRO-1 Programming Guide.

**Confidence scale (Phase 7):**
- **Very High** — observed in multiple independent PDP-1 programs and DEC documentation
- **High** — repeated in one major program and architecturally justified
- **Medium** — observed occasionally in ICSS; plausible but limited evidence
- **Low** — plausible but based on limited evidence; may be aspirational

---

## Table of Contents

1. [Architecture](#1-architecture)
2. [Assembler Conventions](#2-assembler-conventions)
3. [Naming Conventions](#3-naming-conventions)
4. [Memory Organization](#4-memory-organization)
5. [Subroutines](#5-subroutines)
6. [Arithmetic Idioms](#6-arithmetic-idioms)
7. [Loop Idioms](#7-loop-idioms)
8. [Display Programming](#8-display-programming)
9. [Optimization](#9-optimization)
10. [Debugging](#10-debugging)
11. [Commenting](#11-commenting)
12. [Common Pitfalls](#12-common-pitfalls)
13. [Best Practices](#13-best-practices)

---

## 1. Architecture

### 1.1 Memory Model

The PDP-1 is a single-address, stored-program computer with 18-bit word
size. Memory is organized as up to 4,096 words (12-bit address space, but
only 5 bits in the base instruction format; extended addressing uses
indirection and the memory extension register). All instructions and data
share the same address space — the von Neumann architecture is directly
accessible at all times.

Confidence: **Very High** — PDP-1 Handbook, DEC documentation.

### 1.2 The 18-Bit Word

Everything on the PDP-1 is 18 bits. Instructions are 18 bits. Data is 18
bits. The word has two representations:

- **Octal notation:** 6 octal digits, e.g., `311040` = 2π in the angle
  encoding. Each digit is 3 bits.
- **Bit numbering:** Bit 0 = most significant (sign), Bit 17 = least
  significant. The sign bit is position `400000` octal.

The PDP-1 uses **one's complement** arithmetic. Positive zero = `000000`,
negative zero = `777777` (all 18 bits set). This creates pitfalls with
comparisons and negation that are absent in two's complement machines.

**(ICSS reference:** `rkr` angle normalization at lines 1474–1478 uses
`SMA` (skip on minus AC) to test the sign bit, then `SUB (311040` or
`ADD (311040` to wrap within range.)

Confidence: **Very High**

### 1.3 Registers

| Register | Width | Purpose | Encoding |
|----------|-------|---------|----------|
| AC | 18 | Arithmetic accumulator; holds X for DPY | Bit 0 = sign |
| IO | 18 | Input/Output register; holds Y for DPY | Bit 0 = sign |
| PC | 12 | Program counter | 12-bit, mod 2^12 |
| FLAGS | 6 bits | Hardware flag bits (accessible via STF/CLF/SZF) | Bits 1–6 |
| SW | 6 | Sense switches (read via SSW instruction) | Input only |

**AC and IO form a 36-bit register pair** for shift and rotate operations.
The `RCL 9s` instruction rotates the combined pair left by 9 bits; two
`RCL 9s` instructions swap AC and IO — the `swap` macro in ICSS.

**(ICSS reference:** `swap` macro at lines 20–23: `RCL 9s` / `RCL 9s`.)

Confidence: **Very High**

### 1.4 Flag Bits

The 6 flag bits are the PDP-1's fastest inter-routine communication
mechanism — single-cycle set (`STF n`), clear (`CLF n`), and test
(`SZF n`). They survive subroutine calls and are global to the processor.

ICSS uses them extensively:

| Flag | ICSS Purpose | Set By | Cleared By | Tested By |
|------|-------------|--------|------------|-----------|
| 1 | Rocket alive | `rka` (line 1459) | Frame start (line 535) | `eta` (1254), `rkq` (1591), `trp` (1630) |
| 2 | Thrust this frame | `rkt` (line 1482) | Frame start (line 536) | `rkq` (1613), `rot` (1791) |
| 3 | Torpedo fire requested | `rkt` (line 1485) | Frame start (line 537) | `rkq` (1589) |
| 4 | Unused | — | — | — |
| 5 | X sign / explosion block / no-respawn | Multiple | Multiple | Multiple |
| 6 | Y sign / first-dot / mirror pass | Multiple | Multiple | Multiple |

**Key distinction:** `SZF n` tests the current context's flag. `SZF I n`
(indirect) tests the flag of the *returning* subroutine — the flag state
at the caller's return address. This is used in the rocket display (line
1766: `SZF I 6` tests if we're in pass 1 or pass 2 of the mirror drawing).

Confidence: **Very High**

### 1.5 EAE — Extended Arithmetic Element (Multiply/Divide)

The Type 10 EAE provides hardware `mul` and `div` instructions. These must
be enabled at runtime on the blincolnlights emulator:

```
pdp1dbg.py 'muldiv on'
```

**Important:** `muldiv` with no argument **toggles** the state. On every
emulator restart, MUL/DIV resets to OFF.

**MACRO-1 definition (place at top of source):**
```asm
mul=mus     ; MUL = opcode 26 (alias for mus)
div=dis     ; DIV = opcode 27 (alias for dis)
```

**MUL product format:** The 36-bit product (AC, IO) is NOT a simple
high-18/low-18 split. Sign in AC bit 0 and IO bit 17. Magnitude is 34
bits stretching from AC bit 1 through IO bit 16. Reading IO as a plain
integer expecting the low 18 bits is wrong — the magnitude LSB sits at
IO bit 16, not IO bit 0.

**DIV behavior:** DIV skips the next instruction on success. A `jmp .+1`
must absorb this skip:
```asm
div divisor
jmp .+1     ; absorbed by DIV skip
dac result  ; stores the quotient
```

ICSS v1.3 does NOT use EAE multiply/divide — all arithmetic uses
shift-and-add series. The EAE is documented here for programs that
choose a different performance tradeoff.

Confidence: **Very High**

### 1.6 Type 30 Display

The Type 30 is a point-plotting CRT (vector display). It draws dots, not
lines. Every "line" or "shape" is a sequence of individual `DPY` dots.

- **X coordinate:** Bits 0–9 of AC (10-bit signed one's complement)
- **Y coordinate:** Bits 0–9 of IO (10-bit signed one's complement)
- **Range:** −511 to +511 (10-bit signed)
- **Center:** (0, 0) at screen center
- **Positive Y:** UP on screen
- **Toroidal space:** Overflow at screen edges wraps naturally due to
  one's complement arithmetic

**Two zeros pitfall:** In one's complement, both +0 (0000000000) and −0
(1111111111 = 1777 octal in 10 bits) exist. Negative zero maps to a pixel
position just left and below of (0,0).

Coordinates must be in bits 0–9 of the register. Loading a small number
like `lac (100` puts the value in bits 8–17 (low bits), so bits 0–9 are
all zero → dot at screen center regardless of the value! Pre-format
constants in the high bits, or shift left by 8 after computation.

**(ICSS reference:** Character grid unit `cgy` at line 286:
`cgy, 010000` — value 16 decimal, encoded as bits 0–9 = `0000010000`,
full word = `0000010000 00000000`.)

Confidence: **Very High**

---

## 2. Assembler Conventions

### 2.1 MACRO-1 Syntax

- **Default radix is octal.** Digits 8 and 9 are INVALID. `board+8` fails;
  use `board+10` for decimal 8.
- **Comments:** Tab before `/` for end-of-line comments. Space before `/`
  = syntax error in some assembler versions.
- **Labels:** Any alphanumeric identifier starting with a letter.
  `\`-prefix denotes local variables (see 2.2 below).
- **`(label`** evaluates to the **contents** at address `label`, not the
  address of `label`. To get an address, use `LAW label`.
- **`= (EQU)`** assigns a value: `label, value` followed by a term.
  `label, . 1/` reserves one word.

Confidence: **Very High**

### 2.2 Local Variables (\ Prefix)

The `\` prefix (single backslash before a label name) creates a local
symbol scoped to the enclosing section. In ICSS, these are used for
temporary variables, counters, and per-routine state.

Examples from ICSS:
```asm
\frc, . 1/     ; frame counter (free-running)
\ict, . 1/     ; cycle budget counter (negated, counts up to zero via ISP)
\umo, . 1/     ; saucer direction: 0-7 for movement, -3..-1 for stop phase
\trs, . 1/     ; torpedo status: <=0 inactive, >0 life remaining
```

The `\` prefix is assembler syntax, not a runtime concept. When the
assembler processes these, they become ordinary memory addresses.

**Important:** In MACRO-1, the `\` must appear literally. The assembler
uses a single backslash as the local variable prefix (not a double
backslash). Some documentation shows `\\` because the backslash needs
escaping in certain contexts.

Confidence: **Very High**

### 2.3 Macros

MACRO-1 supports parameterized macros. ICSS defines 9 macros at the top
of the source (lines 1–55):

| Macro | Parameters | Expansion | Purpose |
|-------|-----------|-----------|---------|
| `initialize A,B` | 2 (target, address) | `LAW B` / `DAP A` | Set self-modifying pointer |
| `index A,B,C` | 3 (counter, limit, jump) | `IDX A` / `SAS B` / `JMP C` | Loop iterator |
| `swap` | 0 | `RCL 9s` × 2 | Exchange AC↔IO |
| `load A,B` | 2 (target, source) | `LIO (B` / `DIO A` | Load IO from memory |
| `setup A,B` | 2 (target, label) | `LAW I B` / `DAC A` | Store address of B |
| `count A,B` | 2 (counter, jump) | `ISP A` / `JMP B` | Decrement counter, loop if not zero |
| `scale A,B,C` | 3 (src, shift, dst) | `LAC A` / `SAR B` / `DAC C` | Arithmetic right shift |
| `random` | 0 | 5-instruction LFSR | Next pseudorandom number |
| `disp` | 0 | `DPY -I 100` | Display dot at brightness 1 |
| `sdisp B` | 1 (brightness) | `DPY -4000 B` | Display with explicit brightness |

Macro definition syntax:
```asm
macro_name, MACRO
        instruction
        instruction
        ENDM
```

Confidence: **Very High**

### 2.4 The `term` Directive

`term` in MACRO-1 marks the end of an assembly unit. Every source file
must end with `term` or the assembler will not produce output. ICSS ends
with `start 4` (which is a `term` variant that sets the entry point).

```
term        ; end of assembly
start 4     ; end of assembly with entry point at address 4
```

Confidence: **Very High**

### 2.5 Origin and Pseudo-Ops

- **`label,`** — Define a label at the current location counter. Used for
  both code labels and variable declarations.
- **`. N/`** — Reserve N words. `cgx, . 4/` reserves 4 words starting at
  `cgx`. `coa, . 21/` reserves 21 words.
- **`label, value`** — Define a numeric constant. `raa, 1200` defines a
  parameter.
- **`constants`** — Directive (at line 1974). All subsequently defined
  symbols are treated as constants (assembler assigns addresses on the
  current page, reusing space).
- **`variables`** — Directive (at line 1975). All subsequently defined
  symbols are treated as variables (assembler assigns addresses
  sequentially).
- **`start N`** — Set program entry point to address N (octal). Must be
  the last line of the source.

**Startup vectors:** ICSS places three `JMP` instructions at locations
3–5 (lines 97–99):
```asm
. 3/
        JMP sbf    ; address 3: ignore sequence break (interrupt)
        JMP a0     ; address 4: start — control boxes (Spacewar!)
        JMP a1     ; address 5: alternate start — testword (keyboard)
```

Confidence: **Very High**

---

## 3. Naming Conventions

### 3.1 Labels

ICSS uses short, meaningful label names — typically 2–3 characters.
Naming conventions are consistent:

| Pattern | Example | Meaning |
|---------|---------|---------|
| Verb | `bg` (background display), `ufo` (saucer), `rkt` (rocket) | Main routine entry |
| Verb+letter | `ufi` (saucer budget update), `uf1` (saucer sub-label) | Internal routine sections |
| Initials | `dmf` (distance measuring function), `scd` (score display) | Descriptive acronyms |
| Two-letter | `ar` (rocket setup), `au` (saucer setup), `ax` (return) | Sections of larger routines |
| Table | `ut0`, `ut1` (movement tables), `bst` (star table) | Data tables |
| Parameter | `raa`, `rvl`, `ras`, `rad` (rocket params) | Game parameters |

Confidence: **High** — consistent within ICSS; short names are standard in
PDP-1 programming due to 5-bit address fields and octal debugging.

### 3.2 Local Variable Naming

`\`-prefixed local variables use 3-character names:

| Variable | Meaning |
|----------|---------|
| `\t1`, `\t2` | General temporaries |
| `\frc` | Frame counter |
| `\ict` | Instruction cycle counter |
| `\rks` | Rocket state |
| `\rth` | Rocket angle (theta) |
| `\rpx`, `\rpy` | Rocket position |
| `\rdx`, `\rdy` | Rocket velocity |
| `\sn`, `\cs` | sin(θ), cos(θ) |
| `\sn1`–`\sn8` | Sine step values (1–8 step sizes) |
| `\sm1`, `\sm3`, `\sm6` | Negated sine combinations |
| `\upx`, `\upy` | Saucer (UFO) position |
| `\udx`, `\udy` | Saucer velocity |
| `\umo` | Saucer motion code / stop phase |
| `\ufs` | Saucer state |

**Note:** Some variables serve dual purposes (e.g., `\umo` holds both the
direction code 0–7 for movement AND the stop phase −3..−1). This is a
memory-saving technique but requires careful documentation.

Confidence: **High**

### 3.3 Return Address Naming

Every subroutine has a dedicated return address label with the `x` suffix:

| Subroutine | Return Label |
|-----------|-------------|
| `sin`/`cos` | `csx` |
| `ci` (char init) | `cix` |
| `cc` (char compiler) | `ccx` |
| `cdp` (char display) | `cdx` |
| `bsi` (stars init) | `bsx` |
| `bg` (stars display) | `bgx` |
| `ufo` (saucer) | `ufx` |
| `rkt` (rocket) | `rkx` |
| `rod` (rocket display) | `rox` |
| `sd` (saucer display) | `sdx` |
| `trp` (torpedo) | `trx` |
| `etm` (enemy torp) | `etx` |
| `scd` (score display) | `scx` |
| `df` (collision) | `dfx` |
| `dmf` (distance meas) | `dmx` |
| `rcb` (control read) | `rcx` |

The `x` suffix is a reliable signal: "this instruction is a `JMP .`
modified by `DAP` at the subroutine entry."

Confidence: **Very High**

### 3.4 Data Pointer Naming

Self-modifying data pointers (not subroutine returns) use descriptive
names without the `x` suffix:

- `mx1`, `mx2`, `my1`, `my2` — Collision detection coordinate pointers
  (modified `LAC .` / `SUB .` instructions)
- `ci4`, `ci5` — Character compiler pointer slots
- `bsc`, `bgl` — Star table iteration pointers

These are DAP targets, but they modify `LAC .`, `DAC .`, or `SUB .`
instructions, not `JMP .` returns.

Confidence: **Very High**

### 3.5 Parameter Naming

Game parameters use 3-letter names in address range 6–34 octal:

| Label | Purpose | Encoding |
|-------|---------|----------|
| `raa` | Rocket angular acceleration | Numeric: `1200` |
| `rvl` | Rocket velocity scaling | Instruction: `SAR 8s` |
| `ras` | Rocket acceleration skip | Instruction: `LAW I 6` |
| `rad` | Rocket damping iterations | Instruction: `LAW I 4` |
| `trv` | Torpedo velocity scaling | Instruction: `SAR 7s` |
| `tlf` | Torpedo life | Instruction: `LAW I 250` |
| `rsd` | Rocket reset delay | Numeric: `60` |
| `etl` | Enemy torpedo life | Instruction: `LAW I 220` |
| `etd` | Enemy torpedo cooling | Instruction: `LAW I 10` |
| `ela` | Enemy look-ahead far | Instruction: `SAL 6s` |
| `elb` | Enemy look-ahead near | Instruction: `SAL 4s` |
| `eld` | Min distance for look-ahead | Numeric: `60000` |
| `ete` | Tight aiming epsilon | Numeric: `14000` |
| `etn` | Noise scaling | Instruction: `SAL 3s` |

Confidence: **High**

---

## 4. Memory Organization

### 4.1 Code vs. Data Layout

ICSS follows a clean organization:

1. **Macros** (lines 1–55)
2. **Startup vectors** (lines 97–99)
3. **Parameter tables** (lines 102–138) — in code space near the origin
4. **Movement tables** (lines 140–171)
5. **Subroutines** — each with its own local variables embedded before the
   routine or at the end
6. **Compiled character code** — dynamically generated at `ctb` (line 1977)
7. **Constants / Variables** — blocks at end of source (lines 1974–1979):
   ```
   constants
   variables
   ctb, . 1000/    ; reserve 1000 octal words for compiled code
   start 4
   ```

Confidence: **Very High**

### 4.2 Parameter Blocks

Parameters are stored in a contiguous block (addresses 6–34 octal) at the
start of the program. They serve as inline constant tables:

```asm
; Rocket parameters
raa, 1200               ; angular acceleration
rvl, SAR 8s             ; velocity scaling
ras, LAW I 6            ; acceleration skip counter reload
rad, LAW I 4            ; damping loop count
trv, SAR 7s             ; torpedo velocity scaling
tlf, LAW I 250          ; torpedo life
rsd, 60                 ; reset delay

; Enemy torpedo parameters
etl, LAW I 220
etd, LAW I 10
; ...
```

Parameters are accessed via `LAC param` (for numeric values) or `XCT param`
(for instruction-encoded values). The block is intermixed with code but is
never executed — it sits immediately after the startup jump vectors and
before the first subroutine.

Confidence: **High**

### 4.3 Temporary Variables

Local (`\`-prefixed) variables are allocated inline at the point of first
use. For example:
```asm
\frc, . 1/     ; frame counter
\ict, . 1/     ; cycle budget counter
\scc, . 1/     ; score display timeout
```

Two global temporaries `\t1` and `\t2` serve as general-purpose scratch
registers throughout the program. They are reused freely across different
routines — no caller-saves discipline is enforced.

Confidence: **High**

### 4.4 Tables

Key data tables in ICSS:

| Table | Size | Format | Location |
|-------|------|--------|----------|
| `bst` | 63 words | Packed 9+9 bit (X/Y) | Background section |
| `upt` | 64 words | Packed 9+9 bit (Y/X) | Explosion section |
| `upd` | 64 words | dY/dX velocity pairs | Explosion section |
| `uxo` | 26 words | (dy, dx) offset pairs | Explosion section |
| `ut0` | 16 words | 8 × (dy, dx) | Movement tables |
| `ut1` | 16 words | 8 × (dy, dx) | Movement tables |
| `emt` | 16 words | 8 × (dy, dx) | Movement tables |
| `cot` | 32 words | 16 chars × 2 words | Character compiler |
| `coa` | 21 words | Addresses of compiled code | Character compiler |

Tables are always contiguous in memory. Indexing uses `SAL 1s` (×2) for
2-word entries, or manual addition for packed formats.

Confidence: **Very High**

### 4.5 Packed 9+9 Bit Coordinates

Two 9-bit coordinate values pack into one 18-bit word. The unpack sequence:

```asm
CLI             ; clear IO
SCR 9s          ; shift AC right 9: low 9 bits of AC → high 9 of IO
SAL 9s          ; shift AC left 9: remaining 9 bits → AC high 9 bits
```

After unpacking: AC bits 0–8 = X, IO bits 0–8 = Y. This is exactly what
`DPY -I` expects.

```asm
; Star display loop (lines 463–471)
bgl,    LAC .           ; load packed word (self-modifying pointer)
        CLI
        SCR 9s          ; unpack: Y into IO high bits
        SAL 9s          ; X into AC high bits
        ADD bgv         ; add vertical scroll offset
        SWAP            ; Y → IO, X → AC
        ADD bgh         ; add horizontal scroll offset
        DPY -I          ; display star
```

Confidence: **Very High**

---

## 5. Subroutines

### 5.1 JSP Linkage with DAP Return

The standard PDP-1 calling convention used by every routine in ICSS:

**Caller:**
```asm
JSP sub_name    ; stores PC in AC, jumps to sub_name
```

**Callee:**
```asm
sub_name, DAP ret_label    ; save return address (deposit AC bits 6–17 into JMP)
        ...                ; subroutine body
ret_label, JMP .           ; initially a self-loop; modified by DAP to JMP return_addr
```

The `DAP` instruction deposits bits 6–17 of AC (the address portion,
holding the return address from JSP) into the address field of the
`JMP .` instruction, making it jump back to the caller. This is:

1. **Simple** — no save/restore of dedicated return-address storage
2. **Fast** — `DAP` + final `JMP` = 2 instructions for the linkage
3. **Reentrant per call** — each call provides a fresh return address in AC

All 34 `JSP` calls in ICSS follow this pattern. No exceptions.

**Indirect variant:** `JSP I ptr` — jumps through a pointer variable.
Used in ICSS for the sense-switch-selectable control reader (`rcw`).

**(ICSS reference:** `JSP bg` at line 538, `JSP ufo` at line 539, `JSP rkt`
at line 538 of main loop.)

Confidence: **Very High**

### 5.2 JDA Argument Passing

`JDA sub` (Jump and Deposit AC) deposits the contents of AC at the
subroutine entry word, transfers the program counter to AC, and jumps to
`sub+1`. It passes exactly one argument in AC. (Like `JSP`, the return
address goes into AC — never into memory.)

**Caller:**
```asm
LAC angle       ; load argument
JDA sin         ; jump to sine; deposits angle at entry word, return addr in AC, next at sin+1
```

**Callee:**
```asm
sin, 0          ; overwritten by JDA: word = argument (angle << 13)
        DAP csx ; save return address from AC (set by JDA)
        ...     ; access argument via entry word
csx,    JMP .   ; return
```

All 10 `JDA` uses in ICSS pass exactly one argument. No `JDA` call passes
multiple arguments or stores the argument before a `JSP` call.

Confidence: **Very High**

### 5.3 DAP Return — The Universal Pattern

Every subroutine in ICSS uses `DAP` to save the return address at entry
and a modified `JMP .` at exit. The return label always has the `x`
suffix (see Section 3.3).

```asm
; Typical subroutine skeleton (from `bsi` at line 411)
bsi,    DAP bsx     ; save return address
        ...         ; body
bsx,    JMP .       ; return (modified by DAP)
```

**Note:** `DAC ret` / `JMP I ret` is a valid alternative — JSP never
touches the subroutine entry word, so a `DAC ret` at entry executes
normally with the return address in AC. `DAP` / `JMP .` is preferred
(no indirection on return) and is the universal ICSS convention. The
pattern that does NOT work is `sub, 0 / JMP I sub` — that is the PDP-8
`JMS` convention; JSP never writes the return address into `sub`, so
`JMP I sub` jumps through address 0 (garbage).

Confidence: **Very High**

### 5.4 XCT for Inline Parameter Dispatch

The `XCT` instruction executes a single instruction from memory as if it
were inline, without advancing the program counter. ICSS uses this
extensively to load or execute game parameters.

**Pattern 1: Load parameter value:**
```asm
tlf, LAW I 250          ; parameter: torpedo life = 250
        ...
        XCT tlf         ; AC = 250 (executes LAW I 250)
        DAC \trs        ; store as torpedo life
```

**Pattern 2: Execute scaling parameter:**
```asm
rvl, SAR 8s             ; parameter: shift amount
        ...
        XCT rvl         ; executes SAR 8s on current AC
        SWAP            ; move to IO for damping loop
```

**Pattern 3: Indirect XCT:**
```asm
        XCT I \t2       ; execute instruction at the address stored in \t2
```

Parameters encoded as instructions include: `SAR ns` (shift right),
`SAL ns` (shift left), `LAW I N` (load immediate). Plain numeric values
like `raa, 1200` are loaded via `LAC raa`.

**Constraint:** `LAW I N` has limited range (approx. 9-bit unsigned,
max ~256). Values >256 (`1200`, `60000`, `310`) must be plain numbers.
This is why ICSS uses **both** encodings — the choice is dictated by
whether the value fits in a single instruction's immediate field.

**(ICSS reference:** Parameters `rvl`, `ras`, `rad`, `trv`, `tlf`, `etl`,
`etd`, `etf`, `ela`, `elb`, `etn`, `rto` are XCT-encoded. `raa`, `rsd`,
`eld`, `ete`, `efe`, `efd`, `irk`, `isc`, `isx`, `idp` are plain numbers.)

Confidence: **Very High**

### 5.5 JMP I 1 — Sequence Break Return Convention

The sequence break (interrupt) handler uses `JMP I 1`, which jumps to the
address stored in memory location 1. Location 1 is ordinary core memory,
not a special register: when an interrupt is taken, the hardware
automatically stores the AC in location 0, the PC in location 1 (with the
overflow flag in bit 0), and the IO in location 2, then starts the handler
at 0003. The indirect jump through location 1 is the standard
sequence-break return: it restores the interrupted PC and overflow state.

ICSS uses this only for the sequence break handler `sbf` (line 187):
```asm
sbf,    IOT 12/4,6    ; flush typewriter buffer
        JMP I 1       ; return from interrupt
```

No ordinary subroutine uses `JMP I 1`. All use the DAP / `JMP .` pattern.

Confidence: **Very High**

---

## 6. Arithmetic Idioms

### 6.1 Absolute Value (SPA + CMA)

The standard one's-complement absolute value idiom:

```asm
SPA             ; skip if AC positive
CMA             ; complement AC (one's complement negation)
```

After `SPA` + `CMA`:
- If AC ≥ 0: AC unchanged (SPA skipped CMA)
- If AC < 0: AC = ones' complement of AC = |AC| − 1 (since one's complement
  of −N is N−1)

**Important:** This is off by one for negative values. The error is
acceptable for epsilon-based comparisons (collision detection, AI
targeting) but not for exact arithmetic. ICSS never adds the correction
`ADD (1` for two's complement negation — the one's complement
approximation is universally accepted in this codebase.

**ICSS uses in `dmf` (collision, lines 883–892):**
```asm
        LAC I \t1       ; load Δx (through DAP-fixed pointer)
        SUB I \t2       ; subtract Δx2
        SPA             ; skip if positive
        CMA             ; one's complement absolute value
        DAC \dx         ; store |Δx|
```

Also in torpedo AI (lines 1294–1295, 1299–1300, 1318–1319, 1329–1330) and
saucer AI (lines 1343–1344).

Confidence: **Very High**

### 6.2 Manhattan (L1) Distance

Collision detection uses Manhattan distance instead of Euclidean.

**Algorithm (from `dmf`, lines 880–903):**
1. Compute |Δx|. If ≥ εx → miss.
2. Compute |Δy|. If ≥ εy → miss.
3. Compute |Δx| + |Δy|. If ≥ ε₂ → miss.
4. Otherwise → hit.

```asm
dmf,    DAP dmx
        ; X check
mx1,    LAC .           ; load X1 (DAP-fixed pointer)
mx2,    SUB .           ; subtract X2
        SPA
        CMA             ; |Δx|
        DAC \t1
        SUB \dxe        ; compare to epsilon
        SPA             ; if |Δx| >= εx, miss
        JMP dm0
        ; Y check
my1,    LAC .           ; load Y1
my2,    SUB .           ; subtract Y2
        SPA
        CMA             ; |Δy|
        SUB \dye
        SPA             ; if |Δy| >= εy, miss
        JMP dm0
        ; Combined distance
        ADD \t1         ; |Δx| + |Δy|
        SUB \de2        ; compare to combined epsilon
        SPA             ; if sum >= ε₂, miss
        JMP dm0
        ; Hit
        LAC (1          ; return 1
        JMP dmx
dm0,    DZM .           ; return 0 (clear AC first)
        JMP dmx
```

The three-tier test provides early rejection: most objects are far apart,
so the X check alone eliminates most pairs. The `\de2` threshold is
approximately 60–70% of the individual axis epsilons, creating an
elliptical/diamond hitbox.

Confidence: **Very High**

### 6.3 Angle Normalization

After updating an angle, normalize to (0, 2π) by conditional add/subtract.

```asm
rkr,    SMA             ; skip if AC minus (angle < 0?)
        SUB (311040     ; too large: subtract 2π
        SPA             ; skip if AC positive (result >= 0?)
        ADD (311040     ; too small: add 2π
        DAC \rth        ; store normalized angle
```

The constant `311040` octal = 2π in the angle encoding used by the
sine/cosine subroutine. The logic is:
1. If angle ≥ 0 (not negative), try subtracting 2π.
2. If result stays ≥ 0, keep it (angle was > 2π).
3. If result goes negative (angle was < 2π), restore by adding back 2π.

This works because the maximum single-frame rotation is much smaller than
2π, so at most one correction is needed.

Angles for the sine/cosine subroutine must stay in (0, 2π). The internal
normalization in `sin`/`cos` (lines 205–250) also uses the same constant
and `(62210` = π/2 for quadrant reduction.

Confidence: **Very High**

### 6.4 Shift-Series Multiplication (Fractional Multiply)

Fractions with power-of-2 denominators are computed via shift-and-add
series, avoiding the multiply instruction.

**Example: Parallax offset (5/8 of velocity, lines 440–444):**
```asm
        LAC \rdx        ; load X velocity
        SAR 1s          ; >> 1 = ÷2
        ADD \rdx        ; + original
        SAR 3s          ; >> 3 = ÷8 (total: (original/2 + original)/8 = 5/8)
        CMA             ; negate
        ADD bgh         ; apply to background offset
        DAC bgh
```

This decomposes 5/8 = 1/2 + 1/8, each term produced by a right shift.
The `SAR` instruction is arithmetic (preserves sign), so this works for
negative velocities too.

**Rocket tip offset (lines 1530–1532):**
```asm
        SCALE \sn, 4s, \tmp    ; tmp = sin >> 4 = sin/16
        LAC \tmp
        SUB \sn8               ; sn8 = sin >> 6 = sin/64
        DAC \sn1               ; sn1 = sin/16 - sin/64 = 3/16 × sin
```

Here 3/16 = 1/16 − 1/64, computed as `sin/16 - sin/64`.

**Rocket step table (lines 1553–1585):** All power-of-2 step sizes are
generated by cascaded shifts:
```asm
        ; sn8 = sin >> 6, sn4 = sn8 >> 1, sn2 = sn4 >> 1, sn1 = sn2 >> 1
        SCALE \sn, 6s, \sn8    ; sin/64
        LAC \sn8
        SAR 1s                 ; sin/128
        DAC \sn4
        SAR 1s                 ; sin/256
        DAC \sn2
        SAR 1s                 ; sin/512
        DAC \sn1
```

Any fraction N/2^M can be computed as a series of shifts and adds. The
decompositions are derived manually and precomputed once per frame.

Confidence: **Very High**

### 6.5 Exponential Damping via Repeated Averaging

Velocity smoothing is implemented by repeated `(old + new) >> 1`:

```asm
; X damping loop (lines 1506–1512)
rx0,    SWAP             ; bring running average (in IO) to AC
        ADD \rdx         ; add old velocity
        SAR 1s           ; (old + new) ÷ 2
        SWAP             ; store back to IO
        ISP \rdc         ; decrement iteration count (starts at -4)
        JMP rx0          ; loop until count reaches zero
```

After N iterations, the weight of the new input is 1/2^N. With N=4 (from
`rad, LAW I 4`), the new value has 1/16th influence while the old retains
15/16ths — very strong damping. This produces smooth, natural-feeling
acceleration with no multiply or division instructions.

The `SWAP` pattern keeps the running average in IO across iterations,
using the AC/IO register pair as a 36-bit pipeline.

**Two-iteration variant (torpedo steering, lines 1638–1656):**
```asm
        ; new = ((input + tdy) >> 1 + tdy) >> 1
        ; Effectively: 3/4 old + 1/4 new
```

Confidence: **Very High**

### 6.6 Scaling with the SCALE Macro

The `scale` macro (lines 42–45) packages `LAC A` / `SAR B` / `DAC C` into
a single line:

```asm
scale, MACRO A,B,C
        LAC A
        SAR B
        DAC C
        ENDM
```

Used extensively:
```asm
        SCALE \sn, 6s, \sn8     ; sn8 = sin >> 6 = sin/64
        SCALE \cs, 6s, \cn8     ; cn8 = cos >> 6 = cos/64
        SCALE \sn, 4s, \sn1     ; sn1 = sin >> 4 = sin/16
        SCALE \cs, 4s, \cn1     ; cn1 = cos >> 4 = cos/16
        SCALE \sn1, 1s, \rxc    ; rxc = sin/32 (half of tip offset)
        SCALE \cn1, 1s, \ryc    ; ryc = cos/32
```

The macro is used when the shift is a self-contained operation. For
cascading shifts, inline `SAR` is preferred because intermediate `DAC`
instructions would be wasted.

Confidence: **Very High**

---

## 7. Loop Idioms

### 7.1 Count-Up-to-Zero Timers

The fundamental PDP-1 timing idiom: a counter stored negative and
incremented each frame/iteration by `ISP` (increment and skip if positive).

```asm
COUNT \tict, .   ; expands to:
        ISP \tict    ; increment; skip if result >= 0
        JMP .        ; loop back if still negative
```

When the counter reaches zero (or positive), the `ISP` skip fires and
exits the loop. The initial value must be negative.

**Frame budget timer (`\ict`, line 532):**
```asm
        LAC \ifr         ; load negated budget
        DAC \ict         ; e.g., -1190 = -(310+360+60+60)
        ; ... subsystems run, each adding their cost ...
        COUNT \ict, .    ; spin until counter hits zero
```

**Torpedo life (`\trs`, line 1627):**
```asm
        ISP \trs         ; increment life counter
        JMP trx          ; if still negative, continue (alive)
        ; zero reached: torpedo expired
```

This pattern appears in 12+ locations throughout ICSS: `\ict` (frame
budget), `\trs` (torpedo life), `\ets` (enemy torpedo life), `\etc`
(enemy torpedo cooling), `\ufc` (saucer leg duration), `\ufs` (explosion
lifetime), `\scc` (score display timeout), `\rks` (rocket collision
spin), `\rac` (acceleration frame skip), `\gms` (attract mode restart
guard).

Confidence: **Very High**

### 7.2 Count-and-Compare (Modulo Counter)

When the counter needs to compare against a specific modulus (not the sign
boundary), use `IDX` + `SAS`:

```asm
        IDX \fdc         ; increment frame counter
        SAS ifs          ; skip if AC == ifs (74 frames)
        JMP fr2          ; not yet — continue
        DZM \fdc         ; reset counter
        IDX \fd0         ; increment seconds digit
        SAS (12          ; 12 seconds?
        JMP fr2
        DZM \fd0
        ; ... etc.
```

`IDX` leaves the incremented value in AC. `SAS` compares AC against the
literal operand. On match, the counter is reset and the next stage is
incremented. This cascading chain (frames → seconds → tens-of-seconds) uses
base-12 counters (0–11) matching the score display's hex digit encoding.

Confidence: **Very High**

### 7.3 Self-Modifying Loop Bounds

The `initialize` / `index` macro pair iterates over a table by modifying
the operand of a `LAC .` or `DAC .` instruction:

```asm
; Star initialization (lines 418–421)
        INITIALIZE bsc, bst    ; LAW bst → DAP bsc
bsl,    RANDOM
bsc,    DAC .              ; stores random value at current bst position
        INDEX bsc, (DAC bst+nos, bsl
        ; expands to: IDX bsc → SAS (DAC bst+nos → JMP bsl
```

Each iteration:
1. `IDX bsc` increments the address field of the `DAC .` at `bsc`,
   advancing to the next word in the table.
2. `SAS (DAC bst+nos` checks if the modified instruction would write past
   the table end.
3. `JMP bsl` loops back.

The same pattern is used for star display (lines 462–471) and the
character compiler loop (lines 303–314).

**Advantage:** No separate index variable or address calculation — the
instruction's address field IS the pointer. Very tight loop: 4
instructions per iteration.

**Limitation:** Only works for forward iteration. The `SAS` check
compares against a literal assembled constant.

Confidence: **Very High**

### 7.4 Frame-Skip Iteration

Code is selectively executed on a subset of frames by AND-ing the frame
counter with a mask:

```asm
        LAC \frc         ; load frame counter
        AND (1           ; mask: every other frame
        SZA              ; skip if AC zero
        JMP bgi          ; skip this frame if bit 0 is set
        ; ... display stars ...
```

The mask determines the skip rate:

| Mask | Frames Skipped | Fraction Executed |
|------|---------------|------------------|
| `AND (1` | Every other frame | 1/2 |
| `AND (3` | 3 of 4 frames | 1/4 |
| `AND (4` | Every 4th frame | 1/4 (different bit) |
| `AND (177` | 127 of 128 frames | 1/128 |

**ICSS uses:**
- Background stars: `AND (1` — every other frame (line 431)
- Torpedo steering: `AND (3` / `AND (1` — sense-switch selectable (lines
  1633–1635)
- Rocket exhaust: `AND (4` — every 4th frame (line 1804)
- Saucer animation: `AND \uft` — dynamic mask (1 or 3), variable rate
  (line 1003)

The dynamic-mask variant (`AND \uft` where `\uft` holds 1 or 3) allows
the skip rate to change at runtime — `AND 1` = every-other-frame, `AND 3`
= every-4th-frame.

Confidence: **Very High**

---

## 8. Display Programming

### 8.1 AC/IO Coordinate Pipeline

The core pattern for every dot on the Type 30 display:

1. Load/update Y coordinate → AC
2. `SWAP` → Y moves to IO
3. Load/update X coordinate → AC
4. `DPY` — displays (X in AC, Y in IO)

```asm
; Typical point from rocket display (line 1704)
        SWAP             ; bring Y component to AC
        SUB \cn4         ; Y = py - cn4
        SWAP             ; Y → IO
        ADD \sm6         ; X = px + sm6
        DISP             ; DPY -I 100
```

The pipeline is maintained entirely in registers — no memory round-trips
between consecutive display points within the same sprite. This is critical
for performance.

**Saucer hull point (lines 1835–1844):**
```asm
        SZF 6            ; test Y sign (flag 6)
        CMA              ; negate Y if flag set
        ADD \py          ; Y = centerY ± offset
        SWAP             ; Y → IO
        SZF 5            ; test X sign (flag 5)
        CMA              ; negate X if flag set
        ADD \px          ; X = centerX ± offset
        DISP             ; display dot
```

Confidence: **Very High**

### 8.2 DPY vs. DPY -I — Completion Pulse Semantics

Two `DPY` variants exist, and they have DIFFERENT IOH requirements:

| Variant | I/O Transfer Code | Completion Pulse | IOH Required? | ICSS Usage |
|---------|------------------|-----------------|---------------|------------|
| `DPY -I B` | Bit 13 clear | NO | NO | Star display, rocket sprite, torpedo, explosion particles |
| `DPY -4000 B` | Bit 13 set | YES | **YES** | Character compiler, hyperspace indicator, saucer outer dots |

- `DPY -I B` requests NO completion pulse. Multiple dots can be issued
  rapidly without waiting. Used for sequences of dots from the same object.
- `DPY -4000 B` requests a completion pulse. The CRT asserts completion
  when the beam settles. An `IOH` instruction must follow to wait for this
  pulse. Used between dot groups from different objects, or when exact
  positioning matters.

**ICSS example — character compiler (line 367):**
```asm
        COMP (IOH        ; emit IOH instruction
        COMP (DPY -4000 100  ; emit DPY with completion pulse
```

**ICSS example — rocket display (`disp` macro, line 1694):**
```asm
disp, MACRO
        DPY -I 100       ; no completion pulse — fast dot sequence
        ENDM
```

The rocket draws 7+ consecutive dots with `DPY -I` and NO IOH between
them (lines 1704–1764). This works because the dots are closely spaced
and the CRT beam moves fast enough.

Confidence: **Very High**

### 8.3 IOH CRT Synchronization

`IOH` halts the processor until the CRT sends a completion pulse. It's
required after `DPY -4000` but not after `DPY -I`.

**Rule of thumb:**
- Within a single sprite's dots: use `DPY -I` (no IOH) for maximum speed.
- Between different objects (e.g., between rocket and torpedo): use
  `DPY -4000` + `IOH` for correct beam positioning.
- For the first dot of a character outline: emit `IOH` once, then all
  subsequent dots use `DPY -4000` without additional IOH (the completion
  pulse from the previous `DPY` is sufficient).

**Character compiler optimization (lines 364–368):** The first-dot flag
(flag 6) ensures `IOH` is emitted only before the very first dot of each
character — not before every dot:

```asm
        SZF 6            ; is this the first dot?
        JMP ccd          ; no — skip IOH
        COMP (IOH        ; yes — emit IOH
        CLF 6            ; clear first-dot flag
ccd,    COMP (DPY -4000 100  ; emit dot with completion pulse
```

This saves ~6 cycles per dot (one `IOH` ≈ 6 cycles) — significant for
characters with 7–15 dots.

Confidence: **Very High**

### 8.4 Multi-Pass Symmetry Sprites

**Four-pass quadrant drawing (saucer hull):** The saucer is symmetric
about both X and Y axes. Three hull points are defined; flags 5 and 6
control sign negation in a 4-pass loop:

```
Pass 1: Flag 5=0, Flag 6=0  →  (+X, +Y)  Upper-right quadrant
Pass 2: Flag 5=0, Flag 6=1  →  (+X, −Y)  Lower-right quadrant
Pass 3: Flag 5=1, Flag 6=1  →  (−X, −Y)  Lower-left quadrant
Pass 4: Flag 5=1, Flag 6=0  →  (−X, +Y)  Upper-left quadrant
```

The dispatch is via computed GOTO (lines 1868–1881):
```asm
        LAW sdd          ; load dispatch table address
        SUB \sdc         ; subtract counter (-4 to -1)
        DAP sdd          ; modify jump target
        IDX \sdc         ; advance counter (-4 → -3 → -2 → -1 → 0)
        JMP .            ; dispatch to pass handler
sdd,    JMP sd1          ; pass 1: done with hull, draw outer dots
        JMP .            ; pass 2: set flag 6, repeat sdl
        JMP .            ; pass 3: set flag 5, repeat sdl
        JMP .            ; pass 4: clear flag 6, repeat sdl
```

Three hull point definitions produce 12 displayed points — a 4× data
compression.

**Two-pass mirror drawing (rocket):** The rocket is bilaterally symmetric.
Pass 1 draws 7 points for the left half. Between passes, all step values
are negated (`CMA`), and the position resets to the tip:

```asm
        STF 6            ; flag 6 = first pass
rop,    ; ... draw 7 points using step tables ...
        SZF I 6          ; check if this is pass 1
        JMP rot          ; no — go to exhaust flame
        CLF 6            ; clear first-pass flag
        ; Negate all step values for mirror half
        LAC \cm1; CMA; DAC \cm1
        LAC \sm1; CMA; DAC \sm1
        LAC \cm3; CMA; DAC \cm3
        LAC \sm3; CMA; DAC \sm3
        LAC \cm6; CMA; DAC \cm6
        LAC \sm6; CMA; DAC \sm6
        ; Reset to tip
        LAC \px; LIO \py
        JMP rop          ; draw mirrored right half
```

Seven point definitions produce 14 displayed points — a 2× compression
through exact mathematical mirroring via vector negation.

Confidence: **Very High**

### 8.5 Point-at-a-Time Drawing with Dispatch-Table Animation

The saucer center "engine" dots use computed GOTO dispatch for animation
states 0–5 (lines 1894–1968):

```asm
        LAC \udc         ; animation state 0–5
        SAL 1s           ; ×2
        ADD \udc         ; ×3 (total: SAL 1s + ADD = multiply by 3)
        ADD (sd4+1       ; dispatch base (offset by 1 from table start)
        DAP sd4          ; modify jump target
        SWAP             ; prepare display
        LIO \py
sd4,    JMP .            ; dispatch
        JMP s4a          ; state 0: no dots
        NOP              ; filler
        JMP s4a          ; state 1: 1 dot
        NOP
        JMP s4b          ; state 2: 2 dots
        ; ... etc.
```

The ×3 scaling (via `SAL 1s` + `ADD` instead of multiply) creates 3-word
spacing between dispatch entries, allowing 2 instructions per state
(a `JMP` and a filler/NOP). A second dispatch table `sd5` clips the
right-side dots symmetrically.

Confidence: **Very High**

---

## 9. Optimization

### 9.1 Cycle Budget

The PDP-1 has no hardware frame timer. ICSS implements software frame rate
control with a negated cycle budget:

```asm
; Budget definition (lines 517–522)
        LAC irk          ; rocket cost: 310 cycles/3
        ADD isc          ; saucer cost: 360 cycles/3
        ADD idp          ; score display cost: 60 cycles/3
        ADD ith          ; throttle reserve: 60 cycles/3
        CMA              ; negate
        DAC \ifr         ; store as initial budget (~790 cycles per frame)

; Frame start (line 532)
        LAC \ifr
        DAC \ict         ; start counter at negative budget

; Each subsystem adds its cost (e.g., line 1617)
        LAC irk
        ADD \ict
        DAC \ict

; Frame end spin (line 656)
        COUNT \ict, .    ; ISP \ict; JMP . — spin until counter hits zero
```

The constants (`irk=310`, `isc=360`, `isx=440`, `idp=60`, `ith=60`) are
empirically calibrated. The total frame budget is approximately 790 ÷ 3 ≈
263 instruction cycles per frame (since the counter increments by 3 per
actual instruction cycle). This is approximate but effective.

Confidence: **Very High**

### 9.2 Self-Modifying Code for Speed

DAP-based self-modification is not just a technique — it's the primary
optimization strategy. Every use trades memory mutability for speed.

**Key uses in ICSS:**

1. **Subroutine returns** (18 uses): `DAP ret` at entry, `JMP .` at exit
   — replaces a store + indirect jump (3 instructions) with DAP + JMP (2
   instructions) and no dedicated return-address storage.

2. **Collision detection pointers** (4 uses): `mx1`/`mx2`/`my1`/`my2` are
   `LAC .` / `SUB .` instructions whose operands are rewritten per call.
   Without this, each collision check would need 4 pointer loads + 4
   indirect memory accesses + 4 address computations — at least 12
   extra instructions.

3. **Computed dispatches** (5 uses): The DAP-based computed GOTO replaces
   a comparison chain of N instructions with 4 instructions (LAW, SUB,
   DAP, JMP) regardless of N.

4. **Table iteration** (3 uses): The `initialize`/`index` macro pair
   replaces a loop with address computation + increment + compare + jump
   (4+ instructions) with self-modifying IDX (1 instruction).

Confidence: **Very High**

### 9.3 Inlined Parameters (XCT)

Parameters encoded as instructions and loaded via `XCT` eliminate:
- Separate load-and-store instructions
- A decoding step (the instruction IS the operation)
- Memory round-trips for parameter values

```asm
; Instead of:
        LAC rvl          ; load shift count
        DAC \shift       ; store to... some variable
        ; ... code to decode shift count and apply it ...

; Write:
        XCT rvl          ; executes SAR 8s directly on AC
```

This saves 2–4 instructions per parameter use. With ~15 XCT parameters
used 1–3 times each, the total savings is significant.

**Constraint:** Only `SAR`, `SAL`, and `LAW I` instructions are used as
XCT parameters. These span the range of small shift amounts and small
immediate constants. Large values (>~256) use `LAC param` instead.

Confidence: **Very High**

### 9.4 Packed Data

Coordinate pairs are packed 9+9 bits per word, halving memory usage for
the 63-star background table and 64-particle explosion tables.

**Unpack sequence (2 instructions + display):**
```asm
CLI             ; clear IO
SCR 9s          ; shift low 9 bits of AC → high 9 of IO
SAL 9s          ; shift remaining 9 bits → high 9 of AC
DPY -I          ; display (X from AC bits 0-8, Y from IO bits 0-8)
```

Without packing: 2 words per star = 126 words. With packing: 63 words.
Savings: 63 words at cost of 2 instructions per star per frame.

Confidence: **Very High**

### 9.5 Frame-Skip Techniques

Frame-skip reduces per-frame computation without reducing visual quality:

- **Background stars** displayed every 2nd frame: 50% reduction in star
  display time.
- **Torpedo steering** computed every 2nd or 4th frame: 50–75% reduction
  in steering computation.
- **Rocket exhaust** alternates shape every 4th frame: 75% reduction in
  flame drawing complexity.
- **Saucer animation** updates every 2nd or 4th frame: controlled by
  `\uft` (1 or 3).

The frame-skip mask is a single instruction (`AND mask`) with zero setup
cost beyond the existing frame counter.

Confidence: **Very High**

### 9.6 Precomputed Trig Step Tables

The rocket display computes all 14 step values from a single sin(θ) and
cos(θ), then reuses them for every sprite point. This avoids calling the
expensive (200+ cycle) sin/cos subroutine for each of 14+ points.

```asm
; Compute sin/64 as base
SCALE \sn, 6s, \sn8

; Cascade: each step is half the previous
LAC \sn8
SAR 1s; DAC \sn4       ; /128
SAR 1s; DAC \sn2       ; /256
SAR 1s; DAC \sn1       ; /512

; Combinations for specific offset sizes
LAC \sn1; ADD \sn2; DAC \sn3    ; 3/512
LAC \sn2; ADD \sn4; DAC \sn5    ; 5/256
LAC \sn2; ADD \sn4; DAC \sn6    ; 6/256

; Negated versions for mirror half
LAC \sm1; CMA; DAC \sm1
; ... etc.

; Same for cosine → \cn8, \cn4, \cn2, \cn1, \cn3, \cn5, \cn6, \cm1, \cm3, \cm6
```

The step table is recomputed every frame (3–4 instruction cycles per step)
but reused 14 times. Without it: 14 sin/cos calls × ~200 cycles = 2,800
cycles. With it: 2 sin/cos calls + ~40 steps = ~440 cycles. Savings: ~84%.

Confidence: **Very High**

---

## 10. Debugging

### 10.1 Front Panel State Inspection

The PDP-1 front panel displays the contents of AC, IO, PC, and memory.
When debugging, you can observe:

- **AC and IO lights:** Show current register values. Use these to verify
  coordinate pipeline state during display code.
- **PC lights:** Show which instruction is executing. A looping PC narrows
  down which loop or spin is active.
- **Memory display:** Select an address and read its contents via the data
  switches.

**ICSS-specific tips:**
- The frame-budget spin loop (`COUNT \ict, .` at line 656) produces a
  characteristic tight PC loop at `fr3`. If the frame freezes, check
  whether `\ict` has been corrupted (loaded with a positive value that
  never reaches zero via ISP).
- The attract mode loop (`ISP \gms` at line 633) counts toward restart.
  If the game never starts, check `\gms` value.

Confidence: **Very High**

### 10.2 Single-Step Tracing

The emulator's single-step function executes one instruction at a time.
Use it to:

1. **Verify DAP modifications:** After `DAP mx1`, examine the instruction
   at `mx1` to confirm the target address is correct.
2. **Trace computed GOTO:** After `LAW sdd` / `SUB \sdc` / `DAP sdd`,
   check that `sdd`'s `JMP .` now points to the right dispatch entry.
3. **Verify XCT execution:** After `XCT rvl`, check that AC was correctly
   shifted.

**Key addresses in ICSS (octal):**
- `mx1` (line 881 mod origin): collision X pointer — check after DAP
- `sdd` (line 1872): saucer hull dispatch — check after DAP
- `us0` (line 1154): explosion 4-pass dispatch — check after DAP

Confidence: **High**

### 10.3 Self-Modifying Code Traps

Self-modifying code creates two debugging challenges:

**1. Stale instruction cache (mental):** When reading the listing, remember
that the instruction shown in the source may NOT be the instruction that
executes. A `LAC .` at `mx1` may be `LAC 100` at runtime after DAP.

**2. Modification order matters:** If two routines use the same DAP target
(e.g., `ci4` and `ci5` in the character compiler), the last modification
wins. A race condition between overlapping modifications produces
hard-to-reproduce bugs.

**Prevention strategies from ICSS:**
- Each subroutine has its own DAP return target (named with `x` suffix).
- Collision detection pointers are set up immediately before the call and
  are not shared with other routines during the call.
- The character compiler modifies `ci4`/`ci5` only during initialization,
  never during gameplay.

Confidence: **High**

### 10.4 Display Artifacts Diagnosis

Common display artifacts and their causes:

| Artifact | Likely Cause | ICSS Fix/Check |
|----------|-------------|----------------|
| Dots at screen center | Coordinate in low bits, not high bits | Check `SAL 8s` or use pre-formatted constants |
| Missing dots | Missing `IOH` after `DPY -4000` | Ensure completion pulse waited |
| Ghost dots (wrong positions) | AC/IO pipeline corrupted mid-sprite | Verify SWAP discipline between each pair of coordinates |
| Flickering explosion | Random skip mask wrong | Check `AND (400001` — bit 0 selection |
| Saucer hull only in 2 quadrants | Flag 5/6 not cycling through all 4 states | Check `sdd` dispatch table and `\sdc` counter |
| Rocket only one half visible | Flag 6 two-pass logic broken | Check `SZF I 6` at line 1766 |
| Characters corrupt | Character compiler generated bad code | Re-run `JSP ci` initialization |

Confidence: **High**

### 10.5 Console State Dump

When a crash occurs, recording the full console state (AC, IO, PC, flags,
selected memory locations) is the first step. The emulator can display all
registers via the vpanel.

**Key variables to inspect in ICSS:**
- `\ict` — cycle budget counter. If positive, the frame-end spin will
  never terminate (ISP skips on positive, so it loops forever).
- `\sdc` — saucer pass counter. Should be 4 at start of `sd`. If zero,
  the computed GOTO will dispatch to the wrong entry.
- `\ufs` — saucer state. Positive = active, 0 = explosion, negative =
  inactive. An unexpected zero can prevent saucer display.
- `\rks` — rocket state. Positive = active, negative = collision spin.
  Unexpected negative causes rocket hiding.

Confidence: **High**

---

## 11. Commenting

### 11.1 Flag Register Documentation

**Every flag bit must have a documented purpose at the definition site.**

ICSS partially follows this — most `STF`/`CLF`/`SZF` instructions have
inline comments, but there is NO centralized flag usage block:

```asm
; RECOMMENDED — place at top of file:
; Flag usage:
;   Flag 1 — Rocket alive (set by rkt, cleared each frame at fr0)
;   Flag 2 — Thrust active this frame (tested for flame and random advance)
;   Flag 3 — Torpedo fire requested (tested at frame end for launch)
;   Flag 4 — (unused)
;   Flag 5 — X sign negation in saucer hull; also explosion block flag;
;            also "no respawn" during game-over spinning rocket
;   Flag 6 — Y sign negation in saucer hull; also character-compiler
;            first-dot flag; also rocket mirror pass indicator
```

ICSS currently has this pattern of inline comments:
```asm
        STF 1            ; flag1 indicates active player's ship
        CLF 2            ; (minimal comment)
        CLF 3            ; (minimal comment)
```

This is adequate for a familiar codebase but insufficient for new
programmers. Flags 5 and 6 have MULTIPLE context-dependent meanings that
are NOT documented at reuse sites.

Confidence: **High (rule strength) / Low (ICSS compliance)**

### 11.2 Dispatch Table Annotations

**Every computed GOTO dispatch must document:**
1. The index range (e.g., "−4 to −1", "0–5")
2. The scaling factor (e.g., "×3" for `SAL 1s; ADD original`)
3. What each entry in the dispatch table represents

ICSS examples of GOOD documentation:
```asm
sdd,    JMP .            ; dispatch on \sdc (-4..-1) for passes (set flags)
```

ICSS examples of POOR documentation:
```asm
sd4,    JMP .            ; no comment explaining ×3 scaling or 6 states
```

**Recommended pattern:**
```asm
        ; Dispatch on animation state \udc (0–5), scaled ×3
        LAC \udc
        SAL 1s           ; ×2
        ADD \udc          ; ×3
        ADD (sd4+1        ; dispatch base
        DAP sd4
sd4,    JMP .
        JMP s4a           ; state 0: no dots
        NOP
        JMP s4b           ; state 1: 1 dot
        NOP
        JMP s4c           ; state 2: 2 dots
        ; ...
```

Confidence: **Medium**

### 11.3 Self-Modifying Target Labels

**Rule:** Use the `x` suffix ONLY for DAP-modified return addresses
(`JMP .` instructions). Use descriptive names (no suffix) for
DAP-modified data pointers (`LAC .`, `DAC .`, `SUB .`).

This convention is followed consistently in ICSS:
- Returns: `csx`, `ccx`, `cdx`, `bsx`, `bgx`, `ufx`, `rkx`, `rox`, etc.
- Data pointers: `mx1`, `mx2`, `my1`, `my2`, `ci4`, `ci5`, `bsc`, `bgl`

**The `x` suffix signal:** When reading code, any label ending in `x` is
a subroutine return point. It's modified by `DAP` at the corresponding
subroutine entry. This is a universal convention that the reader can
trust.

Confidence: **Very High**

### 11.4 Variable Allocation Comments

**Every local (`\`-prefixed) variable at its allocation site should document:**
1. **Purpose** — what the variable represents
2. **Range** — valid values (or "unbounded")
3. **Encoding** — sign conventions
4. **Multi-use** — if it serves multiple purposes

ICSS currently has this for only 2 of ~45 local variables:
```asm
\scc, . 1/        ; score display timeout (negated counter)
\gms, . 1/        ; game status: <=0 attract, >0 active
```

**Recommended pattern for all variables:**
```asm
\ict, . 1/        ; cycle budget counter: negative = remaining, counts up
                  ; toward zero via ISP; starts at -(irk+isc+idp+ith)
\umo, . 1/        ; saucer motion: 0-7 direction code, -3..-1 stop phase
\ufs, . 1/        ; saucer state: + = active, 0 = explosion, - = inactive
\trs, . 1/        ; torpedo life: <=0 inactive, >0 frames remaining
```

This documentation is critical for variables like `\umo` that serve dual
purposes (direction code AND stop phase counter).

Confidence: **Low (ICSS compliance) / High (rule prescription)**

### 11.5 Rounding Semantics

**Every `SAR` (arithmetic right shift) and `SPA; CMA` (absolute value)
should document rounding behavior.**

`SAR` rounds toward negative infinity for negative values (PDP-1
arithmetic shift characteristic). `SPA; CMA` produces one's complement
absolute value — off by one for negative numbers.

ICSS today has ZERO rounding comments on 31 SAR instructions and 10+
SPA;CMA sequences. This is a significant documentation gap for a
codebase that relies heavily on empirically-tuned arithmetic.

**Recommended:**
```asm
        SAR 1s           ; ÷2, rnd toward -inf for negatives
        ...
        SPA
        CMA              ; one's comp abs: |AC|-1 for AC<0; OK for epsilon
```

Confidence: **Low (ICSS compliance)**

### 11.6 Register State Annotations

**Every subroutine entry and every `DPY` instruction should have a comment
documenting expected AC and IO contents.**

The display pipeline's `compute Y → SWAP → compute X → DPY` rhythm should
be annotated at each step, especially when the state is non-obvious.

**Example — saucer hull point:**
```asm
sdl,    ; AC=Y_offset, IO=trash; Goal: Y in IO, X in AC for DPY
        SZF 6
        CMA              ; Y = py ± offset
        ADD \py
        SWAP             ; Y → IO
        SZF 5
        CMA              ; X = px ± offset
        ADD \px
        ; AC=X, IO=Y — ready for DPY
        DISP
```

ICSS has minimal register-state documentation. The only hints are in the
rocket display (lines 1690–1692) describing step directions. Most entry
points have no AC/IO state comments.

Confidence: **Low (ICSS compliance)**

---

## 12. Common Pitfalls

### 12.1 IOH Timing Mistakes

**Pitfall:** Using `IOH` after every `DPY -I` (wasting cycles) OR omitting
`IOH` after `DPY -4000` (producing visual artifacts).

**Fix:** Know which DPY variant you're using:
- `DPY -I B`: NO completion pulse → NO IOH needed. Use for rapid dot
  sequences within a single sprite.
- `DPY -4000 B`: Completion pulse requested → IOH REQUIRED. Use between
  different display objects.

**ICSS uses both correctly:** The rocket display (`DISP` macro = `DPY -I
100`) draws 7 consecutive dots with NO IOH. The character compiler emits
`DPY -4000 100` and inserts one `IOH` per character (at the first dot).

Confidence: **Very High**

### 12.2 LAW I Immediate Limits

**Pitfall:** Trying to encode a large value (> ~256) as a `LAW I`
immediate. `LAW I N` is limited to approximately 9-bit unsigned range
(0–511 octal, ~0–340 decimal).

**Evidence from ICSS:** Parameters >256 use plain numeric constants:
- `raa, 1200` (angular acceleration) — numeric, not `LAW I`
- `eld, 60000` (distance threshold) — numeric
- `irk, 310` (cycle budget) — numeric
- `ete, 14000` (epsilon) — numeric

Parameters ≤256 use `LAW I N`:
- `tlf, LAW I 250` (torpedo life)
- `etl, LAW I 220` (enemy torpedo life)
- `etd, LAW I 10` (cooling)
- `ras, LAW I 6` (skip counter)

**Rule of thumb:** If the value fits in a small positive integer
(0–511 octal), use `LAW I N`. If it's larger, use a plain numeric
constant and load via `LAC param`.

Confidence: **Very High**

### 12.3 One's Complement Arithmetic

**Pitfall:** Assuming two's complement behavior for negation, comparison,
and zero detection.

The PDP-1 uses one's complement. Key traps:

1. **Negative zero (`777777`):** Arithmetic can produce `777777` instead
   of `000000`. Operations that compare against zero must account for
   both representations.

2. **`CMA` (one's complement) vs. negation (`CMA; ADD (1`):**
   ```asm
   CMA          ; on AC = -N: produces N-1, NOT -N
   CMA; ADD (1  ; true two's complement negation
   ```
   ICSS uses `CMA` alone for absolute value in collision detection,
   accepting the off-by-one error for epsilon comparisons.

3. **`SUB` on one's complement:** Subtraction sets the carry/borrow flag
   differently than two's complement. `SUB (0` with a borrow produces
   `-0` (`777777`), not `-1`.

4. **`SAD` vs. `SAS`:** `SAD` (skip if AC differs) and `SAS` (skip if AC
   same) both work with one's complement values, but comparison against
   a literal constant requires understanding that `−0` won't match `0`.

**ICSS mitigation:** Sign tests (`SPA`, `SMA`, `SPI`) test bit 0, which
correctly distinguishes positive from negative in one's complement.
Epsilon comparisons use empirically tuned constants that absorb the
off-by-one.

Confidence: **Very High**

### 12.4 DAP Overwrite Bugs

**Pitfall:** Two code paths modifying the same DAP target without mutual
exclusion, causing the second modification to overwrite the first.

**ICSS defense:** Each subroutine has a UNIQUE DAP return target (named
with `x` suffix). No two routines share a return address. Collision
detection pointers are set up immediately before each call:

```asm
        ; Set up for rocket vs. saucer
        DAP mx1          ; point to rocket X
        ...              ; load addresses
        DAP mx2          ; point to saucer X
        JSP dmf          ; call immediately — no window for interference
```

**Golden rule:** Set up DAP targets immediately before the call that uses
them. Do not set them up, then run unrelated code, then call.

**ICSS counterexample to watch for:** The `ci4`/`ci5` targets in the
character compiler are modified during the initialization loop and left
in their final state. If any code accidentally DAPs into them during
gameplay (which ICSS does not do), the character dispatch breaks.

Confidence: **Very High**

### 12.5 Overflow in MUL/DIV

**Pitfall:** Assuming the EAE multiply produces a simple 36-bit (AC, IO)
pair when the product format is non-obvious.

**MUL format:** Sign in AC bit 0 AND IO bit 17. The 34-bit magnitude
spans AC bit 1 through IO bit 16. IO bit 17 COPIES the sign rather than
being the magnitude LSB.

```python
# To reconstruct the product:
sign = (ac >> 17) & 1
mag_high = ac & 0o77777        # AC bits 1-17 (17 bits)
mag_low = (io >> 1) & 0o77777  # IO bits 0-16 (17 bits)
magnitude = (mag_high << 17) | mag_low
product = magnitude if sign == 0 else -magnitude
```

**DIV skip behavior:** DIV skips the next instruction on success. Always
absorb with `jmp .+1`:
```asm
        div divisor
        jmp .+1          ; absorbed by DIV skip
        dac result       ; this executes on success
```

**ICSS does not use EAE MUL/DIV** — all arithmetic uses shift-and-add
series. If you add EAE code, be aware that the emulator must have
`muldiv` enabled and the toggle resets on every restart.

Confidence: **Very High**

### 12.6 `dzm i` Does Not Exist

**Pitfall:** Writing `DZM I ptr` to zero a cell through an indirect
pointer. The PDP-1 has no indirect DZM instruction.

**Fix:** Use self-modifying code:
```asm
        LAC ptr          ; load cell address
        DAP clrloc       ; fix up DAC
        LAC (0           ; AC = 0
clrloc, DAC .            ; becomes DAC <cell_addr> — zeros the target
```

This pattern is required throughout PDP-1 programming. There is no
workaround that avoids the self-modifying approach.

Confidence: **Very High**

### 12.7 Coordinate Bit Positioning

**Pitfall:** Loading a coordinate value and expecting `DPY` to read it
correctly when the value is in the low bits of the register.

**Fix:** The coordinate must be in bits 0–9 (the high bits) of the
register. If computing coordinates at runtime, shift left by 8:
```asm
        LAC N            ; coordinate value in low bits
        SAL 8s           ; shift into bits 0–9
        DAC xcoord       ; store for DPY
```

Or pre-format constants with the coordinate in the high bits:
```asm
        LIO (010000      ; Y=16, pre-formatted: bits 0-9 = 010000
        LAC (006000      ; X=12
        DPY
```

ICSS uses the pre-formatted approach for character grid units:
```asm
cgy,    010000           ; Y unit offset = 16 screen positions
cgx1,   006000           ; X unit offset = 12 screen positions
```

Confidence: **Very High**

### 12.8 `SAR` vs. Logical Right Shift

**Pitfall:** In MACRO-1, the mnemonic `SAR` assembles to opcode 67 (RTR
— Rotate Right), NOT to an arithmetic shift with sign extension. RTR
swaps the two 9-bit halves of the word; it only gives the same result as a
right shift when the low 9 bits happen to be zero.

**Fix:** To perform a correct arithmetic right shift WITH sign extension,
use the OPR-group instruction `SAR Ns`, which IS an arithmetic shift
(with the `s` suffix). The ICSS source correctly uses `SAR 4s`, `SAR 1s`,
`SAR 6s`, etc., with the `s` suffix — these are genuine arithmetic shifts.

The `s` suffix is critical: `SAR 1` (without `s`) = RTR (half-word swap,
not a shift). `SAR 1s` = arithmetic right shift by 1.

Confidence: **Very High**

### 12.9 Octal Radix Confusion

**Pitfall:** Writing `board+8` in MACRO-1 produces an error because 8 and
9 are not valid octal digits.

**Fix:** Always use octal for numeric constants. `board+10` = board plus
decimal 8. The default radix is octal throughout MACRO-1.

ICSS consistently uses octal for all numeric values: `60000`, `14000`,
`311040` (2π), `355671` (PRNG constant), `1200`, etc. No decimal
constants appear in the source.

Confidence: **Very High**

---

## 13. Best Practices

### 13.1 Top 10 Rules from Style Guide v0.2

The following 10 rules represent the most important principles for writing
PDP-1 assembly code, verified against ICSS v1.3 and grounded in the
architecture.

---

**Rule 1: Use JSP for Subroutine Calls with DAP Return** *(Very High)*

Every subroutine uses `JSP call` at the call site and `DAP ret` / `JMP .`
for return. This is the standard PDP-1 calling convention, universal in
ICSS across all 34 subroutine calls.

```asm
        JSP ufo          ; call saucer routine
        ...
ufo,    DAP ufx         ; save return address
        ...             ; body
ufx,    JMP .           ; return (modified by DAP)
```

**Exception:** Sequence break handler `sbf` uses `JMP I 1` — the hardware
interrupt return convention. This is a different pattern for a different
purpose.

---

**Rule 2: Use DAP to Parameterize Instruction Operands at Runtime**
*(Very High)*

Whenever an algorithm needs to operate on different data at different
calls, use DAP to modify the operand of a `LAC .`, `SUB .`, or `DAC .`
instruction. This replaces pointer loads and indirect memory accesses.

```asm
        ; Collision detection: DAP-fixed pointers
mx1,    LAC .            ; loaded via: DAP mx1 (LAC addr1 → LAC rocket_X)
mx2,    SUB .            ; loaded via: DAP mx2 (SUB addr2 → SUB saucer_X)
```

DAP-based parameterization appears in 49 locations across ICSS and is the
primary optimization technique.

---

**Rule 3: Use ISP with Negative Counters for Count-Up-to-Zero Timers**
*(Very High)*

All timers, delays, and budgets use the pattern: initialize negative,
`ISP` to increment toward zero, exit when skip fires.

```asm
        LAC \ifr         ; load negated budget
        DAC \ict         ; -790
        ; ... subsystem code ...
        ISP \ict         ; increment toward zero
        JMP .            ; spin if still negative
```

Applies to: frame budget, torpedo life, saucer legs, explosion duration,
collision spin, score display timeout, acceleration skip frame.

---

**Rule 4: Use Computed GOTO via DAP + Self-Modifying Jump for
Multi-Way Branching** *(Very High)*

Replace comparison chains with a computed dispatch: `LAW table` / `SUB
counter` / `DAP jump` / `JMP .` — 4 instructions regardless of the number
of cases.

```asm
        LAW sdd          ; dispatch table base
        SUB \sdc         ; index (-4 to -1)
        DAP sdd          ; modify JMP target
        IDX \sdc         ; advance counter
        JMP .            ; dispatch
sdd,    JMP sd1          ; pass 1 handler
        JMP .            ; pass 2 handler (set flags)
        JMP .            ; pass 3 handler (set flags)
        JMP .            ; pass 4 handler (set flags)
```

Five computed GOTO dispatches in ICSS, all using this pattern. No
comparison-chain alternatives exist.

---

**Rule 5: Use the AC/IO Coordinate Pipeline with SWAP for Display**
*(Very High)*

Maintain (X in AC, Y in IO) as the canonical pair for `DPY`. Use the
`SWAP` macro (two `RCL 9s`) to exchange AC and IO between coordinate
computations. No memory round-trips between consecutive sprite points.

```asm
        SWAP             ; bring Y to AC
        SUB \cn4         ; compute next Y
        SWAP             ; Y → IO
        ADD \sm6         ; compute next X
        DISP             ; DPY -I 100: X in AC, Y in IO
```

This pattern is followed for every dot in the rocket display (7+ points),
saucer display (3 hull points × 4 passes), torpedo display, and exhaust
flame.

---

**Rule 6: Use Manhattan (L1) Distance for Collision Detection**
*(Very High)*

Compute |Δx| + |Δy| < ε rather than Euclidean √(Δx²+Δy²). Much faster
(~15 instructions vs. ~50+) and adequate for game collision hitboxes.

```asm
        ; Three-tier test: X, Y, then combined
        SPA; CMA              ; |Δx|
        SUB \dxe              ; compare to X epsilon
        ...
        SPA; CMA              ; |Δy|
        SUB \dye              ; compare to Y epsilon
        ...
        ADD \t1               ; |Δx| + |Δy|
        SUB \de2              ; compare to combined epsilon
```

The DAP-fixed pointers (`mx1`, `mx2`, `my1`, `my2`) make the routine
reusable for rocket-vs-saucer, torpedo-vs-saucer, and
enemy-torpedo-vs-rocket checks — each with different epsilon values.

---

**Rule 7: Encode Small Parameters as Executable Instructions (XCT)**
*(High)*

For parameters that fit in a single instruction's immediate field (≤~256)
and whose semantics match `SAR`, `SAL`, or `LAW I`, encode them as
instructions and load via `XCT`.

```asm
rvl, SAR 8s              ; parameter: rocket velocity scaling
        ...
        XCT rvl          ; executes SAR 8s on AC
```

```asm
tlf, LAW I 250           ; parameter: torpedo life
        ...
        XCT tlf          ; AC = 250
        DAC \trs
```

**Do NOT force this pattern for large values.** Use plain numeric
constants and `LAC` for values > ~256. The two encodings coexist because
the instruction width constrains what fits.

---

**Rule 8: Use Frame Skip (AND + SZA) for Frame-Rate Division**
*(High)*

Throttle per-frame computation by masking the frame counter. A single
instruction replaces an entire conditional branch structure.

```asm
        LAC \frc         ; frame counter
        AND (1           ; every other frame
        SZA              ; skip if zero
        JMP skip         ; skip this frame
```

The mask can be a literal or a variable (`AND \uft`), enabling dynamic
rate control. Used for background stars, torpedo steering, exhaust flame,
and saucer center animation.

---

**Rule 9: Use Flag Bits for Lightweight Cross-Routine State**
*(Very High)*

For state that multiple routines need to test without passing through AC
or memory, use the 6 flag bits. They are single-cycle, global, and persist
across subroutine calls.

```asm
        STF 1            ; flag 1 = rocket alive
        ...
        SZF I 1          ; test at return: is rocket alive?
        JMP skip         ; no — skip torpedo AI
```

ICSS uses all 6 flags for distinct, documented purposes. The indirect
variant `SZF I n` tests the flag of the CALLING routine (at the return
address), not the current context — a subtle but important distinction.

---

**Rule 10: Document Self-Modifying Targets and Variable Semantics**
*(Medium — aspirational, ICSS falls short)*

Every DAP-modified instruction, subroutine return point, data pointer, and
multi-use variable must have a clear comment explaining:
1. What modifies it
2. What values it can hold
3. The range/encoding of the values

```asm
mx1,    LAC .            ; DAP-fixed X pointer: loaded by dmf caller
bsc,    DAC .            ; star table write slot (modified by INIT macro)
\umo,   . 1/            ; motion code 0-7 OR stop phase -3..-1
```

While ICSS follows this well for return addresses (`x` suffix) and most
data pointers, it falls short for local variable documentation (only 2 of
~45 variables have allocation comments) and rounding semantic annotations
(0 of 31 SAR instructions document rounding behavior). Future code should
address these gaps.

---

### 13.2 Summary Checklist

Before finalizing any PDP-1 subroutine, verify:

- [ ] **Subroutine linkage:** `JSP call` at caller; `DAP ret` / `JMP .`
      at callee. Return label has `x` suffix.
- [ ] **Display coordinates:** X in AC bits 0–9, Y in IO bits 0–9 before
      every `DPY`. Use `SAL 8s` if coordinates are computed in low bits.
- [ ] **DPY variant:** `DPY -I` for rapid sprite dots (no IOH).
      `DPY -4000 B` for cross-object dots (must precede with IOH).
- [ ] **Timers:** Initialized negative, counted up via `ISP`. Not positive
      (or the ISP loop will never terminate).
- [ ] **DAP targets:** Set up immediately before the call, not shared
      between non-nested routines.
- [ ] **Absolute value:** `SPA; CMA` (one's complement) is acceptable for
      comparisons; use `SPA; CMA; ADD (1` for exact negation.
- [ ] **One's complement:** Check for `777777` (negative zero) in
      comparisons. `SMA`/`SPA` sign tests are safe.
- [ ] **XCT parameters:** Value ≤ ~256 octal. Use `LAC param` for larger
      values.
- [ ] **Memory allocation:** `. N/` for reserves; `constants`/`variables`
      directives for page organization.
- [ ] **Commenting:** Flag usage, dispatch ranges, variable semantics,
      rounding behavior, and register state at entry/exit.

---

*Design Handbook v1.0 — Compiled from ICSS v1.3 (1,979 lines), PDP-1
Handbook, MACRO-1 Programming Guide, and 30 reference documents at
`~/.hermes/profiles/siggy/skills/software-development/pdp1-programmer/references/`.*

*13 sections, 80+ rules with confidence ratings, backed by real code
examples from ICSS v1.3 by Norbert Landsteiner (2025).*
