---
name: pdp1-debugging
description: Use when debugging PDP-1 programs on the PiDP-1: the port-1040 debug protocol (breakpoints, stepping, tracing, watchpoints, panel override), stop-reason diagnosis, .lst label mapping, and the pdp1dbg helper client. For assembly knowledge see pdp1-assembly.
---

# PDP-1 Debugging

## 1. The one door

Everything an agent can do to the PDP-1 happens through ONE interface:
the line-oriented debug protocol on **TCP port 1040**. Memory,
registers, run control, breakpoints, tapes, the light pen, and the
front panel (via `panel`/`sw`/`key`) — all of it is this one protocol.
There is no other path. No shared memory, no panel files, no separate
tools. `/dev/shm/pidp1` and `/tmp/pdp1_panel` are prohibited (they
race the emulator). The display stream on 3400 is read only through
the pdp1-type30-vision skill's `pdp1_dpy` tool — never raw.

Debugging is a conversation with the machine, in one language, on one
port.

## 2. The method — expect, compare, conclude

Most PDP-1 bugs are found not by reading octal but by EXPECTING a
value and noticing when it does not match:

1. Before executing an instruction, predict what will change (AC, PC,
   MA, MB, memory).
2. Execute — `step`, `trace`, or a bounded `run`.
3. Compare actual state against the prediction (`s`, `reg`, `e`).
4. Match → understanding is correct, proceed. Mismatch → you found
   the bug.

Reading registers without an expectation is looking, not debugging.

The same discipline runs the copilot: at the start of every command
batch, ask `s` and compare with what you last left behind. If the
machine changed and you did not change it, someone else is driving —
stop, report, and yield.

## 3. Speaking the protocol

TCP, line-oriented US-ASCII, `\n`-terminated. **One outstanding
command per connection** — never send a second command before the
first is answered. No pipelining. Lines over 1024 bytes get
`- ?arg line too long`.

**Numbers: addresses and machine words are OCTAL, always, no prefix.
Counts, timeouts and light-pen values are DECIMAL.** Radix is marked
inline in the tables below — a global footnote is where budget models
lose it.

**Server lines are typed by their first character:**

| char | meaning |
| ---- | ------- |
| `+`  | success — always the final line of a reply |
| `-`  | error — always the final line of a reply |
| `:`  | data line, more follow |
| `!`  | asynchronous event, may appear at any time |

Read lines until `+` or `-`, skipping `!` events for framing — but
NEVER discard `!` lines: `!wp` carries `old=`/`new=` values that
exist nowhere else, and `!bp`/`!wp` precede the `!stop` they caused.
Echo them verbatim (stderr is fine).

Errors are `- ?<token> <prose>` with stable tokens: `?cmd` `?arg`
`?addr` `?reg` `?state` `?busy` `?limit` `?timeout` `?file`. Branch
on the token: `?state` and `?arg` demand different self-corrections.

### The helper client — pdp1dbg.py

The skill set ships `pdp1dbg.py` (stdlib only) so no agent rewrites
the framing per session:

    pdp1dbg.py 's'                            # one command
    pdp1dbg.py 'w pc 4' 'step 3' 'reg'        # several, same connection
    pdp1dbg.py -                              # commands on stdin; blank line = flush;
                                              #   'sleep N'/'usleep N' pause locally
    pdp1dbg.py --lst program.lst 'b loop' 'run 1000'   # label substitution

- Each invocation is one connection; commands run serialized in
  order; every reply is printed. Exit status is `1` if any command
  answered `-` — and the `?token` is printed verbatim.
- **Stdin batch mode (`-`) keeps ONE connection open** — the only way
  to hold connection-scoped state (the panel override, a `claim`).
  Use it for every `panel`/`sw`/`key` sequence. It buffers stdin to
  EOF before sending anything — EXCEPT a blank line, which flushes
  the batch so far (pace from the shell: flush, then sleep, then
  write more).
