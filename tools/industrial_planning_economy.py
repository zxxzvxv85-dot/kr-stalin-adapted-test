"""Render the independent, real-time industrial construction simulation.

Country scope owns the queue and reservations; numbered scopes only read local
conditions or receive a completed building. No original Five-Year Plan hooks.
"""
from __future__ import annotations

P = 'RUS_ip_'
# work days at speed 1, reserved civilian factories / steel / coal, freight demand
PROJECTS = {
    1: dict(days=120, civs=2, steel=2, coal=0, freight=1, zh='煤矿', en='Coal mine'),
    2: dict(days=120, civs=2, steel=2, coal=1, freight=1, zh='铁矿', en='Iron mine'),
    3: dict(days=180, civs=3, steel=4, coal=2, freight=1, zh='强化电网', en='Power grid'),
    4: dict(days=240, civs=4, steel=4, coal=4, freight=2, zh='钢铁厂', en='Steelworks'),
    5: dict(days=300, civs=5, steel=6, coal=2, freight=3, zh='机械军工厂', en='Machine works'),
    6: dict(days=120, civs=2, steel=2, coal=1, freight=1, zh='交通建设', en='Transport'),
}


def block(name, body):
    return name + ' = {\n' + ''.join('\t' + line + '\n' if line else '\n' for line in body.rstrip().splitlines()) + '}\n'


def variable(command, key, value):
    return f'{command} = {{ {P}{key} = {value} }}\n'


def setv(k, v): return variable('set_variable', k, v)
def add(k, v): return variable('add_to_variable', k, v)
def sub(k, v): return variable('subtract_from_variable', k, v)
def mul(k, v): return variable('multiply_variable', k, v)
def div(k, v): return variable('divide_variable', k, v)
def cv(k, op, v): return f'check_variable = {{ {P}{k} {op} {v} }}\n'
def ge(k, v): return block('NOT', cv(k, '<', v))
def iff(cond, body): return block('if', block('limit', cond) + body)
def fx(k, body): return block(P + k, body)
def clamp(k, low, high): return f'clamp_variable = {{ var = {P}{k} min = {low} max = {high} }}\n'


def rail_spec(a, b):
    # No railway is ever constructed through another country's territory.
    return (f'build_only_on_allied = yes\nstart_state = {a}\ntarget_state = {b}\n'
            'controller_priority = { base = -1 modifier = { tag = ROOT add = 2 } }\n')


