"""Export complete generated adviser emblems; default is read-only validation."""
from pathlib import Path
import argparse
import hashlib
import io
import json

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'tools/design/adviser_faction_icons_coloured_20261023/manifest.json'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--write', action='store_true')
    mode.add_argument('--check', action='store_true')
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    errors = []
    hashes = set()
    assert len(manifest['items']) == 9
    for item in manifest['items']:
        source, target = ROOT / item['source'], ROOT / item['destination']
        assert hashlib.sha256(source.read_bytes()).hexdigest() == item['source_sha256'], source
        with Image.open(source) as original:
            assert original.mode == 'RGBA' and original.width > 0 and original.height > 0
            assert list(original.size) == item['source_size']
            assert original.getextrema()[3] == (0, 255)
            fitted = ImageOps.contain(original, tuple(manifest['size']), Image.Resampling.LANCZOS)
            if fitted.size == tuple(manifest['size']):
                image = fitted
            else:
                image = Image.new('RGBA', tuple(manifest['size']))
                image.alpha_composite(fitted, ((image.width - fitted.width) // 2, (image.height - fitted.height) // 2))
        alpha = image.getchannel('A')
        assert alpha.getextrema()[0] == 0 and alpha.getextrema()[1] >= 220, target
        assert max(alpha.getpixel(point) for point in ((0, 0), (0, 19), (19, 0), (19, 19))) <= 3
        data = io.BytesIO()
        image.save(data, format='PNG')
        rendered = data.getvalue()
        digest = hashlib.sha256(rendered).hexdigest()
        assert digest not in hashes, 'Duplicate faction artwork'
        hashes.add(digest)
        if args.write:
            target.write_bytes(rendered)
            item['destination_sha256'] = digest
        elif not target.is_file() or target.read_bytes() != rendered or item.get('destination_sha256') != digest:
            errors.append(item['destination'])
    if args.write:
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if errors:
        raise SystemExit('Stale faction icons: ' + ', '.join(errors))
    print('PASS: 9 unique complete icons; 20x20 RGBA; transparent edges; source and output hashes verified.')


if __name__ == '__main__':
    main()
