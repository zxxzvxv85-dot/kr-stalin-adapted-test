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
TREE = Path('common/national_focus/RUS focus (Russia).txt')
GFX = Path('interface/RUS_future_domestic_icons.gfx')
ASSET_DIR = Path('gfx/interface/goals/RUS_future_domestic')
BEGIN = '\t# BEGIN RUS future domestic preview'
END = '\t# END RUS future domestic preview'
PREFIX = 'RUS_future_domestic_'
ORIGIN = (90, 45)
LIBRARIES = {
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
    assert len(named) == 141, f'Expected 141 focuses, found {len(named)}'
    assert len({label(c) for c in named.values()}) == len(named)
    edges = set()
    mutex = set()
    recovered = []
    for cell in cells:
        if cell.get('edge') != '1':
            continue
        source, target = cell.get('source'), cell.get('target')
        if source is None:
            point = cell.find("mxGeometry/mxPoint[@as='sourcePoint']")
            assert point is not None
            px, py = float(point.get('x')), float(point.get('y'))
            matches = []
            for k, vertex in named.items():
                g = vertex.find('mxGeometry')
                x, y, w, h = (float(g.get(p, '0')) for p in ('x', 'y', 'width', 'height'))
                if abs(px - (x + w / 2)) < 0.1 and abs(py - (y + h)) < 0.1:
                    matches.append(k)
            assert len(matches) == 1, f'Ambiguous free-ended edge {cell.get("id")}: {matches}'
            source = matches[0]
            recovered.append((cell.get('id'), source, target))
        assert source in vertices and target in vertices
        if 'startArrow=classic' in cell.get('style', ''):
            if source in named and target in named:
                mutex.add(tuple(sorted((source, target))))
            continue
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
    minx = min(float(c.find('mxGeometry').get('x')) for c in named.values())
    miny = min(float(c.find('mxGeometry').get('y')) for c in named.values())
    nodes = []
    for key, cell in named.items():
        g = cell.find('mxGeometry')
        # Source row/column jitter is snapped to its 80 x 120 draw.io grid.
        x = ORIGIN[0] + round((float(g.get('x')) - minx) / 80) * 2
        y = ORIGIN[1] + round((float(g.get('y')) - miny) / 120)
        nodes.append({'cell_id': key, 'suffix': key.rsplit('-', 1)[-1],
                      'id': PREFIX + key.rsplit('-', 1)[-1], 'name': label(cell), 'x': x, 'y': y})
    nodes.sort(key=lambda n: (n['y'], n['x'], n['id']))
    by_cell = {n['cell_id']: n for n in nodes}
    edge_ids = sorted((by_cell[s]['id'], by_cell[t]['id']) for s, t in effective)
    mutex_ids = sorted(tuple(sorted((by_cell[s]['id'], by_cell[t]['id']))) for s, t in mutex)
    # Validate a DAG, including ancestors reached through blank placeholders.
    parents = defaultdict(list)
    for source, target in edge_ids:
        parents[target].append(source)
    def visit(key, trail):
        assert key not in trail, f'Prerequisite cycle: {trail} -> {key}'
        for parent in parents[key]:
            visit(parent, trail | {key})
    for node in nodes:
        visit(node['id'], set())
    for i, left in enumerate(nodes):
        for right in nodes[i+1:]:
            assert not (abs(left['x']-right['x'])*96 < 174 and abs(left['y']-right['y'])*130 < 128), f'Node overlap {left} / {right}'
    meta = {'focus_count': len(nodes), 'edge_count': len(edge_ids), 'mutex_pairs': mutex_ids,
            'recovered_free_end_edges': recovered, 'contracted_blank_paths': contracted,
            'ignored_blank_vertices': len(vertices)-len(named)-1, 'ignored_legend': '图案代表提交法案'}
    return nodes, edge_ids, mutex_ids, meta


def choices(nodes):
    rows = {}
    for line in (ROOT / CHOICES).read_text(encoding='utf-8').splitlines():
        if not line or line.startswith('#'):
            continue
        suffix, library, filename = line.split('\t')
        assert suffix not in rows
        source = LIBRARIES[library] / filename
        assert source.is_file(), source
        rows[suffix] = {'library': library, 'filename': filename, 'path': source}
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
    meta['new_bounds'] = {'min_x': min(n['x'] for n in nodes), 'max_x': max(n['x'] for n in nodes),
                          'min_y': min(n['y'] for n in nodes), 'max_y': max(n['y'] for n in nodes)}
    parents, exclusive = defaultdict(list), defaultdict(list)
    for s, t in edges:
        parents[t].append(s)
    for left, right in mutex:
        exclusive[left].append(right)
        exclusive[right].append(left)
    text = ['# Generated by tools/generate_future_domestic_focus.py --write',
            '# Draw.io preview branch: all merges are OR, explicit two-headed arrows are exclusive.',
            '# Preview only: rewards and duration balancing have not been implemented.', '']
    for node in nodes:
        key = node['id']
        text += ['# '+node['name'], 'shared_focus = {', '\tid = '+key, '\ticon = GFX_goal_'+key,
                 '\tcost = 7', f'\tx = {node["x"]}', f'\ty = {node["y"]}',
                 '\tavailable = {', '\t\tcustom_trigger_tooltip = {',
                 '\t\t\ttooltip = RUS_future_domestic_preview_only_tt', '\t\t\talways = no', '\t\t}', '\t}']
        if parents[key]:
            text += ['\tprerequisite = { '+ ' '.join('focus = '+p for p in parents[key])+' }']
        for other in exclusive[key]:
            text += ['\tmutually_exclusive = { focus = '+other+' }']
        text += ['\tcompletion_reward = { }', '\tai_will_do = { factor = 0 }', '}', '']
    refs = '\n'.join([BEGIN]+['\tshared_focus = '+n['id'] for n in nodes]+[END])
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
             .replace('goals/RUS_future_foreign/', 'goals/RUS_future_domestic/') for n in nodes) + '}\n'
    result = {FOCUS: '\n'.join(text).encode('utf-8'), TREE: tree_bytes, GFX: gfx.encode('utf-8')}
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
    make_tree_preview(nodes, selected, target)