- `sleep N` / `usleep N` are LOCAL commands: they pause the client
  between commands and never reach the emulator. That is how a timed
  sequence (TW pulse, §9) is expressed INSIDE the batch. A shell
  `sleep` inside a piped stdin does NOT pace the script — see the
  recipe for the reliable form.
- `--lst` substitutes labels into commands and annotates replies.
  Optional sugar — everything below works in pure octal.
- Bonus listing-only commands: `where [n]` (source context around
  PC) and `check` (every core word that differs from the listing —
  self-modifying code vs. crash damage).
- **Events go to OTHER connections.** When a stop completes YOUR
  pending command, the `+` status carries everything (stop reason,
  pc, at=) and the server suppresses the `!stop` for you. `!bp`/
  `!wp` events arrive on connections that did not cause the stop —
  the helper collects and prints them at the end of an invocation.
  To see a watchpoint's `old=`/`new=` payload, run a second
  connection subscribed `events all` while the first drives the
  machine — or prefer `run <n> if <cond>`, which needs no events.
- `ncat`/`nc` is fine for instant-reply verbs (`load`, `muldiv on`,
  `pen click`) and for humans poking. Never for `step`/`run`/
  `until`/`go`/`wait` — those are pending commands whose reply comes
  when the machine stops, and a one-shot ncat closes the connection
  (and its temporary breakpoint) first.

## 4. Command reference

### Session

| command | reply | notes |
| ------- | ----- | ----- |
| `hello` | `+ proto=1 machine=pdp1 maxmem=200000 opts=…` | `maxmem=200000` is OCTAL = 64K words |
| `help [<cmd>]` | `:` one line per command, then `+` | call once per session, not per command |
| `events none\|stop\|all` | `+ events=stop` | default `stop`; `all` for `!panel` watching |
| `claim` / `release` | `+ claim=1` / `+ claim=0` | advisory; **do not claim** — it is per-connection and rarely needed |
| `quit` | `+ bye`, then close | |

### Inspection

| command | args (radix) | reply |
| ------- | ---- | ----- |
| `s [full]` | | `+ run=0 cyc=0 df1=0 pc=000012 ac=… io=… ma=… mb=… ir=… ov=0 pf=00 ss=00 at=… stop=…` |
| `reg` / `r <reg>…` | | `+ pc=000004 ac=000005 …` — all registers if bare `reg` |
| `e <addr> [n]` | addr OCTAL, n DECIMAL (default 1, max 4096) | `:` lines: start address + up to 8 words, then `+ <n>` |
| `d <addr> <word>…` | OCTAL | `+ <n>` — **refused `?state` while running** |
| `poke <addr> <word>…` | OCTAL | `+ <n>` — never refuses |
| `z [<addr> <n>]` | | `+ <n>` — **bare `z` zeroes ALL of core** |

`e`/`d` are non-destructive — they touch `core[]` and nothing else.
That is what makes debugging a live program possible.

### Run control

| command | args (radix) | reply |
| ------- | ---- | ----- |
| `go [<addr>]` | addr OCTAL | `+ run=1` immediately; the stop arrives as `!stop` |
| `stop` | | `+ <status>` — stops at the next instruction boundary |
| `step [n]` | n DECIMAL | `+ <status>` when stopped |
| `cycle [n]` | n DECIMAL (memory cycles) | `+ <status>` |
| `next [n]` | n DECIMAL | step, but over `jsp`/`jda`/`cal` |
| `run <n> [if <cond>]` | n DECIMAL, cond values OCTAL | `+ <status>` — at most n instructions |
| `until <addr> [n]` | addr OCTAL, n DECIMAL | temp breakpoint + go; `+ <status>` |
| `trace <n> [changed]` | n DECIMAL | `:` one line per retired instruction, then `+ <status>` |
| `wait [<ms>]` | ms DECIMAL, default forever | `+ <status>` or `- ?timeout` |
| `readin [<addr>]` | addr OCTAL | `+ run=1` — READ-IN key |

