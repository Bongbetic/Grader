# Trends flow

Use this flow when the user asks for trends, progress, history, charts, or a multi-week view.

## 1. Build the trends payload

From this skill directory, run:

```bash
python3 scripts/trends_report.py --json
```

Use `--root ...` only when the grader home is not the default `~/.grader`.

The report reads `~/.grader/grades.jsonl` and `~/.grader/metrics.jsonl` and returns:

- `available`: boolean — `true` once there are at least two grade records or metrics cover at least two distinct periods.
- `dimension_levels`: per-dimension level history.
- `bands_over_time`: band history over time.
- `most_frequent_failing`: the dimension most often below level 3.
- `streaks`: consecutive A/B band grades and consecutive practice days.

## 2. Availability

Trends are available as soon as either:

- there are at least two grade records, or
- metrics cover at least two distinct periods.

There is no v2 unlock gate and no dependency on coach history.

## 3. If not available

Tell the user how much data is needed and encourage them to run a couple of Grade or Practice sessions. Do not block the user from viewing other parts of the skill.

## 4. If available

Summarize the JSON in plain language:

- Most frequent failing dimension and count.
- Recent band trajectory.
- Current streaks.

Do not invent trend claims that are not present in the data. If history is sparse, explain what is included and what is not.
