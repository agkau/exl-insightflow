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
  assert.match(fake('contentRoot').innerHTML,/Service performance over time/);
  assert.match(fake('roleTitle').textContent,/Executive leadership/);
  assert.doesNotMatch(fake('contentRoot').innerHTML,/Unable to load/);
});
test('navigation contains six workspaces',()=>{
  for(const name of ['Overview','Performance','Exceptions','Data lineage','Decision log','Data explorer'])
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
