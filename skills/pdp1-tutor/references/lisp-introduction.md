# PDP-1 Lisp — a hands-on start

Converted working copy of the obsolescence.dev page
`pdp1-lisp-introduction.html`. **The HTML page is the canonical
source** (`/home/x/Documents/obso-site/pdp1-lisp-introduction.html`);
regenerate this file if the page changes. Marked WORK IN PROGRESS by
the author ("amended as I learn PDP-1 Lisp myself"); feedback via the
PiDP-1 Google Group.

## PDP-1 Lisp: introduction

- Lisp was developed in 1958 by John McCarthy at MIT — a high-level,
  symbolic programming language designed for AI research, pioneering
  recursion, symbolic expressions and automatic storage management.
- The PDP-1 version was implemented in 1960 by **Peter Deutsch** — at
  the time a 14-year-old high-school student (son of an MIT
  professor). Highly minimalist and efficient for the tiny PDP-1.
- He invented the **read-eval-print loop (REPL)** along the way — the
  first-ever interactive programming environment, and central to Lisp
  to this day. PDP-1 Lisp evolved Lisp from a punch-card-loaded
  theory into a practical interactive tool.
- Knowledge of Lisp is not required for the quick start — this page
  shows how Lisp works on the PDP-1.

Manuals:
- **PDP-1 Lisp manual** — practical operation and language
  differences (essential for details).
- **Lisp 1.5 Programmer's Manual** (IBM 7090) — Deutsch's target;
  good overview of Lisp 1.5 in general.
- Recommended next: *The Programming Language LISP: Its Operation and
  Applications* (opens up Lisp on the PDP-1), then *Anatomy of Lisp*
  (John Allen, early Lisp background).

## Bringing up Lisp

1. **Set the Extend switch.** Be sure to set Extend down again for
   other PDP-1 programs — **READ IN will fail for regular programs
   with this switch set**, a major cause of confusion.
2. Mount the `lisp.rim` tape, press READ IN.
3. TW switches to **7750** — upper memory address for Lisp storage.
   Press CONTINUE.
4. TW switches to **400** — length of the push-down list. Press
   CONTINUE.
5. Set **Sense Switch 5** — enable typewriter input. Press CONTINUE a
   third time. (Without SS5, input comes from a freshly inserted paper
   tape — so you can mount a tape with Lisp functions instead.)
6. **Address switches to 0004, always.** After running a Lisp program
   you press START then CONTINUE to get back into Lisp.
7. Typos and errors make Lisp halt — that is normal. Press START,
   then CONTINUE (address switches at 4).
8. Lines are **not** entered by Return — close each line with a
   **space**. E.g. `oblist[Space]` shows which atomic symbols are
   defined.
9. Before typing anything in, check Lisp is still running: enter
   `nil`. Lisp responds with a second `nil` on a new line. If not:
   START, then CONTINUE. Make it a habit — it is also the best way to
   start on a new line.
10. Arithmetic: `(plus 1 2)` outputs 3 — note **'plus', not '+'**.
    `(times 4 4)` outputs 20 — because 20 octal is 16 decimal.
11. A little program (use Return and TAB when entering it):

        (prog (a b)
         (setq a 4)
         (setq b 4)
         (plus a b)
         (return (plus a b)))

    ...closed with a space. Returns 10 — 4+4=10 in octal.

## Loading and saving

### Paper tape input

Saving functions is not built into Basic Lisp — you first load such a
function from paper tape (this is also just the regular way of loading
any Lisp code):

1. Mount the alphanumeric tape `lisp-defs.pt`.
2. Set SS5 down — straight away the tape gets read in.
3. Newly loaded functions appear in the typewriter output:
   `zerop`, `pdef`, `count`.
4. Set SS5 up again for typewriter input.
5. Press START, then CONTINUE (address switches at 4).

### Make a test tape

`test.lisp` on your laptop:

    (rplacd (quote tt) (quote
     (expr (lambda ()
      (prog ()
       (print (quote hello))
       (terpri)
       (return 5))))))
    [space]

The last line must end with a space to terminate the function.

- `encode_fiodec test.lisp test.pt`
- Mount `test.pt`; SS5 down — the tape gets read in. Output:
  `tt`, `hello`, `5`.
- SS5 up; START + CONTINUE.
- Inspect the loaded program: `(print (cdr (quote tt)))`.

### Paper tape output (saving a function)

`(print (cdr (quote tt)))` shows the body of the program, but it does
**not** output the function definition — you cannot rebuild the
function from it. Use `pdef` (loaded from `lisp-defs.pt`):

1. Turn up **Sense Switch 3** — output goes to the punch instead of
   the typewriter.
2. Type `(pdef tt)`, end with the trailing space as always — your
   function punches out to tape.
3. Turn down SS3 to return to typewriter output, and save the tape.

### Closing remark

PDP-1 core memory is non-volatile: after a power cycle everything is
still in memory — no need to bring up Lisp again from tape. Set the
address switches to 4 and press START, then CONTINUE.

Footnote: a more extensive function library exists at
`https://bitsavers.org/bits/DEC/pdp1/papertapeImages/20031216/lisp/lispFunctions.bin`
(as yet untested here; many useful functions).

## Loading DDT & mixing assembly in Lisp programs

Per the PDP-1 Lisp manual: set a **lower top address** for Lisp so
there is room at the top of memory for DDT to live in, then jump from
Lisp to DDT using the front panel START switch.

## Agent-side expertise

Agent-side Lisp expertise, copied from the read-only
`/home/x/Documents/obso-site/pidp1-sw/`: `references/lisp.md`,
`references/lisp1_5.md`. Not user-facing tour material.
