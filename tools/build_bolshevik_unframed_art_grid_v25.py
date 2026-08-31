from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
WORKSHOP_ROOT = ROOT.parent
KR_GOALS = WORKSHOP_ROOT / "1521695605/gfx/interface/goals"
TMP_DIR = ROOT / "tmp/imagegen"
OUTPUT_DIR = ROOT / "output/imagegen"

CANVAS_SIZE = (1672, 941)
CHROMA = (0, 255, 0, 255)
PLATE_COLOR = (38, 35, 31, 255)
PLATE_DIAMETER = 180
EDIT_SIZE = 250

CENTERS = [
    (270, 240), (644, 240), (1018, 240), (1392, 240),
    (270, 701), (644, 701), (1018, 701), (1392, 701),
]

REFERENCES = [
    "RUS_union_of_peasants_and_workers.png",
    "generic_seize_press.png",
    "CHI_the_party_state.png",
    "ANQ_northern_school.png",
    "generic_syndicalist_workers.png",
    "generic_seize_railway.png",
    "generic_workers_democracy.png",
    "RUS_soldier_with_flag.png",
]

EDIT_TARGET = TMP_DIR / "RUS_kamenev_bolshevik_unframed_art_grid_1672x941_v25.png"
EDIT_MASK = TMP_DIR / "RUS_kamenev_bolshevik_unframed_art_grid_mask_1672x941_v25.png"
STYLE_REFERENCE = TMP_DIR / "RUS_kamenev_bolshevik_official_KR_style_reference_1672x941_v25.png"
FRAME_REFERENCE = OUTPUT_DIR / "RUS_socialist_shared_frame_extracted_from_KR.png"
TARGET_PREVIEW = OUTPUT_DIR / "RUS_kamenev_bolshevik_unframed_art_grid_1672x941_v25.png"
STYLE_PREVIEW = OUTPUT_DIR / "RUS_kamenev_bolshevik_official_KR_style_reference_1672x941_v25.png"
MASK_PREVIEW = OUTPUT_DIR / "RUS_kamenev_bolshevik_unframed_art_grid_mask_preview_v25.png"


def main() -> None:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    target = Image.new("RGBA", CANVAS_SIZE, CHROMA)
    target_draw = ImageDraw.Draw(target)
    mask = Image.new("RGBA", CANVAS_SIZE, (255, 255, 255, 255))
    mask_draw = ImageDraw.Draw(mask)
    mask_preview = target.copy()
    mask_preview_draw = ImageDraw.Draw(mask_preview)

    for center_x, center_y in CENTERS:
        radius = PLATE_DIAMETER // 2
        target_draw.ellipse(
            (center_x - radius, center_y - radius, center_x + radius, center_y + radius),
            fill=PLATE_COLOR,
        )

        edit_radius = EDIT_SIZE // 2
        edit_box = (
            center_x - edit_radius,
            center_y - edit_radius,
            center_x + edit_radius - 1,
            center_y + edit_radius - 1,
        )
        mask_draw.rectangle(edit_box, fill=(255, 255, 255, 0))

    mask_preview = target.copy()
    mask_preview_draw = ImageDraw.Draw(mask_preview)
    for center_x, center_y in CENTERS:
        edit_radius = EDIT_SIZE // 2
        mask_preview_draw.rectangle(
            (
                center_x - edit_radius,
                center_y - edit_radius,
                center_x + edit_radius - 1,
                center_y + edit_radius - 1,
            ),
            outline=(255, 255, 255, 255),
            width=2,
        )

    style = Image.new("RGBA", CANVAS_SIZE, (7, 20, 24, 255))
    for reference_name, (center_x, center_y) in zip(REFERENCES, CENTERS):
        reference = Image.open(KR_GOALS / reference_name).convert("RGBA")
        scale = min(190 / reference.width, 190 / reference.height)
        enlarged = reference.resize(
            (round(reference.width * scale), round(reference.height * scale)),
            Image.Resampling.LANCZOS,
        )
        style.alpha_composite(enlarged, (center_x - enlarged.width // 2, center_y - enlarged.height // 2))

    target.save(EDIT_TARGET)
    target.save(TARGET_PREVIEW)
    mask.save(EDIT_MASK)
    mask_preview.save(MASK_PREVIEW)
    style.save(STYLE_REFERENCE)
    style.save(STYLE_PREVIEW)

    print(f"edit target: {EDIT_TARGET}")
    print(f"edit mask: {EDIT_MASK}")
    print(f"style reference: {STYLE_REFERENCE}")
    print(f"fixed frame reference: {FRAME_REFERENCE}")
    print(f"target preview: {TARGET_PREVIEW}")
    print(f"style preview: {STYLE_PREVIEW}")
    print(f"mask preview: {MASK_PREVIEW}")


if __name__ == "__main__":
    main()
