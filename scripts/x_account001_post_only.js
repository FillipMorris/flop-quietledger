const { chromium }=require('playwright-core');
const fs=require('fs'); const path=require('path');
const OUT='/opt/data/work/flop/agents/quietledger/receipts/tmp/twitter-account001-post-only'; fs.mkdirSync(OUT,{recursive:true});
const CDP=process.env.CDP||'http://127.0.0.1:18801';
const USER='cyberkot1eta';
const TEXT=`QuietLedger maintains a public FLOP / Technocore proof chain: Ed25519 DID, GitHub receipts, and signed evidence.\n\nRepo: https://github.com/FillipMorris/flop-quietledger\n\n@flop_labs Technocore $FLOP`;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{const b=await chromium.connectOverCDP(CDP,{timeout:15000}); const ctx=b.contexts()[0]; const p=ctx.pages().filter(x=>/x\.com/.test(x.url())).pop()||await ctx.newPage();
await p.goto('https://x.com/compose/post',{waitUntil:'domcontentloaded',timeout:60000}); await sleep(5000); await p.getByText('Accept all cookies').click({force:true,timeout:1000}).catch(()=>{});
let box=p.locator('[data-testid="tweetTextarea_0"][role="textbox"], div[aria-label="Post text"][role="textbox"]').first();
await box.click({force:true,timeout:10000}); await p.keyboard.press('Control+A').catch(()=>{}); await p.keyboard.press('Backspace').catch(()=>{}); await p.keyboard.type(TEXT,{delay:12}); await sleep(2000);
let dbg=await p.evaluate(()=>({url:location.href, boxes:Array.from(document.querySelectorAll('[data-testid="tweetTextarea_0"], [role="textbox"]')).map((e,i)=>({i,test:e.getAttribute('data-testid'),aria:e.getAttribute('aria-label'),txt:(e.innerText||e.textContent||'').slice(0,300)})), buttons:Array.from(document.querySelectorAll('[data-testid="tweetButton"], [data-testid="tweetButtonInline"]')).map(b=>({test:b.getAttribute('data-testid'),disabled:b.disabled,txt:b.innerText}))}));
fs.writeFileSync(path.join(OUT,'compose-debug.json'),JSON.stringify(dbg,null,2));
let okText=JSON.stringify(dbg).includes('QuietLedger maintains'); if(!okText) throw new Error('textbox_empty');
let btn=p.locator('[data-testid="tweetButton"], [data-testid="tweetButtonInline"]').filter({hasText:/Post/i}).first();
await btn.click({force:true,timeout:12000}); await sleep(10000);
await p.goto('https://x.com/'+USER,{waitUntil:'domcontentloaded',timeout:60000}); await sleep(8000);
let url=null, foundText=false;
for(let pass=0; pass<5 && !url; pass++){
 const n=await p.locator('article').count().catch(()=>0);
 for(let i=0;i<Math.min(n,12);i++){const a=p.locator('article').nth(i); const tx=await a.innerText({timeout:1500}).catch(()=> ''); if(tx.includes('QuietLedger maintains')&&tx.includes('flop-quietledger')){foundText=true; const links=await a.locator('a[href*="/status/"]').evaluateAll(els=>els.map(e=>e.href)).catch(()=>[]); url=links.find(h=>h.includes('/status/'))||links[0]||null; break}}
 if(!url){await p.mouse.wheel(0,700); await sleep(1500)}
}
const result={ok:!!url,foundText,new_post_url:url,text:TEXT,profile:'account-001',cdp:CDP,artifacts_dir:OUT,ts:new Date().toISOString()}; fs.writeFileSync(path.join(OUT,'post-result.json'),JSON.stringify(result,null,2)); console.log(JSON.stringify(result,null,2)); process.exit(result.ok?0:2);
})().catch(e=>{const r={ok:false,error:String(e.message||e),profile:'account-001',cdp:CDP,artifacts_dir:OUT,ts:new Date().toISOString()}; fs.writeFileSync(path.join(OUT,'post-error.json'),JSON.stringify(r,null,2)); console.log(JSON.stringify(r,null,2)); process.exit(1)});
