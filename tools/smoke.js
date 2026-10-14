#!/usr/bin/env node
/* Post-deploy smoke test for idearipper.com (rewritten 2026-10-14 for the
   Archive Paper redesign; same CLI as the hunt-layer version).
   node tools/smoke.js [URL] [--expect-build MARKER] [--wait SECONDS] [--shots PREFIX] [--json FILE]
   Needs puppeteer-core and Chrome (CHROME_PATH, default /usr/bin/google-chrome).
   Exit 1 on: JS errors, horizontal overflow at 390 or 1366, build marker
   mismatch, #cN hash redirect broken, command-bar jump/search broken,
   card-page prev/next or Copy ID broken, ledger incomplete. */
const puppeteer = require('puppeteer-core');
const fs = require('fs');
const argv = process.argv.slice(2);
const opt = (k, d) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : d; };
const URL0 = (argv[0] && !argv[0].startsWith('--')) ? argv[0] : 'https://idearipper.com/';
const EXPECT = opt('--expect-build', '');
const WAIT = +opt('--wait', '0');
const SHOTS = opt('--shots', '');
const JSONOUT = opt('--json', '');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const bust = u => u + (u.includes('?') ? '&' : '?') + 'smoke=' + Date.now();
const fails = [];
const res = { url: URL0, when: new Date().toISOString() };
const BASE = URL0.replace(/\/?$/, '/');

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

async function homeShell(br, name, w, h, mob) {
  const r = {};
  const p = await br.newPage();
  const errs = [];
  p.on('pageerror', e => errs.push(String(e.message)));
  p.on('console', m => { if (m.type() === 'error' && !/net::ERR|Failed to load resource/.test(m.text())) errs.push('console: ' + m.text()); });
  await p.setViewport({ width: w, height: h, deviceScaleFactor: 1, isMobile: mob, hasTouch: mob });
  const resp = await p.goto(bust(URL0), { waitUntil: 'networkidle2', timeout: 90000 });
  r.status = resp.status();
  r.build = await p.$eval('meta[name=build]', m => m.content).catch(() => '(none)');
  r.colorScheme = await p.$eval('meta[name=color-scheme]', m => m.content).catch(() => '');
  r.googleFonts = await p.evaluate(() => performance.getEntriesByType('resource').filter(e => /fonts\.(googleapis|gstatic)/.test(e.name)).length);
  r.commandbar = await p.evaluate(() => !!document.getElementById('commandbar'));
  r.overflow = await p.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  if (SHOTS) await p.screenshot({ path: `${SHOTS}-${name}-home.png` });
  if (r.status !== 200) fails.push(`${name}: homepage HTTP ${r.status}`);
  if (EXPECT && !r.build.startsWith(EXPECT)) fails.push(`${name}: build marker "${r.build}" != "${EXPECT}"`);
  if (r.colorScheme !== 'light') fails.push(`${name}: color-scheme "${r.colorScheme}" != light`);
  if (r.googleFonts) fails.push(`${name}: ${r.googleFonts} Google Fonts resources loaded`);
  if (!r.commandbar) fails.push(`${name}: command bar missing`);
  if (r.overflow > 0) fails.push(`${name}: horizontal overflow ${r.overflow}px on homepage`);
  if (errs.length) fails.push(`${name}: JS errors: ${errs.slice(0, 3).join(' | ')}`);
  await p.close();
  return r;
}

