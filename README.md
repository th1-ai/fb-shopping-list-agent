# F&B Shopping List Agent

A Claude Code sub-agent + skill for hotel operators. It generates a grocery shopping list for the next few days based on projected guest counts (from your PMS) and current inventory levels (from a Google Sheet). Dry-runs first, writes to the sheet only after approval.

Built on the **WAT framework** (Workflows, Agents, Tools): probabilistic AI handles reasoning, deterministic scripts handle execution.

---

## What it does

- **Projects guest-nights** for the upcoming shopping window from your PMS
- **Reads master inventory + latest stock counts** from a Google Sheet
- **Computes per-item buy quantities** using two consumption models:
  - **Per-guest** — scales with projected guest-nights (e.g. eggs, butter, fruit)
  - **Par-level** — fixed minimum stock (e.g. cleaning supplies, condiments)
- **Auto-adds room-specific items** for special check-ins (e.g. flowers when a premium suite is arriving in the window)
- **Dry-runs first**, presents the list grouped by category, asks for approval, then writes
- **Tracks calibration events** so the consumption model improves over time ("we ran out of X early last shop", "Y was over-stocked")

---

## What you need

- [Claude Code](https://claude.ai/code) installed
- A PMS that returns upcoming reservations with guest counts (the reference setup is Cloudbeds, but any PMS with that data works)
- A Google Sheet (or equivalent) with two tabs:
  - `Inventory` — master list of items, category, unit, consumption model, guests-per-unit / par values
  - `Stock` — most recent counts entered by staff

---

## Quick start

1. **Clone the repo** into a Claude Code project:

   ```bash
   git clone https://github.com/th1-ai/fb-shopping-list-agent.git
   cd fb-shopping-list-agent
   ```

2. **Copy the env template** and fill it in:

   ```bash
   cp .env.example .env
   ```

3. **Set up the inventory sheet** — either build the two tabs manually or run a one-off setup script (`tools/fb_setup_sheet.py` in the reference setup) to create them.

4. **Edit [`.claude/agents/fb-shopping-list.md`](.claude/agents/fb-shopping-list.md)** and [`.claude/skills/fb-shopping-list/SKILL.md`](.claude/skills/fb-shopping-list/SKILL.md) — replace the placeholders described in [Customising](#customising).

5. **Open in Claude Code** from the project root:

   ```bash
   claude
   ```

6. **Invoke the agent**:

   > "Generate the F&B shopping list for the next 4 days."

   Claude Code will pick up the `fb-shopping-list` sub-agent automatically because of the front-matter `description` line.

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
            └── example-feedback-pattern.md         # Example "memory note"
```

---

## Customising

The agent and skill files use placeholders so they can be adapted to any PMS + sheet stack. Replace the following before first run:

| Placeholder | What to put | Example |
|---|---|---|
| `{{HOTEL_NAME}}` | Hotel display name | `The Garden Inn` |
| `{{PMS_PROPERTY_ID}}` | PMS property ID | `123456789` |
| `{{PMS_LOOKUP_TOOL}}` | Script that returns upcoming reservations + guest counts | `tools/pms_lookup.py` |
| `{{INVENTORY_TOOL}}` | Script that runs the dry-run / write logic against the sheet | `tools/fb_shopping_list.py` |
| `{{SHEET_ID_INVENTORY}}` | Google Sheet ID for the master inventory + stock tabs | `1AbC...` |
| `{{SHEET_ID_SHOPPING_LIST}}` | Google Sheet ID where the proposed list is written | `1AbC...` (often same sheet, different tab) |

The reference setup uses a single tool, `tools/fb_shopping_list.py`, with sub-commands `--dry-run`, `--days N`, and `--log "Item" "ran-out|over-stocked" "Notes"`.

---

## How memory works

The agent uses Claude Code's per-agent memory at `.claude/agent-memory/fb-shopping-list/`. After each run, it can save:

- **Feedback** — patterns that improve consumption modelling (e.g. "guests average 1.2 eggs per breakfast, not 2 — adjust guests-per-unit on Eggs")
- **Project notes** — context that affects shopping (e.g. "August public holiday closes the supplier — buy a double load on the previous shop day")
- **References** — pointers to other systems (e.g. "the bakery order is not in this list; handled by a separate workflow")

[`example-feedback-pattern.md`](.claude/agent-memory/fb-shopping-list/example-feedback-pattern.md) shows the recommended format. Delete it once you have your own.

---

## Related agents

This agent works well alongside:

- [`cleaning-schedule-agent`](https://github.com/th1-ai/cleaning-schedule-agent) — uses the same upcoming-reservation feed to plan changeovers; it pairs with the shopping list when you're planning a busy week
- [`morning-routine-agent`](https://github.com/th1-ai/morning-routine-agent) — calls this agent on shop days as part of the daily briefing
- [`villa-analytics-agent`](https://github.com/th1-ai/villa-analytics-agent) — useful for sanity-checking the consumption model against actual food cost over a month

---

## License

MIT — see [LICENSE](LICENSE).
