#!/usr/bin/env python3
"""Build /hamayuki/peaks.json: waveform bars for every mp3 in hamayuki/audio.
Usage: python3 scripts/build-hamayuki-peaks.py   (needs ffmpeg/ffprobe)
Bars are RMS per bucket in dB, stretched between each file's quiet 10th
percentile and its 99th percentile (-> 6..99, curve 2.2), so heavily mastered house still
shows its shape (intros, breakdowns, drops)."""
import json, math, os, struct, subprocess, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'hamayuki')
AUD = os.path.join(ROOT, 'audio')
SR = 4000
def dur(p):
    return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',p]).strip())
def bars(p, n):
    raw = subprocess.check_output(['ffmpeg','-v','error','-i',p,'-ac','1','-ar',str(SR),'-f','s16le','-'])
    s = struct.unpack('<%dh' % (len(raw)//2), raw)
    L = len(s); out = []
    for i in range(n):
        a, b = i*L//n, (i+1)*L//n
        seg = s[a:b] or (0,)
        out.append(math.sqrt(sum(x*x for x in seg)/len(seg)))
    db = [20*math.log10(max(v, 1e-3)) for v in out]
    srt = sorted(db); lo = srt[len(srt)//10] - 1.5; hi = srt[-max(1, len(srt)//100)]
    # stretch between the quiet 5th percentile and the loudest bucket, then
    # bend the curve so drops and breakdowns read clearly on a small canvas
    return [max(4, min(99, round(6 + 93 * min(1.0, max(0.0, (x-lo)/(hi-lo or 1))) ** 2.2))) for x in db]
res = {}
for f in sorted(os.listdir(AUD)):
    if not f.endswith('.mp3'): continue
    p = os.path.join(AUD, f); d = dur(p)
    n = 600 if d > 600 else 140
    res[f[:-4]] = {'d': round(d, 2), 'p': bars(p, n)}
    print(f, round(d,1), n, file=sys.stderr)
with open(os.path.join(ROOT, 'peaks.json'), 'w') as o:
    json.dump(res, o, separators=(',', ':'))
