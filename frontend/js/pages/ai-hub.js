/** AI Hub — Assess + Coach + Diagnose in one tabbed view */
const AIHubPage = {
  activeTab: 'assess',

  TABS: [
    { id: 'assess',   label: 'Assess Yard' },
    { id: 'coach',    label: 'Lawn Coach' },
    { id: 'diagnose', label: 'Photo Diagnose' },
  ],

  async render(container, opts = {}) {
    this.activeTab = opts.tab || 'assess';
    this._container = container;

    container.innerHTML = `
      <div class="hub-header anim-fade-in">
        <h1 class="hub-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="22" height="22" style="flex-shrink:0">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
          </svg>
          AI Tools
        </h1>
      </div>
      <div class="hub-tabs-bar" id="aiHubTabs">
        ${this.TABS.map(t => `
          <button class="hub-tab${t.id === this.activeTab ? ' active' : ''}" data-tab="${t.id}">${t.label}</button>
        `).join('')}
      </div>
      <div id="aiHubContent" class="anim-fade-in-up"></div>`;

    document.getElementById('aiHubTabs').addEventListener('click', (e) => {
      const btn = e.target.closest('.hub-tab');
      if (!btn || btn.dataset.tab === this.activeTab) return;
      this.activeTab = btn.dataset.tab;
      document.querySelectorAll('#aiHubTabs .hub-tab').forEach(b =>
        b.classList.toggle('active', b.dataset.tab === this.activeTab));
      this._renderTab();
    });

    await this._renderTab();
  },

  async _renderTab() {
    const el = document.getElementById('aiHubContent');
    if (!el) return;
    el.innerHTML = '<div class="loading-center" style="min-height:30vh"><div class="spinner"></div></div>';
    try {
      switch (this.activeTab) {
        case 'assess':   await AssessmentPage.render(el); break;
        case 'coach':    await WhatIfPage.render(el); break;
        case 'diagnose': await DiagnosisPage.render(el); break;
      }
    } catch (e) {
      el.innerHTML = `<div class="empty-state"><div class="empty-state-icon">⚠️</div><p class="text-muted">${e.message}</p></div>`;
    }
  },

  switchTab(tab) {
    this.activeTab = tab;
    document.querySelectorAll('#aiHubTabs .hub-tab').forEach(b =>
      b.classList.toggle('active', b.dataset.tab === tab));
    this._renderTab();
  },
};
