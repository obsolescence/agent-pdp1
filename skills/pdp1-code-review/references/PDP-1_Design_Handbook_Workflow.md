# PDP-1 Design Handbook Workflow

## Phase 0 – Preparation
Collect one source file (tapes/source/icss_1_3.mac) and keep line numbers.

---

## Phase 1 – Explain the code

**Goal:** Understand every routine before judging it.

### Prompt

```text
You are an experienced DEC PDP-1 programmer.

Analyze the attached source code section by section.

For every routine provide:

- Name
- Purpose
- Inputs
- Outputs
- Registers / AC usage
- Memory locations modified
- Dependencies
- Algorithm
- Any unusual PDP-1 techniques

Do not critique the code yet. Only explain it accurately.

Maintain a glossary of labels and important memory locations.
```

Deliverable: Routine Reference.

---

## Phase 2 – Extract recurring patterns

### Prompt

```text
Review the complete source again.

Ignore the program's purpose.

Instead identify every recurring programming pattern.

For every pattern provide:

- Pattern name
- Description
- Why it works
- Advantages
- Disadvantages
- Where it occurs
- Whether it is general or game-specific

Do not yet recommend whether it belongs in a style guide.
```

Deliverable: Pattern Catalog.

---

## Phase 3 – Create coding rules

### Prompt

```text
Convert the Pattern Catalog into a PDP-1 Programming Style Guide.

Each rule should contain:

Rule
Reason
Example
Counter-example
When to use
When not to use

Write rules, not observations.
```

Deliverable: Style Guide v0.1

---

## Phase 4 – Challenge the rules

### Prompt

```text
Review the complete source again.

For every rule in the Style Guide:

- Find exceptions.
- Explain why the exception exists.
- Decide whether the rule should be modified.
- Identify performance-driven exceptions.
- Identify hardware-driven exceptions.

Rewrite the rule if needed.
```

Deliverable: Style Guide v0.2

---

## Phase 5 – Rewrite the handbook

### Prompt

```text
Make a backup copy (.backup file extension, so we keep a copy) and then discard the previous handbook.

Rewrite it from scratch using everything learned.

Organize it into:

Architecture
Assembler conventions
Naming conventions
Memory organization
Subroutines
Arithmetic idioms
Loop idioms
Display programming
Optimization
Debugging
Commenting
Common pitfalls
Best practices

Do not preserve wording from the previous version unless it is still optimal.
```

Deliverable: Design Handbook v1.0

---

## Phase 6 – Code Review Mode

```text
Review this PDP-1 routine as if written by a junior DEC programmer.

For every issue classify it as:

Excellent
Good
Acceptable
Questionable
Poor

Explain why.

Suggest improvements that preserve historical PDP-1 style.

Whenever possible cite a similar technique from ICSS.
```

---

## Phase 7 – Continuous refinement

After each project ask:

```text
Compare this new program against the Design Handbook.

List:

New patterns
Violated rules
Better alternatives
Missing guidance

Propose changes to the handbook.

Do not modify the handbook directly.

Instead produce a proposed changelog.
```

## Phase 7B - Then periodically (which means, IMPORTANT: DO NOT DO THIS NOW. Only do this when you are explicitly asked to do this:

```text
Rewrite the complete handbook from scratch using all approved changes.
```

Make sure you understand: Phase 7B is ONLY done when the user EXPLICITLY requests it.

And before doing Phase 7B, make a backup of the old handbook. Avoid risk of data loss.


## Confidence ratings

Assign every rule:

- Very High — observed in multiple independent PDP-1 programs and DEC documentation.
- High — repeated in one major program and architecturally justified.
- Medium — observed occasionally.
- Low — plausible but based on limited evidence.

