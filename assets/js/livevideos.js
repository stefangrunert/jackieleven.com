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
    var spieler = karte.spieler;
    karte.spieler = null;
    karte.bereit = false;
    karte.ladend = false;
    if (spieler && spieler.destroy) spieler.destroy();
    karte.querySelector('.disk-konzert-player').replaceChildren(hinweis);
    karte.querySelector('.disk-konzert-player').classList.remove('ist-ladend');
  }

  function pausiereAndere(aktiv) {
    karten.forEach(function (karte) {
      if (karte !== aktiv && karte.bereit && karte.spieler) karte.spieler.pauseVideo();
    });
  }

  function spieleZiel(karte) {
    if (karte.videoId === karte.ziel.id) {
      karte.spieler.seekTo(karte.ziel.start, true);
      karte.spieler.playVideo();
    } else {
      karte.videoId = karte.ziel.id;
      karte.spieler.loadVideoById({ videoId: karte.ziel.id, startSeconds: karte.ziel.start });
    }
  }

  function spiele(karte, ziel) {
    var id = ziel.dataset.livevideo;
    var start = parseInt(ziel.dataset.start, 10) || 0;
    if (!/^[A-Za-z0-9_-]{11}$/.test(id)) return false;
    markiere(karte, id, start);
    karte.link = ziel.href;
    karte.ziel = { id: id, start: start };
    if (karte.bereit && karte.spieler) {
      spieleZiel(karte);
      return true;
    }
    // Eine Initialisierung pro Karte; weitere Klicks ändern nur das Wunschziel.
    if (karte.ladend) return true;
    karte.ladend = true;
    var bereich = karte.querySelector('.disk-konzert-player');
    bereich.classList.add('ist-ladend');
    ladeApi().then(function () {
      var auswahl = karte.ziel;
      karte.videoId = auswahl.id;
      var platz = document.createElement('div');
      bereich.replaceChildren(platz);
      karte.spieler = new window.YT.Player(platz, {
        host: 'https://www.youtube-nocookie.com',
        videoId: auswahl.id,
        playerVars: { autoplay: 0, start: auswahl.start, rel: 0, playsinline: 1 },
        events: {
          onReady: function (event) {
            if (event.target !== karte.spieler) return;
            karte.bereit = true;
            karte.ladend = false;
            bereich.classList.remove('ist-ladend');
            event.target.getIframe().title = karte.querySelector('h3').textContent;
            spieleZiel(karte);
          },
          onError: function (event) { if (event.target === karte.spieler) zeigeFehler(karte); },
          onStateChange: function (event) {
            if (event.target === karte.spieler && event.data === window.YT.PlayerState.PLAYING) pausiereAndere(karte);
          }
        }
      });
      if (karten.indexOf(karte) < 0) karten.push(karte);
    }).catch(function () {
      // Der Link bleibt auch bei einer blockierten Player-API direkt anklickbar.
      api = null;
      zeigeFehler(karte);
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
