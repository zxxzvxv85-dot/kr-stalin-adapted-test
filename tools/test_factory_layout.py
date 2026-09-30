"""Check generated references, page isolation and native UI dependencies."""
from __future__ import annotations
import os
import re
from pathlib import Path
from PIL import Image
from hoi4_politics_blocks import parse
from industrial_planning_factory_ui import render_outputs, LANGS, BOARD_X, BOARD_Y, TILE_STEP, WINDOW_WIDTH, WINDOW_HEIGHT
from industrial_planning_factory import CELLS, REGIONS, WIDTH, HEIGHT
from industrial_planning_catalog import PLANTS, FREIGHT_KIND, region_plants, extra_stocks
from industrial_planning_factory_assets import ASSET_DIR, COLOUR_SPRITES, render_assets
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
    for lang,cat in catalogs.items():
        for c in CELLS:
            header=cat[P+f'node_{c["id"]}_tt'].split(r'\n',1)[0]
            region=REGIONS[c['region']]['zh' if lang=='simp_chinese' else 'en']
            assert header.startswith('§Y'+region+' · '),(lang,c['id'],header)
            assert '$' not in header and 'RUS_ip_' not in header,'Nested region keys leaked in game tooltips'
    count+=1
    gui=parse(outputs['interface/RUS_industrial_planning.gui'])[0]
    window=next(n for n in gui.v if field(n,'name')=='RUS_industrial_planning_window')
    assert int(field(window.one('size'),'width'))==WINDOW_WIDTH
    assert int(field(window.one('size'),'height'))==WINDOW_HEIGHT
    widgets=[n for n in window.v if n.k in ('buttonType','iconType','instantTextBoxType','containerWindowType')]
    names=[field(n,'name') for n in widgets];assert len(names)==len(set(names));count+=1
    triggers={n.k:n.v for n in GUI.one('triggers').v}
    effect_names={n.k.removesuffix('_click') for n in GUI.one('effects').v}
    assert {field(w,'name') for w in widgets if w.k=='buttonType'}==effect_names;count+=1
    assert all(k.removesuffix('_visible').removesuffix('_click_enabled') in names for k in triggers);count+=1
    assert not any(w.k=='containerWindowType' for w in widgets),'Nested backgrounds may leak across pages';count+=1
    # Include real rail segments and selected backgrounds in the page leak test.
    s=opened()
    for c in CELLS:put(s,f'n{c["id"]}_rail',1)
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
    assets=render_assets();assert assets==render_assets()
    for key,(width,height,rgb) in COLOUR_SPRITES.items():
        path=f'{ASSET_DIR}/{key}.png';sprite=sprites['GFX_RUS_ip_'+key]
        assert sprite.k=='spriteType' and field(sprite,'texturefile')==path
        assert (ROOT/path).read_bytes()==assets[path]
        with Image.open(ROOT/path) as img:
            assert img.size==(width,height) and img.mode=='RGBA'
            assert img.getextrema()==tuple((c,c) for c in (*rgb,255))
    count+=1
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
    assert len(tiles)==len(CELLS)
    for r in REGIONS:
        rectangles=[];call(s,f'select_region_{r["id"]}')
        for w in tiles:
            name=field(w,'name');i=int(name.rsplit('_',1)[1]);visible=check(triggers[name+'_visible'],s)
            assert visible==(CELLS[i]['region']==r['id'])
            if not visible:continue
            pos=w.one('position');x,y=int(field(pos,'x')),int(field(pos,'y'))
            assert BOARD_X<=x and x+40<=BOARD_X+WIDTH*TILE_STEP and BOARD_Y<=y and y+40<=BOARD_Y+HEIGHT*TILE_STEP
            for xx,yy in rectangles:assert x>=xx+40 or xx>=x+40 or y>=yy+40 or yy>=y+40
            rectangles.append((x,y))
        assert len(rectangles)==len(r['cells']);count+=1
    assert field(sprites['GFX_RUS_ip_tile'].one('size'),'x')=='40'
    # Compare text against real visible tile rectangles, not the formerly
    # empty bounding-box margin now used for regional inventory icons.
    for r in REGIONS:
        call(s,f'select_region_{r["id"]}')
        active_tiles=[w for w in tiles if check(triggers[field(w,'name')+'_visible'],s)]
        for w in widgets:
            name=field(w,'name')
            if w.k!='instantTextBoxType':continue
            if name+'_visible' in triggers and not check(triggers[name+'_visible'],s):continue
            x,y=int(field(w.one('position'),'x')),int(field(w.one('position'),'y'))
            width,height=int(field(w,'maxWidth')),int(field(w,'maxHeight'))
            for tile in active_tiles:
                xx,yy=int(field(tile.one('position'),'x')),int(field(tile.one('position'),'y'))
                assert x+width<=xx or x>=xx+40 or y+height<=yy or y>=yy+40,(name,field(tile,'name'))
    count+=1
    assert len({COLOUR_SPRITES[f'grade_{i}'][2] for i in (1,2,3)})==3
    for level in (1,2,3):
        widget=next(w for w in widgets if field(w,'name')==f'ip_grade_legend_{level}')
        assert field(widget,'spriteType')==f'GFX_RUS_ip_legend_{level}' and field(widget,'scale')=='1'
        w,h,rgb=COLOUR_SPRITES[f'legend_{level}']
        assert (w,h)==(16,16) and rgb==COLOUR_SPRITES[f'grade_{level}'][2]
        note=next(w for w in widgets if field(w,'name')=='ip_start')
        assert int(field(widget.one('position'),'y'))+h<int(field(note.one('position'),'y')),'Swatch overlaps the regional text'
    count+=1
    assert all('[GetRUSIPNodeStatus' in catalog[P+f'node_{c["id"]}_tt'] for c in CELLS);count+=1
    for r in REGIONS:
        call(s,f'select_region_{r["id"]}')
        for page in (0,1,2):
            call(s,f'build_page_{page}')
            visible=[n for n in names if n+'_visible' in triggers and check(triggers[n+'_visible'],s)]
            for kind in PLANTS:
                for other in REGIONS:
                    name=f'ip_r{other["id"]}_build_{kind}'
                    if name not in names:continue
                    expected=page==1 and other['id']==r['id']
                    assert (name in visible)==expected
                    assert all((name+tail in visible)==expected for tail in ('_icon','_title','_cost'))
            count+=1
    assert max(len([k for k in region_plants(r['id']) if 5<k<FREIGHT_KIND]) for r in REGIONS)==10
    for rid in range(6):
        call(s,f'select_region_{rid}');call(s,'build_page_2')
        for name in names:
            if not name.startswith('ip_freight_r'):continue
            origin=int(name.split('_')[2][1:])
            assert check(triggers[name+'_visible'],s)==(origin==rid),name
    count+=1
    for kind,p in PLANTS.items():
        assert f'建设投资：§R-{p["cost"]}§!' in catalog[P+f'build_{kind}_tt']
        assert '每日' in catalog[P+f'build_{kind}_tt']
    count+=1
    print(f'{count} layout/reference checks passed; {len(CELLS)} selectable tiles across six isolated pages.')


if __name__=='__main__':main()
