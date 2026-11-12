---
name: fb-shopping-list
description: Generate the hotel's F&B grocery shopping list from projected PMS guest-nights and the inventory sheet, dry run first and written to the sheet only after approval. Also logs "ran out" and "over-stocked" calibration events.
when_to_use: Use when the operator says "shopping list", "grocery list", "what do we need to buy", "F&B list" or "stock check", asks about groceries on a shop day, or reports that an item ran out or was over-stocked.
---

# Skill: F&B Shopping List

Generate a grocery shopping list from projected guest-nights (PMS) and current stock levels (F&B inventory sheet).

> **Template note:** Replace `{{INVENTORY_TOOL}}` and `{{PMS_LOOKUP_TOOL}}` with the scripts your setup uses. This repo does not ship them. See [README.md](../../../README.md#customising) for the placeholders and [the tool contract](../../../README.md#the-tool-you-supply).

## Config

- **Inventory sheet:** ID in `.env` as `SHEET_ID_INVENTORY` (tabs: `Inventory`, `Stock`, `Calibration`)
- **Shopping-list sheet:** ID in `.env` as `SHEET_ID_SHOPPING_LIST` (often the same sheet, different tab)
- **PMS property:** `PMS_PROPERTY_ID` in `.env`
- **Shopping-list tool:** `{{INVENTORY_TOOL}}`
- **PMS lookup tool:** `{{PMS_LOOKUP_TOOL}}` (used by the shopping-list tool; run it directly only to cross-check a guest count)

## Prerequisites

- `SHEET_ID_INVENTORY` has a real value in `.env`.
- The `Inventory` tab lists the items and their consumption model.
- Staff entered current counts in the `Stock` tab. A list built on an old count is wrong in a way nobody sees until something runs out.

## Process

### 1. Check setup

```bash
grep '^SHEET_ID_INVENTORY=' .env
```

If the value is empty, missing or still a `{{...}}` placeholder, stop. Tell the operator the sheet needs to be set up first (README, Quick start).

### 2. Dry run first

```bash
{{INVENTORY_TOOL}} --dry-run
```

The tool reads:
- Items and consumption models from the `Inventory` tab
- Latest stock levels from the `Stock` tab
- Guest counts from the PMS for the shopping window

For a different coverage window, add `--days N`:

```bash
{{INVENTORY_TOOL}} --dry-run --days 5
```

### 3. Check the result before you show it

- **Guest-nights = 0, or the PMS call failed:** treat it as an error, not as an empty hotel. Do not present a zero-guest list. Ask the operator whether the property is really empty. To cross-check, run `{{PMS_LOOKUP_TOOL}}` for the same dates.
- **Stock is stale** (latest entries older than the last shop day): keep the list, put a warning at the top.
- **An item has no stock count:** list it separately. Do not assume zero.

### 4. Present the list

Show the list grouped by category. Include:
- Shopping window (dates covered) and total guest-nights
- Date of the latest stock count
- Items to buy by category (DAIRY, PRODUCE, DRY GOODS, BEVERAGES, CLEANING, and so on, as named in the sheet)
- On-hand and to-buy quantities, with units

Then ask for approval. The operator can ask for changes (another window, drop an item) and you run the dry run again.

### 5. Write after approval

Only after the operator approves the list you showed:

```bash
{{INVENTORY_TOOL}}
```

Use the same `--days` value as the approved dry run, so the written list is the approved list.

### 6. Log calibration events

When the operator says something ran out early or was left over:

```bash
{{INVENTORY_TOOL}} --log "<Item>" "ran-out" "When it ran out, guest-nights in the window"
{{INVENTORY_TOOL}} --log "<Item>" "over-stocked" "How much was left"
```

Events go to the `Calibration` tab. They are the evidence for tuning the consumption model later. Logging an event does not change any consumption value.

## Shopping schedule (example, adapt to your supplier days)

| Shop day | Covers |
|----------|--------|
| Day 1 | Day 2 to Day 5 (4 days) |
| Day 4 | Day 5 to Day 1 (4 days) |
| Day 5 | Day 6 to Day 2 (4 days) |
| Any other day | 4 days from tomorrow |

The shop days and the default window live in your tool. Four days of coverage per shop is a starting point; adjust it to your supplier delivery schedule.

## Consumption models

- **Per-guest:** scales with the PMS guest count.
  `to_buy = max(0, ceil(guest_nights / guests_per_unit * 1.10) - on_hand)`
  `1.10` is a 10 % safety buffer. `guests_per_unit` is how many guest-nights one unit covers, so a lower value means buying more.
- **Par-level:** fixed minimum stock. If `on_hand < par_min`, buy up to `par_target`. Otherwise buy nothing.

The `Inventory` tab is the source of truth. Staff change `Guests/Unit`, `Par Min`, `Par Target` and `Model` there, and add new items in the same column structure.

## Special-room auto-add (optional)

If `PREMIUM_ROOM_TYPE_ID` is set in `.env`, the tool checks for check-ins of that room type inside the shopping window and adds one associated item per check-in, with the check-in date in the notes. Example: a premium suite arrival adds one bouquet under FLOWERS.

If the variable is empty, skip this. Do not add such items by hand from your own reading of the reservations.

## Guardrails

- Always dry run first and show the list before any write.
- Write to the shopping-list sheet only after explicit approval.
- Do not edit the `Inventory` or `Stock` tabs. Suggest the change and let staff make it.
- Do not send the list to a supplier or delivery service. The operator places the order.
- Use only quantities the tool returned. Do not invent items, prices, pack sizes or guest counts, and do not compute the list by hand if the tool fails.
- Specialty or fresh items ordered through a separate channel (for example a daily bakery order) are not part of this list.
