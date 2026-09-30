#!/usr/bin/env node
/* Post-deploy smoke test for idearipper.com (added 2026-09-30).
   node tools/smoke.js [URL] [--expect-build MARKER] [--wait SECONDS] [--shots PREFIX] [--json FILE]
   Needs puppeteer-core and Chrome (CHROME_PATH, default /usr/bin/google-chrome).
   Exit 1 on: JS errors, horizontal overflow at 390 or 1366 (on load or after opening
   a book), Save not persisting to localStorage / Saved count not updating, Copy
   without a toast, build marker mismatch. */
const puppeteer = require('puppeteer-core');
const fs = require('fs');
const argv = process.argv.slice(2);
const opt = (k, d) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : d; };
const URL0 = (argv[0] && !argv[0].startsWith('--')) ? argv[0] : 'https://idearipper.com/';
const EXPECT = opt('--expect-build', '');
const WAIT = +opt('--wait', '0');
const SHOTS = opt('--shots', '');
const JSONOUT = opt('--json', '');
const BOOK = opt('--book', 'b-superintelligence-nick-bostrom');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const bust = u => u + (u.includes('?') ? '&' : '?') + 'smoke=' + Date.now();
const fails = [];
const res = { url: URL0, when: new Date().toISOString() };

async function waitForBuild(br) {
  if (!EXPECT) return;
  const t0 = Date.now();
  for (;;) {
    const p = await br.newPage();
    let got = '';
    try {
      await p.goto(bust(URL0), { waitUntil: 'domcontentloaded', timeout: 60000 });
      got = await p.$eval('meta[name=build]', m => m.content).catch(() => '');
    } catch (e) { got = 'ERR ' + e.message; }
    await p.close();
    if (got.startsWith(EXPECT)) { res.build = got; res.waitedSec = Math.round((Date.now() - t0) / 1000); return; }
    if ((Date.now() - t0) / 1000 > WAIT) { fails.push(`live build marker "${got}" != expected "${EXPECT}"`); res.build = got; return; }
    await sleep(20000);
  }
}

async function run(br, name, w, h, mob) {
  const r = {};
  const p = await br.newPage();
  const errs = [];
  p.on('pageerror', e => errs.push(String(e.message)));
  p.on('console', m => { if (m.type() === 'error' && !/countapi|net::ERR|Failed to load resource/.test(m.text())) errs.push('console: ' + m.text()); });
  await p.setViewport({ width: w, height: h, deviceScaleFactor: 1, isMobile: mob, hasTouch: mob });
  const ctx = br.defaultBrowserContext();
  try { await ctx.overridePermissions(new URL(URL0).origin, ['clipboard-read', 'clipboard-write', 'clipboard-sanitized-write']); } catch (_) {}
  const resp = await p.goto(bust(URL0), { waitUntil: 'networkidle2', timeout: 90000 });
  r.htmlBytes = (await resp.buffer()).length;
  r.build = await p.$eval('meta[name=build]', m => m.content).catch(() => '(none)');
  r.dom = await p.evaluate(() => document.getElementsByTagName('*').length);
  r.colorScheme = await p.$eval('meta[name=color-scheme]', m => m.content).catch(() => '');
  r.googleFonts = await p.evaluate(() => performance.getEntriesByType('resource').filter(e => /fonts\.(googleapis|gstatic)/.test(e.name)).length);
  const ov = () => p.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  r.overflowLoad = await ov();
  if (SHOTS) await p.screenshot({ path: `${SHOTS}-${name}-home.png` });
  // open a book and its first card
  await p.evaluate(b => { const s = document.getElementById(b); s.scrollIntoView(); s.querySelector('.bookhead').click(); }, BOOK);
  await sleep(700);
  const cid = await p.evaluate(b => { const c = document.querySelector('#' + b + ' .card'); c.querySelector('.cardhead').click(); return c.dataset.n; }, BOOK);
  await sleep(700);
  r.overflowBookOpen = await ov();
  if (SHOTS) {
    await p.evaluate(b => { document.getElementById(b).scrollIntoView(); window.scrollBy(0, -90); }, BOOK);
    await sleep(300);
    await p.screenshot({ path: `${SHOTS}-${name}-book-open.png` });
  }
  // Save
  let e0 = errs.length;
  await p.evaluate(id => document.querySelector('#c' + id + ' [data-save]').click(), cid);
  await sleep(400);
  r.save = await p.evaluate(id => ({
    ls: localStorage.getItem('idearipper.saved.v1'),
    pressed: document.querySelector('#c' + id + ' [data-save]').getAttribute('aria-pressed'),
    chip: (document.getElementById('savedchip') || {}).textContent,
    toast: (document.getElementById('toast') || {}).textContent
  }), cid);
  r.save.errors = errs.slice(e0);
  const saved = JSON.parse(r.save.ls || '[]');
  if (!saved.includes(+cid)) fails.push(`${name}: Save did not persist to localStorage (${r.save.ls})`);
  if (!/Saved \(1\)/.test(r.save.chip || '')) fails.push(`${name}: Saved chip not updated (${r.save.chip})`);
  // reload: persisted + button state
  await p.reload({ waitUntil: 'networkidle2' });
  r.save.afterReload = await p.evaluate(id => ({ ls: localStorage.getItem('idearipper.saved.v1'), chip: (document.getElementById('savedchip') || {}).textContent,
    pressed: (document.querySelector('#c' + id + ' [data-save]') || { getAttribute: () => '(lazy)' }).getAttribute('aria-pressed') }), cid);
  if (!/Saved \(1\)/.test(r.save.afterReload.chip || '')) fails.push(`${name}: Saved count lost after reload`);
  // Copy
  await p.evaluate(b => { const s = document.getElementById(b); if (s.classList.contains('collapsed')) s.querySelector('.bookhead').click(); }, BOOK);
  await sleep(500);
  e0 = errs.length;
  await p.evaluate(b => { const c = document.querySelector('#' + b + ' .card'); if (!c.classList.contains('open')) c.querySelector('.cardhead').click(); c.querySelector('[data-copy="steal"]').click(); }, BOOK);
  await sleep(500);
  r.copy = { toast: await p.$eval('#toast', t => t.textContent + '|' + t.className), errors: errs.slice(e0) };
  if (!/show/.test(r.copy.toast) || !/Cop/.test(r.copy.toast)) fails.push(`${name}: Copy showed no toast (${r.copy.toast})`);
  r.overflowAfterActions = await ov();
  // search: AND of words
  await p.evaluate(() => { localStorage.removeItem('idearipper.saved.v1'); });
  await p.goto(bust(URL0), { waitUntil: 'networkidle2' });
  await p.type('#q', 'stuck project');
  await sleep(900);
  r.searchStuckProject = await p.evaluate(() => ({ count: document.getElementById('count').textContent,
    nores: !document.getElementById('noresults').hidden, hint: document.getElementById('noresults').textContent.slice(0, 160) }));
  r.overflowSearch = await ov();
  r.errors = errs;
  if (errs.length) fails.push(`${name}: JS errors: ${errs.join(' | ')}`);
  for (const k of ['overflowLoad', 'overflowBookOpen', 'overflowAfterActions', 'overflowSearch'])
    if (r[k] > 0) fails.push(`${name}: horizontal overflow ${k}=${r[k]}px`);
  if (r.googleFonts) fails.push(`${name}: ${r.googleFonts} Google Fonts requests`);
  if (r.colorScheme !== 'light') fails.push(`${name}: color-scheme=${r.colorScheme}`);
  await p.close();
  return r;
}

