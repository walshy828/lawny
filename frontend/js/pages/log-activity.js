/** Log Activity Page */
const LogActivityPage = {
  selectedType: null,
  healthScore: 5,
  waterInputMode: 'inches',
  lawnSqft: 0,
  zones: [],
  photoFile: null,

  render(container) {
    const types = Object.entries(Fmt.ACTIVITY_META).map(([key, meta]) =>
      `<button class="type-btn" data-type="${key}">
        <span class="type-btn-icon">${meta.icon}</span>
        <span>${meta.label}</span>
      </button>`
    ).join('');

    container.innerHTML = `
      <div class="section-header anim-fade-in">
        <h1 class="section-title">Log Activity</h1>
      </div>

      <div class="anim-fade-in-up anim-delay-1">
        <label class="form-label">Activity Type</label>
        <div class="type-grid" id="typeGrid">${types}</div>
      </div>

      <div class="form-group mt-xl anim-fade-in-up anim-delay-2">
        <label class="form-label">Zone (optional)</label>
        <select class="form-select" id="zoneSelect">
          <option value="">Whole Lawn</option>
        </select>
      </div>

      <!-- Water Amount Section (hidden by default) -->
      <div class="water-input-section" id="waterInputSection" style="display:none">
        <div class="card" style="border-color:var(--color-info);border-left:3px solid var(--color-info)">
          <div class="card-header" style="padding-bottom:var(--space-sm)">
            <span class="card-title">💧 Water Amount</span>
          </div>

          <!-- Input Mode Toggle -->
          <div class="water-mode-toggle" id="waterModeToggle">
            <button class="water-mode-btn active" data-mode="inches">Inches</button>
            <button class="water-mode-btn" data-mode="gallons">Gallons + Area</button>
          </div>

          <!-- Inches Mode -->
          <div class="water-mode-panel" id="inchesPanel">
            <label class="form-label" style="font-size:var(--fs-xs);color:var(--text-muted)">Water applied (inches)</label>
            <input type="number" class="form-input" id="waterInches" step="0.05" min="0" max="5" placeholder="0.25" value="">
            <div class="text-muted" style="font-size:var(--fs-xs);margin-top:var(--space-xs)">
              Tip: 1 inch = about 0.62 gallons per sqft. A typical sprinkler session applies 0.15–0.30 inches.
            </div>
          </div>

          <!-- Gallons Mode -->
          <div class="water-mode-panel" id="gallonsPanel" style="display:none">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--space-md)">
              <div>
                <label class="form-label" style="font-size:var(--fs-xs);color:var(--text-muted)">Gallons applied</label>
                <input type="number" class="form-input" id="waterGallons" step="1" min="0" placeholder="100" value="">
              </div>
              <div>
                <label class="form-label" style="font-size:var(--fs-xs);color:var(--text-muted)">Area (sqft)</label>
                <input type="number" class="form-input" id="waterAreaSqft" step="1" min="1" placeholder="1000" value="">
              </div>
            </div>
            <div class="water-calc-result" id="waterCalcResult" style="margin-top:var(--space-sm)">
              <span class="text-muted" style="font-size:var(--fs-xs)">Calculated: </span>
              <span id="waterCalcInches" style="font-weight:var(--fw-semibold);color:var(--color-accent)">—</span>
              <span class="text-muted" style="font-size:var(--fs-xs)"> inches</span>
            </div>
          </div>
        </div>
      </div>

      <div class="form-group anim-fade-in-up anim-delay-3">
        <label class="form-label">Lawn Health Rating</label>
        <div class="health-slider-container">
          <input type="range" class="health-slider" id="healthSlider" min="1" max="10" value="5">
          <div class="health-labels">
            <span>💀 Dead</span>
            <span id="healthDisplay" style="font-weight:600;color:var(--color-accent)">5 — Average 🟡</span>
            <span>🏆 Lush</span>
          </div>
        </div>
      </div>

      <div class="form-group anim-fade-in-up anim-delay-4">
        <label class="form-label">Date</label>
        <input type="datetime-local" class="form-input" id="activityDate" value="${new Date().toISOString().slice(0, 16)}">
      </div>

      <div class="form-group anim-fade-in-up anim-delay-4">
        <label class="form-label">Notes (optional)</label>
        <textarea class="form-textarea" id="activityNotes" placeholder="Products used, conditions, observations..."></textarea>
      </div>

      <div class="form-group anim-fade-in-up anim-delay-4">
        <label class="form-label">Photo (optional)</label>
        <div class="photo-capture-area" id="photoCaptureArea">
          <input type="file" id="photoInput" accept="image/*" capture="environment" style="display:none">
          <div id="photoPreview" style="display:none">
            <img id="photoPreviewImg" style="max-width:100%;border-radius:var(--radius-md);max-height:200px;display:block;margin:0 auto">
            <button class="btn btn-ghost btn-sm" onclick="LogActivityPage._clearPhoto()" style="margin-top:var(--space-xs);width:100%">Remove Photo</button>
          </div>
          <div id="photoPlaceholder" style="display:flex;gap:var(--space-sm)">
            <button class="btn btn-secondary btn-sm btn-block" onclick="document.getElementById('photoInput').setAttribute('capture','environment');document.getElementById('photoInput').click()">📷 Camera</button>
            <button class="btn btn-secondary btn-sm btn-block" onclick="document.getElementById('photoInput').removeAttribute('capture');document.getElementById('photoInput').click()">🖼️ Gallery</button>
          </div>
        </div>
      </div>

      <button class="btn btn-primary btn-lg btn-block mt-lg anim-fade-in-up anim-delay-5" id="saveActivityBtn" disabled>
        Save Activity
      </button>
    `;

    this.photoFile = null;
    this._loadZones();
    this._bindEvents();
  },

  async _loadZones() {
    try {
      const zones = await API.getZones();
      this.zones = zones;
      const sel = document.getElementById('zoneSelect');
      let totalSqft = 0;
      zones.forEach(z => {
        const opt = document.createElement('option');
        opt.value = z.id;
        opt.textContent = `${z.name} (${Fmt.sqft(z.area_sqft)})`;
        opt.dataset.sqft = z.area_sqft || 0;
        sel.appendChild(opt);
        totalSqft += (z.area_sqft || 0);
      });
      this.lawnSqft = totalSqft;
      // Pre-fill area with total lawn sqft
      const areaInput = document.getElementById('waterAreaSqft');
      if (areaInput && totalSqft > 0) areaInput.value = Math.round(totalSqft);
    } catch (e) { /* zones not yet set up */ }
  },

  _bindEvents() {
    // Type selection
    document.getElementById('typeGrid').addEventListener('click', (e) => {
      const btn = e.target.closest('.type-btn');
      if (!btn) return;
      document.querySelectorAll('.type-btn').forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');
      this.selectedType = btn.dataset.type;
      document.getElementById('saveActivityBtn').disabled = false;

      // Show/hide water input section
      const waterSection = document.getElementById('waterInputSection');
      if (this.selectedType === 'water') {
        waterSection.style.display = 'block';
        waterSection.classList.add('anim-fade-in-up');
      } else {
        waterSection.style.display = 'none';
      }
    });

    // Water input mode toggle
    document.getElementById('waterModeToggle').addEventListener('click', (e) => {
      const btn = e.target.closest('.water-mode-btn');
      if (!btn) return;
      const mode = btn.dataset.mode;
      this.waterInputMode = mode;
      document.querySelectorAll('.water-mode-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('inchesPanel').style.display = mode === 'inches' ? 'block' : 'none';
      document.getElementById('gallonsPanel').style.display = mode === 'gallons' ? 'block' : 'none';
    });

    // Zone change — update area sqft for gallons calc
    document.getElementById('zoneSelect').addEventListener('change', (e) => {
      const sel = e.target;
      const opt = sel.options[sel.selectedIndex];
      const areaInput = document.getElementById('waterAreaSqft');
      if (sel.value && opt.dataset.sqft) {
        areaInput.value = Math.round(parseFloat(opt.dataset.sqft));
      } else {
        areaInput.value = Math.round(this.lawnSqft);
      }
      this._updateGallonsCalc();
    });

    // Gallons / area input — live calculate inches
    ['waterGallons', 'waterAreaSqft'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.addEventListener('input', () => this._updateGallonsCalc());
    });

    // Health slider
    const slider = document.getElementById('healthSlider');
    const display = document.getElementById('healthDisplay');
    slider.addEventListener('input', () => {
      const val = parseInt(slider.value);
      this.healthScore = val;
      display.textContent = `${val} — ${Fmt.healthLabel(val)} ${Fmt.healthEmoji(val)}`;
      display.style.color = Fmt.healthColor(val);
    });

    // Photo input
    document.getElementById('photoInput').addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (!file) return;
      this.photoFile = file;
      const reader = new FileReader();
      reader.onload = (ev) => {
        document.getElementById('photoPreviewImg').src = ev.target.result;
        document.getElementById('photoPreview').style.display = 'block';
        document.getElementById('photoPlaceholder').style.display = 'none';
      };
      reader.readAsDataURL(file);
    });

    // Save
    document.getElementById('saveActivityBtn').addEventListener('click', () => this._save());
  },

  _updateGallonsCalc() {
    const gallons = parseFloat(document.getElementById('waterGallons').value) || 0;
    const area = parseFloat(document.getElementById('waterAreaSqft').value) || 0;
    const resultEl = document.getElementById('waterCalcInches');

    if (gallons > 0 && area > 0) {
      // gallons to cubic inches / area in square inches
      // 1 gallon = 231 cubic inches, 1 sqft = 144 sq inches
      const inches = (gallons * 231) / (area * 144);
      resultEl.textContent = inches.toFixed(3);
      resultEl.style.color = 'var(--color-accent)';
    } else {
      resultEl.textContent = '—';
    }
  },

  _getWaterAmountInches() {
    if (this.selectedType !== 'water') return null;

    if (this.waterInputMode === 'inches') {
      const val = parseFloat(document.getElementById('waterInches').value);
      return val > 0 ? val : null;
    } else {
      const gallons = parseFloat(document.getElementById('waterGallons').value) || 0;
      const area = parseFloat(document.getElementById('waterAreaSqft').value) || 0;
      if (gallons > 0 && area > 0) {
        return parseFloat(((gallons * 231) / (area * 144)).toFixed(3));
      }
      return null;
    }
  },

  _clearPhoto() {
    this.photoFile = null;
    document.getElementById('photoPreview').style.display = 'none';
    document.getElementById('photoPlaceholder').style.display = 'flex';
    document.getElementById('photoInput').value = '';
  },

  async _save() {
    if (!this.selectedType) { Toast.warning('Select an activity type'); return; }

    const btn = document.getElementById('saveActivityBtn');
    btn.disabled = true;
    btn.textContent = 'Saving...';

    try {
      const data = {
        activity_type: this.selectedType,
        health_score: this.healthScore,
        date: document.getElementById('activityDate').value,
        notes: document.getElementById('activityNotes').value || null,
        zone_id: document.getElementById('zoneSelect').value || null,
        water_amount_inches: this._getWaterAmountInches(),
      };
      if (data.zone_id) data.zone_id = parseInt(data.zone_id);

      if (this.photoFile) {
        const formData = new FormData();
        Object.entries(data).forEach(([k, v]) => { if (v != null) formData.append(k, v); });
        formData.append('photo', this.photoFile);
        const resp = await fetch('/api/activities', { method: 'POST', body: formData });
        if (!resp.ok) { const e = await resp.json().catch(() => ({})); throw new Error(e.detail || 'Upload failed'); }
      } else {
        await API.createActivity(data);
      }
      Toast.success(`${Fmt.activityLabel(this.selectedType)} logged!`);
      App.navigate('dashboard');
    } catch (e) {
      Toast.error(e.message);
      btn.disabled = false;
      btn.textContent = 'Save Activity';
    }
  },
};
