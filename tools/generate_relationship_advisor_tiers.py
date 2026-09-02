from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


ADVISORS = [
    {
        "group": "rkp",
        "slug": "sverdlov",
        "character": "RUS_yakov_sverdlov",
        "sprite": 13,
        "name": "RUS_relationship_scaled_sverdlov",
        "effects": {
            "civilian_intel_to_others": -15,
            "min_export": -0.10,
            "political_power_factor": 0.10,
            "consumer_goods_expected_value": -0.05,
            "political_advisor_cost_factor": -0.20,
        },
        "bop": 0.01,
        "legacy": ["RUS_relationship_scaled_sverdlov", "RUS_red_eminence_sverdlov", "KR_bolshevik_sverdlov_bop"],
    },
    {
        "group": "rkp",
        "slug": "frunze",
        "character": "RUS_mikhail_frunze",
        "sprite": 13,
        "name": "RUS_relationship_scaled_frunze",
        "effects": {
            "send_volunteer_size": 5,
            "party_popularity_stability_factor": 0.25,
            "justify_war_goal_time": -0.25,
            "experience_gain_army_factor": 0.25,
            "land_night_attack": 0.05,
        },
        "bop": 0.01,
        "legacy": ["RUS_relationship_scaled_frunze", "RUS_frunze_ideological_crusader", "KR_bolshevik_frunze_bop"],
    },
    {
        "group": "rkp",
        "slug": "kaganovich",
        "character": "RUS_lazar_kaganovich",
        "sprite": 10,
        "name": "RUS_relationship_scaled_kaganovich",
        "effects": {
            "production_cost_arms_factory_factor": -0.10,
            "production_speed_dockyard_factor": 0.15,
            "production_speed_fuel_silo_factor": 0.15,
        },
        "bop": 0.01,
        "legacy": ["RUS_relationship_scaled_kaganovich", "KR_kaganovich_war_industrialist", "KR_bolshevik_kaganovich_bop"],
    },
    {
        "group": "rkp",
        "slug": "zhdanov",
        "character": "RUS_andrei_zhdanov",
        "sprite": 13,
        "name": "RUS_relationship_scaled_zhdanov",
        "effects": {
            "stability_factor": 0.15,
            "party_popularity_stability_factor": 0.25,
            "political_power_gain": 0.25,
        },
        "bop": 0.01,
        "legacy": ["RUS_relationship_scaled_zhdanov", "RUS_ardent_revolutionary", "KR_bolshevik_zhdanov_bop"],
    },
    {
        "group": "rkp",
        "slug": "yezhov",
        "character": "RUS_nikolay_yezhov",
        "sprite": 15,
        "name": "RUS_relationship_scaled_yezhov",
        "effects": {
            "operative_slot": 2,
            "own_operative_capture_chance_factor": -0.50,
            "operation_outcome": 0.20,
            "agency_upgrade_time": -0.40,
        },
        "bop": 0.01,
        "legacy": ["RUS_relationship_scaled_yezhov", "RUS_red_domovoi", "KR_bolshevik_yezhov_bop"],
    },
    {
        "group": "rkp",
        "slug": "bukharin",
        "character": "RUS_nikolay_bukharin",
        "sprite": 10,
        "name": "RUS_relationship_scaled_bukharin",
        "effects": {
            "production_factory_efficiency_gain_factor": 0.15,
            "industrial_capacity_factory": 0.15,
            "industrial_capacity_dockyard": 0.10,
            "political_power_factor": -0.15,
        },
        "bop": 0.01,
        "legacy": ["RUS_relationship_scaled_bukharin", "RUS_bukharin_economic_theorist", "KR_bolshevik_bukharin_bop"],
    },
    {
        "group": "rkp",
        "slug": "kirov",
        "character": "RUS_sergey_kirov",
        "sprite": 13,
        "name": "RUS_relationship_scaled_kirov",
        "effects": {
            "consumer_goods_expected_value": -0.03,
            "production_speed_infrastructure_factor": 0.15,
            "production_speed_industrial_complex_factor": 0.15,
        },
        "bop": 0.01,
        "legacy": [
            "RUS_relationship_scaled_kirov",
            "KR_prince_of_petrograd",
            "KR_bolshevik_kirov_bop",
            "KR_vst_right_kirov",
        ],
    },
    {
        "group": "psr",
        "slug": "mayorov",
        "character": "RUS_ilya_mayorov",
        "sprite": 10,
        "name": "RUS_relationship_scaled_mayorov",
        "effects": {"global_building_slots_factor": 0.20, "conscription_factor": 0.05, "monthly_population": 0.20},
        "bop": -0.01,
        "legacy": ["RUS_relationship_scaled_mayorov", "KR_agricultural_economist", "RUS_psr_advisor_bonus_mayorov", "KR_spiridonist_mayorov_bop"],
    },
    {
        "group": "psr",
        "slug": "zdobnov",
        "character": "RUS_nikolay_zdobnov",
        "sprite": 13,
        "name": "RUS_relationship_scaled_zdobnov",
        "effects": {
            "mobilization_laws_cost_factor": -0.33,
            "trade_laws_cost_factor": -0.33,
            "economy_cost_factor": -0.33,
            "political_advisor_cost_factor": -0.33,
        },
        "bop": -0.01,
        "legacy": ["RUS_relationship_scaled_zdobnov", "KR_political_specialist", "RUS_psr_advisor_bonus_zdobnov", "KR_spiridonist_zdobnov_bop"],
    },
    {
        "group": "psr",
        "slug": "kamkov",
        "character": "RUS_boris_kamkov",
        "sprite": 13,
        "name": "RUS_relationship_scaled_kamkov",
        "effects": {"stability_factor": 0.10, "political_power_factor": 0.10},
        "bop": -0.01,
        "legacy": ["RUS_relationship_scaled_kamkov", "KR_socialist_idealist", "RUS_psr_advisor_bonus_kamkov", "KR_spiridonist_kamkov_bop"],
    },
    {
        "group": "psr",
        "slug": "karelin",
        "character": "RUS_vladimir_karelin",
        "sprite": 13,
        "name": "RUS_relationship_scaled_karelin",
        "effects": {"justify_war_goal_time": -0.15, "civilian_intel_factor": 0.20, "political_power_factor": 0.10},
        "bop": -0.01,
        "legacy": ["RUS_relationship_scaled_karelin", "KR_leading_diplomat", "RUS_psr_advisor_bonus_karelin", "KR_spiridonist_karelin_bop"],
    },
    {
        "group": "psr",
        "slug": "elyashevich",
        "character": "RUS_aleksandr_elyashevich",
        "sprite": 10,
        "name": "RUS_relationship_scaled_elyashevich",
        "effects": {"production_speed_buildings_factor": 0.10},
        "bop": -0.01,
        "legacy": ["RUS_relationship_scaled_elyashevich", "KR_industrialiser", "RUS_psr_advisor_bonus_elyashevich", "KR_spiridonist_elyashevich_bop"],
    },
    {
        "group": "psr",
        "slug": "steinberg",
        "character": "RUS_isaak_steinberg",
        "sprite": 12,
        "name": "RUS_relationship_scaled_steinberg",
        "effects": {"global_building_slots_factor": 0.20, "industrial_capacity_factory": 0.05},
        "bop": -0.01,
        "legacy": ["RUS_relationship_scaled_steinberg", "KR_cooperatives_proponent_steinberg", "RUS_psr_advisor_bonus_steinberg", "KR_sr_steinberg_bop"],
    },
    {
        "group": "psr",
        "slug": "sattel",
        "character": "RUS_yevgeny_sattel",
        "sprite": 12,
        "name": "RUS_relationship_scaled_sattel",
        "effects": {"war_support_factor": 0.05, "send_volunteer_size": 2, "compliance_growth": 0.15},
        "bop": -0.01,
        "legacy": ["RUS_relationship_scaled_sattel", "KR_internationalist_propagandist", "RUS_psr_advisor_bonus_sattel", "KR_sr_sattel_bop"],
    },
    {
        "group": "psr",
        "slug": "blyumkin",
        "character": "RUS_yakov_blyumkin",
        "sprite": 15,
        "name": "RUS_relationship_scaled_blyumkin",
        "effects": {"operative_slot": 2, "own_operative_capture_chance_factor": -0.50, "operation_outcome": 0.20, "agency_upgrade_time": -0.40},
        "bop": -0.01,
        "legacy": ["RUS_relationship_scaled_blyumkin", "KR_legendary_rogue", "RUS_psr_advisor_bonus_blyumkin", "KR_sr_blyumkin_bop"],
    },
    {
        "group": "max",
        "slug": "ustinov",
        "character": "RUS_aleksey_ustinov",
        "sprite": 13,
        "name": "RUS_relationship_scaled_ustinov",
        "stage_effects": [
            {
                "consumer_goods_expected_value": -0.03,
                "stability_factor": -0.05,
                "production_speed_buildings_factor": 0.05,
            },
            {
                "consumer_goods_expected_value": -0.01,
                "stability_factor": -0.03,
                "production_speed_buildings_factor": 0.07,
                "production_cost_infrastructure_factor": -0.04,
            },
            {
                "consumer_goods_expected_value": 0.01,
                "stability_factor": -0.01,
                "production_speed_buildings_factor": 0.09,
                "production_cost_infrastructure_factor": -0.08,
            },
            {
                "consumer_goods_expected_value": 0.02,
                "stability_factor": 0.01,
                "production_speed_buildings_factor": 0.11,
                "production_cost_infrastructure_factor": -0.12,
            },
            {
                "consumer_goods_expected_value": 0.04,
                "stability_factor": 0.03,
                "production_speed_buildings_factor": 0.13,
                "production_cost_infrastructure_factor": -0.16,
            },
            {
                "consumer_goods_expected_value": 0.05,
                "stability_factor": 0.05,
                "production_speed_buildings_factor": 0.15,
                "production_cost_infrastructure_factor": -0.20,
            },
        ],
        "legacy": ["RUS_relationship_scaled_ustinov", "RUS_muromets"],
    },
    {
        "group": "max",
        "slug": "kolegayev",
        "character": "RUS_andrey_kolegayev",
        "sprite": 13,
        "name": "RUS_relationship_scaled_kolegayev",
        "effects": {"global_building_slots_factor": 0.20, "political_power_factor": 0.10},
        "legacy": ["RUS_relationship_scaled_kolegayev", "KR_peasant_populist_3"],
    },
    {
        "group": "max",
        "slug": "kakhovskaya",
        "character": "RUS_irina_kakhovskaya",
        "sprite": 13,
        "name": "RUS_relationship_scaled_kakhovskaya",
        "effects": {"resistance_damage_to_garrison": -0.10, "resistance_target": -0.05, "compliance_gain": 0.01},
        "legacy": ["RUS_relationship_scaled_kakhovskaya", "KR_princess_of_terror"],
    },
]


