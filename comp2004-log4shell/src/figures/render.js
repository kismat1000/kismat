// Render each figure HTML to a 2x PNG (used by the Word report).
// Usage: NODE_PATH=$(npm root -g) node src/figures/render.js
const { chromium } = require('playwright');
const path = require('path');
const figs = ['fig1_attack_chain', 'fig2_cvss_scores', 'fig3_siem_architecture'];
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1000, height: 800 }, deviceScaleFactor: 2 });
  for (const f of figs) {
    await page.goto('file://' + path.join(__dirname, f + '.html'));
    const el = await page.$('.fig');
    await el.screenshot({ path: path.join(__dirname, f + '.png') });
    console.log('rendered', f);
  }
  await browser.close();
})();
