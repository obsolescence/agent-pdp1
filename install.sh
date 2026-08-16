#!/usr/bin/env bash
# agent-pdp1 — install
#
# Updates the PDP-1 emulator to the dbg branch (where the simulator
# handles user and agent concurrently), installs the agent tools, and
# points you at the skills.
#
# Steps:
#   1. take ownership of this directory  (sudo; undo the sudo git clone)
#   2. emulator update + rebuild         (no sudo)
#   3. agent tools -> /usr/local/bin     (sudo)
#   4. smoke test: hello over 1040
#   5. where the skills live

set -u

SELF_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
EMU_DIR="/opt/pidp1/src/blincolnlights/pdp1"
EMU_PID=""
NC="$(command -v nc || command -v ncat)"

say()  { echo "== $*"; }
fail() { echo "ERROR: $*" >&2; exit 1; }
cleanup() { [ -n "$EMU_PID" ] && kill "$EMU_PID" 2>/dev/null; }
trap cleanup EXIT

# --------------------------------------------------------------- ownership

say "taking ownership of $SELF_DIR"
if [ "$(stat -c '%U' "$SELF_DIR" 2>/dev/null)" = "$(id -un)" ]; then
    echo "  already owned by you ($(id -un)) — nothing to do"
else
    echo "  after a 'sudo git clone' the package is owned by root; you need"
    echo "  ownership to update it (skills/update.sh) and edit files."
    read -r -p "  Take ownership now (needs sudo)? [Y/n] " ans
    case "${ans:-y}" in
        ""|[Yy]*)
            sudo chown -R "$(id -un):$(id -gn)" "$SELF_DIR" || fail "sudo failed — see above"
            echo "  ok — $SELF_DIR now belongs to $(id -un)"
            ;;
        *)
            echo "  Skipped. You can do it later:  sudo chown -R $(id -un):$(id -gn) $SELF_DIR"
            ;;
    esac
fi

# ---------------------------------------------------------------- pre-flight

say "checking prerequisites"
for tool in git make gcc python3; do
    command -v "$tool" >/dev/null 2>&1 || fail "missing: $tool — install it, then re-run"
done
command -v nc >/dev/null 2>&1 || command -v ncat >/dev/null 2>&1 || \
    fail "missing: nc or ncat — install it, then re-run"

git -C "$EMU_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1 \
    || fail "$EMU_DIR is not a git repo — install the emulator first"
git -C "$EMU_DIR" rev-parse --verify HEAD >/dev/null 2>&1 || fail "broken repo at $EMU_DIR"

# ------------------------------------------------------------- emulator step

say "emulator update"
echo "  With the dbg version update, the pdp1 simulator can now handle"
echo "  user and agent concurrently."
read -r -p "  Update $EMU_DIR to dbg and rebuild? [Y/n] " ans
case "${ans:-y}" in
    ""|[Yy]*) ;;
    *) echo "  Skipped. (You can do it later: see the failsafe update notes in the pdp1-plumbing skill.)"; SKIP_EMU=1 ;;
esac

if [ -z "${SKIP_EMU:-}" ]; then
    git -C "$EMU_DIR" fetch origin || fail "git fetch failed — check your network"
    if git -C "$EMU_DIR" stash push -u -m "local changes before dbg" 2>/dev/null; then
        echo "  local changes were stashed:  git stash list  to recover"
    fi
    git -C "$EMU_DIR" checkout dbg || fail "checkout dbg failed — is the branch on origin?"
    git -C "$EMU_DIR" pull --ff-only origin dbg || \
        fail "dbg update failed — see git output above (offline, or local commits diverge from origin)"
    echo "  building — takes a couple of minutes"
    ( cd "$EMU_DIR" && make ) || fail "make failed — see the output above"
    [ -x "$EMU_DIR/pdp1" ] || fail "build did not produce $EMU_DIR/pdp1"
fi

# ------------------------------------------------------------------ tools

say "agent tools -> /usr/local/bin"
echo "  pdp1dbg.py — the port-1040 debug client"
echo "  pdp1_dpy   — the Type 30 screen reader"
echo "  (symlinks, so package updates reach them automatically)"
read -r -p "  Install them now (needs sudo)? [Y/n] " ans
case "${ans:-y}" in
    ""|[Yy]*) ;;
    *) echo "  Skipped — copy the two scripts to /usr/local/bin yourself if you want them."; SKIP_TOOLS=1 ;;
esac

if [ -z "${SKIP_TOOLS:-}" ]; then
    DBG_TOOL="$SELF_DIR/skills/pdp1-debugging/scripts/pdp1dbg.py"
    DPY_TOOL="$SELF_DIR/skills/pdp1-type30-vision/scripts/pdp1_dpy"
    [ -f "$DBG_TOOL" ] || fail "missing: $DBG_TOOL — package incomplete?"
    [ -f "$DPY_TOOL" ] || fail "missing: $DPY_TOOL — package incomplete?"
    sudo ln -sfn "$DBG_TOOL" /usr/local/bin/pdp1dbg.py || fail "sudo failed — see above"
    sudo ln -sfn "$DPY_TOOL" /usr/local/bin/pdp1_dpy || fail "sudo failed — see above"
    [ -x "$(readlink -f /usr/local/bin/pdp1dbg.py)" ] || fail "pdp1dbg.py link is broken"
    [ -x "$(readlink -f /usr/local/bin/pdp1_dpy)" ] || fail "pdp1_dpy link is broken"
    command -v pdp1dbg.py >/dev/null && command -v pdp1_dpy >/dev/null || \
        fail "installed, but /usr/local/bin is not on your PATH"
fi

# -------------------------------------------------------------- smoke test

say "smoke test"
if [ -z "${SKIP_EMU:-}" ]; then
    if ! "$NC" -z 127.0.0.1 1040 2>/dev/null; then
        echo "  starting a headless emulator for the test"
        ( cd "$EMU_DIR" && exec ./pdp1 -t ) & EMU_PID=$!
    fi
    OUT=""
    i=0
    while [ "$i" -lt 10 ]; do
        OUT="$("$NC" -w 1 127.0.0.1 1040 <<< 'hello')"
        case "$OUT" in *proto=1*) break ;; esac
        i=$((i+1)); sleep 1
    done
    case "$OUT" in
        *proto=1*) echo "  ok — 1040 answered: $OUT" ;;
        *) fail "no hello from port 1040: $OUT (older emulator still running? stop it, then re-run)" ;;
    esac
else
    echo "  skipped — emulator update was skipped"
fi

# ------------------------------------------------------------------ skills

say "skills"
echo "  knowledge and tools for agents: $SELF_DIR/skills"
echo "  (frozen + curated; ./skills/update.sh refreshes them)"
echo "  Hermes users:    run ./setup-hermes.sh next — it wires the skills,"
echo "                   the learnings file and SOUL.md into your profile"
echo "  other agents:    point yours at $SELF_DIR/skills — see README.txt"

say "done"
