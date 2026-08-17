# The Assemblers

Everything here that is marked **[src]** was read out of
`pidp1/src/macro/macro1_1.c` or `pidp1/src/monas/monas.c`. **Syntax rules do not
transfer between assemblers** — check which one is in play first.

## macro1_1

Lineage: MACRO8 (Messenbrink) → MACRO7/MACRO1 (Supnik) → reworked by Phil Budne.
That ancestry matters: the bundled manual page still carries PDP-8 text, and its
worked error example uses `TAD I DUMMY`, an instruction the PDP-1 does not have.
Do not trust the prose in `MACRO1_PROGRAMMING_GUIDE.md`; trust the symbol table
in the source.

### Canonical program layout

One picture of a valid macro1_1 source:

    / comment                  first line is the tape title — never assembled
go,     law 0
        add one                named data words, never `(` literals
        dac s5
        hlt
        consta                 pool punched here — after the references
s5,     0
s1,     0
        start go               LAST — punches the JMP transfer word, the
                               entry point; anything after it never
                               reaches core

Three rules, mechanisms documented below:
- First line = title. Start the file with a `/` comment.
- `consta` must follow the references it pools.
- `start` goes last: it punches the entry transfer word, and the line
  after a processed `start` is eaten as a new title.

### Invocation

```bash
macro1_1 -r program.mac
```

Just the source file. Output `program.rim` and `program.lst` land in the
**current working directory**, not next to the source and not in any configured
output directory. Passing explicit output or listing paths is a reliable way to
produce confusing errors and zero-byte files.

| Flag | Effect |
|---|---|
| `-r` | emit pure RIM format (DIO+data pairs). Required for the emulator's `l` command |
| (none) | emit block format with a bootstrap loader — for READ-IN |
| `-d` | dump symbol table |
| `-x` | cross-reference |
| `-m` | show macro expansions |
| `-p` | write permanent symbol table |
| `-s` / `-S file` | write / read a symbol tape |

Because output goes to the cwd, assembling from a `sources/` subdirectory leaves
the new tape there while the loader keeps reading the old one from the parent.
When a change appears to have no effect, compare timestamps before anything else.

### The first line is eaten

```c
processLine() {
    if (!list_title_set) {
        strcpy(list_title, line);
        if (list_title[0]) {
            list_title_set = TRUE;
            fprintf(stderr, "%s - pass %d\n", list_title, pass);
        }
        return;                 /* <- line is never assembled */
    }
```
**[src]** `macro1_1.c` around line 1168.

The first line of the file becomes the tape title and is **not assembled**. Code
on it vanishes silently and any label it carries is undefined. Always open a
source with a `/` comment.

Two details fall out of the same code:

- The guard is `if (list_title[0])`, so a genuinely *empty* first line does not
  consume the slot — the next non-empty line becomes the title instead.
- `start` sets `list_title_set = FALSE` again, so the line following a `start`
  is also eaten as a new title. This exists to allow several tapes concatenated
  into one file.

### What `start` really does

```c
start_addr = getExprs() & ADDRESS_FIELD;
printLine(line, 0, start_addr, LINE_VAL);
punchTriplet(JMP | start_addr);
...
list_title_set = FALSE;
return FALSE;
```
**[src]** `macro1_1.c` around line 2915.

`start label` punches a JMP transfer word **at that point in the tape**. The
return value is discarded by the caller (`macro1_1.c:1310`), so *assembly
continues* — this is not an end-of-file directive, despite what inherited notes
say.

The practical effect is nonetheless "put `start` last", but for a more useful
reason: anything assembled after it is punched *after* the transfer word, and
`readrim` stops at the transfer word. The data is in the file, it resolves fine
in the listing, and it never reaches core. Combined with the title-eating above,
the line immediately after `start` disappears entirely.

Knowing the mechanism tells you what the symptom looks like: not an assembler
error, but a program whose trailing tables are all zero at run time.

### Symbols are 6 characters

```c
#define SYMLEN 7                /* 6 chars + NUL */
while(from < term && to < SYMLEN-1) ...
```
**[src]**

Characters past the sixth are discarded silently. `dwdiag1` and `dwdiag2` are
one symbol and produce a duplicate-tag error; worse, near-misses that *don't*
collide can still cross-link two intended-distinct names. Keep labels to six
characters and the whole class of problem disappears.

### Syntax rules

- **Lowercase mnemonics.** Uppercase is treated as an undefined symbol.
- **One instruction per line.** The comma separates a label from its
  instruction; it does not separate instructions.
- **Space-separated values on one line are summed, not stored as several
  words.** `buf, 0 0 0 0` assembles to a *single* word containing 0. A 40-word
  buffer needs 40 lines. This is a genuine memory-corruption source: a buffer
  four words long where forty were intended will overwrite whatever follows it.
- **`=` takes no spaces.** `nx1=mtb nob` is fine; `table = 1000` fails with
  "undefined symbol" plus "illegal equals".
