const fs = require('fs');
const path = require('path');
const {chromium}=require('C:/Users/Playdata/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{
  const input=process.argv[2];
  const stem=process.argv[3]||'original';
  const wd=__dirname;
  let script=fs.readFileSync(path.join(wd,'hwpjs/package/build/esm.js'),'utf8');
  script=script.replace("import require$$0 from 'fs';",'const require$$0={};')
    .replace('export { HWPViewer as Viewer, parse };','globalThis.HWP={Viewer:HWPViewer,parse};');
  const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
  const page=await browser.newPage({viewport:{width:1100,height:1500},deviceScaleFactor:1});
  const logs=[]; page.on('pageerror',e=>logs.push(String(e))); page.on('console',m=>{if(m.type()==='error')logs.push(m.text())});
  await page.setContent('<!DOCTYPE html><html><head><style>*{box-sizing:border-box}html,body{margin:0;padding:0}body{background:#eee}#app>div>div{margin-bottom:12px!important}canvas{display:block}@media print{body{background:white}#app>div>div{margin:0!important;box-shadow:none!important}}</style></head><body><div id="app"></div></body></html>');
  await page.addScriptTag({content:script});
  const bytes=Array.from(fs.readFileSync(input));
  const result=await page.evaluate(bytes=>{try{globalThis.viewer=new HWP.Viewer(document.querySelector('#app'),new Uint8Array(bytes),{type:'array'});return {pages:document.querySelectorAll('[data-page-number]').length,html:document.querySelector('#app').innerHTML,text:document.body.innerText};}catch(e){return {error:String(e),stack:e.stack}}},bytes);
  await page.evaluate(()=>document.fonts.ready);
  await page.screenshot({path:path.join(wd,stem+'.png'),fullPage:true});
  const pages=page.locator('#app [data-page-number]').filter({has:page.locator('canvas')});
  const divs=page.locator('#app div[data-page-number]').filter({hasNot:page.locator('.hwpjs-observer')});
  const targets=page.locator('#app div[data-page-number]:not(.hwpjs-observer)');
  for(let i=0;i<await targets.count();i++) await targets.nth(i).screenshot({path:path.join(wd,`${stem}-page-${i+1}.png`)});
  fs.writeFileSync(path.join(wd,stem+'_result.json'),JSON.stringify({...result,logs},null,2));
  console.log(JSON.stringify({error:result.error,pages:await targets.count(),logs}));
  await browser.close();
})();
