const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');

const CDP = process.env.CDP || 'http://127.0.0.1:18800';
const ROOT = '/opt/data/work/flop/agents/quietledger';
const CRED = '/opt/data/secure/flop/agents/quietledger/twitter/credentials.env';
const OUTDIR = path.join(ROOT, 'receipts/tmp/twitter-full-activity');
fs.mkdirSync(OUTDIR, { recursive: true });

function readEnv(file) {
  const out = {};
  if (!fs.existsSync(file)) return out;
  for (const line of fs.readFileSync(file, 'utf8').split(/\r?\n/)) {
    const m = line.match(/^([A-Z0-9_]+)=(.*)$/i);
    if (m) out[m[1]] = m[2].replace(/^['"]|['"]$/g, '');
  }
  return out;
}
function sleep(ms){ return new Promise(r => setTimeout(r, ms)); }
async function shot(page, name){
  try { await page.screenshot({ path: path.join(OUTDIR, `${Date.now()}-${name}.png`), fullPage: false }); } catch(e) {}
}
async function clickIfVisible(page, selector, timeout=2500) {
  try { const loc = page.locator(selector).first(); await loc.waitFor({ state: 'visible', timeout }); await loc.click({ timeout }); return true; } catch(e) { return false; }
}
async function textPresent(page, re) {
  try { return re.test(await page.locator('body').innerText({ timeout: 5000 })); } catch(e) { return false; }
}
async function getCurrentUserFromUI(page) {
  await page.goto('https://x.com/home', { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(5000);
  const txt = await page.locator('body').innerText({timeout: 10000}).catch(()=> '');
  if (/Log in|Sign in/i.test(txt) && !/Home|Post|What is happening/i.test(txt)) throw new Error('not_logged_in');
  // Try side nav profile link
  const hrefs = await page.locator('a[href^="/"]').evaluateAll(els => els.map(a => a.getAttribute('href')).filter(Boolean)).catch(()=>[]);
  const bad = new Set(['/home','/explore','/notifications','/messages','/i/bookmarks','/jobs','/compose/post','/settings','/login','/signup']);
  for (const h of hrefs) {
    if (/^\/[A-Za-z0-9_]{1,15}$/.test(h) && !bad.has(h)) return h.slice(1);
  }
  return null;
}
async function postTweet(page, text) {
  await page.goto('https://x.com/compose/post', { waitUntil:'domcontentloaded', timeout:60000 });
  await page.waitForTimeout(4000);
  let box = page.locator('div[role="textbox"][data-testid="tweetTextarea_0"]').first();
  await box.waitFor({state:'visible', timeout:20000});
  await box.click();
  await page.keyboard.insertText(text);
  await page.waitForTimeout(1000);
  let clicked = await clickIfVisible(page, '[data-testid="tweetButton"]', 8000);
  if (!clicked) clicked = await clickIfVisible(page, '[data-testid="tweetButtonInline"]', 8000);
  if (!clicked) throw new Error('post_button_not_found');
  await page.waitForTimeout(6000);
  await shot(page, 'after-new-post');
}
async function deleteOldPost(page, username) {
  const markers = ['quietledger/QuietLedger is online for FLOP / Technocore work', 'Public receipts and GitHub proof: https://github.com/FillipMorris/flop-quietledger'];
  await page.goto(`https://x.com/${username}`, { waitUntil:'domcontentloaded', timeout:60000 });
  await page.waitForTimeout(7000);
  let deleted = false, oldUrl = null;
  for (let pass=0; pass<5 && !deleted; pass++) {
    const articles = await page.locator('article').count().catch(()=>0);
    for (let i=0; i<Math.min(articles, 8); i++) {
      const art = page.locator('article').nth(i);
      const txt = await art.innerText({timeout:2000}).catch(()=> '');
      if (markers.some(m => txt.includes(m))) {
        const links = await art.locator('a[href*="/status/"]').evaluateAll(els => els.map(a => a.href)).catch(()=>[]);
        oldUrl = links.find(Boolean) || null;
        let menu = art.locator('[data-testid="caret"]').first();
        if (!(await menu.isVisible({timeout:1000}).catch(()=>false))) menu = art.locator('button[aria-label="More"]').first();
        await menu.click({timeout:7000});
        await page.waitForTimeout(1000);
        let del = page.locator('[role="menuitem"]').filter({hasText:/Delete/i}).first();
        await del.click({timeout:5000});
        await page.waitForTimeout(1000);
        await clickIfVisible(page, '[data-testid="confirmationSheetConfirm"]', 8000);
        await page.waitForTimeout(5000);
        deleted = true;
        await shot(page, 'after-delete-old');
        break;
      }
    }
    if (!deleted) { await page.mouse.wheel(0, 900); await page.waitForTimeout(2000); }
  }
  return {deleted, oldUrl};
}
async function followAndLike(page) {
  const actions = { followed_flop_labs: false, liked: [] };
  await page.goto('https://x.com/flop_labs', { waitUntil:'domcontentloaded', timeout:60000 });
  await page.waitForTimeout(6000);
  const body = await page.locator('body').innerText({timeout:10000}).catch(()=> '');
  if (!/Following/i.test(body)) {
    actions.followed_flop_labs = await clickIfVisible(page, '[data-testid$="-follow"]', 6000);
    await page.waitForTimeout(3000);
  }
  // Like pinned and two relevant recent posts by URL for stable targeting.
  const targets = [
    'https://x.com/flop_labs/status/2092626441339043871',
    'https://x.com/flop_labs/status/2094628978762080357',
    'https://x.com/flop_labs/status/2094257776113713592'
  ];
  for (const url of targets) {
    await page.goto(url, { waitUntil:'domcontentloaded', timeout:60000 });
    await page.waitForTimeout(5000 + Math.floor(Math.random()*2500));
    const txt = await page.locator('body').innerText({timeout:10000}).catch(()=> '');
    if (/Log in|Sign in/i.test(txt) && !/Reply|Post|Flop Labs/i.test(txt)) continue;
    let already = await page.locator('[data-testid="unlike"]').first().isVisible({timeout:2000}).catch(()=>false);
    if (already) { actions.liked.push({url, status:'already_liked'}); continue; }
    let ok = await clickIfVisible(page, '[data-testid="like"]', 6000);
    actions.liked.push({url, status: ok ? 'liked' : 'like_not_found'});
    await page.waitForTimeout(2500 + Math.floor(Math.random()*2500));
  }
  await shot(page, 'after-follow-likes');
  return actions;
}
async function latestOwnPostUrl(page, username, contains) {
  await page.goto(`https://x.com/${username}`, { waitUntil:'domcontentloaded', timeout:60000 });
  await page.waitForTimeout(7000);
  for (let pass=0; pass<4; pass++) {
    const articles = await page.locator('article').count().catch(()=>0);
    for (let i=0; i<Math.min(articles, 8); i++) {
      const art = page.locator('article').nth(i);
      const txt = await art.innerText({timeout:2000}).catch(()=> '');
      if (contains.every(s => txt.includes(s))) {
        const links = await art.locator('a[href*="/status/"]').evaluateAll(els => els.map(a => a.href)).catch(()=>[]);
        const u = links.find(h => h.includes(`/${username}/status/`)) || links.find(Boolean) || null;
        await shot(page, 'new-post-found');
        return u;
      }
    }
    await page.mouse.wheel(0, 800); await page.waitForTimeout(1500);
  }
  return null;
}
(async()=>{
  const env = readEnv(CRED);
  let username = (env.TWITTER_USERNAME || env.X_USERNAME || env.USERNAME || '').replace(/^@/, '').trim();
  const browser = await chromium.connectOverCDP(CDP);
  const context = browser.contexts()[0];
  const page = context.pages()[0] || await context.newPage();
  if (!username) username = await getCurrentUserFromUI(page);
  if (!username) throw new Error('username_not_found');
  await getCurrentUserFromUI(page);
  const del = await deleteOldPost(page, username);
  const social = await followAndLike(page);
  const newText = `QuietLedger published a public FLOP / Technocore agent proof chain.\n\nIt keeps a persistent Ed25519 DID, GitHub receipts, and signed evidence so the work can be checked later.\n\nDID: did:key:z6Mkus1U78m9Sk6b4o4dQVd3eCZQEKdVyFxn1E62GQiWg6iB\nRepo: https://github.com/FillipMorris/flop-quietledger\n\n@flop_labs Technocore $FLOP`;
  await postTweet(page, newText);
  const newUrl = await latestOwnPostUrl(page, username, ['QuietLedger published', 'flop-quietledger']);
  const result = { ok:true, deleted_old_post: del.deleted, old_post_url: del.oldUrl, followed_flop_labs: social.followed_flop_labs, liked: social.liked, new_post_url: newUrl, new_post_text: newText, artifacts_dir: OUTDIR };
  fs.writeFileSync(path.join(OUTDIR, 'x-full-activity-result.json'), JSON.stringify(result, null, 2));
  console.log(JSON.stringify({ok:true, deleted_old_post: del.deleted, followed_flop_labs: social.followed_flop_labs, liked_count: social.liked.filter(x=>x.status==='liked'||x.status==='already_liked').length, new_post_url: newUrl, artifacts_dir: OUTDIR}, null, 2));
  // Keep shared relay browser alive for receipt capture.
})().catch(async e => {
  const out = {ok:false, error: String(e && e.message || e), artifacts_dir: OUTDIR};
  fs.writeFileSync(path.join(OUTDIR, 'x-full-activity-error.json'), JSON.stringify(out, null, 2));
  console.log(JSON.stringify(out, null, 2));
  process.exit(1);
});
