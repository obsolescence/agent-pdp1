---
name: pdp1-type30-vision
description: Use when analyzing Type 30 display output on a PiDP-1 — capture, ASCII grids, point queries, assertions with the pdp1_dpy tool.
version: 1.0.0
---

# PDP-1 Type 30 Display Analysis

Uses tool `scripts/pdp1_dpy` to capture the Type 30 display stream (port
3400, fanned out per pdp1-plumbing), keep a
persistent snapshot, and ask
cheap, repeatable questions about what is on the screen: stats, ASCII
grids, point queries, region counts, assertions, PNG renders.

The tool is in this skill — Python 3 stdlib, no dependencies, no fixed paths.

Important rule, do not violate:
Never dump the raw Type 30 display stream into context — always
capture through this tool's snapshot. (The emulator fans 3400 out to
4 clients, so the agent capturing does not disturb pdp1_periph.)

If the screen is DARK (zero points), that is a real observation — but
the WHY (display halted, program never started, beam off) is
root-cause work: see pdp1-debugging.


## Requirements & portability

- Snapshot path: `--snapshot FILE`, else env `PDP1_SNAPSHOT`, else
  `$TMPDIR/pdp1_dpy.snp` (falling back to `/tmp`). Everything overridable.

## Snapshot rules (read this first — the contract)

- `-r` is the ONLY write: it captures fresh and replaces the snapshot.
  without `-r` you will work on the previous snapshot, which might be stale!
- ask follow-up questions without `-r`:
  (stats/grid/point/region/expect/png/diff) READ the existing
  snapshot. Without one they error (exit 1): `no snapshot at ... — run
  with -r to capture`. There is NO auto-capture.
- Repeat questions on one snapshot is the normal pattern: capture once,
  ask many things. The snapshot persists until the next `-r`.
- Every answer prints the snapshot identity + age line:
  `snapshot 14:03:22 (0.5s, 112 words, 3 pts, 2.1s old)` — staleness is
  visible, refresh is deliberate.

## CLI

```
pdp1_dpy display [-r] [--secs N] [--snapshot FILE] [--host HOST] [--port PORT]
                 [--stats] [--grid [N]] [--point X,Y ...] [--region X1,Y1,X2,Y2]
                 [--expect SPEC] [--png] [--bbox] [--style binary|pattern]
                 [--frames N] [--against FILE] [--save FILE] [--out FILE]
                 [--demo] [--self-test]
```

| Flag | Meaning |
|---|---|
| `-r` | capture fresh snapshot (the only write; composes with any question) |
| `--secs N` | capture window, default 0.5 (with -r only) |
| `--snapshot FILE` | use FILE as the snapshot for this run (must exist unless -r) |
| `--host` / `--port` | display stream endpoint (default 127.0.0.1:3400) |
| `--save FILE` | copy the current snapshot to FILE (archive; needs an existing snapshot) |
| `--stats` | summary: unique points, extent, 8x8 occupancy (DEFAULT question) |
| `--grid [N]` | ASCII grid, N columns (default 64). N=40 cheap, 64 default, 100 detail |
| `--point X,Y` | ON/OFF (+ intensity); repeatable — one snapshot, N answers |
| `--region X1,Y1,X2,Y2` | print the point count in the rectangle (0 = none) — a QUERY, not an assertion |
| `--expect SPEC` | assertions, `;`-separated, all must pass: `cell=X,Y` (must be lit), `same-as=FILE` (fingerprint match). Exit 2 on failure |
| `--png` | write a green-phosphor PNG (512x512; `--bbox` crops to content; `--out FILE` sets the path, default $TMPDIR/pdp1_dpy.png) |
| `--bbox` | fit grid/PNG to the content extents instead of the full display |
| `--style` | `binary` (default: `*` and space) or `pattern` (geometric glyphs) |
| `--frames N` | grid as N time slices (flipbook — motion) |
| `--against FILE` | 3-state diff grid vs another snapshot: `X` new, `.` gone, ` ` unchanged |
| `--demo` | run the question against the bundled demo capture (no machine needed) |
| `--self-test` | run the golden fixture suite, PASS/FAIL per check, exit 0/1 |

Exit codes: `0` ok · `1` connection / no data / missing or corrupt
snapshot · `2` --expect failed.

## Grid glyphs

