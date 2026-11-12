# F&B Shopping List Agent

A Claude Code sub-agent + skill for hotel operators. It generates a grocery shopping list for the next few days based on projected guest counts (from your PMS) and current inventory levels (from a Google Sheet). Dry-runs first, writes to the sheet only after approval.

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

   > Read the README and set this agent up with me. Ask me for each value in the Customising table, one at a time, then replace the placeholders in `.claude/agents/fb-shopping-list.md`, `.claude/skills/fb-shopping-list/SKILL.md` and `.env`. Do not guess a value. When you are done, list any `{{...}}` that is still in the repo.

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

---

## File structure

```
fb-shopping-list-agent/
├── README.md
├── .env.example
├── .gitignore
├── LICENSE
└── .claude/
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
| `{{INVENTORY_TOOL}}` | agent file, skill | Command that runs your shopping-list script | `python3 tools/fb_shopping_list.py` |
| `{{PMS_LOOKUP_TOOL}}` | skill | Command that returns upcoming reservations with guest counts (used to cross-check a guest total) | `python3 tools/pms_lookup.py` |
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
| (no flag) | Same computation, then write the list to the shopping-list sheet. |
| `--days N` | Use an N-day coverage window instead of the default. Works with and without `--dry-run`. |
| `--log "Item" "ran-out\|over-stocked" "Notes"` | Append one row to the `Calibration` tab. Change nothing else. |

The output must show the window dates, the total guest-nights, the date of the latest stock count, and per item: category, on hand, to buy, unit. The tool must exit with an error when the PMS call fails. A silent fallback to 0 guests produces a list that looks valid and is wrong.

The two consumption models (per-guest and par-level) are defined in [`SKILL.md`](.claude/skills/fb-shopping-list/SKILL.md#consumption-models).

---

## How memory works

The agent has `memory: project` in its front matter, so Claude Code gives it a memory directory at `.claude/agent-memory/fb-shopping-list/` and loads the start of `MEMORY.md` from there at every run. The agent reads and writes files in that directory itself. Notes worth keeping:

- **Feedback** — patterns that improve consumption modelling (e.g. "guests average 1.2 eggs per breakfast, not 2 — adjust guests-per-unit on Eggs")
- **Project notes** — context that affects shopping (e.g. "August public holiday closes the supplier — buy a double load on the previous shop day")
- **References** — pointers to other systems (e.g. "the bakery order is not in this list; handled by a separate workflow")

[`example-feedback-pattern.md`](.claude/agent-memory/fb-shopping-list/example-feedback-pattern.md) shows the recommended format and [`MEMORY.md`](.claude/agent-memory/fb-shopping-list/MEMORY.md) indexes it. Delete the example and its index line once you have your own notes. The directory is committed to git, so do not let guest names or other personal data into it.

---

## Related agents

Part of [21 AI Agents That Run a Real Hotel](https://th1.ai/agent-stack). This agent sits well next to:

- [`cleaning-schedule-agent`](https://github.com/th1-ai/cleaning-schedule-agent) — plans changeovers from the same upcoming-reservation data; useful together when you plan a busy week
- [`morning-routine-agent`](https://github.com/th1-ai/morning-routine-agent) — the daily briefing; a natural place to ask for the shopping list on shop days
- [`villa-analytics-agent`](https://github.com/th1-ai/villa-analytics-agent) — property analytics; useful when you review whether the consumption values still fit

---

## License

MIT — see [LICENSE](LICENSE).
