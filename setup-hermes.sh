#!/usr/bin/env bash
# agent-pdp1 — setup-hermes
#
# Part 2 of the agent-pdp1 install. Run AFTER install.sh.
# Wires the PDP-1 knowledge into Hermes Agent and helps you get
# Hermes itself ready.
#
#   1. your LLM API key   (you do this — the script explains how)
#   2. install Hermes     (one command — or the script runs it for you)
#   3. the PDP-1 skills   (the script does this)

set -u

SELF_DIR="$(cd "$(dirname "$0")" && pwd)"
PKG_DIR="$SELF_DIR"
HERMES_BIN=""

say()  { echo "== $*"; }
fail() { echo "ERROR: $*" >&2; exit 1; }

# ------------------------------------------------------------ step 1: the key

say "step 1: your LLM API key"
echo "  Hermes uses an LLM provider as its brains, and that needs an API"
echo "  key. You get the key yourself — this script never sees it."
echo ""
echo "  We use DeepSeek. Why:"
echo "    - very cheap — a few dollars a month even with serious use"
echo "    - you prepay (about \$20) by PayPal or card — no subscription,"
echo "      no risk of surprise bills"
echo "    - not the most powerful model, but excellent for the simple,"
echo "      sparse world of PDP-1 programming"
echo "  How:  go to platform.deepseek.com  ->  API Keys  ->  create a key,"
echo "  then paste it into 'hermes setup' a few steps from now."
echo ""

# ------------------------------------------------------- step 2: install hermes

say "step 2: install Hermes"
if command -v hermes >/dev/null 2>&1; then
    HERMES_BIN="$(command -v hermes)"
    echo "  Hermes is already installed: $(hermes --version 2>/dev/null | head -1)"
elif [ -x "$HOME/.local/bin/hermes" ]; then
    HERMES_BIN="$HOME/.local/bin/hermes"
    echo "  Hermes is already installed: $("$HERMES_BIN" --version 2>/dev/null | head -1)"
else
    echo "  Installing Hermes is one command:"
    echo "    curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash"
    echo "  (This downloads and runs the official installer. It sets up"
    echo "   Python, Node and the 'hermes' command for you — no sudo needed.)"
    read -r -p "  Run it now? [y/N] " ans
    case "${ans:-n}" in
        y|Y)
            curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash \
                || fail "the Hermes installer failed — see the output above"
            export PATH="$HOME/.local/bin:$PATH"
            HERMES_BIN="$(command -v hermes)"
            echo "  (New shells will find 'hermes' too: source ~/.bashrc)"
            ;;
        *)
            echo "  Fine — run that command yourself, then re-run this script:"
            echo "    ./setup-hermes.sh"
            exit 0
            ;;
    esac
fi

# --------------------------------------------------- step 3: the PDP-1 skills

say "step 3: the PDP-1 skills"
if [ ! -d "$HOME/.hermes/profiles" ]; then
    echo "  No Hermes profile yet. Run 'hermes setup' once (it asks for your"
    echo "  API key and creates your profile), then re-run this script:"
    echo "    ./setup-hermes.sh"
    exit 1
fi

mapfile -t PROFILES < <(find "$HOME/.hermes/profiles" -mindepth 1 -maxdepth 1 -type d | sort)
case "${#PROFILES[@]}" in
    0)
        echo "  No Hermes profile yet. Run 'hermes setup' once (it asks for"
        echo "  your API key and creates your profile), then re-run this script."
        exit 1
        ;;
    1)
        PROFILE="$(basename "${PROFILES[0]}")"
        echo "  Using your profile: $PROFILE"
        ;;
    *)
        echo "  You have several Hermes profiles:"
        for i in "${!PROFILES[@]}"; do
            echo "    $((i+1))) $(basename "${PROFILES[$i]}")"
        done
        read -r -p "  Which one gets the PDP-1 knowledge? [1-${#PROFILES[@]}] " ans
        case "$ans" in
            *[!0-9]*|"") fail "pick a number" ;;
            *) [ "$ans" -ge 1 ] && [ "$ans" -le "${#PROFILES[@]}" ] \
                   || fail "pick a number between 1 and ${#PROFILES[@]}"
               PROFILE="$(basename "${PROFILES[$((ans-1))]}")" ;;
        esac
        ;;
esac

SKILLS_DIR="$HOME/.hermes/profiles/$PROFILE/skills"
mkdir -p "$SKILLS_DIR"

echo "  symlinking the frozen skills — a symlink is a pointer, so updates"
echo "  to agent-pdp1 reach your agent automatically"
for d in "$PKG_DIR"/skills/*/; do
    ln -sfn "$d" "$SKILLS_DIR/$(basename "$d")"
done

echo "  copying pdp1-learnings — YOUR agent's own file, where it keeps"
echo "  what it learns. A real copy, never a symlink: updates must not"
echo "  overwrite it"
rm -rf "$SKILLS_DIR/pdp1-learnings"
cp -r "$PKG_DIR/hermes-specific/pdp1-learnings" "$SKILLS_DIR/"

echo "  copying SOUL.md — the rules file. Your agent reads it with every"
echo "  request; it keeps the agent disciplined about the machine"
cp "$PKG_DIR/hermes-specific/SOUL.md" "$HOME/.hermes/profiles/$PROFILE/SOUL.md"

# ------------------------------------------------------------------ verify

say "verify"
echo "  installed for profile '$PROFILE':"
ls "$SKILLS_DIR" | grep 'pdp1' | sed 's/^/    /'
COUNT="$(ls "$SKILLS_DIR" | grep -c 'pdp1' 2>/dev/null || true)"
if [ "${COUNT:-0}" -eq 0 ]; then
    fail "no pdp1 skills found in $SKILLS_DIR"
fi

say "next steps"
echo "  - not done yet?  hermes setup     (paste your DeepSeek API key,"
echo "                                     pick deepseek-v4-flash)"
echo "  - then:           hermes           (start chatting — try:"
echo "                                     'load the pdp1-debugging skill')"
echo "  - package updates: /opt/agent-pdp1/skills/update.sh"

say "done"
