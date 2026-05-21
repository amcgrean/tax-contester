/* ============================================================
   Iowa Property Tax Comp Engine — screens.js
   Fetches real data from Flask API and renders all 5 screens.
   ============================================================ */

const $ = (sel, root = document) => root.querySelector(sel);

const ICONS = {
  search:   '<svg class="icon" viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
  arrow:    '<svg class="icon" viewBox="0 0 24 24"><path d="M5 12h14M13 5l7 7-7 7"/></svg>',
  pin:      '<svg class="icon" viewBox="0 0 24 24"><path d="M12 22s7-7.5 7-13a7 7 0 1 0-14 0c0 5.5 7 13 7 13z"/><circle cx="12" cy="9" r="2.5"/></svg>',
  doc:      '<svg class="icon" viewBox="0 0 24 24"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/></svg>',
  download: '<svg class="icon" viewBox="0 0 24 24"><path d="M12 4v12M6 12l6 6 6-6M5 20h14"/></svg>',
  print:    '<svg class="icon" viewBox="0 0 24 24"><path d="M6 9V3h12v6M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><path d="M6 14h12v7H6z"/></svg>',
  filter:   '<svg class="icon" viewBox="0 0 24 24"><path d="M3 5h18M6 12h12M10 19h4"/></svg>',
  refresh:  '<svg class="icon" viewBox="0 0 24 24"><path d="M3 12a9 9 0 0 1 15-6.7L21 8M21 3v5h-5M21 12a9 9 0 0 1-15 6.7L3 16M3 21v-5h5"/></svg>',
  check:    '<svg class="icon" viewBox="0 0 24 24"><path d="m5 12 5 5 9-11"/></svg>',
  alert:    '<svg class="icon" viewBox="0 0 24 24"><path d="M12 9v4M12 17h.01M10.3 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.7 3.86a2 2 0 0 0-3.4 0z"/></svg>',
  external: '<svg class="icon" viewBox="0 0 24 24"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6M15 3h6v6M10 14 21 3"/></svg>',
  layers:   '<svg class="icon" viewBox="0 0 24 24"><path d="m12 2 10 6-10 6L2 8z"/><path d="m2 16 10 6 10-6M2 12l10 6 10-6"/></svg>',
  spinner:  '<svg class="icon spin" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="28 56" /></svg>',
};

/* ── Global state ─────────────────────────────── */
window.__state = {
  currentParcelId: null,   // county_parcel_id of the loaded parcel
  parcelData: null,         // cached /api/parcel response
  compsData: null,          // cached /api/comps response
};

function setState(patch) {
  Object.assign(window.__state, patch);
}

/* ── Helpers ──────────────────────────────────── */

function spinner() {
  return `<div style="display:flex;align-items:center;gap:8px;padding:40px;color:var(--ink-3)">${ICONS.spinner} Loading…</div>`;
}

function errBanner(msg) {
  return `<div class="banner warn" style="margin:20px"><div class="b-icon">${ICONS.alert}</div><div><b>Error.</b> <span class="muted">${msg}</span></div></div>`;
}

