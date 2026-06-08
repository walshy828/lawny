/** Soil Tests Page — log and track soil health over time */
const SoilTestsPage = {
  zones: [],

  async render(container) {
    container.innerHTML = `
      <div class="section-header anim-fade-in">
        <h1 class="section-title">🧫 Soil Tests</h1>
        <button class="btn btn-primary btn-sm" id="addSoilTestBtn">+ Add Test</button>
      </div>
      <div id="soilTestsContent" class="anim-fade-in-up">
        <div class="loading-center"><div class="spinner"></div></div>
      </div>`;

    try {
      this.zones = await API.getZones();
    } catch (e) { this.zones = []; }

    document.getElementById('addSoilTestBtn').addEventListener('click', () => this._showAddForm());
    await this._loadList();
  },

  async _loadList() {
    const el = document.getElementById('soilTestsContent');
    try {
      const tests = await API.getSoilTests();
      if (!tests.length) {
        el.innerHTML = `
          <div class="card" style="text-align:center;padding:var(--space-2xl)">
            <div style="font-size:3rem;margin-bottom:var(--space-md)">🧫</div>
            <div style="font-size:var(--fs-lg);font-weight:var(--fw-semibold);margin-bottom:var(--space-sm)">No Soil Tests Yet</div>
            <p class="text-secondary" style="font-size:var(--fs-sm);margin-bottom:var(--space-lg)">
              Soil tests reveal pH, nutrients, and organic matter — the foundation for targeted lawn care.
              Most local extension offices offer tests for $10-20.
            </p>
            <button class="btn btn-primary" onclick="SoilTestsPage._showAddForm()">Log Your First Test</button>
          </div>`;
        return;
      }

      const trendHtml = tests.length >= 2 ? this._renderTrendChart(tests) : '';
      el.innerHTML = trendHtml + tests.map(t => this._renderTestCard(t)).join('');
    } catch (e) {
      el.innerHTML = `<div class="text-muted">Error loading soil tests: ${e.message}</div>`;
    }
  },

  _renderTrendChart(tests) {
    const sorted = [...tests].sort((a, b) => (a.test_date || '').localeCompare(b.test_date || ''));
    const metrics = [
      { key: 'ph', label: 'pH', idealMin: 6.0, idealMax: 7.0, colorFn: v => v < 6 || v > 7 ? '#FAB005' : '#20C997' },
      { key: 'phosphorus_ppm', label: 'P (ppm)', idealMin: 25, idealMax: 50, colorFn: () => '#339AF0' },
      { key: 'potassium_ppm', label: 'K (ppm)', idealMin: 150, idealMax: 250, colorFn: () => '#CC5DE8' },
    ].filter(m => sorted.some(t => t[m.key] != null));

    if (!metrics.length) return '';

    const charts = metrics.map(m => {
      const pts = sorted.filter(t => t[m.key] != null).map(t => ({ x: t.test_date, y: t[m.key] }));
      if (pts.length < 1) return '';
      const W = 140, H = 40;
      const vals = pts.map(p => p.y);
      const minV = Math.min(...vals) * 0.9, maxV = Math.max(...vals) * 1.1;
      const svgPts = pts.map((p, i) => {
        const x = pts.length < 2 ? W / 2 : (i / (pts.length - 1)) * W;
        const y = H - ((p.y - minV) / (maxV - minV || 1)) * H;
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      });
      const lastColor = m.colorFn(pts[pts.length - 1].y);
      const lastPt = svgPts[svgPts.length - 1].split(',');
      const latest = pts[pts.length - 1].y;
      const latestDate = pts[pts.length - 1].x ? Fmt.date(pts[pts.length - 1].x) : '';
      return `
        <div class="soil-trend-item">
          <div class="soil-trend-label">${m.label}</div>
          <div class="soil-trend-value" style="color:${lastColor}">${typeof latest === 'number' ? (latest % 1 === 0 ? latest : latest.toFixed(1)) : latest}</div>
          <svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" style="overflow:visible">
            ${pts.length > 1 ? `<polyline points="${svgPts.join(' ')}" fill="none" stroke="${lastColor}" stroke-width="1.5" stroke-linecap="round"/>` : ''}
            <circle cx="${lastPt[0]}" cy="${lastPt[1]}" r="3" fill="${lastColor}"/>
          </svg>
          <div class="soil-trend-date">${latestDate}</div>
        </div>`;
    }).join('');

    return `
      <div class="card" style="margin-bottom:var(--space-md)">
        <div class="card-header"><span class="card-title">📈 Trend (${sorted.length} tests)</span></div>
        <div class="soil-trend-row">${charts}</div>
      </div>`;
  },

  _renderTestCard(t) {
    const ph = t.ph;
    const phStatus = ph ? this._phStatus(ph) : null;
    const dateStr = t.test_date ? Fmt.date(t.test_date) : '—';

    const nutrients = [];
    if (t.phosphorus_ppm !== null && t.phosphorus_ppm !== undefined)
      nutrients.push(this._nutrientBadge('P', t.phosphorus_ppm, 25, 50));
    if (t.potassium_ppm !== null && t.potassium_ppm !== undefined)
      nutrients.push(this._nutrientBadge('K', t.potassium_ppm, 150, 250));
    if (t.organic_matter_pct !== null && t.organic_matter_pct !== undefined)
      nutrients.push(this._nutrientBadge('OM', t.organic_matter_pct, 3, 5, '%'));

    return `
      <div class="card soil-test-card" style="cursor:pointer" onclick="SoilTestsPage._viewTest(${t.id})">
        <div class="card-header">
          <div>
            <span class="card-title">🧫 Soil Test</span>
            ${t.zone_name ? `<span class="text-muted" style="font-size:var(--fs-xs);margin-left:var(--space-sm)">• ${t.zone_name}</span>` : ''}
          </div>
          <span class="text-muted" style="font-size:var(--fs-xs)">${dateStr}${t.lab_name ? ` · ${t.lab_name}` : ''}</span>
        </div>
        <div class="soil-metrics">
          ${ph ? `
            <div class="soil-metric">
              <div class="soil-metric-value" style="color:${phStatus.color}">${ph.toFixed(1)}</div>
              <div class="soil-metric-label">pH · ${phStatus.label}</div>
            </div>` : ''}
          ${nutrients.join('')}
        </div>
        ${t.notes ? `<div class="text-muted" style="font-size:var(--fs-xs);margin-top:var(--space-sm)">${t.notes.substring(0, 80)}</div>` : ''}
      </div>`;
  },

  _phStatus(ph) {
    if (ph < 5.5) return { label: 'Very Acidic', color: 'var(--color-danger)' };
    if (ph < 6.0) return { label: 'Acidic', color: 'var(--color-warning)' };
    if (ph <= 7.0) return { label: 'Ideal', color: 'var(--color-success)' };
    if (ph <= 7.5) return { label: 'Alkaline', color: 'var(--color-info)' };
    return { label: 'Very Alkaline', color: 'var(--color-danger)' };
  },

  _phColor(ph) { return this._phStatus(ph).color; },

  _nutrientBadge(label, value, idealLow, idealHigh, unit = 'ppm') {
    const isLow = value < idealLow;
    const isHigh = value > idealHigh * 2;
    const color = isLow ? 'var(--color-warning)' : isHigh ? 'var(--color-info)' : 'var(--color-success)';
    const status = isLow ? '↓' : isHigh ? '↑' : '✓';
    return `
      <div class="soil-metric">
        <div class="soil-metric-value" style="color:${color}">${value}${unit !== 'ppm' ? unit : ''} ${status}</div>
        <div class="soil-metric-label">${label}</div>
      </div>`;
  },

  async _viewTest(id) {
    try {
      const t = await API.getSoilTest(id);
      const interp = t.interpretation || {};
      const phSt = t.ph ? this._phStatus(t.ph) : null;

      let nutrientRows = '';
      const nutrients = [
        { key: 'phosphorus_ppm', label: 'Phosphorus (P)', low: 25, high: 50, unit: 'ppm' },
        { key: 'potassium_ppm', label: 'Potassium (K)', low: 150, high: 250, unit: 'ppm' },
        { key: 'calcium_ppm', label: 'Calcium (Ca)', low: 500, high: 1500, unit: 'ppm' },
        { key: 'magnesium_ppm', label: 'Magnesium (Mg)', low: 50, high: 150, unit: 'ppm' },
        { key: 'nitrogen_ppm', label: 'Nitrogen (N)', low: 10, high: 40, unit: 'ppm' },
        { key: 'sulfur_ppm', label: 'Sulfur (S)', low: 10, high: 50, unit: 'ppm' },
        { key: 'organic_matter_pct', label: 'Organic Matter', low: 3, high: 5, unit: '%' },
        { key: 'cec', label: 'CEC', low: 5, high: 20, unit: 'meq/100g' },
      ];
      nutrients.forEach(n => {
        const val = t[n.key];
        if (val === null || val === undefined) return;
        const isLow = val < n.low;
        const isHigh = val > n.high * 1.5;
        const color = isLow ? 'var(--color-warning)' : isHigh ? 'var(--color-info)' : 'var(--color-success)';
        const statusLabel = isLow ? 'Low' : isHigh ? 'High' : 'Good';
        nutrientRows += `
          <div style="display:flex;justify-content:space-between;align-items:center;padding:var(--space-sm) 0;border-bottom:1px solid var(--border-subtle)">
            <span style="font-size:var(--fs-sm)">${n.label}</span>
            <span style="font-weight:var(--fw-semibold);color:${color}">${val} ${n.unit} <span style="font-size:var(--fs-xs)">(${statusLabel})</span></span>
          </div>`;
      });

      let amendmentsHtml = '';
      if (interp.amendments && interp.amendments.length) {
        amendmentsHtml = interp.amendments.map(a => {
          const det = a.details || {};
          if (!det.needed) return '';
          return `
            <div class="card" style="background:rgba(250,185,38,0.08);border:1px solid rgba(250,185,38,0.3);margin-top:var(--space-md)">
              <div style="font-weight:var(--fw-semibold);margin-bottom:var(--space-sm)">
                ${a.type === 'lime' ? '🌾' : '⚗️'} ${a.type === 'lime' ? 'Lime' : 'Sulfur'} Amendment Needed
              </div>
              <div style="font-size:var(--fs-sm)">
                <strong>${det.lbs_per_1k_sqft} lbs per 1,000 sqft</strong> (${det.total_lbs} lbs total)
              </div>
              ${det.bags_50lb ? `<div class="text-muted" style="font-size:var(--fs-xs)">≈ ${det.bags_50lb} bags (50 lb bags)</div>` : ''}
              <div class="text-secondary" style="font-size:var(--fs-xs);margin-top:var(--space-xs)">${det.application_note || ''}</div>
              <div class="text-muted" style="font-size:var(--fs-xs);margin-top:var(--space-xs)">Method: ${det.method || ''}</div>
            </div>`;
        }).join('');
      }

      Modal.show(`Soil Test — ${Fmt.date(t.test_date)}`, `
        <div>
          ${t.zone_name ? `<div class="text-muted" style="margin-bottom:var(--space-md)">Zone: ${t.zone_name}</div>` : ''}
          ${t.lab_name ? `<div class="text-muted" style="margin-bottom:var(--space-md)">Lab: ${t.lab_name}</div>` : ''}

          ${t.ph ? `
            <div style="text-align:center;padding:var(--space-lg) 0">
              <div style="font-size:3rem;font-weight:var(--fw-bold);color:${phSt.color}">${t.ph.toFixed(1)}</div>
              <div style="font-size:var(--fs-sm);color:${phSt.color}">${phSt.label}</div>
              <div class="text-muted" style="font-size:var(--fs-xs)">Ideal range: 6.0 – 7.0</div>
              ${t.buffer_ph ? `<div class="text-muted" style="font-size:var(--fs-xs)">Buffer pH: ${t.buffer_ph}</div>` : ''}
            </div>` : ''}

          ${nutrientRows ? `<div style="margin-bottom:var(--space-md)">${nutrientRows}</div>` : ''}

          ${amendmentsHtml}

          ${interp.summary && interp.summary.length ? `
            <div class="card" style="background:rgba(52,183,136,0.06);margin-top:var(--space-md)">
              <div style="font-weight:var(--fw-semibold);margin-bottom:var(--space-sm)">📋 Interpretation</div>
              ${interp.summary.map(s => `<div class="text-secondary" style="font-size:var(--fs-sm);margin-bottom:var(--space-xs)">• ${s}</div>`).join('')}
            </div>` : ''}

          ${t.notes ? `<div class="text-muted" style="font-size:var(--fs-sm);margin-top:var(--space-md)">${t.notes}</div>` : ''}

          <div style="display:flex;gap:var(--space-sm);margin-top:var(--space-lg)">
            <button class="btn btn-danger btn-sm" onclick="SoilTestsPage._deleteTest(${t.id})">Delete</button>
            <button class="btn btn-secondary btn-sm" onclick="Modal.close()">Close</button>
          </div>
        </div>
      `);
    } catch (e) { Toast.error(e.message); }
  },

  _showAddForm() {
    let zoneOptions = '<option value="">Whole Lawn</option>';
    this.zones.forEach(z => {
      zoneOptions += `<option value="${z.id}">${z.name}</option>`;
    });

    Modal.show('Add Soil Test', `
      <div style="display:flex;flex-direction:column;gap:var(--space-md)">
        <div class="form-group">
          <label class="form-label">Test Date</label>
          <input type="date" class="form-input" id="stDate" value="${new Date().toISOString().slice(0,10)}">
        </div>
        <div class="form-group">
          <label class="form-label">Zone (optional)</label>
          <select class="form-select" id="stZone">${zoneOptions}</select>
        </div>
        <div class="form-group">
          <label class="form-label">Lab Name (optional)</label>
          <input type="text" class="form-input" id="stLab" placeholder="Penn State, UMass Extension...">
        </div>

        <div style="font-weight:var(--fw-semibold);font-size:var(--fs-sm);color:var(--text-secondary);padding-top:var(--space-sm)">Soil pH</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--space-sm)">
          <div class="form-group">
            <label class="form-label" style="font-size:var(--fs-xs)">pH (required)</label>
            <input type="number" class="form-input" id="stPh" step="0.1" min="3" max="10" placeholder="6.5">
          </div>
          <div class="form-group">
            <label class="form-label" style="font-size:var(--fs-xs)">Buffer pH (optional)</label>
            <input type="number" class="form-input" id="stBufferPh" step="0.1" min="5" max="8" placeholder="6.8">
          </div>
        </div>

        <div style="font-weight:var(--fw-semibold);font-size:var(--fs-sm);color:var(--text-secondary)">Nutrients (optional)</div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:var(--space-sm)">
          <div class="form-group">
            <label class="form-label" style="font-size:var(--fs-xs)">Phosphorus (ppm)</label>
            <input type="number" class="form-input" id="stP" step="1" min="0" placeholder="30">
          </div>
          <div class="form-group">
            <label class="form-label" style="font-size:var(--fs-xs)">Potassium (ppm)</label>
            <input type="number" class="form-input" id="stK" step="1" min="0" placeholder="150">
          </div>
          <div class="form-group">
            <label class="form-label" style="font-size:var(--fs-xs)">Calcium (ppm)</label>
            <input type="number" class="form-input" id="stCa" step="1" min="0" placeholder="800">
          </div>
          <div class="form-group">
            <label class="form-label" style="font-size:var(--fs-xs)">Magnesium (ppm)</label>
            <input type="number" class="form-input" id="stMg" step="1" min="0" placeholder="100">
          </div>
          <div class="form-group">
            <label class="form-label" style="font-size:var(--fs-xs)">Organic Matter (%)</label>
            <input type="number" class="form-input" id="stOM" step="0.1" min="0" max="25" placeholder="3.5">
          </div>
          <div class="form-group">
            <label class="form-label" style="font-size:var(--fs-xs)">CEC</label>
            <input type="number" class="form-input" id="stCEC" step="0.1" min="0" placeholder="12">
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Lab Lime Recommendation (lbs/1000 sqft, optional)</label>
          <input type="number" class="form-input" id="stLimeRec" step="1" min="0" placeholder="50">
        </div>
        <div class="form-group">
          <label class="form-label">Notes (optional)</label>
          <textarea class="form-textarea" id="stNotes" placeholder="Soil type, any issues observed..."></textarea>
        </div>

        <button class="btn btn-primary btn-block" onclick="SoilTestsPage._saveTest()">Save Soil Test</button>
      </div>
    `);
  },

  async _saveTest() {
    const ph = parseFloat(document.getElementById('stPh').value);
    if (!ph) { Toast.warning('pH is required'); return; }

    const data = {
      test_date: document.getElementById('stDate').value,
      zone_id: document.getElementById('stZone').value ? parseInt(document.getElementById('stZone').value) : null,
      lab_name: document.getElementById('stLab').value || null,
      ph,
      buffer_ph: parseFloat(document.getElementById('stBufferPh').value) || null,
      phosphorus_ppm: parseFloat(document.getElementById('stP').value) || null,
      potassium_ppm: parseFloat(document.getElementById('stK').value) || null,
      calcium_ppm: parseFloat(document.getElementById('stCa').value) || null,
      magnesium_ppm: parseFloat(document.getElementById('stMg').value) || null,
      organic_matter_pct: parseFloat(document.getElementById('stOM').value) || null,
      cec: parseFloat(document.getElementById('stCEC').value) || null,
      lime_recommendation_lbs_per_1k: parseFloat(document.getElementById('stLimeRec').value) || null,
      notes: document.getElementById('stNotes').value || null,
    };

    try {
      await API.createSoilTest(data);
      Modal.close();
      Toast.success('Soil test saved!');
      await this._loadList();
    } catch (e) { Toast.error(e.message); }
  },

  async _deleteTest(id) {
    if (!await Modal.confirm({ title: 'Delete Soil Test?', message: 'This soil test and its results will be permanently deleted.', confirmText: 'Delete', variant: 'danger' })) return;
    try {
      await API.deleteSoilTest(id);
      Modal.close();
      Toast.success('Soil test deleted');
      await this._loadList();
    } catch (e) { Toast.error(e.message); }
  },
};
