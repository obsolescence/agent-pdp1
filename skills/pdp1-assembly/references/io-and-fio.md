# Typewriter, Test Word and Paper Tape I/O

## Status polling with `cks`

`cks` (`720033`) reads device status into IO. Poll it before every transfer —
there is no interrupt-driven path unless the sequence break system is enabled.

| Bit | Flag | Meaning when 1 |
|---|---|---|
| 17 | lps | light pen strobe |
| 16 | rbs | reader buffer has a character |
| 15 | tyo | typewriter output ready |
| 14 | tbs | typewriter input buffer has a character |
| 13 | punon | punch ready |
| 11 | sbm | sequence break mode active |

The idiom rotates the bit of interest into the sign position and tests it with
`sma`:

```asm
/ wait for typewriter output ready (bit 15)
outw,   cks
        dio tmp
        lac tmp
        ral 2s                  / bit 15 -> bit 17... then to sign
        sma
        jmp outw

/ wait for input available (bit 14)
inw,    cks
        dio tmp
        lac tmp
        ral 3s
        sma
        jmp inw
```

`cks` means *check status*. It computes no checksum, despite what some inherited
tables claim.

### Program flags instead of polling

A device completion pulse can set a **program flag**, which turns the wait into
two instructions and avoids reading and masking a status word:

```asm
        clf 1                   / clear program flag 1
        szf i 1                 / skip when flag 1 is SET
        jmp .-1                 / spin
        tyi                     / character is ready
```

`szf n` skips when flag n is clear; the `i` bit inverts it, so `szf i 1` skips
when it is set. Cheaper than the `cks` loop and it frees AC and IO, at the cost
of spending one of the six program flags. FLAP's `keyc` uses exactly this for
typewriter input.

Program flags are also the natural home for conditional breakpoints — see
`references/debugging.md`.

## `tyo` and `tyi`

| Mnemonic | Word | Direction |
|---|---|---|
| `tyo` | `730003` | IO bits 12-17 → typewriter |
| `tyi` | `720004` | typewriter → IO bits 12-17 |

Both operate on **IO**, not AC — a recurring slip is using `dio` where `dac` is
meant, or forgetting to move the character into IO before `tyo`:

```asm
        lac chr                 / FIO code in AC
        dac tmp
        lio tmp                 / into IO for tyo
        tyo
```

```asm
        tyi
        dio tmp
        lac tmp
        and m077                / mask to 6 bits
```

## FIO-DEC character codes

The Flexowriter uses a 6-bit code with **shift state**: the code for a letter is
the same in both cases, and case is selected by a preceding shift character.

| Code | Meaning |
|---|---|
| `072` | lower case shift (LCS) |
| `074` | upper case shift (UCS) |
| `077` | carriage return + line feed |
| `000` | space |

Shifts produce no visible output; they change the state until the next shift.

### Letters

| | | | | | |
|---|---|---|---|---|---|
| a `061` | b `062` | c `063` | d `064` | e `065` | f `066` |
| g `067` | h `070` | i `071` | j `041` | k `042` | l `043` |
| m `044` | n `045` | o `046` | p `047` | q `050` | r `051` |
| s `022` | t `023` | u `024` | v `025` | w `026` | x `027` |
| y `030` | z `031` | | | | |

### Punctuation

| Char | Code | Note |
|---|---|---|
| `,` | `033` | |
| `.` | `073` | |
| `-` | `054` | |
| `(` | `057` | |
| `)` | `055` | |
| `"` | `001` | |
| `'` | `002` | |
| `/` | `021` | in lower case |
| `?` | `021` | **same code**, in upper case |
| `!` | `005` | upper case |

**Code `021` is `/` or `?` depending on shift state** — the most common
character-output bug. Emit `074` before it if a question mark is wanted, and be
sure the state is restored afterwards.

`:` and `;` are not available; substitute `.` and `,`.

Code `005` renders as `∨` in some telnet clients and `!` on a real Flexowriter —
a client substitution, not a program error.

### Printing a string

```asm
/ strp = address of first word; string terminated by 777777
prstr,  dap prret
pslp,   lac i strp
        sad endm
        jmp prret
        dac chr
        jsp outch
        lac strp
        add one
        dac strp
        jmp pslp
prret,  jmp .

endm,   777777
```

