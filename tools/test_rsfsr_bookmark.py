"""Native bookmark wiring and click-through display checks; not an engine UI test."""
from collections import Counter
from PIL import Image
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
    ignored={'backdrop_3','kr_logo','coverup_3','RUS_rsfsr_bookmark_caption','RUS_rsfsr_bookmark_flag','RUS_rsfsr_bookmark_portrait'}
    assert [n.norm() for n in a.v if n.value('name').strip('"') not in ignored]==[n.norm() for n in b.v if n.value('name').strip('"') not in ignored]
    portrait=next(n for n in a.v if n.value('name').strip('"')=='RUS_rsfsr_bookmark_portrait')
    assert portrait.k=='iconType' and portrait.value('alwaystransparent')=='yes'
    assert portrait.value('quadTextureSprite').strip('"')=='GFX_portrait_RUS_iosif_stalin_civilian_large'
    original_entries=load(build.KR/build.GUI)[0];actual_entries=load(build.ROOT/build.GUI)[0]
    template=next(n for n in original_entries.v if n.value('name').strip('"')=='country_entry')
    assert template.norm()==next(n for n in actual_entries.v if n.value('name').strip('"')=='country_entry').norm(),'Do not replace the portrait of every country'
    native=next(n for n in template.children('buttonType') if n.value('name').strip('"')=='country_leader')
    grid=next(n for n in a.v if n.value('name').strip('"')=='countries')
    assert int(portrait.one('position').value('x'))==int(grid.one('position').value('x'))+172*3+int(native.one('position').value('x'))
    assert int(portrait.one('position').value('y'))==int(grid.one('position').value('y'))+int(native.one('position').value('y'))
    assert portrait.value('scale')==native.value('scale')
    sprite=next(n for n in load(build.ROOT/'interface/Stalin_form_sov.gfx')[0].v if n.value('name').strip('"')==portrait.value('quadTextureSprite').strip('"'))
    with Image.open(build.ROOT/sprite.value('texturefile').strip('"')) as im:
        assert im.size==(156,210) and im.mode=='RGB','The explicit portrait must fully cover the native 48x65 portrait'
    central=next(n for n in a.v if n.value('name').strip('"')=='backdrop_3')
    assert central.one('position').value('x')=='526' and central.value('clipping')=='yes'
    assert central.one('iconType').value('quadTextureSprite').strip('"')==build.SPEC['backdrop_sprite']
    caption=next(n for n in a.v if n.value('name').strip('"')=='RUS_rsfsr_bookmark_caption')
    assert a.v.index(grid)<a.v.index(portrait)<a.v.index(caption),'Portrait must paint over the native leader but below the title'
    assert not caption.children('buttonType') and not caption.children('ButtonType')
    text=caption.one('instantTextBoxType');assert text.value('alwaystransparent')=='yes' and text.value('text').strip('"')==build.LABEL
    assert int(caption.one('position').value('x'))==526 and int(caption.one('size').value('width'))==172
    assert caption.value('clipping')=='yes'
    caption_height=int(caption.one('size').value('height'))
    caption_bg=next(n for n in load(build.ROOT/'interface/RUS_rsfsr_bookmark.gfx')[0].v if n.value('name').strip('"')=='GFX_RUS_rsfsr_bookmark_caption_bg')
    assert caption.one('background').value('quadTextureSprite').strip('"')==caption_bg.value('name').strip('"')
    assert int(caption_bg.one('size').value('y'))==caption_height
    assert int(caption_bg.one('borderSize').value('y'))*2<=caption_height,'Nine-slice borders must fit inside the two-line title'
    # Evaluate native cover rectangles in painter order, rather than testing
    # only whether the new caption/portrait nodes exist in the file.
    card=(526,130,698,241)
    def obscures(widget):
        if widget.value('hide')=='yes':return False
        pos=widget.one('position');size=widget.one('size')
        x=int(pos.value('x'));y=int(pos.value('y'))
        w=172 if size.value('width')=='@backdrop_width' else int(size.value('width'))
        h=int(size.value('height'))
        return x<card[2] and card[0]<x+w and y<card[3] and card[1]<y+h
    def covers(window):return [n for n in window.children('containerWindowType') if n.value('name').strip('"').startswith('coverup_')]
    assert any(obscures(n) for n in covers(b)), 'Fixture must reproduce the original opaque center cover'
    assert not any(obscures(n) for n in covers(a)), 'A later KR cover still hides the RSFSR card'
    cover=next(n for n in covers(a) if n.value('name').strip('"')=='coverup_3')
    assert cover.value('hide')!='yes' and cover.value('clipping')=='yes'
    # The lower native AAA card still exists: the caption plus the lower cover
    # must conceal its entire y222..318 range, without hiding the upper portrait.
    assert int(caption.one('position').value('y'))<=222
    assert int(cover.one('position').value('y'))==int(caption.one('position').value('y'))+caption_height
    assert int(cover.one('position').value('y'))+int(cover.one('size').value('height'))>=318
    lower_bg=cover.one('containerWindowType')
    assert int(cover.one('position').value('y'))+int(lower_bg.one('position').value('y'))==int(central.one('position').value('y'))
    assert lower_bg.one('iconType').norm()==central.one('iconType').norm(),'Lower cover must continue the same painting at the same scale'
    for lang in ['simp_chinese','english','russian']:
        raw=(build.ROOT/f'localisation/{lang}/RUS_rsfsr_bookmark_l_{lang}.yml').read_bytes();assert raw.startswith(b'\xef\xbb\xbf')
        keys=re.findall(r'^\s+([^ :]+):',raw.decode('utf-8-sig'),re.M);assert Counter(keys)==Counter([build.DESC,build.LABEL])
    assert (build.ROOT/'gfx/interface/rus_intro_portrait/lenin_painting.png').is_file()
    assert (build.ROOT/'interface/RUS_intro_portrait.gfx').is_file()
    flag=next(n for n in a.v if n.value('name').strip('"')=='RUS_rsfsr_bookmark_flag')
    assert flag.value('alwaystransparent')=='yes'
    assert float(flag.value('scale'))==2.0
    assert (build.ROOT/build.SPEC['flag_texture']).is_file()
    print('PASS: opaque Stalin portrait overlays only the center native leader; lower placeholder masked; original RUS entry, shared controls and bookmark gameplay unchanged.')

if __name__=='__main__':main()