GROUP_TIERS = {"rkp": range(11), "psr": range(11), "max": range(6)}
GROUP_VARIABLES = {"rkp": "RUS_rkp_advisor_trait_tier", "psr": "RUS_psr_advisor_trait_tier", "max": "RUS_max_advisor_trait_tier"}
IDENTITY_TRAITS = {
    "sverdlov": "KR_bolshevik_sverdlov",
    "frunze": "KR_bolshevik_frunze",
    "kaganovich": "KR_bolshevik_kaganovich",
    "zhdanov": "KR_bolshevik_zhdanov",
    "yezhov": "KR_bolshevik_yezhov",
    "bukharin": "KR_bolshevik_bukharin",
    "kirov": "KR_bolshevik_kirov",
    "mayorov": "KR_spiridonist_mayorov",
    "zdobnov": "KR_spiridonist_zdobnov",
    "kamkov": "KR_spiridonist_kamkov",
    "karelin": "KR_spiridonist_karelin",
    "elyashevich": "KR_spiridonist_elyashevich",
    "steinberg": "KR_sr_steinberg",
    "sattel": "KR_sr_sattel",
    "blyumkin": "KR_sr_blyumkin",
    "ustinov": "KR_maximalist_ustinov",
    "kolegayev": "KR_maximalist_kolegayev",
    "kakhovskaya": "KR_maximalist_kakhovskaya",
}