`go` and `readin` return immediately. Everything else that runs the
machine is a PENDING command: the reply is withheld until the machine
stops and carries the status. Every bounded form stops with
`stop=step` when its budget runs out — a program that jumps into the
constant pool must not hang your session.

`trace` line format (`pc` = address of the instruction executed):

    : pc=000005 inst=240015 ac=000005 io=000000 ma=000015 mb=000005 ov=0

### Debug tier

| command | args (radix) | reply |
| ------- | ---- | ----- |
| `b [<addr> [if <cond>]]` | addr OCTAL, cond values OCTAL | set, or LIST if bare |
| `ub <addr>` \| `ub *` | addr OCTAL | `+ <n>` removed |
| `wp <addr> [r\|w\|rw]` | addr OCTAL | `+` — default `w` |
| `uwp <addr>` \| `uwp *` | addr OCTAL | `+ <n>` |
| `back [n]` | n DECIMAL (default 16) | `:` ×n, then `+ <n>` |

Breakpoints are **PC comparisons inside the emulator** — nothing is
written into core, nothing needs restoring, and a breakpoint on a
`jsp` entry is safe (a deposited 0 there eats the return address).
Watchpoints fire on core access and stop at the end of the current
instruction. **A write watchpoint fires only when the word CHANGES** —
core is read-restore, so `dzm` over an already-zero word is invisible.
`back` is the live call ring (last 64 `jsp`/`jda`/`cal` transfers,
index 0 = most recent):

    : 0 to=001165 from=001451 ret=001452

Conditions (fixed grammar, not an expression language; evaluated at
instruction boundaries only):

    <cond> := <reg> ("=" | "!=") <octal>
            | "M[" <addr> "]" ("=" | "!=") <octal>

    run 1000 if M[15]!=5      # stop the instant the invariant breaks
    b 1165 if ac=1            # conditional breakpoint

### Panel tier (the front panel over 1040)

| command | args | notes |
| ------- | ---- | ----- |
| `panel [on\|off [force]]` | | arm/disarm the switch override |
| `key <name> [up]` | `start stop cont exam dep readin feed reader` | one clean edge, synthesised on the emulator thread |
| `sw [<name> [<val>]]` | `ta tw ss sstep sinst extend power`, val OCTAL | requires `panel on` |

See §7 for when — and how — to use this tier.

### Devices

`reader`/`r [<file>]` · `punch`/`p [<file>]` · `load`/`l <file>` ·
`display`/`dpy [<host> [<port>]]` · `muldiv [on|off]` · `audio
[on|off]` · `sbs [1|16]` · `pen [<n>]` (clamped 3..16) ·
`pen click <x> <y> [<ms>]` (x,y,ms DECIMAL; x,y 0..1023, ms 1..10000,
default 100; replies immediately — sleep `ms`, then read the machine's
reaction).

Network filenames are confined to the tape directory: relative, no
`..`. Device verbs are the only lenient verbs; everywhere else,
unknown trailing arguments are `?arg`, never ignored.

## 5. Machine semantics — what the status means

Status line (fixed key order; tolerate unknown keys, never parse
positionally):

    run=0 cyc=0 df1=0 pc=000012 ac=420016 io=000000 ma=000015 mb=000001 ir=21 ov=0 pf=00 ss=00 at=420016 stop=break

- `at` is `core[pc]` — the word about to be executed.
- `ir` is 5 bits, opcode>>1.
- **`ma` reads `000000` at debugger stops** — MA is cleared at the
  end of each instruction. It is only meaningful on `stop=halt` and
  `stop=illegal`. Do not read `ma` as "the address of the last
  instruction".
- `cyc=1` means the machine halted MID-CYCLE — registers are a
  partial snapshot (MB may hold the fetched word, AC the old value).
  `go` resumes the interrupted instruction; `w pc` clears the
  mid-cycle state.
