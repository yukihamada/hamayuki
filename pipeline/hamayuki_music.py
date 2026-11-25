"""HAMAYUKI tracks + sunset mix: one shared player snippet for both the directory page and /hamayuki/."""
import html as _html, json

BASE = '/hamayuki/audio/'
# (file, title, bpm, kind) kind: new = made for HAMAYUKI, sol = SOLUNA original
# (file, title, measured BPM, kind)  kind: new = made for HAMAYUKI, voice = new + HAMAYUKI's synthesized voice, sol = made for SOLUNA
TRACKS = [
    ('first-ember', 'First Ember', 116, 'new'),
    ('sunset-drive', 'Sunset Drive', 116, 'sol'),
    ('horizon', 'Horizon', 118, 'sol'),
    ('rooftop-lagos', 'Rooftop Lagos', 118, 'sol'),
    ('desert-bloom', 'Desert Bloom', 118, 'sol'),
    ('snow-falls-voice', 'Snow Falls on the Beach (Voice)', 118, 'voice'),
    ('organic-afro-house', 'Organic Afro House', 118, 'vocal'),
    ('snow-on-the-beach', 'Snow on the Beach', 118, 'new'),
    ('sunset-terrace', 'Sunset Terrace', 119, 'sol'),
    ('log-drum-dawn', 'Log Drum Dawn', 111, 'sol'),
    ('trade-winds', 'Trade Winds', 120, 'sol'),
    ('shoreline-glow', 'Shoreline Glow', 120, 'new'),
    ('deep-house-afro-intro', 'Deep House (Afro Intro)', 122, 'vocal'),
    ('tidal-turn', 'Tidal Turn', 122, 'new'),
    ('kapolei-golden-hour', 'Kapolei Golden Hour', 123, 'new'),
    ('lantern-festival', 'Lantern Festival', 123, 'new'),
    ('blue-hour', 'Blue Hour', 123, 'new'),
    ('disco-ball-rise', 'Disco Ball Rise', 123, 'sol'),
    ('moonrise-run', 'Moonrise Run', 124, 'new'),
    ('uplift', 'Uplift', 124, 'sol'),
    ('tribal-circuit', 'Tribal Circuit', 124, 'sol'),
    ('afro-tech', 'Afro Tech', 124, 'vocal'),
    ('handover', 'Handover', 124, 'new'),
    ('last-wave', 'Last Wave', 126, 'new'),
]
MIX00 = ['sunset-drive', 'desert-bloom', 'snow-on-the-beach', 'sunset-terrace', 'kapolei-golden-hour', 'uplift', 'handover']
MIX = ('sunset-mix-00', 'HAMAYUKI Sunset Mix #00')
import os as _os, json as _json
_META = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'master_report.json')

