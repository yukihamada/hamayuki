"""Idempotently inject SEO structured data (Person + MusicPlaylist + MusicRecording)
and a first-party pageview beacon into /hamayuki/index.html.

- JSON-LD goes right before </head>, guarded by a marker comment so re-runs replace it.
- Beacon goes right before </body>, guarded the same way. It posts to the site's own
  /api/pv endpoint (no third-party, no cookies) so plays/visits can be measured.
Durations come from master_report.json; titles/BPM from hamayuki_music.
"""
import json, os, pathlib, sys
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import hamayuki_music as HM

SITE = pathlib.Path(os.path.expanduser('~/workspace/pacifica-dance'))
PAGE = SITE / 'hamayuki/index.html'
BASE = 'https://pacifica.dance'
AUDIO = BASE + '/hamayuki/audio/'

MARK_LD = '<!-- hamayuki:jsonld -->'
MARK_BC = '<!-- hamayuki:pv-beacon -->'


def iso(sec):
    sec = int(round(sec))
    m, s = divmod(sec, 60)
    return f'PT{m}M{s}S'


def build_ld():
    rep = json.load(open(HERE / 'master_report.json'))['mixes']['sessions-01']
    order = rep['order']; ch = rep['chapters']; dur = rep['duration']
    title = {f: t for f, t, b, k in HM.TRACKS}
    bpm = {f: b for f, t, b, k in HM.TRACKS}
    durs = [(ch[i + 1] if i + 1 < len(ch) else dur) - ch[i] for i in range(len(ch))]
    person = {
        '@type': 'Person',
        '@id': BASE + '/hamayuki/#person',
        'name': 'HAMAYUKI',
        'alternateName': ['浜雪', 'Yuki Hamada', '濱田優貴'],
        'jobTitle': 'DJ',
        'url': BASE + '/hamayuki/',
        'image': BASE + '/hamayuki/og.png',
        'description': 'DJ HAMAYUKI（浜雪）。夕暮れの太平洋で回す、ゆっくり温まっていくハウス。',
        'sameAs': [BASE + '/hamayuki/'],
        'knowsAbout': ['Deep house', 'Afro house', 'Melodic house'],
    }
    tracks = []
    for f, d in zip(order, durs):
        tracks.append({
            '@type': 'MusicRecording',
            'name': title.get(f, f),
            'duration': iso(d),
            'byArtist': {'@id': BASE + '/hamayuki/#person'},
            'audio': AUDIO + f + '.mp3',
            'additionalProperty': {'@type': 'PropertyValue', 'name': 'BPM', 'value': bpm.get(f)},
        })
    playlist = {
        '@type': 'MusicPlaylist',
        '@id': BASE + '/hamayuki/#sessions-01',
        'name': 'HAMAYUKI Sessions #01',
        'numTracks': len(tracks),
        'track': tracks,
        'url': BASE + '/hamayuki/',
        'image': BASE + '/hamayuki/og.png',
    }
    graph = {'@context': 'https://schema.org', '@graph': [person, playlist]}
    return json.dumps(graph, ensure_ascii=False).replace('<', '\\u003c')


BEACON = """<script>(function(){try{
var p=location.pathname;var r=document.referrer||"";
var b=JSON.stringify({path:p,ref:r,event:"pv"});
if(navigator.sendBeacon){navigator.sendBeacon("/api/pv",new Blob([b],{type:"application/json"}));}
else{fetch("/api/pv",{method:"POST",headers:{"content-type":"application/json"},body:b,keepalive:true});}
}catch(e){}})();</script>"""


def main():
    s = PAGE.read_text()
    ld = build_ld()
    ld_block = f'{MARK_LD}\n<script type="application/ld+json">{ld}</script>\n'
    bc_block = f'{MARK_BC}\n{BEACON}\n'

    # replace existing marked blocks, else insert
    import re
    if MARK_LD in s:
        s = re.sub(re.escape(MARK_LD) + r'.*?</script>\n', ld_block, s, count=1, flags=re.S)
    else:
        s = s.replace('</head>', ld_block + '</head>', 1)

    if MARK_BC in s:
        s = re.sub(re.escape(MARK_BC) + r'.*?</script>\n', bc_block, s, count=1, flags=re.S)
    else:
        s = s.replace('</body>', bc_block + '</body>', 1)

    PAGE.write_text(s)
    print('injected JSON-LD + beacon into', PAGE)


if __name__ == '__main__':
    main()
