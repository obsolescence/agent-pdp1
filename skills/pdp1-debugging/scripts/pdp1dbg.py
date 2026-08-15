#!/usr/bin/env python3
"""Talk to the blincolnlights PDP-1 debug service, with labels from a .lst.

The protocol (DEBUG_PROTOCOL_SPEC.md) is line-oriented and easy to drive by
hand, but two things are worth not rewriting every session: the framing
(replies end at '+' or '-', and '!' events interleave at any time) and the
symbol table (the service speaks octal only, so every address has to be
looked up in the listing by eye).

    pdp1dbg.py --lst tic.lst 'w pc go' 'b chkwin' 'run 100000' 's'
    pdp1dbg.py --lst tic.lst trace 20
    pdp1dbg.py -                        # commands on stdin, one per line

Labels are substituted into commands and annotated in replies, both ways.
Exit status is 1 if any command answered '-'.

Stdlib only.  Import Dbg and Listing for anything this CLI does not cover.
"""

import argparse
import re
import socket
import sys

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 1040


class Listing:
    """Labels and source lines out of a macro1_1 .lst.

    The listing is fixed-column:

        cols 0-4   line number, blank on literal-pool and macro output
        cols 6-10  address, blank on equates and pseudo-ops
        cols 12-17 assembled word
        col  18+   source text

    An equate has a word and no address, which is exactly why the columns
    are read by position and not by splitting on whitespace.
    """

    def __init__(self, path=None):
        self.byname = {}        # label -> address
        self.byaddr = {}        # address -> label
        self.source = {}        # address -> source text
        self.word = {}          # address -> assembled word
        self.path = path
        if path:
            self.load(path)

    def load(self, path):
        with open(path, "r", errors="replace") as f:
            for line in f:
                line = line.rstrip("\n")
                if len(line) < 18:
                    continue
                addr, word, text = line[6:11], line[12:18], line[18:]
                if not re.fullmatch(r"[0-7]{5}", addr):
                    continue
                a = int(addr, 8)
                if re.fullmatch(r"[0-7]{6}", word):
                    self.word[a] = int(word, 8)
                text = text.strip()
                if text:
                    self.source[a] = text
                m = re.match(r"([^\s,/]+),", text)
                if m:
                    name = m.group(1)
                    self.byname[name] = a
                    self.byaddr.setdefault(a, name)

    def resolve(self, tok):
        """Label -> '%o', or None if tok is not a known label."""
        a = self.byname.get(tok)
        return None if a is None else "%o" % a

    def label(self, addr):
        """Exact label, or 'name+n' for an address inside a labelled span."""
        if addr in self.byaddr:
            return self.byaddr[addr]
        best = None
        for a, n in self.byaddr.items():
            if a < addr and (best is None or a > best[0]):
                best = (a, n)
        if best and addr - best[0] <= 32:
            return "%s+%d" % (best[1], addr - best[0])
        return None


# words in a command that name an address and may be given as a label
_ADDRISH = re.compile(r"\bM\[([A-Za-z][^\]]*)\]|(?<![\w+\-])([A-Za-z][\w.]*)")

# commands whose *first* argument is an address; everything else is left alone
_TAKES_ADDR = {
    "b", "break", "ub", "nobreak", "wp", "uwp", "until", "e", "examine",
    "ex", "d", "deposit", "dep", "poke", "z", "go", "cont", "c", "readin",
}


class Dbg:
    """One connection.  At most one command outstanding, as the spec requires."""

    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT, timeout=30.0,
                 lst=None):
        self.sock = socket.create_connection((host, port), timeout)
        self.sock.settimeout(timeout)
        self.f = self.sock.makefile("rw", encoding="ascii", newline="\n")
        self.lst = lst or Listing()
        self.events = []        # '!' lines seen, oldest first

    def close(self):
        try:
            self.f.close()
            self.sock.close()
        except OSError:
            pass

    # ---------------------------------------------------------- raw protocol

    def send(self, line):
        """Send one command, return (ok, [data lines], final line).

        '!' lines that arrive before the reply are collected in .events, not
        returned: they may describe a stop caused by *another* connection.
        """
        self.f.write(line + "\n")
        self.f.flush()
        data = []
        while True:
            raw = self.f.readline()
            if not raw:
                raise EOFError("server closed the connection")
            raw = raw.rstrip("\r\n")
            kind, rest = raw[:1], raw[1:].lstrip()
            if kind == "!":
                self.events.append(rest)
            elif kind == ":":
                data.append(rest)
            elif kind in "+-":
                return kind == "+", data, rest
            else:
                data.append(raw)          # shouldn't happen; don't lose it

    # ------------------------------------------------------------ label help

    def expand(self, line):
        """Replace labels with octal addresses where an address is expected."""
        if not self.lst.byname:
            return line
        parts = line.split()
        if not parts:
            return line
        head = parts[0].lower()

        def sub(m):
            inner, bare = m.group(1), m.group(2)
            tok = inner if inner is not None else bare
            got = self.lst.resolve(tok.strip())
            if got is None:
                return m.group(0)
            return "M[%s]" % got if inner is not None else got

        # the verb itself is never a label
        rest = " ".join(parts[1:])
        if head in _TAKES_ADDR or head in ("w", "run", "trace", "step",
                                           "next", "s", "reg", "r"):
            rest = _ADDRISH.sub(sub, rest)
        return (parts[0] + " " + rest).strip()

    def annotate(self, text):
        """Tag 6-digit octal addresses in a reply with their label."""
        if not self.lst.byaddr:
            return text

        def sub(m):
            key, val = m.group(1), m.group(2)
            if key not in ("pc", "at", "addr", "to", "from", "ret", "ma"):
                return m.group(0)
            if key == "at":
                return m.group(0)          # a word, not an address
            name = self.lst.label(int(val, 8))
            return m.group(0) + ("(%s)" % name if name else "")

        return re.sub(r"\b(\w+)=([0-7]{6})\b", sub, text)

    def source_at(self, addr):
        return self.lst.source.get(addr)

    # ------------------------------------------------------------ convenience

    def status(self):
        """Status as a dict of key -> string."""
        okc, _, final = self.send("s")
        if not okc:
            raise RuntimeError(final)
        return dict(kv.split("=", 1) for kv in final.split() if "=" in kv)

    def reg(self, name):
        okc, _, final = self.send("reg " + name)
        if not okc:
            raise RuntimeError(final)
        return int(final.split("=", 1)[1], 8)

    def examine(self, addr, n=1):
        okc, data, final = self.send("e %o %d" % (addr, n))
        if not okc:
            raise RuntimeError(final)
        out = []
        for line in data:
            out.extend(int(w, 8) for w in line.split()[1:])
        return out


