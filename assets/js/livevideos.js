(function () {
  'use strict';
  // Vor dem ersten Klick lädt nichts von YouTube; danach ein Player je Konzert.
  var api = null;
  var karten = [];

  function ladeApi() {
    if (!api) {
      api = new Promise(function (fertig, fehler) {
        if (window.YT && window.YT.Player) { fertig(); return; }
        var vorher = window.onYouTubeIframeAPIReady;
        window.onYouTubeIframeAPIReady = function () { if (vorher) vorher(); fertig(); };
        var skript = document.createElement('script');
        skript.src = 'https://www.youtube.com/iframe_api';
        skript.onerror = fehler;
        document.head.appendChild(skript);
      });
    }
    return api;
  }

  function markiere(karte, id, start) {
    karte.querySelectorAll('.disk-konzert-stuecke a').forEach(function (link) {
      var aktiv = link.dataset.livevideo === id && (parseInt(link.dataset.start, 10) || 0) === start;
      if (aktiv) link.setAttribute('aria-current', 'true'); else link.removeAttribute('aria-current');
    });
  }

  // Einbetten verweigert, entfernt oder gesperrt: zurück zum Link.
  function zeigeFehler(karte) {
    var bereich = karte.closest('.disk-livevideos');
    var hinweis = document.createElement('p');
    var link = document.createElement('a');
    hinweis.className = 'disk-konzert-fehler';
    hinweis.textContent = bereich.dataset.fehler + ' ';
    link.href = karte.link;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.textContent = bereich.dataset.youtube;
    hinweis.appendChild(link);
    karte.querySelector('.disk-konzert-player').replaceChildren(hinweis);
    karte.spieler = null;
  }

  function pausiereAndere(aktiv) {
    karten.forEach(function (karte) {
      if (karte !== aktiv && karte.spieler && karte.spieler.pauseVideo) karte.spieler.pauseVideo();
    });
  }

  function spiele(karte, ziel) {
    var id = ziel.dataset.livevideo;
    var start = parseInt(ziel.dataset.start, 10) || 0;
    if (!/^[A-Za-z0-9_-]{11}$/.test(id)) return false;
    markiere(karte, id, start);
    karte.link = ziel.href;
    if (karte.spieler && karte.videoId === id) {
      karte.spieler.seekTo(start, true);
      karte.spieler.playVideo();
      return true;
    }
    karte.videoId = id;
    if (karte.spieler) {
      karte.spieler.loadVideoById({ videoId: id, startSeconds: start });
      return true;
    }
    var bereich = karte.querySelector('.disk-konzert-player');
    bereich.classList.add('ist-ladend');
    ladeApi().then(function () {
      var platz = document.createElement('div');
      bereich.replaceChildren(platz);
      bereich.classList.remove('ist-ladend');
      karte.spieler = new window.YT.Player(platz, {
        host: 'https://www.youtube-nocookie.com',
        videoId: id,
        playerVars: { autoplay: 0, start: start, rel: 0, playsinline: 1 },
        events: {
          onReady: function (event) {
            event.target.getIframe().title = karte.querySelector('h3').textContent;
            event.target.playVideo();
          },
          onError: function () { zeigeFehler(karte); },
          onStateChange: function (event) {
            if (event.data === window.YT.PlayerState.PLAYING) pausiereAndere(karte);
          }
        }
      });
      if (karten.indexOf(karte) < 0) karten.push(karte);
    }, function () {
      // Player-API blockiert: das Video auf YouTube öffnen.
      api = null;
      bereich.classList.remove('ist-ladend');
      window.open(ziel.href, '_blank', 'noopener');
    });
    return true;
  }

  document.addEventListener('click', function (event) {
    var ziel = event.target.closest('a[data-livevideo]');
    if (!ziel || event.defaultPrevented || event.button !== 0 ||
        event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    if (spiele(ziel.closest('.disk-konzert'), ziel)) event.preventDefault();
  });
}());
