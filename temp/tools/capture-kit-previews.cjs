// Browser capture of real delivery-file overview pages, NOT upstream application UI.
const fs=require('fs'),http=require('http'),path=require('path'),assert=require('assert');
const {chromium}=require(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES+'/playwright');
const root=path.resolve(__dirname,'../..');
async function main(){
 const server=http.createServer((req,res)=>{
  const f=path.resolve(root,'.'+decodeURIComponent(req.url.split('?')[0]));
  if(!f.startsWith(root+path.sep)){res.writeHead(403);return res.end()}
  try{res.setHeader('Content-Type',f.endsWith('.html')?'text/html; charset=utf-8':'application/octet-stream');res.end(fs.readFileSync(f))}catch{res.writeHead(404);res.end()}
 });
 await new Promise(ok=>server.listen(0,'127.0.0.1',ok));
 const browser=await chromium.launch({headless:true,executablePath:process.env.KIT_QA_CHROME,args:['--no-sandbox']});
 const results=[];
 try{
  for(const project of ['dify-1.17.1','n8n-2.42.6','flowise-3.1.4','anythingllm-1.17.0']){
   const page=await browser.newPage({viewport:{width:1080,height:1080}}),errors=[];
   page.on('pageerror',e=>errors.push(e.message));
   const base=`http://127.0.0.1:${server.address().port}/temp/product-metadata/${project}/listing/`;
   await page.goto(base+'preview.html');await page.evaluate(()=>document.fonts.ready);
   assert.equal(await page.locator('.card').count(),4);
   assert((await page.innerText('body')).includes('不是产品运行截图'));
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   await page.screenshot({path:path.join(root,'temp/product-metadata',project,'listing/01-content-overview.png'),fullPage:true});
   await page.goto(base+'files.html');await page.evaluate(()=>document.fonts.ready);
   const urls=await page.locator('a').evaluateAll(nodes=>nodes.map(n=>n.href));
   for(const url of urls){const r=await page.request.get(url);assert(r.ok());}
   await page.screenshot({path:path.join(root,'temp/product-metadata',project,'listing/02-delivery-files.png'),fullPage:true});
   assert.deepEqual(errors,[]);results.push({project,viewport:[1080,1080],download_links:urls.length,all_links_valid:true,errors,screenshot_kind:'Actual custom delivery-file overview, not upstream app runtime'});
   await page.close();console.log('PASS',project);
  }
  fs.writeFileSync(path.join(root,'temp/docs/install-kit-preview-qa.json'),JSON.stringify(results,null,2)+'\n');
 }finally{await browser.close();await new Promise(ok=>server.close(ok))}
}
main().catch(e=>{console.error(e);process.exit(1)});