def trait_id(advisor: dict, tier: int) -> str:
    return f"RUS_relationship_scaled_{advisor['slug']}_tier_{tier}"


def display_trait_id(advisor: dict) -> str:
    return f"RUS_relationship_display_{advisor['slug']}"


def number(value: float) -> str:
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    return "0" if text == "-0" else text


def effect_factor(group: str, tier: int) -> float:
    if group == "rkp":
        return (tier + 10) / 20
    if group == "psr":
        return 1.5 * (tier + 10) / 20
    # Maximalist advisers grow from the old minimum to 150% of the old maximum.
    return (7 * tier + 10) / 30


def render_traits() -> str:
    lines = ["# Generated by tools/generate_relationship_advisor_tiers.py.", "leader_traits = {"]
    for advisor in ADVISORS:
        lines.extend([
            f"\t# {advisor['character']}",
            f"\t{display_trait_id(advisor)} = {{",
            "\t\trandom = no",
            f"\t\tsprite = {advisor['sprite']}",
            "\t}",
            "",
        ])
        for tier in GROUP_TIERS[advisor["group"]]:
            lines.extend([
                f"\t{trait_id(advisor, tier)} = {{",
                "\t\trandom = no",
                f"\t\tsprite = {advisor['sprite']}",
            ])
            if "stage_effects" in advisor:
                effects = advisor["stage_effects"][tier]
                for modifier, value in effects.items():
                    lines.append(f"\t\t{modifier} = {number(value)}")
            else:
                factor = effect_factor(advisor["group"], tier)
                for modifier, base in advisor["effects"].items():
                    lines.append(f"\t\t{modifier} = {number(base * factor)}")
            if advisor.get("bop", 0) > 0:
                lines.append("\t\tcustom_modifier_tooltip = RUS_kamenev_bop_bolshevik_advisor_weekly_tt")
            elif advisor.get("bop", 0) < 0:
                lines.append("\t\tcustom_modifier_tooltip = RUS_kamenev_bop_psr_advisor_weekly_tt")
            if advisor["group"] == "max":
                lines.append("\t\tcustom_modifier_tooltip = RUS_kamenev_bop_maximalist_advisor_weekly_tt")
                if tier < 5:
                    lines.append("\t\tcustom_modifier_tooltip = RUS_maximalist_advisor_land_reform_monthly_tt")
            lines.extend(["\t}", ""])
    lines.append("}")
    return "\n".join(lines) + "\n"


