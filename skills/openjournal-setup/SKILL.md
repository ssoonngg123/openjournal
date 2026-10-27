---
name: openjournal-setup
description: Install OpenJournal, scan coding agent sessions, and launch the review workbench. Use when user wants to set up openjournal, review their traces, get started with trace curation, or says "setup openjournal". Triggers on "setup openjournal", "install openjournal", "review my traces", or first-time openjournal requests.
---

# OpenJournal Setup

Interactive setup wizard. Walk the user through each step. Only pause when user input is required. Fix problems yourself when possible.

**Principle:** When something is broken or missing, fix it. Don't tell the user to go fix it themselves unless it genuinely requires their action. If a dependency is missing, install it. If a command fails, diagnose and repair.

## 0. Preflight

Check if `openjournal` is already installed:
- `command -v openjournal && openjournal status`
- `test -x ~/.openjournal-venv/bin/openjournal && ~/.openjournal-venv/bin/openjournal status`

**If found and the user is just resuming:** skip to Step 2. If only `~/.openjournal-venv/bin/openjournal` exists, use that full path for commands below.
**If found but the user wants the latest:** re-run Step 1's installer (idempotent — it'll fast-forward the checkout and reinstall in place), then continue to Step 2.
**If not found:** Continue to Step 1.

## 1. Install

Use the bundled installer scripts. They detect a Python 3.10+ interpreter, create an isolated venv at `~/.openjournal-venv`, and `pip install -e` the repo. Idempotent — safe to re-run.

First, ask: "Do you want the browser workbench? (Recommended — it's the primary review surface. Otherwise the CLI works alone.)" Use the answer to pick whether to pass the frontend flag below. If the user intends to share traces or enroll in AnonLab, also pass the sharing flag so the managed secret scanners are ready before packaging. Do not use Homebrew for those scanners.

**macOS / Linux / WSL / Git Bash on Windows:**

```bash
if [ -d ~/openjournal/.git ]; then
  git -C ~/openjournal pull --ff-only
else
  git clone https://github.com/anonymous-org/openjournal.git ~/openjournal
fi

# Pick ONE based on the user's answer above:
~/openjournal/scripts/install.sh                    # CLI only
~/openjournal/scripts/install.sh --with-frontend    # also build the browser workbench (needs Node.js)
# Add --with-sharing to either command for sharing or AnonLab enrollment.
```

**Native Windows PowerShell** (no WSL / Git Bash):

```powershell
if (Test-Path "$HOME\openjournal\.git") {
  git -C "$HOME\openjournal" pull --ff-only
} else {
  git clone https://github.com/anonymous-org/openjournal.git "$HOME\openjournal"
}

# Pick ONE based on the user's answer above:
powershell -ExecutionPolicy Bypass -File "$HOME\openjournal\scripts\install.ps1"                # CLI only
powershell -ExecutionPolicy Bypass -File "$HOME\openjournal\scripts\install.ps1" -WithFrontend  # also build the browser workbench (needs Node.js)
# Add -WithSharing to either command for sharing or AnonLab enrollment.
```

The script's exit code and printed output tell you exactly what to do next. Common failure modes the script surfaces directly:

- **Python 3.10+ not found** — install via the platform hint the script prints, then re-run. macOS users may also need `xcode-select --install` to get a working `python3`.
- **`python3 -m venv` fails on Debian/Ubuntu** — run `sudo apt install -y python3-venv python3-full`, then re-run the script.
- **`node` / `npm` missing** when `--with-frontend` was requested — the script skips the frontend with a warning. Install Node.js (macOS: `brew install node`, Linux: `sudo apt-get install -y nodejs npm`, Windows: nodejs.org) and re-run with the flag.
- **A managed secret scanner download fails** when `--with-sharing` / `-WithSharing` was requested — check the printed network or checksum diagnostic and re-run the same installer. Do not bypass the sharing gate.

Verify (POSIX):

```bash
~/.openjournal-venv/bin/openjournal status
```

Verify (PowerShell):

```powershell
& "$HOME\.openjournal-venv\Scripts\openjournal.exe" status
```

**Network or cluster storage.** If OpenJournal reports that its state directory is on network or shared storage (NFS, Lustre, GPFS, and similar; common on HPC clusters), explain both options and let the user choose:

- If the machine has private, persistent local storage: stop OpenJournal, copy the whole state directory there (keep the original), set `OPENJOURNAL_HOME` to the copy, and restart.
- If it has none (for example, home is on NFS, scratch is purged, and `/tmp` is wiped on reboot): with the user's agreement, run `openjournal storage allow-network`, then restart OpenJournal. The state stays where it is and is used from this machine only. Do not move the state to scratch space that is purged automatically.

