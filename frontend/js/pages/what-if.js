/** What-If / AI Consult Page — scenario-based AI lawn care recommendations */
const WhatIfPage = {
  obsTypes: [],
  selectedObsType: null,
  prefillObsId: null,

  async render(container) {
    container.innerHTML = `
      <div class="section-header anim-fade-in">
        <h1 class="section-title">🌿 Lawn Coach</h1>
      </div>

      <div class="anim-fade-in-up anim-delay-1" id="consultSection">
        <div class="card">
          <div class="card-header"><span class="card-title">Ask About Your Lawn</span></div>
          <p class="text-secondary" style="font-size:var(--fs-sm);margin-bottom:var(--space-md)">
            Describe what you're seeing or ask any lawn care question. The AI uses your full lawn context — soil tests, weather, recent activities, and seasonal alerts.
          </p>

          <div class="form-group">
            <label class="form-label">What are you observing? (optional)</label>
            <div class="obs-type-grid" id="wiObsGrid" style="grid-template-columns:repeat(4,1fr)"></div>
          </div>

          <div class="form-group">
            <label class="form-label">Severity</label>
            <div style="display:flex;gap:var(--space-sm)">
              <button class="sev-btn" data-sev="low">Low</button>
              <button class="sev-btn" data-sev="moderate">Moderate</button>
              <button class="sev-btn" data-sev="severe">Severe</button>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">Your Question</label>
            <textarea class="form-textarea" id="wiQuestion" rows="3"
              placeholder="e.g. 'I see clover taking over my front yard — what should I do?' or 'Is it safe to fertilize with this heat?'"></textarea>
          </div>

          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:var(--space-md)">
            <div id="wiProviderInfo" class="text-muted" style="font-size:var(--fs-xs)">Loading AI provider...</div>
          </div>

          <button class="btn btn-primary btn-block btn-lg" id="wiSubmitBtn">🤖 Get AI Recommendation</button>
        </div>
      </div>

      <div id="wiResult" class="anim-fade-in-up"></div>

      <div class="section-header mt-lg"><span class="section-title" style="font-size:var(--fs-md)">Past Consultations</span></div>
      <div id="wiHistory" class="anim-fade-in-up">
        <div class="loading-center"><div class="spinner spinner-sm"></div></div>
      </div>
    `;

    this.selectedObsType = null;
    this.selectedSeverity = null;

    try {
      this.obsTypes = await API.getObservationTypes();
    } catch (e) { this.obsTypes = []; }

    this._renderObsGrid();
    this._loadProviderInfo();
    this._bindEvents();
    this._loadHistory();

    if (this.prefillObsId) {
      await this._applyPrefill();
    }
  },

  _renderObsGrid() {
    const grid = document.getElementById('wiObsGrid');
    if (!grid) return;
    grid.innerHTML = this.obsTypes.map(t =>
      `<button class="obs-type-btn" data-value="${t.value}">
        <span>${t.icon}</span>
        <span style="font-size:var(--fs-xs)">${t.label}</span>
      </button>`
    ).join('');

    grid.addEventListener('click', (e) => {
      const btn = e.target.closest('.obs-type-btn');
      if (!btn) return;
      if (this.selectedObsType === btn.dataset.value) {
        btn.classList.remove('selected');
        this.selectedObsType = null;
      } else {
        document.querySelectorAll('#wiObsGrid .obs-type-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        this.selectedObsType = btn.dataset.value;
        this._autoFillQuestion();
      }
    });
  },

  _autoFillQuestion() {
    const qEl = document.getElementById('wiQuestion');
    if (!qEl || qEl.value.trim()) return;
    const typeLabel = this.obsTypes.find(t => t.value === this.selectedObsType)?.label || this.selectedObsType;
    const sev = this.selectedSeverity ? ` (${this.selectedSeverity} severity)` : '';
    qEl.value = `I'm seeing ${typeLabel}${sev} in my lawn. What's causing this and what should I do to fix it?`;
  },

  _bindEvents() {
    document.querySelectorAll('.sev-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const same = this.selectedSeverity === btn.dataset.sev;
        document.querySelectorAll('.sev-btn').forEach(b => b.classList.remove('active'));
        this.selectedSeverity = same ? null : btn.dataset.sev;
        if (!same) btn.classList.add('active');
        this._autoFillQuestion();
      });
    });

    document.getElementById('wiSubmitBtn').addEventListener('click', () => this._submit());
  },

  async _loadProviderInfo() {
    const el = document.getElementById('wiProviderInfo');
    try {
      const providers = await API.getAIProviders();
      const active = ['openai', 'anthropic', 'gemini'].find(p => providers[p]?.enabled);
      if (active) {
        el.textContent = `🤖 Using ${active} · ${providers[active].model}`;
      } else {
        el.innerHTML = `<span style="color:var(--color-warning)">⚠ No AI provider configured</span>`;
        document.getElementById('wiSubmitBtn').disabled = true;
      }
    } catch (e) { el.textContent = ''; }
  },

  async _submit() {
    const question = document.getElementById('wiQuestion').value.trim();
    if (!question) { Toast.warning('Enter a question'); return; }

    const btn = document.getElementById('wiSubmitBtn');
    btn.disabled = true;
    btn.innerHTML = '<div class="spinner" style="width:18px;height:18px;border-width:2px;display:inline-block;vertical-align:middle;margin-right:8px"></div> Analyzing...';

    const resultEl = document.getElementById('wiResult');
    resultEl.innerHTML = `
      <div class="card" style="text-align:center;padding:var(--space-2xl)">
        <div class="spinner spinner-lg" style="margin:0 auto var(--space-md)"></div>
        <div class="text-secondary">AI is analyzing your lawn context...</div>
        <div class="text-muted" style="font-size:var(--fs-xs)">This may take 10-20 seconds</div>
      </div>`;

    try {
      let fullQuestion = question;
      if (this.selectedObsType) {
        const label = this.obsTypes.find(t => t.value === this.selectedObsType)?.label || this.selectedObsType;
        fullQuestion = `Observation: ${label}${this.selectedSeverity ? ` (${this.selectedSeverity} severity)` : ''}. ${question}`;
      }

      const data = { question: fullQuestion };
      if (this.prefillObsId) {
        data.observation_ids = [this.prefillObsId];
        this.prefillObsId = null;
      }

      const result = await API.aiConsult(data);
      this._renderResult(result);
      this._loadHistory();
    } catch (e) {
      resultEl.innerHTML = `<div class="card"><div style="color:var(--color-danger)">⚠ ${e.message}</div></div>`;
    }

    btn.disabled = false;
    btn.textContent = '🤖 Get AI Recommendation';
  },

  _renderResult(r) {
    const el = document.getElementById('wiResult');

    const actionsHtml = (r.immediate_actions || []).map(a => `
      <div style="display:flex;gap:var(--space-sm);align-items:flex-start;padding:var(--space-sm) 0;border-bottom:1px solid var(--border-subtle)">
        <span class="badge badge-${a.priority === 'immediate' ? 'danger' : a.priority === 'soon' ? 'warning' : 'info'}" style="flex-shrink:0;font-size:var(--fs-xs)">${a.priority || 'action'}</span>
        <div>
          <div style="font-size:var(--fs-sm);font-weight:var(--fw-medium)">${a.action}</div>
          ${a.details ? `<div class="text-muted" style="font-size:var(--fs-xs)">${a.details}</div>` : ''}
        </div>
      </div>`).join('');

    const productsHtml = (r.products || []).map(p => `
      <div style="padding:var(--space-sm) 0;border-bottom:1px solid var(--border-subtle)">
        <div style="font-weight:var(--fw-semibold);font-size:var(--fs-sm)">${p.name}</div>
        <div class="text-muted" style="font-size:var(--fs-xs)">
          ${p.category ? `${p.category} · ` : ''}${p.application_rate || ''} ${p.timing ? `· ${p.timing}` : ''}
        </div>
        ${p.notes ? `<div class="text-secondary" style="font-size:var(--fs-xs);margin-top:2px">${p.notes}</div>` : ''}
      </div>`).join('');

    el.innerHTML = `
      <div class="card mt-lg">
        <div class="card-header">
          <span class="card-title">🤖 AI Recommendation</span>
          <span class="text-muted" style="font-size:var(--fs-xs)">${r.ai_provider || ''} · ${r.ai_model || ''}</span>
        </div>

        ${r.summary ? `<p style="font-size:var(--fs-sm);color:var(--text-secondary);margin-bottom:var(--space-lg)">${r.summary}</p>` : ''}

        ${r.root_cause ? `
          <div class="card" style="background:rgba(52,144,240,0.06);border:1px solid rgba(52,144,240,0.2);margin-bottom:var(--space-md)">
            <div style="font-weight:var(--fw-semibold);font-size:var(--fs-sm);margin-bottom:var(--space-xs)">🔍 Root Cause</div>
            <div style="font-size:var(--fs-sm)">${r.root_cause}</div>
          </div>` : ''}

        ${actionsHtml ? `
          <div style="font-weight:var(--fw-semibold);font-size:var(--fs-sm);margin-bottom:var(--space-sm)">⚡ Actions</div>
          ${actionsHtml}` : ''}

        ${productsHtml ? `
          <div style="font-weight:var(--fw-semibold);font-size:var(--fs-sm);margin:var(--space-md) 0 var(--space-sm)">🛒 Recommended Products</div>
          ${productsHtml}` : ''}

        ${r.prevention ? `
          <div class="card" style="background:rgba(82,183,136,0.06);border:1px solid rgba(82,183,136,0.2);margin-top:var(--space-md)">
            <div style="font-weight:var(--fw-semibold);font-size:var(--fs-sm);margin-bottom:var(--space-xs)">🛡️ Long-Term Prevention</div>
            <div style="font-size:var(--fs-sm)">${r.prevention}</div>
          </div>` : ''}

        ${r.expected_timeline ? `
          <div class="text-muted" style="font-size:var(--fs-xs);margin-top:var(--space-md)">⏱ Timeline: ${r.expected_timeline}</div>` : ''}

        ${r.watch_for ? `
          <div class="text-muted" style="font-size:var(--fs-xs);margin-top:var(--space-xs)">👁 Watch for: ${r.watch_for}</div>` : ''}
      </div>`;
  },

  async _loadHistory() {
    const el = document.getElementById('wiHistory');
    if (!el) return;
    try {
      const history = await API.getConsultationHistory();
      if (!history.length) {
        el.innerHTML = '<div class="text-muted text-center" style="padding:var(--space-md)">No past consultations yet.</div>';
        return;
      }
      el.innerHTML = history.map(c => `
        <div class="card" style="cursor:pointer" onclick="WhatIfPage._viewHistory(${c.id})">
          <div style="font-size:var(--fs-sm);font-weight:var(--fw-medium)">${c.question}</div>
          ${c.summary ? `<div class="text-muted" style="font-size:var(--fs-xs);margin-top:4px">${c.summary.substring(0, 100)}...</div>` : ''}
          <div class="text-muted" style="font-size:var(--fs-xs);margin-top:4px">${Fmt.relativeDate(c.created_at)} · ${c.ai_provider || ''}</div>
        </div>`).join('');
    } catch (e) { el.innerHTML = ''; }
  },

  async _viewHistory(id) {
    try {
      const r = await API.getConsultation(id);
      this._renderResult(r);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (e) { Toast.error(e.message); }
  },

  prefillObservation(obsId, label) {
    this.prefillObsId = obsId;
    const qEl = document.getElementById('wiQuestion');
    if (qEl) {
      qEl.value = `I'm seeing ${label} in my lawn — what's causing it and how should I treat it?`;
    }
  },

  async _applyPrefill() {
    const qEl = document.getElementById('wiQuestion');
    if (qEl && !qEl.value) {
      qEl.value = `I have an active observation I'd like help with. What should I do?`;
    }
  },
};
