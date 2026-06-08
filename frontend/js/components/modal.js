/** Modal / Drawer component */
const Modal = {
  show(title, contentHtml, options = {}) {
    this.close(); // Close any existing

    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.id = 'modalOverlay';
    overlay.innerHTML = `
      <div class="modal-content">
        <div class="modal-header">
          <h2 class="modal-title">${title}</h2>
          <button class="modal-close" id="modalClose">✕</button>
        </div>
        <div class="modal-body" id="modalBody">${contentHtml}</div>
      </div>`;

    document.body.appendChild(overlay);

    // Close handlers
    overlay.querySelector('#modalClose').addEventListener('click', () => this.close());
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) this.close();
    });

    if (options.onMount) options.onMount(overlay);
    return overlay;
  },

  close() {
    const overlay = document.getElementById('modalOverlay');
    if (overlay) overlay.remove();
    const dialog = document.getElementById('confirmOverlay');
    if (dialog) dialog.remove();
  },

  /**
   * Show an in-app confirmation dialog. Returns Promise<boolean>.
   * variant: 'danger' | 'default'  (controls confirm button color)
   * html: optional custom body HTML (e.g., a form with inputs)
   * onConfirm: optional callback fired before the dialog closes — use to read form values
   */
  confirm({ title, message, html, confirmText = 'Confirm', cancelText = 'Cancel', variant = 'default', onConfirm } = {}) {
    const existing = document.getElementById('confirmOverlay');
    if (existing) existing.remove();

    const btnClass = variant === 'danger' ? 'btn-danger' : 'btn-primary';
    const bodyHtml = html || (message ? `<p class="confirm-message">${message}</p>` : '');

    const overlay = document.createElement('div');
    overlay.className = 'confirm-overlay';
    overlay.id = 'confirmOverlay';
    overlay.innerHTML = `
      <div class="confirm-dialog" role="alertdialog" aria-modal="true">
        <h2 class="confirm-title">${title}</h2>
        ${bodyHtml ? `<div class="confirm-body">${bodyHtml}</div>` : ''}
        <div class="confirm-actions">
          <button class="btn btn-secondary" id="confirmCancel">${cancelText}</button>
          <button class="btn ${btnClass}" id="confirmOk">${confirmText}</button>
        </div>
      </div>`;

    document.body.appendChild(overlay);

    return new Promise((resolve) => {
      const cleanup = (result) => {
        overlay.style.opacity = '0';
        overlay.querySelector('.confirm-dialog').style.transform = 'scale(0.95)';
        setTimeout(() => overlay.remove(), 150);
        resolve(result);
      };

      overlay.querySelector('#confirmOk').addEventListener('click', () => {
        if (onConfirm) onConfirm();
        cleanup(true);
      });
      overlay.querySelector('#confirmCancel').addEventListener('click', () => cleanup(false));
      overlay.addEventListener('click', (e) => { if (e.target === overlay) cleanup(false); });

      const onKey = (e) => {
        if (e.key === 'Escape') { document.removeEventListener('keydown', onKey); cleanup(false); }
        if (e.key === 'Enter' && document.activeElement?.tagName !== 'TEXTAREA') {
          if (onConfirm) onConfirm();
          document.removeEventListener('keydown', onKey);
          cleanup(true);
        }
      };
      document.addEventListener('keydown', onKey);
    });
  },

  /** Show an in-app text input dialog. Returns Promise<string|null> (null = cancelled). */
  prompt({ title, label, placeholder = '', value = '', confirmText = 'OK', cancelText = 'Cancel' } = {}) {
    const existing = document.getElementById('confirmOverlay');
    if (existing) existing.remove();

    const overlay = document.createElement('div');
    overlay.className = 'confirm-overlay';
    overlay.id = 'confirmOverlay';
    overlay.innerHTML = `
      <div class="confirm-dialog" role="dialog" aria-modal="true">
        <h2 class="confirm-title">${title}</h2>
        <div class="confirm-body">
          ${label ? `<label class="form-label">${label}</label>` : ''}
          <input type="text" id="promptInput" class="form-input" placeholder="${placeholder}" value="${value}" autocomplete="off">
        </div>
        <div class="confirm-actions">
          <button class="btn btn-secondary" id="confirmCancel">${cancelText}</button>
          <button class="btn btn-primary" id="confirmOk">${confirmText}</button>
        </div>
      </div>`;

    document.body.appendChild(overlay);
    setTimeout(() => overlay.querySelector('#promptInput')?.focus(), 50);

    return new Promise((resolve) => {
      const getVal = () => overlay.querySelector('#promptInput')?.value?.trim() || null;

      const cleanup = (result) => {
        overlay.style.opacity = '0';
        overlay.querySelector('.confirm-dialog').style.transform = 'scale(0.95)';
        setTimeout(() => overlay.remove(), 150);
        resolve(result);
      };

      overlay.querySelector('#confirmOk').addEventListener('click', () => cleanup(getVal()));
      overlay.querySelector('#confirmCancel').addEventListener('click', () => cleanup(null));
      overlay.addEventListener('click', (e) => { if (e.target === overlay) cleanup(null); });

      overlay.querySelector('#promptInput').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') cleanup(getVal());
        if (e.key === 'Escape') cleanup(null);
      });
    });
  },
};
