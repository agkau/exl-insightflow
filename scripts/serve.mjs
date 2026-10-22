import {createServer} from 'node:http';
import {readFile,stat} from 'node:fs/promises';
import {resolve,extname,sep} from 'node:path';
const root=resolve(import.meta.dirname,'..');
const port=Number(process.env.PORT||4173);
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8','.csv':'text/csv; charset=utf-8','.svg':'image/svg+xml'};
createServer(async(req,res)=>{
  try{
    const path=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
    const target=resolve(root,'.'+(path==='/'?'/index.html':path));
    if(!(target===root||target.startsWith(root+sep))){res.writeHead(403).end('Forbidden');return;}
    if((await stat(target)).isDirectory()){res.writeHead(403).end('Directory listing disabled');return;}
    const body=await readFile(target);
    res.writeHead(200,{'Content-Type':types[extname(target)]||'application/octet-stream','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}).end(body);
  }catch{res.writeHead(404).end('Not found');}
}).listen(port,()=>console.log(`InsightFlow development server: http://localhost:${port}/`));
