#!/usr/bin/env python3
"""Regenerate golden .snp fixtures for pdp1-type30-analysis.

Usage: python3 make_fixtures.py [outdir]
Default outdir: ../test/fixtures relative to this script.

Deterministic: fixed geometry and fixed RNG seed — regenerating produces
byte-identical fixtures. Each fixture is a synthetic Type 30 display
stream: a known point set repeated ~60 times (like a display list loop),
stored in the pdp1_dpy snapshot format (16-byte header + raw 32-bit LE
words). No emulator needed.
"""
import math
import os
import random
import shutil
import sys
import time

HERE = os.path.dirname(os.path.realpath(__file__))

# The tool is a script without a .py extension — load it explicitly so both
# files share one snapshot-format implementation (no drift).
import importlib.machinery
import importlib.util
_TOOL = os.path.join(HERE, "pdp1_dpy")
_loader = importlib.machinery.SourceFileLoader("pdp1_dpy", _TOOL)
_spec = importlib.util.spec_from_loader("pdp1_dpy", _loader)
_mod = importlib.util.module_from_spec(_spec)
_loader.exec_module(_mod)
save_snapshot = _mod.save_snapshot


def word(x, y, intens=5):
    return (y << 10) | (x & 0x3FF) | ((intens & 7) << 20)


def edge(x0, y0, x1, y1, step=4, intens=3):
    """Points along a line segment at fixed step."""
    n = max(1, int(math.hypot(x1 - x0, y1 - y0) / step))
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append((int(round(x0 + (x1 - x0) * t)),
                    int(round(y0 + (y1 - y0) * t)), intens))
    return pts


def line_h(y, x0, x1, step=4, intens=3):
    return edge(x0, y, x1, y, step, intens)


def line_v(x, y0, y1, step=4, intens=3):
    return edge(x, y0, x, y1, step, intens)


def ring(cx, cy, r, step=8, intens=5):
    pts = []
    for a in range(0, 360, step):
        rad = math.radians(a)
        pts.append((int(round(cx + r * math.cos(rad))),
                    int(round(cy + r * math.sin(rad))), intens))
    return pts


def tictactoe():
    """3x3 board, O ring top-left, X diagonals center."""
    pts = []
    pts += line_v(341, 0, 1023) + line_v(682, 0, 1023)
    pts += line_h(341, 0, 1023) + line_h(682, 0, 1023)
    pts += ring(170, 852, 85)                    # O in top-left cell
    for t in range(-85, 86, 4):                  # X in center cell
        pts.append((512 + t, 512 + t, 7))
        pts.append((512 + t, 512 - t, 7))
    return pts


def cube():
    """Wireframe cube: front square + offset back square + connectors."""
    front = [(350, 350), (674, 350), (674, 674), (350, 674)]
    back = [(410, 410), (734, 410), (734, 734), (410, 734)]
    pts = []
    for i in range(4):
        fx, fy = front[i]
        bx, by = back[i]
        pts += edge(fx, fy, front[(i + 1) % 4][0], front[(i + 1) % 4][1])
        pts += edge(fx, fy, bx, by)
        pts += edge(bx, by, back[(i + 1) % 4][0], back[(i + 1) % 4][1])
    return pts


def scatter():
    """Uniform 'points everywhere', fixed seed for determinism."""
    rng = random.Random(42)
    return [(rng.randrange(1024), rng.randrange(1024), rng.randrange(1, 8))
            for _ in range(1500)]


def empty():
    return []


def build(pts, repeats=60):
    words = []
    for _ in range(repeats):
        for (x, y, i) in pts:
            words.append(word(x, y, i))
        if not pts:
            words.append(0)  # null word: empty display still streams timekeeping
    return words


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "test", "fixtures")
    os.makedirs(outdir, exist_ok=True)
    now = int(time.time())
    shapes = {
        "tictactoe": tictactoe(),
        "cube": cube(),
        "scatter": scatter(),
        "empty": empty(),
    }
    for name, pts in shapes.items():
        words = build(pts)
        save_snapshot(os.path.join(outdir, name + ".snp"), words, now, 0.5)
        unique = len({(x, y) for (x, y, i) in pts})
        print("%s.snp: %d words, %d unique points (deduped)" % (name, len(words), unique))
    shutil.copyfile(os.path.join(outdir, "tictactoe.snp"), os.path.join(outdir, "demo.snp"))
    print("demo.snp: copy of tictactoe.snp")


if __name__ == "__main__":
    main()
