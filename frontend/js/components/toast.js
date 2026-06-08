/** Toast notification component */
const Toast = {
  show(message, type = 'info', duration = 3000) {
    const existing = document.querySelector('.toast-container');
    if (existing) existing.remove();

    const colors = {
      success: 'var(--color-success)',
      error: 'var(--color-danger)',
      warning: 'var(--color-warning)',
      info: 'var(--color-accent)',
    };

    const container = document.createElement('div');
    container.className = 'toast-container toast-enter';
    container.style.cssText = `
      position: fixed; top: 16px; left: 50%; transform: translateX(-50%);
      z-index: 9999; max-width: calc(var(--max-width) - 32px); width: calc(100% - 32px);
      padding: 12px 16px; border-radius: var(--radius-md);
      background: var(--bg-elevated); border: 1px solid ${colors[type] || colors.info};
      color: var(--text-primary); font-size: var(--fs-sm);
      box-shadow: var(--shadow-lg); display: flex; align-items: center; gap: 8px;
    `;
    container.innerHTML = `<span style="color:${colors[type]};font-size:1.1rem">${type === 'success' ? '✓' : type === 'error' ? '✕' : type === 'warning' ? '⚠' : 'ℹ'}</span><span>${message}</span>`;
    document.body.appendChild(container);

    setTimeout(() => {
      container.classList.add('toast-exit');
      setTimeout(() => container.remove(), 200);
    }, duration);
  },
  success(msg) { this.show(msg, 'success'); },
  error(msg) { this.show(msg, 'error', 4000); },
  warning(msg) { this.show(msg, 'warning'); },
  info(msg) { this.show(msg, 'info'); },
};
