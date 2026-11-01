// Wide-screen UI smoke on the integrated build (the same checks as smoke.py, in Node's Playwright):
//   node smoke.js BASE_URL OUT_DIR EARLY_GID NATION
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const [base, out, earlyGid, nation] = process.argv.slice(2);
fs.mkdirSync(out, { recursive: true });
const res = { pages: {}, problems: [] };
const bad = (m) => res.problems.push(m);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  async function visit(name, p) {
    const t = Date.now();
    const r = await pg.goto(base + p, { waitUntil: 'load', timeout: 600000 });
    const took = (Date.now() - t) / 1000;
    await pg.screenshot({ path: path.join(out, name + '.png'), fullPage: true });
    const html = await pg.content();
    const width = await pg.evaluate(() => document.documentElement.scrollWidth);
    res.pages[name] = { path: p, status: r ? r.status() : null, seconds: took, width };
    if (!r || r.status() !== 200) bad(`${name}: status ${r ? r.status() : null}`);
    if (html.includes('Traceback') || html.includes('Internal error')) bad(`${name}: error text on the page`);
    return html;
  }
  async function column(header) {
    return await pg.evaluate((header) => {
      const t = [...document.querySelectorAll('table')].find((x) =>
        [...x.querySelectorAll('thead th')].some((h) => h.textContent.trim() === header));
      if (!t) return null;
      const heads = [...t.querySelectorAll('thead th')].map((h) => h.textContent.trim());
      const i = heads.indexOf(header);
      if (i < 0) return null;
      return [...t.querySelectorAll('tbody tr')].map((r) => (r.querySelectorAll('td')[i] || {}).innerText || '');
    }, header);
  }
  const nums = (xs) => (xs || []).map((x) => parseFloat(x)).filter((x) => !Number.isNaN(x));
  const desc = (xs) => xs.every((v, i) => i === 0 || xs[i - 1] >= v);

  let html = await visit('series_first', '/series/TOUR_MASTERS');
  res.pages.series_first.pending = html.includes('being read');
  await sleep(8000);
  html = await visit('series_after', '/series/TOUR_MASTERS');
  res.pages.series_after.pending = html.includes('being read');
  if (!html.includes('Prestige over time')) bad('series: no prestige history');

  html = await visit('tournaments_by_prestige', '/tournaments?sort=prestige&dir=desc');
  const t1 = nums(await column('Prestige'));
  res.pages.tournaments_by_prestige.first_values = t1.slice(0, 8);
  if (!t1.length) bad('tournaments: no prestige values read');
  if (!desc(t1)) bad('tournaments: prestige not descending');
  if (!html.includes('sorts the whole list')) bad('tournaments: whole-list sorting text missing');
  html = await visit('tournaments_page2', '/tournaments?sort=prestige&dir=desc&page=2');
  const t2 = nums(await column('Prestige'));
  if (t1.length && t2.length && Math.max(...t2) > Math.min(...t1)) bad('tournaments: page 2 above page 1');

  html = await visit('courses_by_prestige', '/courses?sort=prestige&dir=desc');
  const c1 = nums(await column('Prestige'));
  res.pages.courses_by_prestige.first_values = c1.slice(0, 8);
  if (!c1.length) bad('courses: no prestige values read');
  if (!desc(c1)) bad('courses: prestige not descending');

  html = await visit('nations', '/nations');
  const m = html.match(/Prestige: national prestige as last settled \(([^)]*)\)/);
  res.pages.nations.measure = m ? m[1] : null;
  if (!m) bad('nations: measure wording missing');

  html = await visit('nation', `/nation/${nation}`);
  res.pages.nation.achievement_columns = html.includes('>Achievement</th>');
  res.pages.nation.pending = html.includes('being read');
  if (!html.includes('>Achievement</th>') || !html.includes('Visible success first')) bad('nation: achievement columns or wording missing');
  res.pages.nation.row_widths = await pg.evaluate(() => {
    const t = [...document.querySelectorAll('table')].find((x) =>
      [...x.querySelectorAll('thead th')].some((h) => h.textContent.trim() === 'Entrant season'));
    return t ? [...new Set([...t.querySelectorAll('tbody tr')].map((r) => r.querySelectorAll('td').length))] : null;
  });
  if (JSON.stringify(res.pages.nation.row_widths) !== '[9]') bad('nation: prestige rows not 9 wide');

  html = await visit('early_pro_golfer', `/golfer/${earlyGid}`);
  res.pages.early_pro_golfer.status_label = html.includes('before college eligibility ended (amateur top 15)');
  if (!res.pages.early_pro_golfer.status_label) bad('early-pro golfer: the status table does not name the early decision');
  html = await visit('early_pro_season_stayed', `/golfer/${earlyGid}?tab=season&year=2027`);
  res.pages.early_pro_season_stayed.line = (html.match(/Could have turned professional from college at \d+[^<]*/) || [null])[0];
  if (!res.pages.early_pro_season_stayed.line) bad('early-pro golfer: the stayed-in-college line is missing');
  html = await visit('early_pro_season_turned', `/golfer/${earlyGid}?tab=season&year=2028`);
  const tl = (html.match(/Turned professional from college at \d+[^<]*/) || [null])[0];
  res.pages.early_pro_season_turned.line = tl;
  if (!tl) bad('early-pro golfer: the turned-pro line is missing');
  else if ((tl.match(/amateur ranking/g) || []).length !== 1) bad('early-pro golfer: the ranking is not said exactly once');

  html = await visit('rules', '/rules');
  res.pages.rules.has_early_pro_rule = html.includes('Turning professional from college');
  res.pages.rules.versions = [...new Set(html.match(/2026-11-1[2-5]/g) || [])].sort();
  await b.close();
  for (const [k, v] of Object.entries(res.pages)) if (v.width > 1920) bad(`${k}: wider than the screen (${v.width} px)`);
  res.ok = res.problems.length === 0;
  fs.writeFileSync(path.join(out, 'smoke.json'), JSON.stringify(res, null, 1));
  console.log(JSON.stringify(res, null, 1));
  process.exit(res.ok ? 0 : 1);
})().catch((e) => { console.error(e); process.exit(2); });
