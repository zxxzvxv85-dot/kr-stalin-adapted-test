"""Explicit user-requested material-frame compositing, never runs on import.

Source sheet is read-only Frost Gallery material; six interiors adapt distinct
existing poster people using built-in image_gen. No sharpening or invented frames.
"""
import argparse, hashlib, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'tools/design/conscription_20261106'
SHEET=ROOT.parent/'3473772709/通用-素材合集/图标素材合集/素材合集－图标框（一）.PNG'
KEYS=('volunteers','territorial','universal','wartime','extended','emergency')
CONTRAST=1.12
SATURATION=.72
INSET=.06

def build():
 # Full pre-existing metal ring, extracted as requested; no generated rim left.
 sheet=Image.open(SHEET).convert('RGBA')
 frame=sheet.crop((389,139,461,211))
 a=Image.new('L',(72,72));d=ImageDraw.Draw(a)
 d.ellipse((0,0,71,71),fill=255);d.ellipse((6,6,65,65),fill=0)
 frame.putalpha(Image.composite(frame.getchannel('A'),Image.new('L',(72,72)),a))
 frame.save(DATA/'material_frame_ring.png')
 output=ROOT/'gfx/interface/ideas';output.mkdir(parents=True,exist_ok=True)
 preview=Image.new('RGB',(720,450),(35,35,31));draw=ImageDraw.Draw(preview)
 manifest=[]
 ref=Image.open(DATA/'native_law_reference.png').convert('RGB')
 preview.paste(ref.crop((0,0,720,96)),(0,0))
 previous=Image.open(DATA/'previous_set_reference.png').convert('RGB')
 sources={a['key']:a for a in json.loads((DATA/'poster_sources.json').read_text(encoding='utf-8'))['assets']}
 draw.text((3,104),'Previous set',fill='white')
 draw.text((3,214),'Poster-based replacement (64px)',fill='white')
 draw.text((3,324),'Grayscale readability preview',fill='white')
 for i,key in enumerate(KEYS):
  old=previous.crop((i*120+20,135,i*120+84,199))
  preview.paste(old,(i*120+20,125))
  entry=sources[key];source_path=DATA/entry['workspace_file']
  source=Image.open(source_path).convert('RGBA')
  # Ignore faint alpha noise beyond the transparent medallion silhouette.
  box=source.getchannel('A').point(lambda v:255 if v>8 else 0).getbbox();x,y,r,b=box;w,h=r-x,b-y
  # Trim the generated metal border; retain the soft painted subject.
  crop=(int(x+w*INSET),int(y+h*INSET),int(r-w*INSET),int(b-h*INSET))
  interior=source.crop(crop).resize((60,60),Image.Resampling.LANCZOS)
  rgb=ImageEnhance.Contrast(interior.convert('RGB')).enhance(CONTRAST)
  rgb=ImageEnhance.Color(rgb).enhance(SATURATION).convert('RGBA')
  mask=Image.new('L',(60,60));ImageDraw.Draw(mask).ellipse((0,0,59,59),fill=255);rgb.putalpha(mask)
  art=Image.new('RGBA',(72,72));art.alpha_composite(rgb,(6,6));art.alpha_composite(frame)
  icon=Image.new('RGBA',(64,64));icon.alpha_composite(art.resize((56,56),Image.Resampling.LANCZOS),(4,4))
  icon.save(DATA/(key+'_64.png'));icon.save(output/('RUS_sc_'+key+'.dds'),pixel_format='DXT5')
  preview.paste(icon,(i*120+20,235),icon);draw.text((i*120+3,304),key,fill='white')
  gray=icon.convert('L').convert('RGBA');gray.putalpha(icon.getchannel('A'))
  preview.paste(gray,(i*120+20,345),gray)
  manifest.append({'key':key,'source':entry['workspace_file'],'source_poster':entry['source_poster'],
   'source_sha256':hashlib.sha256(source_path.read_bytes()).hexdigest(),'source_size':source.size,'interior_crop':crop,'size':[64,64],
   'dds_sha256':hashlib.sha256((output/('RUS_sc_'+key+'.dds')).read_bytes()).hexdigest()})
 preview.save(DATA/'native_size_comparison.png')
 (DATA/'asset_manifest.json').write_text(json.dumps({'frame_source':str(SHEET),'frame_crop':[389,139,461,211],
  'interior_contrast':CONTRAST,'interior_saturation':SATURATION,'interior_inset':INSET,
  'prompt_manifest':'poster_sources.json','sharpening':False,'assets':manifest},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Built six 64x64 alpha DDS icons and native-size comparison.')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');args=p.parse_args()
 if args.write:build()
 else:print('Read-only. Use --write to rebuild from archived poster adaptations and read-only material sheet.')
