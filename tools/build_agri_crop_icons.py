"""Prepare generated crop cutouts and offline small-size visual proofs."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "output/imagegen/crop-icons-20260907"
DEST = ROOT / "gfx/interface/RUS_agri_crops"
DEST.mkdir(parents=True, exist_ok=True)
CROPS = ["wheat", "rye", "beet", "flax", "cotton"]
LABELS = ["Wheat", "Rye", "Sugar beet", "Flax", "Cotton"]
proof = Image.new("RGB", (800, 420), "#20201d")
draw = ImageDraw.Draw(proof)
font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 18)
small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 14)
draw.text((20, 14), "CROP ICONS / enlarged and native 32 px", fill="white", font=font)
metrics = {}
for index, (crop, label) in enumerate(zip(CROPS, LABELS)):
    original = Image.open(SOURCE / f"{crop}.png")
    cutout = Image.open(SOURCE / f"{crop}-cutout.png").convert("RGBA")
    bounds = cutout.getchannel("A").point(lambda a: 255 if a > 16 else 0).getbbox()
    assert bounds, f"Blank cutout: {crop}"
    cropped = cutout.crop(bounds)
    fitted = ImageOps.contain(cropped, (58, 58), Image.Resampling.LANCZOS)
    icon = Image.new("RGBA", (64, 64))
    icon.alpha_composite(fitted, ((64-fitted.width)//2, (64-fitted.height)//2))
    icon.save(DEST / f"RUS_agri_{crop}.png")
    native = icon.resize((32, 32), Image.Resampling.LANCZOS)
    alpha = native.getchannel("A")
    assert alpha.getextrema() == (0, 255), f"Invalid alpha: {crop}"
    assert sum(a > 128 for a in alpha.getdata()) > 100, f"Too little visible subject: {crop}"
    spill = sum(a > 128 and min(r, b) - g > 65 for r,g,b,a in native.getdata())
    assert spill == 0, f"Magenta contamination: {crop}"
    x = index * 156 + 16
    proof.paste(icon.resize((112, 112), Image.Resampling.LANCZOS), (x + 14, 60), icon.resize((112, 112), Image.Resampling.LANCZOS))
    draw.text((x + 18, 184), label, fill="#eeeeea", font=font)
    for y, color in [(236, "#29271f"), (306, "#d4d4d0")]:
        draw.rectangle((x, y, x + 139, y + 55), fill=color)
        proof.paste(native, (x + 54, y + 12), native)
    metrics[crop] = {"generated_size": original.size, "crop_bounds": bounds,
                     "asset_size": icon.size, "display_size": native.size,
                     "opaque_native_pixels": sum(a > 128 for a in alpha.getdata()),
                     "magenta_spill_pixels": spill}
draw.text((20, 386), "Dark and light background checks; PNG alpha preserved. Offline proof, not an in-game screenshot.", fill="#b8b8b4", font=small)
proof.save(SOURCE / "crop-icons-preview.png")
(SOURCE / "validation.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
print(json.dumps(metrics, indent=2))
