"""Prepare only the 2026-10-29 changes starting at the 08:16 military request.

Does not modify an upload. The normal upload builder consumes this reviewed
overlay. Existing upload differences are preserved by three-way application;
localisation applies changed keys only. No earlier education system is imported.
"""
from pathlib import Path
import argparse, hashlib, json, re, subprocess, tempfile

ROOT = Path(__file__).resolve().parents[1]
START = '37c1811'
END = 'fd275a1'
EDUCATION_FX = 'common/scripted_effects/RUS_stalin_education_reform_effects.txt'

def git_bytes(*args):
    return subprocess.run(['git', '-C', str(ROOT), *args], check=True, capture_output=True).stdout

def digest(raw): return hashlib.sha256(raw).hexdigest()

def locale_delta(old, base, new):
    pattern = re.compile(r'^\s+([^\s:#]+):\d*\s+.*$', re.M)
    def entries(raw):
        text = raw.decode('utf-8-sig')
        return {m[1]: m[0] for m in pattern.finditer(text)}
    before, after = entries(base), entries(new)
    changed = {k: line for k, line in after.items() if before.get(k) != line}
    removed = set(before) - set(after)
    text = old.decode('utf-8-sig')
    def replace(m):
        key = m[1]
        if key in removed: return ''
        return changed.pop(key, m[0])
    text = pattern.sub(replace, text)
    if changed: text = text.rstrip('\r\n') + '\n' + '\n'.join(changed.values()) + '\n'
    return b'\xef\xbb\xbf' + text.encode('utf-8')

def merge(old, base, new):
    if old == base: return new
    # Normalise line endings for merge matching, then restore the upload style.
    newline = '\r\n' if b'\r\n' in old else '\n'
    with tempfile.TemporaryDirectory() as directory:
        paths = [Path(directory)/name for name in ('upload', 'before0816', 'after0816')]
        for p, raw in zip(paths, (old, base, new)):
            p.write_bytes(raw.replace(b'\r\n', b'\n'))
        result = subprocess.run(['git', 'merge-file', '--stdout', *map(str, paths)], capture_output=True)
        if result.returncode != 0: raise RuntimeError('Conflicting script changes require review')
        return result.stdout.replace(b'\n', newline.encode())

def prepare(baseline, output):
    baseline, output = baseline.resolve(), output.resolve()
    if baseline.parent != ROOT.parent or not baseline.name.startswith(ROOT.name+'_upload.previous.'):
        raise ValueError('Use an original sibling upload backup')
    if not output.is_relative_to(ROOT/'tmp'): raise ValueError('Output must stay below source/tmp')
    if not (baseline/'descriptor.mod').is_file(): raise ValueError('No baseline descriptor')
    if output.exists() and any(output.iterdir()): raise ValueError('Use an empty output directory')
    names = git_bytes('diff', '--name-only', START, END).decode().splitlines()
    names = [p for p in names if p.startswith(('common/', 'events/', 'interface/', 'localisation/'))]
    rows, deferred = [], []
    modern_education = b'RUS_education_refresh' in (baseline/EDUCATION_FX).read_bytes()
    for name in names:
        if not modern_education and (name == EDUCATION_FX or '/RUS_education_dashboard_l_' in name):
            deferred.append(name)
            continue
        # Pin both ends: future development must never enter this old release.
        new = git_bytes('show', END+':'+name)
        exists = subprocess.run(['git', '-C', str(ROOT), 'cat-file', '-e', START+':'+name], capture_output=True).returncode == 0
        previous = baseline/name
        if not exists:
            if previous.exists(): raise ValueError('New scoped file already exists in upload: '+name)
            raw, method = new, 'new scoped file'
        else:
            if not previous.exists(): raise ValueError('Earlier dependency absent from upload: '+name)
            old = previous.read_bytes()
            base = git_bytes('show', START+':'+name)
            if name.endswith('.yml'):
                raw, method = locale_delta(old, base, new), 'changed localisation keys only'
            else:
                raw, method = merge(old, base, new), 'three-way scoped script delta'
        destination = output/name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
        rows.append(dict(path=name, sha256=digest(raw), source_sha256=digest(new), method=method))
    report = dict(start=START, end=END, baseline=str(baseline), overlay=str(output), files=rows,
                  deferred_education=deferred, reason='Original upload lacks the pre-08:16 education poster and enthusiasm system' if deferred else '')
    report_path = output.parent/(output.name+'_manifest.json')
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(files=len(rows), deferred=len(deferred), manifest=str(report_path))))

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args=parser.parse_args()
    prepare(args.baseline,args.output)
