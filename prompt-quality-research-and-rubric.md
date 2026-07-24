# Prompting Best Practices Across the Major AI Labs — Research Synthesis & Prompt-Quality Rubric

*A grounded review of how Google, OpenAI, Anthropic, and the academic literature define effective prompting — distilled into an operational rubric for scoring prompts and teaching people to write better ones.*

---

## How to use this document

It has two parts:

- **Part I — Research synthesis.** What each lab actually recommends, what the peer-reviewed and preprint literature has established, where they converge, and where they genuinely disagree. This is the evidence base.
- **Part II — The rubric.** A weighted, level-based scoring instrument distilled from Part I, plus a teaching layer that turns each low score into a concrete fix. This is the deliverable you assess prompts with.

A guiding caveat runs through everything below: **prompting is empirical, not doctrinal.** The research shows model outputs can swing wildly on changes that preserve meaning, so no rubric replaces testing. The rubric scores whether a prompt is *well-constructed and likely to succeed*; it does not certify an output.

---

# PART I — Research Synthesis

## 1. Google

Google publishes two distinct frameworks aimed at two audiences, and they are frequently conflated.

**PTCF — Persona, Task, Context, Format.** This is the Workspace / consumer framing. The four parts each remove a class of ambiguity the model would otherwise fill on its own: *Persona* (who the model is being), *Task* (what to produce), *Context* (what it needs to know — audience, goal, constraints, reference material), *Format* (what the finished output looks like). Google's own Workspace guidance notes that effective prompts average roughly 21 words, which signals that the goal is precision, not length. You are not required to label the four parts inside the prompt; the discipline is in deciding all four before you write.

**TCREI — Task, Context, References, Evaluate, Iterate.** This is the framing from *Google Prompting Essentials* (their training course), with the mnemonic "Thoughtfully Create Really Excellent Inputs." It folds Persona and Format *inside* Task, then adds two steps most frameworks omit: *Evaluate* (inspect the output for hallucinations and bias) and *Iterate* (re-run through the steps, adding detail). The framework you attached — persona / task / context / reference / format — is essentially PTCF with References added, i.e. a blend of the two.

The important move in TCREI is that **evaluation and iteration are treated as part of prompting itself**, not as an afterthought. That is a defensible position given the empirical brittleness findings in §6.

Google's developer-facing guidance (Gemini API / Vertex) goes further into technique: role prompting, contextual prompting, step-back prompting (ask a broad question first to surface relevant background, then feed that into the main task), chain-of-thought, and self-consistency (sample multiple reasoning paths, take the majority answer). It also documents parameter control (temperature, top-p, top-k) — and, notably, current Gemini guidance recommends leaving those at defaults for the newest models, warning that lowering temperature can cause looping or degraded reasoning.

## 2. OpenAI

