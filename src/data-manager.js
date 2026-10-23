import {apiBase} from './config.js';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const attr=esc;
const schemaSources=['operations','workforce','quality','finance','teams','clients','workstreams'];
function unit(s){return `<span class="pill">${esc(s)}</span>`;}

export function managementHTML(){
 const url=apiBase();
 return `<div class="section-intro"><h2>Data management</h2><p>Import changing source files, validate relationships, preview the effects, publish safely and restore prior versions. Local demo works without a backend; live imports require the separately hosted service.</p></div>
 <div class="grid-equal">
 <div class="card card-pad">
 <div class="cardhead"><div><h2>Connection & freshness</h2><p>Public dashboard stays online if the backend is unavailable.</p></div>${url?unit('API configured'):unit('Static demo')}</div>
 <label class="field-label" for="apiUrl">Data API address (HTTPS for GitHub Pages)</label><input class="field" id="apiUrl" placeholder="https://your-api.example.com" value="${attr(url)}" autocomplete="off"/>
 <div style="display:flex;gap:8px;margin-top:10px;flex-wrap:wrap"><button class="outline-btn" id="saveApi">Save API address</button><button class="outline-btn" id="statusRefresh">Check connection</button></div>
 <div id="dataStatus" class="topnote" style="margin:16px 0 0"><span>ⓘ</span><div>${url?'Checking current source freshness…':'Using GitHub Pages static sample. For live database updates, deploy the API and enter its URL here. No connection is required for ordinary dashboard use.'}</div></div>
 </div>
 <div class="card card-pad"><div class="cardhead"><div><h2>Report dependencies</h2><p>Publishing waits until the entire candidate dataset passes validation.</p></div></div>
 <div class="small-lines"><b>Operations</b> → closing backlog; QA and finance reconciliation; portfolio metrics<br/><b>Workforce</b> → per-workstream allocation; staffing-related KPIs<br/><b>Quality</b> → QA ratios and operating exceptions<br/><b>Finance</b> → revenue, margin and cross-report reconciliation</div>
 <p class="footnote">Updates use one atomic database transaction. Old reports remain active if validation fails. The system will not invent invoice corrections.</p></div></div>
 <div class="card card-pad" style="margin-top:18px"><div class="cardhead"><div><h2>Secure report ingestion</h2><p>Supported: UTF-8 CSV or Excel XLSX. Select all mutually dependent files together for atomic validation and publication.</p></div><span class="pill">Admin only</span></div>
 <div class="grid-equal"><div><label class="field-label" for="adminToken">Administrator token (never stored)</label><input class="field" id="adminToken" type="password" placeholder="Token configured on backend" autocomplete="new-password"/>
 <label class="field-label" for="uploadReports">Source reports</label><input class="field" id="uploadReports" type="file" multiple accept=".csv,.xlsx"/>
 <label class="field-label" for="batchDescription">Change summary</label><input class="field" id="batchDescription" placeholder="Example: October operational correction" maxlength="200"/>
 </div><div><label class="field-label" for="sourceMap">Optional file-name mapping (JSON)</label><textarea class="field" id="sourceMap" style="min-height:68px;width:100%" spellcheck="false" placeholder='{"renamed_report.xlsx":"operations"}'></textarea>
 <label class="field-label" for="columnMap">Optional column mapping (JSON)</label><textarea class="field" id="columnMap" style="min-height:68px;width:100%" spellcheck="false" placeholder='{"operations":{"Total Closed":"cases_closed"}}'></textarea>
 </div></div>
 <label style="display:flex;gap:8px;align-items:center;margin:12px 0;font-size:12px"><input id="strictFinance" type="checkbox" checked/> Require finance reconciliation before publication (recommended)</label>
 <div style="display:flex;gap:10px;flex-wrap:wrap"><button class="outline-btn" id="previewImport">1. Preview & validate</button><button class="action-btn" id="publishImport" disabled>2. Publish validated batch</button><button class="outline-btn" id="refreshInbox">Run scheduled inbox scan</button></div>
 <div id="ingestionResult" class="topnote" style="margin:16px 0 0"><span>ⓘ</span><div>Preview never changes the active dataset. A successful preview enables publishing. Source files must have recognized names or be identified in file-name mapping.</div></div>
 <p class="footnote">Compatible aliases and basic currency/date conversions are automatic. Ambiguous fields, incorrect joins and inconsistent reports are rejected. Administrator token must belong to your trusted service; never publish it in GitHub.</p>
 </div>
 <div class="card card-pad" style="margin-top:18px"><div class="cardhead"><div><h2>Version history & rollback</h2><p>Immutable dataset versions, publication audit and last-known-good recovery.</p></div><button class="outline-btn" id="loadVersions">View versions</button></div>
 <div id="versionResults" class="small-lines">Connect an API and enter an administrator token to list versions.</div>
 <div style="display:flex;gap:8px;margin-top:12px;align-items:center;flex-wrap:wrap"><input id="rollbackVersion" class="field" type="number" min="1" style="max-width:180px" placeholder="Version ID"/><button class="outline-btn" id="rollbackAction">Restore version</button></div>
 </div>`;
}

