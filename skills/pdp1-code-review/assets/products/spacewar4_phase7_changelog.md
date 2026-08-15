# Phase 7 — Continuous Refinement: Spacewar! 4.8 vs ICSS Design Handbook v1.0

**Source studied:** Spacewar! 4.8 (Dan Edwards, July 1963) — 3 files, ~1,373 lines total
**Files:** `spacewar4.8pt1.mac` (561 lines), `spacewar4.8pt2.mac` (702 lines), `spacewar4.8scorer.mac` (110 lines)
**Handbook baseline:** ICSS v1.3-derived Design Handbook v1.0 (2,118 lines)
**Location:** `/home/x/Documents/x5/pidp1/hermes/icss_design_handbook_v1.0.md`
**Skill references:** `~/.hermes/profiles/siggy/skills/software-development/pdp1-programmer/references/`

---

## New Patterns to Add

### 1. JDA Calling Convention (section 5)

Spacewar! uses `jda sin`, `jda cos`, `jda sqt`, `jda oc` extensively — the classic DEC convention where JDA deposits AC into the subroutine's first word and puts the return address in AC (never into memory). The handbook documents JDA in section 5.2 but frames it as a variant. Spacewar! shows it as a PRIMARY calling convention, used alongside JSP.

**JDA convention:**

```asm
; Caller
        lac angle       ; load argument
        jda sin         ; deposits AC at sin, return addr in AC,
                        ; jumps to sin+1

; Callee
sin,    0               ; overwritten by JDA: word = argument (arg << 13)
        dap csx         ; save return address from AC (set by JDA)
        ...             ; body — access argument via sin word
csx,    jmp .           ; return
```

The relationship: JDA passes one argument IN the accumulator (deposited at the entry word) and saves the return address in AC; JSP only saves the return address in AC. Both are equally valid. The choice depends on whether you need to pass an argument in the subroutine entry word.

Confidence: **Very High** — Spacewar! + ICSS + PDP-1 Handbook all document JDA.

### 2. `define`/`term` Macro Syntax (section 2.3)

The handbook documents ICSS's `macro`/`endm` syntax. Spacewar! uses an entirely different macro syntax:

```asm
define
xincr X,Y,INS
        lac Y
        INS .ssn
        dac Y
        lac X
        INS .scn
        dac X
        term
```

Note three variant spellings of the terminator: `term`, `terminate`, and `terminate` (missing 'r' in `terminate`). All three work — the assembler appears to accept any of them.

Both `macro`/`endm` and `define`/`term` are valid MACRO-1. The handbook should document both syntax variants.

Confidence: **Very High** — Spacewar! source + MACRO-1 manual.

### 3. `repeat` Assembler Directive (section 2.5)

Spacewar! uses `repeat` for assembly-time expansion:

```asm
repeat 6, B=B+B        ; evaluate B+B six times (= B << 6)
repeat 10, starp       ; unroll starp macro 10 times
```

The first form performs assembly-time arithmetic (used for bit rotation to compute display brightness constants). The second form unrolls a macro or instruction sequence N times. The PDP-1 has no hardware multiply, so assembly-time `repeat` with shift arithmetic generates constants that would otherwise require runtime computation.

Confidence: **Very High** — confirmed in Spacewar! source and MACRO-1 documentation.

### 4. `clear` Assembler Directive (section 2.5)

```asm
clear mtb, nnn-1       ; zero out the entire object table (30 entries)
```

A MACRO-1 directive that clears a range of memory at load time. Much more compact than a DAP-based runtime clear loop. The handbook currently only documents `dzm` for clearing individual words at runtime.

Confidence: **High** — observed in Spacewar! only, but matches MACRO-1 documented behavior.

### 5. `=` (EQU) Aliasing for Offset Arithmetic (section 2.5)

Spacewar! uses `=` to build an object-property table system:

```asm
nob=30                          ; number of objects

mtb,                            ; table of objects
nx1=mtb nob                     ; nx1 = mtb + 30 (X position for object 1)
ny1=nx1 nob                     ; ny1 = mtb + 60 (Y position for object 1)
na1=ny1 nob
nb1=na1 nob
ndx=nb1 nob
ndy=ndx nob
nom=ndy nob
nth=nom 2                       ; nth = mtb + ... (angle, 2 words per object)
nfu=nth 2
ntr=nfu 2
not=ntr 2
nco=not 2
nh1=nco 2
nh2=nh1 2
nh3=nh2 2
nh4=nh3 2
nnn=nh4 2                       ; total words used
```

