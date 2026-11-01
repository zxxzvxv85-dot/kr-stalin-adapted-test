"""Package state art and inspected library sprites. --check never paints/writes."""
from pathlib import Path
import argparse,json,hashlib,math,shutil,os
from PIL import Image,ImageDraw,ImageFilter,ImageEnhance
from generate_provisional_industry_gui import ROOT,ART,ZONES
from prepare_provisional_industry_assets import MASKS
SOURCE=ROOT/'tools/design/provisional_industry_20261101';TARGET=ROOT/ART/'dynamic';MANIFEST=SOURCE/'asset_manifest.json'
def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');p.add_argument('--check',action='store_true');a=p.parse_args()
 if a.write:
  TARGET.mkdir(parents=True,exist_ok=True)
  paths=[SOURCE/'idle.png',SOURCE/'construction.png',ROOT/'tools/design/provisional_industry_20261030/industry_hybrid_train_fixed.png']
  plates=[Image.open(p).convert('RGBA').resize((492,394),Image.Resampling.LANCZOS) for p in paths]
  strip=Image.new('RGBA',(1476,394))
  for i,im in enumerate(plates):strip.paste(im,(i*492,0))
  strip.save(TARGET/'scene.png')
  for key,_,x,y,w,h in ZONES:
   mask=Image.new('L',(492,394),0);ImageDraw.Draw(mask).polygon(MASKS[key],fill=255);cutmask=mask.crop((x,y,x+w,y+h))
   frames=Image.new('RGBA',(w*3,h))
   for i,plate in enumerate(plates):
    crop=plate.crop((x,y,x+w,y+h));crop.putalpha(cutmask);frames.paste(crop,(i*w,0))
   frames.save(TARGET/(key+'.png'))
  for key in ('coins','factory','train','tools','clock'):
   im=Image.open(SOURCE/(key+'.png')).convert('RGBA');im.thumbnail((30,31),Image.Resampling.LANCZOS);canvas=Image.new('RGBA',(32,32));canvas.paste(im,((32-im.width)//2,(32-im.height)//2),im);canvas.save(TARGET/(key+'_icon.png'))
  shutil.copyfile(SOURCE/'frame.png',TARGET/'frame.png')
  tex=Image.open(ROOT.parent/'3473772709/通用-素材合集/纹理及背景素材/素材合集-纹理（五）.png').convert('RGB').resize((492,166),Image.Resampling.LANCZOS);tex=ImageEnhance.Color(tex).enhance(.2);tex=ImageEnhance.Brightness(tex).enhance(.2);tex.save(TARGET/'ledger.png')
  order=tex.crop((0,0,223,46));d=ImageDraw.Draw(order);d.rectangle((0,0,222,45),outline=(82,81,72));d.line((1,1,221,1),fill=(115,109,89));order.save(TARGET/'order.png')
  gear=Image.open(SOURCE/'gear.png').convert('RGBA');gear.thumbnail((19,19));spin=Image.new('RGBA',(22*12,22))
  for f in range(12):
   im=gear.rotate(-f*30,resample=Image.Resampling.BICUBIC);spin.paste(im,(f*22+(22-im.width)//2,(22-im.height)//2),im)
  spin.save(TARGET/'gear_spin.png')
  cloud=Image.open(SOURCE/'smoke.png').convert('RGBA');cloud.thumbnail((53,28));dust=Image.new('RGBA',(64*12,36))
  for f in range(12):
   im=cloud.copy();im.putalpha(im.getchannel('A').point(lambda a:int(a*(.22+.10*math.sin(f*math.pi/6)))))
   dust.paste(im,(64*f+f//3,5-f//4),im)
  dust.save(TARGET/'dust.png')
  bar=Image.new('RGBA',(444*7,8))
  for f in range(7):
   im=Image.new('RGBA',(444,8),(22,24,22,255));d=ImageDraw.Draw(im);d.rectangle((0,0,443,7),outline=(99,96,76));width=round(440*f/6)
   if width:d.rectangle((2,2,1+width,5),fill=(139,129,75))
   for x in range(74,444,74):d.line((x,1,x,6),fill=(35,36,30))
   bar.paste(im,(f*444,0))
  bar.save(TARGET/'recovery.png')
  files=paths+list(SOURCE.glob('*.png'))+[ROOT.parent/'3473772709/通用-素材合集/纹理及背景素材/素材合集-纹理（五）.png']+list(TARGET.glob('*.png'))
  manifest={Path(os.path.relpath(p.resolve(),ROOT)).as_posix():{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size':list(Image.open(p).size)} for p in dict.fromkeys(files)}
  MANIFEST.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 data=json.loads(MANIFEST.read_text(encoding='utf-8'))
 for name,v in data.items():
  p=ROOT/name;assert hashlib.sha256(p.read_bytes()).hexdigest()==v['sha256'],name;assert list(Image.open(p).size)==v['size'],name
 print('PASS:',len(data),'dynamic scene/source assets')
if __name__=='__main__':main()
