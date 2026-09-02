const { chromium } = require('playwright-core');
const fs = require('fs');
const CDP='http://127.0.0.1:18800';
const CRED='/opt/data/secure/flop/agents/quietledger/twitter/credentials.env';
function env(){const o={}; for(const l of fs.readFileSync(CRED,'utf8').split(/\r?\n/)){const m=l.match(/^([A-Z0-9_]+)=(.*)$/i); if(m)o[m[1]]=m[2].replace(/^['"]|['"]$/g,'')} return o}
async function body(p){return await p.locator('body').innerText({timeout:6000}).catch(()=> '')}
(async()=>{
 const c=env();
 const b=await chromium.connectOverCDP(CDP,{timeout:60000});
 const p=b.contexts()[0].pages().find(x=>/x\.com/.test(x.url())) || b.contexts()[0].pages()[0] || await b.contexts()[0].newPage();
 if(!/x\.com/.test(p.url())) await p.goto('https://x.com/i/flow/login',{waitUntil:'domcontentloaded',timeout:60000});
 await p.waitForTimeout(1000);
 await p.getByText('Accept all cookies').click().catch(()=>{});
 await p.waitForTimeout(500);
 const candidates=[c.TWITTER_USERNAME, c.TWITTER_EMAIL_OR_PHONE].filter(Boolean);
 let final='';
 for(const candidate of candidates){
   let input=p.locator('input[name="challenge_response"]').first();
   if(await input.isVisible({timeout:2000}).catch(()=>false)){
     await input.fill(candidate,{timeout:5000});
     await p.getByText(/^Continue$/).click({timeout:5000}).catch(()=>p.keyboard.press('Enter'));
     await p.waitForTimeout(5000);
   }
   let t=await body(p);
   final=t;
   if(!/Incorrect answer|Confirm your account/i.test(t)) break;
   // if still on challenge, clear and try next candidate
 }
 let t=await body(p);
 if(/Password|Use password/i.test(t)){
   await p.getByText(/Use password/i).click().catch(()=>{});
   await p.waitForTimeout(800);
   await p.locator('input[type="password"], input[name="password"]').first().fill(c.TWITTER_PASSWORD || '',{timeout:5000}).catch(()=>{});
   await p.getByText(/^Log in$|^Log in$/i).click({timeout:3000}).catch(()=>p.keyboard.press('Enter'));
   await p.waitForTimeout(8000);
   t=await body(p);
 }
 const ok=/Home\n|For you|What is happening|Post/.test(t) && !/Confirm your account|Incorrect answer/i.test(t);
 console.log(JSON.stringify({ok,state:ok?'logged_in':(/Incorrect answer/i.test(t)?'incorrect_confirmation':'needs_more'),url:p.url(),hint:t.replaceAll(c.TWITTER_USERNAME||'__','[user]').replaceAll(c.TWITTER_EMAIL_OR_PHONE||'__','[email]').slice(0,700)},null,2));
})().catch(e=>{console.log(JSON.stringify({ok:false,error:String(e.message||e)})); process.exit(1);});
