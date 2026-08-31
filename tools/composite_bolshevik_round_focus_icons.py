from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "output/imagegen/RUS_kamenev_bolshevik_eight_complete_icons_v6"
FRAME_PATH = ROOT / "gfx/interface/goals/frames/RUS_bolshevik_political_focus_frame_standard.png"
GUIDE_PATH = ROOT / "tmp/imagegen/RUS_kamenev_bolshevik_large_canvas_guide_1672x941_v9.png"
OUTPUT_DIR = ROOT / "output/imagegen/RUS_kamenev_bolshevik_round_100px_v10"
CONTACT_SHEET = ROOT / "output/imagegen/RUS_kamenev_bolshevik_round_100px_contact_v10.png"
TREE_PREVIEW = ROOT / "output/imagegen/RUS_kamenev_bolshevik_round_exact_100px_tree_v10.png"

ICON_SIZE = 100
PLATE_SIZE = 78
APERTURE = (13, 13, 87, 87)
BACKGROUND = (6, 19, 23, 255)

ICONS = [
    ("RUS_kamenev_bol_register_returning_members", (795, 61)),
    ("RUS_kamenev_bol_restore_pravda", (571, 212)),
    ("RUS_kamenev_bol_restore_central_bureau", (1019, 212)),
    ("RUS_kamenev_bol_unify_planning_apparatus", (347, 372)),
    ("RUS_kamenev_bol_rebuild_factory_cells", (795, 372)),
    ("RUS_kamenev_bol_railway_telegraph_bureau", (571, 531)),
    ("RUS_kamenev_bol_win_vst_majority", (1019, 531)),
    ("RUS_kamenev_bol_undissolved_central_committee", (795, 694)),
]


def build_icon(source: Image.Image, frame: Image.Image) -> Image.Image:
    plate = source.convert("RGBA").resize((PLATE_SIZE, PLATE_SIZE), Image.Resampling.LANCZOS)
    artwork = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), BACKGROUND)
    offset = (ICON_SIZE - PLATE_SIZE) // 2
    artwork.alpha_composite(plate, (offset, offset))

    aperture_mask = Image.new("L", (ICON_SIZE, ICON_SIZE), 0)
    ImageDraw.Draw(aperture_mask).ellipse(APERTURE, fill=255)
    artwork.putalpha(aperture_mask)

    result = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    result.alpha_composite(artwork)
    result.alpha_composite(frame)
    return result


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    frame = Image.open(FRAME_PATH).convert("RGBA").resize(
        (ICON_SIZE, ICON_SIZE), Image.Resampling.LANCZOS
    )
    contact = Image.new("RGBA", (400, 200), BACKGROUND)
    tree = Image.open(GUIDE_PATH).convert("RGBA")

    for index, (name, target_xy) in enumerate(ICONS):
        source = Image.open(SOURCE_DIR / f"{name}.png")
        icon = build_icon(source, frame)
        icon.save(OUTPUT_DIR / f"{name}.png", optimize=True)
        contact.alpha_composite(icon, ((index % 4) * ICON_SIZE, (index // 4) * ICON_SIZE))
        tree.alpha_composite(icon, target_xy)

    contact.convert("RGB").save(CONTACT_SHEET, optimize=True)
    tree.convert("RGB").save(TREE_PREVIEW, optimize=True)


if __name__ == "__main__":
    main()
