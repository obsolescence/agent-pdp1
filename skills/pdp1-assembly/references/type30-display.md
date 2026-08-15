# The Type 30 Display

A point-plotting CRT. It draws **dots, one per `dpy` instruction**. There is no
vector generator, no line hardware, no fill. Every line, character and shape is a
loop that plots individual points, and the cost of everything on screen is
counted in `dpy` instructions per frame.

The phosphor is two-layer — a short-persistence white component and a
long-persistence yellow one — so points fade over roughly a quarter second
rather than vanishing. Programs exploit this: anything redrawn every other frame
appears at about half brightness.

## Coordinates: the thing that catches everyone

`dpy` takes X from the **top 10 bits of AC** and Y from the **top 10 bits of
IO**: **[src]** `blincolnlights/pdp1/pdp1.c`, the `case 007` IOT

```c
pdp->dbx |= AC>>8;
pdp->dby |= IO>>8;
pdp->dint |= (MB>>6)&7;
```

In DEC's MSB-first numbering those are bits 0-9. Each is a **10-bit ones'
complement** value, range −511 … +511, with the origin at screen centre.

The consequence is the single most common Type 30 bug:

```asm
        lac (100                / 100 lands in the LOW bits
        lio (100
        dpy                     / plots at the centre — top 10 bits are zero
```

A coordinate must be **pre-shifted left by 8**. One screen unit is 256 in the
raw word.

### Getting a coordinate into position

**Pre-formatted constants** — the ICSS style, and the safest:

```asm
cgy,    010000                  / Y = +16 units   (16 << 8)
cgx1,   006000                  / X = +12 units   (12 << 8)

        lac cgx1
        lio cgy
        dpy
```

The value is `pixel_offset × 256`, written directly in octal. `010000` octal is
4096 = 16 × 256.

**Computed values** — shift after computing:

```asm
        lac value               / small integer in the low bits
        sal 8s                  / now in bits 0-9
        dac xr
```

`sal 8s` only behaves for magnitudes that fit in 10 bits after shifting; a
quotient above 511 will shift its significant bits out of the top of the word.

**Packed pairs** — Spacewar!/ICSS starfield format, 9 bits of X and 9 of Y in
one word:

```asm
        lac packed              / [XXXXXXXXX YYYYYYYYY]
        cli                     / IO = 0
        scr 9s                  / AC = 000000000XXXXXXXXX, IO = YYYYYYYYY000000000
        sal 9s                  / AC = XXXXXXXXX000000000
        dpy-i
```

Halves the table size for star fields. The cost is unsigned 9-bit range only.

### Negative zero

Both `+0` (`0000000000`) and `−0` (`1111111111`) exist in the 10-bit field, and
they plot **one position apart** — `−0` lands just left of and below `+0`.
Arithmetic that can produce `−0` will show a visible one-pixel jitter. The
emulator's coordinate mapping handles the ones'-complement conversion
explicitly: **[src]**

```c
int mapcoord(int x) {
        if(x & 01000) x++;      /* sign bit set: 1's complement -> 2's */
        return (x+01000)&01777;
}
```

That `if` is the negative-zero correction. Reproductions of `mapcoord` that omit
it — as inherited notes do — are off by one across the whole negative half of
the screen.

### Which way is up

**Larger Y is higher on the physical screen.** X increases to the right.

This is worth stating flatly because inherited notes contradict themselves on it
within a single file. The confusion comes from the SVG capture tooling: the
protocol's Y is written straight into an SVG `cy` attribute, and **SVG's Y axis
points down**, so a captured image is vertically mirrored relative to the real
display. A point reported at "y=891" in a capture is near the *top* of the CRT.

Corroboration from the display client: light-pen positions are sent back as
`cmd |= 1023-peny`, an explicit flip between window coordinates and protocol
coordinates. **[src]** `p7sim/main.c`

If a capture is the only view available, mirror it mentally, or fix the capture
tool to emit `1023 - y`.

### Converting between raw values and screen positions

```
screen_position = mapcoord(raw >> 8)        ; centre = 512
raw             = (position - 512) * 256    ; negate in ones' complement if < 0
```

| Position | Raw octal | Raw decimal |
|---|---|---|
| 512 (centre) | `000000` | 0 |
| 416 | `717777` | −24576 |
| 448 | `737777` | −16384 |
| 576 | `040000` | +16384 |
| 608 | `060000` | +24576 |

| Offset | Raw units | Octal |
|---|---|---|
| 1 position | 256 | `000400` |
| 2 | 512 | `001000` |
| 8 | 2048 | `004000` |
| 48 | 12288 | `030000` |

## `dpy` variants and `ioh`

Bit 5 (the `i` bit, `010000`) and bit 6 (`004000`) select completion-pulse
behaviour:

| Written | Word | Behaviour |
|---|---|---|
| `dpy` | `730007` | request completion pulse and wait for it |
| `dpy-i` | `720007` | fire and forget — no pulse, no wait |
| `dpy-4000` | `724007` | request the pulse, keep executing; wait later with `ioh` |

