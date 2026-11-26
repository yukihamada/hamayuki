"""HAMAYUKI Sessions #01 — v4 rebuild.

Same proven transition engine as hamayuki_master.py (beat-phase alignment, bass swap,
filter sweeps, short-blend fallback), but:
  * sources are the already-mastered 320k MP3s (page deliverables, -14 LUFS, TP-safe)
  * tempo/pitch via the rubberband CLI (this ffmpeg has no rubberband filter)
  * new harmonic order + BPM ramp from hamayuki_plan_v4.json
  * output is 192k CBR MP3 in 3 parts (matches the shipped #01 format)
Updates master_report.json['mixes']['sessions-01'] so the page regenerates from it.
"""
import json, os, sys, subprocess
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import hamayuki_master as HM

HERE = os.path.dirname(os.path.abspath(__file__))
A = HM.OUT  # mastered per-track MP3s live here
TMP = HM.TMP
SR = HM.SR
S = json.load(open(os.path.join(HERE, 'hamayuki_sections.json')))
BEATS = HM.BEATS
FORCE_SHORT = HM.FORCE_SHORT
load, save, lowband, ffilt = HM.load, HM.save, HM.lowband, HM.ffilt
local_phase = HM.local_phase
measure, finish, run = HM.measure, HM.finish, HM.run


def finish_nores(src_wav, dst_wav):
    """same as HM.finish but without the soxr resampler (unavailable in this ffmpeg build);
    uses the default swr resampler for the 4x-oversampled limiter."""
    TARGET = HM.TARGET; CEIL = HM.CEIL
    m = measure(src_wav); g = TARGET - m['lufs']
    for _ in range(3):
        lim = 10 ** (CEIL / 20)
        run('ffmpeg', '-v', 'error', '-y', '-i', src_wav, '-af',
            f'volume={g:.2f}dB,aresample={SR*4},alimiter=limit={lim:.4f}:attack=3:release=60:level=0,aresample={SR}',
            '-c:a', 'pcm_f32le', dst_wav)
        m2 = measure(dst_wav)
        if abs(m2['lufs'] - TARGET) <= 0.3: break
        g += TARGET - m2['lufs']
    return m2


def stretch(src, dst, ratio, semis=0):
    """rubberband CLI (R3 fine engine). -T is a speed factor (same meaning as ffmpeg tempo).
    Cached: skip if dst already exists and is newer than src."""
    if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
        return
    args = ['rubberband', '-q', '-3', '-F', '--centre-focus', f'-T{ratio:.6f}']
    if semis:
        args.append(f'-p{semis}')
    args += [src, dst]
    run(*args)


def section_src(f, i, n, name):
    """cut the mastered MP3 to its most eventful section (first keeps intro, last keeps outro)."""
    sec = S.get(f)
    src = f'{A}/{f}.mp3'
    out = f'{TMP}/v4_{f}.cut.wav'
    if not sec:
        run('ffmpeg', '-v', 'error', '-y', '-i', src, '-c:a', 'pcm_f32le', out)
        return out
    a = 0 if i == 0 else sec['start']
    b = None if i == n - 1 else sec['end']
    cmd = ['ffmpeg', '-v', 'error', '-y', '-ss', f'{a:.3f}']
    if b is not None:
        cmd += ['-to', f'{b:.3f}']
    cmd += ['-i', src, '-c:a', 'pcm_f32le', out]
    run(*cmd)
    return out


def mp3_part(wav, dst, title, ss, t):
    run('ffmpeg', '-v', 'error', '-y', '-ss', f'{ss:.3f}', '-t', f'{t:.3f}', '-i', wav,
        '-c:a', 'libmp3lame', '-b:a', '192k', '-compression_level', '0', '-joint_stereo', '1',
        '-metadata', f'title={title}', '-metadata', 'artist=HAMAYUKI', dst)


