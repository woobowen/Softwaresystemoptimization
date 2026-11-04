#!/usr/bin/env python3
"""在真实 Perfetto UI 中打开 trace，保存时间线和 SQL 查询截图。"""

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile


JAVASCRIPT = r"""
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const {chromium} = require(process.env.A3_PLAYWRIGHT);
const cfg = JSON.parse(process.env.A3_CAPTURE_CONFIG);

async function query(page, sql) {
  return page.evaluate(async sql => {
    const result = await app.trace.engine.query(sql);
    const columns = result.columns();
    const rows = [];
    for (const it = result.iter({}); it.valid(); it.next()) {
      rows.push(Object.fromEntries(columns.map(c => {
        const value = it.get(c);
        return [c, typeof value === 'bigint' ? value.toString() : value];
      })));
    }
    return rows;
  }, sql);
}

(async () => {
  const browser = await chromium.launch({headless: true,
    args: ['--disable-dev-shm-usage']});
  try {
    const context = await browser.newContext({
      viewport: {width: 1800, height: 1200}, deviceScaleFactor: 1});
    const cached = [];
    await context.route('https://ui.perfetto.dev/**', async route => {
      const url = route.request().url();
      const cachedFile = path.join(cfg.cache,
        crypto.createHash('sha256').update(url).digest('hex'));
      if (!fs.existsSync(cachedFile)) return route.continue();
      const pathname = new URL(url).pathname;
      const types = {'.wasm': 'application/wasm', '.js': 'application/javascript',
        '.css': 'text/css', '.woff2': 'font/woff2', '.json': 'application/json',
        '.png': 'image/png'};
      const contentType = types[path.extname(pathname)] ||
        (pathname.endsWith('/') ? 'text/html' : undefined);
      cached.push(url);
      await route.fulfill({body: fs.readFileSync(cachedFile), contentType});
    });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto('https://ui.perfetto.dev/', {waitUntil: 'domcontentloaded'});
    await page.getByText('Open trace file').first().waitFor({timeout: 60000});
    await page.locator('input.trace_file').setInputFiles(cfg.trace);
    await page.waitForFunction(() => window.app?.trace && !app.isLoadingTrace,
      null, {timeout: 120000});
    await page.waitForTimeout(1500);
    const cookieButton = page.getByRole('button', {name: 'OK', exact: true});
    if (await cookieButton.count()) await cookieButton.click();

    const escaped = cfg.focus.replaceAll("'", "''");
    const category = cfg.gpu ? "category = 'kernel'" : "category = 'cpu_op'";
    const match = cfg.focus ? ` AND name LIKE '%${escaped}%'` : '';
    const selected = await query(page,
      `SELECT id,ts,dur,name FROM slice WHERE ${category}${match} ` +
      `ORDER BY ts LIMIT 1 OFFSET ${cfg.index}`);
    if (selected.length !== 1) throw Error('No matching real trace slice');
    const event = selected[0];
    let launch = [];
    if (cfg.gpu) {
      launch = await query(page,
        `SELECT s.id,s.ts,s.dur,s.name FROM flow f JOIN slice s ` +
        `ON s.id=f.slice_out WHERE f.slice_in=${event.id} LIMIT 1`);
    }
    const cpuEvent = launch[0] || event;
    const contextName = cfg.context.replaceAll("'", "''");
    const ancestors = contextName ? await query(page,
      `SELECT id,name,ts,dur FROM ancestor_slice(${cpuEvent.id}) ` +
      `WHERE name LIKE '%: ${contextName}' ORDER BY depth DESC LIMIT 1`) : [];
    const frame = ancestors[0] || cpuEvent;
    let start = BigInt(frame.ts);
    let end = start + BigInt(frame.dur);
    if (BigInt(event.ts) < start) start = BigInt(event.ts);
    if (BigInt(event.ts) + BigInt(event.dur) > end)
      end = BigInt(event.ts) + BigInt(event.dur);
    if (cfg.windowUs) {
      start = BigInt(event.ts) - BigInt(Math.round(cfg.windowUs * 100));
      end = start + BigInt(Math.round(cfg.windowUs * 1000));
    }
    const bounds = {start: start.toString(), end: end.toString()};
    await page.evaluate(async ({event, cpuEvent, bounds, gpu}) => {
      const t = app.trace;
      if (gpu) {
        for (const group of t.currentWorkspace.children) group.expandAll();
      }
      await t.selection.selectSqlEvent('slice', Number(event.id),
        {scrollToSelection: !gpu});
      t.timeline.panSpanIntoView(BigInt(bounds.start), BigInt(bounds.end),
        {align: 'zoom', animation: 'step', margin: 0.08});
      raf.scheduleFullRedraw();
    }, {event, cpuEvent, bounds, gpu: cfg.gpu});
    await page.waitForTimeout(1500);
    if (errors.length) throw Error(errors.join('\n'));
    await page.screenshot({path: cfg.timeline});
    const log = {recorded_utc: new Date().toISOString(),
      capture_options: {focus: cfg.focus, context: cfg.context, gpu: cfg.gpu,
        index: cfg.index, window_us: cfg.windowUs},
      trace: cfg.trace, trace_sha256:
      crypto.createHash('sha256').update(fs.readFileSync(cfg.trace)).digest('hex'),
      ui_url: page.url(), browser: browser.version(),
      playwright_version: require(path.join(process.env.A3_PLAYWRIGHT, 'package.json')).version,
      viewport: {width: 1800, height: 1200}, selected, launch, ancestors, bounds,
      cached_official_urls: [...new Set(cached)], errors,
      timeline_body: await page.locator('body').innerText(),
      import_statistics: await query(page,
        "SELECT name,severity,value FROM stats WHERE value>0 AND severity IN ('error','data_loss')"),
      sql: []};
    for (const item of cfg.sql) {
      const sql = fs.readFileSync(item.file, 'utf8');
      await page.getByText('Query (SQL)').first().click();
      await page.locator('.cm-content').fill(sql);
      await page.getByRole('button', {name: 'Run Query'}).click();
      await page.getByText(/Returned \d+ rows in/).first().waitFor();
      await page.waitForFunction(() => app.trace.engine.numRequestsPending === 0);
      await page.waitForTimeout(500);
      await page.screenshot({path: item.image});
      log.sql.push({file: item.file, image: item.image, text: sql,
        body: await page.locator('body').innerText()});
    }
    log.images = [cfg.timeline, ...cfg.sql.map(item => item.image)].map(file => ({
      file, sha256: crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex')
    }));
    fs.writeFileSync(cfg.log, JSON.stringify(log, null, 2) + '\n');
    console.log(JSON.stringify({timeline: cfg.timeline, sql: cfg.sql,
      log: cfg.log, selected: event.name, import_statistics: log.import_statistics}));
  } finally {
    await browser.close();
  }
})().catch(error => {console.error(error); process.exitCode = 1;});
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("timeline", type=Path)
    parser.add_argument("--focus", default="aten::exp", help="slice 名称的一部分")
    parser.add_argument("--context", default="naive_softmax", help="外层函数名")
    parser.add_argument("--gpu", action="store_true", help="选择 kernel 并显示对应 CPU launch")
    parser.add_argument("--index", type=int, default=0)
    parser.add_argument("--window-us", type=float, default=0)
    parser.add_argument("--sql", type=Path, action="append", default=[])
    parser.add_argument("--sql-image", type=Path, action="append", default=[])
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--playwright", type=Path)
    root = Path(__file__).resolve().parents[2]
    parser.add_argument("--cache", type=Path, default=root / ".cache/a3-perfetto/http")
    args = parser.parse_args()
    if len(args.sql) != len(args.sql_image):
        parser.error("each --sql needs a matching --sql-image")
    package = args.playwright
    if package is None:
        packages = sorted(Path.home().glob(".npm/_npx/*/node_modules/playwright/package.json"))
        if not packages:
            parser.error("Playwright 未安装；请指定 --playwright，脚本不会自动安装依赖")
        package = packages[0].parent
    for output in [args.timeline, args.log, *args.sql_image]:
        output.parent.mkdir(parents=True, exist_ok=True)
    config = {
        "trace": str(args.trace.resolve()), "timeline": str(args.timeline.resolve()),
        "focus": args.focus, "context": args.context, "gpu": args.gpu,
        "index": args.index, "windowUs": args.window_us,
        "log": str(args.log.resolve()), "cache": str(args.cache.resolve()),
        "sql": [{"file": str(f.resolve()), "image": str(i.resolve())}
                for f, i in zip(args.sql, args.sql_image)],
    }
    environment = dict(os.environ, A3_PLAYWRIGHT=str(package.resolve()),
                       A3_CAPTURE_CONFIG=json.dumps(config))
    with tempfile.TemporaryDirectory(prefix="a3-perfetto-capture-") as temporary:
        script = Path(temporary) / "capture.cjs"
        script.write_text(JAVASCRIPT)
        return subprocess.run(["node", str(script)], env=environment).returncode


if __name__ == "__main__":
    raise SystemExit(main())