T = {
    'ja': dict(
        tracks_h='オリジナル曲（{n}曲）',
        s01='HAMAYUKI Sessions #01',
        s01_sub='夕暮れの時間を想定して、AI作曲ツール（MUREKA）で作った下の{n}曲（1曲は濱田優貴の声をもとにした合成音声入り）から、自動の解析でそれぞれ展開の多い約2分を選んでつないだミックス（約{m}分）。116BPMから上げていき、中盤で声入りの曲とアマピアノでいったん落とし、終盤の124BPMへもう一度上げる流れ。つなぎ目ごとにキーを確かめ、合わない箇所は短くつなぎ（1曲は半音上げて調整）、曲が変わるたびにフィルターで場面を切り替え、後半に2曲を重ねて鳴らす区間と、HAMAYUKIの声のタグ（合成音声）を入れています。曲の並びはHAMAYUKIのセットの組み立てどおり。ファイルの大きさの都合で3つに分かれていて、続けて再生されます。',
        mix00_sub='最初の試作（AI作曲の7曲・約{m}分）。',
        tracks_sub='すべてAI作曲ツール（MUREKA）で作った曲。「NEW」はHAMAYUKIのために作った曲、「VOICE」はそれに濱田優貴の声をもとにした合成音声（KOE）を重ねた曲、「VOCAL」はSOLUNAのために作った曲のうち、AIが生成した歌声入りの曲、ほかはSOLUNAのために作った曲。',
        inmix='（ミックスでは124BPMに合わせて使用）', role='作曲はAI（MUREKA）。HAMAYUKIの担当は、新曲11曲の方向づけ（どんな曲を作るか）と、24曲すべての選曲・曲順・テンポの上げ方・つなぎの組み立て。つなぎの処理（テンポ合わせ・クロスフェード）は自動。', chap='曲目と時間（押すとその曲から再生）', new='NEW', voice='VOICE', vocal='VOCAL', sol='SOLUNA', play='再生', pause='一時停止', part='パート', more='残りの{k}曲を表示',
    ),
    'en': dict(
        tracks_h='Original tracks ({n})',
        s01='HAMAYUKI Sessions #01',
        s01_sub='Built for sunset: the roughly two minutes an automatic analysis rated most eventful in each of the {n} tracks below, all made with the AI music tool MUREKA (one with a synthesized voice based on Yuki Hamada’s own), joined into about {m} min. It rises from 116 BPM, drops back mid-set with the voice track and an amapiano surprise, then climbs again to 124 BPM. Keys are checked at every change; mismatched pairs get a short blend (one track is shifted up a semitone), every change has a filter sweep, and there is one stretch where two tracks play together plus a few HAMAYUKI voice tags (synthesized). The order follows the HAMAYUKI set structure. It is split into three files because of file size and plays straight through.',
        mix00_sub='The first trial (7 AI-made tracks, about {m} min).',
        tracks_sub='All made with the AI music tool MUREKA. “NEW” tracks were made for HAMAYUKI, “VOICE” adds a synthesized voice based on Yuki Hamada’s own voice (KOE), “VOCAL” tracks were made for SOLUNA and have AI-generated vocals, and the others were made for SOLUNA.',
        inmix=' (played at 124 BPM in the mix)', role='The music is composed by AI (MUREKA). HAMAYUKI directed the 11 new tracks (what to make) and handled the selection, order, tempo ramp and transitions for all 24. The transition processing itself (tempo matching, crossfades) is automatic.', chap='Tracklist with times (tap to jump)', new='NEW', voice='VOICE', vocal='VOCAL', sol='SOLUNA', play='Play', pause='Pause', part='Part', more='Show {k} more tracks',
    ),
}

CSS = """<style>
.hy-mix{border:1px solid var(--line,#2a2a2e);border-radius:12px;padding:16px;display:grid;gap:10px;margin:4px 0 14px}
.hy-mix b{font-size:16px}
.hy-mix p,.hy-sub{font-size:13.5px;line-height:1.75;color:var(--dim,#9a9a9f);margin:0}
.hy-mix audio{width:100%;height:44px;color-scheme:dark}
.hy-parts{display:flex;gap:8px;flex-wrap:wrap}
.hy-parts button{min-height:44px;padding:0 14px;border-radius:999px;border:1px solid var(--line,#2a2a2e);background:none;color:inherit;font:inherit;font-size:13px;cursor:pointer}
.hy-parts button[aria-current="true"]{border-color:var(--gold,#c9a962);color:var(--gold,#c9a962)}
.hy-h{font-size:13px!important;color:var(--dim,#9a9a9f)!important;font-weight:600!important;letter-spacing:.06em;margin:18px 0 8px!important;line-height:1.5}
.hy-tr{list-style:none;padding:0;margin:10px 0 0;display:grid;gap:8px}
.hy-tr li{display:flex;align-items:center;gap:12px;border:1px solid var(--line,#2a2a2e);border-radius:10px;padding:8px 12px 8px 8px}
.hy-tr button{flex:0 0 44px;width:44px;height:44px;border-radius:50%;border:1px solid var(--gold,#c9a962);background:none;color:var(--gold,#c9a962);font-size:15px;cursor:pointer}
.hy-tr button[aria-pressed="true"]{background:var(--gold,#c9a962);color:#0a0a0c}
.hy-tr .t{flex:1;min-width:0;display:flex;flex-direction:column}
.hy-tr .t small{color:var(--dim,#9a9a9f);font-size:12px;font-variant-numeric:tabular-nums}
.hy-tag{font-size:10.5px;letter-spacing:.08em;border:1px solid var(--line,#2a2a2e);border-radius:999px;padding:2px 8px;color:var(--dim,#9a9a9f);white-space:nowrap}
.hy-tag.new,.hy-tag.voice{border-color:var(--gold,#c9a962);color:var(--gold,#c9a962)}
.hy-chap summary{cursor:pointer;min-height:44px;display:flex;align-items:center;color:var(--gold,#c9a962);font-size:13.5px}
.hy-chap ol{list-style:none;padding:0;margin:4px 0 0;display:grid;gap:2px}
.hy-chap button{width:100%;min-height:44px;display:flex;gap:12px;align-items:center;background:none;border:0;border-bottom:1px dashed var(--line,#2a2a2e);color:inherit;font:inherit;font-size:13.5px;text-align:left;cursor:pointer;padding:6px 2px}
.hy-chap button[data-wait]::after{content:'…';margin-left:auto;color:var(--gold,#c9a962)}
.hy-chap .tm{font-variant-numeric:tabular-nums;color:var(--dim,#9a9a9f);min-width:3.2em}
.hy-more summary{cursor:pointer;min-height:44px;display:flex;align-items:center;color:var(--gold,#c9a962);font-size:13.5px;list-style:none}
.hy-more summary::-webkit-details-marker{display:none}
</style>"""

