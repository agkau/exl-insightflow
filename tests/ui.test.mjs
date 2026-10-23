import test,{after} from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const data=JSON.parse(await readFile(new URL('../data/app_data.json',import.meta.url),'utf8'));
const elements=new Map();
function fake(id){
  if(!elements.has(id)) elements.set(id,{
    id,value:id==='period'?'30':id==='role'?'Executive':'',innerHTML:'',textContent:'',dataset:{},style:{},listeners:{},
    addEventListener(name,fn){this.listeners[name]=fn;},get classList(){return {add(){},remove(){},toggle(){}}}
  });
  return elements.get(id);
}
const priorDocument=globalThis.document,priorFetch=globalThis.fetch,priorWindow=globalThis.window,priorStorage=globalThis.localStorage;
globalThis.document={getElementById:fake,querySelectorAll:()=>[],addEventListener(){},body:{appendChild(){}},createElement(){return {click(){},remove(){}}}};
globalThis.fetch=async()=>({ok:true,json:async()=>data});
globalThis.window={scrollTo(){}};
globalThis.localStorage={getItem(){return null},setItem(){}};
await import('../src/main.js');
await new Promise(resolve=>setImmediate(resolve));
test('initial dashboard renders after loading external data',()=>{
  assert.match(fake('contentRoot').innerHTML,/ROLE DECISION BRIEF/);
  assert.match(fake('roleTitle').textContent,/Executive leadership/);
  assert.doesNotMatch(fake('contentRoot').innerHTML,/Unable to load/);
});
test('navigation contains eight workspaces',()=>{
  for(const name of ['Overview','Performance','Exceptions','Data lineage','Decision log','Data explorer','Compare teams','Data management'])
    assert.ok(fake('nav').innerHTML.includes(name),name);
});
test('changing role updates persona and KPI cards',()=>{
  fake('role').value='Operations';fake('role').listeners.change({target:fake('role')});
  assert.match(fake('roleTitle').textContent,/Operations delivery/);
  assert.match(fake('contentRoot').innerHTML,/Absenteeism/);
});
test('navigating to exceptions renders worklist',()=>{
  fake('nav').listeners.click({target:{closest:()=>({dataset:{page:'exceptions'}})}});
  assert.match(fake('contentRoot').innerHTML,/Priority worklist/);
});
test('regional filter changes scope without changing module',()=>{
  fake('region').value='West';fake('region').listeners.change({target:fake('region')});
  assert.match(fake('contentRoot').innerHTML,/Priority worklist/);
  fake('nav').listeners.click({target:{closest:()=>({dataset:{page:'explorer'}})}});
  assert.match(fake('contentRoot').innerHTML,/180 matching workstream-day rows/);
});
test('data lineage module renders original source names',()=>{
  fake('nav').listeners.click({target:{closest:()=>({dataset:{page:'sources'}})}});
  assert.match(fake('contentRoot').innerHTML,/Delivery management export/);
  assert.match(fake('contentRoot').innerHTML,/Workforce planning export/);
});
// No mocks are needed after the integration checks.
after(()=>{globalThis.document=priorDocument;globalThis.fetch=priorFetch;globalThis.window=priorWindow;globalThis.localStorage=priorStorage;});

test('data management workspace exposes database connection, staged validation and version controls',()=>{
  fake('nav').listeners.click({target:{closest:()=>({dataset:{page:'manager'}})}});
  for(const section of ['Data management','Secure report ingestion','Preview & validate','Version history & rollback'])
    assert.ok(fake('contentRoot').innerHTML.includes(section),section);
});

test('eight distinct business roles are selectable',()=>{
 const items=(fake('role').innerHTML.match(/<option/g)||[]).length;
 assert.equal(items,8);
 for(const label of ['Finance Controller','Workforce Planner','Quality Lead','Client Account Manager','Regional Manager'])assert.ok(fake('role').innerHTML.includes(label));
});
test('each role has tailored KPIs, trends and decision brief',()=>{
 fake('nav').listeners.click({target:{closest:()=>({dataset:{page:'overview'}})}});
 const expected={Finance:['Delivery costs','Contribution margin'],Workforce:['Planned staff-days','Absenteeism'],Quality:['Rework rate','Quality pass rate'],Account:['CSAT positivity','SLA attainment'],Regional:['Closing backlog','Contribution margin'],Analyst:['Rework rate','Quality pass rate'],Operations:['Cases completed','Absenteeism'],Executive:['Revenue','Contribution margin']};
 for(const [role,labels] of Object.entries(expected)){
   fake('role').value=role;fake('role').listeners.change({target:fake('role')});
   const html=fake('contentRoot').innerHTML;
   for(const label of labels)assert.ok(html.includes(label),role+': '+label);
   assert.ok(html.includes('ROLE DECISION BRIEF'),role);
   assert.match(html,/Where to review first/);
 }
});
test('team comparison is role sensitive and drilldown changes selected team',()=>{
 fake('role').value='Workforce';fake('role').listeners.change({target:fake('role')});
 fake('nav').listeners.click({target:{closest:()=>({dataset:{page:'compare'}})}});
 assert.match(fake('contentRoot').innerHTML,/Role-based team comparison/);
 assert.match(fake('contentRoot').innerHTML,/Absenteeism/);
 const match=fake('contentRoot').innerHTML.match(/data-focus-team="([A-Z-]+)"/);assert.ok(match);
 fake('contentRoot').listeners.click({target:{closest:()=>({dataset:{focusTeam:match[1]}})}});
 assert.equal(fake('team').value,match[1]);
 assert.match(fake('contentRoot').innerHTML,/Operations and financial drivers/);
});

test('client account manager benchmarks clients, not internal delivery teams',()=>{
 fake('region').value='';fake('region').listeners.change({target:fake('region')});
 fake('role').value='Account';fake('role').listeners.change({target:fake('role')});
 fake('nav').listeners.click({target:{closest:()=>({dataset:{page:'compare'}})}});
 assert.match(fake('contentRoot').innerHTML,/Role-based client comparison/);
 assert.match(fake('contentRoot').innerHTML,/data-focus-client=/);
 assert.match(fake('contentRoot').innerHTML,/CSAT positivity/);
 const client=fake('contentRoot').innerHTML.match(/data-focus-client="(CL\d+)"/);assert.ok(client);
 fake('contentRoot').listeners.click({target:{closest:()=>({dataset:{focusClient:client[1]}})}});
 assert.equal(fake('client').value,client[1]);
 assert.match(fake('contentRoot').innerHTML,/Operations and financial drivers/);
});
