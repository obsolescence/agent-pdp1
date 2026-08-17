# PDP-1: the birth of democoding and videogaming

Converted working copy of the obsolescence.dev page
`pdp1-democoding-and-gaming.html`. **The HTML page is the canonical
source** (`/home/x/Documents/obso-site/pdp1-democoding-and-gaming.html`);
regenerate this file if the page changes.

This page is mostly a pointer to masswerk.at (Norbert Landsteiner's
PDP-1 reconstructions and documentation) — and that is all it needs to
be: everything about the history and the practical craft of PDP-1
programming is there.

## The birth of democoding: the PDP-1 display hacks

The earliest examples of computer graphics coding emerged on the PDP-1
as the 'display hacks':

- **Snowflake** — a recursive drawing routine producing intricate
  crystalline figures.
- **Minskytron** — Marvin Minsky's experiment in feedback loops and
  dynamic geometric transformations.
- **Munching Squares** — a hypnotic bitwise graphics pattern; became a
  classic demo on many later computers.
- **Mapes' Graphical Fun** — David Mapes, Lawrence Livermore PDP-1.

They are pretty because of the Type 30 slow-phosphor tube, but also
historically important: the beginning of interactive computer art,
foreshadowing the demoscene, computers as an artistic medium.

These programs are interesting to study and take little time — they
are tiny in size. They are interactive: the **TW switches change their
patterns and behaviour**.

Masswerk entry points: Minskytron; Snowflake archaeology; Mapes'
Graphical Fun; interview with David Mapes.

Practical note: tape **dpys5** (Peter Samson, made for the CHM)
contains Snowflake (**start address 0**), Munching Squares (**start
address 0, set TW switches whilst the program is running**) and
Minskytron (**start address 500, set TW switches before start**).

## The birth of videogames: Spacewar

PDP-1 graphics culminated in **Spacewar**, the first-ever computer
video game — and the reason the PiDP-1 has game controllers.

- Masswerk: *spacewar history* — the definitive introduction to the
  game and its history.
- Graetz' *1981 review* (one of the authors) — perspective from
  inside the project.
- *Inside spacewar* — Landsteiner's full code analysis; if you want
  PDP-1 programming skills, there is no better way than reading this.
- **ICSS** — Landsteiner's backport of Computer Space (the first
  arcade game) to the PDP-1, written in great detail; the perfect
  companion.
- **PDP-1 Pong** — backport by Hrvoje Čavrak (source code available);
  a later game, in its original not even a computer game, but Al
  Alcorn was directly inspired by seeing spacewar.
- **PDP-1 Lunar Lander** — 2026 backport by Michael Gardi of the
  PDP-11 Lunar Lander from the 1970s; the PDP-1 turns out to have
  enough power to improve upon the PDP-11 original.
- History: Levy's *Hackers* (some chapters online) for the
  human-interest side of the PDP-1 saga; Graetz's summary: it's the
  World's First Toy Computer.

## Practical tour material

Tapes present on this machine (see the pdp1-tutor Tour 4 stub for the
start-address crib and pdp1-type30-vision for reading the display):
`dpys5-demo.rim` (Snowflake / Munching Squares / Minskytron),
`spacewar48.rim`, `pong.rim`, `lunar_lander.rim`, `mapes.rim`,
`minskytron.rim`, `minskytron_ii.rim`, `munch.rim`.
