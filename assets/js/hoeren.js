(() => {
  'use strict';

  document.querySelectorAll('.hoer-video[data-youtube-id]').forEach((video) => {
    const button = video.querySelector('.hoer-video-laden');
    if (!button) return;

    button.addEventListener('click', () => {
      const id = video.dataset.youtubeId;
      if (!/^[A-Za-z0-9_-]{11}$/.test(id || '')) return;

      const frame = document.createElement('iframe');
      frame.src = `https://www.youtube-nocookie.com/embed/${encodeURIComponent(id)}?rel=0`;
      frame.title = video.dataset.youtubeTitle || 'YouTube video';
      frame.allow = 'accelerometer; encrypted-media; gyroscope; picture-in-picture; web-share';
      frame.allowFullscreen = true;
      frame.referrerPolicy = 'strict-origin-when-cross-origin';
      video.classList.add('ist-geladen');
      button.replaceWith(frame);
    }, { once: true });
  });
})();
