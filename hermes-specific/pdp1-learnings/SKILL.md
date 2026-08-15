---
name: pdp1-learnings
description: |-
  Agent learnings bucket for the pdp1 skill set. Two sections: LOCAL
  (machine-specific, never published) and PUBLISHABLE (generic
  candidates for the curated pdp1 skills). This is the feed for the
  curation process — the curated skills themselves are write-protected.
trigger: |-
  Load this skill whenever working with any pdp1 skill or the PiDP-1
  machine. File new learnings here instead of editing the curated
  pdp1 skills.
---

# pdp1-learnings

The curated pdp1 skills (pdp1-assembly, pdp1-debugging,
pdp1-plumbing, pdp1-type30-vision, pdp1-tutor, pdp1-code-review) are
write-protected and updated only through curation (see
protect.sh/curate.sh). **This skill is the one place the agent
writes.** All new knowledge lands here, in the right bucket, and a
curation scan turns PUBLISHABLE entries into concrete proposals for
the curated skills.

## Publishable (candidates)

Generic facts, true for any PiDP-1 user/agent. This section feeds the
curation scan. Entry format — four lines, nothing more:

    ### YYYY-MM-DD · <short title>
    TARGET: <skill name> | repo:pidp1-for-agents.md | repo:pidp1-for-agents-debug.md
    CLAIM: <the fact, one or two lines>
    WHY: <evidence — session, spec section, verification>

Example:

    ### 2026-08-15 · `trace <n> changed` omits unchanged keys
    TARGET: pdp1-debugging
    CLAIM: the changed variant drops keys whose value did not change,
    always keeping pc and inst.
    WHY: DEBUG_PROTOCOL_SPEC.md §5; confirmed in a demo trace.

## Local (machine-specific)

This machine, this user's tapes and paths, this profile's quirks.
Never scanned, never proposed for the curated skills. Same format,
TARGET not needed:

    ### 2026-08-15 · where tapes land on this machine
    macro1_1 writes .rim/.lst to the cwd; on this box that is
    /opt/pidp1/tapes/sources.

## Filing rules

1. Learned something PDP-1-ish not already covered by the curated
   skills? Append it here — right bucket, four lines, thirty seconds.
2. Machine-specific → Local. Generic → Publishable. When in doubt:
   Local.
3. Check the curated skills first; if the fact is already there, do
   not file it.
4. Factual error in a curated skill or repo doc: tell the user
   IMMEDIATELY with the fix, then file it here.
5. While a learning is pending, follow the curated skills as written —
   except for a factual error, where the corrected understanding wins
   (the user has been told).

## Curation scan (on request)

Run when the user asks ("run the curation scan"), or offer it after a
pdp1-heavy session. Procedure:

1. Read the Publishable section only. Local is never scanned.
2. For each entry, load the TARGET (skill or repo doc) and check it
   still lacks the content — dedup; skip stale entries.
3. Format a concrete proposal per entry: exact location in the
   target, proposed text, one-line reason. Numbered list.
4. The user accepts, edits, or rejects each item.
5. Accepted entries get `✓ YYYY-MM-DD` on the date line so they are
   never reproposed.

Scan output shape:

    CURATION SCAN — 3 publishable, 2 local (ignored)
    1. [pdp1-debugging] trace changed variant undocumented
       → Run control table, trace row: append "changed: omit unchanged keys"
    2. [repo:pidp1-for-agents-debug.md] pen click coordinate space
       → spec §5 already covers; SKIP
    Accept [1] / edit / skip?