def render_economy(data):
    cells, hub = data['cells'], data['hub']
    sea = {tuple(edge) for edge in data['sea_edges']}
    sea_terminals = {b: a for a, b in sea}
    triggers, effects = [], []
    triggers += [fx('available', 'original_tag = RUS\nis_ai = no\nhas_country_flag = RUS_ip_ui_unlocked\n'),
                 fx('editing', 'RUS_ip_available = yes\nhas_country_flag = RUS_ip_open\nhas_country_flag = RUS_ip_active\n')]
    for c in cells:
        i, state = c['id'], c['state']
        triggers.append(fx(f'owned_{i}', f'owns_state = {state}\ncontrols_state = {state}\n'))
        for kind in PROJECTS:
            cond = f'RUS_ip_owned_{i} = yes\n'
            if kind in (1, 2):
                cond += cv(f'n{i}_mine_{kind}', '<', 3)
                if not c['coal' if kind == 1 else 'iron']:
                    cond += 'always = no\n'
            elif kind in (3, 4, 5):
                building = {3:'energy_infrastructure', 4:'industrial_complex', 5:'arms_factory'}[kind]
                cond += block(str(state), f'free_building_slots = {{ building = {building} size > 0 include_locked = no }}\n')
            else:
                cond += block(str(state), 'free_building_slots = { building = infrastructure size > 0 }\n')
                if i != hub and i not in sea_terminals:
                    neighbors = []
                    for j in c['neighbors']:
                        if tuple(sorted((i, j))) in sea: continue
                        neighbors.append(block('AND', f'RUS_ip_owned_{j} = yes\n' + cv(f'n{j}_connected', '=', 1)
                                               + block('can_build_railway', rail_spec(cells[j]['state'], state))))
                    cond += block('OR', ''.join(neighbors))
                    # A queued railway keeps its original start, even when
                    # another neighbouring district becomes connected later.
                    anchor_choices = []
                    for j in c['neighbors']:
                        if tuple(sorted((i, j))) in sea: continue
                        anchor_choices.append(block('AND', cv(f'n{i}_anchor', '=', j + 1)
                            + f'RUS_ip_owned_{j} = yes\n' + cv(f'n{j}_connected', '=', 1)
                            + block('can_build_railway', rail_spec(cells[j]['state'], state))))
                    cond += block('OR', cv(f'n{i}_project', '=', 0) + block('AND', cv(f'n{i}_project', '=', 6)
                                         + block('OR', ''.join(anchor_choices))))
                elif i in sea_terminals:
                    cond += cv(f'n{i}_connected', '=', 1)
            triggers.append(fx(f'site_{i}_{kind}', cond))
    for kind, spec in PROJECTS.items():
        cond = 'RUS_ip_editing = yes\n' + ''.join(ge('free_' + r, spec[r]) for r in ('civs', 'steel', 'coal'))
        cond += block('OR', ''.join(block('AND', cv('selected', '=', c['id']) + cv(f'n{c["id"]}_project', '=', 0)
                                               + f'RUS_ip_site_{c["id"]}_{kind} = yes\n') for c in cells))
        triggers.append(fx(f'can_build_{kind}', cond))

    # New namespace flag prevents the old virtual exercise's free starter layout
    # from becoming real buildings or reservations when testing an existing save.
    init = 'set_country_flag = RUS_ip_economy_initialized\n'
    init += setv('selected', hub) + setv('days_left', 1800) + setv('completed', 0)
    init += setv('mining_completed', 0) + setv('resource_penalty', -.30)
    for key in ('civs', 'steel', 'coal'): init += setv('reserved_' + key, 0)
    for c in cells:
        for key in ('project', 'work', 'required', 'paused', 'running', 'mine_1', 'mine_2', 'last_kind'):
            init += setv(f'n{c["id"]}_{key}', 0)
    init += 'RUS_ip_capture_capacity = yes\nRUS_ip_refresh = yes\n'
    effects.append(fx('initialize', iff('NOT = { has_country_flag = RUS_ip_economy_initialized }', init)))
    effects.append(fx('enable_gui', iff('original_tag = RUS\nis_ai = no\nNOT = { has_country_flag = RUS_ip_ui_unlocked }',
        'set_country_flag = RUS_ip_ui_unlocked\nRUS_ip_open_effect = yes\n')))
    effects.append(fx('open_effect', iff('RUS_ip_available = yes',
        'RUS_ip_initialize = yes\nset_country_flag = RUS_ip_open\nclr_country_flag = RUS_ip_help_open\nclr_country_flag = RUS_ip_cancel_armed\nRUS_ip_refresh = yes\n')))
    effects.append(fx('close_effect', 'clr_country_flag = RUS_ip_open\nclr_country_flag = RUS_ip_help_open\nclr_country_flag = RUS_ip_cancel_armed\n' + add('dirty', 1)))
    effects.append(fx('toggle', iff('RUS_ip_available = yes', iff('has_country_flag = RUS_ip_open', 'RUS_ip_close_effect = yes\n')
                                                 + block('else', 'RUS_ip_open_effect = yes\n'))))
    effects.append(fx('start', iff('RUS_ip_available = yes\nhas_country_flag = RUS_ip_open\nNOT = { has_country_flag = RUS_ip_started }',
        'set_country_flag = RUS_ip_started\nset_country_flag = RUS_ip_active\n' + setv('days_left', 1800) + 'RUS_ip_refresh_extraction = yes\nRUS_ip_capture_capacity = yes\nRUS_ip_refresh = yes\n')))
    effects.append(fx('toggle_help', iff('has_country_flag = RUS_ip_help_open', 'clr_country_flag = RUS_ip_help_open\n')
                      + block('else', 'set_country_flag = RUS_ip_help_open\n') + add('dirty', 1)))

    # Recompute from completed mines instead of adding a permanent modifier on
    # every refresh. Negative extraction applies to coal as well as other ores.
    penalty = setv('resource_penalty', P + 'mining_completed') + mul('resource_penalty', .02) + sub('resource_penalty', .30)
    penalty += clamp('resource_penalty', -.30, 0) + iff('NOT = { has_dynamic_modifier = { modifier = RUS_ip_extraction_bottleneck } }',
        'add_dynamic_modifier = { modifier = RUS_ip_extraction_bottleneck }\n')
    clear = setv('resource_penalty', 0) + iff('has_dynamic_modifier = { modifier = RUS_ip_extraction_bottleneck }',
        'remove_dynamic_modifier = { modifier = RUS_ip_extraction_bottleneck }\n')
    extraction = iff('has_country_flag = RUS_ip_started',
        iff('has_country_flag = RUS_ip_active\n' + cv('mining_completed', '<', 15), penalty) + block('else', clear))
    extraction += setv('resource_penalty_percent', P + 'resource_penalty') + mul('resource_penalty_percent', 100) + 'force_update_dynamic_modifier = yes\n'
    effects.append(fx('refresh_extraction', extraction))

    # A native snapshot is taken only at initialization and the daily boundary.
    # UI clicks use a shared ledger, so rapidly queued projects cannot spend the
    # same native availability before the engine updates its economy cache.
    capture = ''
    for r, native in [('civs', 'num_of_civilian_factories_available_for_projects'), ('steel', 'resource@steel'), ('coal', 'resource@coal')]:
        capture += setv('capacity_' + r, native) + add('capacity_' + r, P + 'reserved_' + r) + clamp('capacity_' + r, 0, 99999)
    effects.append(fx('capture_capacity', capture))

    survey = setv('connected_count', 0) + setv('energy', 'energy_ratio') + clamp('energy', 0, 1)
    survey += setv('energy_percent', P + 'energy') + mul('energy_percent', 100)
    for c in cells:
        i, state = c['id'], c['state']
        survey += setv(f'n{i}_connected', 0) + setv(f'n{i}_rail', 0)
        for key, native in [('infra', 'infrastructure_level'), ('civs', 'industrial_complex_level'), ('mil', 'building_level@arms_factory'),
                            ('coal', 'resource@coal'), ('steel', 'resource@steel'), ('grid', 'building_level@energy_infrastructure')]:
            survey += setv(f'n{i}_{key}', f'{state}.{native}')
        for level in range(1, 6):
            survey += iff(f'has_railway_level = {{ state = {state} level = {level} }}', setv(f'n{i}_rail', level))
        connected = f'RUS_ip_owned_{hub} = yes\nRUS_ip_owned_{i} = yes\n'
        if i != hub: connected += block('has_railway_connection', f'build_only_on_allied = yes\nstart_state = 219\ntarget_state = {state}\n')
        survey += iff(connected, setv(f'n{i}_connected', 1))
    for end, anchor in sea_terminals.items():
        cond = f'RUS_ip_owned_{anchor} = yes\nRUS_ip_owned_{end} = yes\nnum_of_convoys > 9\n' + cv(f'n{anchor}_connected', '=', 1)
        for idx in (anchor, end): cond += f'check_variable = {{ {cells[idx]["state"]}.building_level@naval_base > 0 }}\n'
        survey += iff(cond, setv(f'n{end}_connected', 1))
    for c in cells:
        i = c['id']
        survey += iff(cv(f'n{i}_connected', '=', 1), add('connected_count', 1))
        survey += setv(f'n{i}_freight', P + f'n{i}_infra') + add(f'n{i}_freight', P + f'n{i}_rail') + add(f'n{i}_freight', 1)
        survey += iff(cv(f'n{i}_connected', '=', 0), mul(f'n{i}_freight', .25))
    effects.append(fx('survey', survey))

    # Only funded, unpaused projects occupy native factories and resources.
    # If national capacity drops, lower district numbers have stable priority.
    allocate = setv('queued', 0) + setv('running', 0)
    for r in ('civs', 'steel', 'coal'):
        allocate += setv('free_' + r, P + 'capacity_' + r) + setv('reserved_' + r, 0)
    for c in cells:
        i = c['id']
        body = add('queued', 1) + setv(f'n{i}_status', 2)
        for kind, spec in PROJECTS.items():
            cond = f'has_country_flag = RUS_ip_active\nRUS_ip_site_{i}_{kind} = yes\n' + cv(f'n{i}_paused', '=', 0)
            if kind in (4, 5): cond += cv(f'n{i}_connected', '=', 1)
            ready = setv(f'n{i}_status', 5)
            funds = ''.join(ge('free_' + r, spec[r]) for r in ('civs', 'steel', 'coal'))
            spend = setv(f'n{i}_running', 1) + setv(f'n{i}_status', 1) + add('running', 1)
            for r in ('civs', 'steel', 'coal'):
                spend += sub('free_' + r, spec[r]) + add('reserved_' + r, spec[r])
            ready += iff(funds, spend)
            part = iff(cond, ready)
            # Specific reasons override generic site-blocked status.
            if kind in (4, 5): part += iff(cv(f'n{i}_connected', '=', 0) + f'RUS_ip_owned_{i} = yes', setv(f'n{i}_status', 4))
            body += iff(cv(f'n{i}_project', '=', kind), part)
        body += iff(cv(f'n{i}_paused', '=', 1), setv(f'n{i}_status', 3))
        allocate += setv(f'n{i}_running', 0) + setv(f'n{i}_status', 0) + iff(cv(f'n{i}_project', '>', 0), body)
    effects.append(fx('allocate', allocate))
    apply = iff(cv('running', '>', 0),
        iff('NOT = { has_dynamic_modifier = { modifier = RUS_ip_construction_commitment } }',
            'add_dynamic_modifier = { modifier = RUS_ip_construction_commitment }\n'))
    apply += block('else', iff('has_dynamic_modifier = { modifier = RUS_ip_construction_commitment }',
                              'remove_dynamic_modifier = { modifier = RUS_ip_construction_commitment }\n'))
    apply += 'force_update_dynamic_modifier = yes\n'
    effects.append(fx('apply_reservations', apply))

    speeds = ''
    for c in cells:
        i = c['id']
        body = setv(f'n{i}_speed', P + f'n{i}_infra') + mul(f'n{i}_speed', .12) + add(f'n{i}_speed', 1)
        body += setv('speed_part', P + f'n{i}_civs') + clamp('speed_part', 0, 20) + mul('speed_part', .025) + add(f'n{i}_speed', P + 'speed_part')
        for kind, spec in PROJECTS.items():
            resource = 'coal' if kind in (1, 3) else 'steel'
            part = setv('speed_part', P + f'n{i}_{resource}') + clamp('speed_part', 0, 40) + mul('speed_part', .005) + add(f'n{i}_speed', P + 'speed_part')
            part += setv('speed_part', P + f'n{i}_freight') + div('speed_part', spec['freight']) + clamp('speed_part', .1, 1) + mul(f'n{i}_speed', P + 'speed_part')
            if kind in (4, 5):
                part += setv('speed_part', P + 'energy') + mul('speed_part', .75) + add('speed_part', .25) + mul(f'n{i}_speed', P + 'speed_part')
            body += iff(cv(f'n{i}_project', '=', kind), part)
        body += setv(f'n{i}_eta', P + f'n{i}_required') + sub(f'n{i}_eta', P + f'n{i}_work') + div(f'n{i}_eta', P + f'n{i}_speed')
        speeds += setv(f'n{i}_speed', 0) + setv(f'n{i}_eta', 0) + iff(cv(f'n{i}_running', '=', 1), body)
        speeds += setv(f'n{i}_percent', 0)
        speeds += iff(cv(f'n{i}_required', '>', 0), setv(f'n{i}_percent', P + f'n{i}_work') + div(f'n{i}_percent', P + f'n{i}_required') + mul(f'n{i}_percent', 100) + clamp(f'n{i}_percent', 0, 100))
    effects.append(fx('speeds', speeds))

    cache = ''
    for c in cells:
        i = c['id']
        cache += iff(cv('selected', '=', i), ''.join(setv('sel_' + key, P + f'n{i}_{key}') for key in
                         ('project', 'work', 'required', 'running', 'status', 'infra', 'civs', 'mil', 'coal', 'steel', 'grid', 'rail', 'connected', 'freight', 'speed', 'eta', 'percent', 'paused')))
    # 21 frames are under the engine texture size limit; exact percent is text.
    cache += setv('progress_frame', P + 'sel_percent') + div('progress_frame', 5) + 'round_variable = RUS_ip_progress_frame\n' + add('progress_frame', 1) + clamp('progress_frame', 1, 21)
    cache += iff(cv('sel_project', '=', 0), 'clr_country_flag = RUS_ip_cancel_armed\n')
    effects.append(fx('selection_cache', cache))
    effects.append(fx('refresh', 'RUS_ip_refresh_extraction = yes\nRUS_ip_survey = yes\nRUS_ip_allocate = yes\nRUS_ip_speeds = yes\nRUS_ip_apply_reservations = yes\nRUS_ip_selection_cache = yes\n' + add('dirty', 1)))

    rewards = {}
    for c in cells:
        i, state = c['id'], c['state']
        for kind in PROJECTS:
            if kind in (1, 2):
                resource = 'coal' if kind == 1 else 'steel'
                reward = block(str(state), f'add_resource = {{ type = {resource} amount = 4 }}\n')
            elif kind == 3: reward = block(str(state), 'add_building_construction = { type = energy_infrastructure level = 1 instant_build = yes }\n')
            elif kind == 4: reward = block(str(state), 'add_building_construction = { type = industrial_complex level = 1 instant_build = yes }\nadd_resource = { type = steel amount = 2 }\n')
            elif kind == 5: reward = block(str(state), 'add_building_construction = { type = arms_factory level = 1 instant_build = yes }\n')
            else:
                reward = block(str(state), 'add_building_construction = { type = infrastructure level = 1 instant_build = yes }\n')
                if i != hub and i not in sea_terminals:
                    for j in c['neighbors']:
                        if tuple(sorted((i, j))) in sea: continue
                        reward += iff(cv(f'n{i}_anchor', '=', j + 1), block('build_railway', 'level = 1\n' + rail_spec(cells[j]['state'], state)))
            rewards[i, kind] = reward
            completion = setv(f'n{i}_project', 0) + setv(f'n{i}_running', 0) + setv(f'n{i}_work', 0) + setv(f'n{i}_required', 0)
            completion += setv(f'n{i}_last_kind', kind) + add('completed', 1)
            if kind in (1, 2): completion += add(f'n{i}_mine_{kind}', 1) + add('mining_completed', 1) + clamp('mining_completed', 0, 15)
            # Clear the queue before awarding; GUI/refresh/reload never calls it.
            completion += reward
            effects.append(fx(f'complete_{i}_{kind}', iff('has_country_flag = RUS_ip_active\n' + cv(f'n{i}_project', '=', kind)
                           + cv(f'n{i}_running', '=', 1) + ge(f'n{i}_work', P + f'n{i}_required') + f'RUS_ip_site_{i}_{kind} = yes', completion)))

    for kind, spec in PROJECTS.items():
        body = ''
        for c in cells:
            i, state = c['id'], c['state']
            queue = setv(f'n{i}_project', kind) + setv(f'n{i}_work', 0) + setv(f'n{i}_required', spec['days']) + setv(f'n{i}_paused', 0)
            if kind == 6:
                queue += setv(f'n{i}_anchor', 0)
                for j in c['neighbors']:
                    if tuple(sorted((i, j))) in sea: continue
                    queue += iff(cv(f'n{i}_anchor', '=', 0) + cv(f'n{j}_connected', '=', 1) + f'RUS_ip_owned_{j} = yes\n'
                                 + block('can_build_railway', rail_spec(cells[j]['state'], state)), setv(f'n{i}_anchor', j + 1))
            body += iff(cv('selected', '=', i), queue)
        effects.append(fx(f'build_{kind}', 'RUS_ip_refresh = yes\n' + iff(f'RUS_ip_can_build_{kind} = yes', body
                          + 'clr_country_flag = RUS_ip_cancel_armed\nRUS_ip_refresh = yes\n')))
    pause, cancel = '', ''
    for c in cells:
        i = c['id']
        pause += iff(cv('selected', '=', i) + cv(f'n{i}_project', '>', 0), iff(cv(f'n{i}_paused', '=', 0), setv(f'n{i}_paused', 1))
                                                           + block('else', setv(f'n{i}_paused', 0)))
        cancel += iff(cv('selected', '=', i), setv(f'n{i}_project', 0) + setv(f'n{i}_work', 0) + setv(f'n{i}_required', 0) + setv(f'n{i}_paused', 0))
    effects.append(fx('pause', iff('RUS_ip_editing = yes', pause + 'RUS_ip_refresh = yes\n')))
    effects.append(fx('cancel', iff('RUS_ip_editing = yes\nhas_country_flag = RUS_ip_cancel_armed', cancel
                                      + 'clr_country_flag = RUS_ip_cancel_armed\nRUS_ip_refresh = yes\n')))

    daily = 'RUS_ip_capture_capacity = yes\nRUS_ip_refresh = yes\n'
    for c in cells:
        i = c['id']
        progress = add(f'n{i}_work', P + f'n{i}_speed')
        for kind in PROJECTS: progress += f'RUS_ip_complete_{i}_{kind} = yes\n'
        daily += iff(cv(f'n{i}_running', '=', 1), progress)
    daily += sub('days_left', 1)
    end = 'clr_country_flag = RUS_ip_active\nset_country_flag = RUS_ip_ended\n'
    for c in cells: end += setv(f'n{c["id"]}_project', 0) + setv(f'n{c["id"]}_work', 0) + setv(f'n{c["id"]}_required', 0)
    daily += iff(cv('days_left', '<', 1), end) + 'RUS_ip_refresh = yes\n'
    effects.append(fx('daily', iff('original_tag = RUS\nhas_country_flag = RUS_ip_active', daily)))
    on_actions = block('on_actions', block('on_daily', block('effect', 'RUS_ip_daily = yes\n'))
                       + block('on_startup', block('effect', block('every_country', block('limit', 'original_tag = RUS\nhas_country_flag = RUS_ip_economy_initialized') + 'RUS_ip_refresh = yes\n'))))
    modifier = fx('construction_commitment', 'icon = GFX_idea_generic_industry\nenable = { has_country_flag = RUS_ip_active }\n'
                  'civilian_factory_use = RUS_ip_reserved_civs\ncountry_resource_cost_steel = RUS_ip_reserved_steel\ncountry_resource_cost_coal = RUS_ip_reserved_coal\n')
    modifier += fx('extraction_bottleneck', 'icon = GFX_idea_generic_industry\nenable = { has_country_flag = RUS_ip_active }\nlocal_resources_factor = RUS_ip_resource_penalty\n')
    return triggers, effects, on_actions, modifier, rewards