- **Sense switches and program flags are numbered from the LEFT**:
  switch N is bit `0o40>>(N-1)` — switch 1 is `040`, switch 6 is
  `001`. `ss=40` = switch 1 up, which is what `szs 1` (`640010`)
  tests.
- Registers writable with `w`: `pc ac io ma mb ir ov pf epc ema`.
  Read-only: `ta tw ss eta` (switches — use `sw`) and the status bits
  `run run_enable cyc df1 df2 bc hsc rim sbm exd ioh ioc ios`.
- `w` is refused `?state` while running. **`w pc <addr>` while halted
  sets PC exactly** — it clears `cyc/df1/df2/bc/hsc` and the in-out
  transfer, putting the machine at a fetch boundary. No
  EXAMINE/START dance.

### PC after a stop — it depends on WHY

| stop | PC points |
| ---- | --------- |
| `hlt`, `illegal` | **past** the instruction (PC incremented before execution) |
| `break` | **at** the breakpoint address (tested before the fetch) |
| `watch` | after the instruction whose access fired |

An agent that always "examines the instruction that stopped the
machine" will examine the wrong word for the two most common reasons.

## 6. Stop reasons — and what to do on each

| reason | meaning | reaction |
| ------ | ------- | -------- |
| `halt` | the program executed a real HLT (`760400`) | expected or not? Look at PC−1; check the listing |
| `illegal` | undefined opcode — the program ran off into data | check what is at PC and how you got there; the machine ran garbage |
| `break` | your breakpoint | inspect and continue |
| `watch` | a watched location changed | the `!wp` event carried `old=`/`new=` — read it! |
| `cond` | your invariant broke | this IS the bug — inspect the condition's operands |
| `step` | budget exhausted | expected — continue or conclude |
| `cycle` | cycle budget exhausted | expected |
| `stop` | STOP key or `stop` command | expected |
| `manual` | a human flipped SINGLE STEP/INST | a human is driving — yield |
| `power` | power went down | check the panel; power is a human's job |
| `readin` | READ-IN completed | program started — proceed |

A fresh machine stopping on `illegal` before executing anything is
the random-power-on signature (leftover `cyc`/`bc`/`sbm`): the
reaction is `w pc` + `go`.

## 7. The front panel via 1040

**note** `e`/`d` are non-destructive; the
panel EXAMINE/DEPOSIT keys are destructive — they clear PC, IR, OV,
IO flags and sequence-break state. Never debug through `key exam` /
`key dep`. Use the panel tier for authentic panel behaviour:

- START-UP (sequence break mode): `key start up`
- READ-IN from the reader: `key readin`
- setting sense switches or test word for a program that reads them:
  `sw ss <val>` / `sw tw <val>`

The override model:

- `panel on` arms the switch override; `sw` then sets decoded fields
  (`ta tw ss sstep sinst extend power`). `panel off` disarms; it
  REFUSES with `?state` if disarming would power the machine down
  (`panel off force` overrides).
- **The override is connection-owned.** Disconnect clears it. A
  `panel on` in one invocation and `sw` in the next silently disarms
  between them — always compose the whole sequence into ONE batch:
  `pdp1dbg.py -` with `panel on`, all `sw`/`key`, then `panel off`.
- **It is visible and escapable.** While the override holds TW or SS,
  the panel lights every sense switch lamp. The physical panel's tape
  reader key releases the override — the human always wins. If you
  see `!panel override=off by=reader`, you no longer hold anything.

## 8. .lst mapping (optional)

The protocol speaks octal; programs are written in labels. If a
listing exists, use it — labels beat octals for reasoning:

    grep 'loop,' program.lst        # → "… 00006 200015 loop, lac cnt"
    pdp1dbg.py --lst program.lst 'b loop' 'until chkwin'

With `--lst`, labels are substituted into commands and annotated in
replies. Without a listing, pure octal works — nothing in the method
requires labels.

## 9. Recipes

### Session start checklist

    hello                 # expect + proto=1 machine=pdp1
    s                     # where is the machine, what is stop=
    b                     # LIST breakpoints — they are global and persist
                          # (other sessions may have left them)

