"""Shared construction unlock catalogue for decisions and focus previews.

Construction is spread across the domestic and future five-year-plan branches.
The three economic approaches retain one project per assigned domestic focus.
Project assignments do not open preview focuses or activate the next tree.
"""
PLAN_UNLOCK_SUFFIX = '424'
PLAN_UNLOCK_FOCUS = 'RUS_future_domestic_' + PLAN_UNLOCK_SUFFIX

FOCUS_PROJECTS = {
    PLAN_UNLOCK_SUFFIX: ('improve_roads_in_central_russia', 'improve_roads_in_northern_russia',
            'improve_roads_in_the_volga_basin'),
    '621': ('northern_route', 'upgrade_the_railroad_chelyabinsk',
            'upgrade_the_railroad_krasnoyarsk'),
    '804': ('kamenev_all_russian_electrification', 'kashira', 'moscow_grid'),
    '160': ('renovate_and_expand_moscow', 'renovate_and_expand_tsaritsyn',
            'renovate_and_expand_saint_petersburg', 'metro'),
    '421': ('modernisation_of_AMO',),
    '486': ('moscow_rural',),
    '377': ('central_asia_railroads',),
    '487': ('emba_oil_area',),
    # Federal planning.
    '169': ('magnitogorsk',),
    '176': ('bearing',),
    '625': ('bodaybo_gold_mines',),
    '626': ('lipetsk_metallurgical_plant',),
    '182': ('zhiguli_hydroelectric_dam',),
    # Cooperatives.
    '166': ('verny_cotton_industry',),
    '629': ('rostselmash',),
    '179': ('izhevsk_mechanical_plant',),
    '631': ('gaz',),
    '177': ('leningrad_logistics',),
    # Trusts.
    '163': ('kuznetsk_basin',),
    '181': ('svir',),
    '634': ('create_tankograd',),
    '636': ('convert_civilian_aviation_industry',),
    '183': ('volkhov',),
    # The land-reform branch retains the two tractor plants.
    '199': ('tsaritsyn_tractor_plant', 'chelyabinsk_tractor_plant'),
}
FIVE_YEAR_PLAN_PROJECTS = {
    '641': ('tekeli_metallurgical_combine', 'arctic_mines', 'rudny_altay'),
    '644': ('moscow_volga', 'krasnoyarskpromstroy'),
    '190': ('second_baku', 'grozny_oil', 'romanshkino_oil'),
    '642': ('uralmash', 'kursk_tractor_plant', 'uvz'),
    '645': ('upgrade_the_railroad_vladivostok', 'moscow_logistics', 'tsaritsyn_logistics'),
    '723': ('krasnoyarsk_hydroelectric_dam', 'stavropol_hydroelectric_dam', 'rybinsk_hydroelectric_dam'),
    '648': ('tula_arms_factory', 'motovilikha_plants', 'tyrnyauz_tungsten'),
    '194': ('far_eastern_fishing_industry', 'siberian_timber_industries'),
    '643': ('kamensky_uralsky', 'admiralty_dockyards', 'dalnremmash'),
    '649': ('bobrik', 'leningrad_rural', 'tsaritsyn_rural'),
}
FOCUS_PROJECTS.update(FIVE_YEAR_PLAN_PROJECTS)
PROJECT_FOCUS = {key: 'RUS_future_domestic_'+suffix
                 for suffix, keys in FOCUS_PROJECTS.items() for key in keys}
assert len(PROJECT_FOCUS) == sum(map(len, FOCUS_PROJECTS.values())) == 62
assert all(1 <= len(keys) <= (4 if suffix == '160' else 3)
           for suffix, keys in FOCUS_PROJECTS.items())


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
