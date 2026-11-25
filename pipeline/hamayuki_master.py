"""HAMAYUKI mastering v2.

Tracks: original source (MUREKA raw / SOLUNA 256k MP3) -> decode once to float ->
  subsonic high-pass 25 Hz -> gentle glue compression (1.5:1) -> gain to -14 LUFS (measured) ->
  true-peak-safe limiter (-1.5 dBFS ceiling, 4x oversampled) -> one lossy encode (MP3 320k, LAME q0).
Mixes: same mastered PCM per track, stretched (rubberband, crisp transients) onto a 116->124 BPM ramp,
  beat-phase aligned at the middle of each 24-beat overlap, bass swapped at the midpoint,
  bus-limited, encoded once as AAC (AudioToolbox) in parts under the 25 MiB Pages limit.
Every output is re-measured (integrated LUFS, true peak) and written to master_report.json."""
import subprocess, os, sys, json, re, math
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from hamayuki_music import TRACKS, MIX00

HOME = os.path.expanduser('~')
OUT = f'{HOME}/workspace/pacifica-dance/hamayuki/audio'
SCR = os.environ.get('HY_WORK', 'work')
TMP = f'{SCR}/master2'; os.makedirs(TMP, exist_ok=True)
RAW = f'{HOME}/workspace/soluna-web/dist-tracks'
SOL = f'{SCR}/hyaudio'
VOICE = f'{HOME}/workspace/tasks/dj-rating-20261124/hamayuki/voice'
REPORT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'master_report.json')
SR = 44100
SRC = {  # page file -> original source
    'first-ember': f'{RAW}/hamayuki-first-ember.raw.mp3', 'snow-on-the-beach': f'{RAW}/hamayuki-snow-on-the-beach.raw.mp3',
    'shoreline-glow': f'{RAW}/hamayuki-shoreline-glow.raw.mp3', 'kapolei-golden-hour': f'{RAW}/hamayuki-kapolei-golden-hour.raw.mp3',
    'blue-hour': f'{RAW}/hamayuki-blue-hour.raw.mp3', 'handover': f'{RAW}/hamayuki-handover.raw.mp3', 'last-wave': f'{RAW}/hamayuki-last-wave.raw.mp3', 'tidal-turn': f'{RAW}/hamayuki-tidal-turn.raw.mp3', 'lantern-festival': f'{RAW}/hamayuki-lantern-festival.raw.mp3', 'moonrise-run': f'{RAW}/hamayuki-moonrise-run.raw.mp3',
    'sunset-drive': f'{SOL}/mid-3.mp3', 'log-drum-dawn': f'{SOL}/amapiano.mp3', 'desert-bloom': f'{SOL}/world-4.mp3', 'sunset-terrace': f'{SOL}/afro.mp3', 'uplift': f'{SOL}/build-2.mp3',
    'horizon': f'{SOL}/mid-1.mp3', 'rooftop-lagos': f'{SOL}/world-1.mp3', 'trade-winds': f'{SOL}/mid-2.mp3', 'tribal-circuit': f'{SOL}/afro-tech.mp3',
    'disco-ball-rise': f'{SOL}/peak-9.mp3', 'organic-afro-house': f'{SOL}/vocal-organic-house-afro.mp3',
    'deep-house-afro-intro': f'{SOL}/vocal-deep-house-afro.mp3', 'afro-tech': f'{SOL}/vocal-afro-tech-afro.mp3',
}
TITLE = {f: t for f, t, b, k in TRACKS}
CEIL = -1.5  # dBFS sample ceiling before encode (tracks)
MIX_CEIL = -2.8  # AAC overshoots more; keeps encoded true peak under -1 dBTP
TARGET = -14.0

def run(*a): subprocess.run(list(a), check=True)

def measure(path):
    o = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-af', 'ebur128=peak=true:framelog=quiet', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    I = float(re.findall(r'I:\s+(-?[\d.]+) LUFS', o)[-1]); tp = float(re.findall(r'Peak:\s+(-?[\d.]+) dBFS', o)[-1])
    lra = float(re.findall(r'LRA:\s+(-?[\d.]+) LU', o)[-1])
    return {'lufs': I, 'true_peak': tp, 'lra': lra}

