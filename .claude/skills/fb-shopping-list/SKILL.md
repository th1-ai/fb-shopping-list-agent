---
name: fb-shopping-list
---

# Skill: F&B Shopping List

Generate a grocery shopping list based on projected guest counts from the PMS and current stock levels from the F&B Inventory sheet.

## Trigger

User says "shopping list", "grocery list", "what do we need to buy", "F&B list", "stock check", "generate shopping list", or it's a configured shop day and the operator asks about groceries.

> **Template note:** Replace `{{HOTEL_NAME}}`, `{{PMS_*}}`, `{{INVENTORY_TOOL}}`, `{{SHEET_ID_INVENTORY}}` and `{{SHEET_ID_SHOPPING_LIST}}` with the wrappers your setup uses. See [README.md](../../../README.md#customising) for guidance.

## Config

- **Inventory sheet:** ID in `.env` as `SHEET_ID_INVENTORY`
- **Shopping-list sheet:** ID in `.env` as `SHEET_ID_SHOPPING_LIST` (often the same sheet, different tab)
- **Tool:** `{{INVENTORY_TOOL}}`
- **Setup tool:** a one-off script to create the inventory tabs if they don't exist (the reference setup uses `tools/fb_setup_sheet.py`)

## Prerequisites

- `SHEET_ID_INVENTORY` must be set in `.env`. If not, run the setup script first.
- Staff should have entered current stock counts in the Stock tab before generating a list.

## Process

### 1. Check setup

Verify `SHEET_ID_INVENTORY` is set:

```bash
grep SHEET_ID_INVENTORY .env
```

If empty or missing, tell the operator the sheet needs to be set up first and offer to run the setup script.

### 2. Dry-run first

Always start with a dry run to preview what the tool calculates:

```bash
{{INVENTORY_TOOL}} --dry-run
```

This pulls:
- Inventory items and consumption models from the Inventory tab
- Latest stock levels from the Stock tab
- Guest counts from the PMS for the shopping window

### 3. Present the list

Show the operator the shopping list grouped by category. Include:
- Shopping window (dates covered)
- Total guest-nights
- Items to buy, grouped by category (DAIRY, PRODUCE, DRY GOODS, BEVERAGES, CLEANING, etc.)
- On-hand quantities vs. to-buy quantities

### 4. Confirm and write

After approval, write to the sheet:

```bash
{{INVENTORY_TOOL}}
```

### 5. Override days (optional)

If the operator wants a different coverage window:

```bash
{{INVENTORY_TOOL}} --days 5
```

### 6. Log calibration events

If something ran out early or was overstocked:

```bash
{{INVENTORY_TOOL}} --log "<Item>" "ran-out" "Details about when it ran out"
{{INVENTORY_TOOL}} --log "<Item>" "over-stocked" "Details about surplus"
```

These events are appended to a Calibration tab in the inventory sheet — over time, you (or the next maintainer of the tool) can adjust the consumption model to reflect actual usage.

## Shopping schedule (example — adapt to your supplier days)

| Shop day | Covers | Auto-detected |
|----------|--------|---------------|
| Day 1 | Day 2–Day 5 (4 days) | Yes |
| Day 4 | Day 5–Day 1 (4 days) | Yes |
| Day 5 | Day 6–Day 2 (4 days) | Yes |
| Other | 4 days default | Yes |

Configure your own shop days in the tool. The default "4 days of coverage per shop" is a sensible starting point — adjust per supplier delivery schedule.

## Consumption models

- **Per-guest:** Scales with PMS guest count.
  `to_buy = ceil(guest_days / guests_per_unit * 1.10) - on_hand`
  The `1.10` is a safety buffer; tune up or down based on calibration events.
- **Par-level:** Fixed minimum stock. If `on_hand < par_min`, buy up to `par_target`.

The Inventory tab is the source of truth — change `Guests/Unit`, `Par Min`, `Par Target` directly there.

## Special-room → auto-add (optional)

The tool can automatically check for check-ins of a specific room type within the shopping window. If any are found, it adds an associated item per check-in to the shopping list under the matching category, with the guest name and check-in date in the notes.

Example: a premium suite check-in adds one bouquet to the FLOWERS category. Driven by `PREMIUM_ROOM_TYPE_ID` in `.env`. No staff action needed — the item appears in the list whenever a matching arrival falls in the window.

## Adjusting items

The Inventory tab is the source of truth. Edit directly:
- Change `Guests/Unit` to tune consumption rates
- Add new items (follow the same column structure)
- Change `Model` between `per-guest` and `par-level`

## Guardrails

- Always `--dry-run` first, show the list before writing to the sheet
- Don't modify the Inventory tab programmatically without asking
- Excludes specialty/fresh items that are ordered separately (e.g. daily bakery deliveries handled via WhatsApp / a separate workflow)
- If guest count from the PMS comes back as 0, treat it as an error signal — do not buy a "zero guests" list silently