async function apiFetch(url) {
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}: ${url}`);
  return resp.json();
}

/* ═══════════════════════════════════════════════
   1. SEARCH
═══════════════════════════════════════════════ */

function renderSearch(host) {
  host.innerHTML = `
    <section class="search-hero">
      <div class="kicker">Step 1 / 5 · Find a property</div>
      <h1>Look up a parcel <em>in Polk or Dallas County</em>, then build a comp set in under a minute.</h1>
      <p class="lede">Enter an address or parcel ID. We'll pull the latest assessment from the county's CAMA system and propose comparable sales within 0.75 mi.</p>

      <form class="search-box" id="search-form" onsubmit="return false;" style="position:relative">
        <select id="county-select" aria-label="County">
          <option value="both">Both counties</option>
          <option value="polk">Polk County</option>
          <option value="dallas">Dallas County</option>
        </select>
        <div style="position:relative;flex:1;display:flex">
          <input id="search-input" type="text"
                 placeholder="e.g. 4823 Grand Ave, Des Moines  ·  or  ·  010-12345-678-000"
                 autocomplete="off" style="flex:1" />
          <ul id="ac-dropdown" role="listbox" style="
            display:none; position:absolute; top:100%; left:0; right:0; z-index:200;
            background:var(--surface); border:1px solid var(--line-2);
            border-radius:var(--r-md); box-shadow:0 6px 24px rgba(0,0,0,.12);
            margin:3px 0 0; padding:4px 0; list-style:none; max-height:280px;
            overflow-y:auto; font-size:13px;
          "></ul>
        </div>
        <button type="submit" class="go" id="search-btn">${ICONS.search} Search</button>
      </form>

      <div class="search-suggest">
        <b>Try:</b>
        <button type="button" class="suggest-chip" data-query="4823 Grand Ave">4823 Grand Ave</button>
        <button type="button" class="suggest-chip" data-query="2210 Park Ave">2210 Park Ave</button>
        <button type="button" class="suggest-chip" data-query="808 42nd St">808 42nd St</button>
        <button type="button" class="suggest-chip" data-query="3401 Ingersoll">3401 Ingersoll</button>
      </div>
    </section>

    <div class="search-grid">
      <div class="card">
        <div class="card-head">
          <div>
            <div class="h2">Search results</div>
            <div class="muted" id="result-count" style="font-size:12px;margin-top:2px">Enter an address above</div>
          </div>
        </div>
        <div id="search-results" class="recent-list">
          <div style="padding:24px;color:var(--ink-3);font-size:13px">No results yet — search above.</div>
        </div>
      </div>

      <div>
        <div class="card">
          <div class="card-head">
            <div class="h2">Coverage</div>
            <span class="pill good"><span class="dot"></span>Live</span>
          </div>
          <div class="coverage-map" aria-hidden="true">
            <span class="pin" style="left:32%; top:42%"></span>
            <span class="pin" style="left:48%; top:54%"></span>
            <span class="pin" style="left:64%; top:38%"></span>
            <span class="pin" style="left:72%; top:62%"></span>
            <span id="parcel-count">Polk + Dallas · loading…</span>
          </div>
          <div class="qstats" id="qstats">
            <div>
              <div class="qstat-label">Parcels</div>
              <div class="qstat-value tnum" id="stat-parcels">—</div>
              <div class="qstat-sub">Polk + Dallas</div>
            </div>
            <div>
              <div class="qstat-label">Recent sales</div>
              <div class="qstat-value tnum" id="stat-sales">—</div>
              <div class="qstat-sub">Arms-length, 2025+</div>
            </div>
            <div>
              <div class="qstat-label">Median A/V ratio</div>
              <div class="qstat-value tnum" id="stat-ratio">—</div>
              <div class="qstat-sub">Trailing 12 months</div>
            </div>
            <div>
              <div class="qstat-label">Protest window</div>
              <div class="qstat-value tnum">Apr 30</div>
              <div class="qstat-sub">Polk &amp; Dallas boards</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;

  // Wire form
  const form = host.querySelector('#search-form');
  const input = host.querySelector('#search-input');
  const btn = host.querySelector('#search-btn');
  const dropdown = host.querySelector('#ac-dropdown');

  // ── Autocomplete typeahead ──────────────────────────────
  let acTimer = null;
  let acActive = -1; // keyboard-highlighted index

  function closeDropdown() {
    dropdown.style.display = 'none';
    dropdown.innerHTML = '';
    acActive = -1;
  }

  function renderDropdown(suggestions) {
    if (!suggestions.length) { closeDropdown(); return; }
    dropdown.innerHTML = suggestions.map((s, i) => `
      <li role="option" data-idx="${i}" style="
        padding:8px 14px; cursor:pointer; display:flex; align-items:baseline;
        gap:8px; border-bottom:1px solid var(--line);
      ">
        <span style="flex:1; font-weight:500; color:var(--ink)">${s.address}, <span style="font-weight:400;color:var(--ink-3)">${s.city}</span></span>
        <span style="font-family:var(--mono); font-size:11px; color:var(--ink-4)">${s.parcel_id}</span>
      </li>
    `).join('');
    dropdown.style.display = 'block';

    dropdown.querySelectorAll('li').forEach((li, i) => {
      li.addEventListener('mouseenter', () => highlightItem(i));
      li.addEventListener('mouseleave', () => highlightItem(-1));
      li.addEventListener('mousedown', e => {
        e.preventDefault(); // prevent blur before click
        selectSuggestion(suggestions[i]);
      });
    });
  }

  function highlightItem(idx) {
    acActive = idx;
    dropdown.querySelectorAll('li').forEach((li, i) => {
      li.style.background = i === idx ? 'var(--accent-tint)' : '';
    });
  }

  function selectSuggestion(s) {
    input.value = s.address + ', ' + s.city;
    closeDropdown();
    // Navigate directly to parcel
    setState({ currentParcelId: s.parcel_id, parcelData: null, compsData: null });
    window.__goto('parcel');
  }

  input.addEventListener('input', () => {
    clearTimeout(acTimer);
    const q = input.value.trim();
    if (q.length < 2) { closeDropdown(); return; }
    acTimer = setTimeout(async () => {
      const county = host.querySelector('#county-select').value;
      try {
        const data = await apiFetch(`/api/autocomplete?q=${encodeURIComponent(q)}&county=${county}`);
        renderDropdown(data.suggestions || []);
      } catch { closeDropdown(); }
    }, 180); // 180ms debounce
  });

  input.addEventListener('keydown', e => {
    const items = dropdown.querySelectorAll('li');
    if (!items.length) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      highlightItem(Math.min(acActive + 1, items.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      highlightItem(Math.max(acActive - 1, -1));
    } else if (e.key === 'Enter' && acActive >= 0) {
      e.preventDefault();
      items[acActive].dispatchEvent(new MouseEvent('mousedown'));
    } else if (e.key === 'Escape') {
      closeDropdown();
    }
  });

  input.addEventListener('blur', () => {
    // Small delay so mousedown on a suggestion fires first
    setTimeout(closeDropdown, 150);
  });

  async function doSearch(q) {
    if (!q) return;
    const county = host.querySelector('#county-select').value;
    input.value = q;
    btn.disabled = true;
    btn.innerHTML = ICONS.spinner + ' Searching…';
    host.querySelector('#search-results').innerHTML = spinner();
    host.querySelector('#result-count').textContent = 'Searching…';

    try {
      const data = await apiFetch(`/api/search?q=${encodeURIComponent(q)}&county=${county}`);
      renderResults(data.results);
    } catch (e) {
      host.querySelector('#search-results').innerHTML = errBanner(e.message);
      host.querySelector('#result-count').textContent = 'Error';
    } finally {
      btn.disabled = false;
      btn.innerHTML = ICONS.search + ' Search';
    }
  }

  form.addEventListener('submit', () => doSearch(input.value.trim()));
  btn.addEventListener('click', () => doSearch(input.value.trim()));
  host.querySelectorAll('.suggest-chip').forEach(chip => {
    chip.addEventListener('click', () => doSearch(chip.dataset.query));
  });

  function renderResults(results) {
    const el = host.querySelector('#search-results');
    const countEl = host.querySelector('#result-count');

    if (!results.length) {
      el.innerHTML = '<div style="padding:24px;color:var(--ink-3);font-size:13px">No matching parcels found.</div>';
      countEl.textContent = '0 results';
      return;
    }

    countEl.textContent = `${results.length} result${results.length !== 1 ? 's' : ''}`;
    el.innerHTML = results.map(r => `
      <div class="recent-row" data-parcel-id="${r.parcel_id}" style="cursor:pointer">
        <div class="when">${r.county}</div>
        <div class="addr">${r.address} <span class="muted" style="font-weight:400;margin-left:8px">${r.city_state}</span></div>
        <div class="pid">${r.parcel_id}</div>
        <div class="delta">${r.assessed_value_fmt}</div>
        <div>${ICONS.arrow}</div>
      </div>
    `).join('');

    el.querySelectorAll('.recent-row').forEach(row => {
      row.addEventListener('click', () => {
        const pid = row.dataset.parcelId;
        setState({ currentParcelId: pid, parcelData: null, compsData: null });
        window.__goto('parcel');
      });
    });
  }

  // Load quick stats from admin endpoint
  apiFetch('/api/admin').then(data => {
    const s = data.stats;
    host.querySelector('#stat-parcels').textContent =
      s.total_properties ? s.total_properties.toLocaleString() : '—';
    host.querySelector('#stat-sales').textContent =
      s.recent_sales_2025_plus ? s.recent_sales_2025_plus.toLocaleString() : '—';
    host.querySelector('#stat-ratio').textContent =
      s.median_av_ratio || '—';
    host.querySelector('#parcel-count').textContent =
      `Polk + Dallas · ${s.total_properties ? s.total_properties.toLocaleString() : '?'} parcels`;
  }).catch(() => {});
}


