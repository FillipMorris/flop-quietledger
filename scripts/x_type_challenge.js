const { chromium } = require('playwright-core');
const fs = require('fs');
const CDP='http://127.0.0.1:18800';
const CRED='/opt/data/secure/flop/agents/quietledger/twitter/credentials.env';
function env(){const o={}; for(const l of fs.readFileSync(CRED,'utf8').split(/\r?\n/)){const m=l.match(/^([A-Z0-9_]+)=(.*)$/i); if(m)o[m[1]]=m[2].replace(/^['"]|['"]$/g,'')} return o}
async function btxt(p){return await p.locator('body').innerText({timeout:6000}).catch(()=> '')}
(async()=>{
 const c=env();
 const browser=await chromium.connectOverCDP(CDP,{timeout:60000});
 const p=browser.contexts()[0].pages().find(x=>/x\.com/.test(x.url())) || browser.contexts()[0].pages()[0];
 await p.getByText('Accept all cookies').click({force:true, timeout:3000}).catch(()=>{});
 await p.getByText('Refuse non-essential cookies').click({force:true, timeout:1000}).catch(()=>{});
 await p.waitForTimeout(500);
 const candidate=c.TWITTER_USERNAME || c.TWITTER_EMAIL_OR_PHONE || '';
 const inp=p.locator('input[name="challenge_response"]').first();
 await inp.click({timeout:5000});
 await p.keyboard.press(process.platform==='darwin'?'Meta+A':'Control+A');
 await p.keyboard.press('Backspace');
 await p.keyboard.type(candidate, {delay:80});
 await p.waitForTimeout(500);
 const valLen=await inp.evaluate(e=>e.value.length).catch(()=>-1);
 await p.keyboard.press('Enter').catch(()=>{});
 await p.waitForTimeout(1000);
 await p.locator('button').filter({hasText:/^Continue$/}).last().click({timeout:5000, force:true}).catch(()=>{});
 await p.waitForTimeout(7000);
 let t=await btxt(p);
 let state=/Incorrect answer/i.test(t)?'incorrect':(/Password|Use password/i.test(t)?'password':(/Home|For you|What is happening/i.test(t)?'logged_in':'other'));
 console.log(JSON.stringify({ok:state==='logged_in'||state==='password',state,valLen,url:p.url(),hint:t.replaceAll(c.TWITTER_USERNAME||'__','[user]').replaceAll(c.TWITTER_EMAIL_OR_PHONE||'__','[email]').slice(0,700)},null,2));
})().catch(e=>{console.log(JSON.stringify({ok:false,error:String(e.message||e)}));process.exit(1);});
