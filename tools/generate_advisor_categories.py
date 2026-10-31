"""Restore native KR adviser profession filters and original card badges.
Default/check is read-only; --write updates outputs; --write --assets repacks existing art.
"""
from pathlib import Path
from dataclasses import dataclass
import argparse, hashlib, json, re
ROOT = Path(__file__).resolve().parents[1]
KR = ROOT.parent / '1521695605'
ART = ROOT / 'tools/design/advisor_categories_20261031'
ATLAS = 'gfx/interface/ideas/RUS_advisor_categories.png'
CATEGORIES = [
    ('bolshevik', '俄共（布）', 'Bolsheviks', 'Большевики', ('KR_bolshevik_',)),
    ('sr', '社会革命党', 'Socialist Revolutionaries', 'Социалисты-революционеры', ('KR_sr_',)),
    ('sr_populist', '社革党（民粹派）', 'SR Populists', 'Эсеры-народники', ('KR_spiridonist_',)),
    ('sr_maximalist', '社革党（最高纲领派）', 'SR Maximalists', 'Эсеры-максималисты', ('KR_maximalist_',)),
    ('vst_left', '全俄劳联（左派）', 'VST Left', 'Левое крыло ВСТ', ('KR_vst_left_',)),
    ('vst_centre', '全俄劳联（中派）', 'VST Centre', 'Центр ВСТ', ('KR_vst_centre_',)),
    ('vst_right', '全俄劳联（右派）', 'VST Right', 'Правое крыло ВСТ', ('KR_vst_right_',)),
    ('menshevik', '孟什维克', 'Mensheviks', 'Меньшевики', ('KR_menshevik_',)),
    ('sds', '社会民主联盟', 'Social Democratic Union', 'Социал-демократический союз', ('KR_sds_',)),
]

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

FLAG = 'RUS_ui_advisor_faction_'
GUARD = 'RUS_ui_advisor_matches_faction'


def outputs():
    import sys
    from native_advisor_filters import build
    return build(sys.modules[__name__])


def assets(write):
    source = KR/'gfx/interface/ideas/idea_traits_strip.dds'
    paths = [source]+[ART/(row[0]+'.png') for row in CATEGORIES]
    hashes = {str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else 'KR/idea_traits_strip.dds': hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    record = ART/'atlas_hashes.json'
    if write:
        from PIL import Image
        original = Image.open(source).convert('RGBA')
        assert original.size == (828,46)
        image = Image.new('RGBA',(27*46,46))
        image.paste(original,(0,0))
        for i,p in enumerate(paths[1:],18):
            icon=Image.open(p).convert('RGBA')
            assert icon.size == (46,46)
            image.paste(icon,(46*i,0))
        target=ROOT/ATLAS;target.parent.mkdir(parents=True,exist_ok=True);image.save(target)
        hashes[ATLAS]=hashlib.sha256(target.read_bytes()).hexdigest()
        record.write_text(json.dumps(hashes,indent=2)+'\n',encoding='utf-8')
    else:
        hashes[ATLAS]=hashlib.sha256((ROOT/ATLAS).read_bytes()).hexdigest()
        assert hashes == json.loads(record.read_text(encoding='utf-8')), 'Stale atlas or artwork; review before --write --assets'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group();mode.add_argument('--write',action='store_true');mode.add_argument('--check',action='store_true')
    parser.add_argument('--assets',action='store_true');args=parser.parse_args()
    assert not args.assets or args.write
    data,count=outputs();stale=[]
    for name,text in data.items():
        p=ROOT/name
        if args.write:
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text(text,encoding='utf-8-sig' if name.endswith('.yml') else 'utf-8',newline='\n')
        elif not p.exists() or (p.read_bytes().decode('utf-8-sig') if name.startswith('history/') else p.read_text(encoding='utf-8-sig'))!=text:stale.append(name)
    assets(args.assets)
    assert not stale,'Stale generated files: '+', '.join(stale)
    print(f'PASS: native profession filters; no synthetic role ledgers; '+('written' if args.write else 'read-only'))


if __name__=='__main__':main()
