/** AI Diagnosis Page */
const DiagnosisPage = {
  selectedFile: null,
  activeProvider: null,

  async render(container) {
    container.innerHTML = `
      <div class="section-header anim-fade-in">
        <h1 class="section-title">🔬 AI Lawn Diagnosis</h1>
      </div>

      <div class="card anim-fade-in-up anim-delay-1">
        <div class="card-header">
          <span class="card-title">📸 Analyze Your Lawn</span>
          <span id="diagProviderBadge" class="text-muted" style="font-size:var(--fs-xs)">Loading...</span>
        </div>
        <p class="text-secondary" style="font-size:var(--fs-sm);margin-bottom:var(--space-lg)">
          Take a close-up photo of any problem area. AI will identify weeds, diseases, pests, and recommend treatments.
        </p>

        <div class="photo-upload" id="photoUpload">
          <div class="photo-upload-icon">📷</div>
          <div>Tap to take photo or upload</div>
          <input type="file" id="photoInput" accept="image/*" capture="environment" style="display:none">
        </div>
        <img id="photoPreview" class="photo-preview hidden" alt="Selected photo">

        <button class="btn btn-primary btn-lg btn-block mt-lg" id="analyzeBtn" disabled>
          🔬 Analyze Photo
        </button>
      </div>

      <div id="diagnosisResult" class="anim-fade-in-up"></div>

      <div class="section-header mt-xl"><span class="section-title">Past Diagnoses</span></div>
      <div id="diagnosisHistory" class="anim-fade-in-up">
        <div class="loading-center"><div class="spinner"></div></div>
      </div>
    `;

    this._bindEvents();
    this._loadHistory();
    this._loadProviderInfo();
  },

  async _loadProviderInfo() {
    const badge = document.getElementById('diagProviderBadge');
    try {
      const providers = await API.getAIProviders();
      const providerLabels = { openai: 'OpenAI GPT-4o', anthropic: 'Claude', gemini: 'Gemini' };
      const active = ['openai', 'anthropic', 'gemini'].find(p => providers[p]?.enabled);
      if (active) {
        this.activeProvider = active;
        badge.textContent = `🤖 ${providerLabels[active]} · ${providers[active].model}`;
      } else {
        badge.innerHTML = `<span style="color:var(--color-warning)">⚠ No AI configured — <a onclick="App.navigate('settings')" style="cursor:pointer;text-decoration:underline">Settings</a></span>`;
        document.getElementById('analyzeBtn').disabled = true;
      }
    } catch (e) { badge.textContent = ''; }
  },

  _bindEvents() {
    const upload = document.getElementById('photoUpload');
    const input = document.getElementById('photoInput');
    const preview = document.getElementById('photoPreview');

    upload.addEventListener('click', () => input.click());

    input.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (!file) return;
      this.selectedFile = file;
      const reader = new FileReader();
      reader.onload = (ev) => {
        preview.src = ev.target.result;
        preview.classList.remove('hidden');
        upload.style.display = 'none';
      };
      reader.readAsDataURL(file);
      document.getElementById('analyzeBtn').disabled = false;
    });

    document.getElementById('analyzeBtn').addEventListener('click', () => this._analyze());
  },

  async _analyze() {
    if (!this.selectedFile) return;
    const btn = document.getElementById('analyzeBtn');
    btn.disabled = true;
    btn.innerHTML = '<div class="spinner" style="width:20px;height:20px;border-width:2px;display:inline-block;vertical-align:middle;margin-right:8px"></div> Analyzing...';

    const resultEl = document.getElementById('diagnosisResult');
    resultEl.innerHTML = `
      <div class="card" style="text-align:center;padding:var(--space-2xl)">
        <div class="spinner spinner-lg" style="margin:0 auto var(--space-md)"></div>
        <div class="text-secondary">AI is analyzing your lawn photo...</div>
        <div class="text-muted" style="font-size:var(--fs-xs)">This may take 10-20 seconds</div>
      </div>`;

    try {
      const result = await API.analyzeLawnPhoto(this.selectedFile);
      this._renderResult(result);
      btn.textContent = '🔬 Analyze Another';
      btn.disabled = false;
      this._loadHistory();
    } catch (e) {
      Toast.error(e.message);
      resultEl.innerHTML = '';
      btn.textContent = '🔬 Analyze Photo';
      btn.disabled = false;
    }
  },

  _renderResult(result) {
    const el = document.getElementById('diagnosisResult');
    const issues = result.issues || [];
    const products = result.products || [];
    const actions = result.actions || [];

    let issuesHtml = '';
    if (issues.length) {
      issuesHtml = issues.map(i => `
        <div class="diagnosis-issue">
          <div style="flex:1">
            <div style="font-weight:var(--fw-semibold)">${i.name}</div>
            <div class="text-muted" style="font-size:var(--fs-xs)">${i.type} · ${Math.round(i.confidence * 100)}% confidence</div>
          </div>
          <span class="diagnosis-issue-severity severity-${i.severity}">${i.severity}</span>
        </div>`).join('');
    } else {
      issuesHtml = '<div class="text-muted text-center" style="padding:var(--space-md)">✅ No issues detected — lawn looks good!</div>';
    }

    let productsHtml = products.map(p => `
      <div style="padding:var(--space-sm) 0;border-bottom:1px solid var(--border-subtle)">
        <div style="font-weight:var(--fw-semibold);font-size:var(--fs-sm)">${p.name}</div>
        <div class="text-muted" style="font-size:var(--fs-xs)">${p.application_rate || ''} · ${p.timing || ''}</div>
        ${p.notes ? `<div class="text-secondary" style="font-size:var(--fs-xs);margin-top:2px">${p.notes}</div>` : ''}
      </div>`).join('');

    let actionsHtml = actions.map(a => `
      <div style="padding:var(--space-sm) 0;display:flex;gap:var(--space-sm);align-items:flex-start">
        <span class="badge badge-${a.priority === 'immediate' ? 'danger' : a.priority === 'soon' ? 'warning' : 'info'}">${a.priority}</span>
        <div>
          <div style="font-size:var(--fs-sm)">${a.action}</div>
          ${a.details ? `<div class="text-muted" style="font-size:var(--fs-xs)">${a.details}</div>` : ''}
        </div>
      </div>`).join('');

    el.innerHTML = `
      <div class="card mt-lg">
        <div class="card-header"><span class="card-title">📋 Analysis Results</span></div>
        ${result.summary ? `<p class="text-secondary" style="font-size:var(--fs-sm);margin-bottom:var(--space-lg)">${result.summary}</p>` : ''}
        <div class="section-title" style="font-size:var(--fs-sm);margin-bottom:var(--space-sm)">Issues Found</div>
        ${issuesHtml}
        ${products.length ? `<div class="section-title mt-lg" style="font-size:var(--fs-sm);margin-bottom:var(--space-sm)">Recommended Products</div>${productsHtml}` : ''}
        ${actions.length ? `<div class="section-title mt-lg" style="font-size:var(--fs-sm);margin-bottom:var(--space-sm)">Actions</div>${actionsHtml}` : ''}
      </div>`;
  },

  async _loadHistory() {
    try {
      const history = await API.getDiagnosisHistory();
      const el = document.getElementById('diagnosisHistory');
      if (!history.length) {
        el.innerHTML = '<div class="text-muted text-center" style="padding:var(--space-lg)">No past diagnoses.</div>';
        return;
      }
      el.innerHTML = history.map(h => `
        <div class="card" style="cursor:pointer" onclick="DiagnosisPage._viewDetail(${h.id})">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <div>
              <div style="font-weight:var(--fw-semibold);font-size:var(--fs-sm)">${h.summary}</div>
              <div class="text-muted" style="font-size:var(--fs-xs)">${Fmt.relativeDate(h.created_at)} · ${h.issue_count} issue(s)</div>
            </div>
          </div>
        </div>`).join('');
    } catch (e) { /* no history */ }
  },

  async _viewDetail(id) {
    try {
      const d = await API.getDiagnosis(id);
      this._renderResult(d);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (e) { Toast.error(e.message); }
  },
};
