"""Deterministic UI primitives and packed copies of existing game icons.

HOI4 rendered texture-free progress sprites black at the wrong size. Normal
single-frame sprites now read explicit PNGs. Atlases keep existing icon art and
display sizes while replacing thousands of hidden widgets. No writes on import.
"""
from __future__ import annotations
import struct
import zlib
import io
import os
from pathlib import Path
from PIL import Image
from industrial_planning_catalog import PLANTS

ASSET_DIR='gfx/interface/RUS_factory_planning'
LEVEL_COLOURS={0:(38,41,41),1:(46,99,64),2:(43,82,128),3:(138,99,38)}
COLOUR_SPRITES={f'grade_{level}':(36,36,rgb) for level,rgb in LEVEL_COLOURS.items()}
COLOUR_SPRITES.update({f'legend_{level}':(16,16,LEVEL_COLOURS[level]) for level in (1,2,3)})
COLOUR_SPRITES.update(rock_fill=(36,36,(18,19,20)),hub_fill=(36,36,(99,43,36)),
    selection_h=(40,2,(242,194,89)),selection_v=(2,40,(242,194,89)))


def solid_png(width,height,rgb):
    """Encode an RGBA UI primitive with a fully opaque alpha channel."""
    return rgba_png(width,height,(b'\0'+bytes((*rgb,255))*width)*height)


def rgba_png(width,height,pixels):
    def chunk(kind,data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))
    header=struct.pack('>IIBBBBB',width,height,8,6,0,0,0)
    return (b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',header)
        +chunk(b'IDAT',zlib.compress(pixels,9))+chunk(b'IEND',b''))


def render_assets():
    outputs={f'{ASSET_DIR}/{key}.png':solid_png(w,h,rgb)
        for key,(w,h,rgb) in COLOUR_SPRITES.items()}
    # One transparent-centred outline replaces four separate edge widgets.
    edge=bytes((242,194,89,255));clear=bytes(4)
    pixels=b''.join(b'\0'+b''.join(edge if min(x,y,39-x,39-y)<2 else clear
        for x in range(40)) for y in range(40))
    outputs[f'{ASSET_DIR}/selection.png']=rgba_png(40,40,pixels)
    root=Path(__file__).resolve().parents[1]
    roots=(root,Path(os.environ.get('HOI4_KR_ROOT',root.parent/'1521695605')),
        Path(os.environ.get('HOI4_GAME_ROOT',root.parents[3]/'common/Hearts of Iron IV')))
    def atlas(kinds):
        sheet=Image.new('RGBA',(28*len(kinds),28))
        for index,kind in enumerate(kinds):
            if kind is None:continue
            source=next(r/PLANTS[kind]['icon'] for r in roots if (r/PLANTS[kind]['icon']).is_file())
            with Image.open(source) as img:
                size=tuple(round(d*28/max(img.size)) for d in img.size)
                sheet.alpha_composite(img.convert('RGBA').resize(size,Image.Resampling.LANCZOS),(28*index,0))
        out=io.BytesIO();sheet.save(out,format='PNG',compress_level=9)
        return out.getvalue()
    assert sorted(PLANTS)==list(range(1,len(PLANTS)+1))
    outputs[f'{ASSET_DIR}/facilities.png']=atlas(range(1,len(PLANTS)+1))
    # Frame numbers directly match persistent terrain IDs, including empty slots.
    deposits={p['terrain']:kind for kind,p in PLANTS.items() if p['terrain']}
    outputs[f'{ASSET_DIR}/deposits.png']=atlas([deposits.get(t) for t in range(1,9)])
    return outputs
