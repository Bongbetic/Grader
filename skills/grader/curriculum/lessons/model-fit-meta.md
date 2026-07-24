# Model-Fit Meta: Standard vs Reasoning

Prompt design diverges sharply between standard models and reasoning models. Ignoring that split is the most common way to turn a good prompt into a bad one.

For standard models (GPT-4o-class, Claude, Gemini Flash/Pro), explicit structure usually helps. On hard tasks, add step-by-step reasoning, few examples, and clear delimiters. For reasoning models (o-series, extended thinking, Gemini thinking), keep prompts lean, avoid forced chain-of-thought, try zero-shot first, and use native reasoning-effort controls when available. A forced "think step by step" on a reasoning model can degrade the answer.

- Try this: State the model class at the top of your prompt. If the model is reasoning, remove every "think step by step" and every example; if it is standard, add one skeleton or example.
