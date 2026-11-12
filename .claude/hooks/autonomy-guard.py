#!/usr/bin/env python3
"""PreToolUse guard for scheduled runs of the fb-shopping-list agent.

Load it only through the scheduled-run settings file (see README, "Run it on
its own"). It reads the Bash command Claude Code is about to run and blocks
calls to the shopping-list tool that AUTONOMY.md does not permit:

  Level: PAUSED or Level: 0              -> every call to the tool is blocked
  no file, no single readable Level line -> same as PAUSED
  --log (calibration event)              -> always blocked in a scheduled run
  --dry-run                              -> allowed at Level 1, 2 and 3
  write (no --dry-run)                   -> allowed at Level 3 only

Usage (from the hook config):  autonomy-guard.py "<your shopping-list command>"
Exit 0 = no objection (the normal permission rules still apply).
Exit 2 = block; the text on stderr is shown to Claude as the reason.
"""
import json
import os
import sys

AUTONOMY = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "AUTONOMY.md",
)


def block(reason):
    sys.stderr.write("autonomy-guard: " + reason + "\n")
    sys.exit(2)


def read_level():
    """Return 0-3 or "PAUSED". The file must hold exactly one `Level:` line
    whose value is 0, 1, 2, 3 or PAUSED; anything else counts as PAUSED."""
    try:
        with open(AUTONOMY, encoding="utf-8") as fh:
            lines = [ln.strip() for ln in fh.read().splitlines()]
    except OSError:
        return "PAUSED"
    values = [ln[len("Level:"):].strip() for ln in lines if ln.startswith("Level:")]
    if len(values) != 1 or values[0] not in ("0", "1", "2", "3"):
        return "PAUSED"
    return int(values[0])


def main():
    tool = " ".join(sys.argv[1:]).strip()
    if not tool or "{{" in tool:
        block("the guard has no tool command. Replace the placeholder in the hook config.")
    try:
        data = json.load(sys.stdin)
    except ValueError:
        block("could not read the hook input.")
    if data.get("tool_name") != "Bash":
        sys.exit(0)
    command = " ".join(str((data.get("tool_input") or {}).get("command", "")).split())
    calls = command.count(" ".join(tool.split()))
    if calls == 0:
        sys.exit(0)

    level = read_level()
    if level == "PAUSED":
        block("AUTONOMY.md is PAUSED (or has no single readable Level line). Do not run the shopping-list tool. Log the skipped run and stop.")
    if level == 0:
        block("AUTONOMY.md is at Level 0. Scheduled runs are off. Log the skipped run and stop.")
    if "--log" in command:
        block("calibration events are logged only when the operator asks in person, not in a scheduled run.")
    if calls == 1 and "--dry-run" in command:
        sys.exit(0)
    if level == 3:
        sys.exit(0)
    block(
        "writing the list needs Level 3 and AUTONOMY.md is at Level %d. "
        "Do not retry. Report the list as a proposal under 'Needs you'." % level
    )


if __name__ == "__main__":
    main()
