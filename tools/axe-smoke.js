/**
 * Axe smoke test: launches a local page and reports accessibility issues.
 * Usage:
 *   pnpm add -D puppeteer axe-core
 *   node tools/axe-smoke.js http://localhost:5173
 */
const puppeteer = require('puppeteer');
const fs = require('fs');
const url = process.argv[2] || 'http://localhost:5173';

async function run() {
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();
  await page.goto(url, { waitUntil: 'networkidle0' });

  // Inject axe-core from CDN
  await page.addScriptTag({ url: 'https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.0/axe.min.js' });
  const results = await page.evaluate(async () => {
    return await window.axe.run(document, {
      runOnly: ['wcag2a', 'wcag2aa'],
      rules: {
        'color-contrast': { enabled: true },
      },
    });
  });

  const output = {
    violations: results.violations.map(v => ({ id: v.id, impact: v.impact, description: v.description, nodes: v.nodes.length })),
  };
  console.log(JSON.stringify(output, null, 2));
  fs.writeFileSync('axe-report.json', JSON.stringify(results, null, 2));
  await browser.close();
}

run().catch(err => {
  console.error(err);
  process.exit(1);
});
