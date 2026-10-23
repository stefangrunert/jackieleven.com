(function () {
  'use strict';

  var nav = document.querySelector('.bio-zeitstrahl');
  if (!nav) return;

  var fenster = nav.querySelector('.bio-zeitfenster');
  var marken = Array.from(nav.querySelectorAll('.bio-marker'));
  var aktiv = nav.querySelector('[aria-current="page"]');
  var schmal = window.matchMedia('(max-width: 860px)');
  var speicher = 'jackie-leven:biografie:spur';

  function lesen() {
    try { return JSON.parse(sessionStorage.getItem(speicher)); } catch (e) { return null; }
  }

  function schreiben(ziel) {
    try {
      sessionStorage.setItem(speicher, JSON.stringify({
        ziel: ziel,
        schmal: schmal.matches,
        links: fenster.scrollLeft,
        oben: fenster.scrollTop
      }));
    } catch (e) { /* Die Navigation bleibt auch ohne Speicherung vollständig nutzbar. */ }
  }

  function zentriere(marke) {
    if (!marke) return;
    if (schmal.matches) {
      fenster.scrollLeft = Math.max(0, marke.offsetLeft - fenster.clientWidth / 2 + marke.offsetWidth / 2);
    } else {
      fenster.scrollTop = Math.max(0, marke.offsetTop - fenster.clientHeight / 2 + marke.offsetHeight / 2);
    }
  }

  function hoehe() {
    if (!schmal.matches) {
      fenster.style.setProperty('--bio-oberkante', Math.max(0, nav.getBoundingClientRect().top) + 'px');
    }
  }

  nav.addEventListener('keydown', function (e) {
    if (e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;
    var n = marken.indexOf(e.target);
    if (n < 0) return;
    if (e.key === (schmal.matches ? 'ArrowRight' : 'ArrowDown')) n++;
    else if (e.key === (schmal.matches ? 'ArrowLeft' : 'ArrowUp')) n--;
    else if (e.key === 'Home') n = 0;
    else if (e.key === 'End') n = marken.length - 1;
    else return;
    e.preventDefault();
    var ziel = marken[Math.max(0, Math.min(n, marken.length - 1))];
    ziel.focus({ preventScroll: true });
    zentriere(ziel);
  });

  nav.addEventListener('click', function (e) {
    var link = e.target.closest('.bio-marker');
    if (link) schreiben(link.pathname);
  });

  function positioniere() {
    hoehe();
    var stand = lesen();
    if (stand && stand.ziel === location.pathname && stand.schmal === schmal.matches) {
      fenster.scrollLeft = stand.links;
      fenster.scrollTop = stand.oben;
    } else {
      zentriere(aktiv);
    }
  }

  window.addEventListener('resize', function () { hoehe(); });
  window.addEventListener('scroll', hoehe, { passive: true });
  positioniere();
}());
