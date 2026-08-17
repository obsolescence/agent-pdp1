# Arithmetic on the PDP-1

## Ones' complement

The PDP-1 is a **ones'-complement** machine. Negation is bitwise complement
(`cma`), with no "add one" step.

- `+0` = `000000`, `−0` = `777777`. **Both exist and both are zero.**
- Range of an 18-bit word: −131071 … +131071.
- `sza` tests for `000000` only. A computation that lands on `−0` will *not*
  skip. This is the classic source of loops that never terminate and comparisons
  that never match.
- Overflow sets a separate flip-flop, tested and cleared by `szo`. There is no
  link bit.

Where `−0` comes from: subtracting a value from itself via `add` of the
complement (`cma` then `add`) yields `777777`, not `000000`. `sub Y` handles
this correctly and gives `+0` for equal operands, so **prefer `sub` over
`cma`+`add` when the result is going to be tested with `sza`.**

## Comparison

```asm
        lac value
        sub expect              / +0 if equal
        sza
        jmp mismatch
```

`sub` destroys the value in AC. If it is needed afterwards, save or reload it —
this is a frequent bug in win-detection and table-scan code, where the mark
being compared is also the mark to be recorded.

The direct comparisons are usually better:

```asm
        sas expect              / skip if AC = C(expect)
        jmp different
        ...                     / equal

        sad expect              / skip if AC ≠ C(expect)
        jmp same
        ...                     / different
```

Both `sad` (`500000`) and `sas` (`520000`) exist in the emulator and in both
assemblers' symbol tables. They leave AC untouched, which is their main
advantage over `sub`/`sza`.

## Loop termination

Two approaches, and the choice matters more than it looks.

### Counter, decremented to zero — the default

```asm
        lac nsteps
        dac ctr
loop,   ...                     / body
        lac ctr
        sub one
        dac ctr
        sza
        jmp loop
```

Works for any step size and any range. The iteration count is explicit and can
be checked by reading `nsteps`.

### `isp` — increment and skip if positive

```asm
        law i N                 / ctr = −N
        dac ctr
loop,   ...
        isp ctr
        jmp loop                / not yet positive
```

Compact, and the idiom behind Spacewar!'s frame budget. Remember that
ones'-complement zero has its sign bit clear, so **`isp` skips on zero as well
as on positive values** — counting up from −N terminates when the counter
reaches `000000`, after N iterations.

### `sad` against a limit — fragile

```asm
        lac x
        add step
        dac x
        sad limit               / skip if x ≠ limit
        jmp loop
```

This only terminates if `(limit − start)` is an exact multiple of `step`. With
`start = 677777`, `limit = 100000`, `step = 400`, the range is `200001` octal —
`400` does not divide it, `x` never equals `limit`, and the loop runs forever.

Use `sad`/`sas` termination only when scanning for a sentinel value that is
genuinely going to be hit. For counted iteration, use a counter.

## Shifts versus rotates

See `references/instruction-set.md` for the full table. The distinction that
matters:

- `sar Ns` — **arithmetic** right shift, sign bit duplicated. `ac = (AC&B0) | AC>>1`
- `rar Ns` — rotate right, LSB wraps into MSB. `ac = (AC&B17)<<17 | AC>>1`

For a positive value, `sar` is a plain divide-by-2^N. For a *logical* shift of a
word whose sign bit may be set, `rar Ns` followed by `and 377777`-style masking
is the way. Notes claiming `sar` is secretly a rotate that must always be masked
are wrong.

The shift count is the **number of 1-bits in the low 9 bits** of the
instruction, so `9s` = `777`, `8s` = `377`, `1s` = `001`. `rcl 9s` twice rotates
the 36-bit AC:IO pair by 18 and thus exchanges AC and IO:

```asm
define swap rcl 9s rcl 9s term
```

`scr`/`scl` shift the combined pair; `rcr`/`rcl` rotate it. Any of the combined
forms will change IO — that is what they are for, not corruption. A combined
right shift leaves a small (≤18-bit) result in IO, not AC — swap (`rcl 9s`
twice) before `dac`.

## The Extended Arithmetic Element: `mul` and `div`

Hardware multiply and divide come from the Type 10 EAE. In blincolnlights the
same opcodes decode as either the step instructions or the full operations
depending on a runtime switch: **[src]** `pdp1.h`

```c
#define IR_MUS (!pdp->muldiv_sw && (IR == 026))
#define IR_DIS (!pdp->muldiv_sw && (IR == 027))
#define IR_MUL (pdp->muldiv_sw && (IR == 026))
#define IR_DIV (pdp->muldiv_sw && (IR == 027))
```

So `540000` is `mus` with the EAE off and `mul` with it on. The assembler cannot
tell them apart and does not need to — this is a machine configuration, not a
source-level choice. Get the configuration right before concluding that a
multiply is broken.

The emulator implements both as a faithful step-by-step simulation of the EAE's
MDP micro-sequence, not as a host-language `*` — so the register states in the
middle of the operation, and the timing, are real.

### `mul` product format

The product is **not** a simple AC=high / IO=low split. From the handbook:

> The product of C(AC) and C(Y) is formed in the AC and IO registers. The sign of
> the product is in the AC sign bit. IO Bit 17 also contains the sign of the
> product. The magnitude of the product is the 34-bit string from AC Bit 1
> through IO Bit 16.

