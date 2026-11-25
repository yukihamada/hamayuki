"""Build HAMAYUKI mixes: tracks in set order, each stretched onto a smooth 116->124 BPM ramp
(rubberband, tempo only), loudness-matched, joined with 12 s equal-power crossfades.
  python3 hamayuki_mix.py 01   -> Sessions #01 (all TRACKS, ~1 h), split in 3 parts (Pages 25 MiB/file limit)
#00 (7 tracks, built earlier) is left untouched."""
import subprocess, os, json, sys
sys.path.insert(0, os.path.dirname(__file__))
from hamayuki_music import TRACKS

A = os.path.expanduser('~/workspace/pacifica-dance/hamayuki/audio')
TMP = os.environ.get('HY_WORK', 'work/hymix01')
os.makedirs(TMP, exist_ok=True)
XF = 12
META = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hamayuki_mix.json')

def dur(f):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f]).decode())

def build(tracks, name, title, parts):
    n = len(tracks); wavs = []; starts = []; t = 0.0
    for i, (f, ti, bpm, k) in enumerate(tracks):
        target = round(116 + 8 * i / (n - 1), 2)
        out = f'{TMP}/{i:02d}.wav'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f'{A}/{f}.mp3', '-af',
                        f'rubberband=tempo={target / bpm:.5f}:pitchq=quality,loudnorm=I=-14:TP=-1.5:LRA=9,aresample=44100',
                        '-ac', '2', out], check=True)
        d = dur(out); starts.append(round(t, 1)); t += d - XF; wavs.append(out)
        print(f, bpm, '->', target)
    inputs = sum((['-i', p] for p in wavs), [])
    fc = ''; prev = '[0:a]'
    for i in range(1, len(wavs)):
        fc += f'{prev}[{i}:a]acrossfade=d={XF}:c1=qsin:c2=qsin[x{i}];'; prev = f'[x{i}]'
    fc += f'{prev}afade=t=in:d=3,loudnorm=I=-14:TP=-1.5:LRA=9[out]'
    full = f'{TMP}/{name}.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', fc, '-map', '[out]', full], check=True)
    D = dur(full); files = []
    for p in range(parts):
        a, b = D * p / parts, D * (p + 1) / parts
        fn = f'{name}-{p + 1}.mp3' if parts > 1 else f'{name}.mp3'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{a:.3f}', '-t', f'{b - a:.3f}', '-i', full,
                        '-metadata', f'title={title}' + (f' (Part {p + 1})' if parts > 1 else ''), '-metadata', 'artist=HAMAYUKI',
                        '-b:a', '128k', f'{A}/{fn}'], check=True)
        files.append(fn)
        print(fn, round(os.path.getsize(f'{A}/{fn}') / 1048576, 1), 'MiB')
    meta = json.load(open(META)) if os.path.exists(META) else {}
    meta[name] = {'minutes': round(D / 60), 'files': files, 'starts': starts, 'order': [x[0] for x in tracks]}
    json.dump(meta, open(META, 'w'), indent=1)
    print(name, round(D / 60, 1), 'min')

if __name__ == '__main__':
    if sys.argv[1:] == ['01']:
        build(TRACKS, 'sessions-01', 'HAMAYUKI Sessions #01', 3)
