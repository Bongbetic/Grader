// PROTOTYPE — throwaway grade_report UI switcher + variants
(function () {
  const VARIANTS = [
    { key: "A", name: "Linear dossier" },
    { key: "B", name: "Tri-pane cockpit" },
    { key: "C", name: "Focus rail" }
  ];

  function getVariant() {
    const v = new URLSearchParams(location.search).get("variant") || "A";
    return VARIANTS.some((x) => x.key === v) ? v : "A";
  }

  function setVariant(key) {
    const url = new URL(location.href);
    url.searchParams.set("variant", key);
    history.replaceState(null, "", url);
    render();
  }

  function cycle(delta) {
    const keys = VARIANTS.map((v) => v.key);
    const i = keys.indexOf(getVariant());
    const next = keys[(i + delta + keys.length) % keys.length];
    setVariant(next);
  }

  function esc(s) {
    return String(s)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function dimRows(dims) {
    return dims
      .map(
        (d) =>
          `<tr><td>${esc(d.id)}</td><td>${esc(d.level)}</td><td>×${esc(
            d.weight
          )}</td><td>${esc(d.rationale)}</td></tr>`
      )
      .join("");
  }

  function securityBlock(sec) {
    if (sec.status === "hit") {
      return `<div class="security-hit"><strong>Security · ${esc(
        sec.severity
      )}</strong><div>${esc(sec.summary)}</div><div>${esc(
        sec.action
      )}</div></div>`;
    }
    return `<div class="security-ok"><strong>Security</strong><div>none detected</div></div>`;
  }

  function slot(label, slotObj) {
    return `<div class="slot-box"><strong>${esc(
      label
    )}</strong> <span class="hint">[LLM slot]</span><div class="hint">${esc(
      slotObj.hint
    )}</div></div>`;
  }

  function efficacyBlock(e) {
    if (e.status === "unavailable") {
      return `<p class="meta-muted">unavailable — ${esc(e.reason)}</p>`;
    }
    return `
      <p class="metric-line"><strong>${esc(
        (e.attributed_rework_rate * 100).toFixed(0)
      )}%</strong> attributed rework</p>
      <p>restates ${esc(e.restates)} · corrections ${esc(
      e.corrections
    )} · prompts/task ${esc(e.prompts_per_task_mean)} · worst ${esc(
      e.worst_task_prompt_count
    )}</p>
      <p>${esc(e.attribution)}</p>`;
  }

  function planningBlock(p) {
    if (p.status === "unavailable") {
      return `<p class="meta-muted">unavailable — ${esc(p.reason)}</p>`;
    }
    const calls = (p.callouts || [])
      .map(
        (c) =>
          `<li class="${
            c.kind === "negative" ? "callout-neg" : "callout-pos"
          }">${esc(c.text)}</li>`
      )
      .join("");
    return `
      <ul>
        <li>planned_decomposition: ${esc(p.planned_decomposition)}</li>
        <li>under_specified_initial_plan: ${esc(
          p.under_specified_initial_plan
        )}</li>
        <li>scope_change_without_prior_signal: ${esc(
          p.scope_change_without_prior_signal
        )}</li>
        <li>additive_feature: ${esc(p.additive_feature)}</li>
        <li>adaptive_change_with_evidence: ${esc(
          p.adaptive_change_with_evidence
        )}</li>
      </ul>
      <ul>${calls}</ul>`;
  }

  function VariantA(r) {
    const c = r.craft;
    return `
    <article class="variant-a">
      <p class="prototype-banner" style="margin:-1.5rem -1.25rem 1.25rem">Prototype · Variant A · Linear dossier</p>
      <h1 class="title">Prompt grade</h1>
      <p class="lede">${esc(r.prompt_id)} · class ${esc(
      r.classification_summary.prompt_class
    )} · complexity ${esc(r.classification_summary.task_complexity)}</p>
      <div class="excerpt">${esc(r.excerpt)}</div>
      <div class="craft-head">
        <div class="band-letter">${esc(c.band_adjusted)}</div>
        <div>
          <div><strong>Craft</strong> adjusted from raw ${esc(
            c.band_raw
          )}</div>
          <div class="meta-muted">~${esc(
            c.percent
          )}% · confidence ${esc(c.confidence)} · model_class ${esc(
      c.model_class
    )}</div>
          <div>${esc(c.modifier_reason)}</div>
        </div>
      </div>
      ${securityBlock(r.security)}
      <h2>Efficacy</h2>
      ${efficacyBlock(r.efficacy)}
      <h2>Planning</h2>
      ${planningBlock(r.planning)}
      <h2>Dimensions</h2>
      <table class="dim-table">
        <thead><tr><th>ID</th><th>Lvl</th><th>Wt</th><th>Rationale</th></tr></thead>
        <tbody>${dimRows(c.dimensions)}</tbody>
      </table>
      <h2>Coaching slots</h2>
      ${slot("Strongest", r.slots.strongest)}
      ${slot("Weakest", r.slots.weakest)}
      ${slot("Next actions", r.slots.next_actions)}
    </article>`;
  }

  function VariantB(r) {
    const c = r.craft;
    const chips = c.dimensions
      .map(
        (d) =>
          `<span class="chip ${d.level === "N/A" ? "na" : ""}">${esc(
            d.id
          )} ${esc(d.level)}</span>`
      )
      .join("");
    return `
    <div class="variant-b">
      <div class="prototype-banner">Prototype · Variant B · Tri-pane cockpit</div>
      <header class="topbar">
        <div>
          <div class="meta-muted">${esc(r.prompt_id)}</div>
          <div>Craft <span class="band-letter" style="font-size:2.2rem;vertical-align:-0.2rem">${esc(
            c.band_adjusted
          )}</span>
          <span class="meta-muted">raw ${esc(c.band_raw)} · ~${esc(
      c.percent
    )}% · ${esc(c.confidence)}</span></div>
          <div class="meta-muted">${esc(c.modifier_reason)}</div>
        </div>
        <div style="max-width:22rem">${securityBlock(r.security)}</div>
      </header>
      <div class="panes">
        <section class="pane">
          <h2>Craft</h2>
          <p class="metric">${esc(c.band_adjusted)}</p>
          <p class="meta-muted">D5 N/A when class unknown · caps: ${
            c.caps_applied.length ? esc(c.caps_applied.join(", ")) : "none"
          }</p>
          <p class="meta-muted">${esc(r.excerpt)}</p>
        </section>
        <section class="pane">
          <h2>Efficacy</h2>
          ${efficacyBlock(r.efficacy)}
        </section>
        <section class="pane">
          <h2>Planning</h2>
          ${planningBlock(r.planning)}
        </section>
      </div>
      <div class="dims">
        <div class="meta-muted" style="margin-bottom:0.5rem">Dimensions</div>
        <div class="dim-chips">${chips}</div>
      </div>
      <div class="coaching">
        ${slot("Strongest", r.slots.strongest)}
        ${slot("Weakest", r.slots.weakest)}
        ${slot("Next actions", r.slots.next_actions)}
      </div>
    </div>`;
  }

  function VariantC(r) {
    const c = r.craft;
    const cells = c.dimensions
      .map(
        (d) =>
          `<div class="dim-cell"><span>${esc(d.id)}</span><strong>${esc(
            d.level
          )}</strong></div>`
      )
      .join("");
    return `
    <div class="variant-c">
      <aside class="focus">
        <div class="prototype-banner" style="margin:-2rem -1.5rem 0;background:#072c36">Prototype · Variant C · Focus rail</div>
        <div class="meta-muted" style="color:#9ec9d1">${esc(r.prompt_id)}</div>
        <div class="band-letter">${esc(c.band_adjusted)}</div>
        <div>
          <div>Craft · raw ${esc(c.band_raw)} → adjusted ${esc(
      c.band_adjusted
    )}</div>
          <div class="meta-muted" style="color:#9ec9d1">~${esc(
            c.percent
          )}% · confidence ${esc(c.confidence)}</div>
        </div>
        <div class="modifier">${esc(c.modifier_reason)}</div>
        <div class="meta-muted" style="color:#9ec9d1;font-size:0.85rem">${esc(
          r.excerpt
        )}</div>
      </aside>
      <div class="rail">
        <section class="card">
          <h2>Security</h2>
          ${securityBlock(r.security)}
        </section>
        <section class="card">
          <h2>Efficacy</h2>
          ${efficacyBlock(r.efficacy)}
        </section>
        <section class="card">
          <h2>Planning</h2>
          ${planningBlock(r.planning)}
        </section>
        <section class="card">
          <h2>Dimensions</h2>
          <div class="dims-compact">${cells}</div>
        </section>
        <section class="card">
          <h2>Classification</h2>
          <p>${esc(r.classification_summary.prompt_class)} · ${esc(
      r.classification_summary.rework_cause
    )}</p>
        </section>
        <section class="card">
          <h2>Coaching slots</h2>
          ${slot("Strongest", r.slots.strongest)}
          ${slot("Weakest", r.slots.weakest)}
          ${slot("Next actions", r.slots.next_actions)}
        </section>
      </div>
    </div>`;
  }

  function renderSwitcher(meta) {
    return `
    <div class="prototype-switcher" role="navigation" aria-label="Prototype variants">
      <button type="button" data-dir="-1" aria-label="Previous variant">←</button>
      <div class="label">${esc(meta.key)} — ${esc(meta.name)}</div>
      <button type="button" data-dir="1" aria-label="Next variant">→</button>
    </div>`;
  }

  function render() {
    const key = getVariant();
    const meta = VARIANTS.find((v) => v.key === key);
    const r = window.PROTOTYPE_REPORT;
    const body =
      key === "B" ? VariantB(r) : key === "C" ? VariantC(r) : VariantA(r);

    document.getElementById("app").innerHTML = body;
    document.getElementById("switcher").innerHTML = renderSwitcher(meta);
    document.getElementById("state").textContent = JSON.stringify(
      {
        question:
          "Which layout makes Craft/Efficacy/Planning/Security/slots scannable?",
        variant: meta,
        fixture_prompt_id: r.prompt_id,
        craft_adjusted: r.craft.band_adjusted,
        security: r.security.status
      },
      null,
      2
    );

    document.querySelectorAll(".prototype-switcher button").forEach((btn) => {
      btn.addEventListener("click", () => cycle(Number(btn.dataset.dir)));
    });
  }

  document.addEventListener("keydown", (e) => {
    const t = e.target;
    if (
      t &&
      (t.tagName === "INPUT" ||
        t.tagName === "TEXTAREA" ||
        t.isContentEditable)
    ) {
      return;
    }
    if (e.key === "ArrowLeft") cycle(-1);
    if (e.key === "ArrowRight") cycle(1);
  });

  render();
})();
