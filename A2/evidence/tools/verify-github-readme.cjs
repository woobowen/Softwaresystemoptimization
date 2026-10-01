const { chromium } = require('/home/addaswsw/.npm/_npx/48b1ca104c3549f4/node_modules/playwright');
const fs = require('fs');
(async () => {
  const sha = process.argv[2], out = process.argv[3];
  const browser = await chromium.launch({headless: true, executablePath: '/home/addaswsw/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome', args: ['--no-sandbox', '--disable-dev-shm-usage']});
  try {
    const page = await browser.newPage({viewport: {width: 1440, height: 1000}, deviceScaleFactor: 1});
    const url = 'https://github.com/woobowen/Softwaresystemoptimization/blob/' + sha + '/A2/README.md';
    const response = await page.goto(url, {waitUntil: 'domcontentloaded', timeout: 45000});
    if (!response || response.status() !== 200) throw new Error('HTTP ' + response?.status());
    const article = page.locator('article.markdown-body');
    await article.waitFor({timeout: 30000});
    const images = article.locator('img');
    for (let i = 0; i < await images.count(); i++) await images.nth(i).scrollIntoViewIfNeeded();
    await page.waitForFunction(() => [...document.querySelectorAll('article.markdown-body img')].every(i => i.complete && i.naturalWidth > 0), null, {timeout: 30000});
    const content = await article.innerText();
    const headings = await article.locator('h2').allTextContents();
    const imageData = await images.evaluateAll(list => list.map(i => ({src: i.src, alt: i.alt, complete: i.complete, width: i.naturalWidth, height: i.naturalHeight})));
    if (imageData.length !== 6) throw new Error('Expected six images');
    for (let i = 1; i <= 7; i++) if (!headings.some(h => h.trim().startsWith(i + '.'))) throw new Error('Missing Q' + i);
    for (const value of ['604.34', '792.54', '1148.35', '397.00', '853.15', '680.83', '721.80', '6.02%']) if (!content.includes(value)) throw new Error('Missing displayed value ' + value);
    if (/TODO|Codex|ChatGPT|BLOCKED|UNVERIFIED/.test(content)) throw new Error('Unexpected workflow text');
    fs.mkdirSync(out, {recursive: true});
    await images.last().scrollIntoViewIfNeeded();
    await page.screenshot({path: out + '/readme-parameter.png'});
    await article.locator('p').last().scrollIntoViewIfNeeded();
    await page.screenshot({path: out + '/readme-conclusion.png'});
    const record = {sha, url, status: response.status(), at: new Date().toISOString(), browser: await browser.version(), playwright: require('/home/addaswsw/.npm/_npx/48b1ca104c3549f4/node_modules/playwright/package.json').version, headings, tables: await article.locator('table').count(), images: imageData, displayed_values_checked: true, passed: true};
    fs.writeFileSync(out + '/browser-review.json', JSON.stringify(record, null, 2) + '\n');
    console.log(JSON.stringify(record, null, 2));
  } finally { await browser.close(); }
})().catch(error => { console.error(error.stack); process.exitCode = 1; });
