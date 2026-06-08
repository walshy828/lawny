/** Fertilizer Programs Page — 3 views: picker, active dashboard, custom builder */
const FertilizerPage = {
  async render(container) {
    container.innerHTML = '<div class="loading-center"><div class="spinner"></div></div>';

    try {
      const active = await API.fertilizerActive();
      if (active) {
        await this._renderActiveDashboard(container, active);
      } else {
        await this._renderProgramPicker(container);
      }
    } catch (e) {
      await this._renderProgramPicker(container);
    }
  },

  // ── View 1: Program Picker ─────────────────────────────
  async _renderProgramPicker(container) {
    const programs = await API.fertilizerPrograms();

    container.innerHTML = `
      <div class="section-header anim-fade-in">
        <h1 class="section-title">🧪 Fertilizer Programs</h1>
      </div>

      <p class="text-secondary anim-fade-in-up" style="font-size:var(--fs-sm);margin-bottom:var(--space-lg)">
        Choose a proven fertilizer program from top brands, or create your own custom schedule.
      </p>

      <div id="programList" class="anim-fade-in-up anim-delay-1">
        ${programs.length === 0 ? '<div class="text-muted text-center" style="padding:var(--space-xl)">No programs available. Tap refresh to load catalog.</div>' :
          programs.map(p => `
            <div class="program-card ${p.recommended ? 'recommended' : ''}" data-id="${p.id}">
              ${p.recommended ? '<div class="badge-recommended">✓ Recommended for your grass</div>' : ''}
              <div class="program-brand">${p.brand || 'Custom'}</div>
              <div class="program-name">${p.name}</div>
              <div class="program-desc">${p.description || ''}</div>
              <div class="program-meta">
                <span class="badge badge-info">${p.step_count} Steps</span>
                <span class="badge badge-accent">${this._seasonLabel(p.grass_season)}</span>
                ${p.soil_type && p.soil_type !== 'any' ? `<span class="badge">${p.soil_type} soil</span>` : ''}
                ${p.is_custom ? '<span class="badge badge-warning">Custom</span>' : ''}
              </div>
              <div style="display:flex;gap:var(--space-sm);margin-top:var(--space-md)">
                <button class="btn btn-secondary btn-sm" onclick="event.stopPropagation();FertilizerPage._viewDetails(${p.id})">View Details</button>
                <button class="btn btn-primary btn-sm" onclick="event.stopPropagation();FertilizerPage._activate(${p.id},'${p.name.replace(/'/g,"\\'")}')">Activate →</button>
                ${p.is_custom ? `<button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();FertilizerPage._deleteCustom(${p.id},'${p.name.replace(/'/g,"\\'")}')">🗑️</button>` : ''}
              </div>
            </div>
          `).join('')}
      </div>

      <div class="anim-fade-in-up anim-delay-2" style="display:flex;flex-direction:column;gap:var(--space-sm);margin-top:var(--space-lg)">
        <div style="display:flex;gap:var(--space-sm)">
          <button class="btn btn-secondary btn-block" id="createCustomBtn">✏️ Create Custom Program</button>
          <button class="btn btn-ghost btn-block" id="refreshCatalogBtn">↻ Refresh Catalog</button>
        </div>
        <button class="btn btn-accent btn-block" id="aiRefreshBtn">✨ AI Refresh for ${new Date().getFullYear()} Season</button>
      </div>
    `;

    document.getElementById('createCustomBtn').addEventListener('click', () => this._showCustomBuilder());
    document.getElementById('refreshCatalogBtn').addEventListener('click', () => this._refreshCatalog(container));
    document.getElementById('aiRefreshBtn').addEventListener('click', () => this._aiRefreshPrograms(container));
  },

  // ── View 2: Active Program Dashboard ───────────────────
  async _renderActiveDashboard(container, active) {
    const { program, steps, completed, total, progress_pct, year } = active;
    let shopping = { items: [], total_sqft: 0 };
    try { shopping = await API.fertilizerShoppingList(); } catch (e) {}

    const currentMonth = new Date().getMonth() + 1;

    container.innerHTML = `
      <div class="section-header anim-fade-in">
        <h1 class="section-title">🧪 ${program.name}</h1>
        <button class="btn btn-ghost btn-sm" id="changeProgramBtn">Change</button>
      </div>

      <div class="card anim-fade-in-up anim-delay-1">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:var(--space-xs)">
          <span class="text-secondary" style="font-size:var(--fs-sm)">${completed}/${total} steps completed</span>
          <span style="font-weight:var(--fw-bold);color:var(--color-accent)">${progress_pct}%</span>
        </div>
        <div class="fert-progress">
          <div class="fert-progress-fill" style="width:${progress_pct}%"></div>
        </div>
        <div class="text-muted" style="font-size:var(--fs-xs)">${year} Season${program.brand ? ` · ${program.brand}` : ''}</div>
      </div>

      <div class="section-header"><span class="section-title">Steps</span></div>
      <div id="stepList" class="anim-fade-in-up anim-delay-2">
        ${steps.map(s => {
          let statusClass = `step-${s.status}`;
          let statusIcon = s.status === 'done' ? '✅' : s.status === 'skipped' ? '⏭️' :
            s.status === 'current' ? '🔵' : s.status === 'overdue' ? '🔴' : '⬜';

          return `
            <div class="step-card ${statusClass}">
              <div class="step-number">${s.status === 'done' ? '✓' : s.step_number}</div>
              <div class="step-info">
                <div class="step-product">${s.icon_emoji || '🧪'} ${s.product_name}</div>
                <div class="step-season">${s.season_label} · ${s.month_label}</div>
                ${s.status === 'done' && s.applied_date ? `<div class="text-muted" style="font-size:var(--fs-xs);margin-top:2px">Applied ${Fmt.date(s.applied_date)}${s.product_used ? ` · ${s.product_used}` : ''}</div>` : ''}
                ${s.purpose ? `<div class="step-purpose">${s.purpose}</div>` : ''}
                ${s.status === 'current' || s.status === 'overdue' ? `
                  <div class="step-actions">
                    <button class="btn btn-primary btn-sm" onclick="FertilizerPage._applyStep(${s.id},'done')">✓ Mark Applied</button>
                    <button class="btn btn-ghost btn-sm" onclick="FertilizerPage._applyStep(${s.id},'skipped')">Skip</button>
                    <button class="btn btn-ghost btn-sm" onclick="FertilizerPage._showStepDetail(${JSON.stringify(s).replace(/"/g, '&quot;')})">ℹ️</button>
                  </div>
                ` : ''}
              </div>
            </div>`;
        }).join('')}
      </div>

      ${shopping.items.length > 0 ? `
        <div class="section-header mt-xl"><span class="section-title">🛒 Shopping List</span></div>
        <div class="card anim-fade-in-up anim-delay-3">
          <div class="text-muted" style="font-size:var(--fs-xs);margin-bottom:var(--space-md)">
            Based on your lawn: ${Fmt.sqft(shopping.total_sqft)}
          </div>
          ${shopping.items.map(item => `
            <div class="shopping-item">
              <div class="bag-count">${item.bags_needed}×</div>
              <div class="shopping-product">
                <div class="shopping-product-name">${item.product_name}</div>
                <div class="shopping-product-meta">
                  Step ${item.step_number} · ${item.season_label} (${item.month_label})
                  ${item.bag_weight ? ` · ${item.bag_weight}/bag` : ''}
                  ${item.coverage_per_bag ? ` · covers ${Fmt.sqft(item.coverage_per_bag)}/bag` : ''}
                </div>
              </div>
            </div>
          `).join('')}
        </div>
      ` : ''}
    `;

    document.getElementById('changeProgramBtn').addEventListener('click', async () => {
      if (await Modal.confirm({ title: 'Change Program?', message: 'Your application history will be preserved.', confirmText: 'Deactivate', variant: 'danger' })) {
        await API.fertilizerDeactivate();
        Toast.success('Program deactivated');
        await this.render(container);
      }
    });
  },

  // ── Actions ────────────────────────────────────────────
  async _viewDetails(programId) {
    try {
      const p = await API.fertilizerProgramDetail(programId);
      const stepsHtml = p.steps.map(s => `
        <div style="padding:var(--space-md) 0;border-bottom:1px solid var(--border-subtle)">
          <div style="display:flex;align-items:center;gap:var(--space-sm);margin-bottom:4px">
            <span style="font-weight:var(--fw-bold);color:var(--text-accent)">Step ${s.step_number}</span>
            <span>${s.icon_emoji || '🧪'}</span>
            <span class="badge badge-info" style="font-size:10px">${s.season_label}</span>
          </div>
          <div style="font-weight:var(--fw-semibold);font-size:var(--fs-sm)">${s.product_name}</div>
          <div class="text-muted" style="font-size:var(--fs-xs);margin-top:2px">
            📅 ${s.month_label} · ${s.application_rate_per_1k ? `📏 ${s.application_rate_per_1k}/1,000 sqft` : ''}
            ${s.coverage_sqft_per_bag ? ` · 📦 ${Fmt.sqft(s.coverage_sqft_per_bag)}/bag` : ''}
          </div>
          ${s.purpose ? `<div class="text-secondary" style="font-size:var(--fs-xs);margin-top:4px">${s.purpose}</div>` : ''}
          ${s.tips ? `<div style="font-size:var(--fs-xs);margin-top:4px;color:var(--color-accent)">💡 ${s.tips}</div>` : ''}
        </div>
      `).join('');

      Modal.show(`${p.brand || 'Custom'}: ${p.name}`, `
        <div class="text-secondary" style="font-size:var(--fs-sm);margin-bottom:var(--space-lg)">${p.description || ''}</div>
        <div class="program-meta" style="margin-bottom:var(--space-lg)">
          <span class="badge badge-info">${p.step_count} Steps</span>
          <span class="badge badge-accent">${this._seasonLabel(p.grass_season)}</span>
          ${p.soil_type && p.soil_type !== 'any' ? `<span class="badge">${p.soil_type} soil</span>` : ''}
        </div>
        ${stepsHtml}
      `);
    } catch (e) { Toast.error(e.message); }
  },

  async _activate(programId, name) {
    if (!await Modal.confirm({ title: `Activate "${name}"?`, message: 'This will set up step tracking for the current year.', confirmText: 'Activate Program' })) return;
    try {
      await API.fertilizerActivate(programId);
      Toast.success(`${name} activated!`);
      MyLawnPage.reload('fertilizer');
    } catch (e) { Toast.error(e.message); }
  },

  async _applyStep(stepId, status) {
    try {
      await API.fertilizerApply(stepId, { status });
      Toast.success(status === 'done' ? 'Step marked as applied!' : 'Step skipped');
      MyLawnPage.reload('fertilizer');
    } catch (e) { Toast.error(e.message); }
  },

  _showStepDetail(step) {
    Modal.show(`${step.icon_emoji || '🧪'} Step ${step.step_number}`, `
      <div style="font-size:var(--fs-lg);font-weight:var(--fw-bold);margin-bottom:var(--space-md)">${step.product_name}</div>
      <div class="badge badge-info" style="margin-bottom:var(--space-md)">${step.season_label} · ${step.month_label}</div>
      ${step.product_description ? `<p class="text-secondary" style="font-size:var(--fs-sm)">${step.product_description}</p>` : ''}
      ${step.purpose ? `<p class="text-secondary" style="font-size:var(--fs-sm)"><strong>Purpose:</strong> ${step.purpose}</p>` : ''}
      ${step.application_rate_per_1k ? `<p style="font-size:var(--fs-sm)">📏 <strong>Rate:</strong> ${step.application_rate_per_1k} per 1,000 sqft</p>` : ''}
      ${step.coverage_sqft_per_bag ? `<p style="font-size:var(--fs-sm)">📦 <strong>Coverage:</strong> ${Fmt.sqft(step.coverage_sqft_per_bag)} per bag ${step.bag_weight ? `(${step.bag_weight})` : ''}</p>` : ''}
      ${step.tips ? `<div class="card" style="background:rgba(82,183,136,0.08);border-color:var(--color-accent);margin-top:var(--space-md)"><div style="font-size:var(--fs-sm)">💡 <strong>Pro Tip:</strong> ${step.tips}</div></div>` : ''}
    `);
  },

  async _refreshCatalog(container) {
    try {
      const result = await API.fertilizerRefresh();
      Toast.success(result.message);
      await this._renderProgramPicker(container);
    } catch (e) { Toast.error(e.message); }
  },

  async _aiRefreshPrograms(container) {
    const btn = document.getElementById('aiRefreshBtn');
    if (btn) { btn.disabled = true; btn.textContent = '✨ Refreshing with AI...'; }
    try {
      const result = await API.fertilizerAiRefresh();
      Toast.success(result.message || 'AI refresh complete!');
      await this._renderProgramPicker(container);
    } catch (e) {
      Toast.error(e.message || 'AI refresh failed — check AI provider in Settings');
      if (btn) { btn.disabled = false; btn.textContent = `✨ AI Refresh for ${new Date().getFullYear()} Season`; }
    }
  },

  async _deleteCustom(id, name) {
    if (!await Modal.confirm({ title: `Delete "${name}"?`, message: 'This custom program will be permanently deleted.', confirmText: 'Delete Program', variant: 'danger' })) return;
    try {
      await API.fertilizerDeleteCustom(id);
      Toast.success('Custom program deleted');
      MyLawnPage.reload('fertilizer');
    } catch (e) { Toast.error(e.message); }
  },

  // ── Custom Program Builder ─────────────────────────────
  _showCustomBuilder() {
    Modal.show('✏️ Create Custom Program', `
      <div class="form-group">
        <label class="form-label">Program Name</label>
        <input type="text" class="form-input" id="customName" placeholder="e.g., My Organic Mix">
      </div>
      <div class="form-group">
        <label class="form-label">Description (optional)</label>
        <textarea class="form-textarea" id="customDesc" placeholder="What products and schedule..."></textarea>
      </div>
      <div class="form-group">
        <label class="form-label">Grass Season</label>
        <select class="form-select" id="customSeason">
          <option value="any">Any</option>
          <option value="cool">Cool Season</option>
          <option value="warm">Warm Season</option>
          <option value="transition">Transition Zone</option>
        </select>
      </div>
      <button class="btn btn-primary btn-block" id="createCustomSubmit">Create Program</button>
      <p class="text-muted" style="font-size:var(--fs-xs);margin-top:var(--space-sm);text-align:center">After creating, you can add steps from the program detail view.</p>
    `, {
      onMount: () => {
        document.getElementById('createCustomSubmit').addEventListener('click', async () => {
          const name = document.getElementById('customName').value.trim();
          if (!name) { Toast.warning('Enter a program name'); return; }
          try {
            const program = await API.fertilizerCreateCustom({
              name,
              description: document.getElementById('customDesc').value || null,
              grass_season: document.getElementById('customSeason').value,
            });
            Modal.close();
            Toast.success(`"${name}" created! Now add steps.`);
            // Show step adder
            this._showAddStep(program.id, name);
          } catch (e) { Toast.error(e.message); }
        });
      }
    });
  },

  _showAddStep(programId, programName) {
    const seasons = [
      { value: 'early_spring', label: 'Early Spring' },
      { value: 'late_spring', label: 'Late Spring' },
      { value: 'summer', label: 'Summer' },
      { value: 'fall', label: 'Fall' },
    ];

    Modal.show(`Add Step to ${programName}`, `
      <div class="form-group">
        <label class="form-label">Step Number</label>
        <input type="number" class="form-input" id="stepNum" value="1" min="1">
      </div>
      <div class="form-group">
        <label class="form-label">Product Name</label>
        <input type="text" class="form-input" id="stepProduct" placeholder="e.g., Milorganite 6-4-0">
      </div>
      <div class="form-group">
        <label class="form-label">Season</label>
        <select class="form-select" id="stepSeason">
          ${seasons.map(s => `<option value="${s.value}">${s.label}</option>`).join('')}
        </select>
      </div>
      <div style="display:flex;gap:var(--space-sm)">
        <div class="form-group" style="flex:1">
          <label class="form-label">Month Start</label>
          <input type="number" class="form-input" id="stepMonthStart" min="1" max="12" placeholder="3">
        </div>
        <div class="form-group" style="flex:1">
          <label class="form-label">Month End</label>
          <input type="number" class="form-input" id="stepMonthEnd" min="1" max="12" placeholder="4">
        </div>
      </div>
      <div class="form-group">
        <label class="form-label">Coverage per Bag (sqft)</label>
        <input type="number" class="form-input" id="stepCoverage" placeholder="5000">
      </div>
      <div class="form-group">
        <label class="form-label">Purpose / Notes (optional)</label>
        <textarea class="form-textarea" id="stepPurpose" placeholder="What this step does..."></textarea>
      </div>
      <div style="display:flex;gap:var(--space-sm)">
        <button class="btn btn-primary btn-block" id="addStepSubmit">Add Step</button>
        <button class="btn btn-secondary btn-block" id="addStepDone">Done</button>
      </div>
    `, {
      onMount: () => {
        document.getElementById('addStepSubmit').addEventListener('click', async () => {
          const product = document.getElementById('stepProduct').value.trim();
          if (!product) { Toast.warning('Enter a product name'); return; }
          try {
            await API.fertilizerAddStep(programId, {
              step_number: parseInt(document.getElementById('stepNum').value) || 1,
              product_name: product,
              season: document.getElementById('stepSeason').value,
              month_start: parseInt(document.getElementById('stepMonthStart').value) || null,
              month_end: parseInt(document.getElementById('stepMonthEnd').value) || null,
              coverage_sqft_per_bag: parseInt(document.getElementById('stepCoverage').value) || null,
              purpose: document.getElementById('stepPurpose').value || null,
            });
            Toast.success('Step added!');
            // Increment step number for next
            const numInput = document.getElementById('stepNum');
            numInput.value = parseInt(numInput.value) + 1;
            document.getElementById('stepProduct').value = '';
            document.getElementById('stepPurpose').value = '';
          } catch (e) { Toast.error(e.message); }
        });
        document.getElementById('addStepDone').addEventListener('click', () => {
          Modal.close();
          this.render(document.getElementById('pageContent'));
        });
      }
    });
  },

  // ── Helpers ────────────────────────────────────────────
  _seasonLabel(season) {
    const labels = { cool: '❄️ Cool Season', warm: '☀️ Warm Season', transition: '🔄 Transition', any: '🌿 All Seasons' };
    return labels[season] || season || 'Any';
  },
};
