"""Explicit user-requested material-frame compositing, never runs on import.

Source sheet is read-only Frost Gallery material; six interiors were generated
with built-in image_gen. No API/credentials. No sharpening or procedural frames.
"""
import argparse, hashlib, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'tools/design/conscription_20261106'
SHEET=ROOT.parent/'3473772709/通用-素材合集/图标素材合集/素材合集－图标框（一）.PNG'
KEYS=('volunteers','territorial','universal','wartime','extended','emergency')

def build():
 # Full pre-existing metal ring, extracted as requested; no generated rim left.
 sheet=Image.open(SHEET).convert('RGBA')
 frame=sheet.crop((389,139,461,211))
 a=Image.new('L',(72,72));d=ImageDraw.Draw(a)
 d.ellipse((0,0,71,71),fill=255);d.ellipse((6,6,65,65),fill=0)
 frame.putalpha(Image.composite(frame.getchannel('A'),Image.new('L',(72,72)),a))
 frame.save(DATA/'material_frame_ring.png')
 output=ROOT/'gfx/interface/ideas';output.mkdir(parents=True,exist_ok=True)
 preview=Image.new('RGB',(720,240),(35,35,31));draw=ImageDraw.Draw(preview)
 manifest=[]
 ref=Image.open(DATA/'native_law_reference.png').convert('RGB')
 preview.paste(ref.crop((0,0,720,96)),(0,0))
 for i,key in enumerate(KEYS):
  source=Image.open(DATA/(key+'_generated.png')).convert('RGBA')
  box=source.getbbox();x,y,r,b=box;w,h=r-x,b-y
  # Trim the generated metal border; retain the soft painted subject.
  interior=source.crop((int(x+w*.12),int(y+h*.12),int(r-w*.12),int(b-h*.12))).resize((60,60),Image.Resampling.LANCZOS)
  rgb=ImageEnhance.Contrast(interior.convert('RGB')).enhance(1.45)
  rgb=ImageEnhance.Color(rgb).enhance(.9).convert('RGBA')
  mask=Image.new('L',(60,60));ImageDraw.Draw(mask).ellipse((0,0,59,59),fill=255);rgb.putalpha(mask)
  art=Image.new('RGBA',(72,72));art.alpha_composite(rgb,(6,6));art.alpha_composite(frame)
  icon=Image.new('RGBA',(64,64));icon.alpha_composite(art.resize((56,56),Image.Resampling.LANCZOS),(4,4))
  icon.save(DATA/(key+'_64.png'));icon.save(output/('RUS_sc_'+key+'.dds'),pixel_format='DXT5')
  preview.paste(icon,(i*120+20,135),icon);draw.text((i*120+3,208),key,fill='white')
  manifest.append({'key':key,'source_size':source.size,'size':[64,64],
   'dds_sha256':hashlib.sha256((output/('RUS_sc_'+key+'.dds')).read_bytes()).hexdigest()})
 preview.save(DATA/'native_size_comparison.png')
 (DATA/'asset_manifest.json').write_text(json.dumps({'frame_source':str(SHEET),'frame_crop':[389,139,461,211],
  'interior_contrast':1.45,'interior_saturation':.9,'sharpening':False,'assets':manifest},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Built six 64x64 alpha DDS icons and native-size comparison.')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');args=p.parse_args()
 if args.write:build()
 else:print('Read-only. Use --write to rebuild from archived generated images and read-only material sheet.')