def cmd_where(dbg, arg):
    """Source context around PC, from the listing."""
    st = dbg.status()
    pc = int(st["pc"], 8)
    n = int(arg) if arg else 4
    addrs = sorted(a for a in dbg.lst.source if pc - n <= a <= pc + n)
    if not addrs:
        print("  pc=%06o is not in %s" % (pc, dbg.lst.path or "the listing"))
        return True
    for a in addrs:
        print("  %s %06o %06o  %s" % ("->" if a == pc else "  ", a,
                                      dbg.lst.word.get(a, 0),
                                      dbg.lst.source[a]))
    return True


def cmd_check(dbg, arg):
    """Compare core against the listing: what has the program rewritten?

    Every difference is either self-modifying code doing its job (a 'dap'
    return cell, a dispatch word) or damage.  Knowing which words changed
    is the fastest way to tell a fresh bug from the leftovers of the last
    crash -- see references/debugging.md.
    """
    if not dbg.lst.word:
        print("  no listing loaded; --lst is required for check")
        return False
    addrs = sorted(dbg.lst.word)
    lo, hi = addrs[0], addrs[-1]
    live = dbg.examine(lo, hi - lo + 1)
    ndiff = 0
    for a in addrs:
        want, got = dbg.lst.word[a], live[a - lo]
        if want != got:
            ndiff += 1
            print("  %06o %-10s %06o -> %06o  %s" %
                  (a, dbg.lst.label(a) or "", want, got,
                   dbg.lst.source.get(a, "")))
    print("  %d of %d words differ from the listing" % (ndiff, len(addrs)))
    return True


LOCAL = {"where": cmd_where, "check": cmd_check}


def run_cli(argv=None):
    ap = argparse.ArgumentParser(
        description="drive the PDP-1 debug service on port 1040")
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--lst", help="macro1_1 listing, for label names")
    ap.add_argument("--timeout", type=float, default=30.0,
                    help="socket timeout; raise it for long 'wait'")
    ap.add_argument("--raw", action="store_true",
                    help="no label substitution or annotation")
    ap.add_argument("cmd", nargs="*",
                    help="protocol commands, plus the listing-only 'where "
                         "[n]' and 'check'; '-' reads them from stdin")
    a = ap.parse_args(argv)

    lst = Listing(a.lst) if a.lst else Listing()
    try:
        dbg = Dbg(a.host, a.port, a.timeout, lst)
    except OSError as e:
        sys.exit("connect %s:%d: %s\n"
                 "  is the emulator running?  pdp1control stat  (or: ps aux | grep pdp1)" %
                 (a.host, a.port, e))

    cmds = []
    for c in a.cmd:
        if c == "-":
            cmds.extend(l.strip() for l in sys.stdin if l.strip())
        else:
            cmds.append(c)
    if not cmds:
        cmds = ["s"]

    failed = False
    for cmd in cmds:
        head = cmd.split()[0].lower() if cmd.split() else ""
        if head in LOCAL and not a.raw:
            print("> " + cmd)
            if not LOCAL[head](dbg, cmd.split()[1] if len(cmd.split()) > 1
                               else None):
                failed = True
            continue
        line = cmd if a.raw else dbg.expand(cmd)
        okc, data, final = dbg.send(line)
        print("> " + line)
        istrace = line.split()[:1] == ["trace"]
        for d in data:
            out = d if a.raw else dbg.annotate(d)
            if istrace and not a.raw:
                m = re.match(r"pc=([0-7]{6})", d)
                src = dbg.source_at(int(m.group(1), 8)) if m else None
                if src:
                    out += "    " + src
            print("  " + out)
        if okc:
            print("  " + (final if a.raw else dbg.annotate(final)))
        else:
            print("  ERROR " + final)
            failed = True
    for e in dbg.events:
        print("  ! " + (e if a.raw else dbg.annotate(e)))
    dbg.close()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(run_cli())