def make_tree_preview(nodes, selected, target):
    import base64
    import io
    from PIL import Image, ImageDraw, ImageFont
    _, edges, mutex, meta = read_layout()
    positions = {n['id']: ((n['x']-ORIGIN[0])*96+105, (n['y']-ORIGIN[1])*130+65) for n in nodes}
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
        x1,y1 = positions[left];x2,y2=positions[right]
        svg.append(f'<path d="M{x1+55},{y1} L{x2-55},{y2}" fill="none" stroke="#b95550" stroke-width="3" stroke-dasharray="8 6"/>')
    for node in nodes:
        x,y = positions[node['id']]
        blob=io.BytesIO(); package_icon(selected[node['suffix']]['path']).save(blob,format='PNG')
        src = base64.b64encode(blob.getvalue()).decode('ascii')
        svg += [f'<g><title>{html.escape(node["name"])} | {node["id"]}</title>',
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
<header>新政治经济国策树 | 141项 | 灰绿线：前置（任一）；红虚线：互斥 | 布局示意，非游戏截图
<button onclick="fit()">总览</button><input id="zoom" type="range" min="10" max="110" value="25"><span id="pct"></span></header><div id="viewport">'''
    script=f'''</div><script>const s=document.querySelector('svg'),z=document.getElementById('zoom');function scale(v){{s.style.width=({width}*v/100)+'px';s.style.height=({height}*v/100)+'px';document.getElementById('pct').textContent=Math.round(v)+'%';}}z.oninput=()=>scale(+z.value);function fit(){{const v=Math.max(10,100*(innerWidth-20)/{width});z.value=v;scale(v)}}fit();</script>'''
    (target/'国策树布局预览.html').write_text(header+svg_text+script,encoding='utf-8')
    # Native-sized local sections for image review, retaining all icons/labels.
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',13)
    for col in range(6):
        left=col*2304
        board=Image.new('RGB',(2304,height),'#20252a');d=ImageDraw.Draw(board)
        for source,dest in edges:
            x1,y1=positions[source];x2,y2=positions[dest];mid=(y1+y2)/2+20
            d.line([(x1-left,y1+65),(x1-left,mid),(x2-left,mid),(x2-left,y2-48)],fill='#818b78',width=2)
        for node in nodes:
            x,y=positions[node['id']];x-=left
            if not -100<x<2404:continue
            icon=package_icon(selected[node['suffix']]['path']);board.paste(icon,(x-50,y-50),icon)
            d.rounded_rectangle((x-82,y+48,x+82,y+84),radius=7,fill='#343b3b',outline='#8f8869')
            lines=[node['name'][i:i+11] for i in range(0,len(node['name']),11)]
            for i,line in enumerate(lines):d.text((x,y+64+i*15-(7 if len(lines)>1 else 0)),line,anchor='mm',font=font,fill='#eee8d8')
        board.save(target/f'tree-section-{col+1}.png')


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
            sources.append({'id':node['id'],'name':node['name'],'library':s['library'],
                'source':str(s['path']),'source_sha256':hashlib.sha256(s['path'].read_bytes()).hexdigest(),
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
        assert Counter(s['source_sha256'] for s in provenance['sources']).most_common(1)[0][1] == 1, 'Duplicate icon artwork'
    if errors:
        print('STALE: '+', '.join(errors)); return 1
    print(f'PASS: {len(nodes)} named focuses, {len(meta["mutex_pairs"])} mutual exclusions; OR merges; no internal/old-tree overlap; rewards empty; text/assets current.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
