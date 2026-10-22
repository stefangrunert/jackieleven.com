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
  var projekt = form.elements.projekt;
  var format = form.elements.format;
  var status = raum.querySelector('.disk-filterstatus');
  var reset = form.querySelector('button');
  var schmal = window.matchMedia('(max-width: 860px)');
  var deutsch = document.documentElement.lang === 'de';
  var aktuell = null;
  var sichtbareJahre = jahre;

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
      var m = marke.getBoundingClientRect(), f = fenster.getBoundingClientRect();
      if (schmal.matches) {
        if (m.left < f.left + 8) fenster.scrollLeft += m.left - f.left - 8;
        else if (m.right > f.right - 8) fenster.scrollLeft += m.right - f.right + 8;
      } else {
        if (m.top < f.top + 25) fenster.scrollTop += m.top - f.top - 25;
        else if (m.bottom > f.bottom - 25) fenster.scrollTop += m.bottom - f.bottom + 25;
      }
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
  form.addEventListener('change', function () { auswahl(true); });
  form.addEventListener('reset', function (e) {
    e.preventDefault();
    projekt.value = format.value = 'alle';
    auswahl(true);
  });

  nav.addEventListener('keydown', function (e) {
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
    sichtbar[Math.max(0, Math.min(n, sichtbar.length - 1))].focus();
  });

  // Fehlende externe Cover lassen den bibliographischen Eintrag unberührt.
  raum.querySelectorAll('.disk-cover img').forEach(function (img) {
    function ohneBild() {
      img.closest('figure').hidden = true;
      img.closest('article').classList.remove('disk-mit-cover');
      position();
    }
    img.addEventListener('error', ohneBild);
    if (img.complete && !img.naturalWidth) ohneBild();
  });
  var raf;
  window.addEventListener('scroll', function () {
    if (raf) return;
    raf = requestAnimationFrame(function () { raf = null; position(); });
  }, { passive: true });
  window.addEventListener('resize', function () { aktuell = null; position(); });
  window.addEventListener('popstate', ausAdresse);
  window.addEventListener('hashchange', function () { position(); sprachlinks(); });
  ausAdresse();
})();
