"""Regional planning capacities; all quantities are programme points, not manpower.

Native buildings/resources are read afresh. Development and paid training are
persistent. Neighbouring domestic districts may share *surplus* power, consuming
freight at both ends; imports cannot be re-exported or spent twice. This models
planning links, not individual railway provinces or the vanilla power market.
"""
from industrial_planning_economy import P, PROJECTS, setv, add, sub, mul, div, cv, ge, iff, fx, clamp, block

METRICS = ('development', 'workers', 'workers_need', 'power', 'power_need', 'power_import',
           'power_export', 'freight', 'freight_used', 'worker_ratio', 'power_ratio',
           'freight_ratio', 'bottleneck', 'training', 'urban', 'gain', 'training_gain')
BASE_GAINS = {1: 1, 2: 1, 3: 3, 4: 2, 5: 2, 6: 4, 7: 10, 8: 2}
RATE_INPUTS = ('project', 'development', 'infra', 'civs', 'coal', 'steel',
               'workers', 'workers_need', 'power', 'power_need', 'freight', 'freight_used')
RATE_OUTPUTS = ('speed', 'bottleneck', 'worker_ratio', 'power_ratio', 'freight_ratio')


def term(dst, src, factor):
    return setv('region_term', P + src) + mul('region_term', factor) + add(dst, P + 'region_term')


def seed(cells):
    out = '# Seed once from the centre state; later refreshes never reset development.\n'
    for c in cells:
        n, state = f'n{c["id"]}_', c['state']
        out += setv(n + 'development', f'{state}.state_population_k') + div(n + 'development', 400) + clamp(n + 'development', 0, 12)
        for native, factor in [('infrastructure_level', 5), ('industrial_complex_level', 2), ('building_level@arms_factory', 2)]:
            out += setv('region_term', f'{state}.{native}') + mul('region_term', factor) + add(n + 'development', P + 'region_term')
        out += add(n + 'development', 8) + clamp(n + 'development', 8, 70)
        for key in ('trained', 'urban', 'training', *(f'done_{k}' for k in PROJECTS)):
            out += setv(n + key, 0)
    return out


def demand(n, kind):
    """Same demand calculation is used by the live queue and its forecast."""
    s = PROJECTS[kind]
    out = add(n + 'workers_need', s['workers']) + add(n + 'power_need', s['power']) + add(n + 'freight_used', s['freight'])
    # Native materials are reserved nationally; local deposits reduce the
    # programme's shipping burden, never its actual resource cost.
    for resource in ('steel', 'coal'):
        out += setv('region_term', P + n + resource) + mul('region_term', -.25) + add('region_term', s[resource]) + clamp('region_term', 0, s[resource])
        out += mul('region_term', .7) + add(n + 'freight_used', P + 'region_term')
    return out


def speed(n, kind):
    """Single bottleneck, rather than multiplying shortages into a death spiral."""
    out = setv(n + 'bottleneck', 0) + setv('region_factor', 1)
    for number, (capacity, need, ratio) in enumerate([
        ('workers', 'workers_need', 'worker_ratio'), ('power', 'power_need', 'power_ratio'),
        ('freight', 'freight_used', 'freight_ratio')], 1):
        out += setv(n + ratio, 1)
        body = setv(n + ratio, P + n + capacity) + div(n + ratio, P + n + need) + clamp(n + ratio, .01, 1)
        out += iff(cv(n + need, '>', 0), body)
        out += iff(cv(n + ratio, '<', P + 'region_factor'), setv('region_factor', P + n + ratio) + setv(n + 'bottleneck', number))
    # Enabling projects can always make progress if actual national costs/site
    # requirements are met. Heavy industry cannot use this recovery floor.
    floor = .65 if kind in (3, 6, 7, 8) else .30 if kind in (1, 2) else .15
    out += clamp('region_factor', floor, 1)
    out += setv(n + 'speed', P + n + 'infra') + mul(n + 'speed', .12) + add(n + 'speed', 1)
    out += setv('region_term', P + n + 'civs') + clamp('region_term', 0, 20) + mul('region_term', .025) + add(n + 'speed', P + 'region_term')
    resource = 'coal' if kind in (1, 3) else 'steel'
    out += setv('region_term', P + n + resource) + clamp('region_term', 0, 40) + mul('region_term', .005) + add(n + 'speed', P + 'region_term')
    out += setv('region_term', P + n + 'development') + mul('region_term', .012) + add('region_term', .55) + mul(n + 'speed', P + 'region_term')
    out += mul(n + 'speed', P + 'region_factor')
    if kind in (4, 5):
        out += setv('region_term', P + 'energy') + mul('region_term', .75) + add('region_term', .25) + mul(n + 'speed', P + 'region_term')
    return out


