// Playwright fallback renderer for render.sh (used when no chromium binary exists).
// Usage: node render_pw.js input.html output.pdf qa_screenshot.png
const fs = require('fs');
const path = require('path');
const os = require('os');
const { chromium } = require('playwright');

// Find a usable Chromium executable in the Playwright browser cache when the
// module's expected revision is not downloaded (version skew).
function findCachedExecutable() {
  const root = path.join(os.homedir(), 'Library', 'Caches', 'ms-playwright');
  if (!fs.existsSync(root)) return undefined;
  const candidates = [];
  for (const dir of fs.readdirSync(root)) {
    if (dir.startsWith('chromium_headless_shell-')) {
      const p = path.join(root, dir, 'chrome-headless-shell-mac-x64', 'chrome-headless-shell');
      if (fs.existsSync(p)) candidates.push({ rev: dir, p });
    }
    if (dir.startsWith('chromium-')) {
      const p = path.join(root, dir, 'chrome-mac-x64',
        'Google Chrome for Testing.app', 'Contents', 'MacOS', 'Google Chrome for Testing');
      if (fs.existsSync(p)) candidates.push({ rev: dir, p });
    }
  }
  if (!candidates.length) return undefined;
  candidates.sort((a, b) => b.rev.localeCompare(a.rev, undefined, { numeric: true }));
  return candidates[0].p;
}

(async () => {
  const [htmlPath, pdfPath, shotPath] = process.argv.slice(2);
  let browser;
  try {
    browser = await chromium.launch();
  } catch (e) {
    const executablePath = findCachedExecutable();
    if (!executablePath) throw e;
    browser = await chromium.launch({ executablePath });
  }
  const page = await browser.newPage();
  await page.goto('file://' + path.resolve(htmlPath), { waitUntil: 'networkidle' });
  await page.emulateMedia({ media: 'screen' });
  await page.screenshot({ path: shotPath, fullPage: true });
  await page.emulateMedia({ media: 'print' });
  await page.pdf({ path: pdfPath, preferCSSPageSize: true, printBackground: true });
  await browser.close();
})();
