/** Activity History / Journal Page */
const HistoryPage = {
  async render(container) {
    container.innerHTML = `
      <div class="section-header anim-fade-in">
        <h1 class="section-title">📋 Activity Journal</h1>
      </div>

      <div class="anim-fade-in-up anim-delay-1" style="display:flex;gap:var(--space-sm);margin-bottom:var(--space-lg);overflow-x:auto;padding-bottom:var(--space-sm)">
        <button class="btn btn-sm btn-primary filter-btn" data-filter="">All</button>
        ${Object.entries(Fmt.ACTIVITY_META).slice(0, 8).map(([k, v]) =>
          `<button class="btn btn-sm btn-secondary filter-btn" data-filter="${k}">${v.icon} ${v.label}</button>`
        ).join('')}
      </div>

      <div id="historyList" class="anim-fade-in-up anim-delay-2">
        <div class="loading-center"><div class="spinner"></div></div>
      </div>
    `;

    container.querySelectorAll('.filter-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        container.querySelectorAll('.filter-btn').forEach(b => b.classList.replace('btn-primary', 'btn-secondary'));
        btn.classList.replace('btn-secondary', 'btn-primary');
        this._loadActivities(btn.dataset.filter);
      });
    });

    await this._loadActivities();
  },

  async _loadActivities(type = '') {
    const el = document.getElementById('historyList');
    try {
      const params = {};
      if (type) params.activity_type = type;
      const activities = await API.getActivities(params);

      if (!activities.length) {
        el.innerHTML = `<div class="empty-state"><div class="empty-state-icon">📝</div><div class="empty-state-title">No Activities</div><p class="text-muted">Log your first lawn care activity to start tracking!</p></div>`;
        return;
      }

      el.innerHTML = activities.map(a => `
        <div class="card" style="position:relative">
          <div style="display:flex;gap:var(--space-md)">
            <div class="timeline-icon">${Fmt.activityIcon(a.activity_type)}</div>
            <div style="flex:1;min-width:0">
              <div style="display:flex;justify-content:space-between;align-items:flex-start">
                <div>
                  <div style="font-weight:var(--fw-semibold)">${Fmt.activityLabel(a.activity_type)}</div>
                  <div class="text-muted" style="font-size:var(--fs-xs)">${Fmt.relativeDate(a.date)}${a.zone_name ? ` · ${a.zone_name}` : ''}</div>
                </div>
                ${a.health_score ? `<div class="health-score" style="background:${Fmt.healthColor(a.health_score)}">${a.health_score}</div>` : ''}
              </div>
              ${a.notes ? `<div class="text-secondary mt-sm" style="font-size:var(--fs-sm)">${a.notes}</div>` : ''}
              ${a.products_used && a.products_used.length ? `<div class="mt-sm">${a.products_used.map(p => `<span class="badge badge-info" style="margin-right:4px">${p.name || p}</span>`).join('')}</div>` : ''}
            </div>
          </div>
          <button class="btn btn-ghost btn-sm" style="position:absolute;top:var(--space-sm);right:var(--space-sm)" onclick="HistoryPage._delete(${a.id})">🗑️</button>
        </div>
      `).join('');
    } catch (e) { Toast.error(e.message); }
  },

  async _delete(id) {
    if (!await Modal.confirm({ title: 'Delete Activity?', message: 'This activity record will be permanently deleted.', confirmText: 'Delete', variant: 'danger' })) return;
    try {
      await API.deleteActivity(id);
      Toast.success('Deleted');
      await this._loadActivities();
    } catch (e) { Toast.error(e.message); }
  },
};