def snippet(lang, mix_minutes=None, h='h3', show=8):
    x = T[lang]; e = _html.escape
    M = _json.load(open(_META))['mixes']
    s01 = dict(M['sessions-01'], minutes=int(M['sessions-01']['minutes'] + 0.5)); TT = {a: b for a, b, c, d in TRACKS}
    ch = s01.get('chapters') or []; od = s01.get('order') or []; dur = s01.get('duration') or 0
    chap_li = ''.join(f'<li><button type="button" data-t="{t:.2f}"><span class="tm">{int(t // 60)}:{int(t % 60):02d}</span>{e(TT.get(f, f))}</button></li>' for t, f in zip(ch, od))
    chap = f'<details class="hy-chap"><summary>{e(x["chap"])}</summary><ol>{chap_li}</ol></details>' if chap_li else ''
    m00 = int(M['sunset-mix-00']['minutes'] + 0.5); f00 = M['sunset-mix-00']['files'][0]
    def li(f, t, b, k):
        return (f'<li><button type="button" data-src="{BASE}{f}.mp3" aria-pressed="false" aria-label="{e(x["play"])}: {e(t)}">▶</button>'
                f'<span class="t">{e(t)}<small>{b} BPM' + (e(x['inmix']) if b > 124 else '') + f'</small></span><span class="hy-tag {k}">{e(x[k])}</span></li>')
    first = ''.join(li(*tr) for tr in TRACKS[:show]); rest = ''.join(li(*tr) for tr in TRACKS[show:])
    parts = ''.join(f'<button type="button" data-part="{i}" aria-current="{"true" if i == 0 else "false"}">{e(x["part"])} {i + 1}</button>' for i in range(len(s01['files'])))
    files = _json.dumps([BASE + f for f in s01['files']])
    # waveform player: /hamayuki/wave.js (+ /hamayuki/peaks.json from
    # pacifica-dance/scripts/build-hamayuki-peaks.py). Native <audio> stays as no-JS fallback.
    js = '<script src="/hamayuki/wave.js?v=1" defer></script>'
    n = len(TRACKS)
    return (CSS + f'<p class="hy-sub" style="margin:0 0 12px">{e(x["role"])}</p>' +
            f'<div class="hy-mix hy-s01"><b>{e(x["s01"])}</b><p>{e(x["s01_sub"].format(n=n, m=s01["minutes"]))}</p>'
            f'<audio controls preload="none" src="{BASE}{s01["files"][0]}"></audio><div class="hy-parts">{parts}</div>' + chap + '</div>'
            f'<div class="hy-mix"><b>{e(MIX[1])}</b><p>{e(x["mix00_sub"].format(m=m00))}</p>'
            f'<audio controls preload="none" src="{BASE}{f00}"></audio></div>'
            f'<{h} class="hy-h">{e(x["tracks_h"].format(n=n))}</{h}><p class="hy-sub">{e(x["tracks_sub"])}</p>'
            f'<ul class="hy-tr">{first}</ul>'
            f'<details class="hy-more"><summary>{e(x["more"].format(k=n - show))}</summary><ul class="hy-tr">{rest}</ul></details>' + js)
