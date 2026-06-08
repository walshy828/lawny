/** Lawn Program Page — unified fertilizer + AI remediation calendar */
const LawnProgramPage = {
  program: null,

  async render(container) {
    container.innerHTML = `
      <div class="section-header anim-fade-in">
        <h1 class="section-title">📋 Lawn Program</h1>
        <button class="btn btn-primary btn-sm" id="generateBtn">⚡ Generate</button>
      </div>

      <div id="programContent" class="anim-fade-in-up">
        <div class="loading-center"><div class="spinner"></div></div>
      </div>
    `;

    document.getElementById('generateBtn').addEventListener('click', () => this._generateProgram());
    await this._load();
  },

  async _load() {
    const el = document.getElementById('programContent');
    try {
      const program = await API.getActiveProgram();
      this.program = program;

      if (!program) {
        el.innerHTML = `
          <div class="card" style="text-align:center;padding:var(--space-2xl)">
            <div style="font-size:3rem;margin-bottom:var(--space-md)">📋</div>
            <div style="font-size:var(--fs-lg);font-weight:var(--fw-semibold);margin-bottom:var(--space-sm)">No Lawn Program Yet</div>
            <p class="text-secondary" style="font-size:var(--fs-sm);margin-bottom:var(--space-lg)">
              Generate your first lawn program by combining your fertilizer schedule with an AI remediation plan from a lawn assessment.
            </p>
            <div style="display:flex;flex-direction:column;gap:var(--space-sm);max-width:280px;margin:0 auto">
              <button class="btn btn-primary" onclick="App.navigate('assessment')">🔍 Run an Assessment First</button>
              <button class="btn btn-secondary" onclick="LawnProgramPage._generateProgram()">⚡ Generate from Fertilizer Only</button>
            </div>
          </div>`;
        return;
      }

      this._renderProgram(program, el);
    } catch (e) {
      el.innerHTML = `<div class="text-muted">Error: ${e.message}</div>`;
    }
  },

  _renderProgram(program, container) {
    const done = program.completed_steps;
    const total = program.total_steps;
    const pct = program.progress_pct;

    const sourceColors = { fertilizer: '#20C997', ai_remediation: '#339AF0', manual: '#FAB005' };
    const sourceLabels = { fertilizer: 'Fertilizer', ai_remediation: 'AI Plan', manual: 'Manual' };

    container.innerHTML = `
      <div class="card" style="margin-bottom:var(--space-md)">
        <div class="card-header">
          <span class="card-title">${program.name}</span>
          <span class="badge badge-accent">${program.season_year}</span>
        </div>
        <div style="margin:var(--space-sm) 0">
          <div style="display:flex;justify-content:space-between;font-size:var(--fs-xs);color:var(--text-muted);margin-bottom:4px">
            <span>${done} of ${total} completed</span><span>${pct}%</span>
          </div>
          <div style="background:var(--bg-surface-2);border-radius:99px;height:6px">
            <div style="background:var(--color-accent);border-radius:99px;height:6px;width:${pct}%;transition:width 0.5s ease"></div>
          </div>
        </div>
        <div style="display:flex;gap:var(--space-sm);font-size:var(--fs-xs)">
          <span><span style="color:#20C997">●</span> Fertilizer</span>
          <span><span style="color:#339AF0">●</span> AI Remediation</span>
          <span><span style="color:#FAB005">●</span> Manual</span>
        </div>
      </div>

      ${program.by_month.map(m => this._renderMonth(m, sourceColors, sourceLabels)).join('')}

      <div style="margin-top:var(--space-lg);display:flex;gap:var(--space-sm)">
        <button class="btn btn-ghost btn-sm" onclick="LawnProgramPage._addManualStep()">+ Add Step</button>
        <button class="btn btn-ghost btn-sm" onclick="App.navigate('assessment')">🔍 Run New Assessment</button>
      </div>
    `;
  },

  _renderMonth(monthData, sourceColors, sourceLabels) {
    const now = new Date();
    const isCurrentMonth = monthData.month === now.getMonth() + 1;
    const isPast = monthData.month < now.getMonth() + 1;

    const headerStyle = isCurrentMonth
      ? 'color:var(--color-accent);font-weight:var(--fw-bold)'
      : isPast ? 'color:var(--text-muted)' : 'color:var(--text-primary)';

    const stepsHtml = monthData.steps.map(s => this._renderStep(s, sourceColors, sourceLabels)).join('');

    return `
      <div class="program-month" style="${isPast ? 'opacity:0.7' : ''}">
        <div class="program-month-header" style="${headerStyle}">
          ${isCurrentMonth ? '▶ ' : ''}${monthData.month_name}
          ${isCurrentMonth ? '<span style="font-size:var(--fs-xs);font-weight:normal;color:var(--color-accent);margin-left:4px">Current</span>' : ''}
        </div>
        <div class="program-month-steps">
          ${stepsHtml}
        </div>
      </div>`;
  },

  _renderStep(s, sourceColors, sourceLabels) {
    const isDone = s.status === 'done';
    const isSkipped = s.status === 'skipped';
    const color = sourceColors[s.source] || 'var(--text-muted)';
    const priorityColors = { critical: '#E03131', high: '#FA5252', medium: '#FAB005', low: '#20C997' };
    const pColor = priorityColors[s.priority] || 'var(--text-muted)';

    const conflictsHtml = s.conflicts_with?.length
      ? `<div style="font-size:var(--fs-xs);color:var(--color-warning);margin-top:2px">⚠ Conflicts: ${s.conflicts_with.join(', ')}</div>`
      : '';

    return `
      <div class="program-step ${isDone ? 'program-step-done' : ''} ${isSkipped ? 'program-step-skipped' : ''}"
           style="border-left:3px solid ${color}">
        <div style="display:flex;align-items:flex-start;gap:var(--space-sm)">
          <button class="step-check ${isDone ? 'step-check-done' : ''}"
            onclick="LawnProgramPage._toggleStep(${s.program_id}, ${s.id}, '${s.status}')"
            title="${isDone ? 'Mark undone' : 'Mark complete'}">
            ${isDone ? '✓' : '○'}
          </button>
          <div style="flex:1;min-width:0">
            <div style="display:flex;align-items:center;gap:var(--space-xs);flex-wrap:wrap">
              <span style="font-size:1rem">${s.activity_icon}</span>
              <span style="font-size:var(--fs-sm);font-weight:var(--fw-medium);${isDone ? 'text-decoration:line-through;color:var(--text-muted)' : ''}">${s.product_name || s.activity_type}</span>
              <span class="badge" style="background:${pColor}15;color:${pColor};font-size:var(--fs-xs)">${s.priority}</span>
              ${s.week_of_month ? `<span class="text-muted" style="font-size:var(--fs-xs)">Week ${s.week_of_month}</span>` : ''}
            </div>
            ${s.application_rate ? `<div class="text-muted" style="font-size:var(--fs-xs)">${s.application_rate}</div>` : ''}
            ${s.notes ? `<div class="text-muted" style="font-size:var(--fs-xs);margin-top:2px">${s.notes.substring(0, 100)}${s.notes.length > 100 ? '…' : ''}</div>` : ''}
            ${conflictsHtml}
            ${isDone && s.completed_date ? `<div style="font-size:var(--fs-xs);color:var(--color-success)">✓ Done ${Fmt.relativeDate(s.completed_date)}</div>` : ''}
          </div>
          <div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px">
            <span style="font-size:var(--fs-xs);color:${color}">${sourceLabels[s.source] || s.source}</span>
            <button class="btn btn-ghost" style="padding:2px 6px;font-size:var(--fs-xs)"
              onclick="LawnProgramPage._deleteStep(${s.program_id}, ${s.id})">✕</button>
          </div>
        </div>
      </div>`;
  },

  async _toggleStep(programId, stepId, currentStatus) {
    try {
      if (currentStatus === 'done') {
        await API.updateProgramStep(programId, stepId, { status: 'pending', completed_date: null });
      } else {
        await API.completeProgramStep(programId, stepId);
      }
      await this._load();
    } catch (e) { Toast.error(e.message); }
  },

  async _generateProgram() {
    const btn = document.getElementById('generateBtn');
    btn.disabled = true;
    btn.textContent = 'Generating...';

    try {
      const program = await API.generateProgram();
      this.program = program;
      Toast.success(`Program generated: ${program.total_steps} steps across ${program.by_month.length} months`);
      this._renderProgram(program, document.getElementById('programContent'));
    } catch (e) { Toast.error(e.message); }

    btn.disabled = false;
    btn.textContent = '⚡ Generate';
  },

  _addManualStep() {
    if (!this.program) { Toast.warning('Generate a program first'); return; }

    const monthOpts = Array.from({length: 12}, (_, i) =>
      `<option value="${i + 1}" ${i + 1 === new Date().getMonth() + 1 ? 'selected' : ''}>${['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][i]}</option>`
    ).join('');

    Modal.show('Add Step', `
      <div style="display:flex;flex-direction:column;gap:var(--space-md)">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--space-sm)">
          <div class="form-group">
            <label class="form-label">Month</label>
            <select class="form-select" id="manMonth">${monthOpts}</select>
          </div>
          <div class="form-group">
            <label class="form-label">Week (optional)</label>
            <select class="form-select" id="manWeek">
              <option value="">Any time</option>
              <option value="1">Week 1</option>
              <option value="2">Week 2</option>
              <option value="3">Week 3</option>
              <option value="4">Week 4</option>
            </select>
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Activity Type</label>
          <select class="form-select" id="manType">
            <option value="fertilize">🌿 Fertilize</option>
            <option value="weed_control">🌾 Weed Control</option>
            <option value="pre_emergent">🛡️ Pre-Emergent</option>
            <option value="fungicide">🍄 Fungicide</option>
            <option value="pest_control">🪲 Pest Control</option>
            <option value="overseed">🌱 Overseed</option>
            <option value="aerate">🔵 Aerate</option>
            <option value="lime">🪨 Lime</option>
            <option value="other">📋 Other</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Product Name</label>
          <input type="text" class="form-input" id="manProduct" placeholder="e.g. Scotts Turf Builder">
        </div>
        <div class="form-group">
          <label class="form-label">Application Rate (optional)</label>
          <input type="text" class="form-input" id="manRate" placeholder="e.g. 2 lbs per 1000 sqft">
        </div>
        <div class="form-group">
          <label class="form-label">Notes (optional)</label>
          <textarea class="form-textarea" id="manNotes" rows="2"></textarea>
        </div>
        <div class="form-group">
          <label class="form-label">Priority</label>
          <select class="form-select" id="manPriority">
            <option value="high">High</option>
            <option value="medium" selected>Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
        <button class="btn btn-primary btn-block" onclick="LawnProgramPage._saveManualStep()">Add Step</button>
      </div>
    `);
  },

  async _saveManualStep() {
    if (!this.program) return;
    const data = {
      month: parseInt(document.getElementById('manMonth').value),
      week_of_month: parseInt(document.getElementById('manWeek').value) || null,
      activity_type: document.getElementById('manType').value,
      product_name: document.getElementById('manProduct').value.trim() || null,
      application_rate: document.getElementById('manRate').value.trim() || null,
      notes: document.getElementById('manNotes').value.trim() || null,
      priority: document.getElementById('manPriority').value,
    };
    try {
      await API.addProgramStep(this.program.id, data);
      Modal.close();
      Toast.success('Step added');
      await this._load();
    } catch (e) { Toast.error(e.message); }
  },

  async _deleteStep(programId, stepId) {
    if (!await Modal.confirm({ title: 'Remove Step?', message: 'This step will be removed from the program.', confirmText: 'Remove Step', variant: 'danger' })) return;
    try {
      await API.deleteProgramStep(programId, stepId);
      await this._load();
    } catch (e) { Toast.error(e.message); }
  },
};
