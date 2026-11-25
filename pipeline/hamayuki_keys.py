"""Key (Krumhansl-Schmuckler on CQT chroma of the chosen section) and energy (loudness + onset density) per track."""
import json, os, sys, numpy as np, librosa
sys.path.insert(0, os.path.dirname(__file__))
from hamayuki_master import TMP
from hamayuki_music import TRACKS
SEC = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hamayuki_sections.json')))
MAJ = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MIN = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
CAM_MAJ = {0: '8B', 7: '9B', 2: '10B', 9: '11B', 4: '12B', 11: '1B', 6: '2B', 1: '3B', 8: '4B', 3: '5B', 10: '6B', 5: '7B'}
CAM_MIN = {9: '8A', 4: '9A', 11: '10A', 6: '11A', 1: '12A', 8: '1A', 3: '2A', 10: '3A', 5: '4A', 0: '5A', 7: '6A', 2: '7A'}
out = {}
for f, t, b, k in TRACKS:
    s = SEC[f]
    y, sr = librosa.load(f'{TMP}/{f}.master.wav', sr=22050, mono=True, offset=s['start'], duration=s['end'] - s['start'])
    yh = librosa.effects.harmonic(y)
    c = librosa.feature.chroma_cqt(y=yh, sr=sr).mean(1)
    sc = [(np.corrcoef(np.roll(MAJ, i), c)[0, 1], i, 'maj') for i in range(12)] + [(np.corrcoef(np.roll(MIN, i), c)[0, 1], i, 'min') for i in range(12)]
    sc.sort(reverse=True); r, i, mode = sc[0]
    cam = CAM_MAJ[i] if mode == 'maj' else CAM_MIN[i]
    rms = librosa.feature.rms(y=y)[0]; on = librosa.onset.onset_strength(y=y, sr=sr)
    energy = float(np.mean(rms) * 10 + np.mean(on) * 0.5)
    out[f] = {'key': NAMES[i] + ('' if mode == 'maj' else 'm'), 'camelot': cam, 'conf': round(float(r - sc[1][0]), 3), 'r': round(float(r), 3), 'energy': round(energy, 3)}
    print(f'{f:24s} {out[f]["key"]:4s} {cam:4s} conf {out[f]["conf"]:.3f} energy {energy:.2f}')
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hamayuki_keys.json'), 'w'), indent=1)