| Field | Location |
|---|---|
| sign | AC bit 0 (and copied to IO bit 17) |
| magnitude, high 17 bits | AC bits 1-17 |
| magnitude, low 17 bits | IO bits 0-16 |

To read it back out:

```python
sign     = (ac >> 17) & 1
mag_high = ac & 0o377777          # AC bits 1-17
mag_low  = (io >> 1) & 0o377777   # IO bits 0-16
product  = (mag_high << 17) | mag_low
if sign: product = -product
```

### Repacking to a normal double word

Because the whole magnitude sits one place left of where a conventional
double-word wants it, **`scr 1s` immediately after `mul` converts the EAE
packing into an ordinary signed 36-bit double** — high word in AC, low word in
IO, sign preserved by the arithmetic shift. One instruction, no masking:

```asm
        lac multiplier
        cli
        mul i sp                / EAE packing
        scr 1s                  / now a normal AC:IO double
```

The inverse holds going in: to feed a single 18-bit value to `div`, it has to be
shifted *left* one place into the same packing. `scl 1s` does that — but see the
sign-extension note under overflow below, because `scl` on a cleared AC does not
sign-extend a negative dividend.

Worked example — `3 × 1`. The magnitude's least significant bit sits at IO bit
16, not IO bit 17, so the result is shifted one place left relative to a naive
reading:

```
AC = 000000
IO = 000006        not 000003
```

`50 × 1024 = 51200` gives `AC = 000000, IO = 310000`. Both check out against the
handbook packing. If a multiply "returns double the expected value", it is this
packing, not a bug.

### `div` skips on success

> The instruction that follows a DIV will be skipped unless an overflow occurs.

In the emulator the skip is `if(pdp->scr & 2) pc_inc(pdp);` at the end of the
divide sequence, with the step counter short-circuited when overflow is
detected. **[src]**

So the instruction immediately after `div` is the **overflow handler**:

```asm
        div divisor
        jmp ovflow              / executed only on overflow
        dac quotient            / normal path
```

Inherited notes teach `jmp .+1` as the way to "absorb the skip". That assembles
to a jump to the next instruction — which is where the skip lands anyway — so it
is a no-op that silently discards the overflow case. It is only appropriate when
overflow has been proven impossible, and even then `jmp ovflow` to a `hlt` costs
one word and catches the assumption breaking.

After a successful divide, AC holds the quotient as a **plain 18-bit
ones'-complement integer** (not in the 34-bit magnitude format) and IO holds the
remainder, its sign taken from the dividend.

### `div` overflow condition

Overflow occurs when the magnitude of the high-order part of the dividend is
greater than or equal to the magnitude of the divisor. The high-order part is
the value in AC, i.e. `dividend >> 17`.

```
safe when   (dividend >> 17) < divisor
i.e.        dividend < divisor × 2^17
```

On overflow, AC and IO are restored to their pre-`div` values and the next
instruction is *not* skipped.

**Sign-extend the dividend.** For a single 18-bit value the dividend must occupy
AC:IO with the sign in AC bit 0 — not merely the magnitude shifted left. The
common shortcut

```asm
        cla                     / AC = 0
        lio i sp                / IO = v
        scl 1s                  / shift into EAE position
```

is correct for positive `v` only. `scl` moves IO's *sign bit* into AC bit 17,
not bit 0, so a negative `v` arrives looking positive with a corrupted
magnitude, and `div` computes nonsense rather than overflowing. Sign-extend
first — load `v` into AC and shift it arithmetically right so AC becomes all
sign bits, then `scl 1s` the pair.

This bites in the standard `(A × B) / C` chain, because `mul` leaves a 34-bit
product and the divisor is often small:

```asm
        lac hwraw               / A
        mul prjraw              / (AC:IO) = A × B
        div dz                  / C
        jmp ovflow
        dac result
```

With `A = 400`, `B = 1000`, the product is 400000 and its high part is 3 — safe
for any divisor above 3. With `A = 3584`, `B = 51200` the high part is 1400,
which overflows for any realistic distance. Scale the inputs so the intermediate
product stays small rather than trying to handle the overflow.

The chain works because `mul` leaves the product in exactly the (AC:IO) form
`div` expects; nothing needs unpacking in between.

## Software multiply

Only needed when the EAE is unavailable. For a small multiplier, decompose it by
bits and accumulate shifted copies of the multiplicand:

```
result  = 0
shifted = m2 >> 9
temp    = m1
repeat 12 times:
    if temp & 1: result += shifted
    shifted <<= 1
    temp    >>= 1
```

Sizing keeps everything inside 18 bits: with `m2 ≤ 10240`, `shifted` starts
around 20 and reaches `20 × 2^11 = 40960`, comfortably under `2^17`.

For a constant multiplier, decompose it once at design time — `50 = 32+16+2`, so
`(50 × x) >> 9` is `(x>>4) + (x>>5) + (x>>8)`: two adds and three shifts, no loop.

The full 18×18 shift-and-add with a 36-bit accumulator and ones'-complement
carry detection is possible but fiddly enough that it is worth avoiding unless
the operand range genuinely demands it.

## Fixed point

There is no floating point. The usual arrangement mirrors the display format:
signed, 9 integer bits and 8 fractional bits, which makes a coordinate value
directly usable by `dpy` after an 8-bit shift. See
`references/type30-display.md`.

Toroidal wraparound at the screen edges comes free from ones'-complement
overflow, which is why Spacewar!'s playfield wraps without any explicit test.
