from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
WORKSHOP_ROOT = ROOT.parent
KR_GOALS = WORKSHOP_ROOT / "1521695605/gfx/interface/goals"
MOD_GOALS = ROOT / "gfx/interface/goals/RUS_kamenev_politics"
SOURCE_PACK = ROOT / "tools/imagegen_prompts/psr_web_pack_v1"
PACKAGE_DIR = ROOT / "output/imagegen/KR_PSR_11_Focus_Icons_Web_Test_v1"

CANVAS_SIZE = (3344, 1888)
CHROMA = (0, 255, 0, 255)
SLOT_COLOR = (38, 35, 31, 255)
ICON_SIZE = 100
SHEET_BACKGROUND = (19, 24, 23, 255)
SHEET_GAP = 12
SHEET_MARGIN = 12
SHEET_COLUMNS = 4

CENTERS = [
    (512, 384),
    (1280, 384),
    (2048, 384),
    (2816, 384),
    (512, 944),
    (1280, 944),
    (2048, 944),
    (2816, 944),
    (896, 1504),
    (1672, 1504),
    (2448, 1504),
]

PSR_ICONS = [
    "RUS_kamenev_psr_rebuild_central_committee.png",
    "RUS_kamenev_psr_absorb_democratic_parties.png",
    "RUS_kamenev_psr_preserve_land_committees.png",
    "RUS_kamenev_psr_claim_internal_affairs.png",
    "RUS_kamenev_psr_defend_revolutionary_democracy.png",
    "RUS_kamenev_psr_land_socialisation_bill.png",
    "RUS_kamenev_psr_peasant_congress.png",
    "RUS_kamenev_psr_final_party_congress.png",
    "RUS_kamenev_psr_cooperatives_fair_grain_prices.png",
    "RUS_kamenev_psr_local_self_government.png",
    "RUS_kamenev_psr_agrarian_socialism.png",
]

REFERENCE_SHEETS = {
    "05_OFFICIAL_KR_RUSSIAN_ESER_AND_SOCIALIST_REFERENCE_SHEET.png": [
        "RUS_radsocs.png",
        "RUS_rebuild_eser_party.png",
        "RUS_union_of_peasants_and_workers.png",
        "RUS_true_russian_socialism.png",
        "RUS_socialist_democracy.png",
        "RUS_revolution_in_spirit.png",
        "RUS_collective_farms.png",
        "RUS_moscow_economic_council.png",
        "agrarian_socialism.png",
        "CRO_peasant_republic.png",
        "generic_farmer.png",
        "generic_farmer_and_worker.png",
        "generic_land_reform.png",
        "socialist_constitution.png",
        "Socialist_Law.png",
        "commune_politics.png",
    ],
    "06_OFFICIAL_KR_LAND_RURAL_AND_COOPERATIVE_REFERENCE_SHEET.png": [
        "agrarian_reform.png",
        "OTT_Land_Reform.png",
        "GER_Agrarian_Parties.png",
        "FRA_ruralism.png",
        "BEL_Cooperative.png",
        "ENG_cooperative_party.png",
        "generic_market_socialism.png",
        "russian_cooperation.png",
        "LEP_subsidize_villages.png",
        "ANQ_rural_outreach.png",
        "generic_farmer.png",
        "ACC_Farmer_Labour.png",
        "RUS_collective_farms.png",
        "RUS_war_on_peasants.png",
        "MEX_Partido_Nacional_Agrarista.png",
        "CRO_peasant_republic.png",
    ],
    "07_OFFICIAL_KR_PARTY_DEMOCRACY_AND_MILITIA_REFERENCE_SHEET.png": [
        "BRA_congress.png",
        "FRA_Internationale_Congress.png",
        "generic_workers_democracy.png",
        "generic_democratic_socialism.png",
        "generic_union_agreement.png",
        "generic_solidarity.png",
        "socialist_constitution.png",
        "Socialist_Law.png",
        "integrate_the_militia.png",
        "integrate_workers_militia.png",
        "generic_red_guard.png",
        "agrarian_soldiers.png",
        "RUS_rebuild_eser_party.png",
        "RUS_socialist_democracy.png",
        "RUS_centralise_party.png",
        "RUS_union_of_peasants_and_workers.png",
    ],
    "08_OFFICIAL_KR_ROUNDED_FRAME_AND_MATERIAL_REFERENCE_SHEET.png": [
        "RUS_radsocs.png",
        "RUS_rebuild_eser_party.png",
        "RUS_true_russian_socialism.png",
        "RUS_union_of_peasants_and_workers.png",
        "generic_farmer.png",
        "agrarian_socialism.png",
        "CRO_peasant_republic.png",
        "FRA_ruralism.png",
        "BEL_Cooperative.png",
        "ENG_rural_party.png",
        "generic_democratic_socialism.png",
        "commune_politics.png",
        "generic_solidarity.png",
        "socialist_constitution.png",
        "generic_market_socialism.png",
        "RUS_socialist_democracy.png",
    ],
}