- **Comments are `/`.** A whole-line comment works anywhere. After code, the
  slash must follow a **tab**, because `expr/` at the start of a statement is
  the location-setting syntax (`700/` sets the location counter to 700) and the
  parser looks ahead for it. Real-world style is `\tlac x\t\t/comment`.
- **The location counter starts at 4**, the RIM bootstrap convention. The first
  assembled word lands at `00004` unless a `nnnn/` location set says otherwise.
- **Never use `expunge`.** It clears the entire symbol table including the
  built-in opcodes, so every instruction after it fails in pass 2.
- **Numbers are octal.** `law i 20` loads −16 decimal; a loop counter
  written `20` silently runs 16 times. `decimal`/`octal` switch the radix.
  **[verified 2026-08-16]**
- **Never name a label `i`.** `i` is the permanent indirect modifier
  (value 0010000); a user label with that name silently shadows it —
  `lac i ptr` then assembles as a DIRECT reference to `(i+ptr)` with no
  error, and `law i 20` becomes `law (i+20)`. **[verified 2026-08-17:
  label `i` at 00004 → `lac i 20` = 200024 (direct), `law i 20` =
  700024; without the label both are correct]**

### Macros

Both spellings work:

```asm
define swap rcl 9s rcl 9s term

define xincr X,Y,INS
        lac Y
        INS .ssn
        dac Y
        lac X
        INS .scn
        dac X
        term
```

Parameters are positional. `term`, `terminate` — the source matches on the first
four characters (`strncmp(termin, "term", 4)`). **[src]**

`repeat N, expr` evaluates the expression N times at assembly time — used for
unrolling and for bit-doubling constants (`repeat 6, B=B+B`).

`constants` and `variables` mark the literal and variable blocks. `clear a, b`
zeroes an address range at load time, far cheaper than a clear loop.

### Literals: the `(` syntax — do not use

`add (5` is a literal: the assembler pools the value and references the
pool slot. The pool is only punched when an explicit `consta` pseudo-op
follows the references; the "implied constants" path in the source is dead
code (runs before pass 2, count still 0). Without `consta`, `add (5`
assembles to `add 000000` and every literal reads 0 after `l` — silent
wrong math, same in `-r` and block modes. **[verified 2026-08-17:
no-`consta` → s5=0/s1=0 in both modes; with `consta` → s5=5/s1=6]**

Do not write literals; use named data words (`one, 1` ... `add one`), the
style the guides recommend. When reading old code, `(x)` is a pooled
constant, not indirection — the pointer form is `lac i ptr`.

## monas

Angelo Papenhoff's own assembler, ~1000 lines of C, and his preferred one.

- Case-insensitive.
- No tape-banner rule — the first line is ordinary source.
- Macros via `m4` rather than a built-in macro processor.
- Emits **BIN format with a built-in RIM loader**. Load it with the emulator's
  `r` command plus READ-IN, **not** `l` — `l` expects pure RIM from
  `macro1_1 -r`.
- Defines `mul`/`div` and `mus`/`dis` and `spa`/`sma`, same values as
  `macro1_1`. **[src]**

## am1

A separate cross-assembler using C-preprocessor conventions.

| | macro1_1 | am1 |
|---|---|---|
| comments | `/`, tab-prefixed after code | `//` anywhere |
| macros | `define ... term` | `#define` with `\` continuation |
| statement end | newline | `;` |
| `start` | `start go` (label) | `start 500` (numeric) |
| RIM output | `-r` | `-m` |

## `mul`/`div` need no equate

Both `macro1_1` and `monas` define all four mnemonics: **[src]**

```c
{ DEFFIX, "mul", 0540000 },
{ DEFFIX, "mus", 0540000 },      /* for spacewar */
{ DEFFIX, "div", 0560000 },
{ DEFFIX, "dis", 0560000 },      /* for spacewar */
```

`mus`/`dis` are the aliases, kept for Spacewar! sources. The `mul=mus` /
`div=dis` equate that older notes place at the top of every file is a harmless
no-op. Whether those opcodes *behave* as full multiply or as step instructions
is a runtime property of the machine (the EAE), not of the assembler — see
`references/arithmetic.md`.

## Reading a `.lst` listing

The listing is the authority on what was assembled. Columns:

```
  83 00114 700015      go,     law pstr
   |    |      |
   |    |      +-- assembled 18-bit word (octal)
   |    +--------- address this word occupies (octal)
   +-------------- source line number
```

**The address column is not the operand.** Reading it as one produces exactly
the "my label resolved to its own address" report that appears in inherited
notes — `dwvline, dac dwlret` at address 1053 was read as `dac 1053`. A two-pass
assembler does not resolve the same symbol to different values depending on how
often it has been referenced; if the listing appears to show that, re-read the
columns.

To find an entry point:

```bash
grep 'start ' program.lst      # the assembled word on that line is the address
grep 'go,'    program.lst      # or read the address column of the label
```

Error markers appear inline with a two-letter code and a caret under the
offending item, and undefined symbols are prefixed `?` in the symbol table,
redefined ones `#`. Check for these before anything else — a program that
"doesn't run" often did not assemble cleanly.
