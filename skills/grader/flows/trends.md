# Trends flow

Use this flow when the user asks for trends, progress, history, charts, a multi-week view, or whether trends are unlocked.

## 1. Render the trends artifact

From this skill directory, run:

```bash
python3 scripts/render_trends.py --root ... --out trends.html
```

Use the actual Claude root for `--root` when known. If omitted, `render_trends.py` resolves the Claude root using `CLAUDE_CONFIG_DIR` or `~/.claude`.

The history file read by trends is:

```text
{claude_root}/skills/grader/history/coach_sessions.jsonl
```

## 2. Check lock status

Trends unlock after 5 completed Coach sessions. Completion is defined by `scripts/history_lib.py`:

1. `completed` is true.
2. `live_assessment_finished` is true.
3. `coaching_drill_rounds` is at least 1.

To inspect status directly:

```bash
python3 - <<'PY'
import sys

sys.path.insert(0, "scripts")
from history_lib import trends_unlock_status

status = trends_unlock_status()
print(f'{status["completed"]}/{status["required"]}')
print(status)
PY
```

## 3. If locked

Tell the user:

- `completed/required` progress, usually `N/5`.
- How many more completed Coach sessions are needed.
- The completion definition above.
- That Practice and Grade flows do not count toward trends.

Still provide the generated `trends.html` path if rendering succeeded; it will contain the locked-state explanation.

## 4. If unlocked

Show the HTML path and summarize what the report contains:

- DNA clarity trend.
- Efficiency grade trend.
- Habit focus frequency.

Do not invent trend claims that are not present in history. If history is sparse or malformed, explain what could be rendered and what was skipped.
