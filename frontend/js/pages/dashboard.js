/** Dashboard Page — hero-first, collapsible sections, proactive AI */
const DashboardPage = {

  async render(container) {
    container.innerHTML = `<div class="loading-center" style="min-height:60vh"><div class="spinner spinner-lg"></div></div>`;

    let data;
    try { data = await API.getDashboard(); }
    catch (e) {
      container.innerHTML = `<div class="empty-state"><div class="empty-state-icon">⚠️</div>
        <div class="empty-state-title">Connection Error</div>
        <p class="text-muted">Could not reach the Lawny API.</p></div>`;
      return;
    }

    const lawn = data.lawn;
    const hasLocation = lawn?.has_location;

    container.innerHTML = `
      <div class="dash-header anim-fade-in">
        <div>
          <div class="dash-logo">🌿 Lawny</div>
          <div class="dash-greeting">${lawn?.name || 'My Lawn'}</div>
        </div>
        <div style="display:flex;gap:var(--space-sm);align-items:center">
          ${lawn?.grass_type ? `<span class="badge badge-accent" style="text-transform:capitalize">${lawn.grass_type.replace(/_/g,' ')}</span>` : ''}
          <button class="btn btn-ghost btn-sm btn-icon" onclick="App.navigate('settings')" title="Settings">⚙️</button>
        </div>
      </div>

      ${!lawn?.grass_type ? this._renderSetupBanner() : ''}

      <div id="heroSection" class="anim-fade-in-up anim-delay-1"></div>

      <div class="dash-quick-row anim-fade-in-up anim-delay-2">
        <div id="waterQuickStat" class="quick-stat quick-stat-loading">
          <div class="spinner spinner-sm"></div>
        </div>
        <div id="nextQuickStat" class="quick-stat">
          ${this._nextTaskQuickStatHtml(data)}
        </div>
      </div>

      <div id="aiInsightSection" class="anim-fade-in-up anim-delay-2"></div>

      ${this._wrap('tasks',       '📅', 'Upcoming Tasks', true,  '<button class="btn btn-ghost btn-sm" onclick="App.navigate(\'plan\')" style="font-size:var(--fs-xs)">Plan →</button>')}
      ${this._wrap('watering',    '💧', 'Watering',        true)}
      ${this._wrap('weather',     '🌤️', 'Weather',         false)}
      ${this._wrap('fertilizer',  '🌱', 'Fertilizer',      false)}
      ${this._wrap('program',     '📋', 'Lawn Program',    false)}
      ${this._wrap('soil',        '🧪', 'Soil Health',     false)}
      ${this._wrap('recent',      '📝', 'Activity',        false, '<button class="btn btn-ghost btn-sm" onclick="App.navigate(\'history\')" style="font-size:var(--fs-xs)">All →</button>')}
    `;

    // Sync renders
    this._renderHero(data);
    this._renderTasks(data.upcoming_tasks || []);
    this._renderRecent(data.recent_activities || []);

    // Async loads
    if (hasLocation) {
      this._loadAIInsight();
      this._loadWaterQuickStat();
      this._loadWeather();
      this._loadHydration();
    } else {
      document.getElementById('aiInsightSection').innerHTML = '';
      const wqs = document.getElementById('waterQuickStat');
      if (wqs) { wqs.classList.remove('quick-stat-loading'); wqs.innerHTML = `<div class="quick-stat-icon">📍</div><div><div class="quick-stat-label">Watering</div><div class="quick-stat-value text-muted" style="font-size:var(--fs-xs)">Set location in Settings</div></div>`; }
      document.getElementById('section-watering').innerHTML = '<div class="text-muted text-center" style="padding:var(--space-lg)">Add your lawn location in Settings to see watering data.</div>';
      document.getElementById('section-weather').innerHTML = '';
    }

    this._loadFertilizer();
    this._loadSoilSummary();
    this._loadProgramSummary();
  },

  // ── Layout helpers ───────────────────────────────────────────────

  _wrap(id, icon, title, openDefault, extra = '') {
    return `
      <div class="dash-section anim-fade-in-up">
        <div class="dash-section-hdr" onclick="DashboardPage._toggle('${id}')">
          <span class="dash-section-title">${icon} ${title}</span>
          <div style="display:flex;align-items:center;gap:var(--space-xs)">
            ${extra}
            <span class="dash-chevron ${openDefault ? 'open' : ''}" id="chevron-${id}">›</span>
          </div>
        </div>
        <div id="section-${id}" class="dash-section-body" ${openDefault ? '' : 'style="display:none"'}>
          <div class="loading-center" style="padding:var(--space-md) 0"><div class="spinner spinner-sm"></div></div>
        </div>
      </div>`;
  },

  _toggle(id) {
    const body = document.getElementById(`section-${id}`);
    const chevron = document.getElementById(`chevron-${id}`);
    if (!body) return;
    const opening = body.style.display === 'none';
    body.style.display = opening ? 'block' : 'none';
    if (chevron) chevron.classList.toggle('open', opening);
  },

  _renderSetupBanner() {
    return `
      <div class="setup-card anim-fade-in-up">
        <div class="setup-card-icon">🏡</div>
        <div class="setup-card-title">Set Up Your Lawn</div>
        <div class="setup-card-desc">Add your location and grass type to unlock weather insights, watering recommendations, and AI seasonal tips.</div>
        <button class="btn btn-primary btn-lg" onclick="App.navigate('settings')">Get Started →</button>
      </div>`;
  },

  // ── Hero Card ────────────────────────────────────────────────────

  _renderHero(data) {
    const el = document.getElementById('heroSection');
    if (!el) return;

    const avg   = data.avg_health_score;
    const trend = data.health_trend || [];
    const daysSinceMow = data.days_since_mow;
    const tasks = data.upcoming_tasks || [];

    const overdue = tasks.filter(t => t.is_overdue).length;
    const dueThisWeek = tasks.filter(t => !t.is_overdue && t.days_until <= 7).length;

    const scoreColor = avg ? Fmt.healthColor(Math.round(avg)) : 'var(--text-muted)';
    const scoreLabel = avg ? Fmt.healthLabel(Math.round(avg)) : 'No ratings yet';

    // Trend label from health_trend first-half vs second-half avg
    let trendBadge = '';
    if (trend.length >= 4) {
      const mid = Math.floor(trend.length / 2);
      const early = trend.slice(0, mid).reduce((s, t) => s + (t.score || 5), 0) / mid;
      const late  = trend.slice(mid).reduce((s, t) => s + (t.score || 5), 0) / (trend.length - mid);
      const delta = late - early;
      if (delta > 0.4) trendBadge = `<span class="hero-trend-badge up">↑ ${delta.toFixed(1)}</span>`;
      else if (delta < -0.4) trendBadge = `<span class="hero-trend-badge down">↓ ${delta.toFixed(1)}</span>`;
      else trendBadge = `<span class="hero-trend-badge flat">→ Stable</span>`;
    }

    // Task status badge
    let taskBadge = '';
    if (overdue > 0)
      taskBadge = `<div class="hero-task-badge overdue" onclick="App.navigate('plan')">⚠️ ${overdue} overdue</div>`;
    else if (dueThisWeek > 0)
      taskBadge = `<div class="hero-task-badge due" onclick="App.navigate('plan')">🔔 ${dueThisWeek} due this week</div>`;
    else if (tasks.length > 0)
      taskBadge = `<div class="hero-task-badge ok">✓ All caught up</div>`;

    const mowHtml = daysSinceMow !== null && daysSinceMow !== undefined
      ? `<div class="hero-meta">✂️ Mowed ${daysSinceMow === 0 ? 'today' : `${daysSinceMow}d ago`}</div>`
      : '';

    const noDataCta = trend.length === 0
      ? `<div class="hero-cta"><button class="btn btn-secondary btn-sm" onclick="App.navigate('log-activity')">Log first activity to track health →</button></div>`
      : '';

    el.innerHTML = `
      <div class="hero-card card">
        <div class="hero-body">
          <div class="hero-score-col">
            <div class="hero-score" style="color:${scoreColor}">${avg ? avg.toFixed(1) : '—'}</div>
            <div class="hero-score-sub">${scoreLabel} ${trendBadge}</div>
            ${mowHtml}
          </div>
          <div class="hero-chart-col">
            ${this._sparkline(trend)}
            ${taskBadge}
          </div>
        </div>
        ${noDataCta}
      </div>`;
  },

  _sparkline(trend) {
    if (!trend || trend.length < 2) return '<div class="sparkline-empty text-muted" style="font-size:var(--fs-xs)">No history yet</div>';
    const scores = trend.map(t => t.score || 5);
    const W = 110, H = 36;
    const pts = scores.map((s, i) => {
      const x = (i / (scores.length - 1)) * W;
      const y = H - ((s - 1) / 9) * H;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    });
    const lastScore = scores[scores.length - 1];
    const color = Fmt.healthColor(Math.round(lastScore));
    const lastPt = pts[pts.length - 1].split(',');
    const fillPts = `0,${H} ${pts.join(' ')} ${W},${H}`;

    return `
      <div class="sparkline-wrap">
        <svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" style="overflow:visible;display:block">
          <defs>
            <linearGradient id="sg" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="${color}" stop-opacity="0.25"/>
              <stop offset="100%" stop-color="${color}" stop-opacity="0"/>
            </linearGradient>
          </defs>
          <polygon points="${fillPts}" fill="url(#sg)"/>
          <polyline points="${pts.join(' ')}" fill="none" stroke="${color}" stroke-width="1.5"
            stroke-linecap="round" stroke-linejoin="round"/>
          <circle cx="${lastPt[0]}" cy="${lastPt[1]}" r="2.5" fill="${color}"/>
        </svg>
      </div>`;
  },

  // ── Quick Stats ──────────────────────────────────────────────────

  _nextTaskQuickStatHtml(data) {
    const first = (data.upcoming_tasks || [])[0];
    if (!first) return `<div class="quick-stat-icon">📋</div><div><div class="quick-stat-label">Next Task</div><div class="quick-stat-value text-muted">None</div></div>`;
    const meta = Fmt.ACTIVITY_META[first.type] || Fmt.ACTIVITY_META.other;
    const dueText = first.is_overdue ? `${Math.abs(first.days_until)}d overdue` : first.days_until === 0 ? 'Today' : `in ${first.days_until}d`;
    const color = first.is_overdue ? 'var(--color-danger)' : first.days_until <= 2 ? 'var(--color-warning)' : 'var(--text-primary)';
    return `
      <div class="quick-stat-icon">${meta.icon}</div>
      <div>
        <div class="quick-stat-label">Next Task</div>
        <div class="quick-stat-value" style="color:${color}">${meta.label}</div>
        <div class="quick-stat-sub">${dueText}</div>
      </div>`;
  },

  async _loadWaterQuickStat() {
    const el = document.getElementById('waterQuickStat');
    if (!el) return;
    try {
      const [rec, hydration] = await Promise.allSettled([
        API.getWateringRecommendation(),
        API.getHydrationBalance(),
      ]);
      el.classList.remove('quick-stat-loading');

      const hydData  = hydration.status === 'fulfilled' ? hydration.value : null;
      const recData  = rec.status === 'fulfilled' ? rec.value : null;
      const delta    = hydData?.balance?.past_delta_in;

      if (delta !== undefined && delta !== null) {
        const info  = Fmt.hydrationStatus(delta);
        const color = Fmt.hydrationBarColor(info.cls);
        el.innerHTML = `
          <div class="quick-stat-icon">${info.icon}</div>
          <div>
            <div class="quick-stat-label">Hydration</div>
            <div class="quick-stat-value" style="color:${color}">${delta > 0 ? '+' : ''}${delta.toFixed(2)}"</div>
            <div class="quick-stat-sub">${info.label}</div>
          </div>`;
      } else if (recData) {
        const icons = { none: '✅', light: '💧', moderate: '🌧️', heavy: '🚿' };
        el.innerHTML = `
          <div class="quick-stat-icon">${icons[recData.recommendation] || '💧'}</div>
          <div>
            <div class="quick-stat-label">Watering</div>
            <div class="quick-stat-value">${recData.recommendation || '—'}</div>
          </div>`;
      } else {
        el.innerHTML = '<div class="quick-stat-icon">💧</div><div><div class="quick-stat-label">Watering</div><div class="quick-stat-value text-muted">—</div></div>';
      }
    } catch (e) {
      const el2 = document.getElementById('waterQuickStat');
      if (el2) { el2.classList.remove('quick-stat-loading'); el2.innerHTML = '<div class="quick-stat-icon">💧</div><div class="quick-stat-label">—</div>'; }
    }
  },

  // ── AI Insight ───────────────────────────────────────────────────

  async _loadAIInsight() {
    const el = document.getElementById('aiInsightSection');
    if (!el) return;
    el.innerHTML = '<div class="ai-insight-card card"><div class="spinner spinner-sm"></div></div>';
    try {
      const alerts = await API.getSeasonalAlerts();
      if (!alerts.length) { el.innerHTML = ''; return; }

      const top = alerts[0];
      const sevColors = { low: 'var(--color-accent)', medium: 'var(--color-warning)', high: 'var(--color-danger)', critical: '#E03131' };
      const color = sevColors[top.severity] || 'var(--color-accent)';
      const extra = alerts.length > 1 ? `<div class="ai-insight-extra">+${alerts.length - 1} more seasonal alerts</div>` : '';

      el.innerHTML = `
        <div class="ai-insight-card card" style="border-left:3px solid ${color}">
          <div class="ai-insight-header">
            <span class="ai-insight-badge">🤖 AI Insight</span>
            <button class="btn btn-ghost btn-sm" onclick="App.navigate('ai-hub',{tab:'coach'})" style="font-size:var(--fs-xs)">Ask Coach →</button>
          </div>
          <div class="ai-insight-title">${top.icon || '🌿'} ${top.title}</div>
          <div class="ai-insight-body">${top.preventive_action || top.description || ''}</div>
          ${extra}
        </div>`;
    } catch (e) { el.innerHTML = ''; }
  },

  // ── Collapsible section content loaders ─────────────────────────

  async _loadWeather() {
    const el = document.getElementById('section-weather');
    if (!el) return;
    try {
      const w = await API.getCurrentWeather();
      el.innerHTML = `
        <div class="weather-card card">
          <div class="weather-main">
            <div>
              <div class="weather-temp">${Fmt.temp(w.temperature_f)}</div>
              <div class="weather-desc">${w.weather_description || ''}</div>
            </div>
            <div class="weather-icon">${Fmt.weatherIcon(w.weather_code)}</div>
          </div>
          <div class="weather-details">
            <div class="weather-detail">
              <div class="weather-detail-value">${Fmt.temp(w.soil_temp_surface_f)}</div>
              <div class="weather-detail-label">Soil Temp</div>
            </div>
            <div class="weather-detail">
              <div class="weather-detail-value">${w.humidity_pct ? Math.round(w.humidity_pct) + '%' : '—'}</div>
              <div class="weather-detail-label">Humidity</div>
            </div>
            <div class="weather-detail">
              <div class="weather-detail-value">${w.uv_index != null ? w.uv_index.toFixed(1) : '—'}</div>
              <div class="weather-detail-label">UV Index</div>
            </div>
          </div>
        </div>`;
    } catch (e) { el.innerHTML = ''; }
  },

  async _loadHydration() {
    const el = document.getElementById('section-watering');
    if (!el) return;
    try {
      const [watering, hydration] = await Promise.all([
        API.getWateringRecommendation(),
        API.getHydrationBalance(),
      ]);

      const rec = watering;
      const bal = hydration.balance || {};
      const past = hydration.past || {};
      const future = hydration.future || {};
      const drought = hydration.drought;
      const adjustments = hydration.adjustments || {};

      const statusInfo = Fmt.hydrationStatus(bal.past_delta_in);
      const recIcons  = { none: '✅', light: '💧', moderate: '🌧️', heavy: '🚿' };
      const recTitles = { none: 'No Watering Needed', light: 'Light Watering', moderate: 'Moderate Watering', heavy: 'Heavy Watering' };
      const droughtHtml = drought ? this._droughtBadge(drought) : '';
      const weeklyNeed = hydration.weekly_need_in || 1;
      const pastNeed   = past.total_need_in || weeklyNeed;
      const rainPct    = Math.min(100, ((past.rain_in || 0) / pastNeed) * 100);
      const wateredPct = Math.min(100 - rainPct, ((past.watering_logged_in || 0) / pastNeed) * 100);
      const totalPct   = Math.min(100, rainPct + wateredPct);
      const deficitPct = Math.max(0, 100 - totalPct);
      const futureShortfall = future.shortfall_in ?? Math.max(0, (future.predicted_need_in || 0) - (future.predicted_rain_in || 0));
      const timelineHtml = this._renderTimeline(past.daily || [], future.daily || [], pastNeed / 7);

      el.innerHTML = `
        <div class="card ${`water-${rec.recommendation || 'none'}`}" style="border-left:3px solid ${this._recColor(rec.recommendation)}">
          <div class="card-header">
            <span class="card-title">💧 Watering Plan</span>
            ${droughtHtml}
          </div>
          <div class="water-rec-main">
            <div class="water-rec-icon">${recIcons[rec.recommendation] || '💧'}</div>
            <div>
              <div class="water-rec-title">${recTitles[rec.recommendation] || 'Check Conditions'}</div>
              <div class="water-rec-freq">${rec.frequency || ''}</div>
            </div>
          </div>
          ${rec.duration_minutes ? `<div class="text-muted" style="font-size:var(--fs-xs);margin-bottom:var(--space-sm)">⏱ Run ~${rec.duration_minutes} min per zone</div>` : ''}
        </div>

        <div class="card hydration-card hydration-${statusInfo.cls}">
          <div class="card-header">
            <span class="card-title">🌊 Hydration Balance <span class="info-icon" data-tip="How your lawn's water supply (rain + logged watering) compares to its actual needs over the past 7 days.">ⓘ</span></span>
            <span class="hydration-status-badge hydration-badge-${statusInfo.cls}">${statusInfo.icon} ${bal.status_label || statusInfo.label}</span>
          </div>
          <div class="hydration-delta">
            <div class="hydration-delta-value" style="color:${Fmt.hydrationBarColor(statusInfo.cls)}">
              ${bal.past_delta_in > 0 ? '+' : ''}${(bal.past_delta_in || 0).toFixed(2)}"
            </div>
            <div class="hydration-delta-label">${bal.past_delta_in >= 0 ? 'surplus' : 'deficit'} · past 7 days</div>
          </div>
          <div class="hydration-bar-section">
            <div class="hydration-bar-label">
              <span>7-Day Need: ${Fmt.precip(pastNeed)}</span>
              <span>Received: ${Fmt.precip(past.total_received_in)}</span>
            </div>
            <div class="hydration-bar-track">
              <div class="hydration-bar-segment hydration-bar-rain" style="width:${rainPct}%"></div>
              <div class="hydration-bar-segment hydration-bar-watered" style="width:${wateredPct}%"></div>
              ${deficitPct > 2 ? `<div class="hydration-bar-deficit" style="width:${deficitPct}%"></div>` : ''}
              <div class="hydration-bar-need-marker"></div>
            </div>
            <div class="hydration-bar-legend">
              <span class="hydration-legend-item"><span class="hydration-legend-dot" style="background:#339AF0"></span>Rain</span>
              <span class="hydration-legend-item"><span class="hydration-legend-dot" style="background:#22B8CF"></span>Watered</span>
              ${deficitPct > 2 ? '<span class="hydration-legend-item"><span class="hydration-legend-dot" style="background:rgba(250,82,82,0.3)"></span>Deficit</span>' : ''}
            </div>
          </div>
          <div class="stat-row" style="margin:var(--space-md) 0">
            <div class="stat-item">
              <div class="stat-value" style="color:#339AF0">${Fmt.precip(past.rain_in)}</div>
              <div class="stat-label">Rain (7d)</div>
            </div>
            <div class="stat-item">
              <div class="stat-value" style="color:#22B8CF">${Fmt.precip(past.watering_logged_in)}</div>
              <div class="stat-label">Watered (7d)</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">${Fmt.precip(past.total_need_in)}</div>
              <div class="stat-label">Need (7d)</div>
            </div>
            <div class="stat-item">
              <div class="stat-value" style="color:${Fmt.hydrationBarColor(statusInfo.cls)}">${bal.past_delta_in > 0 ? '+' : ''}${Fmt.precip(Math.abs(bal.past_delta_in || 0))}</div>
              <div class="stat-label">Delta</div>
            </div>
          </div>
          <div class="hydration-timeline-section">
            <div class="hydration-timeline-header">
              <span style="font-size:var(--fs-xs);color:var(--text-muted)">Past 7 days</span>
              <span style="font-size:var(--fs-xs);color:var(--text-muted)">▸ Forecast</span>
            </div>
            <div class="hydration-timeline">${timelineHtml}</div>
          </div>
          <div class="hydration-outlook">
            <div class="hydration-outlook-header">📅 7-Day Forecast <span class="info-icon" data-tip="Today through the next 6 days. Rain is probability-weighted (50% chance of 1&quot; = 0.5&quot; expected).">ⓘ</span></div>
            <div class="hydration-outlook-stats">
              <div>
                <span class="text-muted" style="font-size:var(--fs-xs)">Expected Rain <span class="info-icon" data-tip="Forecasted precipitation weighted by probability of occurrence.">ⓘ</span></span>
                <div style="font-weight:var(--fw-semibold);color:#339AF0">${Fmt.precip(future.predicted_rain_in)}</div>
              </div>
              <div>
                <span class="text-muted" style="font-size:var(--fs-xs)">Total ET Need <span class="info-icon" data-tip="Total water your lawn needs this week from all sources (rain + manual watering) based on grass type and forecasted temps.">ⓘ</span></span>
                <div style="font-weight:var(--fw-semibold)">${Fmt.precip(future.predicted_need_in)}</div>
              </div>
              <div>
                <span class="text-muted" style="font-size:var(--fs-xs)">Supplement Needed <span class="info-icon" data-tip="How much you need to manually water beyond expected rain to meet your lawn's needs this week.">ⓘ</span></span>
                <div style="font-weight:var(--fw-semibold);color:${futureShortfall > 0.1 ? 'var(--color-warning)' : 'var(--color-success)'}">
                  ${futureShortfall > 0 ? futureShortfall.toFixed(2) + '"' : 'None'}
                </div>
              </div>
              <div>
                <span class="text-muted" style="font-size:var(--fs-xs)">14-Day Balance <span class="info-icon" data-tip="Cumulative water surplus or deficit across the past 7 days plus the 7-day forecast. Negative means the lawn will be under-watered over the full 14-day window.">ⓘ</span></span>
                <div style="font-weight:var(--fw-semibold);color:${Fmt.hydrationBarColor(Fmt.hydrationStatus(bal.projected_delta_in).cls)}">
                  ${bal.projected_delta_in > 0 ? '+' : ''}${(bal.projected_delta_in || 0).toFixed(2)}"
                </div>
              </div>
            </div>
            ${futureShortfall > 0.25 ? `<div class="hydration-action-callout"><span>⚡</span><span>~${futureShortfall.toFixed(2)}" of supplemental watering needed this week beyond forecasted rain.</span></div>` : ''}
          </div>
          ${adjustments.explanation && adjustments.explanation !== 'Standard conditions' ? `<div class="hydration-adjustments"><span style="font-size:var(--fs-xs);color:var(--text-muted)">⚙️ ${adjustments.explanation}</span></div>` : ''}
        </div>`;

      requestAnimationFrame(() => {
        el.querySelectorAll('.hydration-bar-segment').forEach(seg => {
          const w = seg.style.width; seg.style.width = '0%';
          requestAnimationFrame(() => { seg.style.width = w; });
        });
        el.querySelectorAll('.hydration-day-fill').forEach(fill => {
          const h = fill.style.height; fill.style.height = '0%';
          requestAnimationFrame(() => { fill.style.height = h; });
        });
      });
    } catch (e) {
      if (el) el.innerHTML = '<div class="text-muted text-center" style="padding:var(--space-md)">Watering data unavailable.</div>';
    }
  },

  _renderTasks(tasks) {
    const el = document.getElementById('section-tasks');
    if (!el) return;
    if (!tasks.length) {
      el.innerHTML = `<div class="card"><div class="text-muted text-center" style="padding:var(--space-md) 0">No schedules yet — <button class="btn btn-ghost btn-sm" onclick="App.navigate('schedule')">add one</button> to stay on track.</div></div>`;
      return;
    }
    const html = tasks.slice(0, 5).map(t => {
      const meta = Fmt.ACTIVITY_META[t.type] || Fmt.ACTIVITY_META.other;
      const dueText = t.is_overdue ? `${Math.abs(t.days_until)} days overdue` : t.days_until === 0 ? 'Due today' : `in ${t.days_until} days`;
      return `
        <div class="task-item">
          <span class="task-icon">${meta.icon}</span>
          <div class="task-info">
            <div class="task-name">${meta.label}${t.zone_name ? ` · ${t.zone_name}` : ''}</div>
            <div class="task-due ${t.is_overdue ? 'task-overdue' : ''}">${dueText}</div>
          </div>
          <button class="task-complete-btn" onclick="DashboardPage._completeTask(${t.id})" title="Complete">✓</button>
        </div>`;
    }).join('');
    el.innerHTML = `<div class="card">${html}</div>`;
  },

  _renderRecent(activities) {
    const el = document.getElementById('section-recent');
    if (!el) return;
    if (!activities.length) {
      el.innerHTML = `<div class="card"><div class="text-muted text-center" style="padding:var(--space-md) 0">No activities logged yet.</div></div>`;
      return;
    }
    const html = activities.map(a => `
      <div class="timeline-item">
        <div class="timeline-icon">${Fmt.activityIcon(a.type)}</div>
        <div class="timeline-content">
          <div class="timeline-title">${Fmt.activityLabel(a.type)}${a.zone_name ? ` · ${a.zone_name}` : ''}</div>
          <div class="timeline-meta">
            ${Fmt.relativeDate(a.date)}
            ${a.health_score ? ` · <span style="color:${Fmt.healthColor(a.health_score)}">${Fmt.healthEmoji(a.health_score)} ${a.health_score}/10</span>` : ''}
          </div>
          ${a.notes ? `<div class="text-muted" style="font-size:var(--fs-xs);margin-top:2px">${a.notes.substring(0, 80)}</div>` : ''}
        </div>
      </div>`).join('');
    el.innerHTML = `<div class="card">${html}</div>`;
  },

  async _completeTask(id) {
    try {
      await API.completeSchedule(id);
      Toast.success('Task completed!');
      App.navigate('dashboard');
    } catch (e) { Toast.error(e.message); }
  },

  async _loadProgramSummary() {
    const el = document.getElementById('section-program');
    if (!el) return;
    try {
      const program = await API.getActiveProgram();
      if (!program) {
        el.innerHTML = `<div class="card" style="cursor:pointer;text-align:center;padding:var(--space-lg)" onclick="App.navigate('assessment')">
          <div class="text-muted" style="font-size:var(--fs-sm)">No active program</div>
          <button class="btn btn-primary btn-sm" style="margin-top:var(--space-sm)">🔍 Run Assessment</button>
        </div>`;
        return;
      }
      const now = new Date(); const thisMonth = now.getMonth() + 1;
      const nextSteps = program.steps
        .filter(s => s.status === 'pending' && s.month >= thisMonth)
        .sort((a, b) => (a.month - b.month) || (a.order_index - b.order_index))
        .slice(0, 3);
      const srcColors = { fertilizer: '#20C997', ai_remediation: '#339AF0', manual: '#FAB005' };
      el.innerHTML = `
        <div class="card" style="cursor:pointer" onclick="App.navigate('lawn-program')">
          <div class="card-header">
            <span class="card-title">📋 ${program.name || 'Lawn Program'}</span>
            <span class="badge badge-accent">${program.progress_pct}%</span>
          </div>
          <div style="background:var(--bg-elevated);border-radius:99px;height:5px;margin-bottom:var(--space-md)">
            <div style="background:var(--color-accent);border-radius:99px;height:5px;width:${program.progress_pct}%"></div>
          </div>
          ${nextSteps.length ? nextSteps.map(s => `
            <div style="display:flex;align-items:center;gap:var(--space-sm);padding:var(--space-xs) 0;border-bottom:1px solid var(--border-subtle)">
              <span>${s.activity_icon || '📋'}</span>
              <div style="flex:1;min-width:0">
                <div style="font-size:var(--fs-sm);font-weight:var(--fw-medium)">${s.product_name || s.activity_type}</div>
                <div class="text-muted" style="font-size:var(--fs-xs)">${s.month_name || ''}${s.week_of_month ? ` wk ${s.week_of_month}` : ''}</div>
              </div>
              <span style="font-size:var(--fs-xs);color:${srcColors[s.source] || 'var(--text-muted)'}">${s.source === 'ai_remediation' ? 'AI' : s.source === 'fertilizer' ? 'Fert' : 'Manual'}</span>
            </div>`).join('') : '<div class="text-muted text-center" style="font-size:var(--fs-sm)">All caught up! 🎉</div>'}
          <div style="display:flex;justify-content:space-between;align-items:center;margin-top:var(--space-sm)">
            <span class="text-muted" style="font-size:var(--fs-xs)">${program.completed_steps}/${program.total_steps} done</span>
            <button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();App.navigate('assessment')">+ Assess</button>
          </div>
        </div>`;
    } catch (e) { el.innerHTML = ''; }
  },

  async _loadFertilizer() {
    const el = document.getElementById('section-fertilizer');
    if (!el) return;
    try {
      const active = await API.fertilizerActive();
      if (!active) {
        el.innerHTML = `<div class="card" style="cursor:pointer;text-align:center;padding:var(--space-lg)" onclick="App.navigate('fertilizer')">
          <div class="text-muted" style="font-size:var(--fs-sm)">No program active</div>
          <button class="btn btn-secondary btn-sm" style="margin-top:var(--space-sm)">Browse Programs</button>
        </div>`;
        return;
      }
      const { program, steps, completed, total, progress_pct } = active;
      const nextStep = steps.find(s => s.status === 'current' || s.status === 'overdue');
      el.innerHTML = `
        <div class="card" style="cursor:pointer" onclick="App.navigate('fertilizer')">
          <div class="card-header">
            <span class="card-title">🌱 ${program.brand || ''} ${program.name}</span>
            <span class="badge badge-accent">${progress_pct}%</span>
          </div>
          <div class="fert-progress" style="margin:var(--space-sm) 0">
            <div class="fert-progress-fill" style="width:${progress_pct}%"></div>
          </div>
          <span class="text-secondary" style="font-size:var(--fs-xs)">${completed}/${total} steps complete</span>
          ${nextStep ? `
            <div style="margin-top:var(--space-sm);padding-top:var(--space-sm);border-top:1px solid var(--border-subtle);display:flex;align-items:center;gap:var(--space-sm)">
              <span>${nextStep.icon_emoji || '🧪'}</span>
              <div style="flex:1;min-width:0">
                <div style="font-size:var(--fs-sm);font-weight:var(--fw-semibold)">${nextStep.status === 'overdue' ? '⚠️ ' : ''}Next: ${nextStep.product_name}</div>
                <div class="text-muted" style="font-size:var(--fs-xs)">${nextStep.season_label || ''} · ${nextStep.month_label || ''}</div>
              </div>
            </div>` : ''}
        </div>`;
    } catch (e) { el.innerHTML = ''; }
  },

  async _loadSoilSummary() {
    const el = document.getElementById('section-soil');
    if (!el) return;
    try {
      const test = await API.getLatestSoilTest();
      if (!test?.ph) { el.innerHTML = `<div class="card" style="cursor:pointer;text-align:center;padding:var(--space-lg)" onclick="App.navigate('soil-tests')"><div class="text-muted" style="font-size:var(--fs-sm)">No soil tests yet</div><button class="btn btn-secondary btn-sm" style="margin-top:var(--space-sm)">Log First Test</button></div>`; return; }
      const phColorMap = { very_low:'#FA5252',low:'#FAB005',ideal:'#20C997',high:'#FAB005',very_high:'#E03131' };
      const phInfo = test.interpretation?.ph_status || {};
      const phColor = phColorMap[phInfo.status] || 'var(--color-accent)';
      const testDate = test.test_date ? new Date(test.test_date).toLocaleDateString('en-US',{month:'short',year:'numeric'}) : '';
      el.innerHTML = `
        <div class="card" style="cursor:pointer" onclick="App.navigate('soil-tests')">
          <div class="card-header">
            <span class="card-title">🧪 Latest Soil Test</span>
            <span class="text-muted" style="font-size:var(--fs-xs)">${testDate}</span>
          </div>
          <div class="soil-metrics">
            <div class="soil-metric"><div class="soil-metric-value" style="color:${phColor}">${test.ph?.toFixed(1) || '—'}</div><div class="soil-metric-label">pH</div></div>
            ${test.nitrogen_ppm != null ? `<div class="soil-metric"><div class="soil-metric-value">${test.nitrogen_ppm}</div><div class="soil-metric-label">N ppm</div></div>` : ''}
            ${test.phosphorus_ppm != null ? `<div class="soil-metric"><div class="soil-metric-value">${test.phosphorus_ppm}</div><div class="soil-metric-label">P ppm</div></div>` : ''}
            ${test.potassium_ppm != null ? `<div class="soil-metric"><div class="soil-metric-value">${test.potassium_ppm}</div><div class="soil-metric-label">K ppm</div></div>` : ''}
            ${test.organic_matter_pct != null ? `<div class="soil-metric"><div class="soil-metric-value">${test.organic_matter_pct}%</div><div class="soil-metric-label">Org. Matter</div></div>` : ''}
          </div>
          ${phInfo.label ? `<div style="font-size:var(--fs-xs);color:${phColor};margin-top:var(--space-xs)">${phInfo.label}</div>` : ''}
        </div>`;
    } catch (e) { el.innerHTML = ''; }
  },

  // ── Shared helpers (kept from original) ─────────────────────────

  _recColor(rec) {
    return { none:'var(--color-success)', light:'var(--color-info)', moderate:'var(--color-warning)', heavy:'var(--color-danger)' }[rec] || 'var(--color-info)';
  },

  _droughtBadge(drought) {
    if (!drought?.drought_level || drought.drought_level === 'None') {
      return `<span class="drought-badge" style="background:rgba(82,183,136,0.15);color:#52B788">${Fmt.droughtIcon(null)} No Drought</span>`;
    }
    const severity = drought.severity || 0;
    const pulseClass = severity >= 2 ? 'drought-pulse' : '';
    return `<span class="drought-badge ${pulseClass}" style="background:${drought.color}20;color:${drought.color};border:1px solid ${drought.color}40">
      ${Fmt.droughtIcon(drought.drought_level)} ${drought.drought_label}
      ${drought.coverage_pct ? `<span style="opacity:0.7;font-size:var(--fs-xs);margin-left:4px">${drought.coverage_pct}%</span>` : ''}
    </span>`;
  },

  _renderTimeline(pastDays, futureDays, avgDailyNeed) {
    const allDays = [...pastDays, ...futureDays];
    if (!allDays.length) return '<div class="text-muted text-center" style="padding:var(--space-md)">No data</div>';
    const maxVal = Math.max(avgDailyNeed * 1.5, ...allDays.map(d => (d.rain_in || d.predicted_rain_in || 0) + (d.watered_in || 0)));

    const pastHtml = pastDays.map(d => {
      const rain = d.rain_in || 0, watered = d.watered_in || 0;
      const need = d.need_in || avgDailyNeed;
      const rainH = (rain / maxVal) * 100, wateredH = (watered / maxVal) * 100, needH = (need / maxVal) * 100;
      const dateLabel = d.date ? new Date(d.date + 'T12:00:00').toLocaleDateString('en-US',{weekday:'narrow'}) : '';
      const tempLabel = d.temp_high_f ? `${Math.round(d.temp_high_f)}°` : '';
      return `<div class="hydration-day" title="${d.date}: Rain ${rain.toFixed(2)}&quot; + Watered ${watered.toFixed(2)}&quot; / Need ${need.toFixed(2)}&quot;">
        <div class="hydration-day-bars">
          <div class="hydration-day-fill hydration-day-rain" style="height:${rainH}%"></div>
          <div class="hydration-day-fill hydration-day-watered" style="height:${wateredH}%;bottom:${rainH}%"></div>
          <div class="hydration-day-need-line" style="bottom:${needH}%"></div>
        </div>
        <div class="hydration-day-label">${dateLabel}</div>
        <div class="hydration-day-temp">${tempLabel}</div>
      </div>`;
    }).join('');

    const futureHtml = futureDays.map(d => {
      const rain = d.predicted_rain_in || 0, need = d.predicted_need_in || avgDailyNeed;
      const rainH = (rain / maxVal) * 100, needH = (need / maxVal) * 100;
      const dateLabel = d.date ? new Date(d.date + 'T12:00:00').toLocaleDateString('en-US',{weekday:'narrow'}) : '';
      const tempLabel = d.temp_high_f ? `${Math.round(d.temp_high_f)}°` : '';
      return `<div class="hydration-day hydration-day-forecast" title="${d.date}: Predicted ${rain.toFixed(2)}&quot; / Need ${need.toFixed(2)}&quot;">
        <div class="hydration-day-bars">
          <div class="hydration-day-fill hydration-day-rain hydration-forecast-fill" style="height:${rainH}%"></div>
          <div class="hydration-day-need-line" style="bottom:${needH}%"></div>
        </div>
        <div class="hydration-day-label" style="opacity:0.6">${dateLabel}</div>
        <div class="hydration-day-temp" style="opacity:0.6">${tempLabel}</div>
      </div>`;
    }).join('');

    return `<div class="hydration-timeline-divider-wrap">
      <div class="hydration-timeline-past">${pastHtml}</div>
      <div class="hydration-timeline-divider"></div>
      <div class="hydration-timeline-future">${futureHtml}</div>
    </div>`;
  },
};
