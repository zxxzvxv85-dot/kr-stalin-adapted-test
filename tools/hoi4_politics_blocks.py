from pathlib import Path
import re,json
from dataclasses import dataclass
R=Path(__file__).resolve().parents[1];KR=R.parent/'1521695605'
@dataclass
class N:
 k:str;op:str;v:object;a:int;b:int;s:str;ia:int=0;ib:int=0
 def children(self,k):return [x for x in self.v if x.k==k] if isinstance(self.v,list) else []
 def one(self,k):return next(iter(self.children(k)),None)
 def value(self,k,default=''):
  n=self.one(k);return n.v if n else default
 def raw(self):return self.s[self.a:self.b]
 def inner(self):return self.s[self.ia:self.ib] if isinstance(self.v,list) else self.v
 def norm(self):return (self.k,self.op,tuple(x.norm() for x in self.v) if isinstance(self.v,list) else self.v)
def parse(s):
 ts=[m for m in re.finditer(r'#[^\n]*|"(?:\\.|[^"\\])*"|[{}]|[<>!=]=?|[^\s{}=<>!#]+',s) if not m[0].startswith('#')];i=0
 def block():
  nonlocal i
  ns=[]
  while i<len(ts) and ts[i][0]!='}':
   k=ts[i];i+=1
   if i>=len(ts) or ts[i][0] not in ['=','<','>','>=','<=','!=']:
    ns.append(N(k[0],None,None,k.start(),k.end(),s));continue
   op=ts[i][0];i+=1;v=ts[i];i+=1
   if v[0]=='{':
    inner=block();end=ts[i];assert end[0]=='}';i+=1
    ns.append(N(k[0],op,inner,k.start(),end.end(),s,v.end(),end.start()))
   else:ns.append(N(k[0],op,v[0],k.start(),v.end(),s))
  return ns
 out=block();assert i==len(ts);return out
def load(p):return parse(p.read_text(encoding='utf-8-sig'))
def data(p,key):return next(n for n in load(p) if n.k==key)
def tokens(n):return [x.k for x in n.v] if n else []
def roles(chars):return {(c.k,a.value('idea_token')):(c,a) for c in chars.v for a in c.children('advisor')}
def main():
 mc=data(R/'common/characters/RUS characters.txt','characters');bc=data(KR/'common/characters/RUS characters.txt','characters')
 mr=roles(mc);br=roles(bc);rows=[]
 for key,(c,a) in mr.items():
  if a.value('slot') not in ['political_advisor','second_in_command']:continue
  orig=br.get(key)
  if not orig:rows.append({'key':key,'new':True});continue
  b=orig[1];fields=sorted({x.k for x in a.v}|{x.k for x in b.v})
  changed=[k for k in fields if [x.norm() for x in a.children(k)]!=[x.norm() for x in b.children(k)]]
  if changed:rows.append({'key':key,'fields':changed,'kr_traits':tokens(b.one('traits')),'mod_traits':tokens(a.one('traits'))})
 print(json.dumps(rows,ensure_ascii=False,indent=1))
 kt={t.k:t for p in (KR/'common/country_leader').glob('*.txt') for root in load(p) if root.k=='leader_traits' for t in root.v}
 mt={t.k:(p,t) for p in (R/'common/country_leader').glob('*.txt') for root in load(p) if root.k=='leader_traits' for t in root.v}
 print('SHARED TRAIT OVERRIDES')
 for k,(p,t) in mt.items():
  if k in kt and t.norm()!=kt[k].norm():print(k,p.name,kt[k].inner().strip()[:180].replace('\n',' '),'->',t.inner().strip()[:160].replace('\n',' '))
if __name__=='__main__':main()
