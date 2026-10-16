const assert = require('node:assert/strict');
const { spawn } = require('node:child_process');
const { once } = require('node:events');
const path = require('node:path');
const { chromium } = require('playwright');

(async () => {
  // Bind an ephemeral port; Python prints the selected port before serving.
  const server = spawn('python3', ['-u', '-m', 'http.server', '0', '--bind', '127.0.0.1'], {
    cwd: path.resolve(__dirname, '..'), stdio: ['ignore', 'pipe', 'inherit'],
  });
  let browser;
  try {
    const port = await new Promise((resolve, reject) => {
      let output = '';
      server.stdout.on('data', chunk => {
        output += chunk;
        const match = output.match(/port (\d+)/);
        if (match) resolve(match[1]);
      });
      server.once('error', reject);
      server.once('exit', code => reject(new Error(`Server exited: ${code}`)));
    });
    const origin = `http://127.0.0.1:${port}`;
    browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({ serviceWorkers: 'block' });
    const external = [], errors = [], failures = [];
    await context.route('**/*', route => {
      if (new URL(route.request().url()).origin === origin) return route.continue();
      external.push(route.request().url());
      return route.abort();
    });
    const page = await context.newPage();
    page.on('pageerror', error => errors.push(error.message));
    page.on('requestfailed', request => failures.push(request.url()));
    page.on('response', response => {
      if (response.status() >= 400) failures.push(`${response.status()} ${response.url()}`);
    });
    await page.goto(`${origin}/gnn_money_mule_dashboard.html`);
    await page.locator('.metric').first().waitFor();
    const metrics = () => page.locator('.metric').allTextContents();
    assert.deepEqual(await metrics(), ['89.2%', '62.8%', '11.3%', '21.8%']);
    assert.equal(await page.locator('svg circle').count(), 10);
    assert.equal(await page.locator('svg line').count(), 12);
    assert.equal(await page.locator('.gnn-focus').count(), 4);
    const sliders = page.locator('input[type="range"]');
    async function setSlider(index, value) {
      await sliders.nth(index).fill(String(value));
    }
    await setSlider(0, 0);
    assert.deepEqual(await metrics(), ['69.6%', '57.2%', '17.6%', '23.2%']);
    assert.equal(await page.locator('.ml-focus').count(), 2);
    await setSlider(1, 100);
    assert.deepEqual(await metrics(), ['60.0%', '38.0%', '24.0%', '42.0%']);
    await setSlider(0, 100);
    await setSlider(1, 0);
    assert.deepEqual(await metrics(), ['98.0%', '70.0%', '7.0%', '16.0%']);
    assert.equal(await page.locator('.ml-focus').count(), 1);
    assert.deepEqual(await page.locator('.control strong').allTextContents(), ['100', '0']);
    assert.deepEqual(external, [], 'Dashboard attempted external requests');
    assert.deepEqual(failures, [], 'Failed resource requests');
    assert.deepEqual(errors, [], 'Browser errors');
    console.log('PASS: cold load and both sliders work with all external traffic blocked');
  } finally {
    if (browser) await browser.close();
    server.kill();
    await once(server, 'exit');
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