`--style binary` (default): `*` = cell has points, ` ` = empty. Highest
contrast, best for shape reading. `--grid N` sets the grid width in
columns; height derives from the region's aspect ratio. Row 0 = top of
screen.

`--style pattern`: each glyph is a deterministic function of THIS cell's
point statistics (count, sigma_x, sigma_y, covariance sign) — geometry,
never semantics. The tool never labels anything; the reader recognizes
structure from the pattern:

```
' '  empty
'.'  sparse (1-3 points)
'-'  horizontal stroke      '|'  vertical stroke
'/'  '\'  diagonal strokes (|rho|>0.7 — sign of covariance picks the slope)
'+'  cross / solid / arc (many points, no dominant orientation)
'*'  tight cluster / point source
':'  '#'  scatter/fill, by density
```

Thresholds are locked constants in `_cell_glyph`; calibrated against the
golden fixtures. If a real display misreads, tune there and re-run
`--self-test`.

## Workflows

Triage (cheapest first):

```
pdp1_dpy display -r --stats          # fresh capture + where is content?
pdp1_dpy display --grid 64           # what does it look like? (~1k tokens)
pdp1_dpy display --point 100,900     # is THIS lit?
pdp1_dpy display --region 0,0,511,511  # how many points in that quadrant?
```

Zoom (overview -> region -> detail):

```
pdp1_dpy display --region 0,512,512,1024 --grid 100
pdp1_dpy display --grid 100 --bbox --style pattern
```

Motion / change:

```
pdp1_dpy display -r --grid --frames 6        # flipbook of fresh capture
pdp1_dpy display --grid --against /tmp/old.snp   # what changed since?
```

Scripted tests (humans + agent):

```
pdp1_dpy display -r --expect "cell=30,45; same-as=/tmp/known-good.snp"
# exit 0 = display provably matches expectation; 2 = assertion failed
```

Archiving:

```
pdp1_dpy display --save /tmp/tac13-pre-move.snp   # copy, don't rename
pdp1_dpy display --snapshot /tmp/tac13-pre-move.snp --grid   # read it later
```

## Testing the tool itself

- `pdp1_dpy display --self-test` — golden fixture suite, no machine
  needed, exit 0/1.
- `pdp1_dpy display --demo --grid --style pattern` — tool tour.
- Regenerate fixtures (e.g. after threshold changes) with
  `python3 scripts/make_fixtures.py` — deterministic geometry; the
  suite's expected values (point counts, glyphs) live in `self_test()`.

## Layout

```
scripts/pdp1_dpy          the tool (single file, stdlib only)
scripts/make_fixtures.py  regenerates the golden fixtures
test/fixtures/*.snp       golden captures (tictactoe, cube, scatter, empty, demo)
```

## Pitfalls

- A connected-but-silent display is a VALID capture: 0 words saves fine,
  stats reports 0 points. That is a real observation ("display is dark"),
  not an error — connection problems are the exit-1 case.
- dt=511 words are escape markers; the next word is a raw delay value,
  never a point. Null words (x=0,y=0,intensity=0) are timekeeping — skipped.
- Coordinates are display space (0-1023, y up, as in the protocol).
  Grids flip y so row 0 = top, like the real scope.
- The flipbook slices by WORD COUNT, not wall-clock — fine while the
  display list repeats continuously, which it always does when running.
  Reading the slices: frames each carrying ~the full point count are
  whole pictures at different times (motion evidence); frames with
  fractions summing to the total are chunks of ONE pass (drawing
  sequence — no motion claim). For definitive motion, use two
  time-separated `-r` captures and `--against`.
- Pattern glyphs are inferences from statistics, not ground truth: a
  sparse crossing can look diagonal. When the answer matters, verify with
  `--point`/`--region` or `--expect`.
- The snapshot lives in $TMPDIR by default: shared machines may collide —
  use `--snapshot` or `PDP1_SNAPSHOT` per user.

## Provenance

- Capture validated live against the dbg emulator (`pdp1 -t`),
  15 Aug 2026: circle.rim running at 0o100; 0.5 s capture =
  4224 words / 1716 unique points, extent x=[256-768] y=[256-768] —
  a radius-256 circle centred at (512,512).
- Tool self-test: 19/19 golden-fixture checks pass (no machine
  needed).
- Wire format per the emulator's 3400 fan-out: 32-bit LE words,
  dt=511 escapes, null-word timekeeping; snapshot = 16-byte header +
  raw words.
