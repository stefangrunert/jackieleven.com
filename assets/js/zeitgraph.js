/* Zeitgraph — positioniert die Marken nach Jahreszahl und tauscht die Bühne
   ohne Seitenwechsel aus. Ohne JavaScript bleiben es gewöhnliche Links. */
(function () {
  'use strict';

  var viewport = document.getElementById('g-viewport');
  var track    = document.getElementById('g-track');
  var stage    = document.getElementById('stage');
  if (!viewport || !track || !stage) return;

  var marken   = Array.prototype.slice.call(track.querySelectorAll('.g-marker'));
  if (!marken.length) return;

  var MIN_GAP = 44, RAND = 60, PX_PRO_JAHR = 18;
  var jahre   = marken.map(function (m) { return +m.dataset.jahr; });
  var MIN     = Math.min.apply(null, jahre) - 2;
  var MAX     = Math.max.apply(null, jahre) + 2;
  var tops    = [];

  var schmal = function () { return window.matchMedia('(max-width: 860px)').matches; };

  /* --- Positionen ------------------------------------------------------ */
  function baueGraph() {
    if (schmal()) {
      track.style.height = '';
      track.style.transform = '';
      offset = ziel = 0;
      marken.forEach(function (m) { m.style.top = ''; });
      return;
    }
    var viewH = viewport.clientHeight || 400;
    // Hoch genug, dass die Jahre proportional stehen: die leeren Jahre
    // zwischen 1950 und 1971 sollen als Leere sichtbar bleiben.
    var hoehe = Math.max(
      viewH,
      (MAX - MIN) * PX_PRO_JAHR + 2 * RAND,
      marken.length * MIN_GAP + 2 * RAND
    );

    tops = jahre.map(function (j) {
      return RAND + ((j - MIN) / (MAX - MIN)) * (hoehe - 2 * RAND);
    });
    // Gleiche und dicht beieinanderliegende Jahre auseinanderschieben
    for (var i = 1; i < tops.length; i++) {
      if (tops[i] - tops[i - 1] < MIN_GAP) tops[i] = tops[i - 1] + MIN_GAP;
    }
    // ... und die Spur so hoch machen, dass die letzte Marke hineinpasst
    track.style.height = Math.max(hoehe, tops[tops.length - 1] + RAND) + 'px';
    marken.forEach(function (m, i) { m.style.top = tops[i] + 'px'; });
  }

  /* --- sanftes Gleiten ------------------------------------------------- */
  var offset = 0, ziel = 0, raf = null;

  function maxOffset() {
    var h = parseFloat(track.style.height) || track.scrollHeight;
    return Math.max(0, h - viewport.clientHeight);
  }

  function animiere() {
    offset += (ziel - offset) * 0.14;
    if (Math.abs(ziel - offset) < 0.5) {
      offset = ziel;
      raf = null;
    } else {
      raf = requestAnimationFrame(animiere);
    }
    track.style.transform = 'translateY(' + (-offset) + 'px)';
  }

  function gleiteZu(v) {
    ziel = Math.min(maxOffset(), Math.max(0, v));
    if (raf === null) raf = requestAnimationFrame(animiere);
  }

  viewport.addEventListener('wheel', function (e) {
    if (schmal()) return;
    e.preventDefault();
    gleiteZu(ziel + e.deltaY);
  }, { passive: false });

  var touchY = null;
  viewport.addEventListener('touchstart', function (e) { touchY = e.touches[0].clientY; }, { passive: true });
  viewport.addEventListener('touchmove', function (e) {
    if (schmal() || touchY === null) return;
    var y = e.touches[0].clientY;
    gleiteZu(ziel + (touchY - y));
    touchY = y;
  }, { passive: true });

  function zentriere(i) {
    var m = marken[i];
    if (!m) return;
    if (schmal()) {
      m.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
      return;
    }
    gleiteZu(tops[i] - viewport.clientHeight / 2);
  }

  /* --- Stationswechsel ------------------------------------------------- */
  var aktiv = marken.findIndex(function (m) { return m.classList.contains('active'); });
  if (aktiv < 0) aktiv = 0;
  var anfrage = null;
  var wechsel = 0;

  function markiere(i) {
    marken.forEach(function (m, j) {
      var an = j === i;
      m.classList.toggle('active', an);
      if (an) { m.setAttribute('aria-current', 'true'); } else { m.removeAttribute('aria-current'); }
    });
    var zaehler = document.getElementById('count');
    if (zaehler) {
      zaehler.textContent = String(i + 1).padStart(2, '0') + ' / ' + String(marken.length).padStart(2, '0');
    }
  }

  function pagerAktualisieren(i) {
    var knoepfe = document.querySelectorAll('.pager .knopf');
    if (knoepfe.length !== 2) return;
    var vor  = marken[(i - 1 + marken.length) % marken.length];
    var nach = marken[(i + 1) % marken.length];
    knoepfe[0].href = vor.getAttribute('href');
    knoepfe[0].innerHTML = '← ' + vor.dataset.jahr;
    knoepfe[1].href = nach.getAttribute('href');
    knoepfe[1].innerHTML = nach.dataset.jahr + ' →';
  }

  function seitenangaben(i, pushen, uebersicht) {
    var url = marken[i].getAttribute('href');
    if (pushen && window.location.pathname !== url) history.pushState({ i: i }, '', url);
    var alternativen = JSON.parse((uebersicht ? track : marken[i]).dataset.alternativen);
    document.querySelectorAll('.sprachen a[hreflang], link[rel="alternate"][hreflang]').forEach(function (link) {
      var ziel = alternativen[link.getAttribute('hreflang')];
      if (ziel) link.href = new URL(ziel, window.location.href).href;
    });
    document.title = uebersicht ? track.dataset.titel : marken[i].dataset.jahr + ' — ' +
      marken[i].querySelector('.g-era').textContent + ' · Jackie Leven';
  }

  function zeige(i, pushen, uebersicht) {
    i = (i + marken.length) % marken.length;
    var nummer = ++wechsel;
    if (anfrage) anfrage.abort();
    anfrage = null;
    if (i === aktiv) {
      stage.style.opacity = '1';
      zentriere(i);
      seitenangaben(i, pushen, uebersicht);
      return;
    }
    var url = marken[i].getAttribute('href');
    anfrage = new AbortController();
    stage.style.opacity = '0';

    fetch(url + '?fragment=1', { signal: anfrage.signal, headers: { 'X-Requested-With': 'fetch' } })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.text(); })
      .then(function (html) {
        if (nummer !== wechsel) return;
        stage.innerHTML = html;
        aktiv = i;
        markiere(i);
        pagerAktualisieren(i);
        zentriere(i);
        seitenangaben(i, pushen, uebersicht);
        requestAnimationFrame(function () { if (nummer === wechsel) stage.style.opacity = '1'; });
        anfrage = null;
      })
      .catch(function (fehler) {
        if (nummer === wechsel && fehler.name !== 'AbortError') window.location.href = url;
      });
  }

  track.addEventListener('click', function (e) {
    var m = e.target.closest('.g-marker');
    if (!m || e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
    e.preventDefault();
    zeige(marken.indexOf(m), true);
  });

  document.addEventListener('click', function (e) {
    var k = e.target.closest('.pager .knopf');
    if (!k || e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
    var i = marken.findIndex(function (m) { return m.getAttribute('href') === k.getAttribute('href'); });
    if (i < 0) return;
    e.preventDefault();
    zeige(i, true);
  });

  document.addEventListener('keydown', function (e) {
    if (e.target.matches('input, textarea')) return;
    if (e.key === 'ArrowLeft')  { e.preventDefault(); zeige(aktiv - 1, true); }
    if (e.key === 'ArrowRight') { e.preventDefault(); zeige(aktiv + 1, true); }
  });

  window.addEventListener('popstate', function () {
    var pfad = window.location.pathname;
    var i = marken.findIndex(function (m) { return m.getAttribute('href') === pfad; });
    zeige(i < 0 ? 0 : i, false, i < 0);
  });

  stage.style.transition = 'opacity .3s';

  var rt;
  window.addEventListener('resize', function () {
    clearTimeout(rt);
    rt = setTimeout(function () { baueGraph(); zentriere(aktiv); }, 150);
  });

  baueGraph();
  zentriere(aktiv);
  markiere(aktiv);
})();
