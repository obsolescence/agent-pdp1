# Programming the DEC PDP-1 — a quick way to get started

Converted working copy of the obsolescence.dev page
`pdp1-programming-introduction.html`. **The HTML page is the canonical
source** (`/home/x/Documents/obso-site/pdp1-programming-introduction.html`);
regenerate this file if the page changes. The figures on the page
(paper-tape format diagrams) are not reproduced here — see
`pdp1-understanding-paper-tape.html` for the text version.

Sections: the classical way · cross-compiling & PC data exchange ·
understanding paper tape · ET · MACRO · DDT · tape tools.

## Overview: the Classical Way

The programming cycle of a PDP-1 assembly programmer:

1. Enter and edit the source with a text editor, punching a paper tape
   with the source when done.
2. Compile the source tape with an assembler, punching a binary tape
   when done.
3. Load the binary tape to run it and see if there are bugs.
4. (Smarter) Load a debugger first, let it load the binary. The front
   panel is a debugging tool itself — both can be used at once.

The famous editor was TECO (lost to time). The preserved one is **ET**,
the Expensive Typewriter — easier to work with. The traditional
assembler is **MACRO** (roots on the TX-0, one of the first PDP-1
programs). **DDT** is the traditional debugger — the first debugger
ever, and remarkably pleasant to use.

    ET ---> source paper tape ---> MACRO ---> binary paper tape
    ---> (optionally in DDT) ---> load binary tape to test your program.

## Cross-compiling and data exchange with a PC

Two 21st-century alternatives to the classical way:

- Skip ET editing: edit on a PC, generate a source tape for MACRO on
  the PDP-1.
- Skip ET and MACRO altogether: cross-compile on a PC, load the RIM
  tape on the PDP-1.

Tool set included with the PiDP-1:

- `macro1_1` — the default cross-compiler.
- `encode_fiodec` — PC text file → source-code tape.
- `decode_fiodec` — alphanumeric tape → PC text file.
- `disassemble_tape` — disassembles a binary tape in various formats.
- `tape_visualizer` — visually inspect a paper-tape image file.

Tape extensions are not terribly informative: `.rim` = self-loading
program tape, `.bin` = binary data (may or may not be self-loading),
`.pt` = anything. Use `tape_visualizer` to see what a tape contains.

## Understanding paper tape

- Source code is punched in alphanumeric mode: each line is eight
  holes encoding one character — **6-bit FIODEC**, not 8-bit ASCII.
- Binary tapes encode 18-bit words: the reader takes **three lines**
  per word and constructs the word from them.
- Any tape normally starts with an empty **leader** (no holes — always
  skipped). A human-readable title may follow. A binary tape may carry
  a **RIM loader** block — a tiny loader that loads the rest of the
  body, ending with an instruction jumping to the program's start.
- The **BIN loader** is loaded at the top of memory by the hard-wired
  circuits behind the READ IN switch; it then loads the rest of the
  tape and transfers to the program at the start block.
- A binary tape need not have the BIN loader — DDT is often used to
  read binary tapes without one.
- Alphanumeric tapes may (sometimes must) end with a **STOP block**:
  octal 013, the STOP character, marks EOF. MACRO certainly wants it.

## Editing your source code: ET

ET is a modal editor — command mode and text mode, much like VIM.
Originally an off-line typewriter punched the tape; ET was the
expensive option because it occupies the computer. DEC renamed it "the
PDP-1 Symbolic Tape Editor".

Minimal instructions:

1. Mount `et.rim` in the paper tape reader.
2. Set Sense Switches 2 and 6 — SS2 lets ET number lines when editing;
   SS6 suppresses parity errors.
3. Press READ IN.
4. Once loaded, print the text buffer with `w` — you see one empty
   line. Press `a` and just type away. Backspace deletes the last
   character and overtypes it (literally overtypes on paper — ET works
   on a typewriter, not a video terminal; in the buffer it is fine).
5. Done entering text? Backspace at the start of a new line → command
   mode. `w` prints the text for review.
6. Editing commands: `ni` inserts a new line before line i; `a`
   appends; `nc` replaces (changes) line n; `nd` deletes line n.
7. ET summary (page 1, page 2) and the last pages of the full ET
   manual cover the rest. **There were many versions of ET — not every
   manual command will work.**
8. Saving: make sure SS6 is set, type `p` to punch the tape, `s` to
   add the STOP code at the end. On the PiDP-1, "take the tape out of
   the punch" = save via the web/GUI interface, or pull the USB stick.
9. Reloading: mount the tape, `k` to kill (empty) the buffer, `r` to
   read it, `w` to type it all out for review.

### The recommended first program: CIRCLE

Displays a circle on the Type 30. In ET, use TAB to align instructions
into the second column. `[backspace]` at a newline leaves text mode.

    CIRCLE
    100/
    go, lac x
    lup, cma
     sar 4s
     add y
     dac y
     lio y
     sar 4s
     add x
     dac x
     dpy
     jmp lup

    x, 200000
    y, 0
    start go

Reading the source: first line is the program name; second line is the
start address in memory. The program is an endless loop (`jmp lup`);
x and y are the display coordinates. The last line is the **start
block** — MACRO assembles a RIM tape by adding the RIM loader at the
front; `start go` tells it where to hand over execution once loaded.

