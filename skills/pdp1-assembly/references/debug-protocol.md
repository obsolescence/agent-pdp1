# The Debug Protocol (port 1040)

The blincolnlights emulator carries a debug service: one line-oriented TCP
protocol on **port 1040**, the same port as the old cli. It gives you
breakpoints, watchpoints, single-stepping, tracing, a call ring, and control of
the front-panel switches — none of it by writing into core.

Normative spec: `blincolnlights/pdp1/DEBUG_PROTOCOL_SPEC.md`. Implementation:
`pdp1/dbg.c` (all of it on the emulator thread; nothing blocks `emu()`).
Everything below is marked **[live]** where it was checked against a running
emulator rather than read out of the spec — **the spec's worked example is
partly from the reference mock and does not match the emulator in every
field** (see "MA" below).

## Before you connect

```sh
ps aux | grep '[p]dp1'                  # is one already running?
```

**Never start a second emulator.** The first one holds ports 1040-1043; the
second dies on `bind: Address already in use` and you will spend an hour
debugging a machine that isn't there.

The machine is **global**: every connection drives the same PDP-1, run control
is last-write-wins, and breakpoints are shared. If someone else is using it,
your `run` will be interrupted by their `step` and you will both be confused.
`claim`/`release` is an advisory lock — nothing requires it, but taking it
makes other connections' state-changing commands fail `?busy` instead of
silently interleaving.

For unattended work start your own headless instance:

```sh
cd blincolnlights/pdp1 && make && ./pdp1 -t
```

`-t` is test mode: POWER forced on, no `coremem` load or dump, no tapes
mounted, and `pwrclr` does *not* randomise the flip-flops. That last part is
load-bearing — a randomised power-on leaves `cyc`/`bc`/`sbm` set and the
machine stops on `IR_INCORR` before executing anything.

## Framing

```
+  success — always the last line of a reply
-  error   — always the last line of a reply
:  data    — more lines follow
!  event   — asynchronous, may arrive at ANY time
```

A client reads lines until `+` or `-`, **collecting `!` lines as it goes**.
One outstanding command per connection; no tags, no pipelining. Lines over
1024 bytes are answered `- ?arg line too long` and the rest is discarded
through the next newline.

`ncat` is fine for one-shots. For anything with a pending command
(`step`, `run`, `until`, `wait`) use `scripts/pdp1dbg.py`, which handles the
framing and — much more usefully — knows your labels.

**Numbers: addresses and machine words are octal with no prefix; counts,
timeouts and light-pen radii are decimal.** `e 100 20` examines twenty words
starting at octal 100. Getting this backwards is the most common first mistake.

## The session

```sh
macro1_1 -r prog.mac                       # -> prog.rim + prog.lst

python3 scripts/pdp1dbg.py --lst prog.lst \
    'l /path/prog.rim'  \
    'w pc go'           \
    'b chkwin'          \
    'run 100000'        \
    'where'             \
    'e board 9'
```

`w pc <addr>` while halted is the whole of it. It sets PC and clears
`cyc`/`df1`/`df2`/`bc`/`hsc`, because "the next instruction is here" is only
meaningful at a fetch boundary. **There is no HLT-at-entry / START / restore /
EXAMINE dance** — that was a workaround for a shared-memory stack that no
longer exists, and it corrupted subroutine entries when it landed on one.

`--lst` is what turns octal squinting into source tracing: labels are
substituted into commands (`b chkwin`) and annotated in replies
(`pc=000110(deci)`), and `trace` lines carry the source text. Two extra
listing-only commands:

| | |
|---|---|
| `where [n]` | source context around PC |
| `check` | every word of core that differs from the listing |

`check` is the fastest way to tell a fresh bug from the wreckage of the last
crash. Expect the `dap` return cells and your variables to differ; expect
nothing else to.

## Commands

### Memory

| | |
|---|---|
| `e <addr> [n]`, `e <addr>-<addr>` | examine; n decimal, ≤4096; 8 words per `:` line |
| `d <addr> <word>…` | deposit — **refused `?state` while running** |
| `poke <addr> <word>…` | deposit, never refused |
| `z [<addr> <n>]` | zero; whole core if bare, refused while running |

