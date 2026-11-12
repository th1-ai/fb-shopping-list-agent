# F&B Shopping List Agent

A Claude Code sub-agent + skill for hotel operators. It generates a grocery shopping list for the next few days based on projected guest counts (from your PMS) and current inventory levels (from a Google Sheet). Dry-runs first, writes to the sheet only after approval. It can also run on a schedule, at the autonomy level you set in [`AUTONOMY.md`](AUTONOMY.md).

Built on the **WAT framework** (Workflows, Agents, Tools): probabilistic AI handles reasoning, deterministic scripts handle execution.

**This repo is the agent and the workflow, not the scripts.** It is a markdown-only template. You supply one script that reads your PMS and your sheet and does the arithmetic; see [The tool you supply](#the-tool-you-supply). The agent runs it, checks the result, shows you the list and waits for your approval.

---

## What it does

- **Projects guest-nights** for the upcoming shopping window from your PMS
- **Reads master inventory + latest stock counts** from a Google Sheet
- **Computes per-item buy quantities** using two consumption models:
  - **Per-guest** — scales with projected guest-nights (e.g. eggs, butter, fruit)
  - **Par-level** — fixed minimum stock (e.g. cleaning supplies, condiments)
- **Auto-adds room-specific items** for special check-ins (e.g. flowers when a premium suite is arriving in the window)
- **Dry-runs first**, presents the list grouped by category, asks for approval, then writes
- **Stops instead of guessing** when the PMS returns no guests or the sheet is not set up, and flags stale stock counts
- **Runs on its own if you want it to** — on a schedule it reports, proposes or (at the top level, inside limits you set) writes the list, keeps a run log, and only interrupts you for exceptions. See [Run it on its own](#run-it-on-its-own)
- **Tracks calibration events** so the consumption model improves over time ("we ran out of X early last shop", "Y was over-stocked")

---

## What you need

- [Claude Code](https://code.claude.com/docs/en/overview) installed
- A PMS that returns upcoming reservations with guest counts (the reference setup is Cloudbeds, but any PMS with that data works)
- A Google Sheet (or equivalent) with two tabs:
  - `Inventory` — master list of items: `Item`, `Category`, `Unit`, `Model` (`per-guest` or `par-level`), `Guests/Unit`, `Par Min`, `Par Target`
  - `Stock` — most recent counts entered by staff, with the date of the count
  - plus a `Calibration` tab if you want to log "ran out" / "over-stocked" events
- A shopping-list script that follows [the tool contract](#the-tool-you-supply). This repo does not include one.

---

## Quick start

1. **Clone the repo**:

   ```bash
   git clone https://github.com/th1-ai/fb-shopping-list-agent.git
   cd fb-shopping-list-agent
   ```

2. **Copy the env template** and fill it in:

   ```bash
   cp .env.example .env
   ```

3. **Set up the inventory sheet** with the tabs listed above, and put its ID in `.env`.

4. **Add your shopping-list script** (for example at `tools/fb_shopping_list.py`). See [The tool you supply](#the-tool-you-supply).

5. **Open Claude Code** from the project root:

   ```bash
   claude
   ```

6. **Let Claude fill in the placeholders with you.** Paste this as your first prompt:

   > Read the README and set this agent up with me. Ask me for each value in the Customising table, one at a time, then replace the placeholders in `.claude/agents/fb-shopping-list.md`, `.claude/skills/fb-shopping-list/SKILL.md`, `.claude/settings.example.json` and `.env`. Do not guess a value. When you are done, list any `{{...}}` that is still in the repo.

   You can also edit the files by hand; the [Customising](#customising) table lists every placeholder.

7. **Restart Claude Code** (sub-agent files are loaded at session start), then ask:

   > "Generate the F&B shopping list for the next 4 days."

   Claude Code delegates to the `fb-shopping-list` sub-agent because of the `description` line in its front matter. You can also name it: "Use the fb-shopping-list agent to ...".

### Verify it works

- Run `/agents` in Claude Code. `fb-shopping-list` must be in the list.
- Type `/fb-shopping-list`. The skill must appear in the `/` menu.
- Ask for a shopping list. You must get a list marked **DRY RUN** with a window, a guest-night total and a "Next step" line, and nothing new in the shopping-list sheet.
- Approve it. Only now does the list appear in the sheet.

### Troubleshooting

| What you see | Likely cause |
|---|---|
| The agent is not in `/agents` | Claude Code was not started from the repo root, or was not restarted after you edited the agent file |
| "`SHEET_ID_INVENTORY` is not set" | `.env` is missing, or the value is still `{{SHEET_ID_INVENTORY}}` |
| "command not found" with `{{INVENTORY_TOOL}}` in it | A placeholder was not replaced in the agent or skill file |
| The agent refuses to give a list and reports 0 guest-nights | The PMS call failed or the window has no reservations. This stop is deliberate; check your PMS script and credentials |
| The list has a "stale stock" warning | The `Stock` tab was not updated since the last shop day |
| The agent says it is paused | `AUTONOMY.md` is missing, or its `Level:` line is missing, doubled or not one of 0, 1, 2, 3, PAUSED |
| A scheduled run logs "skipped" | The level is 0 or PAUSED. Set it to 1 or higher |
| A scheduled run reports a denied command | The agent ran a command that your scheduled settings file does not allow. Check that the tool command in the file is exactly the one in the skill |

---

## File structure

```
fb-shopping-list-agent/
├── README.md
├── AUTONOMY.md                                     # Autonomy level, limits, kill switch (you edit it)
├── .env.example
├── .gitignore
├── LICENSE
├── runs/
│   ├── README.md                                   # Run log and handoff formats
│   └── .gitkeep                                    # LOG.md and handoff/ appear here; git ignores them
└── .claude/
    ├── settings.example.json                       # Example permissions + hook for scheduled runs
    ├── hooks/
    │   └── autonomy-guard.py                       # Blocks tool calls that AUTONOMY.md does not permit
    ├── agents/
    │   └── fb-shopping-list.md                     # Sub-agent definition
    ├── skills/
    │   └── fb-shopping-list/
    │       └── SKILL.md                            # Skill (full process)
    └── agent-memory/
        └── fb-shopping-list/
            ├── MEMORY.md                           # Memory index (loaded at every run)
            └── example-feedback-pattern.md         # Example "memory note"
```

There is no `tools/` folder. You add your own script there (or anywhere you like) and point `{{INVENTORY_TOOL}}` at it.

---

## Customising

The files use placeholders so they can be adapted to any PMS + sheet stack. Replace these before first run:

| Placeholder | Where it is | What to put | Example |
|---|---|---|---|
| `{{HOTEL_NAME}}` | agent file | Hotel display name | `The Garden Inn` |
| `{{INVENTORY_TOOL}}` | agent file, skill, `settings.example.json` | Command that runs your shopping-list script | `python3 tools/fb_shopping_list.py` |
| `{{PMS_LOOKUP_TOOL}}` | skill, `settings.example.json` | Command that returns upcoming reservations with guest counts (used to cross-check a guest total) | `python3 tools/pms_lookup.py` |
| `{{PMS_PROPERTY_ID}}` | `.env` | PMS property ID | `123456789` |
| `{{SHEET_ID_INVENTORY}}` | `.env` | Google Sheet ID for the inventory + stock tabs | `1AbC...` |
| `{{SHEET_ID_SHOPPING_LIST}}` | `.env` | Google Sheet ID where the approved list is written | `1AbC...` (often the same sheet, different tab) |

`PREMIUM_ROOM_TYPE_ID` in `.env` is optional. Leave it empty unless you want an item added for each check-in of one room type.

---

## The tool you supply

The agent expects one command, `{{INVENTORY_TOOL}}`, with this behaviour. Any language works; Claude Code can help you write it for your PMS and sheet.

| Call | What it must do |
|---|---|
| `--dry-run` | Read the `Inventory` and `Stock` tabs and the PMS guest counts for the window, compute the list, print it. Write nothing. |
| (no flag) | Same computation, then write the list to the shopping-list sheet. Print the tab and the number of rows written. Exit with an error if the write fails. |
| `--days N` | Use an N-day coverage window instead of the default. Works with and without `--dry-run`. The agent puts `--dry-run` first. |
| `--log "Item" "ran-out\|over-stocked" "Notes"` | Append one row to the `Calibration` tab. Change nothing else. |

The output must show the window dates, the total guest-nights, the date of the latest stock count, and per item: category, on hand, to buy, unit. The tool must exit with an error when the PMS call fails. A silent fallback to 0 guests produces a list that looks valid and is wrong.

The two consumption models (per-guest and par-level) are defined in [`SKILL.md`](.claude/skills/fb-shopping-list/SKILL.md#consumption-models).

---

## Run it on its own

The agent can run on a schedule. How much it does alone is set by one line in [`AUTONOMY.md`](AUTONOMY.md):

| `Level:` | A scheduled run does this |
|---|---|
| `PAUSED` | Nothing. It logs why it stopped. This is the kill switch. A missing or unreadable level counts as PAUSED |
| `0` | Nothing. The agent works only when you ask in a session |
| `1` (default) | Dry run, checks, report. Writes only its own files in `runs/` |
| `2` | The same, with the full list marked "ready to approve" so you approve in one step |
| `3` | Writes the list to the shopping-list sheet itself, only when the run has zero warnings and stays inside the limits in `AUTONOMY.md` (default: 1 write per day, window of 7 days or less, 1 to 200 guest-nights, 60 lines or less). The first 3 runs are shadow runs that write nothing |

At no level does the agent send the list to a supplier, place an order, move money, edit the `Inventory` or `Stock` tabs, or log a calibration event that nobody reported. `AUTONOMY.md` has the full action table.

Every scheduled run appends one entry to `runs/LOG.md` and overwrites `runs/handoff/fb-shopping-list-agent.md`. The report starts with **Needs you**; when it says "Nothing needs you", you can stop reading. [`runs/README.md`](runs/README.md) has the formats. [`morning-routine-agent`](https://github.com/th1-ai/morning-routine-agent) can read both files for the daily briefing.

### 1. Make the scheduled settings file

```bash
cp .claude/settings.example.json .claude/settings.scheduled.json
```

Replace `{{INVENTORY_TOOL}}` and `{{PMS_LOOKUP_TOOL}}` in the copy with the same commands you used in the agent and skill files. The command text must be identical, because permission rules match the command as written.

The file is passed with `--settings`, so it applies to scheduled runs only. Your normal sessions do not change. It holds:

- **`permissions.allow`**: the dry run, the PMS lookup, `date`, and edits inside `runs/`. Nothing else. The command below uses the `dontAsk` permission mode, where everything that is not allowed is denied.
- **`permissions.deny`**: calibration logging, `rm`, `curl`, `wget`, `git push`, web access, and edits to `AUTONOMY.md`, `.env` and `.claude/`. Deny rules match the command text, so they are a second lock and not a sandbox.
- **`hooks.PreToolUse`**: runs [`autonomy-guard.py`](.claude/hooks/autonomy-guard.py) before every shell command. The script reads `AUTONOMY.md` and blocks every call to your tool at `PAUSED` or `0`, blocks a write below Level 3, and blocks `--log` always. It needs `python3`. Do not put this hook in `.claude/settings.json`: there it would also block a write that you approved in a session below Level 3.

### 2. The command

Example. Run it by hand once before you schedule it.

```bash
cd /path/to/fb-shopping-list-agent && claude -p "Use the fb-shopping-list agent for a scheduled run. Follow AUTONOMY.md. Nobody is available to answer questions. Return the agent's report unchanged." \
  --settings .claude/settings.scheduled.json \
  --permission-mode dontAsk \
  --permission-prompts none \
  --max-turns 30 \
  >> runs/cron.log 2>&1
```

- `-p` runs Claude Code without a terminal session and prints the result.
- `--permission-mode dontAsk` denies every tool call that would otherwise ask you. `--permission-prompts none` tells Claude that nobody can approve and not to retry (needs Claude Code v2.1.259 or later).
- `--max-turns` stops a run that loops.
- Do not add `--bare`. Bare mode skips sub-agents, skills and hooks, and this run needs all three.

### 3. Schedule it (cron example, macOS or Linux)

```
# Example: Monday and Thursday at 06:30. Use your own shop days.
30 6 * * 1,4 cd /path/to/fb-shopping-list-agent && /full/path/to/claude -p "Use the fb-shopping-list agent for a scheduled run. Follow AUTONOMY.md. Nobody is available to answer questions. Return the agent's report unchanged." --settings .claude/settings.scheduled.json --permission-mode dontAsk --permission-prompts none --max-turns 30 >> runs/cron.log 2>&1
```

cron starts with a short `PATH`, so give the full path to `claude` (find it with `which claude`) and make sure your tool's commands resolve too. Claude Code also has its own scheduling features; see [scheduled tasks](https://code.claude.com/docs/en/scheduled-tasks), [Desktop scheduled tasks](https://code.claude.com/docs/en/desktop-scheduled-tasks) and [cloud routines](https://code.claude.com/docs/en/routines). This template was not tested with them. A cloud run starts from a fresh clone, so it has no `.env` and no tool of yours.

**Sign-in for scheduled runs.** A scheduled run uses the login of the user that runs it. Where no browser login is possible, `claude setup-token` creates a long-lived token that you set as `CLAUDE_CODE_OAUTH_TOKEN`. If `ANTHROPIC_API_KEY` is set in that environment, `-p` uses the key and bills the API. Headless use of a personal Pro or Max plan is subject to Anthropic's usage policy; heavy or business-critical schedules should use an API key or a team plan.

### 4. Move up one level at a time

1. Run at the current level for at least 7 days or 4 shop days.
2. Read `runs/LOG.md`. Every entry must be one you agree with, and "Needs you" must have held only real exceptions.
3. Change the one `Level:` line in `AUTONOMY.md`.
4. For Level 3 only, also add these two lines to `permissions.allow` in `.claude/settings.scheduled.json`, then read the 3 shadow entries before the fourth run:

   ```
   "Bash({{INVENTORY_TOOL}})",
   "Bash({{INVENTORY_TOOL}} --days *)"
   ```

To go back, or to stop everything, change the `Level:` line. It takes effect at the next run.

### What was tested

The guard script was run against allow and block cases, and the command in step 2 was run with Claude Code v2.1.323 against a stand-in tool at Level 1 and Level 3. The cron line was not run from cron. Your own tool, PMS and sheet are yours to test: start at Level 1.

---

## How memory works

The agent has `memory: project` in its front matter, so Claude Code gives it a memory directory at `.claude/agent-memory/fb-shopping-list/` and loads the start of `MEMORY.md` from there at every run. The agent reads and writes files in that directory itself. Notes worth keeping:

- **Feedback** — patterns that improve consumption modelling (e.g. "guests average 1.2 eggs per breakfast, not 2 — adjust guests-per-unit on Eggs")
- **Project notes** — context that affects shopping (e.g. "August public holiday closes the supplier — buy a double load on the previous shop day")
- **References** — pointers to other systems (e.g. "the bakery order is not in this list; handled by a separate workflow")

[`example-feedback-pattern.md`](.claude/agent-memory/fb-shopping-list/example-feedback-pattern.md) shows the recommended format and [`MEMORY.md`](.claude/agent-memory/fb-shopping-list/MEMORY.md) indexes it. Delete the example and its index line once you have your own notes. The directory is committed to git, so do not let guest names or other personal data into it. Scheduled runs do not write memory; what the agent would have noted goes under "Needs you".

---

## Related agents

Part of [21 AI Agents That Run a Real Hotel](https://th1.ai/agent-stack). This agent sits well next to:

- [`cleaning-schedule-agent`](https://github.com/th1-ai/cleaning-schedule-agent) — plans changeovers from the same upcoming-reservation data; useful together when you plan a busy week
- [`morning-routine-agent`](https://github.com/th1-ai/morning-routine-agent) — the daily briefing; it can read this agent's `runs/LOG.md` and `runs/handoff/fb-shopping-list-agent.md`, and it is a natural place to approve the list on shop days
- [`villa-analytics-agent`](https://github.com/th1-ai/villa-analytics-agent) — property analytics; useful when you review whether the consumption values still fit

---

## License

MIT — see [LICENSE](LICENSE).
