/* Die aktuelle Kolumne im Zeitstrahl zeigen. Artikel bleiben normale Links. */
(function () {
  'use strict';

  var nav = document.querySelector('.pool-zeitstrahl');
  if (!nav) return;
  var fenster = nav.querySelector('.pool-zeitfenster');
  var aktiv = nav.querySelector('[aria-current="page"]');
  var marken = Array.prototype.slice.call(nav.querySelectorAll('.pool-marker'));
  var schmal = window.matchMedia('(max-width: 860px)');
  var positionKey = 'jackie-leven:pool-position';

  // Den Platz unterhalb des Kopfes bis zum unteren Fensterrand nutzen,
  // auch wenn der Seitenkopf beim Scrollen aus dem Bild verschwindet.
  function passeHoeheAn() {
    if (schmal.matches) return;
    var oberkante = Math.max(0, nav.getBoundingClientRect().top);
    fenster.style.setProperty('--pool-oberkante', oberkante + 'px');
  }

  function zentriere() {
    if (!aktiv) return;
    var a = aktiv.getBoundingClientRect();
    var f = fenster.getBoundingClientRect();
    if (schmal.matches) {
      fenster.scrollTop = 0;
      fenster.scrollLeft += a.left - f.left - (fenster.clientWidth - a.width) / 2;
    } else {
      fenster.scrollLeft = 0;
      fenster.scrollTop += a.top - f.top - (fenster.clientHeight - a.height) / 2;
    }
  }

  // Beim Blättern bleibt der Ausschnitt stehen. Nur wenn der neue Beitrag
  // außerhalb liegt, wird er an den sichtbaren Rand geschoben.
  function stellePositionWiederHer() {
    try {
      var position = JSON.parse(sessionStorage.getItem(positionKey));
      sessionStorage.removeItem(positionKey);
      if (!position || position.ziel !== location.pathname || position.schmal !== schmal.matches) return false;
      fenster.scrollLeft = position.links;
      fenster.scrollTop = position.oben;
      if (aktiv) {
        var a = aktiv.getBoundingClientRect();
        var f = fenster.getBoundingClientRect();
        if (schmal.matches) {
          if (a.left < f.left + 8) fenster.scrollLeft += a.left - f.left - 8;
          else if (a.right > f.right - 8) fenster.scrollLeft += a.right - f.right + 8;
        } else {
          if (a.top < f.top + 25) fenster.scrollTop += a.top - f.top - 25;
          else if (a.bottom > f.bottom - 25) fenster.scrollTop += a.bottom - f.bottom + 25;
        }
      }
      return true;
    } catch (e) {
      return false;
    }
  }

  document.addEventListener('click', function (e) {
    if (e.defaultPrevented || e.button !== 0 || e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;
    var link = e.target.closest('.pool-marker, .pool-navigation a[rel="prev"], .pool-navigation a[rel="next"]');
    if (!link) return;
    try {
      sessionStorage.setItem(positionKey, JSON.stringify({
        ziel: link.pathname,
        schmal: schmal.matches,
        links: fenster.scrollLeft,
        oben: fenster.scrollTop
      }));
    } catch (e) {
      // Normale Links funktionieren auch ohne verfügbaren Sitzungsspeicher.
    }
  });

  // Nur im Zeitstrahl: Pfeiltasten bewegen den Fokus, Enter öffnet den Text.
  nav.addEventListener('keydown', function (e) {
    if (e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;
    var n = marken.indexOf(e.target);
    if (n < 0) return;
    var vor = schmal.matches ? 'ArrowLeft' : 'ArrowUp';
    var nach = schmal.matches ? 'ArrowRight' : 'ArrowDown';
    if (e.key === vor) n--;
    else if (e.key === nach) n++;
    else if (e.key === 'Home') n = 0;
    else if (e.key === 'End') n = marken.length - 1;
    else return;
    e.preventDefault();
    marken[Math.max(0, Math.min(marken.length - 1, n))].focus();
  });

  var raf;
  window.addEventListener('resize', function () {
    cancelAnimationFrame(raf);
    raf = requestAnimationFrame(function () {
      passeHoeheAn();
      zentriere();
    });
  });
  window.addEventListener('scroll', passeHoeheAn, { passive: true });
  passeHoeheAn();
  if (!stellePositionWiederHer()) zentriere();
})();
