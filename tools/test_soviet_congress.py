"""Execute generated display effects and check seat geometry, entry wiring and assets.

Uses the existing fail-closed script fixture with only native while-loop/array extensions.
This is not a substitute for the engine's GUI renderer.
"""
from collections import Counter
from io import BytesIO
import json
import hashlib
import math
import re

from PIL import Image
from doudizhu_script_model import ScriptModel
from hoi4_politics_blocks import load
from generate_soviet_congress import ROOT, PARTIES, CHILDREN, ALL_PARTIES, FRAMES, LEADERS, TOTAL, WIDTH, HEIGHT, MAIN_HEIGHT, CONTENT_RIGHT, HALL_SIZE, VERTICAL_SHIFT, PARENTS, CIVIC_SOURCES, SHARED, PORTRAIT_LINE_GAP, outputs, seats, table_rows, row_elements, leader_portraits, leader_textures, portrait_texticon
from hoi4_bitmap_fonts import GAME
from hoi4_bitmap_fonts import measure, font_data


class CongressModel(ScriptModel):
    def __init__(self, effects):
        super().__init__(effects); self.arrays={}

    def check(self,nodes):
        nodes=nodes.v if hasattr(nodes,'v') else nodes
        return all(self.check(n.v) if n.k=='RUS' else super(CongressModel,self).check([n]) for n in nodes)

    def run(self, nodes):
        taken=None
        for node in nodes:
            if node.k=='if':
                taken=self.check(node.one('limit'))
                if taken: self.run([n for n in node.v if n.k!='limit'])
                continue
            if node.k=='else':
                assert taken is not None, 'Orphan else'
                if not taken: self.run(node.v)
                taken=None
                continue
            taken=None
            if node.k=='log':
                continue
            elif node.k=='RUS':
                self.run(node.v)
            elif node.k=='clear_array':
                self.arrays[node.v]=[]
            elif node.k=='add_to_array':
                self.arrays.setdefault(node.v[0].k,[]).append(self.number(node.v[0].v))
            elif node.k=='while_loop_effect':
                iterations=0
                while self.check(node.one('limit')):
                    self.run([n for n in node.v if n.k!='limit'])
                    iterations+=1; assert iterations<=800
            else:
                super().run([node])


def check_partition(model, distribution, expanded=False):
    for (key,*_),n in zip(PARTIES,distribution): model.vars['RUS_congress_'+key+'_seats']=n
    def distribute(parent):
        if parent not in CHILDREN: return
        children=CHILDREN[parent];count=model.vars['RUS_congress_'+parent+'_seats']
        raw=[count*row[3]/sum(r[3] for r in children) for row in children]
        allocation=[math.floor(n) for n in raw]
        for i in sorted(range(len(raw)),key=lambda i:raw[i]-allocation[i],reverse=True)[:count-sum(allocation)]: allocation[i]+=1
        for row,n in zip(children,allocation):
            model.vars['RUS_congress_'+row[0]+'_seats']=n
            distribute(row[0])
    for row in PARTIES: distribute(row[0])
    for parent,var in CIVIC_SOURCES.items(): model.vars[var]=model.vars['RUS_congress_'+parent+'_seats']//2
    model.vars['RUS_congress_sr_citizens_seats']=sum(model.vars[v] for v in CIVIC_SOURCES.values())
    if expanded: model.flags.add('RUS_congress_show_children')
    else: model.flags.discard('RUS_congress_show_children')
    model.call('RUS_congress_refresh_display')
    array=model.arrays['RUS_congress_seats']
    assert len(array)==800
    def leaf_counts(row):
        if expanded and row[0] in CHILDREN:
            result=[item for child in CHILDREN[row[0]] for item in leaf_counts(child)]
            return result+([(SHARED[0],model.vars['RUS_congress_sr_citizens_seats'])] if row[0]=='sr' else [])
        count=model.vars['RUS_congress_'+row[0]+'_seats']
        if expanded and row[0] in CIVIC_SOURCES: count-=model.vars[CIVIC_SOURCES[row[0]]]
        return [(row[0],count)]
    expected=[FRAMES[key] for row in PARTIES for key,count in leaf_counts(row) for _ in range(int(count))]
    assert array==expected, 'Party seats must form continuous sectors, preserving parent totals'
    assert math.isclose(sum(model.vars['RUS_congress_'+key+'_percent'] for key,*_ in PARTIES),100)