**The six strategies** (from OpenAI's prompt-engineering guide) are the durable backbone:

1. **Write clear instructions** — add detail, ask the model to adopt a persona, specify the steps, use delimiters (`###`, `"""`, XML) to separate instruction from data, state the desired length/format.
2. **Provide reference text** — ground answers in supplied material to cut fabrication ("a sheet of notes helps a student on a test").
3. **Split complex tasks into simpler subtasks** — intent classification, recursive summarization of long documents, etc.
4. **Give the model time to "think"** — instruct it to reason before concluding; use an inner monologue or a self-worked solution before it judges an answer.
5. **Use external tools** — retrieval/RAG, code execution, function calling.
6. **Test changes systematically** — evaluate against gold-standard answers.

**The reasoning-model addendum is the critical update.** OpenAI's *reasoning best practices* (for o-series and successors) explicitly invert several of the six-strategy tactics:

- **Keep prompts simple and direct**; these models excel at brief, clear instructions.
- **Avoid explicit chain-of-thought** ("think step by step") — reasoning is internal, and forcing it is redundant or harmful.
- **Use delimiters** for clarity.
- **Limit extra context in RAG** — include only the most relevant material; too much makes the model overcomplicate.
- **Try zero-shot first**, add one or two examples only if needed — few-shot can *degrade* reasoning-model performance.
- **Developer messages** replaced system messages starting with the December-2024 o1 release.
- Newer reasoning models expose a **reasoning-effort** control (low / medium / high, and in the latest generation up through `max`), which is itself a prompt-design lever.

OpenAI's most recent model guidance (GPT-5.x family) adds a further theme: **favor leaner prompts.** Their internal coding-agent evals found that removing repeated instructions and simplifying tool descriptions improved scores by ~10–15% while cutting tokens 40–66%. It also stresses defining autonomy/approval boundaries explicitly and setting response length/tone through describable writing choices rather than vague labels like "be concise" or "friendly."

## 3. Anthropic (Claude)

Anthropic's current (2026) framing splits into **core** and **advanced**, with a distinctive "brilliant new employee with amnesia" mental model and a "golden rule": *show your prompt to a colleague with minimal context; if they're confused, Claude will be too.*

**Core techniques**

- **Be explicit and clear** — state exactly what you want; lead with action verbs; don't rely on inference.
- **Provide context and motivation** — explaining *why* a constraint exists outperforms stating the constraint alone (their example: explaining why you dislike bullet points beats "NEVER use bullet points").
- **Be specific** — constraints, audience, output structure, restrictions.
- **Use examples (one-shot → few-shot)** — but modern Claude attends *very* closely to example details, so examples must model the behavior you want and avoid patterns you don't. Start with one; add more only if needed.
- **Give permission to express uncertainty** — "say so rather than speculating" measurably reduces hallucination.

**Advanced techniques**

- **Prefill the response** (API) — begin the assistant turn to enforce JSON/format or skip preamble.
- **Chain of thought** in three grades — basic ("think step-by-step"), guided (named reasoning stages), structured (`<thinking>` / `<answer>` tags) — but **extended thinking**, when available, is generally preferable to manual CoT.
- **Control output format positively** — say what *to* do ("flowing prose paragraphs") not what *not* to do; match your prompt's style to the desired output style.
- **Prompt chaining** — sequential prompts, each doing one thing well; trades latency for accuracy.

**Notably deprecated:** Anthropic now says **XML tags and heavy role prompting are less necessary** with modern models — useful in specific situations (complex mixed content, strict content boundaries, older models) but no longer default. Over-constrained personas ("world-renowned expert who never makes mistakes") can *reduce* helpfulness; being explicit about the perspective you want usually beats assigning a role.

Their closing principle mirrors OpenAI's lean-prompt turn: **the best prompt is not the longest — it's the one that reliably achieves the goal with the minimum necessary structure.** They also situate prompt engineering inside the larger discipline of *context engineering*.

## 4. CO-STAR and other named frameworks

**CO-STAR** — *Context, Objective, Style, Tone, Audience, Response* — was created by Sheila Teo (GovTech Singapore's Data Science & AI team) and won Singapore's first GPT-4 Prompt Engineering competition. Its distinctive contribution is **separating Style from Tone** and making **Audience** a first-class field — the elements most other frameworks collapse. It is strongest for communication and marketing tasks, where *how* something is said matters as much as *what*. A COSTAR-A variant in the literature adds an "Answer/Assessment" step for smaller/local models.

Other structures in common professional use (lower evidentiary weight; mostly practitioner conventions rather than researched):

- **RTF** — Role, Task, Format (minimalist).
- **TAG** — Task, Action, Goal.
- **RISEN / RODES / TIDD-EC** — expanded business-writing scaffolds.
- **APE / RaR / Rephrase-and-Respond** — self-refinement patterns that have some empirical backing.

These are best understood as **checklists that operationalize the same underlying variables** (role, task, context, constraints, format, audience, tone) rather than competing theories.

## 5. The academic backbone

**The Prompt Report (Schulhoff et al., 2024)** is the anchor: a PRISMA-guided systematic review of 1,565+ papers producing a taxonomy of **58 text-only prompting techniques** (plus 40 multimodal and 33 vocabulary terms), grouped into six categories. Its central motivation is that the field suffers from *conflicting terminology and a fragmented understanding of what makes a prompt effective* — which is precisely the gap a rubric addresses.

The load-bearing individual techniques, with their sources:

- **Few-shot / in-context learning** (Brown et al., 2020) — models learn a task from a few in-prompt examples with no weight updates.
- **Chain-of-thought** (Wei et al., 2022) — few-shot exemplars with explicit intermediate reasoning; produces striking gains on arithmetic, commonsense, and symbolic tasks. Crucially, CoT is an **emergent ability of scale** — it does not help (and can hurt) below ~100B-parameter-class models, and its benefit *grows* with model size.
- **Zero-shot CoT** (Kojima et al., 2022) — simply appending "Let's think step by step" elicits reasoning without exemplars.
- **Self-consistency** (Wang et al., 2022) — sample multiple reasoning paths, take the majority answer; improves reliability over greedy CoT.
- **Least-to-most** (Zhou et al., 2022) — decompose into progressively harder subproblems.
- **Tree-of-Thoughts** (Yao et al., 2023) and **Graph-of-Thoughts** (Besta et al., 2024) — structure reasoning as search / arbitrary topologies.
- **ReAct** (Yao et al., 2022) — interleave reasoning traces with tool actions.

## 6. The empirical finding that most shapes a rubric: prompt brittleness

This is the single most important body of evidence for anyone *scoring* prompts, because it bounds how much any structural rule can promise.

- **Format sensitivity.** Sclar et al. (2024) found meaning-preserving formatting changes (spacing, delimiters, casing) produced accuracy swings **up to 76 points** on some tasks for LLaMA-2-13B, with GPT-3.5 showing spreads up to 56 points across 320 formats. Sensitivity **persists** despite larger models, more few-shot examples, or instruction tuning.
- **Example-order sensitivity.** Lu et al. (2022, "Fantastically Ordered Prompts") showed that permuting the *same* few-shot examples causes large accuracy swings; good orderings **do not transfer across models**; and adding more examples does not reliably reduce the variance.
- **Calibration.** Zhao et al. (2021) documented shifts up to ~30% from format/label choices, partly fixable with calibration.
- **What examples actually teach.** Min et al. (2022) found models benefit from demonstrations *even when the labels are random* — suggesting format and distribution cues can matter more than exemplar correctness.
- **A mitigating factor.** Bertsch et al. (2024): long-context models given *many* demonstrations become substantially *less* order-sensitive — context scale partly absorbs the brittleness.

**Implication for the rubric:** structural quality raises the *expected* value and *lowers the variance* of outcomes, but a high rubric score is a necessary-not-sufficient condition. The rubric must therefore reward testability and iteration-readiness, not just static structure.

## 7. Cross-lab convergence — what everyone agrees on

Stripping away vocabulary, the labs and the literature agree on a small, robust core:

1. **Explicit beats implicit.** State the task, the audience, the constraints, and the output shape; don't make the model guess.
2. **Ground factual work in supplied reference material** to cut hallucination.
3. **Give permission to say "I don't know."**
4. **Match structure to the output** — show the format, or prefill it, when format matters.
5. **Decompose complex tasks** (chaining / subtasks) rather than overloading one prompt.
6. **Reasoning is worth eliciting on hard multi-step tasks** — via CoT on standard models, or via native/extended thinking on reasoning models.
7. **Iterate and evaluate.** First drafts rarely land; test against criteria.
8. **Don't over-engineer.** Minimum necessary structure; lean prompts often score higher and cost less.

## 8. The central modern divergence — standard vs reasoning models

The one place where following "best practice" for the wrong model class actively *hurts*:

| Lever | Standard model (GPT-4o-class, Claude non-thinking, Gemini Flash/Pro) | Reasoning model (o-series, Claude extended thinking, Gemini "thinking", DeepSeek-R1) |
|---|---|---|
| Explicit "think step by step" | Helps on multi-step tasks | Redundant; can **degrade** — reasoning is internal |
| Few-shot examples | Often help; watch order/format | Try **zero-shot first**; 0–2 examples max; can hurt |
| Prompt length / context | More detail usually helps | Keep lean; too much context causes overthinking |
| Reasoning control | Prompt-level only | Native **effort/verbosity** parameters are the lever |
| Best-fit tasks | Breadth, formatting, tool orchestration | Deep multi-step reasoning, math, hard code |
| Overthinking risk | Low | **Real** on trivial tasks — may underperform a fast model |

Any rubric that ignores model class will systematically mis-score prompts. This is why the rubric below includes **Model & Parameter Fit** as a core dimension and adapts several other dimensions to the target model.

---

# PART II — The Prompt-Quality Rubric

## Design principles

- **Weighted, not flat.** Objective clarity and model fit matter more than tone; the weights reflect that.
- **Conditional dimensions.** Some dimensions only apply to certain task types (you don't score "tone" on a code-generation prompt). These are marked *Conditional* and are dropped from the denominator when not applicable, so a lean technical prompt is never penalized for lacking marketing scaffolding.
- **Level-based, 0–3.** Each dimension is scored 0 (absent/counterproductive), 1 (weak), 2 (adequate), 3 (strong). This maps cleanly onto teaching: the gap between the given level and 3 *is* the lesson.
- **Disqualifiers cap the grade.** Certain defects (e.g. instructing a reasoning model to "think step by step," internal contradictions, no success criteria on a complex task) cap the maximum grade regardless of other strengths — because the brittleness research says these dominate outcomes.
- **Grades map to a confidence band** you can act on (A/B/C/D), consistent with a "≥95% pass" style gate.

## The ten dimensions

### Core dimensions (always scored)

**D1. Objective & Success Criteria — weight ×3**
Is the exact action explicit (lead verb: *write / analyze / extract / build*), and is "done well" defined (acceptance criteria, measurable outcome)?
- 0: Vague ("help with marketing"). 1: Action stated, no success bar. 2: Clear action + rough scope. 3: Action + explicit, checkable success criteria.
- *Grounding:* OpenAI #1; CO-STAR Objective; Anthropic "be explicit"; Google Task.

**D2. Context & Motivation — weight ×2**
Background, purpose, audience, and — critically — *why* it matters and how the output will be used.
- 0: None. 1: Minimal background. 2: Adequate background + audience. 3: Background + audience + motivation/use.
- *Grounding:* Anthropic "context and motivation" (why-beats-what); Google Context; CO-STAR Context+Audience.

**D3. Specificity & Constraints — weight ×2**
Scope boundaries, length, format constraints, must-haves/must-nots, budget/technical limits — and *no contradictions*.
- 0: Open-ended, no constraints. 1: One or two constraints. 2: Constraints cover the main risks. 3: Tight, complete, internally consistent.
- *Grounding:* Anthropic "be specific"; OpenAI clear-instructions; GPT-5.x "state each instruction once."

**D4. Output Format & Structure — weight ×2**
Is the desired output shape specified (schema, sections, prose-vs-list, delimiters), and does the prompt use delimiters to separate instruction from data?
- 0: Unspecified. 1: Loosely implied. 2: Format stated. 3: Format shown/prefilled + clean instruction–data separation.
- *Grounding:* Google Format; CO-STAR Response; Anthropic format-control (say what *to* do); OpenAI delimiters.

**D5. Model & Parameter Fit — weight ×3**
Is the prompt built for the *class* of model that will run it? Reasoning vs standard; effort/verbosity set; no cross-class anti-patterns.
- 0: Mismatched (e.g. forced CoT on a reasoning model, or a bare one-liner sent to a standard model for a hard task). 1: Class-agnostic. 2: Reasonable fit. 3: Explicitly tuned to model class + parameters.
- *Grounding:* OpenAI reasoning best-practices; Wei (CoT emergent at scale); the §8 divergence table.

**D6. Economy & Clarity — weight ×2**
Minimum necessary structure; plain unambiguous language; no repetition, no bloat, no dead instructions.
- 0: Bloated or confusing. 1: Wordy but followable. 2: Clean. 3: Lean and unambiguous — passes the "confused colleague" test.
- *Grounding:* Anthropic golden rule + "don't over-engineer"; OpenAI/GPT-5.x lean-prompt evals.

**D7. Testability & Iteration-Readiness — weight ×2**
Can output quality be checked against the stated criteria? Is the prompt structured so one variable can be changed and re-tested? Is it robust rather than brittle (single clear format, not a fragile pile)?
- 0: No way to judge success. 1: Judgeable subjectively. 2: Checkable criteria present. 3: Checkable + isolable variables + evaluation/iteration plan implied.
- *Grounding:* Google TCREI Evaluate+Iterate; OpenAI #6; the brittleness literature (§6).

### Conditional dimensions (score only if the task triggers them; otherwise mark N/A)

**D8. Grounding / Reference Material — weight ×3** *(trigger: factual accuracy or domain data matters)*
Is source text/data supplied or retrieved, rather than left to the model's memory?
- 0: Fact-heavy task, no sources. 1: Vague reference. 2: Relevant sources supplied. 3: Sources supplied + scoped to the most relevant (no dump) + citation/uncertainty instruction.
- *Grounding:* OpenAI #2; Google References; reasoning-model "limit RAG context."

**D9. Examples / Shot Design — weight ×2** *(trigger: format/style/pattern is hard to describe)*
Are examples present where they help, consistent in format, and aligned to the wanted behavior — with model class respected?
- 0: Needed but absent, or examples contradict the ask. 1: Present but inconsistent. 2: Clear, consistent example(s). 3: Minimal-sufficient, consistent, behavior-aligned (and omitted/limited for reasoning models).
- *Grounding:* Brown (ICL); Anthropic examples; Min/Lu/Sclar (order & format sensitivity); reasoning-model few-shot caveat.

**D10. Voice: Persona / Style / Tone / Audience — weight ×2** *(trigger: communication quality matters — copy, comms, teaching)*
Is the perspective/voice specified appropriately for the audience — without over-constraining the persona?
- 0: Voice matters but unspecified. 1: Vague ("professional"). 2: Style + audience specified. 3: Style + tone + audience, calibrated and not over-constrained.
- *Grounding:* CO-STAR Style/Tone/Audience; Anthropic role-prompting caveat; Google Persona.

**D11. Hallucination / Safety Guards — weight ×2** *(trigger: high-stakes or factual)*
Permission to express uncertainty; instruction to avoid fabrication; self-verification step where warranted.
- 0: None on a high-stakes task. 1: Implicit. 2: "Say if unsure" present. 3: Uncertainty permission + verification/self-check step.
- *Grounding:* Anthropic uncertainty-permission; OpenAI self-check against gold answers.

> D11 is numbered as an eleventh line item but belongs to the conditional set; treat the rubric as **7 core + 4 conditional**.

## Scoring procedure

1. Score each **applicable** dimension 0–3; mark conditional dimensions N/A when the task doesn't trigger them.
2. Multiply each score by its weight; sum to get **earned points**.
3. Sum `(3 × weight)` over the **applicable** dimensions to get **possible points**.
4. **Score % = earned / possible × 100.**
5. Apply any **disqualifier caps** (below), taking the lower of the computed grade and the cap.

### Grade bands (map to an actionable confidence level)

| % | Grade | Meaning | Action |
|---|---|---|---|
| 90–100 | **A** | No material ambiguity; ready to run | Ship / execute |
| 75–89 | **B** | Minor gaps; light iteration | One clarifying pass |
| 60–74 | **C** | Real gaps the writer must fill | Return with targeted questions |
| < 60 | **D** | Under-specified; rebuild | Guided rewrite from D1 |

### Disqualifier caps (regardless of raw %)

- Forced explicit CoT / "think step by step" sent to a reasoning model → **cap C**.
- Internal contradiction between instructions → **cap C**.
- Complex/multi-step task with no success criteria (D1 = 0) → **cap C**.
- Fact-critical task with zero grounding (D8 = 0 when triggered) → **cap C**.
- Prompt aimed at the wrong model class for the task (D5 = 0) → **cap C**.

## Quick scoring sheet

```
Task type: ____________________   Target model class: [ ] standard  [ ] reasoning

CORE                              score(0-3)  ×w   = pts
D1 Objective & success criteria   [   ]       ×3   ____
D2 Context & motivation           [   ]       ×2   ____
D3 Specificity & constraints      [   ]       ×2   ____
D4 Output format & structure      [   ]       ×2   ____
D5 Model & parameter fit          [   ]       ×3   ____
D6 Economy & clarity              [   ]       ×2   ____
D7 Testability & iteration        [   ]       ×2   ____

CONDITIONAL (N/A if untriggered)
D8 Grounding / reference          [   ]       ×3   ____
D9 Examples / shot design         [   ]       ×2   ____
D10 Voice (persona/style/tone/aud)[   ]       ×2   ____
D11 Hallucination / safety guards [   ]       ×2   ____

Earned pts ____ / Possible pts ____  =  ____%   Grade: ____
Disqualifier caps applied? ________   Final grade: ____
```

## Teaching layer — turning a low score into a fix

The rubric is didactic by design: **the fix for a low dimension is the lesson for that dimension.**

- **D1 low →** "What does a perfect result look like, and how would you check it?" Add a one-line acceptance test.
- **D2 low →** State the audience and *why* you need this; the "why" lets the model resolve edge cases you didn't foresee.
- **D3 low →** Add scope boundaries and one length/format constraint; then scan for any two instructions that fight each other.
- **D4 low →** Show the shape you want (a two-line skeleton or JSON stub) instead of describing it; separate your instructions from your data.
- **D5 low →** Decide the model class first. Standard model + hard task → add reasoning scaffolding. Reasoning model → strip CoT and examples, set the effort level.
- **D6 low →** Cut every sentence that doesn't change the output. Read it as a stranger would.
- **D7 low →** Write the pass/fail check *before* running; change one thing at a time when iterating.
- **D8 low →** Paste the source material (scoped, not dumped) rather than trusting recall; ask for citations.
- **D9 low →** Add one aligned example; only add a second if output still drifts; keep example format identical.
- **D10 low →** Name style, tone, and audience separately (CO-STAR's insight); avoid caricature personas.
- **D11 low →** Add "If you're unsure or the data is insufficient, say so rather than guessing," plus a verification step for high-stakes output.

## Worked example

**Before (Grade D, ~35%):**
> "Write a marketing email about our new product."

D1=1, D2=0, D3=0, D4=1, D5=1, D6=2, D7=0; D8 N/A, D9 N/A, D10=0 (triggered), D11 N/A.

**After (Grade A):**
> "Write a 120-word launch email for **Beta**, an ultra-fast hair dryer from **Alpha**. **Audience:** existing customers aged 45+ who bought from us before (**context:** they value reliability and clear benefits over hype). **Objective:** one click through to the product page. **Style:** warm, plain, benefit-led — in the mould of Dyson's product emails. **Tone:** confident, not salesy. **Format:** subject line + 3 short paragraphs + one CTA button label. If any product detail is missing, leave a clearly marked `[placeholder]` rather than inventing specs. Success = a reader understands the single main benefit and the next action within one read."

Now D1=3, D2=3, D3=3, D4=3, D5=2, D6=3, D7=2, D10=3, D11=3.

---

## References

**Lab guidance**
- Google Workspace / Gemini — PTCF framework and prompt-design strategies (2025).
- Google *Prompting Essentials* — TCREI framework ("Thoughtfully Create Really Excellent Inputs").
- Google Gemini API / Vertex AI — prompt design strategies; parameter guidance.
- OpenAI — *Prompt engineering: six strategies for getting better results.*
- OpenAI — *Reasoning best practices* (o-series) and GPT-5.x model/prompting guidance.
- Anthropic — *Prompt engineering best practices for 2026* (claude.com/blog) and the Claude platform prompting docs.
- Sheila Teo / GovTech Singapore — CO-STAR framework (2023).

**Academic / research**
- Schulhoff et al. (2024). *The Prompt Report: A Systematic Survey of Prompting Techniques.* arXiv:2406.06608.
- Brown et al. (2020). *Language Models are Few-Shot Learners.* (In-context learning.)
- Wei et al. (2022). *Chain-of-Thought Prompting Elicits Reasoning in Large Language Models.* arXiv:2201.11903.
- Kojima et al. (2022). *Large Language Models are Zero-Shot Reasoners.* ("Let's think step by step.")
- Wang et al. (2022). *Self-Consistency Improves Chain of Thought Reasoning.*
- Zhou et al. (2022). *Least-to-Most Prompting.*
- Yao et al. (2023). *Tree of Thoughts*; Besta et al. (2024). *Graph of Thoughts*; Yao et al. (2022). *ReAct.*
- Zhao et al. (2021). *Calibrate Before Use* (format/label sensitivity).
- Lu et al. (2022). *Fantastically Ordered Prompts and Where to Find Them* (order sensitivity).
- Min et al. (2022). *Rethinking the Role of Demonstrations* (label-independence finding).
- Sclar et al. (2024). *Quantifying Language Model Sensitivity to Spurious Prompt Formatting.*
- Bertsch et al. (2024). *In-Context Learning with Long-Context Models* (order sensitivity mitigation).

*Compiled July 2026. Prompting is empirical — treat this rubric as a structured prior, and let testing have the final word.*
