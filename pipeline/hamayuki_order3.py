"""Surgical reorder: keep the first 16 tracks of v4 EXACTLY as-is (they work),
optimise ONLY the last 8 for a strong 40min+ arc (peak near ~42-43min, warm close).
Same schema output as v4 engine reads."""
import json, os, random, math
HERE = os.path.dirname(os.path.abspath(__file__))
K = json.load(open(os.path.join(HERE, 'hamayuki_keys2.json')))
F = json.load(open(os.path.join(HERE, 'hamayuki_feats.json')))
S = json.load(open(os.path.join(HERE, 'hamayuki_sections.json')))
EFF = {f: dict(v) for f, v in K.items()}
EFF['afro-tech']['camelot'] = '11A'; EFF['afro-tech']['key'] = 'F#m'

FIRST16 = ['first-ember', 'desert-bloom', 'trade-winds', 'blue-hour', 'horizon',
           'tribal-circuit', 'organic-afro-house', 'kapolei-golden-hour',
           'rooftop-lagos', 'sunset-terrace', 'snow-falls-voice', 'log-drum-dawn',
           'lantern-festival', 'disco-ball-rise', 'afro-tech', 'snow-on-the-beach']
LAST8 = ['tidal-turn', 'warm-rise', 'deep-house-afro-intro', 'night-tide',
         'shoreline-glow', 'ember-drive', 'sunset-drive', 'last-light']
CLOSE = 'last-light'


def cam(c): return int(c[:-1]), c[-1]
def hdist(a, b):
    na, la = cam(a); nb, lb = cam(b)
    if la == lb:
        d = abs(na - nb); return min(d, 12 - d)
    if na == nb: return 0.5
    d = abs(na - nb); return min(d, 12 - d) + 1
def cent(f): return F[f]['cent']
def flux(f): return F[f]['flux']
def rise(f): return F[f]['rise']
def energy(f): return K[f].get('energy', 3.0)


def cost(seq):
    """score the last-8 sequence; also account for the join from FIRST16[-1]."""
    full = FIRST16 + seq
    c = 0.0
    # harmonic on the joins inside seq + the entry join
    joints = [(FIRST16[-1], seq[0])] + [(seq[i], seq[i + 1]) for i in range(len(seq) - 1)]
    for a, b in joints:
        d = hdist(EFF[a]['camelot'], EFF[b]['camelot'])
        c += d * 2.0
        if d >= 3: c += 6.0
    # 40min+ zone = roughly the last 6 of the set (positions 18..23 of 24)
    zone = full[18:]
    # want a real build and eventfulness in the 40min+ zone
    best_rise = max(rise(f) for f in zone)
    if best_rise < 0.55: c += (0.55 - best_rise) * 20.0
    best_flux = max(flux(f) for f in zone)
    if best_flux < 1.1: c += (1.1 - best_flux) * 10.0
    # brightness contrast in the zone (avoid a flat warm run)
    cr = max(cent(f) for f in zone) - min(cent(f) for f in zone)
    if cr < 90: c += (90 - cr) * 0.15
    # anti-monotony: no 3 consecutive warm (cent<320) or 3 consecutive mid-similar
    for i in range(len(seq) - 2):
        w = [cent(seq[i]), cent(seq[i + 1]), cent(seq[i + 2])]
        if all(x < 320 for x in w): c += 6.0
    # the peak (highest rise) should land in the 40min+ zone, not too early
    peak_i = max(range(len(seq)), key=lambda i: rise(seq[i]))
    if peak_i < 2: c += 8.0  # peak too early (before 40min)
    # closer must be warm and last
    if seq[-1] != CLOSE: c += 1e6
    # energy should not collapse right before the close
    if energy(seq[-2]) < 2.6: c += (2.6 - energy(seq[-2])) * 3.0
    return c


def anneal(iters=200000, seed=3):
    random.seed(seed)
    cur = [f for f in LAST8 if f != CLOSE]; random.shuffle(cur); cur = cur + [CLOSE]
    cur_c = cost(cur); best, best_c = cur[:], cur_c
    T0, T1 = 5.0, 0.02
    for it in range(iters):
        T = T0 * (T1 / T0) ** (it / iters)
        i, j = random.sample(range(len(cur) - 1), 2)  # keep CLOSE pinned
        cur[i], cur[j] = cur[j], cur[i]
        nc = cost(cur)
        if nc <= cur_c or random.random() < math.exp((cur_c - nc) / T):
            cur_c = nc
            if nc < best_c: best, best_c = cur[:], nc
        else:
            cur[i], cur[j] = cur[j], cur[i]
    return best, best_c


def make_targets(order):
    n = len(order); t = []
    for i in range(n):
        t.append(round(116 + 8 * i / (n - 1), 1))
    t[-1] = 124.0
    return t


if __name__ == '__main__':
    best, bc = anneal()
    order = FIRST16 + best
    tg = make_targets(order)
    plan = []
    for i, f in enumerate(order):
        p = {'f': f, 'bpm': tg[i]}
        if f == 'afro-tech': p['semis'] = 1
        plan.append(p)
    tot = 0
    for i, p in enumerate(plan):
        f = p['f']; c = EFF[f]['camelot']
        nx = EFF[plan[i + 1]['f']]['camelot'] if i + 1 < len(plan) else None
        d = hdist(c, nx) if nx else 0; tot += d
        mark = ' <-- 40min+' if i >= 18 else ''
        print(f'{i:2d} {f:24s} {EFF[f]["key"]:4s} {c:4s} bpm {p["bpm"]:5.1f} '
              f'cent {cent(f):3d} flux {flux(f):.2f} rise {rise(f):.2f} e {energy(f):.2f}{mark}')
    print('cost', round(bc, 2), 'total_hdist', round(tot, 1))
    out = os.path.join(HERE, 'hamayuki_plan_v4.json')
    json.dump({'order': order, 'plan': plan, 'total_hdist': round(tot, 1)}, open(out, 'w'), indent=1)
    print('wrote', out)