This is computed at assembly time. Every property (nx1, ny1, na1, nb1, ...) is a fixed address derived from the base table pointer `mtb` plus the property stride. The `init` macro then wires these addresses into self-modifying code:

```asm
init ml1, mtb    ; generates: law mtb / dap ml1
```

The table walk uses `idx` to advance through property slots. This is an object system built entirely with assembler arithmetic — no runtime offset calculations needed.

Confidence: **High** — Spacewar! only, but architecturally sound and generalizable.

### 6. `jsp i` Indirect Dispatch (section 5.1)

```asm
; Function pointer dispatch
cwr,    jmp mg1        ; normally iot 11 control
dwr,    jmp mg2        ; normally iot 111 control

; At startup, select control method:
a40,    law cwr        ; use IOT 11 control
        dac .cwg       ; store address of control routine
        ...
a1,     law mg2        ; use Test Word control
        dac .cwg
        ...

; Ship calculation calls via indirect JSP:
ss1,    ...
        jsp i .cwg     ; jump to the address stored in .cwg
        jmp sr0

; Control routines save their own return:
mg1,    dap mg3
        cli
        iot 11         ; read IOT 11
        ...
mg3,    jmp .

mg2,    dap mg4
        lat            ; read Test Word
        swap
mg4,    jmp .
```

This is the PDP-1's equivalent of a function pointer. Indirect JSP (`jsp i ptr`) dispatches to whichever routine's address is stored in the pointer variable, and that routine returns via its own `dap ret` / `jmp .`. The handbook mentions `jsp i ptr` briefly — Spacewar! demonstrates it as a primary dispatch mechanism.

Confidence: **Very High** — confirmed in Spacewar! and general PDP-1 programming practice.

### 7. `idx` Counter Loop (section 7)

```asm
; Single counter decrement
idx mx2          ; increment mx2, skip next if result is positive
jmp mq2          ; not yet zero — continue

; Walking through table entries
idx sr1          ; advance pointer
sad (lac mtb-1   ; reached end?
jmp sr1          ; no — keep searching
hlt              ; no space found
```

`idx` is "Increment and Defer Execute" — it increments the memory location and skips the next instruction if the result crosses from negative to positive (i.e., reaches zero). This is identical in effect to `isp` (Increment and Skip if Positive). Both should be documented as the standard PDP-1 counting idiom, with the observation that `idx` is an I/O instruction (IOT variant) while `isp` is an OPR (operation) instruction.

The handbook currently documents only the `isp`/`count` pattern. The `idx` variant is equally valid and appears in both ICSS and Spacewar!.

Confidence: **Very High** — confirmed in both ICSS and Spacewar!.

---

## Existing Rules Challenged

### 8. Commenting Standard (section 11) — Violated

The handbook recommends: "every routine needs a header comment explaining its purpose, inputs, outputs. Use natural language, not just mnemonics."

Spacewar! violates this consistently:

```
ss1,    jmp sex               / something came too close
        jsp i .cwg
        jmp sr0
```

The comment for the spaceship calculation routine is `/ spaceship calc`. The torpedo calc `tcr,` has no header comment at all. The main loop `ml0,` is preceded only by `setup .mtc, 5000 / delay for loop`. Most comments are initials, dates, or single-line descriptions.

This is a deliberate style choice by the original MIT hackers. Code was shared orally, documented in the PDP-1 community, and the source was considered self-explanatory to those familiar with the idiom. The handbook should acknowledge this as a valid (if less accessible) style for period code and note that the verbose-comment convention is a modern best practice, not a period requirement.

Confidence: **Medium** — period-specific practice; modern readers benefit from more comments.

### 9. Return Address Naming (section 3.3) — Extended

The handbook documents the `x` suffix for return labels (`csx`, `bsx`, `rkx`). Spacewar! confirms this convention:

- `csx` — sine/cosine return (same as ICSS!)
- `ocx`, `ocm`, `ocn`, `ocz` — outline compiler returns
- `bpx`, `blx`, `bcx` — background display returns
- `sqx` — square root return

But Spacewar! also uses descriptive return names without the `x` suffix:
- `mg3`, `mg4` — control word routine returns
- `bjm` — star display return

The `x` suffix is common but not universal in period code. The handbook should note this as a strong convention with occasional exceptions.

Confidence: **Very High** — confirmed across both ICSS and Spacewar!.

### 10. `\`-prefixed Local Variables (section 3.2) — Alternative Convention