def remove_if_present(advisor: dict, trait: str, indent: str = "\t\t") -> list[str]:
    character = advisor["character"]
    return [
        f"{indent}if = {{",
        f"{indent}\tlimit = {{ has_trait = {trait} }}",
        f"{indent}\tremove_trait = {{ character = {character} slot = political_advisor trait = {trait} }}",
        f"{indent}}}",
    ]


def render_legacy_cleanup() -> list[str]:
    lines = ["RUS_stalin_clear_legacy_relationship_advisor_traits = {"]
    for advisor in ADVISORS:
        lines.append(f"\t{advisor['character']} = {{")
        for trait in advisor["legacy"]:
            lines.extend(remove_if_present(advisor, trait))
        identity = IDENTITY_TRAITS.get(advisor["slug"])
        if identity:
            lines.extend([
                "\t\tif = {",
                f"\t\t\tlimit = {{ NOT = {{ has_trait = {identity} }} }}",
                f"\t\t\tadd_trait = {{ character = {advisor['character']} slot = political_advisor trait = {identity} }}",
                "\t\t}",
            ])
        lines.append("\t}")
    lines.extend(["}", ""])
    return lines


def tier_flag(group: str, tier: int) -> str:
    return f"RUS_{group}_advisor_trait_tier_{tier}_active"


def render_tier_setters() -> list[str]:
    lines: list[str] = []
    for group, tiers in GROUP_TIERS.items():
        group_advisors = [advisor for advisor in ADVISORS if advisor["group"] == group]
        lines.append(f"RUS_stalin_clear_{group}_advisor_trait_tiers = {{")
        for advisor in group_advisors:
            lines.append(f"\t{advisor['character']} = {{")
            for tier in tiers:
                lines.extend(remove_if_present(advisor, trait_id(advisor, tier)))
            lines.append("\t}")
        lines.extend(["}", ""])
        for tier in tiers:
            lines.append(f"RUS_stalin_set_{group}_advisor_trait_tier_{tier} = {{")
            lines.append(f"\tRUS_stalin_clear_{group}_advisor_trait_tiers = yes")
            for advisor in group_advisors:
                lines.extend([
                    f"\t{advisor['character']} = {{",
                    f"\t\tadd_trait = {{ character = {advisor['character']} slot = political_advisor trait = {trait_id(advisor, tier)} }}",
                    "\t}",
                ])
            for old_tier in tiers:
                lines.append(f"\tclr_country_flag = {tier_flag(group, old_tier)}")
            lines.append(f"\tset_country_flag = {tier_flag(group, tier)}")
            lines.extend(["}", ""])
    return lines


