"""Check generated references, page isolation and native UI dependencies."""
from __future__ import annotations
import os
import re
from pathlib import Path
from hoi4_politics_blocks import parse
from industrial_planning_factory_ui import render_outputs, LANGS
from test_factory_planning import ROOT, P, GUI, FX, TR, opened, check, call, put

GAME=Path(os.environ.get('HOI4_GAME_ROOT',ROOT.parents[3]/'common/Hearts of Iron IV'))
KR=Path(os.environ.get('HOI4_KR_ROOT',ROOT.parent/'1521695605'))


def walk(nodes):
    for node in nodes:
        yield node
        if isinstance(node.v,list):yield from walk(node.v)


def field(node,key,default=''):
    found=node.one(key)
    return found.v.strip('"') if found else default


def main():
    outputs=render_outputs();assert outputs==render_outputs();count=1
    for path,content in outputs.items():
        raw=(ROOT/path).read_bytes()
        assert raw.replace(b'\r\n',b'\n')==content.encode('utf-8-sig' if path.endswith('.yml') else 'utf-8'),path
        if path.endswith('.yml'):assert raw.startswith(b'\xef\xbb\xbf'),path
        else:parse(content)
        count+=1
    catalogs={}
    for lang in LANGS:
        content=outputs[f'localisation/{lang}/RUS_industrial_planning_l_{lang}.yml']
        rows=re.findall(r'^ (\w+):0 "(.*)"$',content,re.M)
        assert len(rows)==len(set(k for k,v in rows))
        assert len(rows)==len(content.splitlines())-1
        catalogs[lang]=dict(rows);count+=1
    catalog=catalogs['simp_chinese']
    assert all(set(cat)==set(catalog) for cat in catalogs.values());count+=1
    gui=parse(outputs['interface/RUS_industrial_planning.gui'])[0]
    window=next(n for n in gui.v if field(n,'name')=='RUS_industrial_planning_window')
    widgets=[n for n in window.v if n.k in ('buttonType','iconType','instantTextBoxType','containerWindowType')]
    names=[field(n,'name') for n in widgets];assert len(names)==len(set(names));count+=1
    triggers={n.k:n.v for n in GUI.one('triggers').v}
    effect_names={n.k.removesuffix('_click') for n in GUI.one('effects').v}
    assert {field(w,'name') for w in widgets if w.k=='buttonType'}==effect_names;count+=1
    assert all(k.removesuffix('_visible').removesuffix('_click_enabled') in names for k in triggers);count+=1
    assert not any(w.k=='containerWindowType' for w in widgets),'Nested backgrounds may leak across pages';count+=1
    # Include real rail segments and selected backgrounds in the page leak test.
    s=opened()
    for i in range(48):put(s,f'n{i}_rail',1)
    call(s,'refresh');call(s,'toggle_help')
    shared={'ip_title','ip_summary','ip_close'}
    for name in names:
        visible=name+'_visible' not in triggers or check(triggers[name+'_visible'],s)
        if name not in shared and not name.startswith('ip_help_') and name!='ip_back':assert not visible,name
    call(s,'toggle_help')
    for name in names:
        if name.startswith('ip_help_') or name=='ip_back':assert not check(triggers[name+'_visible'],s),name
    count+=2
    definitions=parse(outputs['common/scripted_localisation/RUS_industrial_planning_loc.txt'])
    defs={n.value('name'):n for n in definitions}
    for cat in catalogs.values():
        for key,text in cat.items():
            for ref in re.findall(r'\[(Get\w+)\]',text):assert ref in defs,(key,ref)
            for ref in re.findall(r'\$([^$]+)\$',text):assert ref in cat,(key,ref)
            assert 'STATE_' not in text and '$STATE' not in text
    for definition in definitions:
        for n in walk([definition]):
            if n.k=='localization_key':assert n.v in catalog,n.v
    count+=1
    for w in widgets:
        for key in ('text','buttonText','pdx_tooltip'):
            ref=field(w,key)
            if ref.startswith(P):assert ref in catalog,(field(w,'name'),ref)
    count+=1
    known=set(FX)|set(TR)
    for path,content in outputs.items():
        if path.endswith('.yml'):continue
        for n in walk(parse(content)):
            if n.k.startswith(P) and n.v in ('yes','no'):assert n.k in known,(path,n.k)
    count+=1
    # Every game file is resolved against the active mod, KR, then vanilla.
    sprites={field(n,'name'):n for n in parse(outputs['interface/RUS_industrial_planning.gfx'])[0].v}
    for name,sprite in sprites.items():
        asset=field(sprite,'textureFile',field(sprite,'texturefile'))
        assert any((root/asset).is_file() for root in (ROOT,KR,GAME)),(name,asset)
    for w in widgets:
        sprite=field(w,'spriteType',field(w,'quadTextureSprite'))
        if sprite.startswith('GFX_RUS_ip_'):assert sprite in sprites,sprite
    count+=1
    font_sources=[]
    for root in (GAME,KR,ROOT):
        font_sources.extend((root/'interface').glob('*.gfx'))
    fonts=set()
    for path in font_sources:
        source=path.read_text(encoding='utf-8-sig',errors='replace')
        fonts.update(re.findall(r'bitmapfont\s*=\s*{\s*name\s*=\s*"([^"]+)"',source))
    for w in widgets:
        font=field(w,'font',field(w,'buttonFont'))
        if font:assert font in fonts,font
    count+=1
    # Pure sandbox boundary: no real assets, legacy map, debt or old-plan hooks.
    active='\n'.join(v for k,v in outputs.items() if not k.endswith('.yml'))
    for forbidden in ['add_building_construction','build_railway','add_dynamic_modifier','add_resource','RUS_ip_plan_debt','RUS_ip_resource_penalty','RUS_ip_supply_open','GFX_RUS_ip_map','RUS_first_five_year_plan']:
        assert forbidden not in active,forbidden
    assert 'round' not in FX and 'RUS_ip_settle' not in FX;count+=1
    # Independent UI geometry catches actionable overlap, not merely text size.
    tiles=[w for w in widgets if field(w,'name').startswith('ip_cell_')]
    assert len(tiles)==48
    rectangles=[]
    for w in tiles:
        pos=w.one('position');x,y=int(field(pos,'x')),int(field(pos,'y'))
        for xx,yy in rectangles:assert x>=xx+80 or xx>=x+80 or y>=yy+80 or yy>=y+80
        rectangles.append((x,y))
    count+=1
    print(f'{count} layout/reference checks passed; 48 selectable tiles; no Russia-map dependencies.')


if __name__=='__main__':main()
