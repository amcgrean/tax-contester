/* App shell: tab nav + tweaks panel wiring + hash routing */

(function () {
  const tabs = document.querySelectorAll('.tab');
  const screens = document.querySelectorAll('.screen');
  const main = document.getElementById('main');

  const RENDERED = new Set();
  // These screens depend on selected parcel and must re-render on every visit
  const ALWAYS_RENDER = new Set(['parcel', 'comps', 'packet']);

  function goto(name, push = true) {
    if (!name) return;
    tabs.forEach(t => t.classList.toggle('is-active', t.dataset.tab === name));
    screens.forEach(s => {
      const active = s.dataset.screen === name;
      s.classList.toggle('is-active', active);
      const shouldRender = active && window.__renderers[name] &&
        (!RENDERED.has(name) || ALWAYS_RENDER.has(name));
      if (shouldRender) {
        window.__renderers[name](s);
        RENDERED.add(name);
      }
    });
    if (push) {
      history.replaceState(null, '', '#' + name);
    }
    window.scrollTo({ top: 0, behavior: 'instant' });
  }
  window.__goto = goto;

  tabs.forEach(t => t.addEventListener('click', () => goto(t.dataset.tab)));

  // initial
  const initial = (location.hash || '#search').slice(1);
  goto(['search','parcel','comps','admin','packet'].includes(initial) ? initial : 'search', false);

  /* --------- Tweaks panel ---------- */
  const tweaks = document.getElementById('tweaks');

  function openTweaks() {
    tweaks.hidden = false;
  }
  function closeTweaks() {
    tweaks.hidden = true;
    window.parent.postMessage({ type: '__edit_mode_dismissed' }, '*');
  }
  document.getElementById('tweaks-close').addEventListener('click', closeTweaks);

  // host protocol — register listener BEFORE announcing availability
  window.addEventListener('message', (e) => {
    const t = e.data && e.data.type;
    if (t === '__activate_edit_mode') openTweaks();
    if (t === '__deactivate_edit_mode') closeTweaks();
  });
  window.parent.postMessage({ type: '__edit_mode_available' }, '*');

  /* --------- Tweak handlers ---------- */
  function applyConclusion(state) {
    // In live mode, the verdict text comes from the API. Only toggle the CSS class.
    const el = document.getElementById('conclusion');
    if (!el) return;
    el.classList.remove('over','fair','under');
    el.classList.add(state);
  }

  function applyFreshness(state) {
    const banner = document.getElementById('freshness-banner');
    if (!banner) return;
    banner.hidden = state !== 'stale';
  }
  function applyVanguard(show) {
    const banner = document.getElementById('vanguard-banner');
    if (!banner) return;
    banner.hidden = !show;
  }
  function applySubject(state) {
    document.body.dataset.subject = state;
  }
  function applyMapPos(state) {
    const layout = document.getElementById('comps-layout');
    const mapCard = document.getElementById('map-card');
    if (!layout || !mapCard) return;
    layout.classList.remove('has-header-map', 'no-map');
    const map = mapCard.querySelector('.map');
    map.classList.remove('header');
    if (state === 'split') {
      // default
      mapCard.style.display = '';
      mapCard.parentElement.insertBefore(mapCard, mapCard.parentElement.firstChild);
      layout.appendChild(mapCard);
    } else if (state === 'header') {
      layout.classList.add('has-header-map');
      map.classList.add('header');
      // move map card outside layout, before it
      layout.parentElement.insertBefore(mapCard, layout);
    } else if (state === 'hidden') {
      layout.classList.add('no-map');
      mapCard.style.display = 'none';
    }
  }
  function applyMobile(on) {
    document.body.classList.toggle('mobile-preview', !!on);
  }

  function readTweaks() {
    const conc = document.querySelector('input[name="conclusion"]:checked')?.value || 'over';
    const fresh = document.querySelector('input[name="freshness"]:checked')?.value || 'fresh';
    const vang  = document.getElementById('tw-vanguard').checked;
    const subj  = document.querySelector('input[name="subject"]:checked')?.value || 'filled';
    const map   = document.querySelector('input[name="mapPos"]:checked')?.value || 'split';
    const mob   = document.getElementById('tw-mobile').checked;
    applyConclusion(conc);
    applyFreshness(fresh);
    applyVanguard(vang);
    applySubject(subj);
    applyMapPos(map);
    applyMobile(mob);
  }

  document.querySelectorAll('#tweaks input').forEach(i => {
    i.addEventListener('change', () => {
      // ensure comps screen is rendered before re-applying
      if (!RENDERED.has('comps') && window.__renderers.comps) {
        window.__renderers.comps(document.querySelector('[data-screen="comps"]'));
        RENDERED.add('comps');
      }
      readTweaks();
    });
  });

  // Initial pass — re-apply once comps screen renders the first time
  const origGoto = window.__goto;
  window.__goto = function (name, push) {
    origGoto(name, push);
    if (name === 'comps') readTweaks();
  };

  // Apply defaults to body so subject style works on first visit
  applySubject('filled');
})();
