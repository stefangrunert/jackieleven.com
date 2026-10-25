/* Deterministic navigation and player races; run with node, no network or browser needed. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = name => fs.readFileSync(path.join(__dirname, '../assets/js', name), 'utf8');
const tick = () => new Promise(resolve => setImmediate(resolve));
const classes = () => ({ add() {}, remove() {}, toggle() {} });

async function timeline(prefix = '') {
  const navigationOrigin = prefix ? 'https://preview.example' : 'https://example.org';
  const events = {}, windowEvents = {}, requests = [];
  const location = new URL(navigationOrigin + prefix + '/de/zeitreise/a');
  const canonicalURLs = slug => JSON.stringify({ de: '/de/zeitreise' + slug, en: '/en/timeline' + slug, 'x-default': '/de/zeitreise' + slug });
  const urls = slug => JSON.stringify({ de: prefix + '/de/zeitreise' + slug, en: prefix + '/en/timeline' + slug, 'x-default': prefix + '/de/zeitreise' + slug });
  const seo = (slug, titel) => JSON.stringify({ titel, url: 'https://example.org/de/zeitreise' + slug, beschreibung: 'Text ' + titel });
  const links = ['en', 'de', 'x-default'].map(lang => ({
    tagName: lang === 'x-default' ? 'LINK' : 'A',
    href: (lang === 'x-default' ? 'https://example.org' : navigationOrigin + prefix) + '/' + (lang === 'en' ? 'en/timeline/a' : 'de/zeitreise/a'), getAttribute: () => lang
  }));
  const markers = ['a', 'b', 'c'].map((slug, i) => ({
    dataset: { jahr: String(1950 + i), alternativen: urls('/' + slug), ...(prefix ? { canonicalAlternativen: canonicalURLs('/' + slug) } : {}), seo: seo('/' + slug, slug.toUpperCase()) }, style: {},
    classList: { contains: () => i === 0, toggle() {} },
    getAttribute: () => prefix + '/de/zeitreise/' + slug, setAttribute() {}, removeAttribute() {}, scrollIntoView() {},
    querySelector: () => ({ textContent: slug }), closest() { return this; }
  }));
  const viewport = { addEventListener() {} };
  const track = { style: {}, dataset: { alternativen: urls(''), ...(prefix ? { canonicalAlternativen: canonicalURLs('') } : {}), seo: seo('', 'Zeitreise') },
    querySelectorAll: () => markers, addEventListener: (name, fn) => events[name] = fn };
  const stage = { style: {}, innerHTML: 'A' };
  const canonical = { href: 'https://example.org/de/zeitreise/a' }, ogUrl = { content: '' }, description = { content: '' };
  const schema = { textContent: JSON.stringify({ '@graph': [{ '@type': 'WebSite' }, { '@type': 'WebPage' }] }) };
  const document = {
    getElementById: id => ({ 'g-viewport': viewport, 'g-track': track, stage })[id],
    querySelectorAll: selector => selector.includes('hreflang') ? links : selector.includes('description') ? [description] : [],
    querySelector: selector => selector.includes('canonical') ? canonical : selector.includes('og:url') ? ogUrl : selector.includes('ld+json') ? schema : null,
    addEventListener() {}
  };
  const webpage = () => JSON.parse(schema.textContent)['@graph'][1];
  let pushes = 0;
  vm.runInNewContext(source('zeitgraph.js'), {
    document, URL, AbortController, setTimeout, clearTimeout, requestAnimationFrame: fn => fn(),
    window: { location, matchMedia: () => ({ matches: true }), addEventListener: (name, fn) => windowEvents[name] = fn },
    history: { pushState: (_, __, url) => { pushes++; location.pathname = url; } },
    fetch: (url, options) => new Promise((resolve, reject) => requests.push({ url, options, resolve, reject }))
  });
  const click = i => events.click({ target: markers[i], button: 0, preventDefault() {} });
  const finish = async (request, html) => { request.resolve({ ok: true, text: () => Promise.resolve(html) }); await tick(); };
  const back = slug => { location.pathname = prefix + '/de/zeitreise' + slug; windowEvents.popstate(); };

  click(1);
  assert.equal(requests[0].url, prefix + '/de/zeitreise/b?fragment=1');
  await finish(requests[0], 'B');
  assert.equal(stage.innerHTML, 'B');
  assert.equal(links[0].href, navigationOrigin + prefix + '/en/timeline/b');
  assert.equal(links[2].href, 'https://example.org/de/zeitreise/b');
  assert.equal(document.title, 'B');
  assert.equal(canonical.href, 'https://example.org/de/zeitreise/b');
  assert.equal(ogUrl.content, 'https://example.org/de/zeitreise/b');
  assert.equal(description.content, 'Text B');
  assert.equal(webpage()['@id'], 'https://example.org/de/zeitreise/b#webpage');

  click(2);
  back('/a');
  assert.equal(requests[1].options.signal.aborted, true);
  await finish(requests[1], 'STALE C'); // Also reject responses that arrive despite abort.
  await finish(requests[2], 'A');
  assert.equal(stage.innerHTML, 'A');
  assert.equal(location.pathname, prefix + '/de/zeitreise/a');
  assert.equal(pushes, 1);
  assert.equal(links[0].href, navigationOrigin + prefix + '/en/timeline/a');

  click(2);
  back('/a'); // The destination is already rendered: cancel without another fetch.
  assert.equal(stage.style.opacity, '1');
  await finish(requests[3], 'STALE C');
  assert.equal(stage.innerHTML, 'A');
  assert.equal(location.pathname, prefix + '/de/zeitreise/a');
  back('');
  assert.equal(links[0].href, navigationOrigin + prefix + '/en/timeline');
  assert.equal(document.title, 'Zeitreise');
  assert.equal(canonical.href, 'https://example.org/de/zeitreise');
  assert.equal(webpage().name, 'Zeitreise');

  click(1);
  click(2);
  await finish(requests[5], 'C');
  await finish(requests[4], 'STALE B');
  assert.equal(stage.innerHTML, 'C');
  assert.equal(location.pathname, prefix + '/de/zeitreise/c');
  assert.equal(links[0].href, navigationOrigin + prefix + '/en/timeline/c');
  click(1);
  back('/c');
  requests[6].reject(new Error('Late network error'));
  await tick();
  assert.equal(location.pathname, prefix + '/de/zeitreise/c');
}

async function videos() {
  let click;
  const players = [], scripts = [];
  const region = { dataset: { fehler: 'Error', youtube: 'YouTube' } };
  const area = { classList: classes(), replaceChildren() {} };
  const card = { querySelectorAll: () => [], closest: () => region,
    querySelector: selector => selector === 'h3' ? { textContent: 'Concert' } : area };
  const window = {};
  const document = { addEventListener: (_, fn) => click = fn,
    createElement: () => ({ appendChild() {} }), head: { appendChild: script => scripts.push(script) } };
  vm.runInNewContext(source('livevideos.js'), { document, window, Promise });
  const choose = (start, id = '3pcJw_Zjf94') => {
    const target = { dataset: { livevideo: id, start: String(start) }, href: 'https://www.youtube.com/watch?v=' + id,
      closest: selector => selector === '.disk-konzert' ? card : target };
    click({ target, button: 0, preventDefault() {} });
  };
  function Player(element, options) {
    this.options = options;
    this.calls = [];
    this.ready = () => {
      this.getIframe = () => ({});
      this.seekTo = start => this.calls.push(['seek', start]);
      this.playVideo = () => this.calls.push(['play']);
      this.loadVideoById = target => this.calls.push(['load', target.videoId, target.startSeconds]);
      this.destroy = () => this.calls.push(['destroy']);
      options.events.onReady({ target: this });
    };
    players.push(this);
  }
  choose(0);
  choose(120);
  assert.equal(scripts.length, 1);
  window.YT = { Player, PlayerState: { PLAYING: 1 } };
  window.onYouTubeIframeAPIReady();
  await tick();
  assert.equal(players.length, 1);
  assert.equal(players[0].options.playerVars.start, 120);
  choose(240); // Player exists, but its playback methods do not exist yet.
  choose(300, 'XLmSL2QBoy0');
  assert.equal(players.length, 1);
  players[0].ready();
  assert.deepEqual(players[0].calls[0], ['load', 'XLmSL2QBoy0', 300]);
  choose(360, 'XLmSL2QBoy0');
  assert.deepEqual(players[0].calls.slice(-2), [['seek', 360], ['play']]);
  players[0].options.events.onError({ target: players[0] });
  assert.equal(card.spieler, null);
  choose(400);
  await tick();
  assert.equal(players.length, 2);
  players[0].options.events.onReady({ target: players[0] }); // Destroyed player cannot take over.
  assert.equal(card.bereit, false);
  players[1].ready();
  assert.deepEqual(players[1].calls[0], ['seek', 400]);
}

(async () => {
  await timeline();
  await timeline('/jackieleven');
  await videos();
  console.log('Browserabläufe: Sprachwechsel/SEO mit und ohne Mount-Pfad, Verlauf, überholte Antworten und Video-Mehrfachklicks geprüft.');
})().catch(error => { console.error(error); process.exitCode = 1; });
