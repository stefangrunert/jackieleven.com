(() => {
  'use strict';

  document.querySelectorAll('form[data-search-pending]').forEach((form) => {
    const button = form.querySelector('button[type="submit"]');
    const label = button?.querySelector('.search-submit-label');
    const status = document.getElementById(form.dataset.statusId);
    if (!button || !label || !status) return;
    const idleLabel = label.textContent;
    let pending = false;
    let recovery;

    const reset = () => {
      window.clearTimeout(recovery);
      pending = false;
      form.classList.remove('is-searching');
      form.removeAttribute('aria-busy');
      button.disabled = false;
      label.textContent = idleLabel;
      status.textContent = '';
    };
    const start = (event) => {
      if (event.defaultPrevented) return false;
      event.preventDefault();
      if (pending) return false;
      pending = true;
      form.classList.add('is-searching');
      form.setAttribute('aria-busy', 'true');
      button.disabled = true;
      label.textContent = form.dataset.loadingLabel;
      status.textContent = form.dataset.loadingMessage;
      // Native navigation stays intact. Recover if it is stopped or stalls;
      // never automatically repeat a potentially billable search request.
      recovery = window.setTimeout(() => {
        reset();
        status.textContent = form.dataset.retryMessage;
      }, 20000);
      return true;
    };
    // Let the waiting state paint before a browser snapshots the outgoing page.
    const afterPaint = (navigate) => {
      window.requestAnimationFrame(() => window.requestAnimationFrame(navigate));
    };
    // Native validation runs before submit, so invalid forms never look busy.
    form.addEventListener('submit', (event) => {
      if (start(event)) afterPaint(() => HTMLFormElement.prototype.submit.call(form));
    });
    window.addEventListener('pageshow', reset);

    // Examples, section drilldowns and language changes also start searches.
    document.addEventListener('click', (event) => {
      if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      const link = event.target.closest('a[href]');
      if (!link || link.hasAttribute('download') || (link.target && link.target !== '_self')) return;
      const target = new URL(link.href, window.location.href);
      if (target.origin !== window.location.origin || !/\/(?:de\/suche|en\/search)$/.test(target.pathname) || !target.searchParams.get('q')?.trim()) return;
      if (start(event)) afterPaint(() => window.location.assign(target.href));
    });
  });
})();