One character per word is wasteful but simple. Three FIO codes pack into an
18-bit word if space is tight.

### Reading a line with echo

```asm
rdnam,  dap rdret
        law nbuf
        dac bufp
rdlp,   jsp inchr               / one FIO code into chr
        lac chr
        sad crlf
        jmp rdret
        jsp outch               / echo
        lac chr
        dac i bufp
        lac bufp
        add one
        dac bufp
        jmp rdlp
rdret,  jmp .

crlf,   077
```

**Size the buffer properly.** In `macro1_1`, space-separated zeros on one line
assemble to a *single* word, so a buffer written as four lines of ten zeros is
four words long, not forty. Input longer than that overwrites whatever follows
and produces corruption that looks like a logic bug elsewhere. Each word needs
its own line. See `references/macro1-assembler.md`.

## Test Word input

The 18 TEST WORD toggle switches on the console are the simplest interactive
input. `lat` (`762200`) reads them into AC.

`lat` is an **operate** instruction, not an IOT. Its two bits act in order: bit
10 clears AC, then bit 7 ORs in the test word. **[src]** That ordering is why
`lat` gives a clean reading even immediately after a `jsp` has left a return
address in AC — no masking needed.

Switch TW1 is the least significant bit (rightmost), TW18 the most significant.

### Edge detection

Reading `lat` every frame gives a level, not an event; a held switch would
trigger continuously. Compare against the previous reading:

```asm
        lat
        dac cursw
        lac lastsw
        cma
        and cursw               / bits that went 0 -> 1
        and bmsk                / restrict to the switches in use
        dac rising
```

Then require exactly one bit before acting — `rising & (rising-1)` is zero only
for a single-bit value:

```asm
        lac rising
        sub one
        and rising
        sza
        jmp reject              / more than one switch moved
```

### The first-call problem

The first reading has no previous value to compare against. Initialising
`lastsw` to zero makes the first non-zero reading look like a rising edge on
every set switch; initialising it from the switches means a switch already on at
startup can never be seen going on.

Neither works with a "is `lastsw` zero?" test, because `lastsw` legitimately
returns to zero later. Use a **dedicated flag**:

```asm
initfl, 0                       / 0 = not yet calibrated

input,  dap inret
        lat
        dac cursw
        lac initfl
        sza
        jmp inorm               / already calibrated
        law 1
        dac initfl
        lac cursw
        dac lastsw              / take baseline, act on nothing
        jmp inret

inorm,  ...                     / normal edge detection
inret,  jmp .
```

Clear `initfl` wherever the program state is reset.

### Computing a target address from a bit position

Find the set bit's index by rotating right and counting, then form the address:

```asm
        law board               / address of the table
        add ct                  / + index
        dap pcell
```

`law board` loads the *address*; `add (board` would add the literal-pool
reference, and `add board` adds the *contents* of `board`. This is a
three-way distinction that is easy to get wrong and produces a plausible-looking
wrong address rather than an error.

## Paper tape

| Mnemonic | Word | Function |
|---|---|---|
| `rpa` | `730001` | read one line, alphanumeric |
| `rpb` | `730002` | read three lines as a binary word |
| `rrb` | `720030` | read reader buffer into IO |
| `ppa` | `730005` | punch one line, alphanumeric |
| `ppb` | `730006` | punch binary |

These are the paper tape *reader* and *punch*. Inherited tables describing
`rpa`/`rpb` as "read printer" are wrong.

For loading programs the hardware READ-IN sequence is normally used instead of
programmed reads — see `references/tape-formats.md`.

## Sequence break

`esm` (`720055`) enters sequence break mode, `lsm` (`720054`) leaves it, `cbs`
(`720056`) clears the system. In a one-channel system a break stores AC, PC and
IO in locations 0-3 and jumps; the terminating indirect jump restores overflow,
extend state and PC. **[handbook]**

Most small PDP-1 programs poll instead. If sequence break is enabled, remember
that the `dap`-based return convention is not re-entrant — a break landing
inside a subroutine that is then re-entered will destroy the return address.
See `references/subroutines-and-dispatch.md`.
