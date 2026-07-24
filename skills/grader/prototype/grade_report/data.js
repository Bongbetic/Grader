// PROTOTYPE fixture — fake finalized report blob (not production schema lock)
window.PROTOTYPE_REPORT = {
  prompt_id: "p-42",
  excerpt: "do NOT write any code, just report… [numbered requirements + scope boundary]",
  craft: {
    band_raw: "B",
    band_adjusted: "C",
    modifier_reason: "high-confidence attributed rework (under-specified opener earlier in task)",
    percent: 87.2,
    confidence: "low",
    model_class: "unknown",
    caps_applied: [],
    dimensions: [
      { id: "D1", level: 3, weight: 3, rationale: "Clear objective + checkable done." },
      { id: "D2", level: 2, weight: 2, rationale: "Background present; motivation thin." },
      { id: "D3", level: 3, weight: 2, rationale: "Scope guards explicit." },
      { id: "D4", level: 3, weight: 2, rationale: "Output format specified." },
      { id: "D5", level: "N/A", weight: 3, rationale: "Model class unknown — excluded from denominator." },
      { id: "D6", level: 2, weight: 2, rationale: "Lean enough; some repetition." },
      { id: "D7", level: 2, weight: 2, rationale: "Iteration-ready with acceptance checks." },
      { id: "D8", level: "N/A", weight: 2, rationale: "No factual grounding needed." },
      { id: "D9", level: "N/A", weight: 1, rationale: "No examples required." },
      { id: "D10", level: "N/A", weight: 1, rationale: "Voice not in play." },
      { id: "D11", level: "N/A", weight: 2, rationale: "Not high-stakes." }
    ]
  },
  efficacy: {
    status: "available",
    attributed_rework_rate: 0.5,
    restates: 2,
    corrections: 1,
    prompts_per_task_mean: 3.2,
    single_shot_rate: 0.25,
    worst_task_prompt_count: 4,
    abandoned_goal: false,
    attribution:
      "2 restates attributed to under-specified opener — not agent misread."
  },
  planning: {
    status: "available",
    planned_decomposition: 1,
    additive_feature: 0,
    adaptive_change_with_evidence: 0,
    scope_change_without_prior_signal: 1,
    under_specified_initial_plan: 1,
    callouts: [
      { kind: "negative", text: "under_specified_initial_plan ×1" },
      { kind: "positive", text: "planned_decomposition ×1" }
    ]
  },
  classification_summary: {
    prompt_class: "structured_dispatch",
    task_complexity: "moderate",
    rework_cause: "user_under_specified"
  },
  security: {
    status: "hit",
    severity: "high",
    summary: "1 secret-shaped token matched residual pattern family (sample fixture).",
    action: "Rotate referenced credential; never paste live keys — point at env."
  },
  slots: {
    strongest: { mode: "llm_slot", hint: "1–2 lines: what worked in this prompt" },
    weakest: { mode: "llm_slot", hint: "1–2 lines: recurring leak to fix" },
    next_actions: { mode: "llm_slot", hint: "3 concrete next practices" }
  },
  unavailable_example: {
    efficacy: { status: "unavailable", reason: "no session context (paste/single-prompt)" },
    planning: { status: "unavailable", reason: "no session context (paste/single-prompt)" }
  }
};
