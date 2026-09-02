const { chromium } = require('playwright-core');
const fs = require('fs');
const CDP = process.env.CDP || 'http://127.0.0.1:18800';
const CRED = '/opt/data/secure/flop/agents/quietledger/twitter/credentials.env';
function readEnv(file){const out={}; for(const line of fs.readFileSync(file,'utf8').split(/\r?\n/)){const m=line.match(/^([A-Z0-9_]+)=(.*)$/i); if(m) out[m[1]]=m[2].replace(/^['"]|['"]$/g,'')} return out}
async function text(page){return await page.locator('body').innerText({timeout:6000}).catch(()=> '')}
async function fillLastVisibleTextInput(page, value){
  return await page.evaluate((value)=>{
    const inputs=Array.from(document.querySelectorAll('input')).filter(el=>{const r=el.getBoundingClientRect(); return r.width>0&&r.height>0&&el.type!=='password'});
    const el=inputs[inputs.length-1]; if(!el) return false;
    el.focus(); el.value=''; el.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'deleteContentBackward'}));
    el.value=value; el.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'insertText',data:value})); el.dispatchEvent(new Event('change',{bubbles:true}));
    return true;
  }, value);
}
(async()=>{
 const c=readEnv(CRED);
 const b=await chromium.connectOverCDP(CDP,{timeout:60000});
 const ctx=b.contexts()[0]; const p=ctx.pages().find(x=>/x\.com/.test(x.url()))||ctx.pages()[0]||await ctx.newPage();
 await p.goto('https://x.com/i/flow/login',{waitUntil:'domcontentloaded',timeout:60000});
 await p.waitForTimeout(3000);
 if((await text(p)).includes('Accept all cookies')) await p.getByText('Accept all cookies').click().catch(()=>{});
 await p.waitForTimeout(1000);
 let t=await text(p);
 if(/Confirm your account|Username/i.test(t)){
   await fillLastVisibleTextInput(p, c.TWITTER_EMAIL_OR_PHONE || c.TWITTER_USERNAME || '');
   await p.keyboard.press('Enter');
   await p.waitForTimeout(5000);
 }
 t=await text(p);
 if(/Password|Use password/i.test(t)){
   await p.getByText(/Use password/i).click().catch(()=>{});
   await p.waitForTimeout(1000);
   await p.locator('input[type="password"]').first().fill(c.TWITTER_PASSWORD || '',{timeout:5000}).catch(async()=>{});
   await p.keyboard.press('Enter');
   await p.waitForTimeout(8000);
 }
 t=await text(p);
 const ok=/Home\n|For you|What is happening|Post/.test(t) && !/Confirm your account|Incorrect answer/i.test(t);
 console.log(JSON.stringify({ok, url:p.url(), state: ok?'logged_in':(/Incorrect answer/i.test(t)?'incorrect_confirmation':'not_logged_in_or_needs_more'), hint:t.replaceAll(c.TWITTER_EMAIL_OR_PHONE||'__','[email]').replaceAll(c.TWITTER_USERNAME||'__','[user]').slice(0,800)},null,2));
})().catch(e=>{console.log(JSON.stringify({ok:false,error:String(e.message||e)})); process.exit(1);});
