"""Read-only by default; import the user's political/economic draw.io preview branch.

--write updates text outputs and packages the selected complete icons once.
--preview writes review sheets only. No import-time writes or upload-directory edits.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import html
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import sys

from hoi4_politics_blocks import load

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path('tools/design/RUS_future_domestic_layout.drawio')
CHOICES = Path('tools/design/RUS_future_domestic_icon_choices.tsv')
FOCUS = Path('common/national_focus/00_RUS_future_domestic_skeleton.txt')
PLAN_FOCUS = Path('common/national_focus/00_RUS_future_five_year_plan_skeleton.txt')
PLAN_TREE_ID = 'RUS_future_five_year_plan_tree'
REGISTRY = Path('tools/design/RUS_future_domestic_ids.json')
TREE = Path('common/national_focus/RUS focus (Russia).txt')
GFX = Path('interface/RUS_future_domestic_icons.gfx')
ASSET_DIR = Path('gfx/interface/goals/RUS_future_domestic')
BEGIN = '\t# BEGIN RUS future domestic preview'
END = '\t# END RUS future domestic preview'
PREFIX = 'RUS_future_domestic_'
ORIGIN = (90, 45)
PHASE_ORIGINS = {'domestic': ORIGIN, 'five_year_plan': (6, 1)}
LIBRARIES = {
    'CUSTOM': ROOT / 'tools/design/generated_focus_icons',
    'KX': ROOT.parent / '2142407679/gfx/interface/goals',
    'KR': ROOT.parent / '1521695605/gfx/interface/goals',
    'GWR': ROOT.parent / '3365515312/gfx/interface/goals',
    'RT56': ROOT.parent / '2129897125/gfx/interface/goals',
    'VANILLA': ROOT.parents[3] / 'common/Hearts of Iron IV/gfx/interface/goals',
}


def label(cell):
    value = html.unescape(cell.get('value', ''))
    value = re.sub(r'<br\s*/?>', ' ', value, flags=re.I)
    return re.sub(r'<[^>]+>', '', value).replace('\xa0', ' ').strip()


def read_layout():
    cells = ET.parse(ROOT / SOURCE).getroot().findall('.//mxCell')
    vertices = {c.get('id'): c for c in cells if c.get('vertex') == '1'}
    named = {k: c for k, c in vertices.items() if label(c) and not c.get('style', '').startswith('text;')}
    assert len(named) == 171, f'Expected 171 focuses, found {len(named)}'
    assert len({label(c) for c in named.values()}) == len(named)
    registry = json.loads((ROOT/REGISTRY).read_text(encoding='utf-8'))
    assert set(registry)==set(named), 'Stable ID registry must cover the entire drawing'
    assert len({v['suffix'] for v in registry.values()})==len(named)
    by_suffix = {v['suffix']: key for key, v in registry.items()}
    edges = set()
    hidden = set()
    mutex = set()
    recovered = []
    for cell in cells:
        if cell.get('edge') != '1':
            continue
        source, target = cell.get('source'), cell.get('target')
        free_ends = []
        for endpoint in ('source', 'target'):
            if cell.get(endpoint) is not None:
                continue
            point = cell.find(f"mxGeometry/mxPoint[@as='{endpoint}Point']")
            assert point is not None
            px, py = float(point.get('x')), float(point.get('y'))
            matches = []
            for k, vertex in named.items():
                g = vertex.find('mxGeometry')
                x, y, w, h = (float(g.get(p, '0')) for p in ('x', 'y', 'width', 'height'))
                boundary_y = y+h if endpoint == 'source' else y
                # The new free-ended line is one drawing pixel off both box centres.
                if abs(px - (x + w / 2)) < 1.1 and abs(py - boundary_y) < 1.1:
                    matches.append(k)
            assert len(matches) == 1, f'Ambiguous free-ended edge {cell.get("id")}: {matches}'
            if endpoint == 'source':
                source = matches[0]
            else:
                target = matches[0]
            free_ends.append(endpoint)
        assert source in vertices and target in vertices
        if free_ends:
            recovered.append((cell.get('id'), source, target, free_ends))
        if 'startArrow=classic' in cell.get('style', ''):
            if source in named and target in named:
                mutex.add(tuple(sorted((source, target))))
            continue
        if 'dashed=1' in cell.get('style', ''):
            assert source in named and target in named, 'Hidden prerequisite must join named boxes'
            hidden.add((source, target))
        else:
            edges.add((source, target))
    outgoing = defaultdict(set)
    for source, target in edges:
        outgoing[source].add(target)
    effective = set()
    contracted = []
    for source in named:
        todo = list(outgoing[source])
        seen = set()
        while todo:
            target = todo.pop()
            assert target != source, 'Layout cycle through unnamed nodes'
            if target in seen:
                continue
            seen.add(target)
            if target in named:
                effective.add((source, target))
                if (source, target) not in edges:
                    contracted.append((source, target))
            else:
                todo.extend(outgoing[target])
    minima = {phase: (min(float(c.find('mxGeometry').get('x')) for k,c in named.items() if registry[k]['phase']==phase),
                      min(float(c.find('mxGeometry').get('y')) for k,c in named.items() if registry[k]['phase']==phase))
              for phase in PHASE_ORIGINS}
    nodes = []
    for key, cell in named.items():
        g = cell.find('mxGeometry')
        # 160 draw.io units between adjacent same-row focuses = 2 HOI4 x units.
        # 80 is the half-column step used by staggered parent/child positions.
        entry = registry[key];phase = entry['phase'];minx,miny = minima[phase]
        x = PHASE_ORIGINS[phase][0] + round((float(g.get('x')) - minx) / 80)
        y = PHASE_ORIGINS[phase][1] + round((float(g.get('y')) - miny) / 120)
        suffix = entry['suffix']
        name = label(cell)
        if suffix == '638':
            assert name == '第一个五年计划（前置：左边三选一+激发阶级意识）'
            name = '第一个五年计划'
        if suffix == '424':
            assert name == '为发展奠基 （需要完成成立执行委员会）'
            name = '为发展奠基'
            # The user's inline annotation is an additional mandatory gate,
            # without an extra visible connector across the layout.
            hidden.add((by_suffix['428'], key))
        assert name==entry['name'], f'Changed name needs a registry update: {key}'
        nodes.append({'cell_id': key, 'suffix': suffix, 'phase':phase,
                      'id': PREFIX + suffix, 'name': name, 'x': x, 'y': y})
    nodes.sort(key=lambda n: (n['phase'],n['y'], n['x'], n['id']))
    by_cell = {n['cell_id']: n for n in nodes}
    edge_ids = sorted((by_cell[s]['id'], by_cell[t]['id']) for s, t in effective)
    hidden_ids = sorted((by_cell[s]['id'], by_cell[t]['id']) for s, t in hidden)
    phase_by_id = {n['id']:n['phase'] for n in nodes}
    assert all(phase_by_id[s]==phase_by_id[t] for s,t in edge_ids+hidden_ids), 'Cross-stage edges require explicit handover design'
    mutex_ids = sorted(tuple(sorted((by_cell[s]['id'], by_cell[t]['id']))) for s, t in mutex)
    # User retained three mutually exclusive economic approaches, including the outer pair.
    mutex_ids = sorted(set(mutex_ids) | {tuple(sorted((PREFIX+'163', PREFIX+'169')))})
    # Validate a DAG, including ancestors reached through blank placeholders.
    parents = defaultdict(list)
    for source, target in edge_ids + hidden_ids:
        parents[target].append(source)
    def visit(key, trail):
        assert key not in trail, f'Prerequisite cycle: {trail} -> {key}'
        for parent in parents[key]:
            visit(parent, trail | {key})
    for node in nodes:
        visit(node['id'], set())
    for i, left in enumerate(nodes):
        for right in nodes[i+1:]:
            assert left['phase']!=right['phase'] or not (abs(left['x']-right['x'])*96 < 174 and abs(left['y']-right['y'])*130 < 128), f'Node overlap {left} / {right}'
    meta = {'focus_count': len(nodes), 'edge_count': len(edge_ids), 'mutex_pairs': mutex_ids,
            'hidden_required_edges': hidden_ids,
            'phase_counts':dict(Counter(n['phase'] for n in nodes)),
            'planned_stage_entry': {'any_completed': [PREFIX+s for s in ['177','182','183']],
                                    'all_completed': [PREFIX+'237'], 'implemented':False},
            'recovered_free_end_edges': recovered, 'contracted_blank_paths': contracted,
            'ignored_blank_vertices': sum(not label(c) for c in vertices.values()),
            'ignored_legends': [label(c) for c in vertices.values() if c.get('style','').startswith('text;')],
            'layout_scale': {'drawio_x_per_focus_unit': 80, 'drawio_y_per_focus_unit': 120,
                             'minimum_same_row_focus_gap': 2}}
    return nodes, edge_ids, mutex_ids, meta


def choices(nodes):
    rows = {}
    for line in (ROOT / CHOICES).read_text(encoding='utf-8').splitlines():
        if not line or line.startswith('#'):
            continue
        columns = line.split('\t')
        suffix, library, filename = columns[:3]
        assert suffix not in rows
        source = LIBRARIES[library] / filename
        assert source.is_file(), source
        rows[suffix] = {'library': library, 'filename': filename, 'path': source,
                        'sprite': columns[3] if len(columns)>3 else '',
                        'original_kr_focus': columns[4] if len(columns)>4 else ''}
    assert set(rows) == {n['suffix'] for n in nodes}, 'Icon mapping must exactly cover named focuses'
    return rows


def existing_bounds():
    tree = next(n for n in load(ROOT / TREE) if n.k == 'focus_tree')
    focuses = {n.value('id'): n for n in tree.children('focus')}
    shared = {n.value('id'): n for p in (ROOT/'common/national_focus').glob('*.txt')
              for n in load(p) if n.k == 'shared_focus'}
    todo = [n.v for n in tree.children('shared_focus') if not n.v.startswith(PREFIX)]
    seen = set()
    while todo:
        key = todo.pop()
        if key in seen:
            continue
        seen.add(key)
        focuses[key] = shared[key]
        todo.extend(n.v for n in shared[key].children('shared_focus'))
    cache = {}
    def locate(key):
        if key in cache:
            return cache[key]
        node = focuses[key]
        anchor = node.value('relative_position_id')
        bounds = locate(anchor) if anchor else (0, 0, 0, 0)
        x, y = int(node.value('x', 0)), int(node.value('y', 0))
        offsets = [(int(n.value('x', 0)), int(n.value('y', 0))) for n in node.children('offset')]
        # Conservative envelope: include all positive/negative route shifts,
        # including mutually incompatible ones. Thus safe for every actual route.
        cache[key] = (bounds[0]+x+sum(min(0,dx) for dx,dy in offsets),
                      bounds[1]+x+sum(max(0,dx) for dx,dy in offsets),
                      bounds[2]+y+sum(min(0,dy) for dx,dy in offsets),
                      bounds[3]+y+sum(max(0,dy) for dx,dy in offsets))
        return cache[key]
    for key in focuses:
        locate(key)
    return {'count': len(cache), 'min_x': min(v[0] for v in cache.values()),
            'max_x': max(v[1] for v in cache.values()), 'min_y': min(v[2] for v in cache.values()),
            'max_y': max(v[3] for v in cache.values())}


def render_outputs():
    nodes, edges, mutex, meta = read_layout()
    selected = choices(nodes)
    bounds = existing_bounds()
    assert ORIGIN[0] >= bounds['max_x'] + 6, bounds
    assert ORIGIN[1] >= bounds['max_y'] + 4, bounds
    meta['existing_conservative_bounds'] = bounds
    def bounds_for(phase):
        group=[n for n in nodes if n['phase']==phase]
        return {'min_x':min(n['x'] for n in group),'max_x':max(n['x'] for n in group),
                'min_y':min(n['y'] for n in group),'max_y':max(n['y'] for n in group)}
    meta['new_bounds'] = bounds_for('domestic')
    meta['five_year_plan_bounds'] = bounds_for('five_year_plan')
    parents, exclusive = defaultdict(list), defaultdict(list)
    for s, t in edges:
        parents[t].append(s)
    for left, right in mutex:
        exclusive[left].append(right)
        exclusive[right].append(left)
    texts = {phase: ['# Generated by tools/generate_future_domestic_focus.py --write',
            '# Solid merges are OR; dotted edges are additional hidden mandatory requirements.',
            '# Preview only: rewards and duration balancing have not been implemented.', ''] for phase in PHASE_ORIGINS}
    for node in nodes:
        key = node['id']
        text = texts[node['phase']]
        icon = selected[node['suffix']]['sprite'] or 'GFX_goal_'+key
        text += ['# '+node['name'], 'shared_focus = {', '\tid = '+key, '\ticon = '+icon,
                 '\tcost = 7', f'\tx = {node["x"]}', f'\ty = {node["y"]}',
                 '\tavailable = {']
        text += ['\t\thas_completed_focus = '+s for s,t in meta['hidden_required_edges'] if t==key]
        text += ['\t\tcustom_trigger_tooltip = {',
                 '\t\t\ttooltip = RUS_future_domestic_preview_only_tt', '\t\t\talways = no', '\t\t}', '\t}']
        if node['phase']=='domestic':
            text += ['\tallow_branch = { NOT = { has_government = national_populist } }']
        if parents[key]:
            text += ['\tprerequisite = { '+ ' '.join('focus = '+p for p in parents[key])+' }']
        for other in exclusive[key]:
            text += ['\tmutually_exclusive = { focus = '+other+' }']
        text += ['\tcompletion_reward = { }', '\tai_will_do = { factor = 0 }', '}', '']
    refs = '\n'.join([BEGIN]+['\tshared_focus = '+n['id'] for n in nodes if n['phase']=='domestic']+[END])
    texts['five_year_plan'] += ['# Independent phase preview: no automatic selection or switching event.',
        '# Planned handover eligibility: one economic endpoint AND class consciousness.',
        '# Persistent route flags and the switch will be wired when the activation moment is designed.',
        'focus_tree = {', '\tid = '+PLAN_TREE_ID, '\tcountry = { factor = 0 }', '\tdefault = no',
        '\tcontinuous_focus_position = { x = 50 y = 1000 }']
    texts['five_year_plan'] += ['\tshared_focus = '+n['id'] for n in nodes if n['phase']=='five_year_plan']
    texts['five_year_plan'] += ['}', '']
    raw = (ROOT / TREE).read_bytes()
    original = raw.decode('utf-8-sig')
    normal = original.replace('\r\n', '\n')
    if BEGIN in normal:
        normal, count = re.subn(re.escape(BEGIN)+'.*?'+re.escape(END), lambda _: refs, normal, count=1, flags=re.S)
        assert count == 1
    else:
        assert normal.count('\tdefault = no\n') == 1
        normal = normal.replace('\tdefault = no\n', '\tdefault = no\n\n'+refs+'\n', 1)
    if raw.count(b'\r\n') > raw.count(b'\n')/2:
        normal = normal.replace('\n', '\r\n')
    tree_bytes = (b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b'') + normal.encode('utf-8')
    template = (ROOT/'interface/RUS_future_foreign_victory_icon.gfx').read_text(encoding='utf-8-sig')
    inner = template[template.index('{')+1:template.rfind('}')]
    gfx = 'spriteTypes = {\n' + ''.join(inner.replace('RUS_future_foreign_005', n['id'])
             .replace('goals/RUS_future_foreign/', 'goals/RUS_future_domestic/') for n in nodes
             if not selected[n['suffix']]['sprite']) + '}\n'
    result = {FOCUS: '\n'.join(texts['domestic']).encode('utf-8'),
              PLAN_FOCUS: '\n'.join(texts['five_year_plan']).encode('utf-8'), TREE: tree_bytes, GFX: gfx.encode('utf-8')}
    tips = {'simp_chinese': '该国策尚处于设计阶段，暂不可选取。',
            'english': 'This focus is a design preview and cannot yet be selected.',
            'russian': 'Этот фокус находится на стадии проектирования и пока недоступен.'}
    for lang in tips:
        rows = ['l_'+lang+':', ' RUS_future_domestic_preview_only_tt:0 '+json.dumps(tips[lang], ensure_ascii=False)]
        for n in nodes:
            # Keep source titles on other language UIs until translations are authored.
            rows += [' '+n['id']+':0 '+json.dumps(n['name'], ensure_ascii=False), ' '+n['id']+'_desc:0 ""']
        result[Path(f'localisation/{lang}/RUS_future_domestic_l_{lang}.yml')] = ('\n'.join(rows)+'\n').encode('utf-8-sig')
    return result, nodes, selected, meta


def package_icon(path):
    from PIL import Image, ImageOps
    image = Image.open(path).convert('RGBA')
    image = ImageOps.contain(image, (100, 100), Image.Resampling.LANCZOS) if max(image.size)>100 else image
    canvas = Image.new('RGBA', (100,100))
    canvas.alpha_composite(image, ((100-image.width)//2, (100-image.height)//2))
    assert canvas.getchannel('A').getextrema() == (0,255), path
    return canvas


def make_preview(nodes, selected, target):
    from PIL import Image, ImageDraw, ImageFont
    target.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 16)
    small = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 13)
    for page, offset in enumerate(range(0, len(nodes), 48), 1):
        subset = nodes[offset:offset+48]
        sheet = Image.new('RGB', (8*180, 6*160), '#22262a')
        draw = ImageDraw.Draw(sheet)
        for i, n in enumerate(subset):
            x,y = (i%8)*180, (i//8)*160
            icon = package_icon(selected[n['suffix']]['path'])
            sheet.paste(icon, (x+40,y+3), icon)
            name = n['name']
            lines = [name[j:j+10] for j in range(0,len(name),10)]
            for row,line in enumerate(lines[:2]):
                draw.text((x+5,y+105+row*19),line,font=font,fill='white')
            draw.text((x+5,y+145), n['suffix']+' / '+selected[n['suffix']]['library'],font=small,fill='#b6a783')
        sheet.save(target/f'icons-{page}.png')
    make_tree_preview([n for n in nodes if n['phase']=='domestic'], selected, target, 'domestic')
    make_tree_preview([n for n in nodes if n['phase']=='five_year_plan'], selected, target/'一五计划阶段', 'five_year_plan')


def make_tree_preview(nodes, selected, target, phase):
    import base64
    import io
    from PIL import Image, ImageDraw, ImageFont
    _, edges, mutex, meta = read_layout()
    target.mkdir(parents=True,exist_ok=True)
    ids={n['id'] for n in nodes};origin=PHASE_ORIGINS[phase]
    edges=[(s,t) for s,t in edges if s in ids and t in ids]
    mutex=[(s,t) for s,t in mutex if s in ids and t in ids]
    positions = {n['id']: ((n['x']-origin[0])*96+105, (n['y']-origin[1])*130+65) for n in nodes}
    width = max(p[0] for p in positions.values())+110
    height = max(p[1] for p in positions.values())+95
    by_id = {n['id']:n for n in nodes}
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
           '<rect width="100%" height="100%" fill="#20252a"/>']
    # Horizontal-first elbow links preserve the draw.io prerequisite graph.
    for source, dest in edges:
        x1,y1 = positions[source]; x2,y2 = positions[dest]
        mid = (y1+y2)/2+20
        svg.append(f'<path d="M{x1},{y1+65} V{mid} H{x2} V{y2-48}" fill="none" stroke="#818b78" stroke-width="2"/>')
    for left,right in mutex:
        (x1,y1),(x2,y2) = sorted((positions[left],positions[right]))
        svg.append(f'<path d="M{x1+55},{y1} L{x2-55},{y2}" fill="none" stroke="#b95550" stroke-width="3" stroke-dasharray="8 6"/>')
    for node in nodes:
        x,y = positions[node['id']]
        blob=io.BytesIO(); package_icon(selected[node['suffix']]['path']).save(blob,format='PNG')
        src = base64.b64encode(blob.getvalue()).decode('ascii')
        required = [by_id[s]['name'] for s,t in meta['hidden_required_edges'] if t==node['id']]
        note = ' | 额外必需：'+'、'.join(required) if required else ''
        svg += [f'<g><title>{html.escape(node["name"]+note)} | {node["id"]}</title>',
                f'<image href="data:image/png;base64,{src}" x="{x-50}" y="{y-50}" width="100" height="100"/>',
                f'<rect x="{x-82}" y="{y+48}" width="164" height="36" rx="8" fill="#343b3b" stroke="#8f8869"/>']
        name = node['name']; lines=[name[i:i+11] for i in range(0,len(name),11)]
        for i,line in enumerate(lines):
            svg.append(f'<text x="{x}" y="{y+63+i*15-(7 if len(lines)>1 else 0)}" fill="#eee8d8" font-family="Microsoft YaHei,sans-serif" font-size="13" text-anchor="middle">{html.escape(line)}</text>')
        svg.append('</g>')
    svg.append('</svg>')
    svg_text=''.join(svg)
    header='''<!doctype html><meta charset="utf-8"><title>新政治经济国策树 · 布局预览</title>
<style>body{margin:0;background:#20252a;color:#eee8d8;font:15px 'Microsoft YaHei',sans-serif}header{position:sticky;top:0;background:#15191d;padding:14px;z-index:2}button,input{margin-left:14px}#viewport{overflow:auto;height:calc(100vh - 60px)}svg{display:block}</style>
<header>新政治经济国策树 | FOCUS_COUNT项 | 灰绿线：前置（任一）；红虚线：互斥 | PHASE_NOTE | 布局示意
<button onclick="fit()">总览</button><input id="zoom" type="range" min="10" max="110" value="25"><span id="pct"></span></header><div id="viewport">'''
    script=f'''</div><script>const s=document.querySelector('svg'),z=document.getElementById('zoom');function scale(v){{s.style.width=({width}*v/100)+'px';s.style.height=({height}*v/100)+'px';document.getElementById('pct').textContent=Math.round(v)+'%';}}z.oninput=()=>scale(+z.value);function fit(){{const v=Math.max(10,100*(innerWidth-20)/{width});z.value=v;scale(v)}}fit();</script>'''
    title='一五计划独立阶段' if phase=='five_year_plan' else '新政治经济国策树'
    note='尚未设置阶段切换时机' if phase=='five_year_plan' else '额外隐藏前置见悬浮提示；一五计划已拆为独立阶段'
    (target/'国策树布局预览.html').write_text(header.replace('FOCUS_COUNT',str(len(nodes))).replace('新政治经济国策树',title).replace('PHASE_NOTE',note)+svg_text+script,encoding='utf-8')
    # Native-sized local sections for image review, retaining all icons/labels.
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',13)
    for col in range((width+2303)//2304):
        left=col*2304
        board=Image.new('RGB',(min(2304,width-left),height),'#20252a');d=ImageDraw.Draw(board)
        for source,dest in edges:
            x1,y1=positions[source];x2,y2=positions[dest];mid=(y1+y2)/2+20
            d.line([(x1-left,y1+65),(x1-left,mid),(x2-left,mid),(x2-left,y2-48)],fill='#818b78',width=2)
        for a,b in mutex:
            (x1,y1),(x2,y2)=sorted((positions[a],positions[b]))
            assert y1==y2, 'Native preview expects same-row exclusions'
            for x in range(x1+55,x2-55,14):
                d.line([(x-left,y1),(min(x+8,x2-55)-left,y2)],fill='#b95550',width=3)
        for node in nodes:
            x,y=positions[node['id']];x-=left
            if not -100<x<2404:continue
            icon=package_icon(selected[node['suffix']]['path']);board.paste(icon,(x-50,y-50),icon)
            d.rounded_rectangle((x-82,y+48,x+82,y+84),radius=7,fill='#343b3b',outline='#8f8869')
            lines=[node['name'][i:i+11] for i in range(0,len(node['name']),11)]
            for i,line in enumerate(lines):d.text((x,y+64+i*15-(7 if len(lines)>1 else 0)),line,anchor='mm',font=font,fill='#eee8d8')
        board.save(target/f'tree-section-{col+1}.png')
    for old in target.glob('tree-section-*.png'):
        if int(old.stem.rsplit('-',1)[-1])>(width+2303)//2304:
            old.unlink()


def main():
    if hasattr(sys.stdout,'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--write', action='store_true')
    p.add_argument('--check', action='store_true')
    p.add_argument('--preview', action='store_true')
    args = p.parse_args()
    outputs, nodes, selected, meta = render_outputs()
    if args.preview:
        make_preview(nodes, selected, ROOT/'output/future_domestic_focus_20261016')
        print(json.dumps(meta, ensure_ascii=False, indent=2))
        return 0
    if args.write:
        for path,data in outputs.items():
            (ROOT/path).parent.mkdir(parents=True, exist_ok=True)
            (ROOT/path).write_bytes(data)
        (ROOT/ASSET_DIR).mkdir(parents=True, exist_ok=True)
        sources = []
        for node in nodes:
            s = selected[node['suffix']]
            dest = ASSET_DIR/(node['id']+'.png')
            package_icon(s['path']).save(ROOT/dest)
            sources.append({'id':node['id'],'name':node['name'],'phase':node['phase'],'library':s['library'],
                'source':str(s['path']),'source_sha256':hashlib.sha256(s['path'].read_bytes()).hexdigest(),
                'sprite':s['sprite'] or 'GFX_goal_'+node['id'], 'original_kr_focus':s['original_kr_focus'],
                'destination':dest.as_posix(),'destination_sha256':hashlib.sha256((ROOT/dest).read_bytes()).hexdigest()})
        meta['sources'] = sources
        (ROOT/'tools/design/RUS_future_domestic_sources.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(f'Wrote {len(nodes)} preview focuses, {len(outputs)} text files and {len(nodes)} complete icons.')
        return 0
    errors = []
    for path,data in outputs.items():
        if not (ROOT/path).is_file() or (ROOT/path).read_bytes()!=data:
            errors.append(str(path))
    manifest = ROOT/'tools/design/RUS_future_domestic_sources.json'
    if not manifest.is_file():
        errors.append(str(manifest))
    else:
        provenance = json.loads(manifest.read_text(encoding='utf-8'))
        assert len(provenance['sources']) == len(nodes)
        for item in provenance['sources']:
            dest = ROOT/item['destination']
            if not dest.is_file() or hashlib.sha256(dest.read_bytes()).hexdigest()!=item['destination_sha256']:
                errors.append(item['destination'])
            current = selected[item['id'].removeprefix(PREFIX)]
            if current['library']!=item['library'] or str(current['path'])!=item['source'] or hashlib.sha256(current['path'].read_bytes()).hexdigest()!=item['source_sha256']:
                errors.append('source changed: '+item['id'])
        # Shared original artwork is intentional: the user explicitly allows KR reuse.
    if errors:
        print('STALE: '+', '.join(errors)); return 1
    print(f'PASS: {meta["phase_counts"]["domestic"]} domestic + {meta["phase_counts"]["five_year_plan"]} independent stage focuses; {len(meta["mutex_pairs"])} exclusions; no phase switch wired; no overlap; rewards empty; text/assets current.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
