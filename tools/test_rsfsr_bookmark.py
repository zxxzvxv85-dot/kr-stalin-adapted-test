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
    assert len(new)==len(old) and old[6].k=='AAA' and new[6].k=='RSB'
    entry=new[6]
    assert entry.value('ideology')=='communist' and entry.value('override_leader_portrait')=='RSB_iosif_stalin_showcase'
    assert entry.value('history')==build.DESC and sum(n.k=='RUS' for n in new)==1
    assert all(a.norm()==b.norm() for i,(a,b) in enumerate(zip(old,new)) if i!=6)
    assert [n.norm() for n in actual.v if n is not entry]==[n.norm() for n in original.v if n is not old[6]]
    assert actual.one('effect').norm()==original.one('effect').norm(),'Bookmark must not alter the actual starting country'
    a=get_window(load(build.ROOT/build.GUI));b=get_window(load(build.KR/build.GUI))
    ignored={'backdrop_3','kr_logo','coverup_3','RUS_rsfsr_bookmark_caption'}
    assert [n.norm() for n in a.v if n.value('name').strip('"') not in ignored]==[n.norm() for n in b.v if n.value('name').strip('"') not in ignored]
    assert not any(n.value('name').strip('"') in {'RUS_rsfsr_bookmark_portrait','RUS_rsfsr_bookmark_flag'} for n in a.v),'Do not cover the native portrait tooltip, cloth flag or selected frame'
    original_entries=load(build.KR/build.GUI)[0];actual_entries=load(build.ROOT/build.GUI)[0]
    template=next(n for n in original_entries.v if n.value('name').strip('"')=='country_entry')
    assert template.norm()==next(n for n in actual_entries.v if n.value('name').strip('"')=='country_entry').norm(),'Do not replace the portrait of every country'
    grid=next(n for n in a.v if n.value('name').strip('"')=='countries')
    char=load(build.ROOT/'common/characters/RUS_rsfsr_bookmark.txt')[0].one('RSB_iosif_stalin_showcase')
    assert char.value('name')=='RUS_iosif_stalin'
    leader=char.one('country_leader')
    assert leader.value('desc')=='RUS_iosif_stalin_leader_desc' and leader.value('ideology')=='marxism_leninism_subtype'
    large=char.one('portraits').one('civilian').value('large')
    assert large=='GFX_portrait_RUS_iosif_stalin_civilian_large'
    sprite=next(n for n in load(build.ROOT/'interface/Stalin_form_sov.gfx')[0].v if n.value('name').strip('"')==large)
    with Image.open(build.ROOT/sprite.value('texturefile').strip('"')) as im:
        assert im.size==(156,210) and im.mode=='RGB'
    profile=load(build.ROOT/'history/countries/RSB - RSFSR Showcase.txt')
    assert next(n for n in profile if n.k=='recruit_character').v==char.k
    assert next(n for n in profile if n.k=='set_politics').value('ruling_party')=='communist'
    assert next(n for n in profile if n.k=='set_politics').value('elections_allowed')=='no'
    assert {n.k for n in profile}=={'capital','set_politics','set_popularities','recruit_character'}
    tags=load(build.ROOT/'common/country_tags/zz_RUS_rsfsr_bookmark.txt')
    assert len(tags)==1 and tags[0].k=='RSB'
    assert (build.ROOT/'common'/tags[0].v.strip('"')).is_file()
    # Follow the installed KR KAZ->TRK on_startup pattern exactly: only a human
    # display tag is redirected, with PREV still bound to the display country.
    hook=load(build.ROOT/'common/on_actions/00_RUS_rsfsr_bookmark.txt')[0]
    branch=hook.one('on_startup').one('effect').one('RSB').one('if')
    assert branch.one('limit').value('is_ai')=='no'
    assert branch.one('RUS').value('change_tag_from')=='PREV'
    assert {n.k for n in branch.v}=={'limit','RUS'}
    kr_hook=load(build.KR/'common/on_actions/on_actions_Central_Asia.txt')[0].one('on_startup').one('effect').one('KAZ')
    assert parse(kr_hook.raw().replace('KAZ','RSB').replace('TRK','RUS'))[0].norm()==hook.one('on_startup').one('effect').one('RSB').norm()
    def execute(nodes,players,current=None,previous=None):
        for node in nodes:
            if node.k in {'RSB','RUS'}:
                execute(node.v,players,node.k,current)
            elif node.k=='if':
                assert node.one('limit').value('is_ai')=='no'
                if current in players:execute([n for n in node.v if n.k!='limit'],players,current,previous)
            elif node.k=='change_tag_from':
                assert node.v=='PREV' and previous in players
                players.remove(previous);players.add(current)
            else:raise AssertionError('Unexpected handoff operation: '+node.k)
    for player in ['RSB','RUS','GER','AFG',None]:
        players={player} if player else set()
        execute(hook.one('on_startup').one('effect').v,players)
        expected={'RUS' if player=='RSB' else player} if player else set()
        assert players==expected
        execute(hook.one('on_startup').one('effect').v,players)
        assert players==expected,'Reload must not repeat the transfer or affect an ordinary RUS start'
    # No territory, cores, units or real-RUS state are used to make the profile.
    for folder in [build.ROOT/'history/states',build.KR/'history/states']:
        assert not any(re.search(r'\b(?:owner|controller|add_core_of)\s*=\s*RSB\b',p.read_text(encoding='utf-8-sig')) for p in folder.glob('*.txt'))
    central=next(n for n in a.v if n.value('name').strip('"')=='backdrop_3')
    assert central.one('position').value('x')=='526' and central.value('clipping')=='yes'
    assert central.one('iconType').value('quadTextureSprite').strip('"')==build.SPEC['backdrop_sprite']
    caption=next(n for n in a.v if n.value('name').strip('"')=='RUS_rsfsr_bookmark_caption')
    assert a.v.index(grid)<a.v.index(caption)
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
        keys=re.findall(r'^\s+([^ :]+):',raw.decode('utf-8-sig'),re.M)
        assert len(keys)==len(set(keys)) and {build.DESC,build.LABEL,'RSB','RSB_communist','RSB_communist_party','RSB_communist_party_long'}<=set(keys)
    assert (build.ROOT/'gfx/interface/rus_intro_portrait/lenin_painting.png').is_file()
    assert (build.ROOT/'interface/RUS_intro_portrait.gfx').is_file()
    for size in ['', 'medium/', 'small/']:
        assert (build.ROOT/('gfx/flags/'+size+'RSB.tga')).read_bytes()==(build.ROOT/('gfx/flags/'+size+'RUS_sov_5.tga')).read_bytes()
    print('PASS: independent landless Stalin profile supplies native portrait/tooltip/info/cloth flag/frame; fifth-flag bytes exact at all three sizes; human RSB handoff points to RUS; original RUS entry and actual country history untouched.')

if __name__=='__main__':main()
