/** Lawn Assessment Page — multi-finding session with AI remediation plan */
const AssessmentPage = {
  zones: [],
  obsTypes: [],
  findings: [],          // local working list before save
  assessmentId: null,    // set after first save
  analyzing: false,
  currentPlan: null,     // last AI plan rendered
  _scheduleSteps: [],    // working copy for schedule review modal

  async render(container) {
    container.innerHTML = `
      <div class="section-header anim-fade-in">
        <h1 class="section-title">🔍 Lawn Assessment</h1>
        <button class="btn btn-ghost btn-sm" onclick="AssessmentPage._showHistory()">History</button>
      </div>

      <div class="anim-fade-in-up">
        <!-- Step 1: Add findings -->
        <div class="card" id="findingsCard">
          <div class="card-header">
            <span class="card-title">What do you see?</span>
            <span class="text-muted" style="font-size:var(--fs-xs)">Tap all issues you observe</span>
          </div>
          <div class="obs-type-grid" id="typeGrid" style="grid-template-columns:repeat(4,1fr)"></div>
        </div>

        <!-- Current findings list -->
        <div id="findingsList"></div>

        <!-- Overall condition -->
        <div class="card" id="conditionCard" style="display:none">
          <div class="card-header"><span class="card-title">Overall Assessment</span></div>

          <div class="form-group">
            <label class="form-label">Lawn Condition</label>
            <div class="condition-btns" id="conditionBtns">
              <button class="condition-btn" data-val="excellent">Excellent</button>
              <button class="condition-btn" data-val="good">Good</button>
              <button class="condition-btn" data-val="fair">Fair</button>
              <button class="condition-btn" data-val="poor">Poor</button>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">
              Grass Coverage — how much of your lawn is actually grass?
              <span id="coverageVal" style="color:var(--color-accent);font-weight:var(--fw-semibold)">70%</span>
            </label>
            <input type="range" id="grassCoverage" min="0" max="100" value="70" step="5"
              style="width:100%;accent-color:var(--color-accent)">
            <div style="display:flex;justify-content:space-between;font-size:var(--fs-xs);color:var(--text-muted)">
              <span>All weeds/bare</span><span>All grass</span>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">Additional notes (optional)</label>
            <textarea class="form-textarea" id="assessNotes" rows="2"
              placeholder="Recent activities, specific locations, any other context for the AI..."></textarea>
          </div>

          <div id="providerInfo" class="text-muted" style="font-size:var(--fs-xs);margin-bottom:var(--space-md)"></div>

          <button class="btn btn-primary btn-block btn-lg" id="analyzeBtn">
            🤖 Analyze with AI
          </button>
        </div>

        <!-- Remediation plan output -->
        <div id="planOutput"></div>
      </div>
    `;

    this.findings = [];
    this.assessmentId = null;
    this.selectedCondition = null;

    try {
      [this.zones, this.obsTypes] = await Promise.all([API.getZones(), API.getObservationTypes()]);
    } catch (e) { this.zones = []; this.obsTypes = []; }

    this._renderTypeGrid();
    this._bindConditionEvents();
    this._loadProviderInfo();
  },

  _renderTypeGrid() {
    const grid = document.getElementById('typeGrid');
    if (!grid) return;
    grid.innerHTML = this.obsTypes.map(t =>
      `<button class="obs-type-btn" data-value="${t.value}" onclick="AssessmentPage._addFinding('${t.value}','${t.label}','${t.icon}')">
        <span>${t.icon}</span>
        <span style="font-size:var(--fs-xs)">${t.label}</span>
      </button>`
    ).join('');
  },

  _addFinding(type, label, icon) {
    // If already added, open edit
    const existing = this.findings.find(f => f.finding_type === type);
    if (existing) {
      this._editFinding(existing);
      return;
    }

    this._showFindingModal(type, label, icon, null);
  },

  _showFindingModal(type, label, icon, existing) {
    const isEdit = !!existing;
    Modal.show(`${icon} ${label}`, `
      <div style="display:flex;flex-direction:column;gap:var(--space-md)">
        <div class="form-group">
          <label class="form-label">Severity</label>
          <div style="display:flex;gap:var(--space-sm)">
            <button class="sev-btn${existing?.severity === 'low' ? ' active' : ''}" data-sev="low">Low</button>
            <button class="sev-btn${existing?.severity === 'moderate' ? ' active' : ''}" data-sev="moderate">Moderate</button>
            <button class="sev-btn${existing?.severity === 'severe' ? ' active' : ''}" data-sev="severe">Severe</button>
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">
            Coverage — what % of affected area?
            <span id="modalCovVal" style="color:var(--color-accent);font-weight:var(--fw-semibold)">${existing?.coverage_pct || 20}%</span>
          </label>
          <input type="range" id="modalCovRange" min="1" max="100" value="${existing?.coverage_pct || 20}" step="1"
            style="width:100%;accent-color:var(--color-accent)"
            oninput="document.getElementById('modalCovVal').textContent=this.value+'%'">
        </div>
        <div class="form-group">
          <label class="form-label">Location (optional)</label>
          <input type="text" class="form-input" id="modalLocation"
            value="${existing?.location_notes || ''}"
            placeholder="e.g. back yard, along fence, shady areas">
        </div>
        <div style="display:flex;gap:var(--space-sm)">
          <button class="btn btn-primary" style="flex:1"
            onclick="AssessmentPage._saveFindingFromModal('${type}','${label}','${icon}',${isEdit ? JSON.stringify(existing?.id || null) : 'null'})">
            ${isEdit ? 'Update' : 'Add Finding'}
          </button>
          ${isEdit ? `<button class="btn btn-danger" onclick="AssessmentPage._removeFinding('${type}');Modal.close()">Remove</button>` : ''}
        </div>
      </div>
    `);

    // Severity button binding
    setTimeout(() => {
      let selSev = existing?.severity || null;
      document.querySelectorAll('#modalContent .sev-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          document.querySelectorAll('#modalContent .sev-btn').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          selSev = btn.dataset.sev;
          btn.dataset._selected = 'true';
        });
      });
    }, 50);
  },

  _saveFindingFromModal(type, label, icon, existingId) {
    const sevBtn = document.querySelector('#modalContent .sev-btn.active');
    const severity = sevBtn ? sevBtn.dataset.sev : null;
    const coverage = parseInt(document.getElementById('modalCovRange')?.value) || null;
    const location = document.getElementById('modalLocation')?.value?.trim() || null;

    const finding = { finding_type: type, type_label: label, type_icon: icon, severity, coverage_pct: coverage, location_notes: location };

    if (existingId !== null) {
      const idx = this.findings.findIndex(f => f.finding_type === type);
      if (idx >= 0) this.findings[idx] = finding;
    } else {
      this.findings.push(finding);
    }

    Modal.close();
    this._renderFindingsList();
    this._highlightTypeBtn(type);
  },

  _editFinding(finding) {
    this._showFindingModal(finding.finding_type, finding.type_label, finding.type_icon, finding);
  },

  _removeFinding(type) {
    this.findings = this.findings.filter(f => f.finding_type !== type);
    this._renderFindingsList();

    const btn = document.querySelector(`#typeGrid .obs-type-btn[data-value="${type}"]`);
    if (btn) btn.classList.remove('selected');
  },

  _highlightTypeBtn(type) {
    const btn = document.querySelector(`#typeGrid .obs-type-btn[data-value="${type}"]`);
    if (btn) btn.classList.add('selected');
  },

  _renderFindingsList() {
    const el = document.getElementById('findingsList');
    const conditionCard = document.getElementById('conditionCard');
    if (!el) return;

    if (!this.findings.length) {
      el.innerHTML = '';
      if (conditionCard) conditionCard.style.display = 'none';
      return;
    }

    if (conditionCard) conditionCard.style.display = 'block';

    const sevColors = { low: '#20C997', moderate: '#FAB005', severe: '#FA5252' };

    el.innerHTML = `
      <div class="card">
        <div class="card-header">
          <span class="card-title">Findings (${this.findings.length})</span>
          <button class="btn btn-ghost btn-sm" onclick="AssessmentPage._clearAll()">Clear all</button>
        </div>
        ${this.findings.map(f => `
          <div class="finding-chip" onclick="AssessmentPage._editFinding(${JSON.stringify(f).replace(/"/g, '&quot;')})">
            <span style="font-size:1.1rem">${f.type_icon}</span>
            <div style="flex:1;min-width:0">
              <div style="font-size:var(--fs-sm);font-weight:var(--fw-medium)">${f.type_label}</div>
              <div style="font-size:var(--fs-xs);color:var(--text-muted)">
                ${f.severity ? `<span style="color:${sevColors[f.severity]}">${f.severity}</span>` : ''}
                ${f.coverage_pct ? ` · ${f.coverage_pct}% coverage` : ''}
                ${f.location_notes ? ` · ${f.location_notes}` : ''}
              </div>
            </div>
            <span style="font-size:var(--fs-xs);color:var(--text-muted)">Edit ›</span>
          </div>`).join('')}
      </div>`;
  },

  _clearAll() {
    this.findings = [];
    document.querySelectorAll('#typeGrid .obs-type-btn').forEach(b => b.classList.remove('selected'));
    this._renderFindingsList();
  },

  _bindConditionEvents() {
    document.getElementById('conditionBtns')?.addEventListener('click', (e) => {
      const btn = e.target.closest('.condition-btn');
      if (!btn) return;
      document.querySelectorAll('.condition-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      this.selectedCondition = btn.dataset.val;
    });

    const slider = document.getElementById('grassCoverage');
    if (slider) {
      slider.addEventListener('input', () => {
        document.getElementById('coverageVal').textContent = slider.value + '%';
      });
    }

    document.getElementById('analyzeBtn')?.addEventListener('click', () => this._runAnalysis());
  },

  async _loadProviderInfo() {
    const el = document.getElementById('providerInfo');
    if (!el) return;
    try {
      const providers = await API.getAIProviders();
      const active = ['openai', 'anthropic', 'gemini'].find(p => providers[p]?.enabled);
      if (active) {
        el.textContent = `🤖 Using ${active} · ${providers[active].model}`;
      } else {
        el.innerHTML = `<span style="color:var(--color-warning)">⚠ No AI provider configured — add an API key in Settings</span>`;
        if (document.getElementById('analyzeBtn')) {
          document.getElementById('analyzeBtn').disabled = true;
        }
      }
    } catch (e) { el.textContent = ''; }
  },

  async _runAnalysis() {
    if (!this.findings.length) { Toast.warning('Add at least one finding first'); return; }

    const btn = document.getElementById('analyzeBtn');
    btn.disabled = true;
    btn.innerHTML = '<div class="spinner" style="width:18px;height:18px;border-width:2px;display:inline-block;vertical-align:middle;margin-right:8px"></div> Analyzing all findings...';

    const planOutput = document.getElementById('planOutput');
    planOutput.innerHTML = `
      <div class="card" style="text-align:center;padding:var(--space-2xl)">
        <div class="spinner spinner-lg" style="margin:0 auto var(--space-md)"></div>
        <div style="font-weight:var(--fw-semibold)">AI is building your remediation plan...</div>
        <div class="text-muted" style="font-size:var(--fs-xs);margin-top:var(--space-xs)">Analyzing ${this.findings.length} finding${this.findings.length > 1 ? 's' : ''} with your lawn context. This takes 15-30 seconds.</div>
      </div>`;

    try {
      // Save assessment first
      const assessmentData = {
        findings: this.findings,
        overall_condition: this.selectedCondition,
        grass_coverage_pct: parseInt(document.getElementById('grassCoverage')?.value) || null,
        notes: document.getElementById('assessNotes')?.value?.trim() || null,
      };

      const saved = await API.createAssessment(assessmentData);
      this.assessmentId = saved.id;

      // Run AI analysis
      const plan = await API.analyzeAssessment(saved.id);
      this._renderPlan(plan, saved.id);

    } catch (e) {
      planOutput.innerHTML = `<div class="card"><div style="color:var(--color-danger)">⚠ Analysis failed: ${e.message}</div></div>`;
    }

    btn.disabled = false;
    btn.textContent = '🤖 Re-analyze with AI';
  },

  _renderPlan(plan, assessmentId) {
    this.currentPlan = plan;
    const el = document.getElementById('planOutput');
    const priorityColors = { critical: '#E03131', high: '#FA5252', medium: '#FAB005', low: '#20C997' };

    const stepsHtml = (plan.action_steps || []).map((s, i) => {
      const color = priorityColors[s.priority] || 'var(--text-muted)';
      const conflictsHtml = s.conflicts_with?.length
        ? `<div style="font-size:var(--fs-xs);color:var(--color-warning);margin-top:4px">⚠ Don't do at same time as: ${s.conflicts_with.join(', ')}</div>`
        : '';
      return `
        <div class="plan-step" style="border-left:3px solid ${color}">
          <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:var(--space-sm)">
            <div style="display:flex;align-items:center;gap:var(--space-sm);flex:1;min-width:0">
              <span style="font-size:1.1rem;flex-shrink:0">${this._activityIcon(s.activity_type)}</span>
              <div style="flex:1;min-width:0">
                <div style="font-weight:var(--fw-semibold);font-size:var(--fs-sm)">${s.title || s.description || s.activity_type}</div>
                ${s.product_name ? `<div style="font-size:var(--fs-xs);color:var(--color-accent)">📦 ${s.product_name}${s.application_rate ? ' · ' + s.application_rate : ''}</div>` : ''}
                ${s.timing_notes ? `<div class="text-muted" style="font-size:var(--fs-xs)">${s.timing_notes}</div>` : ''}
                ${s.description && s.title ? `<div class="text-muted" style="font-size:var(--fs-xs);margin-top:2px">${s.description}</div>` : ''}
                ${conflictsHtml}
              </div>
            </div>
            <div style="text-align:right;flex-shrink:0">
              <div class="badge" style="background:${color}20;color:${color};font-size:var(--fs-xs)">${s.priority}</div>
              <div class="text-muted" style="font-size:var(--fs-xs);margin-top:4px">${s.week_target || ''}</div>
            </div>
          </div>
        </div>`;
    }).join('');

    const warningsHtml = (plan.key_warnings || []).map(w =>
      `<div style="display:flex;gap:var(--space-sm);padding:var(--space-sm) 0;border-bottom:1px solid var(--border-subtle);font-size:var(--fs-sm)">
        <span>⚠️</span><span>${w}</span>
      </div>`
    ).join('');

    const outcomesHtml = (plan.expected_outcomes || []).map(o => {
      const meta = this.obsTypes.find(t => t.value === o.finding_type) || {};
      return `
        <div style="display:flex;justify-content:space-between;align-items:center;padding:var(--space-xs) 0;font-size:var(--fs-sm)">
          <span>${meta.icon || '🔍'} ${meta.label || o.finding_type}</span>
          <div style="text-align:right">
            <div style="font-size:var(--fs-xs);color:var(--color-success)">${o.expected_resolution || ''}</div>
            <div class="text-muted" style="font-size:var(--fs-xs)">${o.timeline || ''}</div>
          </div>
        </div>`;
    }).join('');

    el.innerHTML = `
      <div class="card mt-lg">
        <div class="card-header">
          <span class="card-title">🤖 Remediation Plan</span>
          <span class="text-muted" style="font-size:var(--fs-xs)">${plan.ai_provider || ''} · ${plan.ai_model || ''}</span>
        </div>

        ${plan.findings_summary ? `
          <p style="font-size:var(--fs-sm);color:var(--text-secondary);margin-bottom:var(--space-md)">${plan.findings_summary}</p>` : ''}

        ${plan.seasonal_context ? `
          <div style="background:rgba(52,144,240,0.06);border:1px solid rgba(52,144,240,0.2);border-radius:var(--radius-md);padding:var(--space-md);margin-bottom:var(--space-md);font-size:var(--fs-sm)">
            📅 ${plan.seasonal_context}
          </div>` : ''}

        ${stepsHtml ? `
          <div style="font-weight:var(--fw-semibold);font-size:var(--fs-sm);margin-bottom:var(--space-sm)">Action Plan</div>
          ${stepsHtml}` : ''}

        ${warningsHtml ? `
          <div style="margin-top:var(--space-lg)">
            <div style="font-weight:var(--fw-semibold);font-size:var(--fs-sm);margin-bottom:var(--space-xs)">⚠️ Treatment Conflicts</div>
            ${warningsHtml}
          </div>` : ''}

        ${outcomesHtml ? `
          <div style="margin-top:var(--space-lg)">
            <div style="font-weight:var(--fw-semibold);font-size:var(--fs-sm);margin-bottom:var(--space-xs)">Expected Outcomes</div>
            ${outcomesHtml}
          </div>` : ''}

        <div style="margin-top:var(--space-xl);display:flex;gap:var(--space-sm);flex-wrap:wrap">
          <button class="btn btn-primary" style="flex:1" onclick="AssessmentPage._showScheduleReview(${assessmentId})">
            📅 Schedule to Lawn Program
          </button>
          <button class="btn btn-secondary" onclick="App.navigate('lawn-program')">
            View Program →
          </button>
        </div>
      </div>`;
  },

  // ── Schedule Review Modal ─────────────────────────────────────

  _inferMonth(step) {
    const now = new Date().getMonth() + 1;
    if (step.schedule_month && step.schedule_month >= 1 && step.schedule_month <= 12) return step.schedule_month;
    const t = (step.week_target || '').toLowerCase();
    const months = { january:1,february:2,march:3,april:4,may:5,june:6,july:7,august:8,september:9,october:10,november:11,december:12 };
    const seasons = { spring:3, summer:6, fall:9, winter:12 };
    for (const [name, m] of Object.entries(months)) { if (t.includes(name)) return m; }
    for (const [name, m] of Object.entries(seasons)) { if (t.includes(name)) return m; }
    if (t.includes('month 3')) return ((now + 1) % 12) + 1;
    if (t.includes('month 2')) return (now % 12) + 1;
    return now;
  },

  _inferWeek(step) {
    if (step.schedule_week && step.schedule_week >= 1 && step.schedule_week <= 4) return step.schedule_week;
    const t = (step.week_target || '').toLowerCase();
    if (t.includes('week 1')) return 1;
    if (t.includes('week 3')) return 3;
    return null;
  },

  _showScheduleReview(assessmentId) {
    if (!this.currentPlan || !this.currentPlan.action_steps?.length) {
      Toast.warning('No action steps to schedule'); return;
    }
    this._scheduleSteps = this.currentPlan.action_steps
      .slice()
      .sort((a, b) => (a.order || 99) - (b.order || 99))
      .map(s => ({
        ai_order: s.order || 1,
        month: this._inferMonth(s),
        week_of_month: this._inferWeek(s),
        step: s,
      }));
    this._renderScheduleModal(assessmentId);
  },

  _renderScheduleModal(assessmentId) {
    const n = this._scheduleSteps.length;
    Modal.show('📅 Schedule to Program', `
      <p style="font-size:var(--fs-xs);color:var(--text-muted);margin-bottom:var(--space-md)">
        AI-suggested months are pre-filled. Adjust timing and drag order as needed, then confirm.
      </p>
      <div id="scheduleStepsList">${this._buildScheduleStepsHtml(assessmentId)}</div>
      <button class="btn btn-primary btn-block" style="margin-top:var(--space-md)"
        onclick="AssessmentPage._confirmAddToProgram(${assessmentId})">
        Add ${n} Step${n !== 1 ? 's' : ''} to Lawn Program
      </button>
    `);
  },

  _buildScheduleStepsHtml(assessmentId) {
    const MONTH_NAMES = ['January','February','March','April','May','June','July','August','September','October','November','December'];
    const priorityColors = { critical:'#E03131', high:'#FA5252', medium:'#FAB005', low:'#20C997' };

    return this._scheduleSteps.map((item, idx) => {
      const s = item.step;
      const pColor = priorityColors[s.priority] || 'var(--text-muted)';
      const monthOpts = MONTH_NAMES.map((m, i) =>
        `<option value="${i+1}"${item.month === i+1 ? ' selected' : ''}>${m}</option>`
      ).join('');
      const weekOpts = `
        <option value=""${!item.week_of_month ? ' selected' : ''}>Any time</option>
        <option value="1"${item.week_of_month===1?' selected':''}>Week 1</option>
        <option value="2"${item.week_of_month===2?' selected':''}>Week 2</option>
        <option value="3"${item.week_of_month===3?' selected':''}>Week 3</option>
        <option value="4"${item.week_of_month===4?' selected':''}>Week 4</option>`;

      const isFirst = idx === 0;
      const isLast = idx === this._scheduleSteps.length - 1;

      return `
        <div style="border-left:3px solid ${pColor};padding:var(--space-sm) var(--space-md);margin-bottom:var(--space-sm);background:var(--bg-surface-2);border-radius:var(--radius-md)">
          <div style="display:flex;align-items:center;gap:var(--space-sm);margin-bottom:var(--space-xs)">
            <div style="display:flex;flex-direction:column;gap:2px;flex-shrink:0">
              <button class="btn btn-ghost" style="padding:2px 8px;font-size:10px;line-height:1.4"
                onclick="AssessmentPage._moveScheduleStep(${idx},-1,${assessmentId})"${isFirst?' disabled':''}>▲</button>
              <button class="btn btn-ghost" style="padding:2px 8px;font-size:10px;line-height:1.4"
                onclick="AssessmentPage._moveScheduleStep(${idx},1,${assessmentId})"${isLast?' disabled':''}>▼</button>
            </div>
            <span style="font-size:1rem;flex-shrink:0">${this._activityIcon(s.activity_type)}</span>
            <div style="flex:1;min-width:0">
              <div style="font-size:var(--fs-sm);font-weight:var(--fw-medium);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${s.title || s.activity_type}</div>
              ${s.product_name ? `<div style="font-size:var(--fs-xs);color:var(--color-accent)">${s.product_name}</div>` : ''}
              ${s.timing_notes ? `<div style="font-size:var(--fs-xs);color:var(--text-muted)">${s.timing_notes}</div>` : ''}
            </div>
            <span class="badge" style="background:${pColor}20;color:${pColor};font-size:var(--fs-xs);flex-shrink:0">${s.priority}</span>
          </div>
          <div style="display:flex;gap:var(--space-sm);margin-left:52px">
            <div style="flex:1">
              <div style="font-size:10px;color:var(--text-muted);margin-bottom:2px">Month</div>
              <select class="form-select" style="font-size:var(--fs-xs);padding:4px 8px"
                onchange="AssessmentPage._updateScheduleMonth(${idx},parseInt(this.value))">${monthOpts}</select>
            </div>
            <div style="width:90px">
              <div style="font-size:10px;color:var(--text-muted);margin-bottom:2px">Week</div>
              <select class="form-select" style="font-size:var(--fs-xs);padding:4px 8px"
                onchange="AssessmentPage._updateScheduleWeek(${idx},this.value?parseInt(this.value):null)">${weekOpts}</select>
            </div>
          </div>
        </div>`;
    }).join('');
  },

  _moveScheduleStep(idx, direction, assessmentId) {
    const newIdx = idx + direction;
    if (newIdx < 0 || newIdx >= this._scheduleSteps.length) return;
    [this._scheduleSteps[idx], this._scheduleSteps[newIdx]] = [this._scheduleSteps[newIdx], this._scheduleSteps[idx]];
    const listEl = document.getElementById('scheduleStepsList');
    if (listEl) listEl.innerHTML = this._buildScheduleStepsHtml(assessmentId);
  },

  _updateScheduleMonth(idx, month) { this._scheduleSteps[idx].month = month; },
  _updateScheduleWeek(idx, week) { this._scheduleSteps[idx].week_of_month = week; },

  async _confirmAddToProgram(assessmentId) {
    const stepsSchedule = this._scheduleSteps.map((item, i) => ({
      ai_order: item.ai_order,
      user_order: i + 1,
      month: item.month,
      week_of_month: item.week_of_month,
    }));
    try {
      const result = await API.addAssessmentToProgram(assessmentId, { steps_schedule: stepsSchedule });
      Modal.close();
      Toast.success(`${result.steps_added} steps added to your Lawn Program`);
      setTimeout(() => App.navigate('my-lawn', { tab: 'program' }), 600);
    } catch (e) { Toast.error(e.message); }
  },

  async _showHistory() {
    try {
      const history = await API.getAssessments();
      if (!history.length) {
        Modal.show('Assessment History', '<div class="text-muted text-center" style="padding:var(--space-lg)">No past assessments.</div>');
        return;
      }
      Modal.show('Assessment History', `
        <div style="display:flex;flex-direction:column;gap:var(--space-sm)">
          ${history.map(a => `
            <div class="card" style="cursor:pointer" onclick="Modal.close();AssessmentPage._loadAssessment(${a.id})">
              <div style="font-size:var(--fs-sm);font-weight:var(--fw-medium)">${Fmt.date(a.date)}</div>
              <div class="text-muted" style="font-size:var(--fs-xs)">${a.finding_count} findings · ${a.overall_condition || 'no condition'} · ${a.ai_analyzed ? '✓ AI analyzed' : 'Not analyzed'}</div>
            </div>`).join('')}
        </div>`);
    } catch (e) { Toast.error(e.message); }
  },

  async _loadAssessment(id) {
    try {
      const a = await API.getAssessment(id);
      this.findings = (a.findings || []).map(f => ({
        finding_type: f.finding_type,
        type_label: f.type_label,
        type_icon: f.type_icon,
        severity: f.severity,
        coverage_pct: f.coverage_pct,
        location_notes: f.location_notes,
      }));
      this.assessmentId = a.id;

      this._renderFindingsList();
      a.findings.forEach(f => this._highlightTypeBtn(f.finding_type));

      if (a.overall_condition) {
        this.selectedCondition = a.overall_condition;
        document.querySelectorAll('.condition-btn').forEach(b => {
          b.classList.toggle('active', b.dataset.val === a.overall_condition);
        });
      }

      if (a.remediation_plan) {
        this._renderPlan(a.remediation_plan, a.id);
      }

      const conditionCard = document.getElementById('conditionCard');
      if (conditionCard && this.findings.length) conditionCard.style.display = 'block';

      window.scrollTo({ top: 0, behavior: 'smooth' });
      Toast.success('Assessment loaded');
    } catch (e) { Toast.error(e.message); }
  },

  _activityIcon(type) {
    const icons = {
      fertilize: '🌿', weed_control: '🌾', pre_emergent: '🛡️', post_emergent: '☠️',
      fungicide: '🍄', pest_control: '🪲', overseed: '🌱', aerate: '🔵',
      lime: '🪨', dethatch: '🧹', other: '📋',
    };
    return icons[type] || '📋';
  },
};
