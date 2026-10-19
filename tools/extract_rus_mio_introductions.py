"""Export existing Chinese RUS MIO introductions, with include inheritance/provenance.

No runtime writes. Default is a read-only summary; --write saves TXT/JSON to output.
"""
from pathlib import Path
import argparse,json,re
from hoi4_politics_blocks import load

ROOT=Path(__file__).resolve().parents[1]
GAME=ROOT.parents[3]/'common/Hearts of Iron IV'
OUT=ROOT/'output/rus_mio_introductions_20261019'

def extract():
    bases=[GAME,ROOT.parent/'1521695605',ROOT.parent/'3391120577',ROOT.parent/'2946487287',ROOT]
    loc={};loc_sources={};files={}
    for base in bases:
        for p in sorted((base/'localisation/simp_chinese').rglob('*.yml')):
            for m in re.finditer(r'^\s*([\w.-]+):\d*\s+"((?:\\.|[^"\\])*)"',p.read_text(encoding='utf-8-sig'),re.M):
                # Preserve Unicode and decode only localisation's string escapes.
                loc[m[1]]=m[2].replace('\\n','\n').replace('\\"','"').replace('\\\\','\\')
                loc_sources[m[1]]=str(p.resolve())
        for p in sorted((base/'common/military_industrial_organization/organizations').glob('*.txt')):
            if not p.name.startswith('_'):files[p.name]=p
    orgs={};org_sources={}
    for p in files.values():
        for n in load(p):orgs[n.k]=n;org_sources[n.k]=str(p.resolve())
    approved=json.loads((ROOT/'tools/design/RUS_stalin_mio_names.json').read_text(encoding='utf-8'))
    renamed={org:r['name'] for r in approved for org in [r['org']]+r.get('related',[])}
    def inherited(org,field,seen=()):
        assert org not in seen,('include cycle',org)
        n=orgs[org]
        if n.one(field):return n.one(field),org
        parent=n.value('include')
        return inherited(parent,field,seen+(org,)) if parent else (None,org)
    def expand(key,seen=()):
        assert key not in seen,('localisation cycle',key)
        assert key in loc,('missing Chinese localisation',key)
        return re.sub(r'\$([\w.-]+)\$',lambda m:expand(m[1],seen+(key,)),loc[key])
    def plain(text):
        text=re.sub(r'§.', '',text)
        return re.sub(r'£\w+\s*','',text).strip()
    rows=[]
    for org in sorted(k for k in orgs if k.startswith('RUS_')):
        name,_=inherited(org,'name');name_key=name.v if name else org
        original=plain(expand('RUS_'+name_key if 'RUS_'+name_key in loc else name_key))
        trait,owner=inherited(org,'initial_trait');intro_key=trait.value('name','') if trait else ''
        if intro_key and 'RUS_'+intro_key in loc:intro_key='RUS_'+intro_key
        if not intro_key:intro_key=owner+'_initial_trait'
        assert intro_key in loc,('initial trait not localised',org,intro_key)
        expanded=plain(expand(intro_key));lines=expanded.splitlines();kind=lines[0].strip();body='\n'.join(lines[1:]).strip()
        # Some native introductions keep their prose in the standard separate desc key.
        if not body and intro_key+'_desc' in loc:body=plain(expand(intro_key+'_desc'))
        assert not re.search(r'\$[\w.-]+\$|\[[A-Za-z_]',kind+'\n'+body),(org,'unresolved localisation')
        rows.append(dict(id=org,name=renamed.get(org,original),kr_name=original,kind=kind,introduction=body,inherited_from=owner if owner!=org else None,localisation_key=intro_key,localisation_source=loc_sources[intro_key],definition_source=org_sources[org]))
    return rows

def main():
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();rows=extract()
    if a.write:
        OUT.mkdir(parents=True,exist_ok=True)
        text='RUS 军工机构介绍汇总\n\n机构名使用当前斯大林上台后的名称；介绍正文逐字提取现有简体中文本地化，去除颜色代码，不重写历史叙事。包括继承母机构介绍的衍生机构；只有类型、没有介绍正文的项目单独注明。不含特质效果、修正或数值。\n\n'
        for i,r in enumerate(rows,1):
            variant={'RUS_sokol_construction_organisation':'（原索科尔建设分支）','RUS_sokol_production_organisation':'（原索科尔生产分支）'}.get(r['id'],'')
            text+=f'{i:02d}. {r["name"]}{variant}\n'
            if r['name']!=r['kr_name']:text+='KR 原名：'+r['kr_name']+'\n'
            text+='设计商类型：'+r['kind']+'\n介绍：\n'+(r['introduction'] or '（当前没有介绍正文。）')+'\n\n'
            if r['inherited_from']:text+='注：沿用母机构的介绍。\n\n'
        (OUT/'RUS军工机构介绍.txt').write_text(text,encoding='utf-8-sig')
        (OUT/'RUS军工机构介绍_来源.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(count=len(rows),with_prose=sum(bool(r['introduction']) for r in rows),inherited=sum(bool(r['inherited_from']) for r in rows),output=str(OUT) if a.write else None),ensure_ascii=True))
if __name__=='__main__':main()