def render_selector(group: str) -> list[str]:
    variable = GROUP_VARIABLES[group]
    tiers = list(GROUP_TIERS[group])
    lines = [f"RUS_stalin_apply_{group}_advisor_trait_tier = {{"]
    for index, tier in enumerate(tiers):
        if tier == tiers[-1]:
            lines.extend([
                "\telse = {",
                "\t\tif = {",
                f"\t\t\tlimit = {{ NOT = {{ has_country_flag = {tier_flag(group, tier)} }} }}",
                f"\t\t\tRUS_stalin_set_{group}_advisor_trait_tier_{tier} = yes",
                "\t\t}",
                "\t}",
            ])
            continue
        keyword = "if" if index == 0 else "else_if"
        lines.extend([
            f"\t{keyword} = {{",
            f"\t\tlimit = {{ check_variable = {{ {variable} < {tier + 0.5} }} }}",
            "\t\tif = {",
            f"\t\t\tlimit = {{ NOT = {{ has_country_flag = {tier_flag(group, tier)} }} }}",
            f"\t\t\tRUS_stalin_set_{group}_advisor_trait_tier_{tier} = yes",
            "\t\t}",
            "\t}",
        ])
    lines.extend(["}", ""])
    return lines


def render_effects() -> str:
    lines = ["# Generated by tools/generate_relationship_advisor_tiers.py.", ""]
    lines.extend(render_legacy_cleanup())
    lines.extend(render_tier_setters())
    for group in GROUP_TIERS:
        lines.extend(render_selector(group))
    lines.extend([
        "RUS_stalin_apply_relationship_advisor_trait_tiers = {",
        "\tif = {",
        "\t\tlimit = { NOT = { has_country_flag = RUS_relationship_advisor_traits_initialised } }",
        "\t\tRUS_stalin_clear_legacy_relationship_advisor_traits = yes",
        "\t\tRUS_stalin_clear_rkp_advisor_trait_tiers = yes",
        "\t\tRUS_stalin_clear_psr_advisor_trait_tiers = yes",
        "\t\tRUS_stalin_clear_max_advisor_trait_tiers = yes",
    ])
    for group, tiers in GROUP_TIERS.items():
        for tier in tiers:
            lines.append(f"\t\tclr_country_flag = {tier_flag(group, tier)}")
    lines.extend([
        "\t\tset_country_flag = RUS_relationship_advisor_traits_initialised",
        "\t}",
        "\tRUS_stalin_apply_rkp_advisor_trait_tier = yes",
        "\tRUS_stalin_apply_psr_advisor_trait_tier = yes",
        "\tRUS_stalin_apply_max_advisor_trait_tier = yes",
        "}",
    ])
    return "\n".join(lines) + "\n"


def render_localisation(language: str) -> str:
    lines = [f"l_{language}:"]
    for advisor in ADVISORS:
        lines.append(f"  {display_trait_id(advisor)}: \"${advisor['name']}$\"")
        for tier in GROUP_TIERS[advisor["group"]]:
            lines.append(f"  {trait_id(advisor, tier)}: \"\"")
    translations = {
        "english": {
            "centre": "Weekly balance of power: §Y1 point toward the centre§!",
            "land": "While land reform is underway, monthly land reform score: §G+1§!",
        },
        "russian": {
            "centre": "Еженедельный баланс сил: §Y1 пункт к центру§!",
            "land": "Пока идет земельная реформа, ежемесячные очки земельной реформы: §G+1§!",
        },
        "simp_chinese": {
            "centre": "每周权力平衡：§Y向中央移动1点§!",
            "land": "土地改革进行期间，每月土地改革分数：§G+1§!",
        },
    }[language]
    lines.append(f"  RUS_kamenev_bop_maximalist_advisor_weekly_tt: \"{translations['centre']}\"")
    lines.append(f"  RUS_maximalist_advisor_land_reform_monthly_tt: \"{translations['land']}\"")
    return "\n".join(lines) + "\n"


def write(path: Path, content: str, bom: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8-sig" if bom else "utf-8", newline="\n")


def main() -> None:
    write(ROOT / "common/country_leader/RUS_stalin_relationship_scaled_advisor_tiers.txt", render_traits())
    write(ROOT / "common/scripted_effects/RUS_stalin_relationship_scaled_advisor_tier_effects.txt", render_effects())
    for language in ("english", "russian", "simp_chinese"):
        write(
            ROOT / f"localisation/{language}/RUS_stalin_relationship_scaled_advisor_tiers_l_{language}.yml",
            render_localisation(language),
            bom=True,
        )


if __name__ == "__main__":
    main()
