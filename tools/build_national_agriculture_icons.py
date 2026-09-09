"""Fit existing vanilla/KR art to 32px agriculture UI sprites; no image API calls."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
KR = ROOT.parent / '1521695605'
GAME = ROOT.parents[3] / 'common/Hearts of Iron IV'
DEST = ROOT / 'gfx/interface/RUS_national_agriculture'
DEST.mkdir(parents=True, exist_ok=True)
SOURCES = {
    'stock': GAME / 'gfx/interface/in_stock_icon.dds',
    'reform': KR / 'gfx/interface/ideas/RUS_land_reforms.png',
    'orders': KR / 'gfx/interface/decisions/generic_agreement.png',
    'machinery': KR / 'gfx/interface/ideas/generic_mechanised_agriculture.png',
    'food': KR / 'gfx/interface/decisions/decisions_categories/agriculture_grain.png',
    'export': KR / 'gfx/interface/decisions/global_trade.png',
    'income': KR / 'gfx/interface/decisions/cash_flow.png',
    'factories': KR / 'gfx/interface/decisions/factories.png',
}
manifest = []
for name, source in SOURCES.items():
    with Image.open(source) as original:
        art = original.convert('RGBA')
    bounds = art.getchannel('A').getbbox()
    assert bounds, f'Blank source: {source}'
    fitted = ImageOps.contain(art.crop(bounds), (28, 28), Image.Resampling.LANCZOS)
    icon = Image.new('RGBA', (32, 32))
    icon.alpha_composite(fitted, ((32-fitted.width)//2, (32-fitted.height)//2))
    assert icon.getchannel('A').getextrema() == (0, 255)
    destination = DEST / f'{name}.png'
    icon.save(destination)
    manifest.append({'name': name, 'source': str(source), 'sha256': hashlib.sha256(destination.read_bytes()).hexdigest()})
    fitted_text = ImageOps.contain(art.crop(bounds), (18, 18), Image.Resampling.LANCZOS)
    text_icon = Image.new('RGBA', (20, 20))
    text_icon.alpha_composite(fitted_text, ((20-fitted_text.width)//2, (20-fitted_text.height)//2))
    text_destination = DEST / f'text_{name}.png'
    text_icon.save(text_destination)
    manifest.append({'name': 'text_'+name, 'source': str(source), 'sha256': hashlib.sha256(text_destination.read_bytes()).hexdigest()})
proof = ROOT / 'output/national-agriculture'
proof.mkdir(parents=True, exist_ok=True)
(proof / 'icon-sources.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
print('Eight existing-art sprites at 32x32 and eight inline icons at 20x20. No paid generation.')