def pre(src, dst, extra=''):
    """decode once, subsonic HPF + glue compression, float WAV"""
    af = f'aresample={SR}:resampler=soxr:precision=28,highpass=f=25:poles=2,acompressor=threshold=-18dB:ratio=1.5:attack=30:release=250:knee=6:makeup=1' + extra
    run('ffmpeg', '-v', 'error', '-y', '-i', src, '-af', af, '-ac', '2', '-c:a', 'pcm_f32le', dst)

def finish(src_wav, dst_wav):
    """gain to TARGET then 4x-oversampled limiter at CEIL; iterate once if limiting pulled loudness down"""
    m = measure(src_wav); g = TARGET - m['lufs']
    for _ in range(2):
        lim = 10 ** (CEIL / 20)
        run('ffmpeg', '-v', 'error', '-y', '-i', src_wav, '-af',
            f'volume={g:.2f}dB,aresample={SR*4}:resampler=soxr,alimiter=limit={lim:.4f}:attack=3:release=60:level=0,aresample={SR}:resampler=soxr:precision=28',
            '-c:a', 'pcm_f32le', dst_wav)
        m2 = measure(dst_wav)
        if abs(m2['lufs'] - TARGET) <= 0.3: break
        g += TARGET - m2['lufs']
    return m2

def mp3(wav, dst, title):
    run('ffmpeg', '-v', 'error', '-y', '-i', wav, '-c:a', 'libmp3lame', '-b:a', '320k', '-compression_level', '0', '-joint_stereo', '1',
        '-metadata', f'title={title}', '-metadata', 'artist=HAMAYUKI', dst)

def aac(wav, dst, title, br, ss=None, t=None):
    cmd = ['ffmpeg', '-v', 'error', '-y'] + (['-ss', f'{ss:.3f}', '-t', f'{t:.3f}'] if ss is not None else []) + ['-i', wav,
           '-c:a', 'aac_at', '-b:a', br, '-aac_at_quality', '0', '-movflags', '+faststart',
           '-metadata', f'title={title}', '-metadata', 'artist=HAMAYUKI', dst]
    run(*cmd)

def voice_track(dst_pre):
    """bed (pre-processed) + KOE voice lines, ducked; returns pre-master float wav"""
    bed = f'{TMP}/bed.wav'; pre(f'{RAW}/hamayuki-voice-bed.raw.mp3', bed)
    fc = ('[1:a]aresample=44100:resampler=soxr,adelay=6000|6000[a1];[2:a]aresample=44100:resampler=soxr,adelay=113000|113000[a2];'
          '[3:a]aresample=44100:resampler=soxr,adelay=166500|166500[a3];'
          '[a1][a2][a3]amix=inputs=3:normalize=0:duration=longest,highpass=f=100,equalizer=f=3000:t=q:w=1.2:g=2,'
          'acompressor=threshold=-22dB:ratio=3:attack=4:release=120:makeup=2,volume=1.6,'
          'aecho=0.85:0.55:80|210:0.20|0.10,apad=whole_dur=181,asplit=2[vo][sc];'
          '[0:a]apad=whole_dur=181[bd];[bd][sc]sidechaincompress=threshold=0.04:ratio=4:attack=15:release=450[duck];'
          '[duck][vo]amix=inputs=2:normalize=0:duration=longest,atrim=0:179.6,afade=t=out:st=175:d=4.6[out]')
    run('ffmpeg', '-v', 'error', '-y', '-i', bed, '-i', f'{VOICE}/v1.mp3', '-i', f'{VOICE}/v2.mp3', '-i', f'{VOICE}/v3.mp3',
        '-filter_complex', fc, '-map', '[out]', '-c:a', 'pcm_f32le', dst_pre)

def master_tracks(report):
    for f, t, b, k in TRACKS:
        p = f'{TMP}/{f}.pre.wav'; m = f'{TMP}/{f}.master.wav'
        if f == 'snow-falls-voice': voice_track(p)
        else: pre(SRC[f], p)
        src_m = measure(p); out_m = finish(p, m)
        mp3(m, f'{OUT}/{f}.mp3', t)
        enc = measure(f'{OUT}/{f}.mp3')
        report['tracks'][f] = {'source': src_m, 'master_wav': out_m, 'mp3_320': enc}
        print(f, src_m['lufs'], '->', enc['lufs'], 'TP', enc['true_peak'])

# ---------- mix engine ----------
def load(path):
    b = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', path, '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'])
    return np.frombuffer(b, np.float32).reshape(-1, 2).copy()

def save(x, path):
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-i', '-', '-c:a', 'pcm_f32le', path], stdin=subprocess.PIPE)
    p.communicate(x.astype(np.float32).tobytes())

