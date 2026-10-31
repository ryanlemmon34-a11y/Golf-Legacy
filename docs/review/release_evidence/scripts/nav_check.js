// Wide-screen observer navigation check: crawl same-origin links from the overview (GET only, no forms), at two
// desktop widths; every page must answer 200, show no Python traceback, and not scroll sideways (wide tables sit in
// their own scrolling boxes). Key views are then visited explicitly: Upsets, My World, rules, courses, nations, up to
// four editions' Story view and six golfers' coaching tab (found while crawling); a missing kind fails the check.
// Writes results.json and one screenshot per page at 1920 px.
//   BASE=http://localhost:8791 OUT=<dir> node nav_check.js
const { chromium } = require('playwright');
const fs = require('fs');
const BASE = process.env.BASE, OUT = process.env.OUT, LIMIT = +(process.env.LIMIT || 70);
const SKIP = /\/(worlds|api|jobs|static|download|export|read|shortlist)/;
(async () => {
  const b = await chromium.launch();
  const results = [];
  for (const width of [1920, 1366]) {
    const p = await b.newPage({ viewport: { width, height: 1000 } });
    const seen = new Set(), queue = ['/'], stories = [], coaching = [];
    const visit = async (path) => {
      seen.add(path);
      let status = 0, err = null;
      try {
        const r = await p.goto(BASE + path, { waitUntil: 'domcontentloaded', timeout: 120000 });
        status = r ? r.status() : 0;
      } catch (e) { err = String(e).slice(0, 200); }
      const info = err ? {} : await p.evaluate(() => ({
        text: document.body ? document.body.innerText.length : 0,
        traceback: /Traceback \(most recent call last\)|Internal Server Error/.test(document.body ? document.body.innerText : ''),
        overflow: document.documentElement.scrollWidth - window.innerWidth,
        title: document.title,
        links: Array.from(document.querySelectorAll('a[href^="/"]')).map(a => a.getAttribute('href')),
      }));
      const ok = !err && status === 200 && !info.traceback && info.text > 50 && info.overflow <= 1;
      results.push({ width, path, status, err, ok, overflow: info.overflow, traceback: info.traceback, title: info.title });
      if (width === 1920) await p.screenshot({ path: `${OUT}/w${width}_${String(results.length).padStart(3, '0')}.png` });
      for (const h of (info.links || [])) {
        if (SKIP.test(h) || h.includes('#')) continue;
        if (!seen.has(h) && !queue.includes(h)) queue.push(h);
        if (/^\/event\/[^?]+$/.test(h) && stories.length < 4 && !stories.includes(h + '?view=story')) stories.push(h + '?view=story');
        if (/^\/golfer\/\d+$/.test(h) && coaching.length < 6 && !coaching.includes(h + '?tab=coaching')) coaching.push(h + '?tab=coaching');
      }
    };
    while (queue.length && seen.size < LIMIT) {
      const path = queue.shift();
      if (!seen.has(path)) await visit(path);
    }
    for (const path of ['/upsets', '/my-world', '/rules', '/courses', '/nations', ...stories, ...coaching])
      if (!seen.has(path)) await visit(path);
    for (const [kind, list] of [['view=story', stories], ['tab=coaching', coaching]])
      if (!list.length) results.push({ width, path: `(none found: ${kind})`, status: 0, ok: false });
    await p.close();
  }
  await b.close();
  fs.writeFileSync(`${OUT}/results.json`, JSON.stringify(results, null, 1));
  const bad = results.filter(r => !r.ok);
  console.log(`pages ${results.length}, failing ${bad.length}`);
  for (const r of bad) console.log('FAIL', JSON.stringify(r));
})();