def main():
    generated=outputs()
    assert all((ROOT/p).read_bytes()==data for p,data in generated.items())
    effects={n.k:n for n in load(ROOT/'common/scripted_effects/RUS_soviet_congress.txt')}
    model=CongressModel(effects); model.call('RUS_congress_prepare_demo')
    assert 'RUS_congress_demo_initialized' in model.flags
    assert {p:cs for p,cs in PARENTS.items()}=={
        'workers_opposition':['labour'],'new_theory':['labour'],'new_society':['labour'],
        'new_youth':['workers_opposition'],'literary_union':['workers_opposition'],
        'moderates':['workers_opposition'],'left_syndicalists':['workers_opposition'],
        'young_guard':['new_theory'],'anarcho_syndicalists':['new_theory'],
        'old_guard':['new_theory'],'right_syndicalists':['new_theory'],
        'sr_maximalists':['sr'],'sr_populists':['sr'],'sr_democrats':['sr'],
        'sr_citizens':['sr_populists','sr_democrats']}, 'Must match user diagram, including depth-2 and the civic join'
    assert len(ALL_PARTIES)==20 and set(LEADERS)=={row[0] for row in ALL_PARTIES}
    for key,_,_,count,_ in ALL_PARTIES: assert model.vars['RUS_congress_'+key+'_seats']==count
    default=[p[3] for p in PARTIES]; assert default==[240,160,120,200,80]
    check_partition(model,default)
    check_partition(model,default,True)
    colours=Counter(model.arrays['RUS_congress_seats'])
    for key in ['new_youth','literary_union','moderates','left_syndicalists','young_guard','anarcho_syndicalists','old_guard','right_syndicalists']:
        assert colours[FRAMES[key]]==10
    assert colours[FRAMES['sr_populists']]==colours[FRAMES['sr_democrats']]==25
    assert colours[FRAMES['sr_citizens']]==50
    assert len({r[0][0] for r in table_rows(True)})==len(table_rows(True))==20
    assert {depth for _,depth,_ in table_rows(True)}=={0,1,2}
    # A shared pool cannot overdraw a source or publish a negative contribution.
    for source,shared in [(-1,24),(51,76)]:
        before=list(model.arrays['RUS_congress_seats']);revision=model.vars['RUS_congress_revision']
        model.vars[CIVIC_SOURCES['sr_populists']]=source
        model.vars['RUS_congress_sr_citizens_seats']=shared
        model.call('RUS_congress_refresh_display')
        assert model.arrays['RUS_congress_seats']==before and model.vars['RUS_congress_revision']==revision
    check_partition(model,default)
    for distribution in [[800,0,0,0,0],[0,0,0,0,800],[160]*5,[1,399,0,1,399],[0,0,800,0,0]]:
        for expanded in [False,True]: check_partition(model,distribution,expanded)
        before=(dict(model.vars),list(model.arrays['RUS_congress_seats']))
        model.call('RUS_congress_prepare_demo')
        assert before==(model.vars,model.arrays['RUS_congress_seats']), 'Reopening must not reset saved seats'
    before=(dict(model.vars),list(model.arrays['RUS_congress_seats']))
    model.vars['RUS_congress_bolsheviks_seats']=-1
    model.vars['RUS_congress_labour_seats']=801
    model.call('RUS_congress_refresh_display')
    assert before[1]==model.arrays['RUS_congress_seats']
    assert before[0]['RUS_congress_revision']==model.vars['RUS_congress_revision']
    model.vars['RUS_congress_bolsheviks_seats']=0
    model.call('RUS_congress_refresh_display')
    assert before[1]==model.arrays['RUS_congress_seats'], 'Invalid total must not publish partial display'
    # No country modifiers, campaign currencies, event hooks or daily pulses.
    allowed={'RUS_congress_refresh_display','RUS_congress_prepare_demo'}
    assert set(effects)==allowed
    points=seats(); assert len(points)==len(set(points))==TOTAL
    for x,y in points:
        assert 20<=x<WIDTH-20 and 212+VERTICAL_SHIFT<=y<416+VERTICAL_SHIFT
    assert min(math.dist(a,b) for i,a in enumerate(points) for b in points[i+1:])>=6
    windows={n.value('name').strip('"'):n for n in load(ROOT/'interface/RUS_soviet_congress.gui')[0].v}
    assert set(windows)=={'RUS_congress_window_main','RUS_congress_window_children'}
    gui=windows['RUS_congress_window_children'];main_gui=windows['RUS_congress_window_main']
    assert int(main_gui.one('size').value('height'))==MAIN_HEIGHT==824
    assert int(gui.one('size').value('height'))==HEIGHT==1360
    icons=gui.children('iconType'); by_name={n.value('name').strip('"'):n for n in icons}
    scripted={n.k:n for n in load(ROOT/'common/scripted_guis/RUS_soviet_congress.txt')[0].v}
    sg=scripted['RUS_congress_gui_children'];main_sg=scripted['RUS_congress_gui_main']
    assert sg.value('context_type')=='decision_category' and sg.value('dirty')=='RUS.RUS_congress_revision'
    assert sg.value('window_name').strip('"')==gui.value('name').strip('"')
    props=sg.one('properties').v; assert len(props)==800
    frame_props=[n for n in props if n.one('frame') is not None]
    position_props={n.k:n for n in props if n.one('y') is not None}
    assert len(frame_props)==800 and not position_props
    for i,node in enumerate(frame_props):
        assert node.k=='RUS_congress_seat_'+str(i)
        assert node.k in by_name and node.value('frame')==f'RUS.RUS_congress_seats^{i}'
        pos=by_name[node.k].one('position'); assert (int(pos.value('x')),int(pos.value('y')))==points[i]
    cats={n.k:n for n in load(ROOT/'common/decisions/categories/RUS_soviet_congress.txt')}
    category=cats['RUS_congress_category']; entry=cats['RUS_congress_entry_category']
    expanded_category=cats['RUS_congress_children_category']
    assert category.value('scripted_gui')==main_sg.k and expanded_category.value('scripted_gui')==sg.k
    assert category.value('visible_when_empty')=='yes'
    assert category.one('allowed').value('original_tag')=='RUS' and category.one('visible').value('is_ai')=='no'
    decision=load(ROOT/'common/decisions/RUS_soviet_congress.txt')[0].v[0]
    assert decision.value('cost')=='0'
    assert decision.one('complete_effect').one('hidden_effect').value('RUS_congress_prepare_demo')=='yes'
    # Unlike a root GUI visible trigger, category visibility prevents construction
    # of any uninitialised window. Execute the real launcher before showing it.
    fresh=CongressModel(effects)
    assert not fresh.check(category.one('visible')) and not fresh.check(expanded_category.one('visible')) and fresh.check(entry.one('visible'))
    assert entry.one('scripted_gui') is None
    fresh.run(decision.one('complete_effect').one('hidden_effect').v)
    assert fresh.check(category.one('visible')) and not fresh.check(expanded_category.one('visible')) and not fresh.check(entry.one('visible'))
    assert len(fresh.arrays['RUS_congress_seats'])==800
    assert Counter(fresh.arrays['RUS_congress_seats'])=={1:240,2:160,3:120,4:200,5:80}
    # Read GUI bindings as an unscoped host: data must explicitly select RUS,
    # rather than accidentally passing because the fixture is already a country.
    for i,node in enumerate(frame_props):
        tag,reference=node.value('frame').split('.',1)
        name,index=reference.split('^')
        assert tag=='RUS' and fresh.arrays[name][int(index)]==next(frame for frame,cut in [(1,240),(2,400),(3,520),(4,720),(5,800)] if i<cut)
    # Execute the single actual button, including both native if/else paths.
    check_partition(model,default,False)
    saved={k:v for k,v in model.vars.items() if k.endswith('_seats')}
    for i in range(6):
        active_sg=sg if 'RUS_congress_show_children' in model.flags else main_sg
        model.run(active_sg.one('effects').one('RUS_congress_toggle_click').v)
        expanded=i%2==0
        assert ('RUS_congress_show_children' in model.flags)==expanded
        assert len(model.arrays['RUS_congress_seats'])==800
        assert any(frame>5 for frame in model.arrays['RUS_congress_seats'])==expanded
        assert model.check(category.one('visible'))==model.check(main_sg.one('visible'))==(not expanded)
        assert model.check(expanded_category.one('visible'))==model.check(sg.one('visible'))==expanded
        assert sum(model.check(c.one('visible')) for c in [category,expanded_category])==1
    assert saved=={k:v for k,v in model.vars.items() if k.endswith('_seats')}
    triggers=sg.one('triggers')
    # Never rely on container visibility: every child leaf owns its condition.
    assert not gui.children('containerWindowType')
    assert not main_gui.children('containerWindowType')
    assert len(main_sg.one('properties').v)==800
    assert not main_sg.one('triggers').v
    assert len(gui.children('buttonType'))==1
    widgets={n.value('name').strip('"'):n for n in gui.v if n.one('name') is not None}
    assert len(widgets)==sum(n.one('name') is not None for n in gui.v)
    assert not any('_legend_' in name for name in widgets)
    assert not {'RUS_congress_hierarchy_note','RUS_congress_footer'} & widgets.keys()
    children=[e for row,child,y in table_rows(True) for e in row_elements(row,child,y) if child]
    assert len(children)==60
    for e in children:
        trigger=triggers.one(e['name']+'_visible')
        assert trigger is not None and not model.check(trigger)
    for node in gui.children('instantTextBoxType'):
        if node.value('name').strip('"').startswith(('RUS_congress_count_','RUS_congress_share_')):
            assert node.value('alwaystransparent')=='no'
            assert node.value('pdx_tooltip').strip('"').startswith('RUS_congress_leaders_')
    portraits=leader_portraits()
    assert LEADERS['unions']==['RUS_mikhail_tomsky']
    assert LEADERS['bolsheviks']==['RUS_yakov_sverdlov']
    assert LEADERS['new_theory']==['RUS_daniil_sulimov','RUS_vladimir_levitsky']
    assert LEADERS['workers_opposition']==['RUS_grigory_zinovyev','RUS_lev_kamenev']
    for key in ['moderates','left_syndicalists']: assert LEADERS[key]==['RUS_lev_kamenev']
    for key in ['anarcho_syndicalists','old_guard','right_syndicalists']: assert LEADERS[key]==['RUS_vladimir_levitsky']
    assert LEADERS['sr_democrats']==['RUS_vladimir_rikhter','RUS_pitirim_sorokin']
    assert LEADERS['sr_citizens']==['RUS_pitirim_sorokin']
    assert set(portraits)=={c for cs in LEADERS.values() for c in cs}
    recruited={n.v for n in load(ROOT/'history/countries/RUS - Russia.txt') if n.k=='recruit_character'}
    assert set(portraits)<=recruited
    # Audit the actual installed Chinese font definitions, not a Pillow substitute.
    cn_fonts=load(ROOT.parent/'2946487287/interface/core_chinese.gfx')[0]
    font_names={n.value('name').strip('"') for n in cn_fonts.v}
    def walk(nodes):
        for n in nodes:
            yield n
            if isinstance(n.v,list): yield from walk(n.v)
    used_fonts={n.v.strip('"') for n in walk(gui.v) if n.k in {'font','buttonFont'}}
    assert used_fonts<=font_names,(used_fonts-font_names)
    assert not {'hoi_14mbs','Main_14'} & used_fonts
    assert {'hoi_18mbs','hoi_16mbs','hoi_24header'}<=used_fonts
    native_gui=(GAME/'interface/countrydecisionview.gui').read_text(encoding='utf-8-sig')
    slot_width=int(re.search(r'name\s*=\s*"decision_grid".*?size\s*=\s*{\s*width\s*=\s*(\d+)',native_gui,re.S)[1])
    assert WIDTH<=slot_width==502
    assert slot_width-CONTENT_RIGHT>=34, 'Reserve a real native clipping/scrollbar gutter'
    assert 12+HALL_SIZE[0]<=WIDTH-12
    cn_text=(ROOT/'localisation/simp_chinese/RUS_soviet_congress_l_simp_chinese.yml').read_text(encoding='utf-8-sig')
    cn_values={k:json.loads(v) for k,v in re.findall(r'^\s+([^ :]+):0 (".*")$',cn_text,re.M)}
    def resolve(key):
        return re.sub(r'\[\?RUS\.([^|\]]+)\|(\d+)\]',lambda m:f'{model.vars[m[1]]:.{m[2]}f}',cn_values[key])
    # Verify native advances and actual positions in the selected short/long root.
    for expanded in [False,True]:
        check_partition(model,default,expanded)
        active_gui=gui if expanded else main_gui
        active_sg=sg if expanded else main_sg
        active_widgets={n.value('name').strip('"'):n for n in active_gui.v if n.one('name') is not None}
        active_triggers=active_sg.one('triggers')
        active_height=int(active_gui.one('size').value('height'))
        rects=[]
        for row,child,y in table_rows(expanded):
            for e in row_elements(row,child,y):
                node=active_widgets[e['name']]
                assert bool(child)==(active_triggers.one(e['name']+'_visible') is not None)
                if child: assert model.check(active_triggers.one(e['name']+'_visible'))
                assert int(node.one('position').value('y'))==e['y']
                x=int(node.one('position').value('x')); assert x==e['x']
                assert 0<=x<x+e['w']<=WIDTH and 0<=e['y']<e['y']+e['h']<=active_height
                assert x+e['w']<=CONTENT_RIGHT
                rect=(x,e['y'],x+e['w'],e['y']+e['h'])
                assert all(rect[2]<=r[0] or rect[0]>=r[2] or rect[3]<=r[1] or rect[1]>=r[3] for r in rects), e['name']
                rects.append(rect)
                if e['kind']=='text':
                    assert node.value('font').strip('"')==e['font']
                    assert measure(e['font'],resolve(e['loc']))<=e['w'],e['name']
        assert len(rects)==(80 if expanded else 20)
        assert active_height-max(r[3] for r in rects)<=(48 if expanded else 32),'No oversized empty root below the table'
        assert len(active_widgets)==(len(widgets) if expanded else len(widgets)-60)
        for node in active_gui.children('instantTextBoxType'):
            name=node.value('name').strip('"'); vis=active_triggers.one(name+'_visible')
            if vis is not None and not model.check(vis): continue
            font=node.value('font').strip('"'); value=resolve(node.value('text').strip('"'))
            assert measure(font,value)<=int(node.value('maxWidth')),(name,measure(font,value))
            assert int(node.one('position').value('x'))+int(node.value('maxWidth'))<=WIDTH-12,name
            assert len(value.split('\n'))*max(f['height'] for f in font_data(font))<=int(node.value('maxHeight')),name
    assert measure('hoi_16mbs',cn_values['RUS_congress_toggle'])<=148
    # Counts/percentages stay within columns at both numeric extremes.
    for key,*_ in ALL_PARTIES:
        for count in [0,800]:
            model.vars['RUS_congress_'+key+'_seats']=count
            model.vars['RUS_congress_'+key+'_percent']=count/8
            assert measure('hoi_18mbs',resolve('RUS_congress_count_'+key))<=62
            assert measure('hoi_18mbs',resolve('RUS_congress_share_'+key))<=88
    gfx=load(ROOT/'interface/RUS_soviet_congress.gfx')[0]
    sprites={n.value('name').strip('"'):n for n in gfx.v}
    for window,height in [(main_gui,MAIN_HEIGHT),(gui,HEIGHT)]:
        panel=next(n for n in window.children('iconType') if n.value('name').strip('"')=='RUS_congress_panel')
        sprite=sprites[panel.value('spriteType').strip('"')]
        assert Image.open(ROOT/sprite.value('texturefile').strip('"')).size==(WIDTH,height)
    for window,script in [(main_gui,main_sg),(gui,sg)]:
        names={n.value('name').strip('"') for n in window.v if n.one('name') is not None}
        assert all(n.k in names for n in script.one('properties').v)
    textures=leader_textures()
    for char,texture in textures.items():
        sprite=sprites['GFX_'+portrait_texticon(char)]
        assert sprite.value('legacy_lazy_load')=='no'
        assert sprite.value('texturefile').strip('"')==texture
        assert any((root/texture).is_file() for root in [ROOT,ROOT.parent/'1521695605'])
    registry=json.loads((ROOT/'tools/design/RUS_future_domestic_ids.json').read_text(encoding='utf-8'))
    names={n['suffix']:n['name'] for n in registry.values()}
    assert all(names[suffix]==name for _,name,suffix,_,_ in PARTIES)
    for path,data in generated.items():
        if path.suffix=='.png':
            im=Image.open(BytesIO(data)); assert im.mode=='RGBA'
            assert im.size=={'seats':(120,6),'panel':(WIDTH,HEIGHT),'panel_main':(WIDTH,MAIN_HEIGHT),'congress_hall':HALL_SIZE}[path.stem]
        if path.suffix=='.yml':
            assert data.startswith(b'\xef\xbb\xbf')
            keys=re.findall(r'^\s+([^ :]+):0 ',data.decode('utf-8-sig'),re.M)
            assert len(keys)==len(set(keys))
            values={k:json.loads(v) for k,v in re.findall(r'^\s+([^ :]+):0 (".*")$',data.decode('utf-8-sig'),re.M)}
            for key,chars in LEADERS.items():
                tip=values['RUS_congress_leaders_'+key+'_tt']
                for char in chars:
                    assert '['+char+'.GetName]' in tip
                    assert '$'+char+'$' not in tip
                    assert '£'+portrait_texticon(char) in tip
                lines=tip.split('\n');previous=lines.index('§Y派系领导人§!')
                for char in chars:
                    at=next(i for i,line in enumerate(lines) if '£'+portrait_texticon(char) in line)
                    assert at-previous>=PORTRAIT_LINE_GAP
                    texture=textures[char]
                    path=next(r/texture for r in [ROOT,ROOT.parent/'1521695605'] if (r/texture).exists())
                    assert Image.open(path).height<=PORTRAIT_LINE_GAP*16
                    previous=at
                assert '[?RUS.RUS_congress_' in tip
            for key,_,_,count,_ in PARTIES:
                refs=re.findall(r'\[\?([^|\]]+)\|',values['RUS_congress_value_'+key])
                assert len(refs)==2
                resolved=[]
                for ref in refs:
                    tag,name=ref.split('.',1); assert tag=='RUS'
                    resolved.append(fresh.vars[name])
                assert resolved==[count,count/8]
    manifest=json.loads((ROOT/'tools/design/soviet_congress_hall_20261023/manifest.json').read_text(encoding='utf-8'))
    source=ROOT/manifest['source']; image=Image.open(source)
    assert hashlib.sha256(source.read_bytes()).hexdigest()==manifest['source_sha256']
    assert list(image.size)==manifest['source_dimensions'] and image.width/image.height==2
    print('PASS: 502px native slot/gutter; exclusive 824/1360px short/long windows, real toggle preserves seats and contracts root height; 20 diagram groups over three levels; shared civic seats counted once; actual font widths/row bounds/portrait spacing; 800-seat boundaries; RUS/BOM/assets.')


if __name__=='__main__':
    main()