let previewVersion=null;
function show(target,message,isError=false){const node=document.getElementById(target);if(!node)return;node.innerHTML=`<span>${isError?'⚠':'ⓘ'}</span><div>${esc(message)}</div>`;}
async function fetchJSON(path,options={}){
 const base=apiBase();if(!base)throw Error('Configure and save the backend API URL first.');
 const result=await fetch(base+path,options);
 let body;try{body=await result.json();}catch{throw Error(`Backend returned an unreadable response (HTTP ${result.status})`)}
 if(!result.ok)throw Error(typeof body.detail==='string'?body.detail:body.report?.errors?.join('; ')||`HTTP ${result.status}`);
 return body;
}
function headers(){let token=document.getElementById('adminToken')?.value||'';return {'Authorization':'Bearer '+token};}
function uploadForm(){
 const selected=document.getElementById('uploadReports')?.files;
 if(!selected?.length)throw Error('Select at least one CSV or XLSX report.');
 const form=new FormData();for(const file of selected)form.append('files',file);
 form.append('source_map',document.getElementById('sourceMap')?.value.trim()||'{}');
 form.append('mappings',document.getElementById('columnMap')?.value.trim()||'{}');
 form.append('strict_finance',document.getElementById('strictFinance')?.checked?'true':'false');
 form.append('description',document.getElementById('batchDescription')?.value||'Browser upload');
 return form;
}
async function loadStatus(){
 try{
  const status=await fetchJSON('/api/v1/status');
  const items=Object.entries(status.refresh||{}).filter(([k])=>['operations','workforce','quality','finance'].includes(k)).map(([k,v])=>`${k}: ${(v.at||'unknown').slice(0,19)}`).join(' · ');
  show('dataStatus',`LIVE DATABASE · Version ${status.version_id} · through ${status.data_end} · ${items}`);
 }catch(e){show('dataStatus',`Static sample remains available. Database status unavailable: ${e.message}`,true)}
}
export function enterManagement(){if(apiBase())loadStatus();}
export async function managementClick(id){
 try{
  if(id==='saveApi'){
   let url=(document.getElementById('apiUrl')?.value||'').trim().replace(/\/+$/,'');
   if(url && !/^https:\/\/[^\s/]+(?:\/[^\s]*)?$/i.test(url) && !/^http:\/\/(?:localhost|127\.0\.0\.1)(?::\d+)?$/i.test(url))throw Error('Use an HTTPS API URL, or localhost for local development.');
   localStorage.setItem('insightflow_api_url',url);show('dataStatus','Connection preference saved. Reload the page to activate the selected data source.');return;
  }
  if(id==='statusRefresh'){await loadStatus();return}
  if(id==='previewImport'){
   previewVersion=null;document.getElementById('publishImport').disabled=true;
   const data=await fetchJSON('/api/v1/ingest/preview',{method:'POST',headers:headers(),body:uploadForm()});
   previewVersion=data.publishable?data.active_version:null;
   document.getElementById('publishImport').disabled=!data.publishable;
   show('ingestionResult',`${data.publishable?'Validated':'Blocked'} · Base version ${data.active_version} · ${data.report?.new_fact_rows??'—'} fact rows · ${(data.report?.warnings||[]).join('; ')||'No warnings'} · ${(data.report?.errors||[]).join('; ')||'No validation errors'}`,!data.publishable);
   return;
  }
  if(id==='publishImport'){
   if(previewVersion===null)throw Error('Run a successful preview first.');
   const form=uploadForm();form.append('expected_version',String(previewVersion));
   const data=await fetchJSON('/api/v1/ingest/publish',{method:'POST',headers:headers(),body:form});
   previewVersion=null;document.getElementById('publishImport').disabled=true;
   show('ingestionResult',data.unchanged?`No changes detected; active dataset remains version ${data.version_id}.`:`Published dataset version ${data.version_id}. Reload to see recomputed KPIs and alerts.`);await loadStatus();return;
  }
  if(id==='refreshInbox'){
   const data=await fetchJSON('/api/v1/admin/refresh-inbox',{method:'POST',headers:headers()});
   show('ingestionResult',`Inbox refresh: ${data.processed} batch(es) processed; inspect audit log for failures.`);await loadStatus();return;
  }
  if(id==='loadVersions'){
   const versions=await fetchJSON('/api/v1/versions',{headers:headers()});
   document.getElementById('versionResults').innerHTML=versions.map(v=>`<div style="padding:8px 0;border-bottom:1px solid #e6e9f1"><b>#${Number(v.id)}</b> · ${esc(v.created_at)} · ${esc(v.description)}</div>`).join('')||'No versions';return;
  }
  if(id==='rollbackAction'){
   const version=Number(document.getElementById('rollbackVersion').value);
   if(!Number.isInteger(version)||version<1)throw Error('Enter a valid version number.');
   if(!confirm(`Restore dataset version ${version}? This will change the active reporting snapshot for all connected users.`))return;
   const d=await fetchJSON('/api/v1/rollback',{method:'POST',headers:{...headers(),'Content-Type':'application/json'},body:JSON.stringify({version_id:version})});
   show('ingestionResult',`Restored version ${d.active_version}. Reload to refresh dashboard.`);await loadStatus();return;
  }
 }catch(e){show(['saveApi','statusRefresh'].includes(id)?'dataStatus':id==='loadVersions'?'versionResults':'ingestionResult',e.message,true)}
}
export const MANAGEMENT_ACTIONS=['saveApi','statusRefresh','previewImport','publishImport','refreshInbox','loadVersions','rollbackAction'];
