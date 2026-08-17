# Understanding paper tape formats

Converted working copy of the obsolescence.dev page
`pdp1-understanding-paper-tape.html`. **The HTML page is the canonical
source** (`/home/x/Documents/obso-site/pdp1-understanding-paper-tape.html`);
regenerate this file if the page changes. The format diagrams on the
page carry the byte-level detail; this file is the prose.

(The page opens with Samson at the CHM — "Mozart or Bach" — and points
to the Composers & Computers podcast for the pre-history of music and
computers.)

## Alphanumeric (symbolic) tape format

Source code is punched on tape in alphanumeric mode. Each line on the
tape consists of eight holes, encoding one character. The character
codes are **not 8-bit ASCII but 6-bit FIODEC**.

## Binary tape format

Binary tapes encode 18-bit words. For this, **three lines** on the
tape are used: when the PDP-1 reads a binary tape, it reads three lines
and constructs the loaded word from them.

## Anatomy of a tape

Any paper tape normally starts with an empty **leader** — no holes are
punched, and these lines are always skipped by the computer. After that
may come a title of human-readable lines punching out readable
characters. If this is a binary tape, a data block called the **RIM
loader** may follow: this tiny loader program loads the rest — the body
of the actual program. Right at the end of the tape comes an
instruction to jump to the start location of the actual program.

## Binary RIM blocks

The RIM loader is the self-loading block at the front of a RIM tape
(assembler output with the RIM loader included). Once loaded by READ
IN, it executes and loads the body, then hands over via the start
block. `tape_visualizer` marks RIM blocks in blue (an `R` at the `dio`
instruction, `aa` load address, then the three lines of the loaded
word). See `programming-introduction.md` (tape tools) and pdp1-assembly
`references/tape-formats.md` for what `-r` changes.

## Binary BIN blocks

The **BIN loader** is loaded in at the top of the memory map by the
hard-wired circuits behind the READ IN switch — in its details a very
neat trick worth studying. After the BIN loader is read, it starts
executing to load the rest of the tape. Once it hits the start block,
execution is transferred to the actual program.

Note that a binary tape does **not** have to have the BIN loader —
that merely makes it read data in more efficiently. **DDT is often
used to read binary tapes without a BIN loader.**

`tape_visualizer` marks BIN blocks in red (`B` at the block start, `ss`
start address, `ee` end address, `ccc` checksum at the end). Tapes can
be creative: one ET tape has two BIN blocks joined by a `jmp 1000` —
the first block loads and clears memory, then hands back to the BIN
loader, which proceeds to load the actual game.

## Alphanumeric tapes

Simpler: they may carry a human-readable title, but there is no BIN
loader or start block. What there might be — sometimes must be — is a
**STOP block** at the end of the punched data: octal code 013, the
STOP character, demarks end-of-file. Not all alphanumeric tapes have
it; it depends on the program they are intended for. **MACRO certainly
wants it.**
