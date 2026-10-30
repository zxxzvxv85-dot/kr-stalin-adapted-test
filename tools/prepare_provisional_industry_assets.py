"""Explicit packaging only: scale final art and derive alpha-tested GUI hit sprites.

No repainting, generation, sharpening, blurring or color edits. Default checks
the saved asset manifest; --write is required for raster packaging.
"""
from pathlib import Path
import argparse, hashlib, json
from PIL import Image, ImageDraw
from generate_provisional_industry_gui import ROOT, ART, ZONES

SOURCE = ROOT/'tools/design/provisional_industry_20261030/industry_hybrid_train_fixed.png'
MANIFEST = ROOT/'tools/design/provisional_industry_20261030/asset_manifest.json'
# Coordinates relative to the plate. They isolate painted objects for native
# button-state tint; they do not paint rectangular backgrounds over the scene.
MASKS = {
 'relief': [(27,199),(54,190),(55,184),(93,183),(105,211),(148,221),(150,253),(108,270),(27,263)],
 'factory': [(181,218),(188,186),(205,173),(205,154),(240,151),(240,105),(285,67),(372,67),(373,105),(332,123),(332,198),(364,216),(355,245),(310,270),(181,263)],
 'rail': [(82,321),(109,295),(145,285),(162,277),(183,278),(212,275),(235,275),(237,288),(203,307),(169,335),(123,348),(82,337)],
 'road': [(317,291),(342,281),(344,264),(393,235),(416,241),(452,262),(446,278),(413,264),(393,297),(402,317),(397,332),(384,337),(328,334),(317,322)],
}

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args()
 if a.write:
  target=ROOT/ART;target.mkdir(parents=True,exist_ok=True)
  source=Image.open(SOURCE).convert('RGBA')
  plate=source.resize((492,394),Image.Resampling.LANCZOS);plate.save(target/'plate.png')
  for key,_,x,y,w,h in ZONES:
   mask=Image.new('L',plate.size,0);ImageDraw.Draw(mask).polygon(MASKS[key],fill=255)
   crop=plate.crop((x,y,x+w,y+h));crop.putalpha(mask.crop((x,y,x+w,y+h)));crop.save(target/(key+'.png'))
  paths=[SOURCE]+[target/(n+'.png') for n in ['plate']+[z[0] for z in ZONES]]
  data={str(f.relative_to(ROOT)).replace('\\','/'):{'sha256':digest(f),'size':Image.open(f).size} for f in paths}
  MANIFEST.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 data=json.loads(MANIFEST.read_text(encoding='utf8'))
 for rel,record in data.items():
  f=ROOT/rel;assert digest(f)==record['sha256'],rel;assert list(Image.open(f).size)==record['size'],rel
 print(f'Checked {len(data)} saved source/GUI assets. No image regeneration during check.')
if __name__=='__main__':main()