/* ═══════════════════════════════════════════════
   2. PARCEL
═══════════════════════════════════════════════ */

function renderParcel(host) {
  host.innerHTML = spinner();

  const parcelId = window.__state.currentParcelId;
  if (!parcelId) {
    host.innerHTML = `
      <div style="padding:40px">
        <p style="color:var(--ink-3)">No parcel selected. <a href="#" onclick="window.__goto('search');return false;">Search for one</a>.</p>
      </div>`;
    return;
  }

  // Use cached data if available
  if (window.__state.parcelData) {
    _renderParcelData(host, window.__state.parcelData);
    return;
  }

  apiFetch(`/api/parcel/${encodeURIComponent(parcelId)}`)
    .then(data => {
      setState({ parcelData: data });
      _renderParcelData(host, data);
    })
    .catch(e => { host.innerHTML = errBanner(e.message); });
}

function _renderParcelData(host, p) {
  const fullAddr = `${p.address}, ${p.city} ${p.state} ${p.zip}`.trim();
  const sqftFmt = p.living_area_sqft ? p.living_area_sqft.toLocaleString() + ' sqft' : '—';
  const lotFmt = p.lot_sqft ? p.lot_sqft.toLocaleString() + ' sqft' : '—';
  const bbFmt = `${p.bedrooms ?? '?'} / ${p.bathrooms ?? '?'}`;
  const countyName = p.county ? p.county.charAt(0) + p.county.slice(1).toLowerCase() : '—';

  // Build SVG chart from history
  const chart = p.chart || [];
  const vals = chart.map(c => c.value).filter(Boolean);
  const minV = vals.length ? Math.min(...vals) : 0;
  const maxV = vals.length ? Math.max(...vals) : 1;
  const range = maxV - minV || 1;
  const W = 600, H = 140, PAD = 10;
  const pts = chart.map((c, i) => {
    const x = chart.length > 1 ? (i / (chart.length - 1)) * W : W / 2;
    const y = PAD + (1 - (((c.value || minV) - minV) / range)) * (H - PAD * 2);
    return [x, y];
  });
  const polyline = pts.map(([x, y]) => `${x},${y}`).join(' ');
  const area = polyline + ` ${pts[pts.length - 1][0]},${H} 0,${H}`;

  host.innerHTML = `
    <div class="parcel-head">
      <div>
        <div class="crumbs">
          <a href="#" onclick="window.__goto('search');return false;">Search</a>
          &nbsp;/&nbsp; ${countyName} County &nbsp;/&nbsp;
          <b style="color:var(--ink)">${p.address}</b>
        </div>
        <h1>${fullAddr}</h1>
        <div class="meta">
          <span><b>Parcel</b> <span class="pid">${p.parcel_id}</span></span>
          <span><b>Class</b> ${p.class_code || 'Residential'}</span>
          <span><b>Owner</b> ${p.owner}</span>
          ${p.year_built ? `<span><b>Built</b> ${p.year_built}</span>` : ''}
        </div>
      </div>
      <div class="parcel-actions">
        ${p.county_site_url ? `<a class="btn" href="${p.county_site_url}" target="_blank" rel="noopener">${ICONS.external} View on county site</a>` : ''}
        <button class="btn btn-primary" onclick="window.__goto('comps')">${ICONS.layers} Find comparables ${ICONS.arrow}</button>
      </div>
    </div>

    ${p.flagged ? `
    <div class="banner accent" style="margin-bottom:18px">
      <div class="b-icon">${ICONS.alert}</div>
      <div>
        <b>Year-over-year jump flagged.</b>
        <span class="muted"> Assessed value rose <b style="color:var(--ink)">${p.yoy_pct}</b> from ${p.prev_year} (${p.prev_year_value_fmt}) to ${p.assessment_year} (${p.total_value_fmt}) — outside the typical band. Worth a comp run.</span>
      </div>
      <div class="b-actions">
        <button class="btn btn-sm" onclick="this.closest('.banner').remove()">Dismiss</button>
        <button class="btn btn-sm btn-primary" onclick="window.__goto('comps')">Run comps</button>
      </div>
    </div>` : ''}

    <div class="parcel-grid">

      <div class="card span-2 assess-card">
        <div class="card-pad">
          <div class="h3">Assessment · ${p.assessment_year}</div>
          <div class="nums">
            <div>
              <div class="lbl">Land</div>
              <div class="val tnum">${p.land_value_fmt}</div>
            </div>
            <div>
              <div class="lbl">Improvements</div>
              <div class="val tnum">${p.improvement_value_fmt}</div>
            </div>
            <div>
              <div class="lbl">Total assessed</div>
              <div class="val tnum">${p.total_value_fmt}</div>
            </div>
            <div>
              <div class="lbl">Est. taxes</div>
              <div class="val tnum">${p.estimated_taxes_fmt}<span style="font-size:12px;color:var(--ink-3);font-family:var(--sans);font-weight:400;margin-left:6px">/ yr</span></div>
            </div>
          </div>
          <div class="delta-row">
            <span class="pill ${p.yoy_direction === 'up' ? 'bad' : (p.yoy_direction === 'down' ? 'good' : '')}">
              <span class="dot"></span>${p.yoy_amt_fmt} vs ${p.prev_year}
            </span>
            <a href="#" onclick="window.__goto('comps');return false;">Find comparables</a>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-pad">
          <div class="h3">Property</div>
          <div class="parcel-photo">street view · ${p.address}</div>
          <table class="facts">
            <tr><th>Living area</th><td>${sqftFmt}</td></tr>
            <tr><th>Lot</th><td>${lotFmt}</td></tr>
            <tr><th>Beds / baths</th><td>${bbFmt}</td></tr>
            <tr><th>Style</th><td>${p.bldg_style || '—'}</td></tr>
            ${p.stories ? `<tr><th>Stories</th><td>${p.stories}</td></tr>` : ''}
            ${p.garage_spaces ? `<tr><th>Garage</th><td>${p.garage_spaces}-car</td></tr>` : ''}
            <tr><th>Last sale</th><td>${p.last_sale_price_fmt} · ${p.last_sale_date_fmt}</td></tr>
            <tr><th>Neighborhood</th><td>${p.neighborhood_code}</td></tr>
          </table>
        </div>
      </div>

      <div class="card span-2">
        <div class="card-head">
          <div class="h2">Assessed value · history</div>
          <span class="pill"><span class="dot"></span>${countyName} Co. CAMA</span>
        </div>
        <div class="card-pad">
          <div class="chart">
            <svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">
              <polyline fill="none" stroke="var(--accent)" stroke-width="2" points="${polyline}" />
              <polyline fill="var(--accent)" fill-opacity="0.08" stroke="none" points="${area}" />
              ${pts.map(([x, y]) => `<circle cx="${x}" cy="${y}" r="3" fill="white" stroke="var(--accent)" stroke-width="2"/>`).join('')}
            </svg>
            <div class="x-axis">
              ${chart.map(c => `<span>${c.year}</span>`).join('')}
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-head">
          <div class="h2">Est. tax bill · history</div>
        </div>
        <div class="card-pad">
          <div class="tax-rows">
            ${(p.tax_rows || []).map(r => `
              <div class="row">
                <div class="yr">${r.year}</div>
                <div class="bar"><span style="width:80%"></span></div>
                <div class="amt tnum">${r.estimated_tax}</div>
                <div class="chg ${r.direction}">${r.change_pct}</div>
              </div>
            `).join('')}
          </div>
        </div>
      </div>

    </div>
  `;
}


