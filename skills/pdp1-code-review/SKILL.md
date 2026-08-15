---
name: pdp1-code-review
description: "Use when the user asks for PDP-1 code review or phases 0-7B."
---

# PDP-1 Code Review / Design Handbook Workflow

A multi-phase methodology for analyzing PDP-1 assembly programs and building
a design handbook from them. The full step-by-step instructions and prompts
live in `references/PDP-1_Design_Handbook_Workflow.md` — read that file
first. The user can ask for any phase; phases build on each other.

## The phases (summary — full prompts in the reference)

- **Phase 0 — Preparation:** collect one source file, keep line numbers.
- **Phase 1 — Explain:** routine-by-routine explanation (name, purpose,
  inputs, outputs, registers, memory modified, dependencies, algorithm,
  unusual techniques). No critique. Deliverable: Routine Reference.
- **Phase 2 — Patterns:** identify every recurring pattern (name, why it
  works, advantages, disadvantages, where it occurs, general vs
  game-specific). Deliverable: Pattern Catalog.
- **Phase 3 — Rules:** convert the catalog into a Style Guide (rule, reason,
  example, counter-example, when to use / not use). Deliverable: Style
  Guide v0.1.
- **Phase 4 — Challenge:** find exceptions to every rule, decide whether it
  stands or is rewritten. Deliverable: Style Guide v0.2.
- **Phase 5 — Rewrite:** back up the old handbook (.backup extension), then
  rewrite the handbook from scratch. Deliverable: Design Handbook v1.0.
- **Phase 6 — Code Review Mode:** review routines as if written by a junior
  DEC programmer; rate Excellent / Good / Acceptable / Questionable / Poor;
  suggest period-style improvements; cite ICSS idioms when possible.
- **Phase 7 — Continuous refinement:** after each project, produce a
  PROPOSED changelog (new patterns, violated rules, better alternatives,
  missing guidance). Never modify the handbook directly.
- **Phase 7B — Handbook merge:** rewrite the handbook from all approved
  changes. ONLY when the user explicitly asks — never proactively. Back up
  the old handbook before doing it.

Confidence ratings for every rule: Very High (multiple independent programs
+ DEC docs) / High (one major program + architectural justification) /
Medium / Low. Rubric in the reference.

## Products (assets/products/)

| File | What it is | Status |
|---|---|---|
| `icss_design_handbook_v1.0.md` | The ICSS-derived design handbook | CURRENT truth (corrected Aug 2026) |
| `ddt_phase7_changelog.md` | Proposed changes from the DDT analysis | UNMERGED — proposal only |
| `spacewar4_phase7_changelog.md` | Proposed changes from the Spacewar! 4.8 analysis | UNMERGED — proposal only |

The two changelogs are merged into the handbook ONLY when the user requests
Phase 7B. Until then they are proposals, not doctrine.

## Canonical location (IMPORTANT)

The files in THIS skill directory are canonical. The legacy working copies
under `/home/x/Documents/x5/pidp1/hermes/` are history — treat them as
read-only. All merges, fixes, and rewrites land in `assets/products/` here.
This skill is shared with other Hermes agents; when a product file changes,
say so in the skill so copies held elsewhere get updated.

## Rules

- Phase 7 produces changelogs, never handbook edits.
- Phase 7B runs only on explicit user request; back up the old handbook
  first (keep a `.backup` file alongside).
- Changelogs are proposals; only the handbook is current truth.
- Every claim carries a confidence rating per the rubric.
- The handbook and changelogs were audited Aug 2026 against corrected
  PDP-1 doctrine (JSP/JDA return-in-AC semantics, no link register). If
  old material contradicts the doctrine, the doctrine wins.