`d`/`poke` write `core[]` directly. They disturb nothing else — not PC, not
IR, not the sequence-break state — which is what makes patching a live program
possible at all, and is exactly what the panel DEPOSIT key does *not* give you
(`spec()`→`sc()` clears PC, IR, OV and the IO flags).

The `e <addr>-<addr>` range form is in the implementation but not in the spec's
command table. **[live]**

### Registers

| | |
|---|---|
| `reg`, `reg <r>…`, `r <r>…` | read; bare `reg` lists everything |
| `w <reg> <val>` | write — refused while running |

Writable: `pc ac io mb ma ir ov pf epc ema`. Read-only status: `run run_enable
cyc df1 df2 bc hsc rim sbm exd ioh ioc ios`.

**`ta tw ss eta` are not writable through `w`** — they are switches, and while
the override is disarmed the panel would overwrite them on the next pass of
`emu()`, so `w tw` would silently do nothing. Use `sw`, which says so:
`- ?reg ss is not writable (a switch: use sw)`. **[live]**

`r` is still the paper-tape *reader* — `r <file>` mounts a tape. It reads
registers only when its argument names one, so `r ac` works but `r foo` mounts
a tape called foo. `reg` is unambiguous; prefer it in scripts.

### Run control

| | |
|---|---|
| `s [full]` | status line |
| `go [<addr>]` | START at addr, else CONTINUE — **returns at once** |
| `stop` | STOP key |
| `step [n]` | n instructions |
| `cycle [n]` | n memory cycles |
| `next [n]` | step, but over `jsp`/`jda`/`cal` |
| `run <n> [if <cond>]` | at most n instructions |
| `until <addr> [n]` | temporary breakpoint, then go |
| `trace <n> [changed]` | one `:` line per instruction retired, ≤4096 |
| `wait [<ms>]` | block until stopped; returns at once if already stopped |
| `readin [<addr>]` | READ-IN key |

Everything except `go` and `readin` is a **pending** command: the reply is
withheld until the machine stops and carries the status line. `go` and
`readin` answer `+ run=1` immediately and the stop arrives later as `!stop`.

Every bounded form stops when its budget runs out with `stop=step`, so a
program that jumps into its own constant pool cannot hang the session. The
ceiling is 10,000,000 instructions; `run 20000000` is `- ?limit count out of
range`. **[live]**

`next` steps over a call **only if the current instruction is one** — op 031
(`jsp`) or op 007 (`cal`/`jda`). On anything else it is `step`. On a call it
sets a temporary breakpoint at PC+1 and ignores any count you gave it.

### Breakpoints and watchpoints

| | |
|---|---|
| `b [<addr> [if <cond>]]` | set, or list if bare (≤64) |
| `ub <addr>`, `ub *` | remove |
| `wp <addr> [r\|w\|rw]` | watchpoint, default `w` (≤16) |
| `uwp <addr>`, `uwp *` | remove |
| `back [n]` | ring of the last 64 `jsp`/`jda`/`cal` transfers, 0 = newest |

**Breakpoints are PC comparisons inside the emulator.** Nothing is written
into core, so nothing needs restoring, and a breakpoint on the first
instruction of a `jsp` subroutine no longer destroys the return address the
way a deposited `0` does. They are tested *before the fetch*, so PC still
points **at** the breakpoint address when the machine stops.

Watchpoints fire from `readmem`/`writemem` and stop the machine at the **end
of the current instruction**, not mid-cycle. PDP-1 core is read-restore, so
every reference — the instruction fetch included — writes its word back; a
write watchpoint therefore fires only when the word written *differs* from the
word just read. That is exactly "the program changed this location", and it
means **`dzm` over an already-zero word is invisible**.

`back` survives across runs and across programs — the ring is global and is
not cleared by `w pc` or by loading a tape. Old entries from someone else's
session will be sitting under yours.

### Conditions

A fixed grammar, deliberately not an expression language:

