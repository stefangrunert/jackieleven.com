(function () {
  'use strict';
  var raum = document.querySelector('.disk-raum');
  if (!raum) return;
  var nav = raum.querySelector('.disk-zeitstrahl');
  var fenster = nav.querySelector('.disk-zeitfenster');
  var marken = Array.from(nav.querySelectorAll('.disk-marker'));
  var jahre = Array.from(raum.querySelectorAll('.disk-jahr'));
  var platten = Array.from(raum.querySelectorAll('.disk-platte'));
  var form = raum.querySelector('.disk-auswahl');
  var projekt = form && form.elements.projekt;
  var format = form && form.elements.format;
  var status = raum.querySelector('.disk-filterstatus');
  var reset = form && form.querySelector('button');
  var schmal = window.matchMedia('(max-width: 860px)');
  var deutsch = document.documentElement.lang === 'de';
  var aktuell = null;
  var sichtbareJahre = jahre;
  var speicher = 'jackie-leven:diskografie:';

  function lesen(key) {
    try { return JSON.parse(sessionStorage.getItem(speicher + key)); } catch (e) { return null; }
  }
  function schreiben(key, value) {
    try { sessionStorage.setItem(speicher + key, JSON.stringify(value)); } catch (e) { /* Normale Links bleiben nutzbar. */ }
  }

  function tastatur(e) {
    if (e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;
    var sichtbar = marken.filter(function (m) { return !m.parentElement.hidden; });
    var n = sichtbar.indexOf(e.target);
    if (n < 0) return;
    if (e.key === (schmal.matches ? 'ArrowRight' : 'ArrowDown')) n++;
    else if (e.key === (schmal.matches ? 'ArrowLeft' : 'ArrowUp')) n--;
    else if (e.key === 'Home') n = 0;
    else if (e.key === 'End') n = sichtbar.length - 1;
    else return;
    e.preventDefault();
    sichtbar[Math.max(0, Math.min(n, sichtbar.length - 1))].focus({ preventScroll: true });
    zeigeMarke(sichtbar[Math.max(0, Math.min(n, sichtbar.length - 1))]);
  }
  nav.addEventListener('keydown', tastatur);

  function zeigeMarke(marke) {
    var m = marke.getBoundingClientRect(), f = fenster.getBoundingClientRect();
    if (schmal.matches) {
      if (m.left < f.left + 8) fenster.scrollLeft += m.left - f.left - 8;
      else if (m.right > f.right - 8) fenster.scrollLeft += m.right - f.right + 8;
    } else {
      if (m.top < f.top + 25) fenster.scrollTop += m.top - f.top - 25;
      else if (m.bottom > f.bottom - 25) fenster.scrollTop += m.bottom - f.bottom + 25;
    }
  }

  // Die Höhe des Covers bleibt auch bei einem Ladefehler erhalten. So verschiebt
  // ein externer Bildserver weder die Leseposition noch das Rücksprungziel.
  raum.querySelectorAll('.disk-cover img').forEach(function (img) {
    function ohneBild() { img.style.visibility = 'hidden'; }
    img.addEventListener('error', ohneBild);
    if (img.complete && !img.naturalWidth) ohneBild();
  });

  function hoehe() {
    if (!schmal.matches) fenster.style.setProperty('--disk-oberkante', Math.max(0, nav.getBoundingClientRect().top) + 'px');
  }

  function markiere(jahr) {
    if (aktuell === jahr) return;
    aktuell = jahr;
    marken.forEach(function (marke) {
      var an = marke.parentElement.dataset.jahr === jahr;
      marke.classList.toggle('active', an);
      if (an) marke.setAttribute('aria-current', 'location');
      else marke.removeAttribute('aria-current');
      if (!an) return;
      zeigeMarke(marke);
    });
  }

  function position() {
    hoehe();
    var aktiv = sichtbareJahre[0];
    var grenze = schmal.matches ? nav.getBoundingClientRect().height + 35 : 160;
    sichtbareJahre.forEach(function (jahr) {
      if (jahr.getBoundingClientRect().top <= grenze) aktiv = jahr;
    });
    // Am Seitenende kann die letzte Jahresüberschrift nicht mehr ganz nach
    // oben gelangen. Sie bleibt trotzdem das aktuelle Ziel.
    if (window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 2) {
      aktiv = sichtbareJahre[sichtbareJahre.length - 1];
    }
    markiere(aktiv ? aktiv.dataset.jahr : null);
  }

  function sprachlinks() {
    document.querySelectorAll('.sprachen a').forEach(function (link) {
      var url = new URL(link.href);
      url.search = location.search;
      url.hash = location.hash;
      link.href = url.pathname + url.search + url.hash;
    });
  }

  if (!form) {
    var aktiv = nav.querySelector('[aria-current="page"]');
    var ursprung = raum.dataset.origin;
    var rueckweg = lesen('von:' + ursprung);
    var ruecklinks = Array.from(document.querySelectorAll('[data-overview-return]'));
    // Der Hauptmenü-Link führt ebenfalls zur gemerkten Übersicht.
    var hauptlink = document.querySelector('.topbar a.hier');
    if (hauptlink) ruecklinks.push(hauptlink);
    var query = new URLSearchParams(location.search);
    if (query.has('von') && rueckweg && ['projekt', 'format'].every(function (name) {
      return (new URLSearchParams(rueckweg.search).get(name) || 'alle') === (query.get(name) || 'alle');
    })) {
      var basis = new URL(ruecklinks[0].href).pathname;
      var ziel = basis + rueckweg.search + rueckweg.hash;
      ruecklinks.forEach(function (link) {
        link.href = ziel;
        link.addEventListener('click', function () { schreiben('rueckkehr', { ziel: ziel, position: rueckweg }); });
      });
    }
    function detailPosition() { hoehe(); if (aktiv) zeigeMarke(aktiv); }
    var spur = lesen('spur');
    if (spur && spur.ziel === location.pathname && spur.schmal === schmal.matches) {
      fenster.scrollLeft = spur.links;
      fenster.scrollTop = spur.oben;
    } else if (aktiv) {
      // Nur den Zeitstrahl bewegen, nie die Seite über scrollIntoView.
      fenster.scrollTop = aktiv.offsetTop - fenster.clientHeight / 2 + aktiv.offsetHeight / 2;
      fenster.scrollLeft = aktiv.offsetLeft - fenster.clientWidth / 2 + aktiv.offsetWidth / 2;
    }
    document.addEventListener('click', function (e) {
      var link = e.target.closest('.disk-marker, .disk-blaettern a[rel]');
      if (!link) return;
      schreiben('spur', { ziel: link.pathname, schmal: schmal.matches, links: fenster.scrollLeft, oben: fenster.scrollTop });
    });
    window.addEventListener('scroll', hoehe, { passive: true });
    window.addEventListener('resize', detailPosition);
    detailPosition();
    sprachlinks();
    return;
  }

  // Links tragen die Auswahl und den Einstieg durch alle folgenden Detailseiten.
  function plattenlinks() {
    var query = new URLSearchParams(location.search);
    raum.querySelectorAll('[data-release-link]').forEach(function (link) {
      var url = new URL(link.href);
      url.search = '';
      ['projekt', 'format'].forEach(function (key) { if (query.has(key)) url.searchParams.set(key, query.get(key)); });
      url.searchParams.set('von', link.dataset.releaseLink);
      link.href = url.pathname + url.search + url.hash;
    });
  }

  function momentaufnahme() {
    var sichtbar = platten.filter(function (p) { return !p.hidden; });
    var grenze = schmal.matches ? nav.getBoundingClientRect().height : 0;
    var anker = sichtbar.find(function (p) { return p.getBoundingClientRect().bottom > grenze; });
    return {
      search: location.search, hash: location.hash, y: window.scrollY,
      anker: anker ? anker.id : null, abstand: anker ? anker.getBoundingClientRect().top : 0,
      links: fenster.scrollLeft, oben: fenster.scrollTop,
      offen: Array.from(raum.querySelectorAll('.disk-platte details[open]')).map(function (d) { return d.closest('article').id; })
    };
  }
  function merkePosition() {
    var stand = momentaufnahme();
    history.replaceState(Object.assign({}, history.state, { diskPosition: stand }), '', location.href);
    return stand;
  }
  raum.addEventListener('click', function (e) {
    var link = e.target.closest('[data-release-link]');
    if (link) schreiben('von:' + link.dataset.releaseLink, merkePosition());
  });
  window.addEventListener('pagehide', merkePosition);

  function auswahl(merken) {
    var anzahl = 0;
    platten.forEach(function (platte) {
      var art = platte.dataset.format;
      var passt = projekt.value === 'alle' || platte.dataset.projekte.split(' ').includes(projekt.value);
      var typ = format.value === 'alle' || format.value === art;
      if (format.value === 'alben') typ = ['album', 'live', 'compilation', 'spoken', 'tribute'].includes(art);
      if (format.value === 'kleine') typ = ['single', 'ep'].includes(art);
      platte.hidden = !(passt && typ);
      if (!platte.hidden) anzahl++;
    });
    jahre.forEach(function (jahr, i) {
      var n = jahr.querySelectorAll('.disk-platte:not([hidden])').length;
      jahr.hidden = n === 0;
      marken[i].parentElement.hidden = n === 0;
      marken[i].querySelector('.g-era').textContent = n + (deutsch ? (n === 1 ? ' Eintrag' : ' Einträge') : (n === 1 ? ' entry' : ' entries'));
    });
    sichtbareJahre = jahre.filter(function (jahr) { return !jahr.hidden; });
    var gefiltert = projekt.value !== 'alle' || format.value !== 'alle';
    reset.hidden = !gefiltert;
    status.textContent = gefiltert ? anzahl + (deutsch ? (anzahl === 1 ? ' Eintrag' : ' Einträge') : (anzahl === 1 ? ' entry' : ' entries')) : '';
    raum.querySelector('.disk-leer').hidden = anzahl !== 0;
    if (merken) {
      var url = new URL(location.href);
      ['projekt', 'format'].forEach(function (key) {
        var wert = form.elements[key].value;
        if (wert === 'alle') url.searchParams.delete(key);
        else url.searchParams.set(key, wert);
      });
      url.hash = '';
      history.pushState(null, '', url.pathname + url.search);
    }
    aktuell = undefined;
    position();
    sprachlinks();
    plattenlinks();
  }

  function ausAdresse() {
    var query = new URLSearchParams(location.search);
    [projekt, format].forEach(function (feld) {
      var wert = query.get(feld.name) || 'alle';
      feld.value = Array.from(feld.options).some(function (option) { return option.value === wert; }) ? wert : 'alle';
    });
    auswahl(false);
  }

  form.hidden = false;
  form.addEventListener('submit', function (e) { e.preventDefault(); });
  form.addEventListener('change', function () { merkePosition(); auswahl(true); });
  form.addEventListener('reset', function (e) {
    e.preventDefault();
    merkePosition();
    projekt.value = format.value = 'alle';
    auswahl(true);
  });

  var raf;
  window.addEventListener('scroll', function () {
    if (raf) return;
    raf = requestAnimationFrame(function () { raf = null; position(); });
  }, { passive: true });
  window.addEventListener('resize', function () { aktuell = null; position(); });
  window.addEventListener('popstate', function () { ausAdresse(); stelleWiederHer(history.state && history.state.diskPosition); });
  window.addEventListener('hashchange', function () { position(); sprachlinks(); });
  ausAdresse();

  function stelleWiederHer(stand) {
    if (!stand || stand.search !== location.search) return;
    raum.querySelectorAll('.disk-platte details').forEach(function (d) { d.open = (stand.offen || []).includes(d.closest('article').id); });
    var anker = stand.anker && document.getElementById(stand.anker);
    var y = anker && !anker.hidden ? window.scrollY + anker.getBoundingClientRect().top - stand.abstand : stand.y;
    window.scrollTo({ top: y, behavior: 'instant' });
    fenster.scrollLeft = stand.links;
    fenster.scrollTop = stand.oben;
    position();
  }
  var rueckkehr = lesen('rueckkehr');
  var wiederherstellen = rueckkehr && rueckkehr.ziel === location.pathname + location.search + location.hash ? rueckkehr.position : null;
  if (wiederherstellen) schreiben('rueckkehr', null);
  var navigation = performance.getEntriesByType('navigation')[0];
  if (!wiederherstellen && navigation && ['back_forward', 'reload'].includes(navigation.type)) wiederherstellen = history.state && history.state.diskPosition;
  if (wiederherstellen) {
    if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
    stelleWiederHer(wiederherstellen);
    // Schriftmetriken können beim ersten Laden noch wechseln. Nur vor der
    // ersten Benutzeraktion korrigieren, niemals gegen die Lesebewegung.
    var beruehrt = false;
    ['pointerdown', 'wheel', 'keydown', 'touchstart'].forEach(function (name) {
      window.addEventListener(name, function () { beruehrt = true; }, { once: true, passive: true });
    });
    Promise.all([document.fonts.ready, new Promise(function (resolve) {
      if (document.readyState === 'complete') resolve(); else window.addEventListener('load', resolve, { once: true });
    })]).then(function () { if (!beruehrt) stelleWiederHer(wiederherstellen); });
  }
  window.addEventListener('pageshow', function (e) {
    if (e.persisted) { ausAdresse(); stelleWiederHer(history.state && history.state.diskPosition); }
  });
})();
