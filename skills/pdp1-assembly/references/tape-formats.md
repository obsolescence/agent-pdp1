# Tape Formats and Loading

## Frames and words

Paper tape holds 6 bits per line. A tape word is **three frames**, most
significant first. Bit 7 of a byte marks it as data; bytes without it are
leader and are skipped entirely.

```c
int getwrd(int fd) {
        u8 c; int w = 0, n = 3;
        while(n--) {
                do {
                        if(read(fd, &c, 1) <= 0) return -1;
                } while((c & 0200) == 0);       /* skip leader */
                w = w << 6 | (c & 077);
        }
        return w;
}
```
**[src]** `blincolnlights/pdp1/pdp1.c`

Punching is the inverse — each of the three 6-bit groups gets bit 7 set:

```c
punchObject(((val >> 12) & 077) | 0200);
punchObject(((val >>  6) & 077) | 0200);
punchObject(( val        & 077) | 0200);
```

## RIM format

The simplest format: alternating instruction/data pairs, decoded by the high six
bits.

| High 6 bits | Record | Meaning |
|---|---|---|
| `032` (`dio`) | data | next word is stored at `inst & 07777` |
| `060` (`jmp`) | transfer | stop loading; address is the entry point |
| anything else | — | malformed ("rim botch") |

```
readrim:
  loop:
    inst = getwrd()
    if inst == -1: stop                          (EOF)
    if (inst & 0760000) == 0320000:              (DIO)
        core[inst & 07777] = getwrd()
    elif (inst & 0760000) == 0600000:            (JMP)
        print "start: %04o"; return              (does NOT run)
    else:
        print "rim botch"; return
```
**[src]**

Two words of tape per word of core, so RIM tapes are large and slow — which is
why the block format exists.

## Block format

The default `macro1_1` output. Structure:

1. leader
2. a small bootstrap loader, placed high in core (around `7751`)
3. a JMP to the bootstrap
4. one or more data blocks: start address, end address, the data words, a
   checksum
5. the transfer JMP from the `start` directive

The bootstrap reads the blocks and expands them into core, then honours the
trailing JMP. Checksummed and roughly half the tape length of RIM.

## Which loader accepts which

| Assembler output | `l` command | READ-IN |
|---|---|---|
| `macro1_1 -r` (RIM) | yes | yes, if `start` is present |
| `macro1_1` (block) | **no** | yes |
| `monas` (BIN + loader) | **no** | yes |

The emulator's `l` command calls `readrim`, which understands only DIO/JMP
pairs. Given a block tape it reads the bootstrap loader as if it were program
data, then stops at the JMP to the bootstrap. **It reports success either way** —
the load "works", the program is simply not in core.

So: **verify core after loading.** Dump a few words at the expected addresses. If
they are zero, the format was wrong — almost always a missing `-r`.

For `monas` output, use the reader (`r`) plus READ-IN rather than `l`.

## `l` versus READ-IN

**`l file.rim`** loads into core and stops. `readrim` prints the entry address
from the transfer word but does not execute it. Start the program separately.

**READ-IN** mounts a tape in the reader (`r file.rim`) and then runs the
hardware read-in sequence from the console key. It decodes the same records, but
on the transfer word it sets `run = 1` and loads PC — **auto-starting** the
program. This is what the real machine does and needs no separate start.

`l` also **zeroes all of core** before loading. Any state left by a previous run
is gone, so load once and then run; reloading between experiments discards the
results being measured.

## Starting a loaded program

The entry point comes from the `.lst`, not from memory:

```bash
grep 'start ' program.lst
```

The assembled word on that line is the entry address. For a program with a boot
trampoline (`boot, jmp go` and `start boot`), the value the `start` directive
assembled is the address to use — not the address the `boot` label occupies,
though for a trampoline they usually coincide.

Adding or removing a single data word shifts every subsequent address, entry
point included. Re-read it from the listing after every change rather than
reusing a remembered octal number.

## Checking a tape without loading it

The last word tells you whether the tape will auto-start:

```python
with open('program.rim', 'rb') as f:
    data = f.read()

frames = [b & 0o77 for b in data if b & 0x80]   # data frames only
f1, f2, f3 = frames[-3:]
word = (f1 << 12) | (f2 << 6) | f3

if (word & 0o760000) == 0o600000:
    print(f"JMP to {word & 0o7777:04o} — auto-start present")
else:
    print(f"{word:06o} — no transfer word")
```

If the transfer word is missing, `start` was not the last thing assembled. See
`references/macro1-assembler.md` for what `start` actually does — assembly does
not stop there, so trailing data ends up on the tape *after* the transfer word
where no loader will ever reach it.

## After a crash

A program that ran through address 0 has been executing its own constant pool
and variables as instructions. Any `dac`/`dap`/`dio` bit patterns among that data
will have written to memory. Constants shift, counters go negative, and the
damage accumulates across repeated crash cycles.

**Reload the tape before debugging anything.** Otherwise the symptoms being
chased belong to the previous crash rather than to the bug. This is the single
most effective habit in PDP-1 debugging — corruption outlives the crash, and a
"new" symptom is frequently just old damage.
