(function () {
  'use strict';
  var musikfenster = null;

  document.addEventListener('click', function (event) {
    var link = event.target.closest('a[data-music-link]');
    if (!link || event.defaultPrevented || event.button !== 0 ||
        event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;

    try {
      if (!musikfenster || musikfenster.closed) {
        musikfenster = window.open('about:blank', '_blank');
        if (!musikfenster) return; // Der normale Link bleibt als Rückfall nutzbar.
        // Vor dem ersten externen Aufruf den Zugriff auf die Hommage trennen.
        musikfenster.opener = null;
      }
      musikfenster.location.href = link.href;
    } catch (error) {
      musikfenster = null;
      return; // Auch bei vom Anbieter getrennten Fenstern funktioniert der Link.
    }

    event.preventDefault();
    try { musikfenster.focus(); } catch (error) { /* Der Browser bestimmt den Fokus. */ }
  });
}());
