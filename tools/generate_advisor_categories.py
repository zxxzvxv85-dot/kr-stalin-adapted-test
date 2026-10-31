"""Russian faction filter row replacing the native row visually, with list visibility guards.
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


def guard_text(text):
    changes = []; seen = 0
    def visit(nodes, character=None):
        nonlocal seen
        for n in nodes:
            if not isinstance(n.v,list):continue
            owner = n.k if n.k.startswith('RUS_') and any(x.k in ('portraits','advisor') for x in n.v) else character
            # add_advisor_role can use explicit character or character scope.
            if n.k.startswith('RUS_') and n.k not in ('RUS_ui_advisor_matches_faction',):
                if any(x.k in ('add_advisor_role',) for x in n.v):owner=n.k
            if n.k in ('advisor','add_advisor_role'):
                who = n.value('character',owner)
                if who and who.startswith('RUS_'):
                    visible=n.one('visible')
                    if visible and visible.one(GUARD):
                        assert visible.one(GUARD).value('CHARACTER') == who
                    elif visible:
                        changes.append((visible.ib, '\n\t\t\t\t'+GUARD+' = { CHARACTER = '+who+' }\n\t\t\t'))
                    else:
                        changes.append((n.ib,'\n\t\t\tvisible = { '+GUARD+' = { CHARACTER = '+who+' } }\n\t\t'))
                    seen += 1
            visit(n.v,owner)
    visit(parse(text))
    for pos, insertion in sorted(changes,reverse=True):text=text[:pos]+insertion+text[pos:]
    lines=text.splitlines()
    for i,line in enumerate(lines):
        if GUARD in line:
            for j in range(max(0,i-1),min(len(lines),i+2)):lines[j]=lines[j].rstrip()
    return '\n'.join(lines)+'\n',seen


def guard_roles():
    """Append one UI-only AND condition; do not edit availability or effects."""
    outputs = {}; count = 0
    files = list((ROOT/'common/characters').glob('*.txt'))
    files += list((ROOT/'common/scripted_effects').glob('*.txt'))
    files += list((ROOT/'events').glob('*.txt'))
    for path in sorted(files):
        text,seen=guard_text(path.read_text(encoding='utf-8-sig'))
        count+=seen
        if seen:outputs[path.relative_to(ROOT).as_posix()]=text
    return outputs,count

def outputs():
    result,count=guard_roles()
    # Read identities as data; never mutate trait sprites or numeric effects.
    identity={row[0]:set() for row in CATEGORIES}
    for source in (KR,ROOT):
        for p in (source/'common/country_leader').glob('*.txt'):
            for root in load(p):
                if root.k!='leader_traits':continue
                for n in root.v:
                    for row in CATEGORIES:
                        # BOP helper traits can live on the country-leader role;
                        # only the adviser identity should determine this list.
                        if n.k.startswith(row[4]) and not n.k.endswith('_bop'):identity[row[0]].add(n.k)
    flags=' '.join('has_country_flag = '+FLAG+r[0] for r in CATEGORIES)
    triggers=['# UI selection only. Original advisor conditions remain in their own visible blocks.',
              'RUS_ui_use_faction_advisor_filters = { original_tag = RUS is_ai = no OR = { has_government = totalist has_government = communist has_government = syndicalist has_government = radical_socialist } }',
              GUARD+' = {',
              ' OR = { NOT = { RUS_ui_use_faction_advisor_filters = yes }',
              '  NOT = { OR = { '+flags+' } }']
    for row in CATEGORIES:
        assert identity[row[0]],row[0]
        members=' '.join('has_trait = '+key for key in sorted(identity[row[0]]))
        triggers += ['  AND = { has_country_flag = '+FLAG+row[0]+' $CHARACTER$ = { OR = { '+members+' } } }']
    triggers += [' }','}']
    result['common/scripted_triggers/RUS_advisor_faction_filter_triggers.txt']='\n'.join(triggers)+'\n'
    # Preserve native row for other countries. The Russian scripted row covers
    # it in place, following KR's double-button intelligence agency blocker.
    gui=(KR/'interface/command_character_view.gui').read_text(encoding='utf-8-sig')
    assert 'name = "command_character_view_filter_button"' not in gui
    result['interface/command_character_view.gui']='# Generated from installed KR; native single-row geometry preserved.\n'+gui
    ui=['guiTypes = {',' containerWindowType = {','  name = "RUS_advisor_faction_bar"',
        '  position = { x = 0 y = 43 }','  size = { width = 500 height = 50 }']
    for name in ('cover_lower','cover_upper'):
        ui += ['  buttonType = { name = "'+name+'" position = { x = 0 y = 0 } size = { x = 500 y = 50 } quadTextureSprite = "GFX_tiled_plain_bg" }']
    script=['scripted_gui = {',' RUS_advisor_faction_bar = {','  context_type = player_context',
            '  window_name = "RUS_advisor_faction_bar"','  parent_window_name = "command_character_view_window"',
            '  ai_enabled = { always = no }','  visible = { RUS_ui_use_faction_advisor_filters = yes }','  effects = {']
    clear=' '.join('clr_country_flag = '+FLAG+row[0] for row in CATEGORIES)
    script += ['   cover_lower_click = { }','   all_click = { '+clear+' }']
    selected=['   cover_upper_click_enabled = { always = no }','   selected_all_visible = { NOT = { OR = { '+flags+' } } }']
    entries=[('all',None)]+[(r[0],i) for i,r in enumerate(CATEGORIES,19)]
    for index,(key,frame) in enumerate(entries):
        x=23+45*index
        ui += ['  buttonType = { name = "'+key+'" position = { x = '+str(x)+' y = 3 } quadTextureSprite = "GFX_FOCUS_FILTER_ICON_BG" clicksound = click_checkbox pdx_tooltip = "RUS_advisor_filter_'+key+'"'+(' buttonText = "RUS_advisor_filter_all_short" buttonFont = "hoi_16mbs"' if frame is None else '')+' }',
               '  iconType = { name = "selected_'+key+'" position = { x = '+str(x+21)+' y = 24 } spriteType = "GFX_RUS_native_advisor_category_filter_button" frame = 2 centerposition = yes alwaystransparent = yes }']
        if frame is not None:
            ui += ['  iconType = { name = "icon_'+key+'" position = { x = '+str(x+20)+' y = 22 } spriteType = "GFX_RUS_advisor_faction_strip" frame = '+str(frame)+' centerposition = yes alwaystransparent = yes }']
            script += ['   '+key+'_click = { if = { limit = { has_country_flag = '+FLAG+key+' } '+clear+' } else = { '+clear+' set_country_flag = '+FLAG+key+' } }']
            selected += ['   selected_'+key+'_visible = { has_country_flag = '+FLAG+key+' }']
    ui += [' }','}'];script += ['  }','  triggers = {']+selected+['  }',' }','}']
    result['interface/RUS_advisor_faction_bar.gui']='\n'.join(ui)+'\n'
    result['common/scripted_guis/RUS_advisor_faction_bar.txt']='\n'.join(script)+'\n'
    result['interface/zz_RUS_advisor_categories.gfx']='spriteTypes = {\n SpriteType = { name = "GFX_RUS_advisor_faction_strip" texturefile = "'+ATLAS+'" noOfFrames = 27 }\n}\n'
    for language,col,all_text,short in [('simp_chinese',1,'显示全部顾问','全部'),('english',2,'Show all advisors','All'),('russian',3,'Все советники','Все')]:
        lines=[f'l_{language}:',f' RUS_advisor_filter_all: "{all_text}"',f' RUS_advisor_filter_all_short: "{short}"']
        lines += [f' RUS_advisor_filter_{row[0]}: "{row[col]}"' for row in CATEGORIES]
        result[f'localisation/replace/RUS_advisor_faction_filter_l_{language}.yml']='\n'.join(lines)+'\n'
    return result,count

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
        elif not p.exists() or p.read_text(encoding='utf-8-sig')!=text:stale.append(name)
    assets(args.assets)
    assert not stale,'Stale generated files: '+', '.join(stale)
    print(f'PASS: {count} advisor role guards; single replacement row, 9 faction buttons and All; '+('written' if args.write else 'read-only'))


if __name__=='__main__':main()