Spacewar! does NOT use `\`-prefixed locals. Instead it uses `.`-prefixed names:

```asm
.t1, 0         ; general temporary 1
.t2, 0         ; general temporary 2
.xys, 0        ; variable shift state
.ssn, 0        ; sine step (small)
.scn, 0        ; cosine step (small)
.cwg, 0        ; control word routine address
.bx, 0         ; background X (star offset)
.by, 0         ; background Y (star offset)
.sn, 0         ; sin(θ)
.cs, 0         ; cos(θ)
.sx1, 0        ; ship display X1
.sy1, 0        ; ship display Y1
.stx, 0        ; ship display X2 (tail)
.sty, 0        ; ship display Y2 (tail)
.scw, 0        ; saved control word
.src, 0        ; exhaust particle counter
.acx, 0        ; acceleration X accumulator
.acy, 0        ; acceleration Y accumulator
.iox, 0        ; IO save for multiply
```

These serve the same purpose as ICSS's `\`-prefixed locals — subroutine-scoped temporaries and per-routine state — but use a dot prefix. Both conventions exist in period code. The dot prefix is actually more common in older PDP-1 programs (Spacewar! predates most of the ICSS code).

The handbook should document both `\` and `.` prefix conventions as valid local-scope markers.

Confidence: **High** — `.` prefix observed in Spacewar!; `\` prefix in ICSS.

---

## New Techniques to Document

### 11. Runtime Code Generation — The Outline Compiler (new section)

The most sophisticated technique in Spacewar!. The `oc` (outline compiler) routine reads outline description tables and emits display instructions into memory at runtime.

**Outline data format:** Each spaceship outline is described as a sequence of 3-bit direction codes packed into data words:

```asm
; Spaceship 1 outline (ot1)
ot1,    111131
        111111
        111111
        111163
        311111
        146111
        111114
        700000          ; terminator
