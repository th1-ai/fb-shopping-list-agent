---
name: Per-guest model needs calibration once per season
description: The guests-per-unit values in the Inventory tab drift as menus, guest mix, and portion sizes change. Calibrate once at the start of each high season using the previous season's calibration events.
type: feedback
---

> **Example pattern.** This file shows the *shape* of a useful agent-memory note. Replace it with your own learnings as the agent runs.

The per-guest consumption model multiplies projected guest-nights by a `guests-per-unit` constant for each item. That constant is correct on day one and slowly drifts because:

- Breakfast portions creep up or down depending on what's offered
- Long-stay guests use less of "welcome" items than short-stay guests, but staff still buy the same amount per guest-night
- Seasonal items appear and disappear (cold-pressed juice, soup, etc.)

**How to calibrate:**

1. Every time something runs out before the next shop, log it with `--log "<Item>" "ran-out" "Notes"`. Note: which day it ran out, and what the actual guest-night count was for the window.
2. Every time something is overstocked at the end of a window, log it with `--log "<Item>" "over-stocked" "Notes"`.
3. At the start of each high season (or once a quarter, whichever is sooner), open the Calibration tab and:
   - For items with multiple "ran-out" events: reduce `Guests/Unit` (i.e. buy more per guest)
   - For items with multiple "over-stocked" events: increase `Guests/Unit` (i.e. buy less per guest)
   - Don't tune anything with fewer than 2 events in the period — single events are noise.

**Anti-pattern:**

Tuning `Guests/Unit` mid-season based on one shop day's surprise. Always wait for a second event in the same direction before adjusting.
