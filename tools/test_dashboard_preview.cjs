// Offline logic check only: no browser launch, network or rendering.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=path.resolve(__dirname,'..');
const file=path.join(root,'output/constructivist_dashboard_20261112/interactive.html');
const html=fs.readFileSync(file,'utf8');
const nodes=new Map([...html.matchAll(/id="([^"]+)"/g)].map(m=>[m[1],{
 innerHTML:'',hidden:m[1]==='ledger',style:{},attributes:{},
 classList:{set:new Set(),toggle(k,v){if(v)this.set.add(k);else this.set.delete(k)}},
 setAttribute(k,v){this.attributes[k]=v}
}]));
const context=vm.createContext({document:{getElementById(id){assert(nodes.has(id),id);return nodes.get(id)}}});
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
new vm.Script(script).runInContext(context);
const n=id=>nodes.get(id);
assert(n('score').innerHTML.includes('78.5'));
n('r-4').onclick();assert(n('status').innerHTML.includes('乌拉尔'));
n('s-2').onclick();assert(n('status').innerHTML.includes('工业与资源'));
n('all').onclick();assert(n('status').innerHTML.includes('全部地区'));
n('ledger-toggle').onclick();assert(!n('ledger').hidden);
n('close').onclick();assert(n('ledger').hidden);
n('sample').onchange({target:{value:'0'}});assert(n('score_label').innerHTML.includes('预备建设'));
assert(n('anim-rotor').classList.set.has('still'));
n('sample').onchange({target:{value:'2'}});assert(n('score').innerHTML.includes('136.5'));
assert(!n('anim-rotor').classList.set.has('still'));
assert(![...nodes.values()].some(n=>n.innerHTML.includes('[?')));
for(const m of html.matchAll(/(?:src="|url\()([^"\)]+\.(?:png|gif))/g))assert(fs.existsSync(path.resolve(path.dirname(file),m[1])),m[1]);
console.log('PASS preview script: region/type/reset/ledger/state/asset references; no browser used.');
