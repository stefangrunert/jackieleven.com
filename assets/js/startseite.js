(() => {
  const button = document.querySelector('.home-menuknopf');
  const menu = document.querySelector('.home-menu');
  if (!button || !menu) return;
  const mobile = window.matchMedia('(max-width: 1023px)');
  const setOpen = (open) => {
    button.setAttribute('aria-expanded', String(open));
    menu.hidden = mobile.matches && !open;
  };
  const resize = () => {
    button.hidden = !mobile.matches;
    setOpen(false);
  };
  button.addEventListener('click', () => setOpen(button.getAttribute('aria-expanded') !== 'true'));
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && mobile.matches && !menu.hidden) {
      setOpen(false);
      button.focus();
    }
  });
  document.addEventListener('click', (event) => {
    if (mobile.matches && !event.target.closest('.home-kopf')) setOpen(false);
  });
  mobile.addEventListener('change', resize);
  resize();
})();