/* ═══════════════════════════════════════════════
   3. COMPS
═══════════════════════════════════════════════ */

function renderComps(host) {
  host.innerHTML = spinner();

  const parcelId = window.__state.currentParcelId;
  if (!parcelId) {
    host.innerHTML = `
      <div style="padding:40px">
        <p style="color:var(--ink-3)">No parcel loaded. <a href="#" onclick="window.__goto('search');return false;">Search first</a>.</p>
      </div>`;
    return;
  }

  if (window.__state.compsData) {
    _renderCompsData(host, window.__state.compsData);
    return;
  }

  apiFetch(`/api/comps/${encodeURIComponent(parcelId)}`)
    .then(data => {
      if (data.error) throw new Error(data.error);
      setState({ compsData: data });
      _renderCompsData(host, data);
    })
    .catch(e => { host.innerHTML = errBanner(e.message); });
}

function _renderCompsData(host, data) {
  const subj = data.subject;
  const comps = data.comps || [];
  const all = data.all_rows || [subj, ...comps];
  const v = data.verdict;

  // Rough scatter positions for the fake map
  const positions = [[50,50],[56,46],[41,60],[47,35],[64,56],[32,42],[70,68],[58,28],[28,65]];
  const allWithPos = all.map((r, i) => ({ ...r, x: (positions[i] || [50,50])[0], y: (positions[i] || [50,50])[1] }));

  const subjectDetail = data.subject_detail || {};
  const addr = subj.address || subjectDetail.address || '—';

  host.innerHTML = `
    <div class="comps-head">
      <div>
        <div class="crumbs">
          <a href="#" onclick="window.__goto('parcel');return false;">${addr}</a>
          &nbsp;/&nbsp; <b style="color:var(--ink)">Comparable sales</b>
        </div>
        <h1>${comps.length} comparable sale${comps.length !== 1 ? 's' : ''} · within 0.75 mi · last 6 months</h1>
      </div>
      <div class="comps-toolbar">
        <button class="btn" id="rerun-btn">${ICONS.refresh} Re-run</button>
        <button class="btn btn-primary" onclick="window.__goto('packet')">${ICONS.doc} Build protest packet ${ICONS.arrow}</button>
      </div>
    </div>

    <div class="banner warn" id="freshness-banner" hidden style="margin-bottom:14px">
      <div class="b-icon">${ICONS.alert}</div>
      <div>
        <b>Data may be stale.</b>
        <span class="muted"> Verify any comp before filing.</span>
      </div>
    </div>

    <div class="banner" id="vanguard-banner" style="margin-bottom:18px">
      <div class="b-icon">${ICONS.alert}</div>
      <div>
        <b>Vanguard migration · advisory.</b>
        <span class="muted"> Polk County is moving CAMA records from Tyler to Vanguard. Sale dates &amp; PIDs may shift formats during the cutover.</span>
      </div>
      <div class="b-actions">
        <button class="btn btn-sm" onclick="document.getElementById('vanguard-banner').remove()">Dismiss</button>
      </div>
    </div>

    <div class="conclusion ${v.state}" id="conclusion">
      <div class="gauge">
        <div style="text-align:center">
          <div class="pct" id="conc-pct">${v.pct_str}</div>
          <div class="lbl">${v.lbl}</div>
        </div>
      </div>
      <div>
        <div class="verdict" id="conc-verdict">${v.verdict_html}</div>
        <div class="why" id="conc-why">${v.why}</div>
      </div>
      <div class="actions">
        <button class="btn" onclick="document.getElementById('method-card').scrollIntoView({behavior:'smooth'})">View methodology</button>
        <button class="btn btn-primary" onclick="window.__goto('packet')">${ICONS.doc} Generate packet</button>
      </div>
    </div>

    <div class="comps-layout" id="comps-layout">

      <div class="map-card card" id="map-card">
        <div class="map" id="map">
          <div class="grid"></div>
          <div class="road h1"></div>
          <div class="road h2"></div>
          <div class="road v1"></div>
          <div class="road v2"></div>
          ${allWithPos.map(c => `
            <div class="pin ${c.subj ? 'subject' : ''}" style="left:${c.x}%;top:${c.y}%" title="${c.address}">${c.n}</div>
          `).join('')}
        </div>
        <div class="map-legend">
          <span><span class="swatch" style="background:var(--ink)"></span>Subject</span>
          <span><span class="swatch" style="background:var(--accent)"></span>Comp sales</span>
          <span class="map-attrib">EPSG:4326</span>
        </div>
      </div>

      <div class="comp-table-card card">
        <div class="comp-controls">
          <div class="seg">
            <button class="is-active">All comps</button>
          </div>
          <div class="right">
            <span>Sort</span>
            <div class="seg">
              <button class="is-active">Similarity</button>
              <button onclick="sortCompsBy('psf')">$/sqft</button>
              <button onclick="sortCompsBy('dist')">Distance</button>
            </div>
          </div>
        </div>
        <table class="comp-table" id="comp-table">
          <thead>
            <tr>
              <th style="width:40px"></th>
              <th>Address</th>
              <th class="num" style="width:74px">Sqft</th>
              <th style="width:62px">Bd/Ba</th>
              <th class="num" style="width:60px">Year</th>
              <th class="num" style="width:80px">Distance</th>
              <th class="num" style="width:96px">Sale date</th>
              <th class="num" style="width:96px">Sale price</th>
              <th class="num" style="width:70px">$/sqft</th>
              <th style="width:120px">Similarity</th>
            </tr>
          </thead>
          <tbody>
            ${allWithPos.map(c => `
              <tr class="${c.subj ? 'subject' : ''}">
                <td><span class="pin-num">${c.n}</span></td>
                <td>
                  <div class="addr">${c.address}</div>
                  <div class="pid">${c.city} · ${c.parcel_id}</div>
                </td>
                <td class="num">${c.sqft_fmt || c.sqft || '—'}</td>
                <td>${c.bb || '—'}</td>
                <td class="num">${c.year_built || '—'}</td>
                <td class="num">${c.distance_fmt || '—'}</td>
                <td class="num">${c.sale_date_fmt || '—'}</td>
                <td class="num"><b>${c.sale_price_fmt}</b></td>
                <td class="num">${c.psf_fmt || '—'}</td>
                <td>
                  <span class="simbar">
                    <span class="track"><span class="fill" style="width:${c.similarity}%"></span></span>
                    <span class="pct">${c.similarity}</span>
                  </span>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>

    </div>

    <div class="card method-card" id="method-card" style="margin-top:20px">
      <div class="card-head">
        <div class="h2">How we picked these</div>
      </div>
      <div class="card-pad">
        <div class="steps">
          <div class="step"><div class="n">01 / Filter</div><b>Geo + recency</b>Residential parcels within 0.75 mi sold in the last 6 months, arms-length only.</div>
          <div class="step"><div class="n">02 / Score</div><b>Similarity score</b>Living area ±20% (30%), recency (25%), neighborhood (15%), age ±15 yrs (15%), distance (10%), lot ±25% (5%).</div>
          <div class="step"><div class="n">03 / Select</div><b>Top comps</b>Up to 10 highest-scoring comparable sales. Expands search radius if not enough same-neighborhood comps.</div>
          <div class="step"><div class="n">04 / Conclude</div><b>Median $/sqft</b>Weighted median applied to subject sqft, compared to assessor's value. &gt;10% over = protest candidate.</div>
        </div>
      </div>
    </div>
  `;

  // Re-run button
  host.querySelector('#rerun-btn').addEventListener('click', () => {
    setState({ compsData: null });
    renderComps(host);
  });
}

window.sortCompsBy = function(field) { /* future: re-sort table rows */ };


/* ═══════════════════════════════════════════════
   4. ADMIN
═══════════════════════════════════════════════ */

function renderAdmin(host) {
  host.innerHTML = spinner();

  apiFetch('/api/admin')
    .then(data => _renderAdminData(host, data))
    .catch(e => { host.innerHTML = errBanner(e.message); });
}

function _renderAdminData(host, data) {
  const sources = data.sources || [];
  const runs = data.runs || [];
  const config = data.config || {};
  const health = data.health || {};

  const STATUS_LABEL = { good: 'OK', warn: 'Lag', bad: 'Down' };

  // Build log lines from recent runs
  const logLines = runs.slice(0, 15).map(r => {
    const statusClass = r.status === 'success' ? 'ok' : (r.status === 'error' ? 'err' : 'warn');
    const statusText = r.status === 'success' ? 'done' : r.status;
    return `<span class="ts">[${r.started}]</span> ${r.source.padEnd(30)} ins=${r.inserted} upd=${r.updated} <span class="${statusClass}">${statusText} ${r.duration}</span>${r.error ? ` <span class="err">${r.error}</span>` : ''}`;
  }).join('\n') || '(no runs recorded yet)';

  host.innerHTML = `
    <div class="parcel-head">
      <div>
        <div class="crumbs">Operator console</div>
        <h1>Data admin</h1>
        <div class="meta">
          <span><b>Env</b> local</span>
          <span><b>Build</b> <span class="pid">v1.5 · iowa_propertytax</span></span>
          <span><b>DB</b> PostgreSQL 18</span>
        </div>
      </div>
      <div class="parcel-actions">
        <button class="btn" id="refresh-admin-btn">${ICONS.refresh} Refresh stats</button>
      </div>
    </div>

    <div class="admin-grid">
      <div>
        <div class="card">
          <div class="card-head">
            <div class="h2">Data sources</div>
            <span class="pill"><span class="dot"></span>${sources.filter(s => s.status === 'good').length} active</span>
          </div>
          <div>
            ${sources.map(s => `
              <div class="source-row">
                <span class="pill ${s.status}"><span class="dot"></span>${STATUS_LABEL[s.status] || s.status}</span>
                <div>
                  <div class="label">${s.name}</div>
                  <div class="desc">${s.desc}</div>
                </div>
                <div class="count">${s.count}</div>
                <div class="stamp">${s.stamp}</div>
              </div>
            `).join('')}
          </div>
        </div>

        <div class="card" style="margin-top:20px">
          <div class="card-head">
            <div class="h2">Ingestion run log</div>
          </div>
          <div class="card-pad">
            <pre class="runlog">${logLines}</pre>
          </div>
        </div>
      </div>

      <div>
        <div class="card">
          <div class="card-head">
            <div class="h2">Health</div>
            <span class="pill good"><span class="dot"></span>DB connected</span>
          </div>
          <div class="card-pad">
            <div class="kv">
              ${Object.entries(health).map(([k, v]) => `
                <div class="k">${k}</div><div class="v">${v}</div>
              `).join('')}
            </div>
          </div>
        </div>

        <div class="card" style="margin-top:20px">
          <div class="card-head">
            <div class="h2">Configuration</div>
          </div>
          <div class="card-pad">
            <table class="facts">
              ${Object.entries(config).map(([k, v]) => `<tr><th>${k}</th><td>${v}</td></tr>`).join('')}
            </table>
          </div>
        </div>
      </div>
    </div>
  `;

  host.querySelector('#refresh-admin-btn').addEventListener('click', () => {
    renderAdmin(host);
  });
}


/* ═══════════════════════════════════════════════
   5. PACKET
═══════════════════════════════════════════════ */

function renderPacket(host) {
  const parcelId = window.__state.currentParcelId;
  const parcel = window.__state.parcelData;
  const comps = window.__state.compsData;

  if (!parcelId || !parcel || !comps) {
    host.innerHTML = `
      <div style="padding:40px">
        <p style="color:var(--ink-3)">Run a comp analysis first before generating a packet.
          <a href="#" onclick="window.__goto('search');return false;">Start over</a>.</p>
      </div>`;
    return;
  }

  const v = comps.verdict;
  const allComps = comps.comps || [];
  const addr = parcel.address || '—';
  const fullAddr = `${addr}, ${parcel.city} ${parcel.state} ${parcel.zip}`.trim();
  const today = new Date().toISOString().split('T')[0];
  const owner = parcel.owner || '—';

  host.innerHTML = `
    <div class="parcel-head">
      <div>
        <div class="crumbs">
          <a href="#" onclick="window.__goto('comps');return false;">Comps</a>
          &nbsp;/&nbsp; <b style="color:var(--ink)">Protest packet</b>
        </div>
        <h1>Protest packet · ${addr}</h1>
        <div class="meta">
          <span><b>Pages</b> 3 · letter</span>
          <span><b>Filed by</b> ${owner}</span>
          <span><b>Deadline</b> Apr 30, 2026</span>
        </div>
      </div>
      <div class="parcel-actions">
        <button class="btn" onclick="window.print()">${ICONS.print} Print</button>
        <a class="btn btn-primary" href="/api/packet/${encodeURIComponent(parcelId)}" target="_blank">${ICONS.download} Download PDF</a>
      </div>
    </div>

    <div class="packet-layout">
      <aside class="packet-side">
        <div class="h3">Pages</div>
        <ul>
          <li class="is-active">Cover &amp; summary <span class="pgnum">1</span></li>
          <li>Comp grid <span class="pgnum">2</span></li>
          <li>Methodology <span class="pgnum">3</span></li>
        </ul>

        <div class="h3" style="margin-top:18px">Include</div>
        <div style="padding:0 4px;display:grid;gap:6px;font-size:12.5px">
          <label style="display:flex;gap:8px;align-items:center"><input type="checkbox" checked> Cover letter</label>
          <label style="display:flex;gap:8px;align-items:center"><input type="checkbox" checked> Comp grid</label>
          <label style="display:flex;gap:8px;align-items:center"><input type="checkbox" checked> Methodology page</label>
          <label style="display:flex;gap:8px;align-items:center"><input type="checkbox"> Map exhibit</label>
        </div>
      </aside>

      <div>
        <div class="paper">
          <div class="pg-stamp">Page 1 of 3</div>
          <div class="deck-h">
            <span>${parcel.county ? parcel.county.charAt(0) + parcel.county.slice(1).toLowerCase() : '—'} County · Board of Review · 2026 Protest</span>
            <span>Filed ${today}</span>
          </div>
          <h2 class="cover">Petition to adjust assessed value, ${fullAddr}.</h2>
          <p style="font-family:var(--sans);font-size:13.5px;color:var(--ink-2);max-width:560px">
            The 2026 assessment of <b style="color:var(--ink)">${v.assessed_fmt}</b> is approximately
            <b style="color:var(--ink)">${v.pct_str} ${v.lbl === 'over' ? 'above' : 'below'}</b>
            a similarity-weighted comp median of <b style="color:var(--ink)">${v.implied_value_fmt}</b>,
            drawn from ${v.n_comps} arms-length sales within 0.75 mi over the last 6 months.
            ${v.state === 'over' ? `We respectfully request a revised value of <b style="color:var(--ink)">${v.implied_value_fmt}</b>.` : ''}
          </p>

          <div class="cover-meta">
            <b>Parcel</b><span style="font-family:var(--mono)">${parcel.parcel_id}</span>
            <b>Owner</b><span>${owner}</span>
            <b>Class</b><span>${parcel.class_code || 'Residential'}</span>
            <b>Current value</b><span style="font-family:var(--mono)">${v.assessed_fmt}</span>
            <b>Implied comp value</b><span style="font-family:var(--mono)">${v.implied_value_fmt}</span>
            <b>Verdict</b><span style="font-family:var(--mono);color:var(--${v.state === 'over' ? 'bad' : (v.state === 'under' ? 'good' : 'ink-2')})">${v.lbl} ${v.pct_str}</span>
          </div>

          <h3 class="section">Comp set summary</h3>
          <table class="summary-table">
            <thead><tr>
              <th>Address</th>
              <th class="num">Sqft</th>
              <th class="num">Sale date</th>
              <th class="num">Price</th>
              <th class="num">$/sqft</th>
            </tr></thead>
            <tbody>
              <tr class="subject">
                <td>${addr} <span style="font-family:var(--mono);color:var(--ink-3);font-size:11px">· subject</span></td>
                <td class="num">${parcel.living_area_sqft ? parcel.living_area_sqft.toLocaleString() : '—'}</td>
                <td class="num">—</td>
                <td class="num">${v.assessed_fmt}*</td>
                <td class="num">—</td>
              </tr>
              ${allComps.map(c => `
                <tr>
                  <td>${c.address}</td>
                  <td class="num">${c.sqft_fmt || '—'}</td>
                  <td class="num">${c.sale_date_fmt || '—'}</td>
                  <td class="num">${c.sale_price_fmt || '—'}</td>
                  <td class="num">${c.psf_fmt || '—'}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
          <p style="font-family:var(--sans);font-size:11.5px;color:var(--ink-3);margin-top:10px">
            * Subject value shown is the assessor's ${parcel.assessment_year} figure; not a sale.
          </p>

          <div class="seal">Comp Engine<br>v1.5<br>Iowa PTax</div>
        </div>
      </div>
    </div>
  `;
}


/* ═══════════════════════════════════════════════
   Registry
═══════════════════════════════════════════════ */

window.__renderers = {
  search: renderSearch,
  parcel: renderParcel,
  comps:  renderComps,
  admin:  renderAdmin,
  packet: renderPacket,
};
