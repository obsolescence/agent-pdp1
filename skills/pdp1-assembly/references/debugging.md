# Debugging

Two toolkits, and they are complementary.

**The debug service on port 1040** gives you breakpoints, watchpoints,
stepping, tracing and a call ring, all from outside the program, with nothing
written into core. It is the right default for anything you are actively
working on. See `references/debug-protocol.md`.

**Source-level techniques**, chiefly the `szs`/`hlt` pairs below, need nothing
but the program and the front panel. Reach for them when:

- you want a breakpoint that is a *label*, not an address, and survives every
  reassembly that moves the code;
- you want to arm and disarm it by reaching over and flipping a switch while
  the program runs, without a socket or a client;
- you are on real PiDP-1 hardware, or the machine is shared and you would
  rather not take run control away from whoever else is on it;
- the interesting thing happens inside a display frame and you want the stop
  to cost two instructions rather than a network round trip.

The habits at the end of this file — predict-then-compare, reload before you
debug, read the listing, suspect your own code — apply to both and matter more
than either.

## Sense-switch breakpoints

The best trick in the box. Put a `szs` / `hlt` pair anywhere you want a
breakpoint, and arm it from the front panel at run time:

```asm
        szs 10                  / SS1 down: skip the hlt and carry on
        hlt                     / SS1 up:   stop here
```

`szs n` skips when the selected sense switch is **clear**. So with the switch
down the pair costs two instructions and does nothing; flip the switch up and
the program stops the next time it reaches that point. Flip it down and press
CONTINUE to carry on.

There are six sense switches, so this gives **six independently toggleable
breakpoint channels**. They are channels, not individual breakpoints — put as
many `szs 20 / hlt` pairs as you like throughout the program and SS2 arms all of
them at once. Grouping by *category* is what makes this powerful:

```asm
        szs 10 / hlt            / SS1 — per-frame: stop once per display frame
        szs 20 / hlt            / SS2 — input: stop when a switch edge is seen
        szs 30 / hlt            / SS3 — AI: stop on entry to the move chooser
        szs 40 / hlt            / SS4 — win detection
        szs 50 / hlt            / SS5 — error and can't-happen paths
        szs 60 / hlt            / SS6 — the one you move around while working
```

Why this beats **depositing** `hlt` over an instruction — which is what you
should do only if you have no debugger at all, since `b <addr>` on port 1040
has none of these problems either:

- **Nothing is patched**, so nothing has to be restored. No risk of leaving a
  breakpoint behind in core, and no chance of clobbering the instruction you
  meant to stop *before*.
- **It survives reassembly.** Deposited breakpoints are addresses, and every
  address moves when you add a word. These are labels in the source.
- **It survives a crash and reload.** The breakpoints come back with the tape.
- **Arming is instantaneous and needs no tooling** — reach over and flip a
  switch while the program runs.
- **It is safe on subroutine entry.** A deposited breakpoint on the first
  instruction of a `jsp` subroutine destroys the `dap ret` that saves the return
  address, so the routine crashes on return instead of stopping. A `szs`/`hlt`
  pair placed *after* the `dap ret` has no such interaction.

The cost is two words and roughly 10 µs each time the pair is passed with the
switch down. Cheap enough to leave in permanently, though think twice inside the
innermost loop of a display routine where the frame budget is tight.

### Getting the operand right

`szs` and `szf` are **both** defined as `0640000` in `macro1_1` and in `monas`.
**[src]** The mnemonic is documentation; the operand supplies the field, and the
two fields are different:

```
 640000 + 0N0   sense switch selector   (bits 070)
 640000 + 00N   program flag selector   (bits 007)
```

So the operand is the **field value in octal, not the switch number**:

| Want | Write | Assembles to |
|---|---|---|
| sense switch 1 | `szs 10` | `640010` |
| sense switch 2 | `szs 20` | `640020` |
| sense switch 3 | `szs 30` | `640030` |
| sense switch 4 | `szs 40` | `640040` |
| sense switch 5 | `szs 50` | `640050` |
| sense switch 6 | `szs 60` | `640060` |
| all six clear | `szs 70` | `640070` |

**`szs 1` does not test sense switch 1.** It assembles to `640001`, which is
`szf 1` — skip on *program flag* 1. It will silently do the wrong thing rather
than fail, so this is worth checking in the listing the first time.

The decoder confirms the mapping: **[src]**

```c
if((MB&070) && !(pdp->ss & decflg(MB>>3))) skip = 1;   /* sense switches */
if((MB&007) && !(pdp->pf & decflg(MB)))    skip = 1;   /* program flags  */
if(MB & B5) skip = !skip;
```

`decflg` turns the selector 1-6 into a single bit mask, and selector **7 into
`077` — all six at once**. So `szs 70 / hlt` halts if *any* sense switch is up:
a master arm, useful as a "stop at the top of the frame whenever I'm debugging
anything" marker.

### Inverting the polarity

Bit 5 (`i`) inverts the skip, so `szs i 10` skips when SS1 is **up**:

```asm
        szs i 10                / SS1 up: skip
        hlt                     / SS1 down: stop
```

Occasionally handy, but prefer the plain form — switches down meaning "not
debugging" is the safer default, since that is how the machine will be found
after someone else has used it.

### Arming them without a front panel

`szs`/`hlt` pairs are not only for people standing at the machine. Over the
debug service:

```
panel on
sw ss 40          # SS1 up: every 'szs 10 / hlt' pair is now live
go
wait 5000
sw ss 0
panel off
```

