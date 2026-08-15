# PDP-1 Instruction Set

Opcode values verified against the blincolnlights decoder
(`blincolnlights/pdp1/pdp1.h`, `pdp1.c`) and the `macro1_1`/`monas` permanent
symbol tables. **[src]**

## Word and bit numbering

18-bit words. DEC numbers bits **MSB first**: bit 0 is the sign / most
significant bit (`0400000`), bit 17 is the least significant (`0000001`).
Almost all confusion in inherited notes comes from mixing this with LSB-first
numbering. In this file, "bit N" always means DEC numbering.

```
 bit:  0  1  2  3  4 | 5 | 6 ................ 17
      [  opcode     ]|[I]|[   address (12 bits)  ]
```

- **Opcode** — bits 0-4. The emulator computes it as `IR = MB>>13`. **[src]**
- **Bit 5** — the indirect ("defer") bit. In `macro1` source it is written `i`,
  as in `lac i ptr`, and its value is `010000`.
- **Address** — bits 6-17, a full 12 bits. Every word in a 4K bank is directly
  addressable. **There is no page-zero or current-page addressing on the
  PDP-1** — that is a PDP-8 concept.

Indirection is *multi-level* in normal mode: if the fetched word also has bit 5
set, the machine defers again. `eem` (Enter Extend Mode) switches to
single-level indirection with 16-bit effective addresses. **[handbook]**

Bit 5 only means "indirect" for memory-reference instructions. The emulator
excludes the shift, skip, `law`, `opr`, `iot` and `cal`/`jda` groups: **[src]**

```c
if((MB & B5) && !IR_SHRO && !IR_SKIP &&
                !IR_LAW && !IR_OPR && !IR_IOT && !IR_CALJDA)
        pdp->df1 = 1;
```

In those groups bit 5 is repurposed — see the skip group below.

## Memory reference instructions

| Mnemonic | Word | IR | Effect |
|---|---|---|---|
| `and Y` | `020000` | 001 | AC ← AC ∧ C(Y) |
| `ior Y` | `040000` | 002 | AC ← AC ∨ C(Y) |
| `xor Y` | `060000` | 003 | AC ← AC ⊕ C(Y) |
| `xct Y` | `100000` | 004 | Execute the instruction at Y |
| `cal Y` | `160000` | 007 | AC → M(100); PC → AC; jump to 101. Y ignored |
| `jda Y` | `170000` | 007 | AC → M(Y); PC → AC; jump to Y+1 |
| `lac Y` | `200000` | 010 | AC ← C(Y) |
| `lio Y` | `220000` | 011 | IO ← C(Y) |
| `dac Y` | `240000` | 012 | C(Y) ← AC |
| `dap Y` | `260000` | 013 | Address part (bits 6-17) of AC → address part of Y |
| `dip Y` | `300000` | 014 | Instruction part (bits 0-5) of AC → bits 0-5 of Y |
| `dio Y` | `320000` | 015 | C(Y) ← IO |
| `dzm Y` | `340000` | 016 | C(Y) ← 0 |
| `add Y` | `400000` | 020 | AC ← AC + C(Y), ones' complement |
| `sub Y` | `420000` | 021 | AC ← AC − C(Y), ones' complement |
| `idx Y` | `440000` | 022 | C(Y) ← C(Y)+1; AC ← result. **No skip** |
| `isp Y` | `460000` | 023 | C(Y) ← C(Y)+1; AC ← result; skip if result positive |
| `sad Y` | `500000` | 024 | Skip if AC ≠ C(Y) |
| `sas Y` | `520000` | 025 | Skip if AC = C(Y) |
| `mus`/`mul Y` | `540000` | 026 | Multiply step / full multiply — see below |
| `dis`/`div Y` | `560000` | 027 | Divide step / full divide |
| `jmp Y` | `600000` | 030 | PC ← Y |
| `jsp Y` | `620000` | 031 | PC → AC; PC ← Y. **No memory write** |

Notes that matter:

- **`idx` does not skip.** `isp` is the one that skips. The PDP-8's `isz`
  ("increment and skip if zero") does not exist here and is the source of a
  common misreading. `isp` skips when the *sign bit is clear* — and since
  ones'-complement `000000` has sign 0, **zero counts as positive**. **[handbook]**
