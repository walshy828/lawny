/** My Lawn Hub — Program + Fertilizer + Zones + Soil in one tabbed view */
const MyLawnPage = {
  activeTab: 'program',

  TABS: [
    { id: 'program',    label: 'Program' },
    { id: 'fertilizer', label: 'Fertilizer' },
    { id: 'zones',      label: 'Zones' },
    { id: 'soil',       label: 'Soil' },
  ],

  async render(container, opts = {}) {
    this.activeTab = opts.tab || 'program';
    this._container = container;

    container.innerHTML = `
      <div class="hub-header anim-fade-in">
        <h1 class="hub-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="22" height="22" style="flex-shrink:0">
            <path d="M12 22V12"/><path d="M12 12C12 7 7 4 3 6c4 1 7 4 9 6z"/><path d="M12 12c0-5 5-8 9-6-4 1-7 4-9 6z"/>
          </svg>
          My Lawn
        </h1>
        <button class="btn btn-ghost btn-sm btn-icon" onclick="App.navigate('settings')" title="Settings">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="18" height="18">
            <circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
          </svg>
        </button>
      </div>
      <div class="hub-tabs-bar" id="myLawnTabs">
        ${this.TABS.map(t => `
          <button class="hub-tab${t.id === this.activeTab ? ' active' : ''}" data-tab="${t.id}">${t.label}</button>
        `).join('')}
      </div>
      <div id="myLawnContent" class="anim-fade-in-up"></div>`;

    document.getElementById('myLawnTabs').addEventListener('click', (e) => {
      const btn = e.target.closest('.hub-tab');
      if (!btn || btn.dataset.tab === this.activeTab) return;
      this.activeTab = btn.dataset.tab;
      document.querySelectorAll('#myLawnTabs .hub-tab').forEach(b =>
        b.classList.toggle('active', b.dataset.tab === this.activeTab));
      this._renderTab();
    });

    await this._renderTab();
  },

  async _renderTab() {
    const el = document.getElementById('myLawnContent');
    if (!el) return;
    el.innerHTML = '<div class="loading-center" style="min-height:30vh"><div class="spinner"></div></div>';
    try {
      switch (this.activeTab) {
        case 'program':    await LawnProgramPage.render(el); break;
        case 'fertilizer': await FertilizerPage.render(el); break;
        case 'zones':      await LawnMapPage.render(el); break;
        case 'soil':       await SoilTestsPage.render(el); break;
      }
    } catch (e) {
      el.innerHTML = `<div class="empty-state"><div class="empty-state-icon">⚠️</div><p class="text-muted">${e.message}</p></div>`;
    }
  },

  // Allow sub-pages to re-render themselves within the hub
  reload(tab) {
    if (tab) this.activeTab = tab;
    document.querySelectorAll('#myLawnTabs .hub-tab').forEach(b =>
      b.classList.toggle('active', b.dataset.tab === this.activeTab));
    this._renderTab();
  },
};