No floating point, sine or cosine — see "Integer Circle Algorithm" for
democoding ideas. DEC suggested this as the first step into PDP-1
programming.

## Compiling your source code: MACRO

Make sure **all switches are off** — the 18 Test Word switches, the 17
Address switches, and the 6 Sense Switches. They have a meaning to
MACRO.

1. Mount `macro.rim`, press READ IN.
2. Mount your source tape, press CONT. You see `Pass 1` on the
   typewriter.
3. Mount the source tape again, press CONT. You see `Pass 2` and the
   punch starts outputting the binary tape.
4. Press CONT again — punches the start block to the end of the tape.
5. Take the binary tape out of the punch (save it).

Basic operation only — the MACRO manual has much more.

To run: mount the just-created tape and press READ IN. If everything is
right, the Type 30 displays the circle. Alternatively load DDT (next
section), let it load your program tape, and debug.

## Debugging your program with DDT

1. Mount `ddt.rim`, press READ IN.
2. Mount the tape MACRO generated (or any small binary tape).
3. Type `Z` — DDT clears all memory (keeps an overview).
4. Type `Y` — DDT reads in your binary tape.
5. Type `100/` — inspect your program (compiled to start at 100); DDT
   shows the `lac 113` instruction.
6. Backspace to keep reading lines; at 112 you hit the `jmp` that
   loops back.
7. Type `100G` to run from 100. Press the front panel STOP to stop it.
8. Set address **6000** on the front panel (switches 110 000 000 000)
   and press START — DDT lives at 6000, so this returns you to DDT.

### Writing small programs in DDT

The helloworld program, entered directly in DDT:

    200/ lac i 212
    201/ cli
    202/ rcl 77
    203/ tyo
    204/ sza
    205/ jmp 202
    206/ idx 212
    207/ sas 217
    210/ jmp 200
    211/ hlt

Exact keystrokes:

- Return to start on a new line.
- Type `200/` — DDT prints ` 0 ` (current content). Type
  `lac i 212` Backspace to enter the instruction and advance.
- DDT prints `201/ 0 `. Type `cli` Backspace. Continue until `hlt` is
  entered at 211.
- Address 212 is a variable — initialize it: `212/`, DDT shows ` 0 `,
  type `0` Return. (Not strictly necessary.)
- Store the string 'Hello' from 213: `213/`, DDT shows ` 0 `. Type
  `hel"` Backspace, `low` Backspace, `orl"` Backspace. The double
  quote stores three characters as one word. It only accepts exactly
  three characters (no spaces).
- Last letter 'd': fiodec code for d is octal 64. Type `216/`, then
  `640000` Return.
- Inspect: `200/` then Backspace through the lines. At 212 the stored
  value can't disassemble — DDT shows the number. At 213 DDT types
  `law 6543` (it is a string, not an instruction): type `~` and DDT
  shows ` hel `. Backspace and `~` again for the rest.
- Run: `200G` — prints `helloworld` and halts. The typewriter still
  accepts keystrokes, but that is misleading: you type to yourself,
  DDT is not listening. Set the address word to 6000 and press START
  to get DDT back.
- Re-running: reset the variable at 212 to 213 first:
  `212/213` Return.
- Exercise: make it print a modern "Hello, world" instead of the very
  1950s 'helloworld'.

### Saving your program

1. Note the end address (216 for the original; more if the string is
   longer).
2. Make sure the variable at 212 is initialized to 213.
3. Clear the punch.
4. Type `L hello` Return — a readable header; Return tells DDT this is
   a binary tape **with RIM loader**, so it autoboots when mounted.
   The punch prints `HELLO`, then the RIM loader code.
5. `200<216D` — DDT dumps the program to the punch.
6. `200J` — completes the RIM tape with a start block (the PDP-1 will
   know where to start execution after loading).
7. Save the tape, clear the punch, mount the saved tape, READ IN.

That is the entire development cycle on a 1959 DEC PDP-1 —
interesting, worthwhile, historically significant, but not completely
comfortable from a 21st-century perspective — hence cross-compiling.

## Tape tools, cross-compiler, disassembler

- `encode_fiodec text-input-file.mac tape-output-file.pt` — put text
  on an alphanumeric tape (for MACRO or anything else — Lisp and
  FORTRAN too). Answer **y** when asked about the STOP trailer, or
  MACRO will not know when to stop reading.
- `macro1_1 text-input-file.mac` — cross-compile straight onto a
  bootable RIM binary tape; load it and it runs.
- `disassemble_tape binary-tape` — disassemble in various formats;
  run it bare to see its options.
- `tape_visualizer paper-tape-file.pt` — visually inspect a tape image
  (you can't hold the physical tape). Decodes alphanumeric tapes too.
  RIM loader binary data is blue, BIN red; `R` marks a RIM `dio`
  instruction (the following `aa` is the load address, the next three
  lines the loaded word); `B` marks a BIN block start (`ss` start, `ee`
  end, `ccc` checksum). Tapes can be creative: one ET tape carries two
  BIN blocks joined by a `jmp 1000` — the first block loads and clears
  memory, then hands back to the BIN loader for the actual game.