async function deepLink(br) {
  // shared-link stability: /#b-... at 390; record CLS and scroll positions
  const p = await br.newPage();
  await p.setViewport({ width: 390, height: 844, isMobile: true, hasTouch: true });
  await p.evaluateOnNewDocument(() => {
    window.__cls = 0;
    new PerformanceObserver(l => { for (const e of l.getEntries()) if (!e.hadRecentInput) window.__cls += e.value; })
      .observe({ type: 'layout-shift', buffered: true });
  });
  const errs = []; p.on('pageerror', e => errs.push(String(e.message)));
  await p.goto(bust(URL0) + '#' + BOOK, { waitUntil: 'load', timeout: 90000 });
  const samples = [];
  for (const t of [300, 1200, 2500, 4000]) {
    await sleep(t - (samples.length ? [300, 1200, 2500, 4000][samples.length - 1] : 0));
    samples.push(await p.evaluate(b => ({ y: Math.round(scrollY), top: Math.round(document.getElementById(b).getBoundingClientRect().top),
      open: !document.getElementById(b).classList.contains('collapsed') }), BOOK));
  }
  const cls = await p.evaluate(() => window.__cls);
  if (SHOTS) await p.screenshot({ path: `${SHOTS}-deeplink-390.png` });
  await p.close();
  const last = samples[samples.length - 1];
  const stable = samples.slice(1).every(s => Math.abs(s.top - last.top) <= 2);
  if (!last.open) fails.push('deeplink: book not open');
  if (last.top < -5 || last.top > 200) fails.push(`deeplink: book top at ${last.top}px, not near the top`);
  if (errs.length) fails.push('deeplink JS errors: ' + errs.join(' | '));
  return { samples, cls: +cls.toFixed(4), stable, errors: errs };
}

(async () => {
  const br = await puppeteer.launch({ executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome', headless: 'new', args: ['--no-sandbox'] });
  try {
    await waitForBuild(br);
    res.m390 = await run(br, 'mobile-390', 390, 844, true);
    res.d1366 = await run(br, 'desktop-1366', 1366, 900, false);
    res.deeplink = await deepLink(br);
  } catch (e) { fails.push('smoke crashed: ' + e.stack); }
  await br.close();
  res.fails = fails; res.ok = !fails.length;
  if (JSONOUT) fs.writeFileSync(JSONOUT, JSON.stringify(res, null, 2));
  console.log(JSON.stringify(res, null, 2));
  process.exit(fails.length ? 1 : 0);
})();
