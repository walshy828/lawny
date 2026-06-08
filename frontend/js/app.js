/** Lawny SPA — Main application router */
const App = {
  currentPage: 'dashboard',
  contentEl: null,
  authenticated: false,

  async init() {
    this.contentEl = document.getElementById('pageContent');
    if (!this.contentEl) return;

    try {
      const pinCheck = await API.checkPinRequired();
      if (pinCheck.pin_required) { this.showPinOverlay(); return; }
    } catch (e) { /* API not ready */ }

    this.authenticated = true;
    this.renderNav();
    this.navigate('dashboard');
  },

  showPinOverlay() {
    const overlay = document.createElement('div');
    overlay.className = 'pin-overlay';
    overlay.innerHTML = `
      <div style="font-size:3rem;margin-bottom:var(--space-lg)">🌿</div>
      <div class="pin-title">Lawny</div>
      <input type="password" class="pin-input" id="pinInput" maxlength="10" placeholder="PIN" inputmode="numeric" autocomplete="off">
      <div class="pin-error" id="pinError"></div>`;
    document.body.appendChild(overlay);
    const input = document.getElementById('pinInput');
    input.focus();
    input.addEventListener('keyup', async (e) => {
      if (e.key === 'Enter') {
        try {
          const result = await API.verifyPin(input.value);
          if (result.valid) {
            overlay.remove();
            this.authenticated = true;
            this.renderNav();
            this.navigate('dashboard');
          } else {
            document.getElementById('pinError').textContent = 'Incorrect PIN';
            input.value = '';
          }
        } catch (err) { document.getElementById('pinError').textContent = 'Connection error'; }
      }
    });
  },

  renderNav() {
    const nav = document.getElementById('bottomNav');
    if (!nav) return;
    nav.innerHTML = `
      <button class="nav-item" data-page="dashboard">
        <svg class="nav-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>
        </svg>
        <span class="nav-label">Today</span>
      </button>
      <button class="nav-item" data-page="plan">
        <svg class="nav-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
        </svg>
        <span class="nav-label">Plan</span>
      </button>
      <button class="nav-item nav-add" data-page="quick-log">
        <div class="nav-add-btn">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" width="22" height="22">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
        </div>
        <span class="nav-label">Log</span>
      </button>
      <button class="nav-item" data-page="my-lawn">
        <svg class="nav-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 22V12"/><path d="M12 12C12 7 7 4 3 6c4 1 7 4 9 6z"/><path d="M12 12c0-5 5-8 9-6-4 1-7 4-9 6z"/>
        </svg>
        <span class="nav-label">My Lawn</span>
      </button>
      <button class="nav-item" data-page="ai-hub">
        <svg class="nav-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
        </svg>
        <span class="nav-label">AI</span>
      </button>`;

    nav.addEventListener('click', (e) => {
      const item = e.target.closest('.nav-item');
      if (!item) return;
      if (item.dataset.page === 'quick-log') { QuickLog.open(); }
      else { this.navigate(item.dataset.page); }
    });
    this.updateNavActive();
  },

  updateNavActive() {
    const page = this.currentPage;
    // Map legacy/child pages to their nav tab
    const navMap = {
      'dashboard': 'dashboard',
      'plan': 'plan', 'schedule': 'plan', 'history': 'plan',
      'my-lawn': 'my-lawn', 'fertilizer': 'my-lawn', 'lawn-program': 'my-lawn',
        'lawn-map': 'my-lawn', 'soil-tests': 'my-lawn',
      'ai-hub': 'ai-hub', 'assessment': 'ai-hub', 'lawn-coach': 'ai-hub', 'diagnosis': 'ai-hub',
      'settings': 'dashboard',
    };
    const activeNav = navMap[page] || page;
    document.querySelectorAll('#bottomNav .nav-item').forEach(item => {
      item.classList.toggle('active', item.dataset.page === activeNav);
    });
  },

  async navigate(page, opts = {}) {
    if (!this.authenticated) return;
    this.currentPage = page;
    this.updateNavActive();
    this.contentEl.innerHTML = '';
    window.scrollTo(0, 0);

    switch (page) {
      case 'dashboard': await DashboardPage.render(this.contentEl); break;
      case 'plan':      await PlanPage.render(this.contentEl, opts); break;
      case 'my-lawn':   await MyLawnPage.render(this.contentEl, opts); break;
      case 'ai-hub':    await AIHubPage.render(this.contentEl, opts); break;
      case 'settings':  await SettingsPage.render(this.contentEl); break;

      // Legacy routes → redirect into hub with correct tab
      case 'fertilizer':   this.currentPage = 'my-lawn'; this.updateNavActive();
                           await MyLawnPage.render(this.contentEl, { tab: 'fertilizer' }); break;
      case 'lawn-program': this.currentPage = 'my-lawn'; this.updateNavActive();
                           await MyLawnPage.render(this.contentEl, { tab: 'program' }); break;
      case 'lawn-map':     this.currentPage = 'my-lawn'; this.updateNavActive();
                           await MyLawnPage.render(this.contentEl, { tab: 'zones' }); break;
      case 'soil-tests':   this.currentPage = 'my-lawn'; this.updateNavActive();
                           await MyLawnPage.render(this.contentEl, { tab: 'soil' }); break;
      case 'assessment':   this.currentPage = 'ai-hub'; this.updateNavActive();
                           await AIHubPage.render(this.contentEl, { tab: 'assess' }); break;
      case 'lawn-coach':   this.currentPage = 'ai-hub'; this.updateNavActive();
                           await AIHubPage.render(this.contentEl, { tab: 'coach' }); break;
      case 'diagnosis':    this.currentPage = 'ai-hub'; this.updateNavActive();
                           await AIHubPage.render(this.contentEl, { tab: 'diagnose' }); break;
      case 'schedule':     this.currentPage = 'plan'; this.updateNavActive();
                           await PlanPage.render(this.contentEl, { tab: 'recurring' }); break;
      case 'history':      this.currentPage = 'plan'; this.updateNavActive();
                           await PlanPage.render(this.contentEl, { tab: 'agenda' }); break;

      default: await DashboardPage.render(this.contentEl);
    }
  },
};

document.addEventListener('DOMContentLoaded', () => App.init());
