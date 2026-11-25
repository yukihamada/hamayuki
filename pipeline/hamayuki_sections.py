"""Pick the most eventful phrase-aligned section of each track for the mix (run with the librosa venv).
Grid: kick phase + kick tempo. Phrases: 16 beats, offset chosen where novelty peaks line up.
Score: novelty (checkerboard on beat-synchronous MFCC+chroma) + timbral variance + loudness,
with kicks required in the first and last 32 beats so transitions can be beat-matched."""
import json, os, sys, subprocess
import numpy as np, librosa
sys.path.insert(0, os.path.dirname(__file__))
from hamayuki_master import TMP, BEATS, kick_env, KSR, KH
from hamayuki_music import TRACKS

W = int(os.environ.get('HY_W', 256))  # beats per section (64 bars)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hamayuki_sections.json')

def analyse(f):
    y, sr = librosa.load(f'{TMP}/{f}.master.wav', sr=KSR, mono=True)
    bj = BEATS[f]; bpm = bj['bpm_kick'] if abs(bj.get('bpm_kick', 0) - bj['bpm']) < 1.5 else bj['bpm']
    P = 60 / bpm
    o = kick_env(y); fps = KSR / KH
    ph = np.arange(0, P, 0.001)
    sc = [o[np.clip(np.round(np.arange(p, len(o) / fps, P) * fps).astype(int), 0, len(o) - 1)].sum() for p in ph]
    phase = ph[int(np.argmax(sc))]
    beats = np.arange(phase, len(y) / sr - P, P)
    bf = librosa.time_to_frames(beats, sr=sr, hop_length=512)
    mf = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=512)
    ch = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=512)
    rms = librosa.feature.rms(y=y, hop_length=512)[0]
    F = np.vstack([librosa.util.sync(mf, bf), librosa.util.sync(ch, bf) * 3])
    F = (F - F.mean(1, keepdims=True)) / (F.std(1, keepdims=True) + 1e-9)
    R = librosa.util.sync(rms[None], bf)[0]
    n = F.shape[1]
    S = np.corrcoef(F.T)
    k = 16; nov = np.zeros(n)
    kern = np.kron(np.array([[1, -1], [-1, 1]]), np.ones((k, k)))
    for i in range(k, n - k):
        nov[i] = (S[i - k:i + k, i - k:i + k] * kern).sum()
    nov = np.maximum(0, nov); nov /= nov.max() + 1e-9
    # kick presence per beat
    kb = np.array([o[max(0, int(t * fps) - 2):int(t * fps) + 3].max() for t in beats[:n]])
    kick_on = kb > np.median(kb) * 0.6
    off = int(np.argmax([nov[o_::16].sum() for o_ in range(16)]))  # phrase offset
    best = None
    for s0 in range(off, max(off + 1, n - W + 1), 16):
        e0 = min(n, s0 + W)
        if e0 - s0 < min(W, n - off) - 1: continue
        head = kick_on[s0:s0 + 32].mean(); tail = kick_on[max(s0, e0 - 32):e0].mean()
        score = nov[s0:e0].sum() / 16 + F[:, s0:e0].std(1).mean() * 2 + R[s0:e0].mean() / (R.max() + 1e-9) * 2 + 3 * min(head, tail)
        if best is None or score > best[0]: best = (score, s0, e0, head, tail)
    _, s0, e0, head, tail = best
    return {'start': round(float(beats[s0]), 3), 'end': round(float(beats[min(e0, len(beats) - 1)]), 3), 'beats': int(e0 - s0),
            'full': round(len(y) / sr, 1), 'kick_head': round(float(head), 2), 'kick_tail': round(float(tail), 2), 'bpm': bpm}

if __name__ == '__main__':
    res = json.load(open(OUT)) if os.path.exists(OUT) else {}
    for f, t, b, k in TRACKS:
        if f in res and '--all' not in sys.argv: continue
        res[f] = analyse(f); r = res[f]
        print(f'{f:24s} {r["start"]:6.1f}-{r["end"]:6.1f}s of {r["full"]}s  kicks head/tail {r["kick_head"]}/{r["kick_tail"]}')
        json.dump(res, open(OUT, 'w'), indent=1)