- **`dap` writes only bits 6-17** — the address field. It leaves the opcode
  alone. This is what makes `dap ret` / `ret, jmp .` work.
- **`dzm i Y` is valid.** It is an ordinary memory-reference instruction and the
  decoder applies deferral to it like any other. Claims that indirect `dzm`
  causes an illegal-instruction trap are wrong. **[src]**
- **`sad` and `sas` both exist** in the emulator and in both assemblers' symbol
  tables. **[src]**

### Illegal opcodes

```c
#define IR_INCORR (IR==0 || IR==5 || IR==6 || IR==017 || IR==036)
```

IR 0 is included, so **a word of `000000` is not a clean halt** — it is an
illegal instruction. Executing through a zeroed region does not stop the machine
predictably. **[src]** To halt deliberately, use `hlt` = `760400`.

## Jump / subroutine group

`jsp Y` clears AC, then transfers PC into AC and jumps: **[src]**

```c
if(IR_JSP && !pdp->df1 || IR_LAW || IR_OPR && (MB & B10)) AC = 0;   // TP7
if(IR_JSP) pc_to_ac(pdp), clr_pc(pdp);                              // TP8
if(!pdp->df1 && (IR_JMP || IR_JSP)) mb_to_pc(pdp);                  // TP9
```

At the moment of transfer, PC already holds the address of the instruction
*after* the `jsp`, so AC receives the correct return address. AC also picks up
the overflow flag in bit 0, extend mode in bit 1 and the extended PC in bits
2-5 — which is why the return address is extracted with `dap` (address part
only) rather than by using AC whole. **[handbook]**

`jda Y` is the one that writes memory: `MB = AC` then `pc_to_ac`, then jump to
Y+1. It is exactly `dac Y` followed by `jsp Y+1`. **[src, handbook]** `cal Y` is
`jda 100` with Y ignored.

## Skip group (`opcode 032`, base `640000`)

Assembled as `640000` plus the bits below; several may be combined. **[src]**

| Mnemonic | Word | Bit | Skips when |
|---|---|---|---|
| `sza` | `640100` | 11 | AC = 0 |
| `spa` | `640200` | 10 | AC positive (bit 0 clear) |
| `sma` | `640400` | 9 | AC negative (bit 0 set) |
| `szo` | `641000` | 8 | overflow flag clear (and clears it) |
| `spi` | `642000` | 7 | IO positive (bit 0 clear) |
| `szs n` | `640000+n<<3` | — | sense switch n clear |
| `szf n` | `640000+n` | — | program flag n clear |

**Bit 5 inverts the whole condition:**

```c
if(MB & B5) skip = !skip;
```

So `sza i` (`650100`) skips when AC ≠ 0, `sma i` skips when AC is not negative,
and so on. Written `i` in source. This is the only conditional-inversion
mechanism the machine has.

`spa` is a real mnemonic in both `macro1_1` (`0640200`) and `monas`
(`0640200`). **[src]** Do not substitute `760200` for it — that is `cla`, which
silently clears AC instead of skipping.

## Operate group (`opcode 037`, base `760000`)

Combinable bits, evaluated in one instruction: **[src]**

| Mnemonic | Word | Bit | Effect |
|---|---|---|---|
| `nop` | `760000` | — | nothing |
| `cla` | `760200` | 10 | AC ← 0 |
| `cli` | `764000` | 6 | IO ← 0 |
| `cma` | `761000` | 8 | AC ← ¬AC |
| `clc` | `761200` | 8+10 | AC ← 0 then complement = all ones. **Not "clear link"** |
| `hlt` | `760400` | 9 | run ← 0 |
| `lat` | `762200` | 7+10 | AC ← 0, then AC ∨= test word |
| `lap` | `760100` | 11 | PC → AC |
| `stf n` / `clf n` | `760010+n` / `760000+n` | 14 | set / clear program flag |

The ordering inside `lat` matters and is worth internalising: bit 10 clears AC
*first*, then bit 7 ORs in the test word. That is why `lat` yields a clean test
word reading even immediately after a `jsp` left a return address in AC. **[src]**

There is **no link register on the PDP-1**. Overflow is a separate flip-flop
tested by `szo`.

## Shift and rotate group (`opcode 033`, base `660000`)

