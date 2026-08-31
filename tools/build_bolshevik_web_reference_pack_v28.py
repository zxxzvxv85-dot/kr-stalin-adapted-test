from __future__ import annotations

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
WORKSHOP_ROOT = ROOT.parent
KR_GOALS = WORKSHOP_ROOT / "1521695605/gfx/interface/goals"
PACKAGE_DIR = ROOT / "output/imagegen/KR_Bolshevik_8_Focus_Icons_Web_Test_v28"

BACKGROUND = (7, 20, 24, 255)
ICON_SIZE = 100
GAP = 12
MARGIN = 12
COLUMNS = 4

SHEETS = {
    "05_OFFICIAL_KR_RUSSIAN_SOCIALIST_REFERENCE_SHEET.png": [
        "RUS_union_of_peasants_and_workers.png",
        "RUS_red_flag_over_kremlin.png",
        "RUS_socialist_democracy.png",
        "RUS_true_russian_socialism.png",
        "RUS_revolution_in_spirit.png",
        "RUS_centralise_party.png",
        "RUS_rebuild_eser_party.png",
        "RUS_moscow_economic_council.png",
        "RUS_collective_farms.png",
        "RUS_european_russia_industry.png",
        "RUS_urals_industry.png",
        "RUS_siberia_industry.png",
        "RUS_soldier_with_flag.png",
        "RUS_army_socialist.png",
        "RUS_navy_socialist.png",
        "RUS_airforce_socialist.png",
    ],
    "06_OFFICIAL_KR_PARTY_AND_POLITICAL_REFERENCE_SHEET.png": [
        "CHI_the_party_state.png",
        "generic_workers_democracy.png",
        "generic_syndicalist_council.png",
        "generic_revolutionary_government.png",
        "generic_parliamentary_syndicalism.png",
        "generic_spreading_the_revolution.png",
        "generic_union_agreement.png",
        "generic_syndicalism.png",
        "generic_red_guard.png",
        "generic_syndicalist_army_soldiers.png",
        "generic_farmer_and_worker.png",
        "generic_female_workers.png",
        "generic_workers_rights.png",
        "generic_democratic_socialism.png",
        "generic_market_socialism.png",
        "generic_solidarity.png",
    ],
    "07_OFFICIAL_KR_INDUSTRY_AND_LABOUR_REFERENCE_SHEET.png": [
        "generic_seize_press.png",
        "generic_seize_railway.png",
        "generic_railway_construction.png",
        "generic_railroad.png",
        "generic_heavy_industry.png",
        "generic_medium_industry.png",
        "generic_light_industry.png",
        "generic_improve_industry.png",
        "generic_takeover_industries.png",
        "generic_industry_reallocation.png",
        "generic_electricity.png",
        "generic_lightbulb.png",
        "generic_syndicalist_workers.png",
        "generic_integralist_workers.png",
        "RUS_central_asia_industry.png",
        "RUS_central_asia_mining.png",
    ],
    "08_OFFICIAL_KR_FRAME_AND_MATERIAL_REFERENCE_SHEET.png": [
        "RUS_radsocs.png",
        "RUS_syndies.png",
        "RUS_maximalist.png",
        "RUS_VST.png",
        "RUS_union_of_peasants_and_workers.png",
        "RUS_red_flag_over_kremlin.png",
        "RUS_revolution_in_spirit.png",
        "RUS_true_russian_socialism.png",
        "generic_syndicalism.png",
        "generic_workers_democracy.png",
        "generic_syndicalist_council.png",
        "generic_revolutionary_government.png",
        "CHI_the_party_state.png",
        "FRA_parti_socialiste_unifie.png",
        "ENG_communist_workers_group.png",
        "ENG_syndicalist_labour_party.png",
    ],
}


def padded_icon(path: Path) -> Image.Image:
    source = Image.open(path).convert("RGBA")
    if source.width > ICON_SIZE or source.height > ICON_SIZE:
        scale = min(ICON_SIZE / source.width, ICON_SIZE / source.height)
        source = source.resize(
            (round(source.width * scale), round(source.height * scale)),
            Image.Resampling.LANCZOS,
        )
    icon = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    icon.alpha_composite(source, ((ICON_SIZE - source.width) // 2, (ICON_SIZE - source.height) // 2))
    return icon


def build_sheet(filenames: list[str]) -> Image.Image:
    rows = (len(filenames) + COLUMNS - 1) // COLUMNS
    width = MARGIN * 2 + COLUMNS * ICON_SIZE + (COLUMNS - 1) * GAP
    height = MARGIN * 2 + rows * ICON_SIZE + (rows - 1) * GAP
    sheet = Image.new("RGBA", (width, height), BACKGROUND)

    for index, filename in enumerate(filenames):
        path = KR_GOALS / filename
        if not path.exists():
            raise FileNotFoundError(path)
        column = index % COLUMNS
        row = index // COLUMNS
        x = MARGIN + column * (ICON_SIZE + GAP)
        y = MARGIN + row * (ICON_SIZE + GAP)
        sheet.alpha_composite(padded_icon(path), (x, y))
    return sheet


def main() -> None:
    PACKAGE_DIR.mkdir(parents=True, exist_ok=True)
    for output_name, filenames in SHEETS.items():
        output_path = PACKAGE_DIR / output_name
        sheet = build_sheet(filenames)
        sheet.save(output_path)
        print(f"{output_name}: {sheet.width}x{sheet.height}, {len(filenames)} official icons")


if __name__ == "__main__":
    main()
