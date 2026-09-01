const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright-core');

const CDP = process.env.RELAY_CDP || 'http://127.0.0.1:18800';
const CREDS = '/opt/data/secure/flop/agents/quietledger/twitter/credentials.env';
const OUT = '/opt/data/work/flop/agents/quietledger/receipts/tmp/twitter-relay';
fs.mkdirSync(OUT, { recursive: true });

function loadEnv(file) {
  const out = {};
  for (const line of fs.readFileSync(file, 'utf8').split(/\r?\n/)) {
    const i = line.indexOf('=');
    if (i < 0 || line.trim().startsWith('#')) continue;
    const k = line.slice(0, i).trim();
    let v = line.slice(i + 1).trim();
    if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) v = v.slice(1, -1);
    out[k] = v;
  }
  return out;
}
async function text(page) { return await page.locator('body').innerText({ timeout: 6000 }).catch(() => ''); }
function clean(s, c) { return String(s || '').replaceAll(c.email, '[email]').replace(new RegExp(c.user, 'ig'), '[handle]').slice(0, 1200); }
async function shot(page, name) { const f = path.join(OUT, `${Date.now()}-${name}.png`); await page.screenshot({ path: f, fullPage: true }).catch(()=>{}); return f; }
async function fillVisible(page, pred, value) {
  const ok = await page.evaluate(({ pred, value }) => {
    const inputs = Array.from(document.querySelectorAll('input'));
    for (const el of inputs) {
      const r = el.getBoundingClientRect();
      if (!(r.width > 0 && r.height > 0)) continue;
      const p = { type: el.type || '', name: el.name || '', autocomplete: el.autocomplete || '', placeholder: el.placeholder || '', aria: el.getAttribute('aria-label') || '' };
      let want = false;
      if (pred === 'password') want = p.type === 'password' || p.name === 'password';
      if (pred === 'text') want = p.type !== 'password';
      if (!want) continue;
      el.focus();
      el.value = value;
      el.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: value }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
      return true;
    }
    return false;
  }, { pred, value });
  return ok;
}
async function clickText(page, re) {
  const loc = page.getByText(re).first();
  if (await loc.isVisible({ timeout: 2500 }).catch(() => false)) { await loc.click().catch(()=>{}); return true; }
  return false;
}

async function main() {
  const c = loadEnv(CREDS);
  c.user = (c.TWITTER_USERNAME || '').replace(/^@/, '');
  c.email = c.TWITTER_EMAIL_OR_PHONE || c.user;
  c.pass = c.TWITTER_PASSWORD || '';
  const browser = await chromium.connectOverCDP(CDP, { timeout: 60000 });
  const context = browser.contexts()[0] || await browser.newContext();
  let page = context.pages().find(p => /x\.com|twitter\.com/.test(p.url())) || context.pages()[0] || await context.newPage();
  await page.goto('https://x.com/i/flow/login', { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(4000);

  let state = 'unknown';
  for (let i = 0; i < 10; i++) {
    const t = await text(page);
    const url = page.url();
    if (url.includes('/home') || /For you\n|Home\n|What is happening/i.test(t)) { state = 'logged_in'; break; }
    if (/temporarily limited your login/i.test(t)) { state = 'temporarily_limited'; break; }
    if (/Enter your code|confirmation code|verification code|Check your email|Authenticate your account/i.test(t)) { state = 'needs_code'; break; }
    if (/wrong|incorrect|does not match/i.test(t)) { state = 'bad_credentials'; break; }

    if (/See what's happening|Email or username|Phone, email, or username/i.test(t)) {
      await clickText(page, /Email or username/i);
      await page.waitForTimeout(800);
      if (await fillVisible(page, 'text', c.email)) { await page.keyboard.press('Enter'); await page.waitForTimeout(4500); continue; }
    }
    if (/Confirm your account|Username/i.test(t) && !/Password/i.test(t)) {
      if (await fillVisible(page, 'text', c.user)) { await page.keyboard.press('Enter'); await page.waitForTimeout(4500); continue; }
    }
    if (/Password|Use password/i.test(t) || await page.locator('input[type="password"]').first().isVisible().catch(()=>false)) {
      await clickText(page, /Use password/i);
      await page.waitForTimeout(800);
      if (await fillVisible(page, 'password', c.pass)) { await page.keyboard.press('Enter'); await page.waitForTimeout(7000); continue; }
    }
    await page.keyboard.press('Enter').catch(()=>{});
    await page.waitForTimeout(3000);
  }
  const finalText = await text(page);
  const screenshot = await shot(page, state);
  console.log(JSON.stringify({ ok: state === 'logged_in', state, url: page.url(), screenshot, text_hint: clean(finalText, c) }, null, 2));
  // Keep shared relay browser alive for subsequent actions.
}
main().catch(e => { console.error(JSON.stringify({ ok:false, error:e.message }, null, 2)); process.exit(1); });
