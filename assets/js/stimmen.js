(function () {
  'use strict';

  var raum = document.querySelector('.stimmen-raum');
  var regler = document.getElementById('quellen-auswahl');
  if (!raum || !regler) return;

  var stufen = Array.from(raum.querySelectorAll('[data-auswahl-stufe]'));
  var jahre = Array.from(raum.querySelectorAll('.stimmen-jahr'));
  var marker = Array.from(raum.querySelectorAll('[data-quellen-jahr]'));
  var treffer = raum.querySelector('.stimmen-treffer');
  var reset = raum.querySelector('.stimmen-zuruecksetzen');
  var felder = Array.from(regler.form.querySelectorAll('select'));

  function anwenden(speichern) {
    var schwelle = Number(regler.value);
    var gesamt = 0;
    var filter = {};
    felder.forEach(function (feld) { filter[feld.name] = feld.value; });
    stufen.forEach(function (stufe) {
      var aktiv = Number(stufe.dataset.auswahlStufe) === schwelle;
      stufe.classList.toggle('aktiv', aktiv);
      if (aktiv) regler.setAttribute('aria-valuetext', stufe.textContent);
    });

    jahre.forEach(function (jahr, i) {
      var anzahl = 0;
      jahr.querySelectorAll('[data-quellen-gewicht]').forEach(function (quelle) {
        var sprache = quelle.dataset.sprache;
        var passtSprache = !filter.sprache || (filter.sprache === 'andere'
          ? ['en', 'no', 'de'].indexOf(sprache) === -1 : sprache === filter.sprache);
        quelle.hidden = Number(quelle.dataset.quellenGewicht) < schwelle
          || (filter.art !== '' && quelle.dataset.art !== filter.art)
          || (filter.zugang !== '' && quelle.dataset.zugang !== filter.zugang)
          || !passtSprache;
        if (!quelle.hidden) anzahl++;
      });
      var weitere = jahr.querySelector('.stimmen-weitere');
      if (weitere) {
        var weitereAnzahl = weitere.querySelectorAll('[data-quellen-gewicht]:not([hidden])').length;
        weitere.hidden = weitereAnzahl === 0;
        var summary = weitere.querySelector('summary');
        summary.textContent = summary.dataset.vorlage.replace('{n}', weitereAnzahl);
      }
      jahr.hidden = anzahl === 0;
      marker[i].hidden = anzahl === 0;
      marker[i].querySelector('.g-era').textContent =
        (anzahl === 1 ? raum.dataset.eintrag : raum.dataset.eintraege).replace('{n}', anzahl);
      gesamt += anzahl;
    });
    treffer.textContent = treffer.dataset.vorlage.replace('{n}', gesamt);
    raum.querySelector('.disk-leer').hidden = gesamt > 0;
    reset.hidden = schwelle === 0 && !felder.some(function (feld) { return feld.value !== ''; });

    if (speichern) {
      var url = new URL(location.href);
      if (schwelle !== 1) url.searchParams.set('auswahl', String(schwelle));
      else url.searchParams.delete('auswahl');
      felder.forEach(function (feld) {
        if (feld.value) url.searchParams.set(feld.name, feld.value);
        else url.searchParams.delete(feld.name);
      });
      // Ein ausgeblendetes Sprungziel soll beim Neuladen keinen Sprung auslösen.
      var ziel = url.hash && document.getElementById(decodeURIComponent(url.hash.slice(1)));
      if (ziel && ziel.closest('[hidden]')) url.hash = '';
      history.replaceState(history.state, '', url);
    }
  }

  regler.addEventListener('input', function () { anwenden(true); });
  felder.forEach(function (feld) {
    feld.addEventListener('change', function () { anwenden(true); });
  });
  regler.form.addEventListener('submit', function (e) { e.preventDefault(); anwenden(true); });
  reset.addEventListener('click', function (e) {
    e.preventDefault();
    regler.value = '0';
    felder.forEach(function (feld) { feld.value = ''; });
    anwenden(true);
  });
  function wiederherstellen() {
    var params = new URL(location.href).searchParams;
    var wert = params.get('auswahl');
    regler.value = wert === '0' || wert === '2' ? wert : '1';
    felder.forEach(function (feld) {
      var wert = params.get(feld.name) || '';
      feld.value = Array.from(feld.options).some(function (option) { return option.value === wert; }) ? wert : '';
    });
    anwenden(false);
  }
  window.addEventListener('pageshow', wiederherstellen);
  window.addEventListener('popstate', wiederherstellen);
  anwenden(false);
  // Ohne JavaScript bleibt das Formular über seinen Submit-Button bedienbar.
  regler.form.querySelector('button[type="submit"]').hidden = true;
}());
