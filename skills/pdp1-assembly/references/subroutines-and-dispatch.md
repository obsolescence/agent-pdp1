# Subroutine Linkage, Dispatch and Self-Modifying Code

The PDP-1 has no stack and no index registers. Subroutine return, array
indexing and table dispatch are all built out of instructions that rewrite other
instructions. This is idiomatic, not a workaround.

## How `jsp` actually works

`jsp Y` transfers PC into AC and jumps to Y. **It writes nothing to memory.**
The word at Y is untouched and executes normally as the subroutine's first
instruction. See `references/instruction-set.md` for the decoder trace.

Because PC has already been incremented past the `jsp` at transfer time, AC
receives the address of the instruction *after* the call. AC also carries
overflow in bit 0 and extend state in bit 1, so the return address must be
extracted with `dap` (address part only), never used as a whole word.

### The standard pattern

```asm
        jsp sub                 / call
        ...                     / control returns here

sub,    dap ret                 / splice AC's address part into ret
        ...                     / body
ret,    jmp .                   / dap rewrote this to jmp <caller>
```

`ret, jmp .` assembles a `jmp` whose address field points at itself; `dap`
overwrites just that field. The opcode stays `jmp`.

This is the pattern used throughout ICSS and Spacewar!. It is the DEC-standard
PDP-1 convention, not an emulator-specific accommodation.

### The `dac` variant

```asm
sub,    dac rt
        ...
rt,     0
        jmp i rt
```

Also correct: `dac` stores the whole AC, `jmp i rt` jumps through it. Slightly
slower (indirect fetch) and it stores the overflow/extend bits along with the
address, so prefer the `dap` form for consistency. Do not mix the halves —
`dap` + `rt, 0` + `jmp rt` jumps to whatever opcode bits happened to be there.

### What does *not* work

```asm
        jsp sub
sub,    0                       / stays 0 — jsp never writes here
        ...
        jmp i sub               / jumps through 0
```

This is the **PDP-8 `jms` convention**, not PDP-1. On the PDP-8, `jms Y` deposits
the return address at Y and begins execution at Y+1. The PDP-1's equivalent
instruction is `jda`:

```asm
        jda sub                 / AC → M(sub); PC → AC; jump to sub+1
sub,    0                       / receives the caller's AC (an argument)
        dap ret                 / and the return address is in AC
        ...
ret,    jmp .
```

So `jda` is the right choice when the subroutine takes an AC argument *and*
needs a return address. `jsp` is the right choice when it only needs the return.

Also broken: `dac ret` paired with `jmp ret`. That jumps to the *value* stored
at `ret`, executing the return address as an instruction.

### The fall-through trap

`jsp` returns to the instruction after the call. If a `jsp` is the last thing in
a routine, the return lands on whatever the assembler placed next — usually the
following subroutine.

```asm
/ WRONG
dwd1,   lac left
        jsp diagline
                                / nothing here — return falls into dwd2
dwd2,   lac right

/ RIGHT
dwd1,   lac left
        jsp diagline
        jmp dpret               / explicit continuation
dwd2,   lac right
```

Every `jsp` must be followed by the instruction that should run on return.
A blank line or comment is not one. This bites hardest when converting a `jmp`
call site (which expects no return) into a `jsp`.

### Re-entrancy

None of these patterns are re-entrant. The return cell is a fixed location, so a
subroutine cannot call itself, and cannot be called from an interrupt (sequence
break) that might occur inside it. If recursion is needed, the return addresses
have to be pushed into a table by hand.

## Computed GOTO dispatch

The general N-way branch. Each table entry is one word holding a `jmp`
instruction, so the index needs no scaling.

```asm
dispatch, dap dpret             / save return from jsp
        lac index               / 0-based selector
        add tblptr              / + address of the table
        dap dpgoto              / point dpgoto at the table entry
        lac i dpgoto            / fetch the jmp instruction from the table
        dap dpgoto              / splice its target into dpgoto
dpgoto, jmp .                   / go
dpret,  jmp .                   / handlers return here

tblptr, dwtab                   / data word holding dwtab's address

dwtab,  jmp case0
        jmp case1
        jmp case2
```

Points worth noting:

- `dpgoto` is rewritten in place on each call, so the dispatch is reusable.
- Handlers return with `jmp dpret`, not their own `jsp` bookkeeping.
- Getting the table's *address* into AC: `law dwtab` works and is one
  instruction. A data word (`tblptr, dwtab` then `add tblptr`) also works and
  reads more clearly at the call site. Both are fine.

### Conditional branches cannot be dispatched

This is a real architectural limit and shapes a lot of PDP-1 code. Skip
instructions take no address, and the `jmp` after them has its target baked into
the instruction word. You can compute the target of an *unconditional* jump; you
cannot compute which handler a `sza` should fall into.

Consequence: if N items each need their own conditional path, you write N copies
of the conditional. The *read* path can be collapsed with `dap` (below), but the
dispatch path has to be unrolled. Plan table-driven loops around this rather than
fighting it.

## `dap` self-modification

`dap` deposits AC's address part (bits 6-17) into the address field of the target
word, leaving the opcode alone. That makes it the machine's indexing mechanism.

### Computed store

```asm
        lac celladr             / address of the cell to write
        dap stloc               / splice it into the dac below
        lac value
stloc,  dac .                   / became dac <celladr>
```

### Computed load

```asm
        lac celladr
        dap ldloc
ldloc,  lac .                   / became lac <celladr>
```

### Walking a table of addresses

When a table holds *addresses* rather than values, `dap` removes the
load-through-temporary chain. Instead of:

```asm
        lac i wptr              / fetch cell address from the table
        dac tmp
        lac i tmp               / fetch the cell's value
```

splice the address straight into the load:

```asm
        lac i wptr              / fetch cell address from the table
        dap cload
cload,  lac .                   / became lac <cell> — fetches the value
```

Three instructions become two, and the temporary disappears. Over a scan of
24 cells this is the difference between ~70 and ~48 instructions.

### Indirection through a `dap`-fixed word

A word whose address field has been set by `dap` can be used as an indirect
pointer, because indirection reads bits 6-17 — the same field `dap` writes. The
opcode bits are irrelevant to the fetch.

```asm
        lac celladr
        dap pcell               / pcell's address field now = celladr
        lac i pcell             / reads M(celladr)
        ...
        dac i pcell             / writes M(celladr) — same cell
```

One caveat: indirection in normal mode is *multi-level*. If bit 5 of the word at
`pcell` happens to be set, the machine defers again. `dap` does not touch bit 5,
so keep the target word's opcode field free of it — assembling `pcell` as
`dac 0` or `lac .` is safe.

### When not to use it

A `dap`-fixed instruction is global mutable state at a fixed address. A
subroutine that patches itself cannot be called from two places with different
parameters interleaved, and cannot be re-entered. For genuinely parameterised
access, pay for the indirect chain through a variable:

```asm
sub,    dap ret
        lac i ptr               / ptr is an ordinary variable
        dac tmp
        lac i tmp
        ...
```

## Chaining unrolled cases

When per-item code is unrolled (because the dispatch cannot be computed — see
above), each item must hand control to the *next* item. Only the last falls
through to whatever follows.

```asm
/ item 0
c0,     lac .
        sza
        jmp c0occ
        dac emptyl
        jmp c1en                / → item 1, NOT the final check

/ item 1
c1en,   ...
c1,     lac .
        sza
        jmp c1occ
        dac emptyl
        jmp c2en                / → item 2

/ item 2
c2en,   ...
c2,     lac .
        sza
        jmp c2occ
        dac emptyl
        jmp done                / → final check (last item only)

c0occ,  ... / jmp c1en          / side exits rejoin the chain too
c1occ,  ... / jmp c2en
c2occ,  ... / jmp done

done,   ...                     / sees all three items
```

The failure mode is silent and specific: the aggregate check follows the item
code in source order, so an item that jumps straight to it *looks* like it
finished the loop. Everything after item 0 becomes dead code, and the aggregate
only ever sees one item's data. Every side exit — including the ones that just
bump a counter — has to rejoin the chain.

## Address shifts

Adding or removing a single word shifts every label after it. The assembler
recomputes all references correctly, so this is not in itself a bug — but the
entry point moves too. After any edit, re-read the entry address from the `.lst`
rather than reusing a remembered octal value.

For a program with a boot trampoline (`boot, jmp go` plus `start boot`), the
address to start at is the one the `start` directive assembled, which the
listing shows on that line.
