# Gold set

Human-labeled prompts for calibrating the Grader judge. One JSON object per line.

Fields:
- id: stable string id
- prompt: redacted prompt text
- task_type: e.g. code_generation, marketing_copy, data_extraction
- model_class: standard | reasoning | unknown
- language: ISO-ish tag (en, en-nonnative, es, ...)
- human_levels: {D1..D11: 0-3 or "N/A"} — expert-rater consensus
- human_band: A|B|C|D — expert-rater consensus
- tags: list of markers (adversarial, fairness, terse_valid_continuation, ...)

Expand this set with expert raters before enabling the Phase 6 band modifier.