So the same two words serve a human at the console and a script. Note the
numbering: `sw ss 40` is switch **1** — see `references/debug-protocol.md`.
Note also that while `ss` or `tw` is overridden the panel lights **all six
sense-switch lamps** as a warning, so on real hardware the SS lamps stop
telling you which switches are actually up; ask `sw` instead.

### Sense switches as run-time options

The same instruction is worth using for non-debugging purposes, and Spacewar!
and ICSS both do: sense switches select starfield mode, gravity, input source.
If you are already spending switches on options, keep a written note of the
assignment in the source header — six is not many, and a breakpoint channel
sharing a switch with a feature toggle is a confusing afternoon.

## Program flags as a software-only equivalent

`szf n` tests the six program flags, set and cleared under program control with
`stf n` / `clf n`. Same skip structure, same 1-6 plus 7-means-all encoding.

Because the program controls them, they suit conditional breakpoints that the
front panel cannot express:

```asm
        lac count
        sad (144                / 100th iteration?
        stf 1                   / arm the flag
        ...
        szf 1 / hlt             / stops only once armed
```

A crude but effective "break on the Nth time round".

## After a halt: reading the panel

`hlt` clears the run flag at TP9, by which point PC has already advanced. So:

- **PC points to the instruction *after* the one that halted.** The `hlt` itself
  is at PC−1; for a `szs`/`hlt` breakpoint pair, the `szs` is at PC−2, which is
  what identifies *which* breakpoint fired.
- **MA** holds the last memory address touched.
- **AC** is often the most informative register. If a `jsp` was the last thing
  executed, AC holds a return address — and if that value looks nothing like a
  code address, the call itself is the bug.
- **A halt you did not plant is not a `hlt`.** Opcode 0 is an *illegal*
  instruction, not a halt: `IR_INCORR` covers IR 0, 5, 6, 017 and 036. **[src]**
  A machine stopped in zeroed memory got there by running off the end of
  something, and the PC will be somewhere meaningless. Real `hlt` is `760400`.

Press CONTINUE to resume from PC. Nothing needs restoring, because nothing was
modified.

Over the debug service the same halt reads:

```
+ run=0 cyc=0 df1=0 pc=000106 ac=000000 … ma=000105 mb=760400 ir=37 … stop=halt
```

`stop=halt` is a real `hlt`; `stop=illegal` is opcode 0 or another undefined
word, which used to be indistinguishable. **`ma` is only meaningful on these
two reasons** — every debugger-caused stop is at an instruction boundary,
where MA has already been cleared and reads `000000`. See
`references/debug-protocol.md`.

## Predict, then compare

The habit that finds bugs, as distinct from the habit that looks at registers.

1. Before stepping, say what will change — AC, PC, and which memory word.
2. Step.
3. Compare against the prediction.

A match means the mental model survives one more instruction. A mismatch is the
bug, located exactly. Reading registers without having formed an expectation
first is sightseeing: everything looks plausible in octal.

This works with nothing but SINGLE INSTRUCTION and the register lamps. The
debug service just makes the loop faster: `trace 20` with a `--lst` gives you
twenty predictions to check at once, each next to its source line.

Automated expectation checking is a convenience, not a prerequisite. The
protocol has no assertion command on purpose — `run <n> if M[x]!=<v>` is the
machine-side half (stop when an invariant breaks) and comparing a `trace`
against what you expected is the human-side half.

## Reload before you debug

A program that ran through address 0 has been executing its own constants and
variables as instructions, and any `dac`/`dap`/`dio` bit patterns among them have
written to memory. Constants shift, counters go negative, and the damage
compounds across repeated crash cycles.

**Reload the tape before investigating anything.** Otherwise the symptoms being
chased belong to the previous crash. This is the highest-value habit in PDP-1
debugging: corruption outlives the crash, and a "new" symptom is very often old
damage.

You no longer have to guess whether it happened:

```sh
python3 scripts/pdp1dbg.py --lst prog.lst check
```

compares every assembled word against core and prints the differences. The
`dap` return cells and your variables *should* differ — that is the program
working. Anything else is damage, and the answer is `l prog.rim` before you
form a single hypothesis.

Symptoms that usually mean corrupted state rather than a fresh bug:

| Observation | Likely cause |
|---|---|
| Display dark but RUN still on | Loop counters corrupted; a negative count runs 2^18 iterations |
| Constants near the start of core look shifted | Execution marched through the constant pool |
| A subroutine that worked yesterday returns to nowhere | Its return cell was overwritten |

## Read the listing, not the source

The `.lst` is the authority on addresses:

```
  83 00114 700015      go,     law pstr
   |    |      |
   |    |      +-- assembled word
   |    +--------- address of this word
   +-------------- source line number
```

The address column is **not** the operand. Confusing the two produces
convincing-looking reports of the assembler resolving labels wrongly — see item
4 of `references/errata.md`.

Check the end of the listing too: undefined symbols are prefixed `?`, redefined
ones `#`. A program that "doesn't run" quite often did not assemble cleanly.

## Suspect your own code first

The assembler and the emulator are far better exercised than the program being
written. Before concluding a tool is broken:

1. Did the assembly produce errors? Check the listing.
2. Did you trace the path with real addresses from the listing?
3. Did you reload after the last crash?
4. Is it a plain logic error — wrong jump target, missing instruction, a label
   truncated to six characters and colliding with another?

Nearly every "the emulator is wrong" conclusion in the inherited notes resolved
the other way. `references/errata.md` is a list of them.
