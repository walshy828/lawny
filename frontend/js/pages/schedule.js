/** Schedule Page */
const SchedulePage = {
  async render(container) {
    container.innerHTML = `
      <div class="section-header anim-fade-in">
        <h1 class="section-title">📅 Maintenance Schedule</h1>
        <button class="btn btn-primary btn-sm" id="addScheduleBtn">+ Add</button>
      </div>
      <div id="scheduleList" class="anim-fade-in-up anim-delay-1">
        <div class="loading-center"><div class="spinner"></div></div>
      </div>`;

    document.getElementById('addScheduleBtn').addEventListener('click', () => this._showAddForm());
    await this._loadSchedules();
  },

  async _loadSchedules() {
    try {
      const schedules = await API.getSchedules();
      const el = document.getElementById('scheduleList');

      if (!schedules.length) {
        el.innerHTML = `
          <div class="empty-state">
            <div class="empty-state-icon">📅</div>
            <div class="empty-state-title">No Schedules Yet</div>
            <p class="text-muted">Set up recurring maintenance to stay on track.</p>
          </div>`;
        return;
      }

      el.innerHTML = schedules.map(s => {
        const meta = Fmt.ACTIVITY_META[s.activity_type] || Fmt.ACTIVITY_META.other;
        const dueText = s.is_overdue ? `${Math.abs(s.days_until_due)} days overdue` :
          s.days_until_due === 0 ? 'Due today' :
          s.days_until_due === null ? 'Not scheduled' :
          `in ${s.days_until_due} days`;

        return `
          <div class="card" style="opacity:${s.is_active ? 1 : 0.5}">
            <div class="card-header">
              <div style="display:flex;align-items:center;gap:var(--space-sm)">
                <span>${meta.icon}</span>
                <span class="card-title">${meta.label}</span>
                ${s.zone_name ? `<span class="badge badge-accent">${s.zone_name}</span>` : ''}
              </div>
              <div style="display:flex;gap:var(--space-xs)">
                <button class="btn btn-ghost btn-sm" onclick="SchedulePage._complete(${s.id})" title="Complete">✓</button>
                <button class="btn btn-ghost btn-sm" onclick="SchedulePage._delete(${s.id})" title="Delete">🗑️</button>
              </div>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <div>
                <div class="text-secondary" style="font-size:var(--fs-sm)">Every ${s.frequency_days} days</div>
                <div class="${s.is_overdue ? 'text-accent' : 'text-muted'}" style="font-size:var(--fs-xs);margin-top:2px;${s.is_overdue ? 'color:var(--color-danger)' : ''}">${dueText}</div>
              </div>
              ${s.last_completed ? `<div class="text-muted" style="font-size:var(--fs-xs)">Last: ${Fmt.date(s.last_completed)}</div>` : ''}
            </div>
          </div>`;
      }).join('');
    } catch (e) { Toast.error(e.message); }
  },

  _showAddForm() {
    const typeOptions = Object.entries(Fmt.ACTIVITY_META).map(([k, v]) =>
      `<option value="${k}">${v.icon} ${v.label}</option>`).join('');

    const todayISO = new Date().toLocaleDateString('en-CA'); // YYYY-MM-DD in local time

    Modal.show('New Schedule', `
      <div class="form-group">
        <label class="form-label">Activity Type</label>
        <select class="form-select" id="schedType">${typeOptions}</select>
      </div>
      <div class="form-group">
        <label class="form-label">Frequency (days)</label>
        <input type="number" class="form-input" id="schedFreq" value="7" min="1">
      </div>
      <div class="form-group">
        <label class="form-label">First occurrence</label>
        <input type="date" class="form-input" id="schedStart" value="${todayISO}">
      </div>
      <div class="form-group">
        <label class="form-label">Notes (optional)</label>
        <textarea class="form-textarea" id="schedNotes" placeholder="Any notes..."></textarea>
      </div>
      <button class="btn btn-primary btn-block" id="schedSaveBtn">Create Schedule</button>
    `, {
      onMount: () => {
        document.getElementById('schedSaveBtn').addEventListener('click', async () => {
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
            await this._loadSchedules();
          } catch (e) { Toast.error(e.message); }
        });
      }
    });
  },

  async _complete(id) {
    try {
      await API.completeSchedule(id);
      Toast.success('Completed! Next due date updated.');
      await this._loadSchedules();
    } catch (e) { Toast.error(e.message); }
  },

  async _delete(id) {
    if (!await Modal.confirm({ title: 'Delete Schedule?', message: 'This recurring schedule will be permanently deleted.', confirmText: 'Delete', variant: 'danger' })) return;
    try {
      await API.deleteSchedule(id);
      Toast.success('Schedule deleted');
      await this._loadSchedules();
    } catch (e) { Toast.error(e.message); }
  },
};
