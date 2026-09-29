"""Deterministic, pixel-sized UI rectangles; no painted or composited artwork.

HOI4 rendered texture-free progress sprites black at the wrong size. Normal
single-frame sprites now read these explicit opaque PNGs. No writes on import.
"""
from __future__ import annotations
import struct
import zlib

ASSET_DIR='gfx/interface/RUS_factory_planning'
LEVEL_COLOURS={0:(38,41,41),1:(46,99,64),2:(43,82,128),3:(138,99,38)}
COLOUR_SPRITES={f'grade_{level}':(36,36,rgb) for level,rgb in LEVEL_COLOURS.items()}
COLOUR_SPRITES.update({f'legend_{level}':(16,16,LEVEL_COLOURS[level]) for level in (1,2,3)})
COLOUR_SPRITES.update(rock_fill=(36,36,(18,19,20)),hub_fill=(36,36,(99,43,36)),
    selection_h=(40,2,(242,194,89)),selection_v=(2,40,(242,194,89)))


def solid_png(width,height,rgb):
    """Encode an RGBA UI primitive with a fully opaque alpha channel."""
    def chunk(kind,data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))
    pixels=(b'\0'+bytes((*rgb,255))*width)*height
    header=struct.pack('>IIBBBBB',width,height,8,6,0,0,0)
    return (b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',header)
        +chunk(b'IDAT',zlib.compress(pixels,9))+chunk(b'IEND',b''))


def render_assets():
    return {f'{ASSET_DIR}/{key}.png':solid_png(w,h,rgb)
        for key,(w,h,rgb) in COLOUR_SPRITES.items()}