```
<reg> = | != <octal>
M[<addr>] = | != <octal>
```

Anything else is `- ?arg b <addr> [if <cond>]`. Conditions are evaluated at
instruction boundaries only.

`run <n> if M[cnt]!=5` is the invariant-breaking form — it stops the instant
`cnt` stops being 5. **Establish the invariant first**: if `cnt` is not
already 5 the condition is true at the first boundary and you stop after one
instruction wondering what happened. **[live]**

### Panel

| | |
|---|---|
| `panel [on\|off [force]]` | arm/disarm the switch override; bare = query |
| `key <name> [up]` | `start stop cont exam dep readin feed` |
| `sw [<name> [<val>]]` | `ta tw ss sstep sinst extend power`; needs `panel on` |

See the section below — this is the part with the sharp edges.

### Devices

The old port-1040 verbs, unchanged, so `pdp_periph` and the web UI keep
working: `reader`/`r [<file>]`, `punch`/`p [<file>]`, `load`/`l <file>`,
`display`/`dpy [host [port]]`, `muldiv`, `audio`, `sbs [1|16]`, `pen <n>`.
`sbs` and `pen` take **decimal**.

**Bare `muldiv` toggles the EAE.** With no argument the handler does
`muldiv_sw = !muldiv_sw` and reports the new state, so a "query" flips it and
your `mul` silently becomes `mus`. Use `muldiv on` / `muldiv off` to set, and
`muldiv ?` to query — any argument that is neither on/1 nor off/0 changes
nothing and reports the current state, which is why existing clients send
exactly that. **[src]** `pdp1.c:2187` The same shape applies to `audio`.

`hello`'s `opts=muldiv,extend,sbs16,symgen` is a **fixed string**, not a
description of the machine's configuration. It tells you the build can do
these things, not that they are switched on. `symgen` in particular has no
command behind it yet. **[src]** `dbg.c:1027`

## Semantics that bite

### The instruction at PC runs before the debugger looks at anything

Continuing presses CONTINUE, and `emu()` handles that edge with `spec(pdp);
cycle(pdp);` — a fetch that happens *before* `dbgfetch()` is ever consulted.
**[src]** `main.c:59-62`, and the comment on `snapshot()` in `dbg.c:952`.

Three consequences, all verified live:

- **A breakpoint at the current PC does not fire when you continue from it.**
  `w pc loop; b loop; run 100` runs straight past. It fires the *next* time
  round the loop, which is almost always what you wanted, but not what you
  asked for.
- **Continuing from a breakpoint does not immediately re-trigger it.** This is
  the same rule seen from the useful side: no arm/disarm dance is needed.
- **`run <n> if <cond>` executes at least one instruction** before the first
  condition test.

### MA is zero at every debugger stop

`clr_ma()` runs at the end of every instruction while the machine is running
(`if(pdp->run) clr_ma(pdp);`, five sites in `pdp1.c`). The debugger stops at
instruction boundaries, so `ma` in a status or `trace` line reads `000000`
essentially always. **[live]**

MA is only informative when the machine stopped **mid-instruction**:

| stop reason | MA | note |
|---|---|---|
| `break`, `step`, `cond`, `watch`, `cycle`, `stop` | `000000` | boundary; MA already cleared |
| `halt` | address of the `hlt` | `run` went 0 before `clr_ma` |
| `illegal` | address of the bad word, with `cyc=1` | mid-cycle signature |

The spec's §9 example shows `ma=000015` on trace lines. That came from
`test/pdp1dbg_mock.py`, which is an instruction-level stand-in rather than a
TP-level emulator. Where the two disagree, the emulator is right.

### Where PC points after a stop

`pc` is always the machine's real PC — the one on the panel lights — and PC is
incremented at TP2, *before* the instruction executes.

- After a `hlt` at 000105, the status reads **`pc=000106`**. The `hlt` is at
  PC−1. For a `szs`/`hlt` breakpoint pair the `szs` is at PC−2, which is how
  you tell which one fired.
