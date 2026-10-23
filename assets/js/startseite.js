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

(() => {
  const video = document.querySelector('.home-video[data-youtube-id]');
  const youtubeLink = document.querySelector('#home-hoeren-youtube');
  const choices = document.querySelectorAll('.home-playlist button[data-youtube-id]');
  if (!video || !youtubeLink || !choices.length) return;

  const loadVideo = (id, title) => {
    if (!/^[A-Za-z0-9_-]{11}$/.test(id || '')) return;
    const frame = document.createElement('iframe');
    frame.src = `https://www.youtube-nocookie.com/embed/${encodeURIComponent(id)}?rel=0`;
    frame.title = title || 'YouTube video';
    frame.allow = 'accelerometer; encrypted-media; gyroscope; picture-in-picture; web-share';
    frame.allowFullscreen = true;
    frame.referrerPolicy = 'strict-origin-when-cross-origin';
    const current = video.querySelector('iframe, .hoer-video-laden');
    if (current) current.replaceWith(frame);
  };

  const firstPreview = video.querySelector('.hoer-video-laden');
  if (!firstPreview) return;
  const previewTemplate = firstPreview.cloneNode(true);
  const bindPreview = (preview) => {
    preview.addEventListener('click', () => loadVideo(video.dataset.youtubeId, video.dataset.youtubeTitle), { once: true });
  };
  bindPreview(firstPreview);

  const showPreview = (choice) => {
    const id = choice.dataset.youtubeId;
    if (!/^[A-Za-z0-9_-]{11}$/.test(id || '')) return;
    const preview = previewTemplate.cloneNode(true);
    const image = preview.querySelector('.hoer-video-bild');
    const meta = preview.querySelector('.hoer-video-text small');
    preview.setAttribute('aria-label', choice.dataset.youtubeLabel || choice.dataset.youtubeTitle || 'Load video');
    if (image && choice.dataset.youtubePreview) image.src = choice.dataset.youtubePreview;
    if (meta) meta.textContent = choice.dataset.youtubeMeta || '';
    const current = video.querySelector('iframe, .hoer-video-laden');
    if (current) current.replaceWith(preview);
    video.dataset.youtubeId = id;
    video.dataset.youtubeTitle = choice.dataset.youtubeTitle || '';
    youtubeLink.href = `https://www.youtube.com/watch?v=${encodeURIComponent(id)}`;
    choices.forEach((item) => item.setAttribute('aria-pressed', String(item === choice)));
    bindPreview(preview);
  };

  choices.forEach((choice) => {
    choice.addEventListener('click', () => {
      showPreview(choice);
    });
  });
})();
