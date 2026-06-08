/** Settings Page */
const SettingsPage = {
  miniMap: null,
  miniMarker: null,

  async render(container) {
    container.innerHTML = `
      <div class="section-header anim-fade-in">
        <h1 class="section-title">⚙️ Settings</h1>
      </div>
      <div id="settingsContent" class="anim-fade-in-up">
        <div class="loading-center"><div class="spinner"></div></div>
      </div>`;
    await this._load();
  },

  async _load() {
    const el = document.getElementById('settingsContent');
    try {
      const [settings, grassTypes] = await Promise.all([API.getSettings(), API.getGrassTypes()]);
      const lawn = settings.lawn || {};
      const integrations = settings.integrations || {};
      const aiProviders = settings.ai_providers || {};

      let grassOptions = '<option value="">Select grass type...</option>';
      for (const [season, types] of Object.entries(grassTypes)) {
        grassOptions += `<optgroup label="${season.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}">`;
        types.forEach(t => {
          grassOptions += `<option value="${t.value}" ${lawn.grass_type === t.value ? 'selected' : ''}>${t.label}</option>`;
        });
        grassOptions += '</optgroup>';
      }

      el.innerHTML = `
        <div class="card">
          <div class="card-header"><span class="card-title">🏡 Lawn Configuration</span></div>

          <div class="form-group">
            <label class="form-label">Lawn Name</label>
            <input type="text" class="form-input" id="lawnName" value="${lawn.name || 'My Lawn'}" placeholder="My Lawn">
          </div>

          <div class="form-group">
            <label class="form-label">Address / Location</label>
            <div style="display:flex;gap:var(--space-sm)">
              <input type="text" class="form-input" id="lawnAddress" value="${lawn.address || ''}" placeholder="123 Main St, City, State" style="flex:1">
              <button class="btn btn-secondary" id="validateAddrBtn" title="Validate address">📍 Verify</button>
            </div>
            <div id="addressStatus" style="font-size:var(--fs-xs);margin-top:6px;min-height:18px">
              ${lawn.latitude ? `<span style="color:var(--color-success)">✓ Verified — ${lawn.latitude.toFixed(5)}, ${lawn.longitude.toFixed(5)}</span>` : '<span class="text-muted">Enter address and click Verify to validate</span>'}
            </div>
          </div>

          <div id="miniMapWrapper" class="anim-scale-in" style="display:${lawn.latitude ? 'block' : 'none'};margin-bottom:var(--space-lg)">
            <div id="settingsMiniMap" style="width:100%;height:200px;border-radius:var(--radius-md);border:1px solid var(--border-medium);overflow:hidden"></div>
            <div class="text-muted text-center" style="font-size:var(--fs-xs);margin-top:4px">📍 Confirm this is your lawn location</div>
          </div>

          <div class="form-group">
            <label class="form-label">Grass Type</label>
            <select class="form-select" id="lawnGrass">${grassOptions}</select>
          </div>

          <button class="btn btn-primary btn-block" id="saveLawnBtn">Save Configuration</button>
        </div>

        <div class="card">
          <div class="card-header"><span class="card-title">🤖 AI Configuration</span></div>
          <p class="text-muted" style="font-size:var(--fs-sm);margin-bottom:var(--space-md)">
            Configure AI providers for lawn diagnosis, assessment analysis, and consultations. Keys are stored securely in the database.
          </p>
          <div id="aiProviderCards"></div>
        </div>

        <div class="card">
          <div class="card-header"><span class="card-title">🔌 Integrations</span></div>
          <div style="display:flex;flex-direction:column;gap:var(--space-sm)">
            <div style="display:flex;justify-content:space-between;align-items:center;padding:var(--space-sm) 0">
              <span>🌤️ Weather (Open-Meteo)</span>
              <span class="badge ${integrations.weather ? 'badge-success' : 'badge-danger'}">${integrations.weather ? '✓ Active' : '✕ Off'}</span>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;padding:var(--space-sm) 0">
              <span>🏜️ Drought Monitor</span>
              <span class="badge ${integrations.drought ? 'badge-success' : 'badge-danger'}">${integrations.drought ? '✓ Active' : '✕ Off'}</span>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;padding:var(--space-sm) 0">
              <span>🗺️ MapTiler Satellite</span>
              <span class="badge ${integrations.maptiler ? 'badge-success' : 'badge-info'}">${integrations.maptiler ? '✓ Active' : 'Using Esri (free)'}</span>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;padding:var(--space-sm) 0">
              <span>🧠 AI Features</span>
              <span class="badge ${integrations.ai_diagnosis ? 'badge-success' : 'badge-warning'}">${integrations.ai_diagnosis ? '✓ Configured' : '⚠ No key'}</span>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-header"><span class="card-title">ℹ️ About</span></div>
          <div class="text-secondary" style="font-size:var(--fs-sm)">
            <strong>Lawny</strong> v2.0.0<br>
            Smart Lawn Care Management<br><br>
            Weather: Open-Meteo (free, no key required)<br>
            Drought data: US Drought Monitor<br>
            AI: OpenAI GPT-4o · Anthropic Claude · Google Gemini
          </div>
        </div>
      `;

      if (lawn.latitude && lawn.longitude) {
        this._initMiniMap(lawn.latitude, lawn.longitude);
      }

      this._renderAIProviders(aiProviders, lawn.ai_provider);

      document.getElementById('validateAddrBtn').addEventListener('click', () => this._validateAddress());
      document.getElementById('saveLawnBtn').addEventListener('click', () => this._save());
      document.getElementById('lawnAddress').addEventListener('keyup', (e) => {
        if (e.key === 'Enter') this._validateAddress();
      });
    } catch (e) { el.innerHTML = `<div class="text-muted">Error loading settings: ${e.message}</div>`; }
  },

  _renderAIProviders(aiProviders, activeProvider) {
    const el = document.getElementById('aiProviderCards');
    if (!el) return;

    const PROVIDER_META = {
      openai:     { icon: '🟢', label: 'OpenAI',           placeholder: 'sk-...', hint: 'Get key at platform.openai.com' },
      anthropic:  { icon: '🟣', label: 'Anthropic Claude', placeholder: 'sk-ant-...', hint: 'Get key at console.anthropic.com' },
      gemini:     { icon: '🔵', label: 'Google Gemini',    placeholder: 'AIza...', hint: 'Get key at aistudio.google.com' },
    };

    const cards = Object.entries(PROVIDER_META).map(([provider, meta]) => {
      const info = aiProviders[provider] || {};
      const isEnabled = info.enabled;
      const isActive = activeProvider === provider;
      const keyMasked = info.key_masked || '';
      const keySource = info.key_source;
      const availableModels = info.available_models || [];
      const currentModel = info.model || '';

      const modelOptions = availableModels.map(m =>
        `<option value="${m.id}" ${currentModel === m.id ? 'selected' : ''}>${m.label}</option>`
      ).join('');

      const statusBadge = isEnabled
        ? `<span class="badge badge-success" style="font-size:10px">✓ ${keySource === 'database' ? 'DB key' : 'Env key'}</span>`
        : `<span class="badge badge-warning" style="font-size:10px">No key</span>`;

      const activeBadge = isActive && isEnabled
        ? `<span class="badge badge-primary" style="font-size:10px;margin-left:4px">Active</span>`
        : '';

      return `
        <div class="ai-config-card" id="aiCard-${provider}" style="border:1px solid var(--border-light);border-radius:var(--radius-md);padding:var(--space-md);margin-bottom:var(--space-md)">
          <div style="display:flex;align-items:center;gap:var(--space-sm);margin-bottom:var(--space-sm)">
            <span style="font-size:1.3rem">${meta.icon}</span>
            <div style="flex:1">
              <span style="font-weight:var(--fw-semibold)">${meta.label}</span>
              ${statusBadge}${activeBadge}
            </div>
            ${isEnabled && !isActive ? `<button class="btn btn-secondary" style="font-size:var(--fs-xs);padding:4px 8px" onclick="SettingsPage._setActiveProvider('${provider}')">Set Active</button>` : ''}
          </div>

          <div class="form-group" style="margin-bottom:var(--space-sm)">
            <label class="form-label" style="font-size:var(--fs-xs)">API Key</label>
            <div style="display:flex;gap:6px;align-items:center">
              <div style="position:relative;flex:1">
                <input type="password" class="form-input" id="key-${provider}"
                  placeholder="${keyMasked ? keyMasked : meta.placeholder}"
                  style="font-family:monospace;font-size:var(--fs-sm);padding-right:36px"
                  autocomplete="new-password">
                <button type="button" onclick="SettingsPage._toggleKeyVisibility('${provider}')"
                  id="toggle-${provider}"
                  style="position:absolute;right:8px;top:50%;transform:translateY(-50%);background:none;border:none;cursor:pointer;padding:0;font-size:14px;color:var(--text-muted)">👁</button>
              </div>
              ${keyMasked ? `<button class="btn btn-secondary" style="font-size:var(--fs-xs);padding:4px 8px;white-space:nowrap" onclick="SettingsPage._clearKey('${provider}')">Clear</button>` : ''}
            </div>
            ${keyMasked ? `<div style="font-size:var(--fs-xs);color:var(--text-muted);margin-top:3px">Current: ${keyMasked}</div>` : `<div style="font-size:var(--fs-xs);color:var(--text-muted);margin-top:3px">${meta.hint}</div>`}
          </div>

          <div class="form-group" style="margin-bottom:var(--space-sm)">
            <label class="form-label" style="font-size:var(--fs-xs)">Model</label>
            <div style="display:flex;gap:6px;align-items:center">
              <select class="form-select" id="model-${provider}" style="font-size:var(--fs-sm);flex:1">
                ${modelOptions}
              </select>
              <button type="button" title="Refresh models from provider API"
                onclick="SettingsPage._refreshModels('${provider}')"
                id="refresh-models-${provider}"
                style="background:none;border:1px solid var(--border-medium);border-radius:var(--radius-sm);cursor:pointer;padding:6px 8px;font-size:14px;color:var(--text-muted);white-space:nowrap;flex-shrink:0"
                ${!isEnabled ? 'disabled title="Save an API key first"' : ''}>↻</button>
            </div>
            <div id="model-source-${provider}" style="font-size:var(--fs-xs);color:var(--text-muted);margin-top:3px">
              ${isEnabled ? 'Click ↻ to fetch latest models from the API' : 'Add API key to see available models'}
            </div>
          </div>

          <button class="btn btn-primary" style="font-size:var(--fs-xs);padding:6px 16px" onclick="SettingsPage._saveProviderConfig('${provider}')">
            Save ${meta.label}
          </button>
        </div>`;
    }).join('');

    el.innerHTML = cards;
  },

  async _refreshModels(provider) {
    const select = document.getElementById(`model-${provider}`);
    const btn = document.getElementById(`refresh-models-${provider}`);
    const statusEl = document.getElementById(`model-source-${provider}`);
    if (!select || !btn) return;

    btn.textContent = '⏳';
    btn.disabled = true;
    if (statusEl) statusEl.textContent = 'Fetching models from API...';

    try {
      const result = await API.getAIModels(provider);
      const models = result.models || [];
      const currentVal = select.value;

      select.innerHTML = models.map(m =>
        `<option value="${m.id}" ${m.id === currentVal ? 'selected' : ''}>${m.label}</option>`
      ).join('');

      // Restore selection or pick first
      if (!models.find(m => m.id === currentVal) && models.length) {
        select.value = models[0].id;
      }

      const sourceLabel = result.source === 'live'
        ? `✓ ${models.length} models loaded from ${provider} API`
        : `Using offline list (${models.length} models)`;
      if (statusEl) statusEl.textContent = sourceLabel;
      Toast.success(`Loaded ${models.length} models from ${provider}`);
    } catch (e) {
      if (statusEl) statusEl.textContent = 'Could not fetch models — showing offline list';
      Toast.warning('Could not reach provider API');
    }

    btn.textContent = '↻';
    btn.disabled = false;
  },

  _toggleKeyVisibility(provider) {
    const input = document.getElementById(`key-${provider}`);
    const btn = document.getElementById(`toggle-${provider}`);
    if (!input) return;
    if (input.type === 'password') {
      input.type = 'text';
      btn.textContent = '🙈';
    } else {
      input.type = 'password';
      btn.textContent = '👁';
    }
  },

  async _clearKey(provider) {
    if (!await Modal.confirm({ title: `Remove ${provider} API Key?`, message: 'You can re-add it anytime from Settings.', confirmText: 'Remove Key', variant: 'danger' })) return;
    try {
      await API.updateAIConfig({ provider, api_key: '' });
      Toast.success(`${provider} key removed`);
      await this._load();
    } catch (e) { Toast.error(e.message); }
  },

  async _saveProviderConfig(provider) {
    const keyInput = document.getElementById(`key-${provider}`);
    const modelSelect = document.getElementById(`model-${provider}`);
    const key = keyInput?.value?.trim();
    const model = modelSelect?.value;

    if (!key && !model) {
      Toast.warning('Enter an API key or select a model to save.');
      return;
    }

    const btn = document.querySelector(`#aiCard-${provider} .btn-primary`);
    if (btn) { btn.disabled = true; btn.textContent = 'Saving...'; }

    try {
      const payload = { provider };
      if (key) payload.api_key = key;
      if (model) payload.model = model;

      const result = await API.updateAIConfig(payload);
      Toast.success(`${provider} configuration saved${result.enabled ? ' — AI enabled!' : ''}`);
      await this._load();
    } catch (e) {
      Toast.error(e.message || 'Save failed');
      if (btn) { btn.disabled = false; btn.textContent = `Save ${provider}`; }
    }
  },

  async _setActiveProvider(provider) {
    try {
      await API.updateAIProvider(provider);
      Toast.success(`Active AI provider set to ${provider}`);
      await this._load();
    } catch (e) { Toast.error(e.message); }
  },

  _initMiniMap(lat, lon) {
    const wrapper = document.getElementById('miniMapWrapper');
    const mapEl = document.getElementById('settingsMiniMap');
    if (!wrapper || !mapEl) return;

    wrapper.style.display = 'block';

    if (this.miniMap) {
      this.miniMap.remove();
      this.miniMap = null;
    }

    this.miniMap = L.map(mapEl, { zoomControl: false, attributionControl: false, dragging: false, scrollWheelZoom: false }).setView([lat, lon], 18);

    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 22,
    }).addTo(this.miniMap);

    this.miniMarker = L.marker([lat, lon]).addTo(this.miniMap);
    this.miniMarker.bindPopup(`<div style="text-align:center;font-size:12px;color:#333"><strong>Your Lawn</strong><br>${lat.toFixed(5)}, ${lon.toFixed(5)}</div>`).openPopup();

    setTimeout(() => this.miniMap.invalidateSize(), 200);
  },

  async _validateAddress() {
    const address = document.getElementById('lawnAddress').value.trim();
    const statusEl = document.getElementById('addressStatus');
    const btn = document.getElementById('validateAddrBtn');

    if (!address) {
      statusEl.innerHTML = '<span style="color:var(--color-warning)">⚠ Please enter an address</span>';
      return;
    }

    btn.disabled = true;
    btn.textContent = '⏳';
    statusEl.innerHTML = '<span class="text-muted">🔍 Looking up address...</span>';

    try {
      const result = await API.geocode(address);
      if (result) {
        statusEl.innerHTML = `
          <span style="color:var(--color-success)">✓ Found — ${result.display_name || `${result.city}, ${result.state}`}</span><br>
          <span class="text-muted">📍 ${result.latitude.toFixed(5)}, ${result.longitude.toFixed(5)}</span>
        `;
        document.getElementById('lawnAddress').dataset.lat = result.latitude;
        document.getElementById('lawnAddress').dataset.lon = result.longitude;
        document.getElementById('lawnAddress').dataset.displayName = result.display_name || '';
        this._initMiniMap(result.latitude, result.longitude);
        Toast.success('Address verified! Map preview updated.');
      } else {
        statusEl.innerHTML = '<span style="color:var(--color-danger)">✕ Address not found. Try a more specific address.</span>';
        Toast.warning('Could not find that address. Try being more specific.');
      }
    } catch (e) {
      statusEl.innerHTML = `<span style="color:var(--color-danger)">✕ Lookup failed: ${e.message}</span>`;
      Toast.error('Address lookup failed');
    }

    btn.disabled = false;
    btn.textContent = '📍 Verify';
  },

  async _save() {
    const btn = document.getElementById('saveLawnBtn');
    btn.disabled = true;
    btn.textContent = 'Saving...';

    try {
      const addressInput = document.getElementById('lawnAddress');
      const address = addressInput.value.trim();
      const data = {
        name: document.getElementById('lawnName').value,
        address,
        grass_type: document.getElementById('lawnGrass').value || null,
      };

      if (addressInput.dataset.lat && addressInput.dataset.lon) {
        data.latitude = parseFloat(addressInput.dataset.lat);
        data.longitude = parseFloat(addressInput.dataset.lon);
      } else if (address) {
        try {
          const geo = await API.geocode(address);
          if (geo) {
            data.latitude = geo.latitude;
            data.longitude = geo.longitude;
          } else {
            Toast.warning('Could not validate address. Saving without GPS coordinates.');
          }
        } catch (e) { /* save without coords */ }
      }

      await API.updateLawn(data);
      Toast.success('Settings saved!');
      btn.textContent = 'Save Configuration';
      btn.disabled = false;
      await this._load();
    } catch (e) {
      Toast.error(e.message);
      btn.textContent = 'Save Configuration';
      btn.disabled = false;
    }
  },
};
