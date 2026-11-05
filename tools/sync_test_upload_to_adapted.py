"""Copy a frozen published snapshot to formal development; explicit --write only.

The formal upload is subsequently built with its existing PowerShell builder.
Backups and SHA manifests live outside either mod in workspace/output.
"""
import argparse,hashlib,json,shutil,subprocess
from datetime import datetime
from pathlib import Path

BASE=Path(__file__).resolve().parents[2]
SOURCE=BASE/'kr_stalin_adapted_test_upload'
TARGET=BASE/'kr_stalin_adapted_local'
RUNTIME=('common','events','gfx','history','interface','localisation','music')
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def inventory(root):
    result={}
    for p in root.rglob('*'):
        if p.is_symlink() or p.is_junction():raise RuntimeError('Redirected path: '+str(p))
        if p.is_file():result[p.relative_to(root).as_posix()]=digest(p)
    return result
def target_inventory():
    result={}
    for name in RUNTIME:
        result.update({name+'/'+r:h for r,h in inventory(TARGET/name).items()})
    for name in ('descriptor.mod','thumbnail.png'):result[name]=digest(TARGET/name)
    return result
def copy_file(src,dst):
    if not dst.resolve().is_relative_to(BASE):raise RuntimeError('Destination escaped workspace')
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
    for p in (SOURCE,TARGET):
        if p.resolve()!=p or p.is_symlink() or p.is_junction():raise RuntimeError('Redirected mod root')
    source=inventory(SOURCE);before=target_inventory()
    if set(r.split('/')[0] for r in source if '/' in r)!=set(RUNTIME):raise RuntimeError('Unexpected source roots')
    if any('/' not in r and r not in ('descriptor.mod','thumbnail.png') for r in source):raise RuntimeError('Unexpected source root file')
    changed=[r for r,h in source.items() if r!='descriptor.mod' and before.get(r)!=h]
    removed=sorted(set(before)-set(source))
    print(json.dumps(dict(source_files=len(source),changed_or_new=len(changed),removed=len(removed)),ensure_ascii=False))
    if not args.write:return
    running=subprocess.run(['powershell','-NoProfile','-Command',"if (Get-Process -Name hoi4 -ErrorAction SilentlyContinue) {exit 1}"],capture_output=True)
    if running.returncode:raise RuntimeError('Exit HOI4 before synchronization')
    audit=BASE/'output'/('test_upload_to_adapted_20261105_'+datetime.now().strftime('%H%M%S%f'))
    audit.mkdir(parents=True)
    snapshot=audit/'source_upload';backup=audit/'formal_before'
    for r in source:copy_file(SOURCE/r,snapshot/r)
    for r in before:copy_file(TARGET/r,backup/r)
    for name in ('MOD制作日志.md','AGENTS.md'):
        copy_file(TARGET/name,backup/name)
    (audit/'formal_dirty_before.patch').write_bytes(subprocess.check_output(['git','-C',str(TARGET),'diff','--binary']))
    (audit/'formal_status_before.txt').write_bytes(subprocess.check_output(['git','-C',str(TARGET),'status','--porcelain=v1','-z']))
    if inventory(snapshot)!=source:raise RuntimeError('Source backup checksum mismatch')
    if inventory(SOURCE)!=source or target_inventory()!=before:raise RuntimeError('Files changed during backup')
    manifest=dict(source=str(SOURCE),target=str(TARGET),source_sha256=source,before_sha256=before,
                  changed=changed,removed=removed,descriptor_preserved=before['descriptor.mod'])
    (audit/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    for r in changed:copy_file(snapshot/r,TARGET/r)
    for r in removed:
        p=TARGET/r
        if not p.resolve().is_relative_to(TARGET) or r.split('/')[0] not in RUNTIME:raise RuntimeError('Unsafe removal')
        p.unlink()  # Individual backed-up files only; no recursive removal.
    expected={**source,'descriptor.mod':before['descriptor.mod']}
    if target_inventory()!=expected:raise RuntimeError('Formal development checksum mismatch')
    print('AUDIT='+str(audit))

if __name__=='__main__':main()
