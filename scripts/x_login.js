const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const SECURE_DIR = '/opt/data/secure/flop-one-agent/account01/twitter';
const CREDS = path.join(SECURE_DIR, 'credentials.env');
const PROFILE = path.join(SECURE_DIR, 'browser-profile');
const ARTIFACTS = path.join('/opt/data/work/flop-one-agent/receipts/tmp/twitter');
fs.mkdirSync(PROFILE, { recursive: true, mode: 0o700 });
fs.mkdirSync(ARTIFACTS, { recursive: true });

function loadEnvFile(file) {
  const out = {};
  for (const line of fs.readFileSync(file, 'utf8').split(/\r?\n/)) {
    if (!line || line.trim().startsWith('#')) continue;
    const i = line.indexOf('=');
    if (i < 0) continue;
    const k = line.slice(0, i).trim();
    let v = line.slice(i + 1).trim();
    if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) v = v.slice(1, -1);
    out[k] = v;
  }
  return out;
}
async function clickAny(page, selectors, timeout = 2500) {
  for (const selector of selectors) {
    try { const loc = page.locator(selector).first(); await loc.waitFor({ state: 'visible', timeout }); await loc.click(); return selector; } catch {}
  }
  return null;
}
async function fillAny(page, selectors, value, timeout = 8000) {
  for (const selector of selectors) {
    try { const loc = page.locator(selector).first(); await loc.waitFor({ state: 'visible', timeout }); await loc.fill(value); return selector; } catch {}
  }
  return null;
}
async function bodyText(page) { return await page.locator('body').innerText({ timeout: 5000 }).catch(() => ''); }
async function snapshot(page, name) {
  const file = path.join(ARTIFACTS, `${Date.now()}-${name}.png`);
  await page.screenshot({ path: file, fullPage: true }).catch(() => {});
  return file;
}
function sanitize(text, email, username) {
  return text.replaceAll(email, '[email]').replace(new RegExp(username, 'gi'), '[handle]').slice(0, 900);
}
async function main() {
  const cmd = process.argv[2] || 'status';
  const creds = loadEnvFile(CREDS);
  const username = (creds.TWITTER_USERNAME || '').replace(/^@/, '');
  const email = creds.TWITTER_EMAIL_OR_PHONE || username;
  const password = creds.TWITTER_PASSWORD || '';
  const context = await chromium.launchPersistentContext(PROFILE, { headless: true, viewport: { width: 1280, height: 900 }, locale: 'en-US' });
  const page = context.pages()[0] || await context.newPage();

  if (cmd === 'status') {
    await page.goto(`https://x.com/${username}`, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(4000);
    console.log(JSON.stringify({ ok: true, command: 'status', profile: PROFILE, url: page.url(), page_text_hint: sanitize(await bodyText(page), email, username) }, null, 2));
    await context.close(); return;
  }

  await page.goto('https://x.com/i/flow/login', { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(2500);
  await clickAny(page, ['text=Email or username', 'text=Sign in', 'a[href="/login"]'], 4000);
  await page.waitForTimeout(1000);

  for (let step = 0; step < 8; step++) {
    const text = await bodyText(page);
    const url = page.url();
    if (url.includes('/home') || /What is happening|Home\n|For you\n/i.test(text)) {
      console.log(JSON.stringify({ ok: true, state: 'logged_in', url }, null, 2));
      await context.close(); return;
    }
    if (/password/i.test(text) || await page.locator('input[type="password"], input[name="password"]').first().isVisible().catch(() => false)) {
      if (await fillAny(page, ['input[name="password"]', 'input[type="password"]'], password, 8000)) {
        await page.keyboard.press('Enter'); await page.waitForTimeout(7000); continue;
      }
    }
    if (/Confirm your account|Username/i.test(text)) {
      if (await fillAny(page, ['input[name="text"]', 'input[type="text"]'], username, 8000)) {
        await page.keyboard.press('Enter'); await page.waitForTimeout(5000); continue;
      }
    }
    if (/Email or username|Phone, email, or username|See what's happening/i.test(text)) {
      await clickAny(page, ['text=Email or username'], 2000);
      if (await fillAny(page, ['input[autocomplete="username"]', 'input[name="text"]', 'input[type="text"]'], email, 8000)) {
        await page.keyboard.press('Enter'); await page.waitForTimeout(5000); continue;
      }
    }
    await clickAny(page, ['text=Continue', 'text=Next', 'div[role="button"]:has-text("Continue")', 'div[role="button"]:has-text("Next")'], 2000);
    await page.waitForTimeout(3000);
  }
  const text = await bodyText(page);
  let state = 'needs_verification';
  if (/wrong|incorrect/i.test(text)) state = 'login_failed';
  const screenshot = await snapshot(page, state);
  console.log(JSON.stringify({ ok: false, state, url: page.url(), screenshot, page_text_hint: sanitize(text, email, username) }, null, 2));
  await context.close();
}
main().catch(err => { console.error(JSON.stringify({ ok: false, error: err.message }, null, 2)); process.exit(1); });
