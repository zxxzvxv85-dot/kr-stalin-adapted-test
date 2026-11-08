"""Shared construction unlock catalogue for decisions and focus previews.

Only construction-related focuses own projects. Political/organisational
choices and the three mutually exclusive economic approaches do not gate them.
"""
FOCUS_PROJECTS = {
    '424': ('improve_roads_in_central_russia', 'improve_roads_in_northern_russia',
            'improve_roads_in_the_volga_basin', 'metro', 'moscow_volga'),
    '621': ('northern_route', 'upgrade_the_railroad_chelyabinsk',
            'upgrade_the_railroad_krasnoyarsk', 'upgrade_the_railroad_vladivostok',
            'central_asia_railroads', 'moscow_logistics', 'leningrad_logistics', 'tsaritsyn_logistics'),
    '804': ('kamenev_all_russian_electrification', 'stavropol_hydroelectric_dam',
            'rybinsk_hydroelectric_dam', 'zhiguli_hydroelectric_dam',
            'krasnoyarsk_hydroelectric_dam', 'kashira', 'moscow_grid', 'svir'),
    '420': ('renovate_and_expand_moscow', 'renovate_and_expand_tsaritsyn',
            'renovate_and_expand_saint_petersburg', 'magnitogorsk',
            'izhevsk_mechanical_plant', 'tula_arms_factory', 'create_tankograd',
            'lipetsk_metallurgical_plant', 'uralmash', 'motovilikha_plants',
            'admiralty_dockyards', 'kamensky_uralsky', 'krasnoyarskpromstroy',
            'tekeli_metallurgical_combine', 'volkhov'),
    '160': ('second_baku', 'grozny_oil', 'arctic_mines', 'tyrnyauz_tungsten',
            'romanshkino_oil', 'kuznetsk_basin', 'bodaybo_gold_mines',
            'rudny_altay', 'emba_oil_area', 'siberian_timber_industries'),
    '197': ('modernisation_of_AMO', 'convert_civilian_aviation_industry', 'gaz', 'bearing'),
    '199': ('tsaritsyn_tractor_plant', 'chelyabinsk_tractor_plant', 'kursk_tractor_plant',
            'rostselmash', 'uvz', 'dalnremmash'),
    '189': ('far_eastern_fishing_industry', 'verny_cotton_industry', 'bobrik'),
    '455': ('moscow_rural', 'leningrad_rural', 'tsaritsyn_rural'),
}
PROJECT_FOCUS = {key: 'RUS_future_domestic_'+suffix
                 for suffix, keys in FOCUS_PROJECTS.items() for key in keys}
assert len(PROJECT_FOCUS) == sum(map(len, FOCUS_PROJECTS.values())) == 62


def focus_condition(project):
    return 'has_completed_focus = '+PROJECT_FOCUS[project['key']]


def unlock_rewards(projects):
    """Native KR-style unlock display; actual eligibility lives in decisions."""
    by_key = {p['key']: p for p in projects}
    assert set(by_key) == set(PROJECT_FOCUS)
    return {suffix: ['unlock_decision_tooltip = '+by_key[key]['id'] for key in keys]
            for suffix, keys in FOCUS_PROJECTS.items()}
