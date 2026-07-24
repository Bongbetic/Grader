# PROTOTYPE — throwaway

**Question:** Which fixed layout for a per-prompt grade report makes Craft / Efficacy / Planning / Security / coaching slots scannable without inviting freestyle narration?

**Plan:** Three structurally different variants on one page, switchable via `?variant=A|B|C`.

## Run

```bash
python skills/grader/prototype/grade_report/serve.py
```

Open http://127.0.0.1:8765/?variant=A

Arrow keys or bottom bar cycle variants. Not production. Delete or park on a throwaway branch after verdict.