- After a **breakpoint**, PC points **at** the instruction — breakpoints are
  tested before the fetch.
- After `illegal`, PC is inconsistent and `cyc=1`. Do not trust it; find the
  bad word at `ma`.

### Opcode 0 is not HLT

Real `hlt` is `760400`. Depositing `0` gives you an *undefined opcode*
(`IR_INCORR` covers IR 0, 5, 6, 017, 036), which stops as `stop=illegal` with
the mid-cycle signature above. `stop=illegal` is the single most valuable new
stop reason — a machine that ran off the end of something used to just sit
there.

### Events

Default subscription is `stop`: you get `!stop` and nothing else. `!bp`,
`!wp` and `!panel` need `events all`. **[live]**

```
!stop reason=break run=0 … pc=000110 at=260114 stop=break
!bp addr=000012
!wp addr=000130 old=000007 new=000005 pc=000101
!panel key=start
!panel power=0
```

`!bp`/`!wp` precede the `!stop` they caused. `!stop` carries a full status
line, so no follow-up round trip is needed.

A connection that receives a `+` status for its **own** pending command does
not also get `!stop` for that stop. But `go` is not a pending command, so the
sequence `go` … `!stop` … `wait` → `+ status` is normal and a client must not
be confused by getting the event before the reply. **[live]**

`!panel` reports human activity on the real panel — key edges and POWER
changes only, never toggle wiggles — armed or not. It exists so an agent can
notice that someone has walked up to the machine and get out of the way.

### Limits

| | |
|---|---|
| connections | 8 (a ninth gets `?busy` and is closed) |
| `e` words, `trace` lines | 4096 |
| `run`/`until`/`step` budget | 10,000,000 |
| breakpoints / watchpoints | 64 / 16 |
| call ring | 64 |

### Stop reasons

`halt` `illegal` `break` `watch` `cond` `step` (budget) `cycle` `stop`
`manual` (a human moved SINGLE STEP/INST) `power` `readin`, and `none` before
the first stop.

### Errors

`- ?<token> <prose>`: `?cmd` `?arg` `?addr` `?reg` `?state` `?busy` `?limit`
`?timeout` `?file`.

## The panel override

This is the part that lets you drive switches a **program** can read. The test
word is what `lat` loads; the sense switches are what `szs` tests. Overriding
them is the whole point.

```
panel on
sw tw 123456      # lat now yields 123456
sw ss 40          # sense switch 1 up
sw               # query everything, no arming needed
panel off
```

`sw` with a value requires `panel on` (`- ?state the override is not armed;
panel on`). `sw` with no value is a plain read and works either way.

The override merges at the *decoded* level, at the end of `updateswitches()`
in both `panel1.c` and `panelb18.c`, so it wins on every pass while armed and
needs no knowledge of panel bit layouts.

### Sense switches are numbered from the left

**Switch or flag N is bit `040 >> (N-1)`** — switch 1 is `040`, switch 6 is
`001`. Not `1<<N`. `sw ss 40` raises sense switch 1, and that is what `szs 10`
(`640010`) tests. Verified live: with `sw ss 40` a `szs 10` does not skip;
with `sw ss 0` it does. **[live]**

This catches everyone once, and it is the same encoding trap as `szs 1` not
meaning sense switch 1 — see `references/debugging.md`.

### `lat` clears AC first

`lat` is `762200` in both `macro1_1` and `monas` **[src]**, and the two operate
bits act in order: bit 10 clears AC, then bit 7 ORs in the test word. With
AC = `777777` beforehand, `lat` leaves exactly the test word. **[live]**

The bare word `762000` is the OR half on its own and *does* accumulate into
whatever AC held. Notes saying "`lat` is an OR, not a load — clear AC first"
are describing `762000`, not `lat`.

### Two things the panel does that the spec does not mention

Both are in the code and not in `DEBUG_PROTOCOL_SPEC.md` §5:

**Overriding `tw` or `ss` lights every sense-switch lamp.** A machine whose
sense switches disagree with the ones under the operator's hands is baffling,
so while the override holds either program-visible switch the panel lights all
six SS lamps as a warning. **[src]** `panel1.c:99`:

