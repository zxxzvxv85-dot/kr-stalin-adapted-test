"""Native bookmark wiring and click-through display checks; not an engine UI test."""
from collections import Counter
import re
import generate_rsfsr_bookmark as build
from hoi4_politics_blocks import load,parse

def major_nodes(tree):return [n for n in tree.v if isinstance(n.v,list) and n.one('ideology') and n.value('minor')!='yes']
def get_window(nodes):return next(n for n in nodes[0].v if n.value('name').strip('"')=='gamesetup_interesting_countries_window')

def main():
    original=load(build.KR/build.BOOKMARK)[0].one('bookmark')
    actual=load(build.ROOT/build.BOOKMARK)[0].one('bookmark')
    old=major_nodes(original);new=major_nodes(actual)
    assert len(new)==len(old) and old[6].k=='AAA' and new[6].k=='RUS'
    entry=new[6]
    assert entry.value('ideology')=='totalist' and entry.value('override_leader_portrait')=='RUS_iosif_stalin'
    assert entry.value('history')==build.DESC and sum(n.k=='RUS' for n in new)==2
    assert all(a.norm()==b.norm() for i,(a,b) in enumerate(zip(old,new)) if i!=6)
    assert [n.norm() for n in actual.v if n is not entry]==[n.norm() for n in original.v if n is not old[6]]
    assert actual.one('effect').norm()==original.one('effect').norm(),'Bookmark must not alter the actual starting country'
    a=get_window(load(build.ROOT/build.GUI));b=get_window(load(build.KR/build.GUI))
    ignored={'backdrop_3','kr_logo','RUS_rsfsr_bookmark_caption','RUS_rsfsr_bookmark_flag'}
    assert [n.norm() for n in a.v if n.value('name').strip('"') not in ignored]==[n.norm() for n in b.v if n.value('name').strip('"') not in ignored]
    central=next(n for n in a.v if n.value('name').strip('"')=='backdrop_3')
    assert central.one('position').value('x')=='526' and central.value('clipping')=='yes'
    assert central.one('iconType').value('quadTextureSprite').strip('"')==build.SPEC['backdrop_sprite']
    caption=next(n for n in a.v if n.value('name').strip('"')=='RUS_rsfsr_bookmark_caption')
    assert not caption.children('buttonType') and not caption.children('ButtonType')
    text=caption.one('instantTextBoxType');assert text.value('alwaystransparent')=='yes' and text.value('text').strip('"')==build.LABEL
    assert int(caption.one('position').value('x'))==526 and int(caption.one('size').value('width'))==172
    for lang in ['simp_chinese','english','russian']:
        raw=(build.ROOT/f'localisation/{lang}/RUS_rsfsr_bookmark_l_{lang}.yml').read_bytes();assert raw.startswith(b'\xef\xbb\xbf')
        keys=re.findall(r'^\s+([^ :]+):',raw.decode('utf-8-sig'),re.M);assert Counter(keys)==Counter([build.DESC,build.LABEL])
    assert (build.ROOT/'gfx/interface/rus_intro_portrait/lenin_painting.png').is_file()
    assert (build.ROOT/'interface/RUS_intro_portrait.gfx').is_file()
    flag=next(n for n in a.v if n.value('name').strip('"')=='RUS_rsfsr_bookmark_flag')
    assert flag.value('alwaystransparent')=='yes'
    assert float(flag.value('scale'))==2.0
    assert (build.ROOT/build.SPEC['flag_texture']).is_file()
    print('PASS: central-slot RUS showcase, Stalin portrait override, untouched original RUS card and all other entries, exact history text, native Lenin backdrop and click-through caption. No bookmark gameplay effects added.')

if __name__=='__main__':main()