def build_mix(order, name, title, parts, report, beats=32, plan=None):
    n = len(order)
    tgt = [p_['bpm'] for p_ in plan]
    semis = [p_.get('semis', 0) for p_ in plan]
    chapters = []
    out = None; outl = None; starts = [0.0]; diag = []
    for i, f in enumerate(order):
        bj = BEATS[f]
        bpm = bj['bpm_kick'] if abs(bj.get('bpm_kick', 0) - bj['bpm']) < 1.5 else bj['bpm']
        rB = tgt[i] / bpm
        src_i = section_src(f, i, n, name)
        body = f'{TMP}/v4_{name}_{i:02d}.wav'
        stretch(src_i, body, rB, semis[i]); lowband(body, body + '.low.wav')
        Bb = load(body); Bbl = load(body + '.low.wav')
        if i == 0:
            out, outl = Bb, Bbl; continue
        rH = tgt[i - 1] / bpm
        head = f'{TMP}/v4_{name}_{i:02d}.head.wav'
        stretch(src_i, head, rH, semis[i]); lowband(head, head + '.low.wav')
        Bh = load(head); Bhl = load(head + '.low.wav')
        mash = bool(plan[i].get('mash')); nb = 64 if mash else beats
        Ps = 60 / tgt[i - 1]; PA = Ps * SR; L = int(round(nb * PA))
        gA0, qa = local_phase(out, len(out) - L - 8 * PA, len(out), Ps)
        m = int(np.floor((len(out) - L - gA0) / PA)); sA = int(round(gA0 + m * PA))
        gB0, qb = local_phase(Bh, 0, min(len(Bh), 40 * PA), Ps)
        hs = int(round(gB0 % PA))
        while hs < 0.2 * SR: hs += int(round(PA))
        L = min(L, len(out) - sA, len(Bh) - hs)
        for _ in range(2):
            hp = hs + L; bs_ = int(round(hp * rH / rB)); Pb = 60 / tgt[i] * SR
            gBb, qbb = local_phase(Bb, bs_, min(len(Bb), bs_ + 32 * Pb), 60 / tgt[i])
            if qbb < 1.4: break
            pos = sA + L + (gBb - bs_)
            e = ((pos - gA0) % PA + PA / 2) % PA - PA / 2
            if abs(e) < 0.004 * SR: break
            hs = int(round(hs + e))
            while hs < 0.2 * SR: hs += int(round(PA))
            L = min(int(round(nb * PA)), len(out) - sA, len(Bh) - hs)
        hp = hs + L; bs_ = int(round(hp * rH / rB)); Pb = 60 / tgt[i] * SR
        gBb, qbb = local_phase(Bb, bs_, min(len(Bb), bs_ + 32 * Pb), 60 / tgt[i])
        e_ms = (((sA + L + (gBb - bs_)) - gA0) % PA + PA / 2) % PA - PA / 2
        e_ms = e_ms / SR * 1000
        short = (abs(e_ms) > 25 or qa < 1.4 or (order[i - 1], f) in FORCE_SHORT or plan[i].get('short')) and not mash
        if short:
            Ls = int(round(8 * PA)); m = int(np.floor((len(out) - Ls - gA0) / PA)); sA = int(round(gA0 + m * PA))
            L = min(Ls, len(out) - sA, len(Bh) - hs)
        tau = np.linspace(0, 1, L, endpoint=False)[:, None]
        gA = np.cos(tau * np.pi / 2); gB = np.sin(tau * np.pi / 2)
        if mash:
            gA = np.clip((1 - tau) / 0.25, 0, 1) ** 0.5 * 0.9; gB = np.clip(tau / 0.15, 0, 1) ** 0.5 * 0.9
        mid = (L // 2) - ((L // 2) % 1); w = int(PA)
        bA = np.ones((L, 1)); seg_ = min(w, L - mid); bA[mid:mid + seg_, 0] = np.linspace(1, 0, seg_); bA[mid + seg_:] = 0; bB = 1 - bA
        Alo = outl[sA:sA + L]; Ahi = out[sA:sA + L] - Alo
        Blo = Bhl[hs:hs + L]; Bhi = Bh[hs:hs + L] - Blo
        sw = tau ** 1.5
        Ahp = ffilt(out[sA:sA + L], 'highpass=f=420:poles=2,highpass=f=420:poles=2')
        Blp = ffilt(Bh[hs:hs + L] - Bhl[hs:hs + L], 'lowpass=f=1600:poles=2')
        Ahi = Ahi * (1 - sw) + Ahp * sw
        op = np.clip(tau / 0.75, 0, 1)
        Bhi = Blp * (1 - op) + Bhi * op
        x = Ahi * gA + Bhi * gB + Alo * bA + Blo * bB; xl = Alo * bA + Blo * bB
        hp = hs + L; bs0 = int(round(hp * rH / rB))
        ref = Bhl[max(0, hp - SR // 2):hp].mean(axis=1)
        best = (None, bs0)
        for d in range(-int(0.025 * SR), int(0.025 * SR) + 1, 8):
            c = Bbl[max(0, bs0 + d - len(ref)):bs0 + d].mean(axis=1)
            if len(c) != len(ref): continue
            v = float(np.dot(ref, c))
            if best[0] is None or v > best[0]: best = (v, bs0 + d)
        bs = best[1]
        z = int(0.01 * SR); r_ = np.linspace(0, 1, z)[:, None]
        nz = min(z, len(Bh) - hp, len(Bb) - bs)
        spl = Bh[hp:hp + nz] * (1 - r_[:nz]) + Bb[bs:bs + nz] * r_[:nz]
        spl_l = Bhl[hp:hp + nz] * (1 - r_[:nz]) + Bbl[bs:bs + nz] * r_[:nz]
        out = np.concatenate([out[:sA], x, spl, Bb[bs + nz:]]); outl = np.concatenate([outl[:sA], xl, spl_l, Bbl[bs + nz:]])
        chapters.append(round((sA + L // 2) / SR, 2)); starts.append(round(sA / SR, 3))
        diag.append({'from': order[i - 1], 'to': f, 'pred_err_ms': round(float(e_ms), 1), 'short_blend': bool(short),
                     'kick_conf_out': round(float(qa), 2), 'kick_conf_in': round(float(qb), 2)})
        print('joined', order[i - 1], '->', f, 'overlap', round(L / SR, 1), 's', 'conf', round(qa, 2), round(qb, 2), 'short' if short else '')
    if plan and any(p_.get('drop') for p_ in plan):
        out = HM.voice_drops(out, outl, plan, [0.0] + chapters)
    raw = f'{TMP}/{name}.v4.raw.wav'; save(out, raw)
    run('ffmpeg', '-v', 'error', '-y', '-i', raw, '-af', 'afade=t=in:d=2', '-c:a', 'pcm_f32le', f'{TMP}/{name}.v4.fade.wav')
    # persist the join structure now, before the (separately-fallible) limiter step
    D = len(out) / SR
    report['mixes'][name] = {'minutes': round(D / 60, 2), 'files': [], 'master_wav': f'{TMP}/{name}.v4.master.wav',
                             'parts': [], 'starts': starts, 'transitions': diag, 'chapters': [0.0] + chapters,
                             'order': order, 'duration': round(D, 2), 'format': 'mp3 192k CBR'}
    json.dump(report, open(HM.REPORT + '.tmp', 'w'), indent=1, default=float); os.replace(HM.REPORT + '.tmp', HM.REPORT)
    print('saved structure: duration', round(D, 2), 's,', len(chapters), 'joins')
    mixm = f'{TMP}/{name}.v4.master.wav'
    _c = HM.CEIL; HM.CEIL = HM.MIX_CEIL; mm = finish_nores(f'{TMP}/{name}.v4.fade.wav', mixm); HM.CEIL = _c
    files = []
    for p in range(parts):
        a, b = D * p / parts, D * (p + 1) / parts
        fn = f'{name}-{p + 1}.mp3'
        mp3_part(mixm, f'{A}/{fn}', title + (f' (Part {p + 1})' if parts > 1 else ''), a, b - a)
        sz = os.path.getsize(f'{A}/{fn}') / 1048576
        assert sz < 24.5, f'{fn} too big {sz:.1f} MiB'
        files.append(fn)
    enc = [measure(f'{A}/{f}') for f in files]
    report['mixes'][name] = {'minutes': round(D / 60, 2), 'files': files, 'master_wav': mm, 'parts': enc,
                             'starts': starts, 'transitions': diag, 'chapters': [0.0] + chapters,
                             'order': order, 'duration': round(D, 2), 'format': 'mp3 192k CBR'}
    print(name, round(D / 60, 1), 'min', files)
    return files, D


def make_plan():
    p = json.load(open(os.path.join(HERE, 'hamayuki_plan_v4.json')))['plan']
    # mark short blends at the jarring harmonic jumps; keep a couple of voice tags
    short_pairs = {('first-ember', 'desert-bloom'), ('night-tide', 'shoreline-glow'), ('sunset-drive', 'last-light')}
    for i, e in enumerate(p):
        if i > 0 and (p[i - 1]['f'], e['f']) in short_pairs:
            e['short'] = True
    # voice tags (KOE synthesized from his own voice): opener, a peak, the closer
    drops = {'first-ember': ('tag2', 24), 'ember-drive': ('tag1', 6), 'last-light': ('v3', 60)}
    for e in p:
        if e['f'] in drops:
            e['drop'] = drops[e['f']]
    return p


if __name__ == '__main__':
    report = json.load(open(HM.REPORT))
    plan = make_plan()
    order = [e['f'] for e in plan]
    build_mix(order, 'sessions-01', 'HAMAYUKI Sessions #01', 3, report, plan=plan)
    tmp = HM.REPORT + '.tmp'
    json.dump(report, open(tmp, 'w'), indent=1, default=float)
    os.replace(tmp, HM.REPORT)
    print('updated', HM.REPORT)