```c
ss = dbgswoverride() ? 077 : pdp->ss;
...
panel->lights6 = pdp->ir<<13 | ss<<6 | pdp->pf;
```

The SS lamps are the right group to borrow because they normally just mirror
the switches, which are sitting right there in front of you — they are the one
lamp group that carries nothing of its own. The program flags do carry
information and are left alone.

`dbgswoverride()` is true only for `tw` and `ss` — the other overrides (TA,
SSTEP, SINST, EXTEND, POWER) already show in the lamps they drive. Note the
consequence: **all six SS lamps lit means "a client is driving the switches",
not "all six switches are up".** Read the real value from `sw` or from the
status line's `ss=`.

**The tape reader key force-releases the override.** The reader key drives
nothing on this machine, so either position of it drops the override entirely
— arm, switches, POWER and all — whoever set it and whether or not they are
still connected. **[src]** `dbg.c:909` `dbgreaderkey()`, called from
`updateswitches()` *before* `dbgoverride()` so it takes effect on that same
pass. It is edge-triggered, so a client can re-arm even while the key is held:
an escape hatch, not a lockout. It is deliberately **not** on the network — a
client that could unlock could already say `panel off force`.

If you are at the machine and a program is ignoring your switches, that key is
the way out.

### `panel off` can refuse

```
- ?state the panel says POWER off; disarming would power the machine down.
  'panel off force' if you mean it
```

Fires when the override holds POWER on, the machine is powered, and the real
panel segment says POWER off — i.e. a client powered the machine up through
the override and is about to hand it back to a panel that still says OFF. This
was the single biggest operational trap in the old stack. `panel off force`
overrides it.

`/tmp/pdp1_panel` **persists across emulator runs**, same surprise class as
`coremem` carryover, so a stale POWER bit can silently disable the refusal.
The segment is 0666; inspect it freely.

### Keys

`key <name> [up]` synthesises one clean edge on the emulator thread, held for
exactly one pass of `emu()` — no sleeps, no missed edges, no races.
`key start up` is START-UP (sequence break mode). Names: `start stop cont exam
dep readin feed`.

On disconnect the server cancels your pending command, drops your temporary
breakpoints, and clears any override bits you owned — SINST and SSTEP in
particular are never left set by a client that died mid-step.

## Recipes

**Where does it hang?**

```
go
wait 3000            # -> ?timeout if it is still spinning
stop
s
back                 # who called whom on the way in
```

**Which instruction corrupts this word?**

```
wp count w
run 1000000
```
Stops at the end of the instruction that changed it; the `!wp` line (with
`events all`) names the old value, the new one, and the PC that did it.

**Is my `jsp` returning to the right place?**

```
b sub
run 100000
r ac                 # jsp leaves the return address in AC
step                 # let the dap ret land
e sub-<the ret cell>
```
`back` gives the same answer from the ring: `to=` the subroutine, `from=` the
call site, `ret=` where it should come back to.

**Did the last crash leave core damaged?**

```
python3 scripts/pdp1dbg.py --lst prog.lst check
```
Anything beyond the `dap` return cells and your variables means reload the
tape before you investigate anything — see `references/debugging.md`.

**Drive a program that reads the sense switches:**

```
panel on
sw ss 20             # sense switch 2 up
until frame
sw ss 0
panel off
```

## What this replaces

Older material describes a shared-memory control channel
(`/dev/shm/pidp1`, `/dev/shm/pdp1_hermes`), a `pdp1_hermes_ctrl` tool, and
breakpoints made by depositing `0`. All of it is superseded, and the
deposit-`0` breakpoint was actively harmful — see `references/errata.md`.

Reading core through `/dev/shm/pidp1` is still supported *where the shm patch
is present* and is invisible to the machine, which makes it good for watching
a program run. The patches were **not upstreamed**, so a stock build does not
have it and `hello` does not advertise `shm`; `e` is the only way to read core.
Client *writes* to that segment race `emu()` and are unsupported.