Selected by bits 9-12 (`(MB>>9) & 017`); the *number of shift steps* is the
number of 1-bits in the low 9 bits of the word. So `9s` = `777` = 9 steps,
`8s` = `377` = 8 steps, `1s` = `001` = 1 step. **[src]**

| Mnemonic | Word | Operation |
|---|---|---|
| `ral` | `661000` | rotate AC left |
| `ril` | `662000` | rotate IO left |
| `rcl` | `663000` | rotate combined AC:IO left |
| `sal` | `665000` | shift AC left (sign preserved) |
| `sil` | `666000` | shift IO left |
| `scl` | `667000` | shift combined left |
| `rar` | `671000` | rotate AC right |
| `rir` | `672000` | rotate IO right |
| `rcr` | `673000` | rotate combined AC:IO right |
| `sar` | `675000` | shift AC right (**arithmetic** — sign duplicated) |
| `sir` | `676000` | shift IO right |
| `scr` | `677000` | shift combined right |

**`sar` is an arithmetic shift, not a rotate.** From the decoder: **[src]**

```c
case 015:  // SAR
        ac = (AC&B0) | AC>>1;          // sign bit preserved
        break;
case 011:  // RAR
        ac = (AC&B17)<<17 | AC>>1;     // LSB wraps to MSB
        break;
```

Any note claiming `sar` is really a rotate and must be patched up with an
`and` mask is wrong — it is `rar` that rotates. For a *logical* right shift of a
value whose sign bit may be set, `rar` + `and 377777` is correct; for a positive
value `sar` alone is fine.

`rcl 9s` twice (18 steps total) exchanges AC and IO — the classic `swap` macro:

```asm
define swap rcl 9s rcl 9s term
```

## `law` — load accumulator with word

`law N` (`700000+N`) loads the 12-bit constant N into AC: **[src]**

```c
if(IR_LAW) AC = 0;              // TP7
if(IR_LAW) AC |= MB & 0007777;  // TP8
if(IR_LAW && (MB & B5)) AC ^= WORDMASK;   // TP9 — 'law i' negates
```

So `law i N` gives −N in ones' complement. `law` is defined in both assemblers
(`0700000`) and works reliably; it is the normal way to get a small constant or
a label's address into AC. Claims that it "may not execute reliably" are
superstition.

Range is 12 bits, so `law` cannot load a constant above `07777`. Larger
constants come from a literal (`lac (377777`) or a data word.

## `iot` — input/output transfer (`opcode 035`, base `720000`)

Device selected by the low bits. Bit 5 (`010000`) controls completion-pulse
behaviour, which is why `dpy` and `dpy-i` differ. See `references/io-and-fio.md`
and `references/type30-display.md`.

Common ones:

| Mnemonic | Word | Device |
|---|---|---|
| `rpa` | `730001` | read paper tape, alphanumeric |
| `rpb` | `730002` | read paper tape, binary |
| `rrb` | `720030` | read reader buffer |
| `ppa` | `730005` | punch paper tape, alphanumeric |
| `ppb` | `730006` | punch paper tape, binary |
| `tyo` | `730003` | typewriter out |
| `tyi` | `720004` | typewriter in |
| `dpy` | `730007` | display a point on the Type 30 |
| `cks` | `720033` | read device status into IO ("check status") |
| `ioh` | `730000` | halt until I/O completion pulse |
| `lsm` | `720054` | **leave** sequence break mode |
| `esm` | `720055` | **enter** sequence break mode |
| `cbs` | `720056` | clear sequence break system |
| `lem` | `720074` | **leave extend mode** |
| `eem` | `724074` | **enter extend mode** |

`rpa`/`rpb` are the paper-tape *reader*, not a printer. `lem`/`eem` are about
extend (16-bit addressing) mode, not "end mode" — the handbook is explicit.
`cks` reads status; it computes no checksum. Older notes get all three wrong.

## Extend mode

`eem` switches to single-level indirection with 16-bit effective addresses; PC
and MA become 16-bit. Non-indirect instructions still address the 4K bank
selected by PC bits 2-5. Under extend mode an instruction in location 7777 is
followed by location 0000 *of the same bank* unless control is transferred.
**[handbook]**

`jsp`, `jda`, `cal` and `lap` all deposit overflow in AC bit 0, extend-mode
state in bit 1, and the extended PC in bits 2-17. **[handbook]**
