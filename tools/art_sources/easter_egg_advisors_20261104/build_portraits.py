"""Explicit rebuild using the user's requested existing KR frame workflow."""
import json,hashlib,subprocess,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
FRAME=ROOT/'tools/art_templates/KR_advisor_frame_bukharin_260x268.png'
ROWS=[('su_beichen','su_beichen_source.jpg','35,0,410,455','苏北辰'),
      ('larruping','larruping_source.png','35,20,560,580','larruping'),
      ('mia','mia_source.jpg','215,0,1040,1080','米娅'),
      ('xin','xin_source.png','170,25,500,490','心'),
      ('suyi','suyi_source.png','0,0,606,606','Suyi'),
      ('hongying','hongying_source.png','0,0,602,601','今日红缨在手')]

def main():
    if sys.argv[1:]!=['--write']:raise SystemExit('Explicit image rebuild requires --write')
    manifest={'method':'Existing Build-KRAdvisorPortrait.py; crop/grayscale/card perspective/transparent KR frame','frame_sha256':hashlib.sha256(FRAME.read_bytes()).hexdigest(),'portraits':[]}
    canvas=Image.new('RGB',(300*len(ROWS),344),(34,36,35));draw=ImageDraw.Draw(canvas)
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',21)
    for i,(key,source,crop,name) in enumerate(ROWS):
        output=ROOT/f'gfx/interface/advisors/RUS/RUS_{key}.png'
        subprocess.run([sys.executable,str(ROOT/'tools/art_templates/Build-KRAdvisorPortrait.py'),
            '--input',str(HERE/source),'--frame',str(FRAME),'--crop',crop,'--output',str(output),
            '--preview',str(ROOT/f'tools/art_previews/RUS_{key}_advisor_preview.png')],check=True)
        card=Image.open(output).convert('RGBA');canvas.paste(card.resize((260,268),Image.Resampling.NEAREST),(20+i*300,12),card.resize((260,268),Image.Resampling.NEAREST))
        draw.text((28+i*300,294),name,font=font,fill=(231,229,216))
        manifest['portraits'].append(dict(source=source,source_sha256=hashlib.sha256((HERE/source).read_bytes()).hexdigest(),crop=crop,
            output=output.relative_to(ROOT).as_posix(),size=list(card.size),mode=card.mode,output_sha256=hashlib.sha256(output.read_bytes()).hexdigest()))
    canvas.save(ROOT/'tools/art_previews/RUS_easter_egg_advisors.png')
    (HERE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

if __name__=='__main__':main()
