/** Plan Page — unified schedule/calendar across all programs and schedules */
const PlanPage = {
  view: 'agenda',
  data: null,
  calYear: null,
  calMonth: null,
  weekStart: null,
  listFilter: 'all',
  selectedDay: null,
  conflicts: null,
  _tooltipHideTimer: null,

  MONTH_NAMES: ['January','February','March','April','May','June','July','August','September','October','November','December'],
  DAY_NAMES: ['Su','Mo','Tu','We','Th','Fr','Sa'],

  SOURCE_COLORS: {
    lawn_program: 'var(--color-accent)',
    fertilizer:   '#FAB005',
    schedule:     '#339AF0',
    activity:     'var(--text-muted)',
  },

  STATUS_META: {
    overdue:  { label: 'Overdue',  color: 'var(--color-danger)',  bg: 'var(--color-danger-bg)' },
    due:      { label: 'Due',      color: 'var(--color-warning)', bg: 'var(--color-warning-bg)' },
    upcoming: { label: 'Upcoming', color: 'var(--color-accent)',  bg: 'rgba(82,183,136,0.12)' },
    done:     { label: 'Done',     color: 'var(--text-muted)',    bg: 'var(--bg-elevated)' },
    skipped:  { label: 'Skipped',  color: 'var(--text-muted)',    bg: 'var(--bg-elevated)' },
  },

  // Chemical/timing incompatibilities [type1, type2, max_days_apart]
  CONFLICT_RULES: [
    ['weed_control',  'fertilize',  3],
    ['post_emergent', 'fertilize',  3],
    ['pre_emergent',  'overseed',  14],
    ['post_emergent', 'overseed',  21],
    ['fungicide',     'fertilize',  3],
    ['lime',          'fertilize',  7],
    ['weed_control',  'overseed',  14],
    ['pest_control',  'fertilize',  3],
  ],

  // ── Entry ────────────────────────────────────────────────────────
  async render(container, opts = {}) {
    const today = new Date();
    this.calYear  = today.getFullYear();
    this.calMonth = today.getMonth();
    this.weekStart = this._weekOf(today);
    this.selectedDay = null;
    this.conflicts = null;

    // Support opts.tab for direct deep-linking to recurring tab
    if (opts.tab === 'recurring') this.view = 'recurring';

    container.innerHTML = `
      <div id="planHeader" class="plan-header anim-fade-in">
        <h1 class="section-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="20" height="20" style="display:inline;vertical-align:middle;margin-right:6px">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
          </svg>
          Plan
        </h1>
        <div class="plan-view-tabs" id="planViewTabs">
          <button class="plan-tab${this.view === 'agenda' ? ' active' : ''}" data-view="agenda">Agenda</button>
          <button class="plan-tab${this.view === 'month' ? ' active' : ''}" data-view="month">Month</button>
          <button class="plan-tab${this.view === 'week' ? ' active' : ''}" data-view="week">Week</button>
          <button class="plan-tab${this.view === 'recurring' ? ' active' : ''}" data-view="recurring">Recurring</button>
        </div>
      </div>
      <div class="plan-legend anim-fade-in" id="planLegend">
        <span class="plan-legend-item"><span class="plan-legend-dot" style="background:var(--color-accent)"></span>Program</span>
        <span class="plan-legend-item"><span class="plan-legend-dot" style="background:#FAB005"></span>Fertilizer</span>
        <span class="plan-legend-item"><span class="plan-legend-dot" style="background:#339AF0"></span>Schedule</span>
        <span class="plan-legend-item"><span class="plan-legend-dot" style="background:var(--text-muted)"></span>History</span>
      </div>
      <div id="planSummary" class="plan-summary anim-fade-in-up anim-delay-1"></div>
      <div id="planBody" class="anim-fade-in-up anim-delay-2">
        <div class="loading-center"><div class="spinner"></div></div>
      </div>`;

    document.getElementById('planViewTabs').addEventListener('click', e => {
      const btn = e.target.closest('.plan-tab');
      if (btn && btn.dataset.view !== this.view) this._setView(btn.dataset.view);
    });

    if (this.view === 'recurring') {
      // Hide legend for recurring tab — it's not a timeline view
      document.getElementById('planLegend').style.display = 'none';
      document.getElementById('planSummary').style.display = 'none';
      await this._renderRecurring();
    } else {
      await this._load();
    }
  },

  async _load() {
    try {
      this.data = await API.getTimeline({ include_history: true, history_days: 90 });
      this.conflicts = this._detectConflicts(this.data.items || []);
      this._renderSummary();
      this._renderView();
    } catch (e) {
      document.getElementById('planBody').innerHTML =
        `<div class="empty-state"><div class="empty-state-icon">📅</div>
         <div class="empty-state-title">Could not load plan</div>
         <p class="text-muted">${e.message}</p></div>`;
    }
  },

  _renderSummary() {
    const { summary } = this.data;
    const el = document.getElementById('planSummary');
    if (!summary) { el.innerHTML = ''; return; }
    const chips = [];
    if (summary.overdue)  chips.push(`<span class="plan-summary-chip overdue">${summary.overdue} overdue</span>`);
    if (summary.due)      chips.push(`<span class="plan-summary-chip due">${summary.due} due</span>`);
    if (summary.upcoming) chips.push(`<span class="plan-summary-chip upcoming">${summary.upcoming} upcoming</span>`);
    if (summary.done)     chips.push(`<span class="plan-summary-chip done">${summary.done} done</span>`);
    el.innerHTML = chips.length ? `<div class="plan-summary-row">${chips.join('')}</div>` : '';
  },

  _setView(view) {
    this.view = view;
    this.selectedDay = null;
    document.querySelectorAll('.plan-tab').forEach(b => b.classList.toggle('active', b.dataset.view === view));
    const legend = document.getElementById('planLegend');
    const summary = document.getElementById('planSummary');
    if (legend) legend.style.display = view === 'recurring' ? 'none' : '';
    if (summary) summary.style.display = view === 'recurring' ? 'none' : '';
    this._renderView();
  },

  _renderView() {
    switch (this.view) {
      case 'agenda':    this._renderAgenda();    break;
      case 'month':     this._renderMonth();     break;
      case 'week':      this._renderWeek();      break;
      case 'recurring': this._renderRecurring(); break;
    }
  },

  // ── Recurring Schedules Tab ──────────────────────────────────────
  async _renderRecurring() {
    const el = document.getElementById('planBody');
    if (!el) return;
    el.innerHTML = '<div class="loading-center" style="padding:var(--space-xl)"><div class="spinner"></div></div>';
    try {
      const schedules = await API.getSchedules();
      const addBtn = `<button class="btn btn-primary btn-sm" id="recurAddBtn">+ Add Schedule</button>`;

      if (!schedules.length) {
        el.innerHTML = `
          <div class="empty-state">
            <div class="empty-state-icon">🔁</div>
            <div class="empty-state-title">No Recurring Schedules</div>
            <p class="text-muted">Set up recurring tasks — mowing, watering, inspection — to stay on track.</p>
            <div style="margin-top:var(--space-lg)">${addBtn}</div>
          </div>`;
      } else {
        el.innerHTML = `
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:var(--space-md)">
            <span class="text-secondary" style="font-size:var(--fs-sm)">${schedules.length} recurring task${schedules.length !== 1 ? 's' : ''}</span>
            ${addBtn}
          </div>
          ${schedules.map(s => {
            const meta = Fmt.ACTIVITY_META[s.activity_type] || Fmt.ACTIVITY_META.other;
            const dueText = s.is_overdue ? `${Math.abs(s.days_until_due)}d overdue` :
              s.days_until_due === 0 ? 'Due today' :
              s.days_until_due == null ? 'Not scheduled' :
              `in ${s.days_until_due}d`;
            const dueColor = s.is_overdue ? 'var(--color-danger)' : s.days_until_due === 0 ? 'var(--color-warning)' : 'var(--text-muted)';
            return `
              <div class="card" style="${s.is_active ? '' : 'opacity:0.5'}">
                <div style="display:flex;align-items:center;gap:var(--space-md)">
                  <div style="font-size:1.4rem">${meta.icon}</div>
                  <div style="flex:1;min-width:0">
                    <div style="font-weight:var(--fw-semibold);font-size:var(--fs-sm)">${meta.label}</div>
                    <div class="text-muted" style="font-size:var(--fs-xs)">Every ${s.frequency_days} days</div>
                    ${s.zone_name ? `<span class="badge badge-accent" style="margin-top:2px">${s.zone_name}</span>` : ''}
                  </div>
                  <div style="text-align:right;flex-shrink:0">
                    <div style="font-size:var(--fs-sm);font-weight:var(--fw-semibold);color:${dueColor}">${dueText}</div>
                    ${s.last_completed ? `<div class="text-muted" style="font-size:var(--fs-xs)">Last: ${Fmt.date(s.last_completed)}</div>` : ''}
                  </div>
                  <div style="display:flex;flex-direction:column;gap:4px;margin-left:var(--space-sm)">
                    <button class="btn btn-ghost btn-sm" onclick="PlanPage._completeRecurring(${s.id})" title="Mark done">✓</button>
                    <button class="btn btn-ghost btn-sm" onclick="PlanPage._deleteRecurring(${s.id})" title="Delete">✕</button>
                  </div>
                </div>
              </div>`;
          }).join('')}`;
      }

      document.getElementById('recurAddBtn')?.addEventListener('click', () => this._showAddScheduleForm());
    } catch (e) {
      el.innerHTML = `<div class="text-muted text-center" style="padding:var(--space-xl)">${e.message}</div>`;
    }
  },

  _showAddScheduleForm() {
    const typeOptions = Object.entries(Fmt.ACTIVITY_META).map(([k, v]) =>
      `<option value="${k}">${v.icon} ${v.label}</option>`).join('');

    const todayISO = new Date().toLocaleDateString('en-CA'); // YYYY-MM-DD in local time

    Modal.show('New Recurring Schedule', `
      <div class="form-group">
        <label class="form-label">Activity Type</label>
        <select class="form-select" id="schedType">${typeOptions}</select>
      </div>
      <div class="form-group">
        <label class="form-label">Repeat every (days)</label>
        <input type="number" class="form-input" id="schedFreq" value="7" min="1">
      </div>
      <div class="form-group">
        <label class="form-label">First occurrence</label>
        <input type="date" class="form-input" id="schedStart" value="${todayISO}">
      </div>
      <div class="form-group">
        <label class="form-label">Notes (optional)</label>
        <textarea class="form-textarea" id="schedNotes" placeholder="Any notes..." rows="2"></textarea>
      </div>
      <button class="btn btn-primary btn-block" id="schedSaveBtn">Create Schedule</button>
    `);
    setTimeout(() => {
      document.getElementById('schedSaveBtn')?.addEventListener('click', async () => {
        try {
          const startVal = document.getElementById('schedStart').value;
          await API.createSchedule({
            activity_type: document.getElementById('schedType').value,
            frequency_days: parseInt(document.getElementById('schedFreq').value),
            notes: document.getElementById('schedNotes').value || null,
            next_due: startVal ? startVal + 'T00:00:00' : null,
          });
          Modal.close();
          Toast.success('Schedule created');
          await this._renderRecurring();
        } catch (e) { Toast.error(e.message); }
      });
    }, 50);
  },

  async _completeRecurring(id) {
    try {
      await API.completeSchedule(id);
      Toast.success('Done! Next due date updated.');
      await this._renderRecurring();
    } catch (e) { Toast.error(e.message); }
  },

  async _deleteRecurring(id) {
    if (!await Modal.confirm({ title: 'Delete Schedule?', message: 'This recurring schedule will be permanently deleted.', confirmText: 'Delete', variant: 'danger' })) return;
    try {
      await API.deleteSchedule(id);
      Toast.success('Deleted');
      await this._renderRecurring();
    } catch (e) { Toast.error(e.message); }
  },

  // ── Conflict Detection ───────────────────────────────────────────
  _detectConflicts(items) {
    const conflicted = new Set();
    const pending = items.filter(i =>
      i.status !== 'done' && i.status !== 'skipped' && i.source !== 'activity'
    );

    for (let i = 0; i < pending.length; i++) {
      for (let j = i + 1; j < pending.length; j++) {
        const a = pending[i], b = pending[j];
        const dateA = new Date((a.planned_date || a.date) + 'T00:00:00');
        const dateB = new Date((b.planned_date || b.date) + 'T00:00:00');
        const daysDiff = Math.abs((dateA - dateB) / 86400000);

        for (const [t1, t2, maxDays] of this.CONFLICT_RULES) {
          const match = (a.activity_type === t1 && b.activity_type === t2) ||
                        (a.activity_type === t2 && b.activity_type === t1);
          if (match && daysDiff <= maxDays) {
            conflicted.add(a.id);
            conflicted.add(b.id);
          }
        }
      }
    }
    return conflicted;
  },

  // ── Agenda View ──────────────────────────────────────────────────
  _renderAgenda() {
    const { items, today: todayStr } = this.data;
    const todayDate = new Date(todayStr + 'T00:00:00');
    const weekEnd   = new Date(todayDate); weekEnd.setDate(todayDate.getDate() + 7);
    const el = document.getElementById('planBody');

    const actionable = items.filter(i => i.source !== 'activity');

    if (!actionable.length) {
      el.innerHTML = `<div class="empty-state">
        <div class="empty-state-icon">🌿</div>
        <div class="empty-state-title">All caught up!</div>
        <p class="text-muted">No scheduled tasks. Add a program or recurring schedule to get started.</p>
        <button class="btn btn-primary" style="margin-top:var(--space-lg)" onclick="QuickLog.open()">+ Log Activity</button>
      </div>`;
      return;
    }

    const pending = actionable.filter(i => i.status !== 'done' && i.status !== 'skipped');
    const history = items.filter(i => i.status === 'done' || i.status === 'skipped' || i.source === 'activity')
                         .sort((a, b) => b.date.localeCompare(a.date));

    // Partition pending into time buckets
    const overdue      = pending.filter(i => i.status === 'overdue');
    const dueNow       = pending.filter(i => i.status === 'due' && (i.planned_date || i.date) <= todayStr);
    const thisWeekSet  = new Set([...overdue, ...dueNow].map(i => i.id));

    const thisWeek = pending.filter(i => {
      if (thisWeekSet.has(i.id)) return false;
      const d = new Date((i.planned_date || i.date) + 'T00:00:00');
      return d > todayDate && d <= weekEnd;
    });
    thisWeek.forEach(i => thisWeekSet.add(i.id));

    const dueThisMonth = pending.filter(i => i.status === 'due' && !thisWeekSet.has(i.id));

    const upcoming = pending.filter(i => i.status === 'upcoming' && !thisWeekSet.has(i.id));

    const groups = [];
    const urgentItems = [...overdue, ...dueNow];
    if (urgentItems.length) {
      groups.push({ label: '⚠️ Overdue & Due Now', items: urgentItems, cls: 'group-overdue' });
    }
    if (thisWeek.length) {
      groups.push({ label: '📆 This Week', items: thisWeek, cls: 'group-due' });
    }
    if (dueThisMonth.length) {
      groups.push({ label: '🔔 Due This Month', items: dueThisMonth, cls: 'group-due' });
    }

    // Group upcoming by month
    const byMonth = {};
    upcoming.forEach(i => {
      const key = i.planned_date?.slice(0, 7) || i.date.slice(0, 7);
      (byMonth[key] = byMonth[key] || []).push(i);
    });
    Object.keys(byMonth).sort().forEach(key => {
      const [y, m] = key.split('-');
      groups.push({ label: `📅 ${this.MONTH_NAMES[parseInt(m) - 1]} ${y}`, items: byMonth[key], cls: 'group-upcoming' });
    });

    let html = '';

    // Global conflict banner
    const conflictCount = pending.filter(i => this.conflicts?.has(i.id)).length;
    if (conflictCount > 0) {
      html += `<div class="plan-conflict-banner">
        ⚠️ <strong>${conflictCount} items</strong> have potential scheduling conflicts — products applied too close together.
      </div>`;
    }

    html += groups.map(g => `
      <div class="plan-group ${g.cls}">
        <div class="plan-group-label">${g.label}</div>
        ${g.items.map(i => this._agendaCard(i)).join('')}
      </div>`).join('');

    if (history.length) {
      html += `
        <div class="plan-group group-history">
          <div class="plan-group-label" onclick="PlanPage._toggleHistory(this)" style="cursor:pointer">
            ✓ Completed &amp; History <span id="historyChevron">▼</span>
          </div>
          <div id="historyItems" style="display:none">
            ${history.slice(0, 50).map(i => this._agendaCard(i)).join('')}
          </div>
        </div>`;
    }

    html += `<div style="padding:var(--space-xl) 0;text-align:center">
      <button class="btn btn-secondary btn-sm" onclick="QuickLog.open()">+ Log Activity</button>
    </div>`;

    el.innerHTML = html;
  },

  _toggleHistory(labelEl) {
    const items = document.getElementById('historyItems');
    const chevron = document.getElementById('historyChevron');
    const shown = items.style.display !== 'none';
    items.style.display = shown ? 'none' : 'block';
    chevron.textContent = shown ? '▼' : '▲';
  },

  _agendaCard(item) {
    const srcColor = this.SOURCE_COLORS[item.source] || 'var(--border-medium)';
    const statusMeta = this.STATUS_META[item.status] || this.STATUS_META.upcoming;
    const isDone = item.status === 'done' || item.status === 'skipped';
    const hasConflict = !isDone && this.conflicts?.has(item.id);

    const dateLabel = this._itemDateLabel(item);
    const priorityDot = item.priority === 'critical' ? '<span class="priority-dot critical"></span>' :
                        item.priority === 'high'     ? '<span class="priority-dot high"></span>' : '';

    const conflictRow = hasConflict
      ? `<div class="agenda-card-conflict-row">⚠️ Potential scheduling conflict with another task</div>`
      : '';

    const actions = !isDone && item.can_complete ? `
      <div class="agenda-card-actions">
        <button class="btn btn-ghost btn-sm" onclick="PlanPage._complete('${item.id}')">✓ Done</button>
        <button class="btn btn-ghost btn-sm" style="color:var(--text-muted)" onclick="PlanPage._skip('${item.id}')">Skip</button>
      </div>` : '';

    const chipStyle = `color:${srcColor};border-color:${srcColor}40;background:${srcColor}18`;

    return `
      <div class="agenda-card ${isDone ? 'agenda-card-done' : ''} ${hasConflict ? 'agenda-card-has-conflict' : ''}"
           style="border-left-color:${srcColor}">
        <div class="agenda-card-header">
          <div class="agenda-card-left">
            <span class="agenda-card-icon">${item.icon}</span>
            <div>
              <div class="agenda-card-title">${priorityDot}${item.title}</div>
              ${item.subtitle ? `<div class="agenda-card-sub">${item.subtitle}</div>` : ''}
              ${item.product_name && item.product_name !== item.title ? `<div class="agenda-card-sub">📦 ${item.product_name}</div>` : ''}
              ${item.zone_name ? `<div class="agenda-card-sub">📍 ${item.zone_name}</div>` : ''}
            </div>
          </div>
          <div class="agenda-card-right">
            <span class="plan-badge" style="color:${statusMeta.color};background:${statusMeta.bg}">${statusMeta.label}</span>
            <div class="agenda-card-date">${dateLabel}</div>
            <span class="source-chip" style="${chipStyle}">${item.source_label}</span>
          </div>
        </div>
        ${conflictRow}
        ${actions}
      </div>`;
  },

  _itemDateLabel(item) {
    const d = item.completed_date || item.date;
    if (!d) return '';
    const dt = new Date(d + 'T00:00:00');
    const today = new Date(); today.setHours(0, 0, 0, 0);
    const diff = Math.round((dt - today) / 86400000);
    if (diff === 0)  return 'Today';
    if (diff === -1) return 'Yesterday';
    if (diff === 1)  return 'Tomorrow';
    if (diff > 1 && diff <= 7)  return `in ${diff} days`;
    if (diff < -1 && diff >= -7) return `${Math.abs(diff)} days ago`;
    return dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  },

  // ── Monthly Calendar View ────────────────────────────────────────
  _renderMonth() {
    const el = document.getElementById('planBody');
    const year = this.calYear;
    const month = this.calMonth;
    const monthStr = `${year}-${String(month + 1).padStart(2, '0')}`;

    const dayMap = {};
    (this.data.items || []).forEach(item => {
      const d = item.planned_date || item.date;
      if (d && d.slice(0, 7) === monthStr) {
        (dayMap[d] = dayMap[d] || []).push(item);
      }
    });

    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const todayStr = this.data.today;
    const todayObj = new Date(todayStr + 'T00:00:00');
    const isCurrentMonth = year === todayObj.getFullYear() && month === todayObj.getMonth();

    let grid = '';
    let cell = 0;
    for (let i = 0; i < firstDay; i++) { grid += '<div class="cal-cell cal-empty"></div>'; cell++; }

    for (let d = 1; d <= daysInMonth; d++) {
      const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
      const dayItems = dayMap[dateStr] || [];
      const isToday    = dateStr === todayStr;
      const isPast     = !isToday && dateStr < todayStr;
      const isSelected = dateStr === this.selectedDay;
      const hasConflict = dayItems.some(i => this.conflicts?.has(i.id));

      const MAX_CHIPS = 5;
      const chips = dayItems.slice(0, MAX_CHIPS).map(i => this._calIconChip(i)).join('');
      const overflow = dayItems.length > MAX_CHIPS
        ? `<div class="cal-overflow-count" onclick="PlanPage._selectDay('${dateStr}');event.stopPropagation()">+${dayItems.length - MAX_CHIPS}</div>`
        : '';

      grid += `
        <div class="cal-cell ${isToday ? 'cal-today' : ''} ${isPast ? 'cal-past' : ''} ${isSelected ? 'cal-selected' : ''}"
             onclick="PlanPage._selectDay('${dateStr}')">
          <span class="cal-day-num${isToday ? ' cal-today-badge' : ''}">${d}</span>
          ${hasConflict ? '<span class="cal-conflict-indicator">!</span>' : ''}
          <div class="cal-icon-row">${chips}${overflow}</div>
        </div>`;
      cell++;
    }
    while (cell % 7 !== 0) { grid += '<div class="cal-cell cal-empty"></div>'; cell++; }

    const dayDetail = this.selectedDay
      ? this._renderDayDetail(this.selectedDay, dayMap[this.selectedDay] || [])
      : '';

    const todayBtn = !isCurrentMonth
      ? `<button class="btn btn-ghost btn-sm plan-today-btn" onclick="PlanPage._goToToday()">Today</button>`
      : '';

    el.innerHTML = `
      <div class="cal-nav">
        <button class="btn btn-ghost btn-sm" onclick="PlanPage._prevMonth()">‹</button>
        <span class="cal-month-label">${this.MONTH_NAMES[month]} ${year}</span>
        <div style="display:flex;gap:4px;align-items:center">
          ${todayBtn}
          <button class="btn btn-ghost btn-sm" onclick="PlanPage._nextMonth()">›</button>
        </div>
      </div>
      <div class="cal-frame">
        <div class="cal-dow-bar">
          ${this.DAY_NAMES.map(d => `<div class="cal-dow">${d}</div>`).join('')}
        </div>
        <div class="cal-grid">${grid}</div>
      </div>
      <div id="calDayDetail">${dayDetail}</div>`;
  },

  _selectDay(dateStr) {
    this._hideTooltip();
    this.selectedDay = this.selectedDay === dateStr ? null : dateStr;
    this._renderMonth();
  },

  _prevMonth() {
    this._hideTooltip();
    this.calMonth--;
    if (this.calMonth < 0) { this.calMonth = 11; this.calYear--; }
    this.selectedDay = null;
    this._renderMonth();
  },

  _nextMonth() {
    this._hideTooltip();
    this.calMonth++;
    if (this.calMonth > 11) { this.calMonth = 0; this.calYear++; }
    this.selectedDay = null;
    this._renderMonth();
  },

  _goToToday() {
    const today = new Date();
    this.calYear   = today.getFullYear();
    this.calMonth  = today.getMonth();
    this.weekStart = this._weekOf(today);
    this.selectedDay = null;
    this._renderView();
  },

  // ── Calendar Icon Chips & Tooltips ──────────────────────────────
  _calIconChip(item) {
    const STATUS_CLS = {
      overdue:  'chip-overdue',
      due:      'chip-due',
      upcoming: 'chip-upcoming',
      done:     'chip-done',
      skipped:  'chip-skipped',
    };
    const cls    = 'cal-icon-chip ' + (STATUS_CLS[item.status] || 'chip-upcoming');
    const safeId = item.id.replace(/'/g, "\\'");
    return `<div class="${cls}" data-item-id="${item.id}"
                 onmouseenter="PlanPage._showTooltip(event,'${safeId}')"
                 onmouseleave="PlanPage._scheduleHideTooltip()"
                 onclick="PlanPage._showItemDetail('${safeId}');event.stopPropagation()"
                 >${item.icon}</div>`;
  },

  _showTooltip(event, itemId) {
    clearTimeout(this._tooltipHideTimer);
    const item = (this.data?.items || []).find(i => i.id === itemId);
    if (!item) return;

    let tip = document.getElementById('calTooltip');
    if (!tip) {
      tip = document.createElement('div');
      tip.id = 'calTooltip';
      tip.className = 'cal-tooltip';
      tip.addEventListener('mouseenter', () => clearTimeout(this._tooltipHideTimer));
      tip.addEventListener('mouseleave', () => this._scheduleHideTooltip());
      document.body.appendChild(tip);
    }
    tip.classList.remove('cal-tooltip-visible');

    const sm         = this.STATUS_META[item.status] || this.STATUS_META.upcoming;
    const srcColor   = this.SOURCE_COLORS[item.source] || 'var(--border-medium)';
    const dateLabel  = item.planned_date
      ? new Date(item.planned_date + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
      : '';
    const navTarget  = this._itemNavTarget(item.source);
    const chipStyle  = `color:${srcColor};border-color:${srcColor}40;background:${srcColor}18`;

    tip.innerHTML = `
      <div class="cal-tooltip-title">${item.icon} ${item.title}</div>
      <div style="display:flex;gap:5px;align-items:center;margin-bottom:6px;flex-wrap:wrap">
        <span class="cal-tooltip-status" style="color:${sm.color};background:${sm.bg}">${sm.label}</span>
        <span class="source-chip" style="${chipStyle}">${item.source_label}</span>
      </div>
      ${item.subtitle ? `<div class="cal-tooltip-row">📝 ${item.subtitle}</div>` : ''}
      ${item.product_name && item.product_name !== item.title ? `<div class="cal-tooltip-row">📦 ${item.product_name}</div>` : ''}
      ${item.zone_name ? `<div class="cal-tooltip-row">📍 ${item.zone_name}</div>` : ''}
      ${dateLabel ? `<div class="cal-tooltip-row">📅 ${dateLabel}</div>` : ''}
      ${navTarget ? `<span class="cal-tooltip-nav" onclick="${navTarget}">View details →</span>` : ''}
    `;

    // Position after paint so offsetWidth/Height are available
    requestAnimationFrame(() => {
      const r  = event.currentTarget.getBoundingClientRect();
      const tw = tip.offsetWidth;
      const th = tip.offsetHeight;
      const vw = window.innerWidth;
      const vh = window.innerHeight;

      let left = r.left;
      let top  = r.bottom + 8;
      if (top + th > vh - 16)  top  = r.top - th - 8;
      if (left + tw > vw - 16) left = vw - tw - 16;
      if (left < 8)            left = 8;

      tip.style.left = left + 'px';
      tip.style.top  = top  + 'px';
      tip.classList.add('cal-tooltip-visible');
    });
  },

  _scheduleHideTooltip() {
    clearTimeout(this._tooltipHideTimer);
    this._tooltipHideTimer = setTimeout(() => this._hideTooltip(), 120);
  },

  _hideTooltip() {
    clearTimeout(this._tooltipHideTimer);
    document.getElementById('calTooltip')?.classList.remove('cal-tooltip-visible');
  },

  _itemNavTarget(source) {
    switch (source) {
      case 'lawn_program': return "App.navigate('lawn-program');PlanPage._hideTooltip()";
      case 'fertilizer':   return "App.navigate('fertilizer');PlanPage._hideTooltip()";
      case 'schedule':     return "App.navigate('schedule');PlanPage._hideTooltip()";
      case 'activity':     return "App.navigate('history');PlanPage._hideTooltip()";
      default: return null;
    }
  },

  _renderDayDetail(dateStr, items) {
    const dt    = new Date(dateStr + 'T00:00:00');
    const label = dt.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
    const addBtn = `<button class="btn btn-secondary btn-sm" onclick="QuickLog.open()" style="margin-bottom:var(--space-md)">+ Log Activity</button>`;

    if (!items.length) {
      return `<div class="cal-day-panel">
        <div class="cal-day-panel-title">${label}</div>
        ${addBtn}
        <p class="text-muted" style="font-size:var(--fs-sm)">No items scheduled.</p>
      </div>`;
    }
    return `<div class="cal-day-panel">
      <div class="cal-day-panel-title">${label}</div>
      ${addBtn}
      ${items.map(i => this._agendaCard(i)).join('')}
    </div>`;
  },

  // ── Weekly View ──────────────────────────────────────────────────
  _renderWeek() {
    const el = document.getElementById('planBody');
    const ws = this.weekStart;
    const days = Array.from({ length: 7 }, (_, i) => {
      const d = new Date(ws); d.setDate(ws.getDate() + i);
      return d;
    });

    const todayStr = this.data.today;
    const isCurrentWeek = days.some(d => d.toISOString().slice(0, 10) === todayStr);

    const dayMap = {};
    (this.data.items || []).forEach(item => {
      const d = item.planned_date || item.date;
      if (d) (dayMap[d] = dayMap[d] || []).push(item);
    });

    const rangeLabel = `${days[0].toLocaleDateString('en-US',{month:'short',day:'numeric'})} – ${days[6].toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'})}`;
    const todayBtn = !isCurrentWeek
      ? `<button class="btn btn-ghost btn-sm plan-today-btn" onclick="PlanPage._goToToday()">Today</button>`
      : '';

    const cols = days.map(day => {
      const dateStr = day.toISOString().slice(0, 10);
      const isToday = dateStr === todayStr;
      const dayItems = dayMap[dateStr] || [];

      const cards = dayItems.length
        ? dayItems.map(i => this._weekItemChip(i)).join('')
        : `<div class="week-empty-day" onclick="QuickLog.open()" title="Log activity">+</div>`;

      return `
        <div class="week-col ${isToday ? 'week-col-today' : ''}">
          <div class="week-col-header">
            <div class="week-dow">${this.DAY_NAMES[day.getDay()]}</div>
            <div class="week-daynum ${isToday ? 'week-today-num' : ''}">${day.getDate()}</div>
          </div>
          <div class="week-items">${cards}</div>
        </div>`;
    }).join('');

    el.innerHTML = `
      <div class="cal-nav">
        <button class="btn btn-ghost btn-sm" onclick="PlanPage._prevWeek()">‹</button>
        <span class="cal-month-label">${rangeLabel}</span>
        <div style="display:flex;gap:4px;align-items:center">
          ${todayBtn}
          <button class="btn btn-ghost btn-sm" onclick="PlanPage._nextWeek()">›</button>
        </div>
      </div>
      <div class="week-grid">${cols}</div>`;
  },

  _weekItemChip(item) {
    const srcColor = this.SOURCE_COLORS[item.source] || 'var(--border-medium)';
    const isDone = item.status === 'done' || item.status === 'skipped';
    const hasConflict = !isDone && this.conflicts?.has(item.id);
    return `
      <div class="week-chip ${isDone ? 'week-chip-done' : ''} ${hasConflict ? 'week-chip-conflict' : ''}"
           style="border-left-color:${srcColor}"
           onclick="PlanPage._showItemDetail('${item.id}')">
        <span>${item.icon}</span>
        <span class="week-chip-title">${item.title}</span>
        ${hasConflict ? '<span class="week-conflict-dot">!</span>' : ''}
      </div>`;
  },

  _prevWeek() {
    const d = new Date(this.weekStart); d.setDate(d.getDate() - 7);
    this.weekStart = d; this._renderWeek();
  },

  _nextWeek() {
    const d = new Date(this.weekStart); d.setDate(d.getDate() + 7);
    this.weekStart = d; this._renderWeek();
  },

  // ── List View ────────────────────────────────────────────────────
  _renderList() {
    const el = document.getElementById('planBody');
    const filters = [
      { key: 'all',     label: 'All' },
      { key: 'overdue', label: '⚠️ Overdue' },
      { key: 'due',     label: '🔔 Due' },
      { key: 'upcoming',label: '📆 Upcoming' },
      { key: 'done',    label: '✓ Done' },
    ];

    const base = this.data.items.filter(i => i.source !== 'activity');
    const filtered = this.listFilter === 'all'
      ? base
      : base.filter(i => i.status === this.listFilter);

    const chips = filters.map(f => `
      <button class="filter-chip ${this.listFilter === f.key ? 'active' : ''}"
              onclick="PlanPage._setListFilter('${f.key}')">${f.label}</button>`).join('');

    const cards = filtered.length
      ? filtered.map(i => this._agendaCard(i)).join('')
      : `<div class="empty-state"><div class="empty-state-icon">🎉</div>
         <div class="empty-state-title">Nothing here</div></div>`;

    el.innerHTML = `
      <div class="filter-chips">${chips}</div>
      <div class="list-items">${cards}</div>`;
  },

  _setListFilter(filter) {
    this.listFilter = filter;
    this._renderList();
  },

  // ── Item Detail Modal ────────────────────────────────────────────
  _showItemDetail(itemId) {
    this._hideTooltip();
    const item = (this.data?.items || []).find(i => i.id === itemId);
    if (!item) return;
    const statusMeta = this.STATUS_META[item.status] || this.STATUS_META.upcoming;
    const srcColor   = this.SOURCE_COLORS[item.source] || 'var(--border-medium)';
    const hasConflict = this.conflicts?.has(item.id);
    Modal.show(`${item.icon} ${item.title}`, `
      <div style="display:flex;gap:var(--space-sm);flex-wrap:wrap;margin-bottom:var(--space-md)">
        <span class="plan-badge" style="color:${statusMeta.color};background:${statusMeta.bg}">${statusMeta.label}</span>
        <span class="source-chip" style="color:${srcColor};border-color:${srcColor}40;background:${srcColor}18">${item.source_label}</span>
        ${item.priority ? `<span class="badge">${item.priority}</span>` : ''}
      </div>
      ${hasConflict ? `<div class="plan-conflict-banner" style="margin-bottom:var(--space-md)">⚠️ This item may conflict with another task scheduled nearby.</div>` : ''}
      ${item.subtitle ? `<p class="text-secondary" style="font-size:var(--fs-sm);margin-bottom:var(--space-md)">${item.subtitle}</p>` : ''}
      ${item.product_name ? `<p style="font-size:var(--fs-sm)">📦 <strong>Product:</strong> ${item.product_name}</p>` : ''}
      ${item.zone_name ? `<p style="font-size:var(--fs-sm)">📍 <strong>Zone:</strong> ${item.zone_name}</p>` : ''}
      ${item.completed_date ? `<p style="font-size:var(--fs-sm)">📅 <strong>Completed:</strong> ${new Date(item.completed_date + 'T00:00:00').toLocaleDateString('en-US',{month:'long',day:'numeric',year:'numeric'})}</p>` : ''}
      ${item.can_complete ? `
        <div style="display:flex;gap:var(--space-sm);margin-top:var(--space-xl)">
          <button class="btn btn-primary" style="flex:1" onclick="PlanPage._complete('${item.id}');Modal.close()">✓ Mark Done</button>
          <button class="btn btn-secondary" onclick="PlanPage._skip('${item.id}');Modal.close()">Skip</button>
        </div>` : ''}
    `);
  },

  // ── Completion Actions ───────────────────────────────────────────
  async _complete(itemId) {
    const item = (this.data?.items || []).find(i => i.id === itemId);
    if (!item) return;
    try {
      if (item.ref_type === 'LawnProgramStep') {
        await API.completeProgramStep(item.ref_program_id, item.ref_id);
      } else if (item.ref_type === 'FertilizerApplication') {
        await API.fertilizerApply(item.ref_step_id, { status: 'done' });
      } else if (item.ref_type === 'MaintenanceSchedule') {
        await API.completeSchedule(item.ref_id);
      } else { return; }
      Toast.success('Marked as done!');
      await this._load();
    } catch (e) { Toast.error(e.message); }
  },

  async _skip(itemId) {
    const item = (this.data?.items || []).find(i => i.id === itemId);
    if (!item) return;
    try {
      if (item.ref_type === 'LawnProgramStep') {
        await API.updateProgramStep(item.ref_program_id, item.ref_id, { status: 'skipped' });
      } else if (item.ref_type === 'FertilizerApplication') {
        await API.fertilizerApply(item.ref_step_id, { status: 'skipped' });
      } else { return; }
      Toast.success('Skipped');
      await this._load();
    } catch (e) { Toast.error(e.message); }
  },

  // ── Helpers ──────────────────────────────────────────────────────
  _weekOf(d) {
    const day = new Date(d);
    day.setHours(0, 0, 0, 0);
    day.setDate(day.getDate() - day.getDay());
    return day;
  },
};