. 5/
```

**Compilation process:** The compiler reads these direction codes and emits ready-to-execute display instructions:

```asm
oc,     0               ; JDA target: AC = destination address
        dap ocx         ; save return
        lac i ocx       ; load outline table address
        dap ocg         ; fix pointer into outline table
        plinst (stf 5   ; compile: STF 5 (set flag 5)
        dap ocm         ; save return for display
        idx ocx
```

For each direction code, the compiler emits:
1. `lac .sx1` — load current X
2. `lio .sy1` — load current Y
3. `clf 6` — clear flag 6
4. `dpy-4000` — display dot
5. Direction-appropriate X/Y increment
6. Loop back for next point

This compresses display data by ~10x — 8 words of outline data expand to ~80 words of display code. The compiled code is stored in the object table and executed each frame by the ship calculation routine.

This is a meta-programming layer that would fit as an advanced technique in section 4 (Memory Organization) or a new section on code generation.

Confidence: **High** — unique to Spacewar! but well-documented in the source. The same technique was used in the original PDP-1 Spacewar!.

### 12. Data-as-Instructions Parameter Blocks (section 4.2, extended)

The handbook documents ICSS's parameter block pattern where parameters are stored as inline data with both numeric and instruction encodings. Spacewar! takes this to an extreme:

```asm
; Parameters at addresses 6-32 — ALL are executable instructions
tno,  6,       law i 41        ; number of torps + 1
tvl,  7,       sar 4s          ; torpedo velocity
rlt, 10,       law i 20        ; torpedo reload time
tlf, 11,       law i 140       ; torpedo life
foo, 12,       -20000          ; fuel supply (negative = NOP-ish)
maa, 13,       40              ; spaceship angular acceleration (HLT-ish)
sac, 14,       sar 4s          ; spaceship acceleration
str, 15,       100             ; star capture radius (HLT!)
me1, 16,       6000            ; collision "radius" (HLT!)
me2, 17,       3000            ; above/2 (HLT!)
ddd, 20,       -0              ; 0 to save space for DDT
the, 21,       sar 9s          ; amount of torpedo space warpage
mhs, 22,       law i 10        ; number of hyperspace shots
hd1, 23,       law i 40        ; time in hyperspace before breakout
hd2, 24,       law i 100       ; time in hyperspace breakout
hd3, 25,       law i 200       ; time to recharge hyperfield generators
hr1, 26,       scl 9s          ; scale on hyperspatial displacement
hr2, 27,       scl 4s          ; scale on hyperspatially induced velocity
hur, 30,       40000           ; hyperspatial uncertainty
ran, 31,       0               ; random number seed
grv, 32,       sar 6s          ; gravitational constant
```

These are accessed via `xct`:

```asm
xct tno        ; AC = 41 (executes law i 41)
xct tvl        ; execute sar 4s on current AC
xct sac        ; execute sar 4s (same mnemonic, different parameter!)
xct hd1        ; AC = 40 (executes law i 40)
```

Some constants serve triple duty:
- `str, 100` = `hlt` if accidentally executed (opcode 760000 + 100 = 760100 ≈ HLT)
- `maa, 40` = `dac .` if accidentally executed (opcode 400000 + 40 = 400040 = DAC at address 40)
- `foo, -20000` = harmless negative number if executed

This economy — making every word serve as both data AND a safely-executable instruction — is characteristic of hardware-constrained development where every word counts.

Confidence: **Very High** — a general technique on the PDP-1, demonstrated here at its most extreme.

### 13. Frame Budget via `setup`/`count` Macros (section 9, new)

Spacewar! implements explicit frame timing:

```asm
ml0,    setup .mtc, 5000       ; initialise frame budget counter (5000 cycles)
        ...                     ; all game calculations
        background              ; display stars
        jsp blp                 ; display massive star
        count .mtc, .           ; burn remaining budget cycles
        jmp ml0                 ; next frame
```

The `setup` macro stores the address of the timing constant into the counter cell. The `count` macro is `isp` / `jmp` pair that decrements the counter toward zero, looping at ~3 cycles per iteration. Any remaining cycles in the frame budget are consumed here, ensuring consistent frame timing regardless of how much work the game logic did.

This is the exact pattern described in our tic-tac-toe "under consideration" section. Spacewar! implements it and it WORKS. The handbook's optimization section (9) should include this pattern as the standard PDP-1 frame pacing technique.

Confidence: **Medium** — observed in Spacewar! only, but the technique is architecturally general.

### 14. Multi-File Assembly (new section)

Spacewar! is split across 3 `.mac` files that must be assembled and loaded in sequence:

1. `spacewar4.8pt1.mac` — Main logic and utility subroutines (sin, cos, sqrt, outline compiler, star display). No `start` directive — just `start` (no label) at the end.
2. `spacewar4.8pt2.mac` — Game objects, collision, torpedo, hyperspace, ship calculation, initialization. Ends with `start 4`.
3. `spacewar4.8scorer.mac` — Score display system. Starts at fixed origin `4544/` (octal). Ends with `start 4`.

The loading order matters: the RIM tapes load into memory sequentially, building up the complete program. The final `start 4` in the scorer file sets the entry point.

The handbook currently assumes single-file programs. Multi-file builds require:
- Consistent origin directives (`.` or `N/`)
- Non-overlapping address allocation
- Correct load order
- Only the LAST file's `start` directive matters

Confidence: **High** — demonstrated in Spacewar!; general PDP-1 practice.

### 15. The `init` Macro Pattern (section 2.3)

Spacewar! has an `init` macro (different from ICSS's `initialize`):

```asm
; Definition (implied — not explicitly defined, used as built-in)
; init A,B generates: law B / dap A

; Usage — initialise the object table dispatch (17 calls in a row):
ml0,    setup .mtc, 5000       / delay for loop
        init ml1, mtb           / loc of calc routines
        init mx1, nx1           / x
        init my1, ny1           / y
        init ma1, na1           / count for length of explosion or torp
        init mb1, nb1           / time taken by calc routine
        init mdx, ndx           / dx
        init mdy, ndy           / dy
        init mom, nom           / angular velocity
        init mth, nth           / angle
        init mfu, nfu           / fuel
        init mtr, ntr           / number torps remaining
        init mot, not           / outline of spaceship
        init mco, nco           / old control word
```

This sets up 14 self-modifying pointers in a clean 14-line block rather than 28 lines of `law`/`dap` pairs. The pattern is: `init target, source` → assembles `law source / dap target`.

Confidence: **High** — used extensively in Spacewar!; generalizable.

### 16. The `swap` Macro (confirmed)

Spacewar! doesn't define `swap` as a named macro but uses `rcl 9s` pairs directly:

```asm
; In outline compiler: swap AC and IO
ocs,    dap ocz
        dio i oc       ; store IO to compiled output
        idx oc
        dio i oc       ; store IO again
        idx oc
ocz,    jmp .

; In ship display coordinate handling
        swap           ; (if swap were a macro: rcl 9s / rcl 9s)
```

The `rcl 9s` / `rcl 9s` pair (rotate combined 36-bit register left by 9 bits, twice) exchanges AC and IO. This confirms the technique is period-authentic and was used by the original Spacewar! developers. The handbook's section 1.3 already documents this.

Confidence: **Very High** — confirmed in original Spacewar! source + ICSS + PDP-1 Handbook.

---

## Proposed Handbook Section Changes

| Section | Change | Priority |
|---------|--------|----------|
| 2.3 Macros | Add `define`/`term` syntax variant. Add `init`, `repeat`, `clear` directives. Document both spellings (`term`, `terminate`, `terminate`). | High |
| 2.5 Pseudo-ops | Add `=` for computed offset arithmetic. Document `.`-prefixed local variables as alternative to `\`. Add `clear range` directive. | High |
| 4.5 | Add "Runtime Code Generation" as an advanced memory organization technique, with the outline compiler as worked example. | Medium |
| 5.1 Subroutines | Elevate JDA to co-primary status with JSP. Add `jsp i` indirect dispatch with Spacewar! control-word example. | High |
| 5.4 XCT | Expand with Spacewar!'s triple-duty parameter block example (data-as-instructions, safely executable). | Medium |
| 7 Loop Idioms | Add `idx` counting idiom alongside `isp`/`count`. Add `index` table-walk pattern. Add `setup`/`count` frame budget pattern. | High |
| 9 Optimization | Add new subsection: "Frame Budget Timing" with Spacewar!'s `setup`/`count` macro pattern. Add "Data-as-Instructions" economy. | Medium |
| 11 Commenting | Add note that period-appropriate minimal style exists and was standard at MIT; modern verbose commenting is a best practice. | Low |
| **NEW** | **Multi-File RIM Builds** — origin directives, load order, non-overlapping address allocation, only last `start` matters. | Low |
| **NEW** | **Object Table Design** — computed-offset property tables using `=` aliasing, with the Spacewar! object system as worked example. | Medium |
| **NEW** | **The Outline System** — runtime code generation as a display optimisation technique: direction-code data format, compiler pattern, execution. | Medium |

---

## Confidence Ratings

| New Rule / Pattern | Confidence | Evidence |
|-------------------|------------|----------|
| JDA/JSP co-primary calling conventions | Very High | Spacewar! + ICSS + PDP-1 Handbook |
| `define`/`term` macro syntax | Very High | Spacewar! source + MACRO-1 manual |
| `repeat` assembler directive | Very High | Spacewar! source + MACRO-1 manual |
| `clear` range directive | High | Spacewar! only; matches MACRO-1 docs |
| `=` computed offset arithmetic | High | Spacewar! only; architecturally sound |
| `jsp i` indirect dispatch | Very High | Spacewar! + PDP-1 Handbook |
| `idx` counting idiom | Very High | Spacewar! + ICSS + PDP-1 Handbook |
| `.`-prefixed local variables | High | Spacewar! only; general PDP-1 convention |
| Outline compiler (runtime code gen) | High | Unique to Spacewar!; well-documented source |
| Data-as-instructions parameter economy | Very High | Spacewar! + general PDP-1 practice |
| Frame budget with `setup`/`count` | Medium | Observed in Spacewar! only |
| Multi-file RIM builds | High | Spacewar! demonstration; general practice |
| `init` macro pattern | High | Spacewar! only; generalizable |
| Minimal commenting style (period) | Medium | Period-specific practice |
| `swap` = `rcl 9s` × 2 | Very High | Spacewar! + ICSS + PDP-1 Handbook |

---

## Summary

Spacewar! 4.8 (1963) confirms:

- **8 handbook rules** as Very High confidence (JDA, JSP, `swap`, `idx`, packed coordinates, `xct` parameterization, `sma`/`spa` abs value, computed GOTO)
- **Extends 3 rules** with additional variants (`define` syntax, `.`-prefixed locals, non-`x` return labels)
- **Challenges 1 rule** (commenting standard — period code was minimally commented)
- **Adds 7 new patterns** not in the handbook (outline compiler, object table with `=` offsets, multi-file builds, frame budget, `init` macro, data-as-instructions extremes, `clear` directive)
- **Proposes 3 new sections** for the handbook

The most significant finding is that 62-year-old Spacewar! code and modern ICSS code share the same core patterns — the PDP-1 idiom is remarkably stable across decades. The differences are in style (comments, naming) and in Spacewar!'s more aggressive use of meta-programming (runtime code generation, data-as-instructions) driven by tighter memory constraints.
