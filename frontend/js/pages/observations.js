/** Observations Page — log and track what you see in your lawn */
const ObservationsPage = {
  zones: [],
  obsTypes: [],

  async render(container) {
    container.innerHTML = `
      <div class="section-header anim-fade-in">
        <h1 class="section-title">👁️ Observations</h1>
        <button class="btn btn-primary btn-sm" id="addObsBtn">+ Log</button>
      </div>
      <div class="obs-filter-tabs anim-fade-in-up" id="obsFilterTabs">
        <button class="obs-tab active" data-status="active">Active</button>
        <button class="obs-tab" data-status="monitoring">Monitoring</button>
        <button class="obs-tab" data-status="resolved">Resolved</button>
        <button class="obs-tab" data-status="">All</button>
      </div>
      <div id="obsContent" class="anim-fade-in-up">
        <div class="loading-center"><div class="spinner"></div></div>
      </div>`;

    try {
      [this.zones, this.obsTypes] = await Promise.all([API.getZones(), API.getObservationTypes()]);
    } catch (e) { this.zones = []; this.obsTypes = []; }

    document.getElementById('addObsBtn').addEventListener('click', () => this._showAddForm());
    document.getElementById('obsFilterTabs').addEventListener('click', (e) => {
      const btn = e.target.closest('.obs-tab');
      if (!btn) return;
      document.querySelectorAll('.obs-tab').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      this._loadList(btn.dataset.status);
    });

    await this._loadList('active');
  },

  async _loadList(status = 'active') {
    const el = document.getElementById('obsContent');
    el.innerHTML = `<div class="loading-center"><div class="spinner"></div></div>`;
    try {
      const obs = await API.getObservations({ status });
      if (!obs.length) {
        el.innerHTML = `
          <div class="card" style="text-align:center;padding:var(--space-2xl)">
            <div style="font-size:2.5rem;margin-bottom:var(--space-sm)">👁️</div>
            <div style="font-weight:var(--fw-semibold);margin-bottom:var(--space-sm)">${status ? `No ${status} observations` : 'No observations logged'}</div>
            <p class="text-muted" style="font-size:var(--fs-sm)">Log what you see — weeds, bare spots, discoloration — and get AI-powered remediation plans.</p>
          </div>`;
        return;
      }
      el.innerHTML = obs.map(o => this._renderObsCard(o)).join('');
    } catch (e) {
      el.innerHTML = `<div class="text-muted">Error: ${e.message}</div>`;
    }
  },

  _renderObsCard(o) {
    const sevColors = { low: '#20C997', moderate: '#FAB005', severe: '#FA5252' };
    const sevColor = sevColors[o.severity] || 'var(--text-muted)';
    const statusBadge = o.status === 'resolved'
      ? `<span class="badge badge-success" style="font-size:var(--fs-xs)">✓ Resolved</span>`
      : o.status === 'monitoring'
      ? `<span class="badge badge-info" style="font-size:var(--fs-xs)">👁 Monitoring</span>`
      : `<span class="badge badge-warning" style="font-size:var(--fs-xs)">⚠ Active</span>`;

    return `
      <div class="card obs-card" onclick="ObservationsPage._viewObs(${o.id})">
        <div class="card-header">
          <div style="display:flex;align-items:center;gap:var(--space-sm)">
            <span style="font-size:1.3rem">${o.type_icon}</span>
            <div>
              <div style="font-weight:var(--fw-semibold)">${o.type_label}</div>
              <div class="text-muted" style="font-size:var(--fs-xs)">${Fmt.relativeDate(o.date)}${o.zone_name ? ` · ${o.zone_name}` : ''}</div>
            </div>
          </div>
          <div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px">
            ${statusBadge}
            ${o.severity ? `<span style="font-size:var(--fs-xs);color:${sevColor};font-weight:var(--fw-semibold)">${o.severity.charAt(0).toUpperCase() + o.severity.slice(1)}</span>` : ''}
          </div>
        </div>
        ${o.coverage_pct !== null && o.coverage_pct !== undefined ? `
          <div style="margin-top:var(--space-sm)">
            <div style="display:flex;justify-content:space-between;font-size:var(--fs-xs);color:var(--text-muted);margin-bottom:4px">
              <span>Coverage</span><span>${o.coverage_pct}%</span>
            </div>
            <div style="background:var(--bg-surface-2);border-radius:99px;height:6px">
              <div style="background:${sevColor};border-radius:99px;height:6px;width:${o.coverage_pct}%;transition:width 0.5s ease"></div>
            </div>
          </div>` : ''}
        ${o.description ? `<div class="text-muted" style="font-size:var(--fs-xs);margin-top:var(--space-sm)">${o.description.substring(0, 80)}</div>` : ''}
        <div style="display:flex;gap:var(--space-sm);margin-top:var(--space-md)">
          <button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();ObservationsPage._askAI(${o.id}, '${o.type_label}')">🤖 Ask AI</button>
          ${o.status !== 'resolved' ? `<button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();ObservationsPage._resolveObs(${o.id})">✓ Resolve</button>` : ''}
        </div>
      </div>`;
  },

  _showAddForm(prefillType = null) {
    let zoneOptions = '<option value="">Whole Lawn</option>';
    this.zones.forEach(z => { zoneOptions += `<option value="${z.id}">${z.name}</option>`; });

    const typeButtons = (this.obsTypes || []).map(t =>
      `<button class="obs-type-btn${prefillType === t.value ? ' selected' : ''}" data-value="${t.value}">
        <span>${t.icon}</span><span style="font-size:var(--fs-xs)">${t.label}</span>
      </button>`
    ).join('');

    Modal.show('Log Observation', `
      <div style="display:flex;flex-direction:column;gap:var(--space-md)">
        <div class="form-group">
          <label class="form-label">What do you see?</label>
          <div class="obs-type-grid" id="obsTypeGrid">${typeButtons}</div>
          <input type="hidden" id="obsTypeVal" value="${prefillType || ''}">
        </div>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--space-sm)">
          <div class="form-group">
            <label class="form-label">Severity</label>
            <select class="form-select" id="obsSeverity">
              <option value="">Unknown</option>
              <option value="low">Low — minor issue</option>
              <option value="moderate">Moderate — spreading</option>
              <option value="severe">Severe — widespread</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Coverage %</label>
            <input type="number" class="form-input" id="obsCoverage" min="1" max="100" placeholder="10">
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Zone (optional)</label>
          <select class="form-select" id="obsZone">${zoneOptions}</select>
        </div>

        <div class="form-group">
          <label class="form-label">Description (optional)</label>
          <textarea class="form-textarea" id="obsDesc" placeholder="Where in the yard? Any other details..."></textarea>
        </div>

        <button class="btn btn-primary btn-block" onclick="ObservationsPage._saveObs()">Save Observation</button>
      </div>
    `);

    // Bind type grid
    setTimeout(() => {
      document.getElementById('obsTypeGrid')?.addEventListener('click', (e) => {
        const btn = e.target.closest('.obs-type-btn');
        if (!btn) return;
        document.querySelectorAll('.obs-type-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        document.getElementById('obsTypeVal').value = btn.dataset.value;
      });
    }, 50);
  },

  async _saveObs() {
    const obsType = document.getElementById('obsTypeVal').value;
    if (!obsType) { Toast.warning('Select an observation type'); return; }

    const data = {
      observation_type: obsType,
      severity: document.getElementById('obsSeverity').value || null,
      coverage_pct: parseInt(document.getElementById('obsCoverage').value) || null,
      zone_id: document.getElementById('obsZone').value ? parseInt(document.getElementById('obsZone').value) : null,
      description: document.getElementById('obsDesc').value || null,
    };

    try {
      await API.createObservation(data);
      Modal.close();
      Toast.success('Observation logged!');
      await this._loadList('active');
    } catch (e) { Toast.error(e.message); }
  },

  async _viewObs(id) {
    try {
      const o = await API.getObservation(id);
      const sevColors = { low: '#20C997', moderate: '#FAB005', severe: '#FA5252' };
      const sevColor = sevColors[o.severity] || 'var(--text-secondary)';

      Modal.show(`${o.type_icon} ${o.type_label}`, `
        <div>
          <div style="display:flex;gap:var(--space-sm);margin-bottom:var(--space-md)">
            ${o.severity ? `<span class="badge" style="background:${sevColor}20;color:${sevColor}">${o.severity}</span>` : ''}
            ${o.coverage_pct !== null ? `<span class="badge badge-secondary">${o.coverage_pct}% coverage</span>` : ''}
            <span class="badge ${o.status === 'resolved' ? 'badge-success' : o.status === 'monitoring' ? 'badge-info' : 'badge-warning'}">${o.status}</span>
          </div>

          <div class="text-muted" style="font-size:var(--fs-xs);margin-bottom:var(--space-sm)">
            ${Fmt.date(o.date)}${o.zone_name ? ` · ${o.zone_name}` : ''}
          </div>

          ${o.description ? `<p style="font-size:var(--fs-sm);margin-bottom:var(--space-md)">${o.description}</p>` : ''}

          ${o.photo_url ? `<img src="${o.photo_url}" style="width:100%;border-radius:var(--radius-md);margin-bottom:var(--space-md)" alt="Observation photo">` : ''}

          ${o.resolved_date ? `
            <div class="card" style="background:rgba(82,183,136,0.08);border:1px solid rgba(82,183,136,0.3)">
              <div style="font-size:var(--fs-sm);font-weight:var(--fw-semibold)">✓ Resolved ${Fmt.date(o.resolved_date)}</div>
              ${o.resolution_notes ? `<div class="text-muted" style="font-size:var(--fs-xs)">${o.resolution_notes}</div>` : ''}
            </div>` : ''}

          <div style="display:flex;gap:var(--space-sm);flex-wrap:wrap;margin-top:var(--space-lg)">
            <button class="btn btn-primary btn-sm" onclick="Modal.close();ObservationsPage._askAI(${o.id}, '${o.type_label}')">🤖 Ask AI</button>
            ${o.status !== 'resolved' ? `<button class="btn btn-secondary btn-sm" onclick="Modal.close();ObservationsPage._resolveObs(${o.id})">✓ Resolve</button>` : ''}
            <button class="btn btn-danger btn-sm" onclick="ObservationsPage._deleteObs(${o.id})">Delete</button>
          </div>
        </div>
      `);
    } catch (e) { Toast.error(e.message); }
  },

  async _askAI(obsId, label) {
    App.navigate('what-if');
    setTimeout(() => {
      if (window.WhatIfPage) {
        WhatIfPage.prefillObservation(obsId, label);
      }
    }, 200);
  },

  async _resolveObs(id) {
    let notes = '';
    const confirmed = await Modal.confirm({
      title: 'Resolve Observation',
      html: `
        <p class="confirm-message" style="margin-bottom:var(--space-md)">Mark this observation as resolved?</p>
        <label class="form-label">Resolution notes (optional)</label>
        <textarea id="resolveNotesInput" class="form-textarea" placeholder="What did you do to address this?" rows="3" style="margin-bottom:0"></textarea>
      `,
      confirmText: 'Mark Resolved',
      onConfirm: () => { notes = document.getElementById('resolveNotesInput')?.value || ''; },
    });
    if (!confirmed) return;
    try {
      await API.resolveObservation(id, { resolution_notes: notes || null });
      Toast.success('Observation marked as resolved');
      const activeTab = document.querySelector('.obs-tab.active');
      await this._loadList(activeTab?.dataset.status || 'active');
    } catch (e) { Toast.error(e.message); }
  },

  async _deleteObs(id) {
    if (!await Modal.confirm({ title: 'Delete Observation?', message: 'This observation and any linked photos will be permanently deleted.', confirmText: 'Delete', variant: 'danger' })) return;
    try {
      await API.deleteObservation(id);
      Modal.close();
      Toast.success('Observation deleted');
      const activeTab = document.querySelector('.obs-tab.active');
      await this._loadList(activeTab?.dataset.status || 'active');
    } catch (e) { Toast.error(e.message); }
  },
};
