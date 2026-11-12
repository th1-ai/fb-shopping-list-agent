# runs/

The agent's own record of what it did. Everything in this folder except this file and `.gitkeep` is ignored by git.

| File | Written by | What it is |
|---|---|---|
| `LOG.md` | the agent, one entry appended per run | The run log. The last entry is the latest run summary. The agent reads the last entries at the start of a run so it does not repeat work |
| `handoff/fb-shopping-list-agent.md` | the agent, overwritten every run | The latest result with the full list, for [`morning-routine-agent`](https://github.com/th1-ai/morning-routine-agent) and for you |
| `cron.log` | your scheduler, if you use the example command | Raw output of scheduled runs |

## `LOG.md` entry format

Newest entry last. No guest names, only counts and dates.

```
## 2026-01-15T06:30:12+01:00 | Level 1 | scheduled
- Checked: AUTONOMY.md, last 10 log entries, setup, dry run (window 2026-01-16 to 2026-01-19, 4 days, 38 guest-nights, stock counted 2026-01-14)
- Actions taken: none
- Actions proposed: list of 17 lines, window 2026-01-16 to 2026-01-19
- Errors: none
- Needs you: nothing
```

A write is logged under "Actions taken" as `wrote list | window <start> to <end> | tab <tab> | <N> rows | verified`. That line is the id the agent looks for before it writes: one window is written once. A shadow run logs `would have written | window ... | shadow <n> of 3`. A run stopped by the kill switch logs `skipped: PAUSED`, `skipped: Level 0` or `skipped: PAUSED (no readable Level line)`.

## `handoff/fb-shopping-list-agent.md` format

```
# F&B shopping list handoff
- Generated: 2026-01-15T06:30:12+01:00
- Level: 1
- Status: proposed | ready to approve | written | blocked | skipped
- Window: 2026-01-16 to 2026-01-19 (4 days)
- Guest-nights: 38
- Stock counted: 2026-01-14
- Needs you: nothing

(the list, grouped by category, when there is one)
```

The dates and numbers above are invented examples.