A point takes about 50 µs to plot. `dpy-i` in a tight loop is safe whenever the
loop body itself takes longer than that; ICSS uses it throughout the star field.
`dpy-4000` followed by `ioh` lets the CPU do useful work during the plot and is
what the character-drawing code uses, where dots come faster than the loop
overhead covers.

Using plain `dpy` everywhere is correct but slow — it stalls for every dot.

## Frame timing

The machine has no timer interrupt and no realtime clock. Frames are paced by
**counting instructions**, the technique Spacewar! established:

```asm
define load  A,B  lio (B  dio A  term
define count A,B  isp A   jmp B  term

fr0,    load \ict, -4500        / budget for this frame
        jsp bg                  / draw background; it adds its cost back
        count \ict, .           / burn whatever is left
        jmp fr0
```

Each routine adds its known instruction cost back into the budget:

```asm
rkt,    ...
        lac \ict
        add (1000               / this routine's cost
        dac \ict
        jmp rkx
```

so the total time per frame stays constant regardless of how much was drawn.
The budget constant is calibrated so the burn loop always has something left to
burn — if a frame ever overruns, the pacing collapses and the display flickers
at a variable rate.

## Half-brightness by drawing every other frame

Long phosphor persistence plus a 50% duty cycle gives a second brightness level
for free — how Spacewar! dims its star field against the ships.

```asm
gridfc, 0                       / frame counter

grid4,  dap gr4ret
        isp gridfc              / increment; skip if positive (or zero)
        jmp gr4ret              / negative — skip this frame
        law i 1                 / reset to −1
        dac gridfc
        ...                     / draw
gr4ret, jmp .
```

Cycle: `777777` → increments to `000000`, sign clear, skips, draws, resets to
`777776`; next frame `777776` → `777777`, sign set, no skip, returns without
drawing. Alternating frames, 50% duty.

This depends on `isp` treating ones'-complement zero as positive. See
`references/arithmetic.md`.

## Drawing lines

Every line is a plotted loop. Use a **counter**, not a comparison against the
end coordinate — the step rarely divides the range exactly, and a `sad` test
against the endpoint will miss and run forever. See `references/arithmetic.md`.

```asm
        lac nsteps
        dac ctr
lloop,  lac cx
        lio cy
        dpy-i
        lac cx
        add xstep
        dac cx
        lac cy
        add ystep
        dac cy
        lac ctr
        sub one
        dac ctr
        sza
        jmp lloop
```

Diagonals that cross other artwork need a visible offset — a line drawn exactly
through a symbol's own dots is invisible against it. Apply such offsets in the
dispatch before the call, not inside the line routine, so the routine stays
general.

## Characters

There is no character generator. Two approaches:

**Bitmap loop** — 5×7 dot matrix, two 18-bit words per glyph, row-major. Test
the sign bit of IO, rotate, plot where set. Simple, and costs a test per cell
whether or not a dot is drawn.

**Compiled outlines** — Dan Edwards' technique for Spacewar!, revived in ICSS
episode 9. Generate PDP-1 instructions for the *set* dots only, then `jmp` to
the generated code. Each dot becomes an `add`/`sub` of the delta from the
previous dot plus a `dpy-i`; rows advance with `swap` / `sub cgy` / `swap`. The
compiled form costs nothing for blank cells, which is most of a character.

```
03423 402566  add cgx+2         / step right
03424 724107  dpy-i             / plot
03427 422564  sub cgy           / next row
03433 730000  ioh
03504 602757  jmp cdx           / exit
```

Worth it when the same text is redrawn every frame; not worth it for a title
screen.

## Sine and cosine

The Adams Associates routine (DEC memo M-1094, 1960) as used by Spacewar! and
ICSS. Taylor series to four terms:

```
sin(x) = ((((C7)x² + C5)x² + C3)x² + C1)x
```

Argument in AC, ±2π, binary point right of bit 3 (2π = `311040` octal). Result
has its binary point right of bit 0. Called with `jda sin` or `jda cos` — note
`jda`, because the argument arrives in AC and must be deposited. Roughly 2.3 ms
per call with hardware multiply, which is a substantial fraction of a frame:
precompute where possible.

## The wire protocol

The emulator streams 32-bit words to the display client over TCP.

```
bits  0-9   x          (0-1023, after mapcoord)
bits 10-19  y          (0-1023)
bits 20-22  intensity  (0-7)
bits 23-31  dt         (time delta)
```

```c
int cmd = x | (y<<10) | (dt<<23);
```
**[src]**

`dt == 511` is an escape: the **next** word is not a point but a raw time delta,
used to age the display when nothing is being drawn. Points with x=0, y=0 and
zero intensity are idle filler.

There are no frame markers. The client reconstructs frames purely from
accumulated time, ageing points out after a fixed persistence interval.

This matters for capture tooling: to reconstruct an image, read words, skip the
escape pairs, drop zero-intensity points, and remember the Y flip described
above.
