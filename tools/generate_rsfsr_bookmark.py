"""A presentation-only RSFSR major entry linking to the existing RUS start.

Default/--check is read-only. --write updates six text files; no game history,
politics, portraits, flags or source artwork are modified.
"""
from pathlib import Path
import argparse,json,re
from hoi4_politics_blocks import parse

ROOT=Path(__file__).resolve().parents[1];KR=ROOT.parent/'1521695605'
SPEC=json.loads((ROOT/'tools/design/RUS_rsfsr_bookmark_20261018.json').read_text(encoding='utf-8'))
BOOKMARK='common/bookmarks/the_gathering_storm.txt'
GUI='interface/frontendgamesetupview.gui'
DESC='RUS_rsfsr_bookmark_history'
LABEL='RUS_rsfsr_bookmark_card_label'

def patch(text,spans):
    for start,end,new in sorted(spans,reverse=True):text=text[:start]+new+text[end:]
    return text

def render_bookmark():
    text=(KR/BOOKMARK).read_text(encoding='utf-8-sig')
    bookmark=parse(text)[0].one('bookmark')
    majors=[n for n in bookmark.v if isinstance(n.v,list) and n.one('ideology') and n.value('minor')!='yes']
    placeholder=majors[SPEC['major_slot']];assert placeholder.k=='AAA'
    entry='''RUS = {
            # Route showcase only: the selected playable country remains RUS.
            version = all_the_russias
            history = RUS_rsfsr_bookmark_history
            ideology = totalist
            override_leader_portrait = RUS_iosif_stalin
            focuses = {
                RUS_reverse_the_october_revolution
                RUS_future_foreign_005
                RUS_fr_post_revolutionary_armed_forces
            }
        }'''
    return patch(text,[(placeholder.a,placeholder.b,entry)]).rstrip()+'\n'

def render_gui():
    text=(KR/GUI).read_text(encoding='utf-8-sig')
    root=parse(text)[0];window=next(n for n in root.v if n.value('name').strip('"')=='gamesetup_interesting_countries_window')
    backdrop=next(n for n in window.children('containerWindowType') if n.value('name').strip('"')=='backdrop_3')
    replacement='''containerWindowType = {
            name = "backdrop_3"
            position = { x = 526 y = 42 }
            size = { width = @backdrop_width height = @backdrop_height }
            clipping = yes
            background = { quadTextureSprite = "GFX_tiled_paper_bg2" }
            iconType = {
                name = "backdrop_texture_3"
                quadTextureSprite = "GFX_RUS_intro_lenin_painting"
                position = { x = 2 y = 2 }
                scale = 0.250229
                alwaystransparent = yes
            }
        }'''
    logo=next(n for n in window.children('iconType') if n.value('name')=='kr_logo')
    logo_raw=logo.raw();closing=logo_raw.rfind('}')
    logo_raw=logo_raw[:closing]+'    hide = yes\n        '+logo_raw[closing:]
    # The engine's TAG-based caption cannot carry two different names for RUS.
    # A click-through label covers only the showcase slot's original name bar.
    filters=next(n for n in window.children('OverlappingElementsBoxType') if n.value('name').strip('"')=='filters')
    overlay='''containerWindowType = {
            name = "RUS_rsfsr_bookmark_caption"
            position = { x = 526 y = 203 }
            size = { width = 172 height = 38 }
            background = { quadTextureSprite = "GFX_tiled_paper_bg2" }
            instantTextBoxType = {
                name = "RUS_rsfsr_bookmark_caption_text"
                position = { x = 1 y = 0 }
                font = "hoi_16mbs"
                text = "RUS_rsfsr_bookmark_card_label"
                maxWidth = 170
                maxHeight = 38
                fixedsize = yes
                format = centre
                alwaystransparent = yes
            }
        }

        iconType = {
            name = "RUS_rsfsr_bookmark_flag"
            quadTextureSprite = "GFX_RUS_rsfsr_bookmark_flag"
            position = { x = 594 y = 145 }
            scale = 2.0
            alwaystransparent = yes
        }

        '''
    return patch(text,[(backdrop.a,backdrop.b,replacement),(logo.a,logo.b,logo_raw),(filters.a,filters.a,overlay)])

def outputs():
    data={BOOKMARK:render_bookmark().encode('utf-8'),GUI:render_gui().encode('utf-8')}
    data['interface/RUS_rsfsr_bookmark.gfx']=('spriteTypes = {\n\tspriteType = {\n\t\tname = "GFX_RUS_rsfsr_bookmark_flag"\n\t\ttexturefile = "'+SPEC['flag_texture']+'"\n\t}\n}\n').encode('utf-8')
    histories={
        'simp_chinese':SPEC['history'],
        'english':'At first, under Vladimir Lenin’s passionate leadership, the Bolsheviks became known throughout Russia, supported by those with the bleakest prospects.\n\nBut events turned against them. As the revolution changed, the hoped-for unity of the left failed to materialise. Opportunist Socialist Revolutionaries betrayed the revolution, and Lenin perished in that betrayal. The once-promising Russian revolution collapsed; the Bolsheviks could only leave their homeland and seek another path…',
        'russian':'Поначалу под вдохновенным руководством Владимира Ленина большевики стали известны по всей стране, получив поддержку самых обездоленных.\n\nНо надежды не сбылись. В стремительно менявшейся революционной обстановке ожидаемое народом единство левых так и не наступило. Эсеры-оппортунисты предали революцию, и товарищ Ленин погиб. Некогда многообещающая русская революция потерпела крах, а большевикам оставалось лишь покинуть родину и искать иной путь…'
    }
    labels={'simp_chinese':SPEC['card_label'],'english':'Russian Soviet\nFederative Republic','russian':'Российская Советская\nФедеративная Республика'}
    for lang in histories:
        rows=['l_'+lang+':',' '+DESC+': '+json.dumps(histories[lang],ensure_ascii=False),' '+LABEL+': '+json.dumps(labels[lang],ensure_ascii=False)]
        data[f'localisation/{lang}/RUS_rsfsr_bookmark_l_{lang}.yml']=('\n'.join(rows)+'\n').encode('utf-8-sig')
    return data

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');ap.add_argument('--check',action='store_true');args=ap.parse_args()
    generated=outputs()
    for path,raw in generated.items():
        if path.endswith(('.txt','.gui')):parse(raw.decode('utf-8-sig'))
    if args.write:
        for path,raw in generated.items():p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
        print('Wrote RSFSR showcase bookmark, central Lenin backdrop and three-language text; actual RUS history unchanged.')
    else:
        stale=[p for p,v in generated.items() if not (ROOT/p).exists() or (ROOT/p).read_bytes()!=v]
        if stale:print('STALE: '+', '.join(stale));return 1
        print('PASS: RUS-linked RSFSR showcase files match their sources.')
    return 0

if __name__=='__main__':raise SystemExit(main())