Watchpoints have no documented list form — if you fear leftovers,
`uwp *` cleans all of them (and other sessions' too — say so out
loud before doing it).

### Load and step from entry

    l /path/to/program.rim    # or: r … + key readin for auto-start
    w pc 0o4                  # entry from the listing; sets a fetch boundary
    s                         # at= should be the entry instruction
    trace 5                   # five annotated steps
    step                      # continue stepping

### Run to a label and inspect

    until 0o12                # temp breakpoint + go; stops BEFORE the fetch
    reg                       # PC points AT the label
    e 0o15 1                  # inspect a variable

### Timed switch pulse (hold TW/SS for N seconds)

    pdp1dbg.py - <<'EOF'
    panel on
    sw tw 400
    sleep 4
    sw tw 0
    panel off
    EOF

The in-stream `sleep` runs client-side while the connection stays
open, so the emulator holds TW400 for the full 4 s. This is the
reliable way to time a pulse: a shell `sleep` inside a PIPED stdin
(`echo … | pdp1dbg.py -`) sleeps on the shell side, and the script
sends everything back-to-back once the pipe closes.

### Why did it halt

    s                         # read stop= and at=
    reg                       # PC semantics depend on stop= (§5)
    # stop=halt → PC−1 in the listing; stop=illegal → ran into data

### Watch a variable

    run 1000 if M[15]!=5      # stop the instant cnt stops being 5
    wp 0o15 w                 # or: stop when core[0o15] changes
    # read the !wp event — old=/new= are the payload

### Step over vs into

    next                      # over jsp/jda/cal (one round trip)
    step / trace 3            # into the subroutine

### Hunt a crash loop

    run 1000                  # stop=step when the budget runs out
    back                      # the call ring — where did control come from
    e <pc> 1                  # what is at the stop address

### Timeout recovery

A bounded `wait`/`until` that times out kills the connection — but a
completed `go` is not pending, so the machine may still be running:

    pdp1dbg.py 's'            # reconnect and ask
    pdp1dbg.py 'stop'         # only if run=1

Never assume. Ask `s` first.

### Machine appears hung

    s                         # run=1? then it is not hung, it is looping
    stop                      # halt it
    reg / e <vars> 4          # inspect the loop variables

### Worked example (real validated run, 15 Aug 2026)

    $ pdp1dbg.py --lst demo.lst 'l demo.rim'
    > l demo.rim
      ok
    $ pdp1dbg.py 'w pc 4' 's'
    > w pc 4
      pc=000004
    > s
      run=0 cyc=0 df1=0 pc=000004 ac=000000 io=625400 ma=000000 mb=000000 ir=00 ov=0 pf=00 ss=00 at=700005 stop=stop
    $ pdp1dbg.py 'trace 3'
    > trace 3
      pc=000004 inst=700005 ac=000005 io=625400 ma=000000 mb=700005 ov=0
      pc=000005 inst=240015 ac=000005 io=625400 ma=000000 mb=000005 ov=0
      pc=000006 inst=200015 ac=000005 io=625400 ma=000000 mb=000005 ov=0
      run=0 cyc=0 df1=0 pc=000007 ac=000005 io=625400 ma=000000 mb=000005 ir=10 ov=0 pf=00 ss=00 at=640100 stop=step
    $ pdp1dbg.py 'b 12' 'go'
    > b 12
      1
    > go
      run=1
    $ pdp1dbg.py 'wait 2000'
    > wait 2000
      run=0 cyc=0 df1=0 pc=000012 ac=000005 io=625400 ma=000000 mb=600012 ir=30 ov=0 pf=00 ss=00 at=420016 stop=break
    $ pdp1dbg.py 'e 15 1' 'reg'
    > e 15 1
      000015 000005
      1
    > reg
      pc=000012 ac=000005 io=625400 mb=600012 ma=000000 ir=30 ov=0 pf=00 epc=00 ema=00 ta=000000 tw=000000 ss=00 eta=00 run=0 run_enable=0 cyc=0 df1=0 df2=0 bc=0 hsc=0 rim=0 sbm=0 exd=0 ioh=0 ioc=1 ios=0
    $ pdp1dbg.py 'run 1000 if M[15]!=1'
    > run 1000 if M[15]!=1
      run=0 cyc=0 df1=0 pc=000013 ac=000004 io=625400 ma=000000 mb=000001 ir=21 ov=0 pf=00 ss=00 at=240015 stop=cond
    $ pdp1dbg.py 'ub *' 'quit'
    > ub *
      1
    > quit
      bye