If OpenJournal later reports that the state is set up for another machine, ask the user to stop OpenJournal on that machine before running `openjournal storage allow-network --take-over`.

## 2. Scan Sessions

Discover all local coding agent sessions:

```bash
~/.openjournal-venv/bin/openjournal scan
```

This indexes sessions from Claude Code, Codex, Gemini CLI, OpenCode, OpenClaw, Kimi CLI, and Cline — whatever is present on the machine.

Show the user a summary: "Found N sessions across M sources."

If zero sessions found:
- Check if the user has any supported coding agents installed
- Common issue: sessions live in non-default paths — ask the user

## 3. Score & Auto-Triage (optional but recommended)

Ask: "Would you like me to auto-score your sessions? Each session gets two AI ratings: a failure-value score (1-5, the primary signal for finding teachable agent failures on real work) and a productivity score (1-5, legacy compatibility)."

If yes:

```bash
~/.openjournal-venv/bin/openjournal score --batch --source failure-corpus --auto-triage
```

`--source failure-corpus` scopes to the supported sources (claude, codex, opencode, openclaw); auto-triage archives productivity-1 sessions only when failure value is 1-2.

Show summary: "N sessions scored. Failure-value distribution: ... M productivity-1 low-failure-value sessions auto-archived as noise."

If no: skip to Step 4.

## 4. Launch Workbench

Ask: "How would you like to review your traces?"

**Option A — Browser UI (recommended for local machines):**

Check whether the frontend is already built:

```bash
test -f ~/openjournal/openjournal/web/frontend/dist/index.html && echo built || echo missing
```

If missing, re-run the installer with the frontend flag (POSIX):

```bash
~/openjournal/scripts/install.sh --with-frontend
```

PowerShell equivalent:

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME\openjournal\scripts\install.ps1" -WithFrontend
```

Then start the workbench:

```bash
~/.openjournal-venv/bin/openjournal open
```

This starts or reuses the local daemon, waits a bounded time for readiness, opens
the browser, and then returns. Do not wait for a foreground daemon to exit.

Tell the user: "Your workbench is open at localhost:8384. Everything is 100% local. Use the Inbox to triage traces, Search to find sessions, and Bundles to assemble exports."

**Option B — Terminal review (for remote VMs or headless environments):**

```bash
~/.openjournal-venv/bin/openjournal inbox --json --limit 15
```

Parse the JSON and present traces as a numbered list. Then guide triage interactively.

**For remote VMs:** use `openjournal serve --remote` in a dedicated terminal or
background process and follow the SSH tunnel command it prints. `serve` is a
foreground, long-running daemon command; do not wait for it to exit before
continuing the setup conversation.

## 5. Done

Show summary:
- OpenJournal version installed
- Number of sessions indexed
- Number scored/triaged (if applicable)
- How to access the workbench

Tell the user:
- "You can review and share traces anytime with `/openjournal`"
- "Score sessions with `/openjournal-score`"
- "Everything stays 100% local until you explicitly choose to share"

## Before sharing: source scope + project confirmation

Sharing/exporting is gated until two one-time confirmations are set — this
prevents accidentally contributing traces from a source or project the user
didn't intend. Local review and scoring do **not** need these; only the first
share does. The workbench Share flow and `openjournal` export both block until
both are in place:

- **Source scope** — explicitly choose which agents' traces are in scope:
  ```bash
  ~/.openjournal-venv/bin/openjournal config --source <claude|codex|gemini|all>
  ```
- **Project confirmation** — confirm the projects whose traces may be shared:
  ```bash
  ~/.openjournal-venv/bin/openjournal config --confirm-projects
  ```

It's fine to defer this until the user is ready to contribute — if they try to
share first, OpenJournal prints the exact command to run.

## Troubleshooting

**openjournal command not found after install:** Use `~/.openjournal-venv/bin/openjournal` directly, or add the venv bin directory to your shell PATH.

**No sessions found:** Make sure you've used a supported coding agent (Claude Code, Codex, Gemini CLI, etc.) on this machine. Sessions are stored in agent-specific directories under your home folder.

**Permission errors on scan:** OpenJournal reads session files from `~/.claude/`, `~/.codex/`, etc. Ensure these directories are readable.

**Browser UI shows a placeholder page:** The frontend has not been built yet. Re-run the installer with the frontend flag: `~/openjournal/scripts/install.sh --with-frontend` (or `.\scripts\install.ps1 -WithFrontend` on PowerShell). Requires Node.js.

**venv issues on Linux:** If you see `externally-managed-environment`, make sure you're installing into the venv: `python3 -m venv ~/.openjournal-venv && ~/.openjournal-venv/bin/python -m pip install -e ~/openjournal`.