(async () => {
  const br = await puppeteer.launch({
    executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome',
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
  });
  try {
    await waitForBuild(br);
    res.desktop = await homeShell(br, 'desktop', 1366, 900, false);
    res.mobile = await homeShell(br, 'mobile', 390, 844, true);

    // #cN hash redirect -> stub -> canonical card page
    const p = await br.newPage();
    const errs = [];
    p.on('pageerror', e => errs.push(String(e.message)));
    await p.setViewport({ width: 390, height: 844, isMobile: true, hasTouch: true });
    try { await br.defaultBrowserContext().overridePermissions(new URL(URL0).origin, ['clipboard-read', 'clipboard-write', 'clipboard-sanitized-write']); } catch (_) {}
    await p.goto(BASE + '#c12', { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForFunction(() => /\/c\/12-[a-z0-9-]+\/$/.test(location.pathname), { timeout: 20000 }).catch(() => {});
    res.hashLanding = await p.evaluate(() => location.pathname);
    if (!/^\/c\/12-[a-z0-9-]+\/$/.test(res.hashLanding)) fails.push(`hash redirect: /#c12 landed on ${res.hashLanding}`);
    res.cardTitle = await p.title();
    if (!/#c12/.test(res.cardTitle)) fails.push(`card page title missing #c12: "${res.cardTitle}"`);
    const nav = await p.evaluate(() => ({
      prev: !!document.querySelector('.navrow a[href^="/c/"]'),
      quote: !!document.querySelector('blockquote.theline'),
      copy: !!document.getElementById('copyx'),
    }));
    if (!nav.quote) fails.push('card page: the-line blockquote missing');
    if (!nav.copy) fails.push('card page: Copy for X button missing');
    if (!nav.prev) fails.push('card page: prev/next nav missing');
    await p.click('#copyid').catch(() => {});
    await sleep(400);
    const clip = await p.evaluate(() => navigator.clipboard.readText().catch(() => '')).catch(() => '');
    if (clip && !/idearipper\.com\/c\/12$/.test(clip)) fails.push(`Copy ID clipboard = "${clip}"`);
    if (errs.length) fails.push(`card page JS errors: ${errs.slice(0, 3).join(' | ')}`);
    if (SHOTS) await p.screenshot({ path: `${SHOTS}-card.png` });
    await p.close();

    // command bar: numeric jump + keyword hits
    const q = await br.newPage();
    await q.setViewport({ width: 390, height: 844, isMobile: true, hasTouch: true });
    await q.goto(bust(URL0), { waitUntil: 'domcontentloaded', timeout: 60000 });
    await q.type('#cb-input', 'war');
    await q.waitForFunction(() => document.querySelectorAll('.cb-hit').length > 0, { timeout: 25000 }).catch(() => {});
    res.cbHits = await q.evaluate(() => document.querySelectorAll('.cb-hit').length);
    if (!res.cbHits) fails.push('command bar: keyword "war" produced no hits');
    await q.evaluate(() => { document.getElementById('cb-input').value = ''; });
    await q.type('#cb-input', '402');
    await q.keyboard.press('Enter');
    await q.waitForFunction(() => /^\/c\/402/.test(location.pathname), { timeout: 15000 }).catch(() => {});
    res.cbJump = await q.evaluate(() => location.pathname);
    if (!/^\/c\/402/.test(res.cbJump)) fails.push(`command bar: "402" + Enter landed on ${res.cbJump}`);
    await q.close();

    // ledger completeness
    const l = await br.newPage();
    await l.setViewport({ width: 390, height: 844, isMobile: true, hasTouch: true });
    const lresp = await l.goto(BASE + 'ledger/', { waitUntil: 'domcontentloaded', timeout: 60000 });
    res.ledgerStatus = lresp.status();
    res.ledgerRows = await l.evaluate(() => document.querySelectorAll('table.ledger tbody tr').length);
    res.ledgerOverflow = await l.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    if (res.ledgerStatus !== 200) fails.push(`ledger HTTP ${res.ledgerStatus}`);
    if (res.ledgerRows < 1000) fails.push(`ledger rows ${res.ledgerRows} < 1000`);
    if (res.ledgerOverflow > 0) fails.push(`ledger horizontal overflow ${res.ledgerOverflow}px at 390`);
    await l.close();
  } catch (e) {
    fails.push('smoke crashed: ' + e.message);
  } finally {
    await br.close();
  }
  res.ok = fails.length === 0;
  res.fails = fails;
  console.log(JSON.stringify(res, null, 1));
  if (JSONOUT) fs.writeFileSync(JSONOUT, JSON.stringify(res, null, 1));
  process.exit(res.ok ? 0 : 1);
})();