Notes on reading this run:

- The `+` status of `wait 2000` carries `stop=break` and `pc=000012`
  — no `!bp` line, because this connection caused the stop (§3:
  events go to other connections).
- `e 15 1` shows `000015 000005`: the countdown variable `cnt` still
  holds 5 — the breakpoint stopped BEFORE `sub one` executed.
- `run 1000 if M[15]!=1` stops with `stop=cond` the moment `cnt`
  leaves 1: `pc=000013`, `ac=000004`, `at=240015` (the `dac cnt`
  about to store the new value).
- `ma=000000` throughout — cleared at instruction end (§5). The
  register VALUES are machine state and will differ between runs;
  the FORMAT is normative.

The discipline in one session: predict (cnt should still be 5 at the
breakpoint), verify (`e 15 1`), assert the invariant (`run … if
M[15]!=1`), clean up (`ub *`).

## 10. Token economy and footguns

- **Never dump ranges into context.** `e` can emit 4096 words — that
  is a context bomb. Default: `e` ≤ 32 words unless justified.
  `trace 10` max; prefer `trace <n> changed` (omits unchanged keys).
- Never poll `s` in a loop — use `go` + `wait` (or a bounded `run`),
  and let the `+` status / `!stop` carry the state.
- Never read the 3400 stream raw — the pdp1-type30-vision skill's
  `pdp1_dpy` is the only sanctioned way to look at the screen.
- `help` once per session, not per command.
- **Opcode 0 is NOT HLT** — real HLT is `760400`. A deposited 0 stops
  via the illegal path with an inconsistent PC. Use breakpoints.
- **Bare `r` UNMOUNTS the reader tape**; `r <file>` mounts it;
  `r <name>` reads a register. Filing `r` under "registers" unmounts
  tapes.
- **`d`/`z`/`w` refuse `?state` while running**; `poke` never
  refuses. `sw` requires `panel on`.
- `?busy` means either a foreign `claim` OR a ninth connection.
- The 1024-byte line limit: cap `d <addr> <word>…` at ~140 words per
  command.
- Breakpoints are GLOBAL: `ub *` removes other sessions' breakpoints
  too. List with bare `b` before touching anything.
- Don't debug through panel keys (§7). Don't `claim` (§4).
- If a skill fact and `DEBUG_PROTOCOL_SPEC.md` disagree, the spec
  wins — file the discrepancy in pdp1-learnings.

## 11. Provenance

- Protocol: `proto=1`, as `DEBUG_PROTOCOL_SPEC.md` v1.
- Conformance: `pdp1/test/pdp1dbg_test.py` — **41 pass / 0 fail /
  1 skip** against the dbg emulator (`pdp1 -t`), 15 Aug 2026.
- Live-validated: the worked example in §9 is a real transcript from
  the same session; `pdp1dbg.py` exercised end-to-end (one-shot,
  batch, `--lst` labels).
- Gotcha verified: a stale `/tmp/pdp1_panel` from an earlier stack
  leaves SINST set and makes every run stop with `stop=manual` —
  remove the file before a clean test run (file hygiene, not an
  interface).
- 2026-08-16: stdin batch timing — blank-line flush plus `sleep`/
  `usleep` locals (verified against the dbg emulator; timed-pulse
  recipe in §9).
- This skill: v1.0 after the live validation.
