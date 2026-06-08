/** Quick-Log Bottom Sheet — fast activity logging from the + nav button */
const QuickLog = {
  _overlay: null,
  _sheet: null,
  _selectedType: null,
  _zones: [],

  async open() {
    if (document.getElementById('quickLogOverlay')) return;

    let zones = this._zones;
    if (!zones.length) {
      try { zones = this._zones = await API.getZones(); } catch (e) { zones = []; }
    }

    const types = Object.entries(Fmt.ACTIVITY_META).slice(0, 8).map(([key, meta]) => `
      <button class="quick-log-type-btn" data-type="${key}">
        <span class="quick-log-type-icon">${meta.icon}</span>
        <span>${meta.label}</span>
      </button>`).join('');

    const zoneOptions = zones.map(z =>
      `<option value="${z.id}">${z.name}</option>`).join('');

    const overlay = document.createElement('div');
    overlay.className = 'quick-log-overlay';
    overlay.id = 'quickLogOverlay';
    overlay.addEventListener('click', (e) => { if (e.target === overlay) this.close(); });

    const sheet = document.createElement('div');
    sheet.className = 'quick-log-sheet';
    sheet.innerHTML = `
      <div class="quick-log-handle"></div>
      <div class="quick-log-title">Log Activity</div>
      <div class="quick-log-type-grid" id="qlTypeGrid">${types}</div>
      <div id="qlForm" style="display:none">
        <div class="form-group">
          <label class="form-label">Zone</label>
          <select class="form-select" id="qlZone">
            <option value="">Whole Lawn</option>
            ${zoneOptions}
          </select>
        </div>
        <div id="qlWaterSection" style="display:none" class="form-group">
          <label class="form-label">Water Amount (inches)</label>
          <input type="number" class="form-input" id="qlWaterInches" step="0.05" min="0" max="5" placeholder="0.25">
        </div>
        <div class="form-group">
          <label class="form-label">Health Rating <span id="qlHealthVal" style="color:var(--color-accent)">5</span></label>
          <input type="range" class="health-slider" id="qlHealth" min="1" max="10" value="5">
        </div>
        <div class="form-group">
          <label class="form-label">Notes</label>
          <textarea class="form-textarea" id="qlNotes" rows="2" placeholder="Optional notes..."></textarea>
        </div>
        <div style="display:flex;gap:var(--space-sm);margin-top:var(--space-lg)">
          <button class="btn btn-secondary" onclick="QuickLog.close()" style="flex:0 0 auto">Cancel</button>
          <button class="btn btn-primary btn-block" id="qlSaveBtn">Save</button>
        </div>
        <button class="btn btn-ghost btn-block btn-sm" onclick="QuickLog.close();App.navigate('plan')" style="margin-top:var(--space-sm)">
          View Plan →
        </button>
      </div>`;

    document.body.appendChild(overlay);
    document.body.appendChild(sheet);
    this._overlay = overlay;
    this._sheet = sheet;
    this._selectedType = null;

    sheet.querySelector('#qlTypeGrid').addEventListener('click', (e) => {
      const btn = e.target.closest('.quick-log-type-btn');
      if (!btn) return;
      sheet.querySelectorAll('.quick-log-type-btn').forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');
      this._selectedType = btn.dataset.type;
      sheet.querySelector('#qlForm').style.display = 'block';
      sheet.querySelector('#qlWaterSection').style.display = this._selectedType === 'water' ? 'block' : 'none';
    });

    sheet.querySelector('#qlHealth').addEventListener('input', (e) => {
      const val = parseInt(e.target.value);
      sheet.querySelector('#qlHealthVal').textContent = `${val} — ${Fmt.healthLabel(val)}`;
    });

    sheet.querySelector('#qlSaveBtn').addEventListener('click', () => this._save());
  },

  async _save() {
    if (!this._selectedType) { Toast.warning('Pick an activity type'); return; }
    const btn = this._sheet.querySelector('#qlSaveBtn');
    btn.disabled = true;
    btn.textContent = 'Saving...';

    try {
      const waterInches = this._selectedType === 'water'
        ? (parseFloat(this._sheet.querySelector('#qlWaterInches')?.value) || null)
        : null;

      const data = {
        activity_type: this._selectedType,
        health_score: parseInt(this._sheet.querySelector('#qlHealth').value),
        date: new Date().toISOString().slice(0, 16),
        notes: this._sheet.querySelector('#qlNotes').value.trim() || null,
        zone_id: parseInt(this._sheet.querySelector('#qlZone').value) || null,
        water_amount_inches: waterInches,
      };

      await API.createActivity(data);
      Toast.success(`${Fmt.activityLabel(this._selectedType)} logged!`);
      this.close();
      if (App.currentPage === 'dashboard') App.navigate('dashboard');
    } catch (e) {
      Toast.error(e.message);
      btn.disabled = false;
      btn.textContent = 'Save';
    }
  },

  close() {
    this._overlay?.remove();
    this._sheet?.remove();
    this._overlay = null;
    this._sheet = null;
  },
};