def slot_box(center: tuple[int, int]) -> tuple[int, int, int, int]:
    radius = ICON_SIZE // 2
    return (
        center[0] - radius,
        center[1] - radius,
        center[0] + radius - 1,
        center[1] + radius - 1,
    )


def fit_icon(path: Path, size: int = ICON_SIZE) -> Image.Image:
    source = Image.open(path).convert("RGBA")
    scale = min(size / source.width, size / source.height)
    source = source.resize(
        (round(source.width * scale), round(source.height * scale)),
        Image.Resampling.LANCZOS,
    )
    result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    result.alpha_composite(source, ((size - source.width) // 2, (size - source.height) // 2))
    return result


def build_edit_target() -> Image.Image:
    target = Image.new("RGBA", CANVAS_SIZE, CHROMA)
    draw = ImageDraw.Draw(target)
    for center in CENTERS:
        draw.ellipse(slot_box(center), fill=SLOT_COLOR)
    return target


def build_subject_reference() -> Image.Image:
    canvas = Image.new("RGBA", CANVAS_SIZE, CHROMA)
    reference_size = 300
    for center, filename in zip(CENTERS, PSR_ICONS, strict=True):
        path = MOD_GOALS / filename
        if not path.exists():
            raise FileNotFoundError(path)
        icon = fit_icon(path, reference_size)
        canvas.alpha_composite(
            icon,
            (center[0] - reference_size // 2, center[1] - reference_size // 2),
        )
    return canvas


def build_reference_sheet(filenames: list[str]) -> Image.Image:
    rows = (len(filenames) + SHEET_COLUMNS - 1) // SHEET_COLUMNS
    width = SHEET_MARGIN * 2 + SHEET_COLUMNS * ICON_SIZE + (SHEET_COLUMNS - 1) * SHEET_GAP
    height = SHEET_MARGIN * 2 + rows * ICON_SIZE + (rows - 1) * SHEET_GAP
    sheet = Image.new("RGBA", (width, height), SHEET_BACKGROUND)

    for index, filename in enumerate(filenames):
        path = KR_GOALS / filename
        if not path.exists():
            raise FileNotFoundError(path)
        x = SHEET_MARGIN + (index % SHEET_COLUMNS) * (ICON_SIZE + SHEET_GAP)
        y = SHEET_MARGIN + (index // SHEET_COLUMNS) * (ICON_SIZE + SHEET_GAP)
        sheet.alpha_composite(fit_icon(path), (x, y))
    return sheet


def copy_source(name: str, output_name: str | None = None) -> None:
    source = SOURCE_PACK / name
    if not source.exists():
        raise FileNotFoundError(source)
    shutil.copy2(source, PACKAGE_DIR / (output_name or name))


def main() -> None:
    PACKAGE_DIR.mkdir(parents=True, exist_ok=True)

    build_edit_target().save(PACKAGE_DIR / "01_EDIT_TARGET_exact_100px_slots_3344x1888.png")
    build_subject_reference().save(PACKAGE_DIR / "02_SUBJECT_REFERENCE_current_11_icons.png")

    previous_pack = ROOT / "output/imagegen/KR_Bolshevik_8_Focus_Icons_Web_Test_v28"
    shutil.copy2(
        previous_pack / "03_STYLE_REFERENCE_official_KR_icons.png",
        PACKAGE_DIR / "03_STYLE_REFERENCE_official_KR_icons.png",
    )
    shutil.copy2(
        KR_GOALS / "RUS_radsocs.png",
        PACKAGE_DIR / "04_FRAME_STRUCTURE_REFERENCE_RUS_ESER.png",
    )

    for output_name, filenames in REFERENCE_SHEETS.items():
        build_reference_sheet(filenames).save(PACKAGE_DIR / output_name)

    copy_source("PROMPT_COPY_TO_WEB.txt")
    copy_source("README_使用说明.txt")
    copy_source("REFERENCE_INDEX.txt")

    archive = shutil.make_archive(str(PACKAGE_DIR), "zip", PACKAGE_DIR)
    print(f"package: {PACKAGE_DIR}")
    print(f"archive: {archive}")
    print(f"canvas: {CANVAS_SIZE[0]}x{CANVAS_SIZE[1]}")
    print(f"slots: {len(CENTERS)} at {ICON_SIZE}x{ICON_SIZE}")


if __name__ == "__main__":
    main()
