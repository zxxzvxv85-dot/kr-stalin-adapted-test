from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output/imagegen"
SOURCE = OUTPUT_DIR / "RUS_kamenev_bolshevik_native_KR_anchors_generated_1680x944_v17.png"
OVERLAY = OUTPUT_DIR / "RUS_kamenev_bolshevik_native_KR_anchors_bounds_v17.png"
CONTACT = OUTPUT_DIR / "RUS_kamenev_bolshevik_native_KR_anchors_exact_100px_contact_v17.png"
CROP_DIR = OUTPUT_DIR / "RUS_kamenev_bolshevik_native_KR_anchors_exact_100px_v17"

NODES = [
    ("RUS_kamenev_bol_win_vst_majority", "一切权力归苏维埃", 795, 61),
    ("RUS_kamenev_bol_restore_pravda", "《真理报》重返俄罗斯", 571, 212),
    ("RUS_kamenev_bol_undissolved_central_committee", "两张党证", 1019, 212),
    ("RUS_kamenev_bol_register_returning_members", "开设党校", 347, 372),
    ("RUS_kamenev_bol_rebuild_factory_cells", "车间里的党小组", 795, 372),
    ("RUS_kamenev_bol_railway_telegraph_bureau", "铁路与电报联络局", 571, 531),
    ("RUS_kamenev_bol_unify_planning_apparatus", "设立最高纲领派联络处", 1019, 531),
    ("RUS_kamenev_bol_raise_red_flag", "高举红旗", 795, 694),
]


def font(size: int) -> ImageFont.ImageFont:
    for path in (Path("C:/Windows/Fonts/msyh.ttc"), Path("C:/Windows/Fonts/simhei.ttf")):
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def main() -> None:
    CROP_DIR.mkdir(parents=True, exist_ok=True)
    source = Image.open(SOURCE).convert("RGB")

    overlay = source.copy()
    overlay_draw = ImageDraw.Draw(overlay)
    for _, _, left, top in NODES:
        overlay_draw.rectangle((left, top, left + 99, top + 99), outline=(0, 255, 255), width=2)
    overlay.save(OVERLAY)

    contact = Image.new("RGB", (4 * 120 + 20, 2 * 140 + 20), (10, 18, 20))
    contact_draw = ImageDraw.Draw(contact)
    label_font = font(12)

    for index, (focus_id, label, left, top) in enumerate(NODES):
        crop = source.crop((left, top, left + 100, top + 100))
        crop.save(CROP_DIR / f"{focus_id}.png")

        column = index % 4
        row = index // 4
        x = 10 + column * 120
        y = 10 + row * 140
        contact.paste(crop, (x, y))
        contact_draw.rectangle((x - 1, y - 1, x + 100, y + 100), outline=(230, 230, 220), width=1)
        box = contact_draw.textbbox((0, 0), label, font=label_font)
        text_width = box[2] - box[0]
        contact_draw.text((x + 50 - text_width // 2, y + 106), label, font=label_font, fill=(235, 235, 225))

    contact.save(CONTACT)
    print(f"source dimensions: {source.width}x{source.height}")
    print(f"bounds overlay: {OVERLAY}")
    print(f"native crop contact: {CONTACT}")
    print(f"individual crops: {CROP_DIR}")


if __name__ == "__main__":
    main()
