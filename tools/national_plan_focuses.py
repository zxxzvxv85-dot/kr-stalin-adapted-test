"""Shared construction unlock catalogue for decisions and focus previews.

Construction is spread through the economic branches, with at most three
projects per focus. Mutually exclusive approaches own distinct project groups;
this does not open preview focuses or wire the future five-year-plan phase.
"""
PLAN_UNLOCK_SUFFIX = '424'
PLAN_UNLOCK_FOCUS = 'RUS_future_domestic_' + PLAN_UNLOCK_SUFFIX

FOCUS_PROJECTS = {
    PLAN_UNLOCK_SUFFIX: ('improve_roads_in_central_russia', 'improve_roads_in_northern_russia',
            'improve_roads_in_the_volga_basin'),
    '621': ('northern_route', 'upgrade_the_railroad_chelyabinsk',
            'upgrade_the_railroad_krasnoyarsk'),
    '804': ('kamenev_all_russian_electrification', 'kashira'),
    '420': ('renovate_and_expand_moscow', 'renovate_and_expand_tsaritsyn',
            'renovate_and_expand_saint_petersburg'),
    '160': ('second_baku', 'grozny_oil', 'romanshkino_oil'),
    '421': ('modernisation_of_AMO', 'tula_arms_factory'),
    '486': ('moscow_rural', 'leningrad_rural', 'tsaritsyn_rural'),
    '377': ('far_eastern_fishing_industry', 'central_asia_railroads', 'upgrade_the_railroad_vladivostok'),
    '487': ('emba_oil_area', 'arctic_mines'),
    # Federal planning: integrated industry, surveys, power and trunk transport.
    '169': ('magnitogorsk', 'moscow_logistics'),
    '176': ('bearing', 'moscow_grid'),
    '625': ('bodaybo_gold_mines', 'tyrnyauz_tungsten', 'rudny_altay'),
    '626': ('lipetsk_metallurgical_plant', 'uralmash', 'motovilikha_plants'),
    '182': ('zhiguli_hydroelectric_dam', 'krasnoyarsk_hydroelectric_dam', 'moscow_volga'),
    # Cooperatives: producer networks, machinery and urban services.
    '166': ('verny_cotton_industry', 'kursk_tractor_plant'),
    '629': ('rostselmash', 'bobrik'),
    '179': ('izhevsk_mechanical_plant', 'kamensky_uralsky'),
    '631': ('gaz', 'metro'),
    '177': ('leningrad_logistics', 'tsaritsyn_logistics'),
    # Trusts: consolidated heavy industry, specialists and hydropower.
    '163': ('kuznetsk_basin', 'tekeli_metallurgical_combine'),
    '181': ('svir', 'uvz'),
    '634': ('create_tankograd', 'krasnoyarskpromstroy', 'admiralty_dockyards'),
    '636': ('convert_civilian_aviation_industry', 'dalnremmash', 'siberian_timber_industries'),
    '183': ('volkhov', 'stavropol_hydroelectric_dam', 'rybinsk_hydroelectric_dam'),
    # The land-reform branch retains the two tractor plants.
    '199': ('tsaritsyn_tractor_plant', 'chelyabinsk_tractor_plant'),
}
PROJECT_FOCUS = {key: 'RUS_future_domestic_'+suffix
                 for suffix, keys in FOCUS_PROJECTS.items() for key in keys}
assert len(PROJECT_FOCUS) == sum(map(len, FOCUS_PROJECTS.values())) == 62
assert all(1 <= len(keys) <= 3 for keys in FOCUS_PROJECTS.values())


def focus_condition(project):
    return 'has_completed_focus = '+PROJECT_FOCUS[project['key']]


def unlock_rewards(projects):
    """Native KR-style unlock display; actual eligibility lives in decisions."""
    by_key = {p['key']: p for p in projects}
    assert set(by_key) == set(PROJECT_FOCUS)
    rewards = {suffix: ['unlock_decision_tooltip = '+by_key[key]['id'] for key in keys]
               for suffix, keys in FOCUS_PROJECTS.items()}
    rewards[PLAN_UNLOCK_SUFFIX].insert(0, 'unlock_decision_tooltip = RUS_np_open_account')
    return rewards