def stretch(src, dst, ratio, semis=0):
    run('ffmpeg', '-v', 'error', '-y', '-i', src, '-af',
        f'rubberband=tempo={ratio:.6f}:pitch={2 ** (semis / 12):.6f}:transients=crisp:detector=percussive:phase=laminar:pitchq=quality:formant=preserved:channels=together',
        '-c:a', 'pcm_f32le', dst)

def lowband(src, dst):
    run('ffmpeg', '-v', 'error', '-y', '-i', src, '-af', 'lowpass=f=160:poles=2,lowpass=f=160:poles=2', '-c:a', 'pcm_f32le', dst)

def beat_phase(low, period, lo, hi):
    """phase (samples) of the kick grid inside low[lo:hi] given beat period in samples"""
    hop = 128; seg = low[lo:hi].mean(axis=1)
    n = len(seg) // hop
    if n < 8: return 0.0
    e = np.sqrt((seg[:n * hop].reshape(n, hop) ** 2).mean(axis=1))
    on = np.maximum(0, np.diff(e, prepend=e[0]))
    bins = 96; hist = np.zeros(bins)
    idx = ((np.arange(n) * hop) % period) / period * bins
    np.add.at(hist, idx.astype(int) % bins, on)
    hist = np.convolve(np.r_[hist[-2:], hist, hist[:2]], [0.25, 0.5, 1, 0.5, 0.25], 'same')[2:-2]
    ph = np.argmax(hist) / bins * period
    return (lo + ph) % period

BEATS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hamayuki_beats.json')))

KSR = 22050; KH = 64

def kick_env(y):
    """kick = low thump (35-110 Hz percussive flux) coinciding with a broadband percussive attack;
    offbeat bass (low, no attack) and hats (attack, no low) are suppressed by the product."""
    import librosa
    S = np.abs(librosa.stft(y, n_fft=1024, hop_length=KH))
    Hp, _ = librosa.decompose.hpss(S, margin=2.0)
    f = librosa.fft_frequencies(sr=KSR, n_fft=1024)
    lo = np.log1p(Hp[(f >= 35) & (f <= 110)].sum(0) * 10); lo = np.maximum(0, np.diff(lo, prepend=lo[0]))
    md = np.log1p(Hp[(f >= 1500) & (f <= 6000)].sum(0) * 10); md = np.maximum(0, np.diff(md, prepend=md[0]))
    md = np.convolve(md, np.ones(3) / 3, 'same')
    return lo * (md / (md.mean() + 1e-9))