def gain(n, kind):
    out = setv('region_divisor', P + n + f'done_{kind}') + add('region_divisor', 1)
    out += setv(n + 'gain', BASE_GAINS[kind]) + div(n + 'gain', P + 'region_divisor')
    out += setv('region_room', 100) + sub('region_room', P + n + 'development') + clamp('region_room', 0, 100)
    out += clamp(n + 'gain', 0, P + 'region_room')
    if kind == 8:
        out += setv(n + 'training_gain', P + n + 'development') + mul(n + 'training_gain', .08) + add(n + 'training_gain', 4)
        out += setv('region_divisor', P + n + 'training') + mul('region_divisor', .5) + add('region_divisor', 1)
        out += div(n + 'training_gain', P + 'region_divisor')
    return out


def completion(n, kind):
    out = gain(n, kind) + add(n + 'development', P + n + 'gain') + clamp(n + 'development', 0, 100)
    if kind == 7: out += add(n + 'urban', 1)
    if kind == 8: out += add(n + 'trained', P + n + 'training_gain') + add(n + 'training', 1)
    return out + add(n + f'done_{kind}', 1)


def render_regions(data):
    cells = data['cells']; edges = [(e['a'], e['b']) for e in data['edge_sprites']]
    sea = {tuple(e) for e in data['sea_edges']}
    effects = []; setup = ''
    for c in cells:
        i = c['id']; n = f'n{i}_'
        setup += setv(n + 'population', f'{c["state"]}.state_population_k') + div(n + 'population', 300) + clamp(n + 'population', 0, 12)
        setup += setv(n + 'workers', 4) + add(n + 'workers', P + n + 'population') + term(n + 'workers', n + 'development', .18)
        setup += add(n + 'workers', P + n + 'trained') + term(n + 'workers', n + 'urban', 2)
        setup += setv(n + 'power', 3) + term(n + 'power', n + 'infra', .5) + term(n + 'power', n + 'grid', 8)
        setup += term(n + 'power', n + 'coal', .1) + term(n + 'power', n + 'development', .035)
        setup += setv(n + 'freight', 3) + term(n + 'freight', n + 'infra', 2) + term(n + 'freight', n + 'rail', 1.5) + add(n + 'freight', P + n + 'urban')
        setup += iff(cv(n + 'connected', '=', 0), mul(n + 'freight', .6))
        for key, factors in [('workers_need', [('civs', 1.5), ('mil', 2), ('mine_1', .5), ('mine_2', .5)]),
                             ('power_need', [('civs', 1.5), ('mil', 2), ('mine_1', .5), ('mine_2', .75)]),
                             ('freight_used', [('civs', .7), ('mil', .8), ('mine_1', .7), ('mine_2', .7)])]:
            setup += setv(n + key, 0)
            for field, factor in factors: setup += term(n + key, n + field, factor)
            setup += setv(n + 'base_' + key, P + n + key)
        for kind in PROJECTS:
            setup += iff(cv(n + 'running', '=', 1) + cv(n + 'project', '=', kind), demand(n, kind))
        setup += setv(n + 'local_power', P + n + 'power') + setv(n + 'power_import', 0) + setv(n + 'power_export', 0)
        setup += setv(n + 'surplus', P + n + 'power') + sub(n + 'surplus', P + n + 'power_need') + clamp(n + 'surplus', 0, 99999)
        setup += setv(n + 'deficit', P + n + 'power_need') + sub(n + 'deficit', P + n + 'power') + clamp(n + 'deficit', 0, 99999)
        setup += setv(n + 'spare_freight', P + n + 'freight') + sub(n + 'spare_freight', P + n + 'freight_used') + clamp(n + 'spare_freight', 0, 99999)
    effects.append(fx('regional_setup', setup))
    trade = '# Stable neighbour order; 1 power imported consumes 0.5 freight at each endpoint.\n'
    for a, b in edges:
        edge = f'edge_{a}_{b}_'
        condition = f'RUS_ip_owned_{a} = yes\nRUS_ip_owned_{b} = yes\n' + cv(f'n{a}_connected', '=', 1) + cv(f'n{b}_connected', '=', 1)
        if (a, b) not in sea:
            condition += block('has_railway_connection', f'build_only_on_allied = yes\nstart_state = {cells[a]["state"]}\ntarget_state = {cells[b]["state"]}\n')
        trade += setv(edge + 'live', 0) + setv(edge + 'flow', 0)
        body = setv(edge + 'live', 1)
        if (a, b) in sea:
            # Sea links carry material access, not an invented submarine grid.
            trade += iff(condition, body)
            continue
        for source, target in [(a, b), (b, a)]:
            src, dst = f'n{source}_', f'n{target}_'
            transfer = setv('region_flow', P + src + 'surplus') + clamp('region_flow', 0, P + dst + 'deficit')
            for n in (src, dst):
                transfer += setv('region_limit', P + n + 'spare_freight') + mul('region_limit', 2) + clamp('region_flow', 0, P + 'region_limit')
            transfer += sub(src + 'surplus', P + 'region_flow') + sub(dst + 'deficit', P + 'region_flow')
            transfer += add(src + 'power_export', P + 'region_flow') + add(dst + 'power_import', P + 'region_flow')
            transfer += sub(src + 'power', P + 'region_flow') + add(dst + 'power', P + 'region_flow') + add(edge + 'flow', P + 'region_flow')
            transfer += mul('region_flow', .5)
            for n in (src, dst): transfer += sub(n + 'spare_freight', P + 'region_flow') + add(n + 'freight_used', P + 'region_flow')
            body += transfer
        trade += iff(condition, body)
    effects.append(fx('regional_trade', trade))
    # Share the rate calculation across 36 districts rather than expanding the
    # same eight project equations in every district's daily handler.
    rates = ''.join(iff(cv('calc_project', '=', kind), speed('calc_', kind)) for kind in PROJECTS)
    effects.append(fx('regional_rate', rates))
    cached = ('development', 'workers', 'local_power', 'freight', 'infra', 'civs', 'coal', 'steel',
              'training', *(f'done_{k}' for k in PROJECTS), 'base_workers_need', 'base_power_need', 'base_freight_used')
    cache, imports = '', ''
    for c in cells:
        i = c['id']; n = f'n{i}_'
        cache += iff(cv('selected', '=', i), ''.join(setv('preview_' + key, P + n + key) for key in cached))
        body = ''
        for j in c['neighbors']:
            a, b = sorted((i, j)); src = f'n{j}_'
            if (a, b) in sea: continue
            incoming = setv('region_flow', P + 'preview_power_need') + sub('region_flow', P + 'preview_power') + clamp('region_flow', 0, P + src + 'surplus')
            incoming += setv('region_limit', P + 'preview_freight') + sub('region_limit', P + 'preview_freight_used') + clamp('region_limit', 0, 99999) + mul('region_limit', 2) + clamp('region_flow', 0, P + 'region_limit')
            incoming += setv('region_limit', P + src + 'spare_freight') + mul('region_limit', 2) + clamp('region_flow', 0, P + 'region_limit')
            incoming += add('preview_power', P + 'region_flow') + mul('region_flow', .5) + add('preview_freight_used', P + 'region_flow')
            body += iff(cv(f'edge_{a}_{b}_live', '=', 1), incoming)
        imports += iff(cv('selected', '=', i), body)
    effects.append(fx('regional_forecast_imports', imports))
    # An advisory for idle sites; unused neighbour capacity is read without
    # changing any queue, reservation, transfer ledger or persistent reward.
    forecasts = cache
    for kind, spec in PROJECTS.items():
        forecasts += ''.join(setv('preview_' + key, P + 'preview_base_' + key) for key in ('workers_need', 'power_need', 'freight_used'))
        forecasts += setv('preview_power', P + 'preview_local_power') + demand('preview_', kind) + 'RUS_ip_regional_forecast_imports = yes\n'
        forecasts += speed('preview_', kind) + gain('preview_', kind)
        forecasts += setv(f'forecast_{kind}_days', spec['days']) + div(f'forecast_{kind}_days', P + 'preview_speed')
        for key in ('gain', 'training_gain', 'bottleneck'):
            forecasts += setv(f'forecast_{kind}_{key}', P + 'preview_' + key)
    effects.append(fx('regional_forecasts', forecasts))
    return effects