def kick_phase(seg, period_s):
    """(phase seconds within seg, kick-vs-halfbeat contrast)"""
    import librosa
    y = librosa.resample(seg.mean(axis=1), orig_sr=SR, target_sr=KSR)
    o = kick_env(y); fps = KSR / KH
    ph = np.arange(0, period_s, 0.0005); sc = []
    for p in ph:
        k = np.round(np.arange(p, len(o) / fps, period_s) * fps).astype(int); k = k[k < len(o)]
        sc.append(o[k].sum() + 0.5 * o[np.clip(k - 1, 0, None)].sum() + 0.5 * o[np.clip(k + 1, None, len(o) - 1)].sum())
    sc = np.array(sc); i = int(np.argmax(sc)); j = (i + len(ph) // 2) % len(ph)
    return ph[i], float(sc[i] / (sc[j] + 1e-9))

def local_phase(x, lo, hi, period_s, min_contrast=1.6, grow=(1, 1.6, 2.5, 4)):
    """kick phase measured as close to [lo,hi) as possible; widen the window if the kick is weak there"""
    best = None
    for g in grow:
        c = (lo + hi) / 2; h = (hi - lo) / 2 * g
        a = int(max(0, c - h)); b = int(min(len(x), c + h))
        ph, con = kick_phase(x[a:b], period_s)
        if best is None or con > best[2]: best = (a + ph * SR, a, con)
        if con >= min_contrast: break
    return best[0], best[2]

# transitions where the two independent grid measurements disagree (verified 2026-11-25): keep the blend short
FORCE_SHORT = {('sunset-terrace', 'trade-winds'), ('uplift', 'tribal-circuit'), ('afro-tech', 'handover'), ('handover', 'last-wave'),
               ('kapolei-golden-hour', 'uplift'), ('uplift', 'handover')}

SECTIONS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hamayuki_sections.json')

def section_src(f, i, n, name):
    """master cut to its most eventful section (first track keeps its intro, last keeps its outro)"""
    if name != 'sessions-01' or not os.path.exists(SECTIONS_PATH): return f'{TMP}/{f}.master.wav'
    sec = json.load(open(SECTIONS_PATH)).get(f)
    if not sec: return f'{TMP}/{f}.master.wav'
    a = 0 if i == 0 else sec['start']; b = None if i == n - 1 else sec['end']
    out = f'{TMP}/{f}.cut.wav'
    run('ffmpeg', '-v', 'error', '-y', '-ss', f'{a:.3f}', *(['-to', f'{b:.3f}'] if b else []), '-i', f'{TMP}/{f}.master.wav', '-c:a', 'pcm_f32le', out)
    return out

def ffilt(x, af):
    p = subprocess.run(['ffmpeg', '-v', 'error', '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-i', '-', '-af', af, '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'],
                       input=x.astype(np.float32).tobytes(), capture_output=True, check=True)
    y = np.frombuffer(p.stdout, np.float32).reshape(-1, 2)
    return np.pad(y, ((0, max(0, len(x) - len(y))), (0, 0)))[:len(x)]

def voice_drops(out, outl, plan, chap):
    """overlay HAMAYUKI voice tags (KOE synthesized from his own voice) at chosen moments, with a short duck"""
    for i, p_ in enumerate(plan):
        if not p_.get('drop'): continue
        clip, after = p_['drop']
        v = load(f'{VOICE}/{clip}.mp3')
        v = ffilt(v, 'highpass=f=110,acompressor=threshold=-20dB:ratio=3:attack=4:release=120:makeup=2,aecho=0.85:0.5:90|240:0.25|0.12,volume=1.5')
        v = np.pad(v, ((0, int(1.2 * SR)), (0, 0)))
        at = int((chap[i] + after) * SR)
        if at + len(v) > len(out): continue
        env = np.ones((len(v), 1)); r_ = int(0.15 * SR)
        duck = 0.55
        g = np.full((len(v), 1), duck); g[:r_, 0] = np.linspace(1, duck, r_); g[-r_:, 0] = np.linspace(duck, 1, r_)
        out[at:at + len(v)] = out[at:at + len(v)] * g + v
        print('voice drop', clip, 'at', round(at / SR, 1), 's')
    return out

# Sessions #01 v3 plan: energy arc (rise / mid dip with the voice track and an amapiano surprise / climb / peak),
# harmonic fixes (afro-tech +1 semitone into F#m), one 64-beat mash-up, voice tags.
PLAN01 = [
    {'f': 'first-ember', 'bpm': 116.0, 'drop': ('tag2', 24)},
    {'f': 'sunset-drive', 'bpm': 116.5, 'short': True},
    {'f': 'horizon', 'bpm': 117.0},
    {'f': 'rooftop-lagos', 'bpm': 117.5},
    {'f': 'desert-bloom', 'bpm': 118.0},
    {'f': 'organic-afro-house', 'bpm': 118.0, 'short': True},
    {'f': 'snow-on-the-beach', 'bpm': 118.5},
    {'f': 'sunset-terrace', 'bpm': 119.0, 'short': True},
    {'f': 'trade-winds', 'bpm': 120.0, 'short': True},
    {'f': 'shoreline-glow', 'bpm': 120.0},
    {'f': 'snow-falls-voice', 'bpm': 117.0},
    {'f': 'log-drum-dawn', 'bpm': 114.0, 'short': True},
    {'f': 'deep-house-afro-intro', 'bpm': 119.0, 'short': True, 'drop': ('v1', 4)},
    {'f': 'tidal-turn', 'bpm': 121.0},
    {'f': 'kapolei-golden-hour', 'bpm': 122.0, 'short': True},
    {'f': 'lantern-festival', 'bpm': 122.5},
    {'f': 'blue-hour', 'bpm': 123.0, 'mash': True},
    {'f': 'disco-ball-rise', 'bpm': 123.0},
    {'f': 'moonrise-run', 'bpm': 124.0, 'drop': ('tag1', 6)},
    {'f': 'afro-tech', 'bpm': 124.0, 'semis': 1},
    {'f': 'tribal-circuit', 'bpm': 124.0, 'short': True},
    {'f': 'uplift', 'bpm': 124.0, 'short': True},
    {'f': 'handover', 'bpm': 124.0, 'short': True},
    {'f': 'last-wave', 'bpm': 124.0, 'short': True, 'drop': ('v3', 60)},
]

def build_mix(order, name, title, parts, br, report, beats=32, plan=None):
    """DJ-style transitions measured on the audio itself: the incoming head runs at the outgoing
    tempo, its kick grid is laid on the outgoing kick grid (both measured locally from the kick
    drum), lows swap over one beat at the midpoint, then the track returns to its own tempo."""
    n = len(order)
    tgt = [p_['bpm'] for p_ in plan] if plan else [116 + 8 * i / (n - 1) for i in range(n)]
    semis = [p_.get('semis', 0) for p_ in plan] if plan else [0] * n
    chapters = []
    out = None; outl = None; starts = [0.0]; diag = []
    for i, f in enumerate(order):
        bj = BEATS[f]; bpm = bj['bpm_kick'] if abs(bj.get('bpm_kick', 0) - bj['bpm']) < 1.5 else bj['bpm']; rB = tgt[i] / bpm
        src_i = section_src(f, i, n, name); body = f'{TMP}/mx_{name}_{i:02d}.wav'; stretch(src_i, body, rB, semis[i]); lowband(body, body + '.low.wav')
        Bb = load(body); Bbl = load(body + '.low.wav')
        if i == 0:
            out, outl = Bb, Bbl; continue
        rH = tgt[i - 1] / bpm
        head = f'{TMP}/mx_{name}_{i:02d}.head.wav'; stretch(src_i, head, rH, semis[i]); lowband(head, head + '.low.wav')
        Bh = load(head); Bhl = load(head + '.low.wav')
        mash = bool(plan and plan[i].get('mash')); nb = 64 if mash else beats
        Ps = 60 / tgt[i - 1]; PA = Ps * SR; L = int(round(nb * PA))
        # outgoing grid measured around the overlap itself (last L + 8 beats of the running mix)
        gA0, qa = local_phase(out, len(out) - L - 8 * PA, len(out), Ps)
        m = int(np.floor((len(out) - L - gA0) / PA)); sA = int(round(gA0 + m * PA))
        # incoming grid measured over its first 40 beats at the outgoing tempo
        gB0, qb = local_phase(Bh, 0, min(len(Bh), 40 * PA), Ps)
        hs = int(round(gB0 % PA))
        while hs < 0.2 * SR: hs += int(round(PA))
        L = min(L, len(out) - sA, len(Bh) - hs)
        # continuity check on pure audio: B's body kick grid (after the overlap) must land on A's grid
        for _ in range(2):
            hp = hs + L; bs_ = int(round(hp * rH / rB))
            Pb = 60 / tgt[i] * SR
            gBb, qbb = local_phase(Bb, bs_, min(len(Bb), bs_ + 32 * Pb), 60 / tgt[i])
            if qbb < 1.4: break
            pos = sA + L + (gBb - bs_)
            e = ((pos - gA0) % PA + PA / 2) % PA - PA / 2
            if abs(e) < 0.004 * SR: break
            hs = int(round(hs + e))
            while hs < 0.2 * SR: hs += int(round(PA))
            L = min(int(round(nb * PA)), len(out) - sA, len(Bh) - hs)
        # if continuity still can't be confirmed, use a short 8-beat blend so any residual offset is brief
        hp = hs + L; bs_ = int(round(hp * rH / rB)); Pb = 60 / tgt[i] * SR
        gBb, qbb = local_phase(Bb, bs_, min(len(Bb), bs_ + 32 * Pb), 60 / tgt[i])
        e_ms = (((sA + L + (gBb - bs_)) - gA0) % PA + PA / 2) % PA - PA / 2
        e_ms = e_ms / SR * 1000
        short = (abs(e_ms) > 25 or qa < 1.4 or (order[i - 1], f) in FORCE_SHORT or bool(plan and plan[i].get('short'))) and not mash
        if short:
            Ls = int(round(8 * PA)); m = int(np.floor((len(out) - Ls - gA0) / PA)); sA = int(round(gA0 + m * PA))
            L = min(Ls, len(out) - sA, len(Bh) - hs)
        tau = np.linspace(0, 1, L, endpoint=False)[:, None]
        gA = np.cos(tau * np.pi / 2); gB = np.sin(tau * np.pi / 2)
        if mash:  # both tracks play together for most of the blend, then A bows out
            gA = np.clip((1 - tau) / 0.25, 0, 1) ** 0.5 * 0.9; gB = np.clip(tau / 0.15, 0, 1) ** 0.5 * 0.9
        mid = (L // 2) - ((L // 2) % 1); w = int(PA)
        bA = np.ones((L, 1)); seg_ = min(w, L - mid); bA[mid:mid + seg_, 0] = np.linspace(1, 0, seg_); bA[mid + seg_:] = 0; bB = 1 - bA
        Alo = outl[sA:sA + L]; Ahi = out[sA:sA + L] - Alo
        Blo = Bhl[hs:hs + L]; Bhi = Bh[hs:hs + L] - Blo
        # filter sweep: the outgoing track thins out (high-pass rises), the incoming one opens up (low-pass lifts)
        sw = tau ** 1.5
        Ahp = ffilt(out[sA:sA + L], 'highpass=f=420:poles=2,highpass=f=420:poles=2')
        Blp = ffilt(Bh[hs:hs + L] - Bhl[hs:hs + L], 'lowpass=f=1600:poles=2')
        Ahi = Ahi * (1 - sw) + Ahp * sw
        op = np.clip(tau / 0.75, 0, 1)
        Bhi = Blp * (1 - op) + Bhi * op
        x = Ahi * gA + Bhi * gB + Alo * bA + Blo * bB; xl = Alo * bA + Blo * bB
        # head -> body at the same musical point, refined by envelope cross-correlation (+-25 ms)
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
        chapters.append(round((sA + L // 2) / SR, 2)); starts.append(round(sA / SR, 3)); diag.append({'from': order[i - 1], 'to': f, 'pred_err_ms': round(float(e_ms), 1), 'short_blend': bool(short), 'kick_conf_out': round(float(qa), 2), 'kick_conf_in': round(float(qb), 2)})
        print('joined', order[i - 1], '->', f, 'overlap', round(L / SR, 1), 's', 'conf', round(qa, 2), round(qb, 2))
    if plan:
        out = voice_drops(out, outl, plan, [0.0] + chapters)
    raw = f'{TMP}/{name}.raw.wav'; save(out, raw)
    run('ffmpeg', '-v', 'error', '-y', '-i', raw, '-af', 'afade=t=in:d=2', '-c:a', 'pcm_f32le', f'{TMP}/{name}.fade.wav')
    mixm = f'{TMP}/{name}.master.wav'
    global CEIL; _c = CEIL; CEIL = MIX_CEIL; mm = finish(f'{TMP}/{name}.fade.wav', mixm); CEIL = _c
    D = len(out) / SR; files = []
    for p in range(parts):
        a, b = D * p / parts, D * (p + 1) / parts
        fn = f'{name}-{p + 1}.m4a' if parts > 1 else f'{name}.m4a'
        aac(mixm, f'{OUT}/{fn}', title + (f' (Part {p + 1})' if parts > 1 else ''), br, a, b - a)
        sz = os.path.getsize(f'{OUT}/{fn}') / 1048576
        assert sz < 24.5, f'{fn} too big {sz:.1f} MiB'
        files.append(fn)
    enc = [measure(f'{OUT}/{f}') for f in files]
    report['mixes'][name] = {'minutes': round(D / 60, 2), 'files': files, 'master_wav': mm, 'parts': enc, 'starts': starts, 'transitions': diag, 'chapters': [0.0] + chapters, 'order': order, 'duration': round(D, 2)}
    print(name, round(D / 60, 1), 'min', files)
    return files, D

if __name__ == '__main__':
    try: report = json.load(open(REPORT))
    except Exception: report = {'tracks': {}, 'mixes': {}}
    if not report.get('tracks'):
        for f, t, b, k in TRACKS: report['tracks'][f] = {'mp3_320': measure(f'{OUT}/{f}.mp3'), 'master_wav': measure(f'{TMP}/{f}.master.wav')}
    what = sys.argv[1:] or ['tracks', 'mixes']
    if 'tracks' in what: master_tracks(report)
    if 'mixonly' in what: what = ['mixes']
    if 'mixes' in what:
        build_mix([p_['f'] for p_ in PLAN01], 'sessions-01', 'HAMAYUKI Sessions #01', 3, '160k', report, plan=PLAN01)
        if 'with00' in what: build_mix(MIX00, 'sunset-mix-00', 'HAMAYUKI Sunset Mix #00', 1, '144k', report)
    tmp = REPORT + '.tmp'; json.dump(report, open(tmp, 'w'), indent=1, default=float); os.replace(tmp, REPORT)
