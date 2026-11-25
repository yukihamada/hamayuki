"""Generate /djs/hamayuki/ and /ja/djs/hamayuki/ in the same format as the directory pages.
Not added to data-*.json (the list and counts stay at 989)."""
import json, re, shutil, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import build_detail as BD
import hamayuki_music as HM

SITE = BD.SITE
REL_IDS = [('Q1375814', 'ディープ・ハウス', 'Deep house'), ('Q16215736', 'ハウス', 'House'), ('Q20311234', 'ディープ・ハウス', 'Deep house'),
           ('Q52160540', 'ハウス', 'House'), ('Q111292358', 'ディープ・ハウス', 'Deep house'), ('Q131317897', 'ハウス', 'House')]
SRC = [
    {'t': 'BRIDGE（2015年1月）', 'u': 'https://thebridge.jp/2015/01/interview-w-yuki-hamada-mercari'},
    {'t': 'Business Insider Japan', 'u': 'https://www.businessinsider.jp/post-109030'},
    {'t': 'ニュースイッチ', 'u': 'https://newswitch.jp/p/16616'},
    {'t': 'enabler', 'u': 'https://enabler.fun/'},
    {'t': 'Hawaiʻi Public Radio（イベント情報）', 'u': 'https://www.hawaiipublicradio.org/community-calendar/event/zamna-hawaii-2026-06-11-2026-14-24-01'},
    {'t': 'PACIFICA 組織ページ（本人）', 'u': 'https://pacifica.dance/ja/organization/'},
    {'t': 'HAMAYUKI公式ページ（本人）', 'u': 'https://pacifica.dance/hamayuki/'},
]
SRC_EN = [dict(s, u=s['u'].replace('/ja/organization/', '/organization/'), t=s['t'].replace('（2015年1月）', ' (Jan 2015)').replace('ニュースイッチ', 'Newswitch').replace('HAMAYUKI公式ページ（本人）', 'HAMAYUKI official page (self-published)').replace('（イベント情報）', ' (event listing)').replace('PACIFICA 組織ページ（本人）', 'PACIFICA organization page (self-published)')) for s in SRC]

JA = dict(
    id='HAMAYUKI', sl='hamayuki', n='HAMAYUKI', ja='浜雪', k='person', dead=False, ds=True,
    cj=['日本'], gj=['ディープ・ハウス', 'アフロ・ハウス', 'メロディック・ハウス'],
    dj='本名は濱田優貴。1983年生まれ。東京理科大学在学中にサイブリッジを共同創業し、副社長を務めた。メルカリでは2015年1月に同社初の執行役員となり、のちに取締役CPO（最高プロダクト責任者）と研究開発組織「mercari R4D」の代表を務めた。現在は別荘事業「enabler」の代表。2026年11月13日にオアフ島カポレイで開かれた音楽フェス「Zamna Hawaii 2026」では、Soluna Productionとしてブッキングと現地運営を指揮した。DJ名義のHAMAYUKIは、名字「濱田」の「濱（浜）」と、名前「優貴（ゆき）」の音をつなげたもので、「浜に降る雪」とも読める。2026年11月に名乗りはじめた。',
    wj='作曲はAI（MUREKA）。HAMAYUKIの担当は、新曲11曲の方向づけと、24曲すべての選曲・曲順・テンポの上げ方・つなぎの組み立て。オリジナル曲24曲（うち11曲はHAMAYUKIのために作った曲で、1曲は本人の声をもとにした合成音声入り）と、自動の解析で展開の多い約2分を選んで夕暮れの順につないだ約47分のミックス「HAMAYUKI Sessions #01」を、このページで公開している。DJとしての出演歴は、まだない。夕暮れの時間帯に向けて、ディープ・ハウス、アフロ・ハウス、メロディック・ハウスを116BPMあたりから124BPMへ、途中で一度落としてから上げ直すセットを組んでいる。#01は各曲の聴きどころを集めた約47分の版。今後も、夕暮れのミックスを月1本を目標に公開する予定。',
    s=SRC,
)
EN = dict(JA, ja='', cj=None, ce=['Japan'], ge=['Deep house', 'Afro house', 'Melodic house'],
    de='Real name Yuki Hamada, born 1983. While studying at Tokyo University of Science he co-founded CYBRiDGE and served as its vice president. At Mercari he became the company’s first executive officer in January 2015, and later its director and CPO (chief product officer) and head of the research organization mercari R4D. He now heads the vacation-home company enabler. At Zamna Hawaii 2026, a music festival held in Kapolei, Oahu, on November 13, 2026, he led booking and local operations through Soluna Production. The DJ name HAMAYUKI joins “Hama” from his family name Hamada (hama means “beach”) with his given name Yuki, a sound that also means “snow” in Japanese, so it can be read as “snow on the beach”. He started using it in November 2026.',
    we='The music is composed by AI (MUREKA). HAMAYUKI directed the 11 new tracks and handled the selection, order, tempo ramp and transitions for all 24. On this page he has published the 24 original tracks (11 made for HAMAYUKI, one with a synthesized voice based on his own) and a 47-minute mix, “HAMAYUKI Sessions #01”, that joins the roughly two minutes of each that an automatic analysis rated most eventful, in sunset order. No past DJ bookings yet. His set is built for the sunset slot: deep, afro and melodic house that rises from about 116 to 124 BPM, with one dip mid-set. #01 is a 47-minute set of highlights; he plans to keep publishing a sunset mix, aiming for one a month.',
    s=SRC_EN)

PICKS = [('Can You Feel It', 'Mr. Fingers', '1986'), ('Superman (feat. Bucie)', 'Black Coffee', '2009'),
         ('Brightest Lights (feat. POLIÇA)', 'Lane 8', '2019'), ('Beyond Beliefs', 'Ben Böhmer', '2021')]
LISTEN = {
    'ja': (BD.TX['ja']['listen'], 'セットでかける曲の例。ほかのアーティストの曲で、HAMAYUKIの作品ではありません。', 'HAMAYUKIのページ（セットの組み立て・出演の相談）'),
    'en': (BD.TX['en']['listen'], 'Examples of tracks played in the set. These are by other artists, not HAMAYUKI originals.', 'HAMAYUKI page (set structure and bookings)'),
}
NOTE = {'ja': 'このページの人物は、PACIFICAの運営に関わる本人です。名鑑の一覧と掲載数（989組）には含めていません。',
        'en': 'This person is involved in running PACIFICA. The page is not part of the directory list or its count of 989.'}

BOOK = {
    'ja': '<section class="djcta" aria-labelledby="djcta-h"><div class="djc-txt"><h2 class="djc-h" id="djcta-h">HAMAYUKIの出演相談</h2><span>開演直後や夕日の時間帯のセットを、東京とホノルルを中心にお受けします。日程・会場・時間帯を添えて、HAMAYUKIのページの窓口からご連絡ください。</span></div><a class="djc-btn" href="/hamayuki/#h-book">HAMAYUKIに出演を相談する</a></section>',
    'en': '<section class="djcta" aria-labelledby="djcta-h"><div class="djc-txt"><h2 class="djc-h" id="djcta-h">Book HAMAYUKI</h2><span>Available for opening and sunset slots, mainly in Tokyo and Honolulu. Send the date, venue and time slot through the contact on the HAMAYUKI page.</span></div><a class="djc-btn" href="/hamayuki/#h-book">Ask about booking HAMAYUKI</a></section>',
}
DESC = {'ja': '浜雪（HAMAYUKI）の経歴と、夕暮れのセット。AI作曲ツールで作ったオリジナル曲24曲と、約47分のミックスをこのページで聴ける。',
        'en': 'HAMAYUKI: background and sunset set. 24 original tracks made with an AI music tool and a 47-minute mix, playable on this page.'}
LIC = {'ja': '文章は、上の出典（記事・公式サイト）をもとにPACIFICA編集部がまとめたものです。',
       'en': 'Written by the PACIFICA editors from the sources above (articles and official sites).'}

def main():
    data = {l: json.load(open(SITE/f'djs/data-{l}.json')) for l in ('ja', 'en')}
    by = {l: {d['id']: d for d in data[l]['djs']} for l in data}
    BD.JA_BY = by['ja']
    BD.PHOTO_DONE = set(BD.PHOTO_DONE) | {'HAMAYUKI'}
    BD.PHOTOS['HAMAYUKI'] = {'artist': 'self', 'license': '', 'page': 'https://pacifica.dance/hamayuki/'}
    for lang, d in (('ja', JA), ('en', EN)):
        d = dict(d)
        if lang == 'en': d['cj'] = ['日本']  # pick_country / jp_first read cj; ja='' keeps EN h1 Latin
        rel = [(by[lang][i], g if lang == 'ja' else BD.JA_BY[i].get('gj', [g])[0]) for i, g, ge in REL_IDS if i in by[lang]]
        if lang == 'en':
            rel = [(by['en'][i], 'ディープ・ハウス' if g == 'ディープ・ハウス' else 'ハウス') for i, g, ge in REL_IDS if i in by['en']]
        h = BD.page(lang, d, {}, [], None, None, '2026-11-25', [])  # no 'same genre' block: avoids borrowing other artists' standing
        # listen section: example tracks instead of an empty search
        title, lead, epk = LISTEN[lang]
        items = ''.join(f'<li><span class="wt">{BD.esc(t)}<small>{BD.esc(a)} · {y}</small></span>'
                        f'<a class="btn2" href="https://www.youtube.com/results?search_query={BD.urllib.parse.quote_plus(a + " " + t)}" target="_blank" rel="noopener noreferrer" aria-label="{BD.esc(t)} — YouTube">▶ YouTube</a>'
                        f'<a class="btn2" href="https://open.spotify.com/search/{BD.urllib.parse.quote(a + " " + t)}" target="_blank" rel="noopener noreferrer" aria-label="{BD.esc(t)} — Spotify">Spotify</a></li>' for t, a, y in PICKS)
        refh = '選曲の例（ほかのアーティストの曲）' if lang == 'ja' else 'Tracks in the set by other artists'
        new = f'<section><h2>{title}</h2>' + HM.snippet(lang) + '</section>'
        CRED = {'ja': '<p class="phcredit">画像：本人提供（AIで生成した本人の肖像）</p>', 'en': '<p class="phcredit">Image: provided by the artist (an AI-generated portrait of him)</p>'}
        h, k2 = re.subn(r'<p class="phcredit">.*?</p>', CRED[lang], h, count=1, flags=re.S); assert k2 == 1
        h, k3 = re.subn(r'(<img class="mono photo"[^>]*alt=")[^"]*"', lambda mm: mm.group(1) + ('浜雪（HAMAYUKI）のAI生成の肖像' if lang == 'ja' else 'AI-generated portrait of HAMAYUKI') + '"', h, count=1); assert k3 == 1
        h2, n = re.subn(r'<section><h2>[^<]*</h2><p class="na">.*?</section>', new, h, count=1, flags=re.S)
        assert n == 1, 'listen section not found'
        # conflict-of-interest note at the top; drop the generic 'listing is not endorsement' note
        h2 = h2.replace('<div class="meta">', '<div class="meta">', 1)
        h2 = re.sub(r'(<div class="meta">.*?</div>)', lambda mm: mm.group(1) + f'\n<p class="djtop">{BD.esc(NOTE[lang])}</p>', h2, count=1, flags=re.S)
        h2, k = re.subn(r'<p class="topnote">.*?</p>\n', '', h2, count=1, flags=re.S); assert k == 1
        # official link section before sources
        lk = ('公式リンク' if lang == 'ja' else 'Official links')
        lbl = ('HAMAYUKIのページ' if lang == 'ja' else 'HAMAYUKI page')
        # heading: this is background, not a DJ debut
        h2 = h2.replace(f'<h2>{BD.esc(BD.BP.T[lang]["debut"])}</h2>', '<h2>経歴</h2>' if lang == 'ja' else '<h2>Background</h2>', 1)
        # booking: HAMAYUKI only (not PACIFICA co-hosting); no PACIFICA fan signup on this page
        h2, kc = re.subn(r'<section class="djcta".*?</section>', lambda _m: BOOK[lang] + '\n<div data-fan-signup hidden></div>', h2, count=1, flags=re.S); assert kc == 1
        h2 = h2.replace('<div class="djcta-anchor"></div>', '<div data-fan-signup hidden></div>')
        if '<div data-fan-signup' not in h2: h2 = h2.replace('<p class="topnote">', '<div data-fan-signup hidden></div>\n<p class="topnote">', 1)
        h2 = re.sub(r'<nav class="pn"[^>]*><span></span></nav>', '', h2)
        # meta description
        h2 = re.sub(r'(<meta (?:name|property)="(?:og:)?description" content=")[^"]*"', lambda mm: mm.group(1) + BD.esc(DESC[lang]) + '"', h2)
        # JSON-LD
        def fixld(mm):
            ld = json.loads(mm.group(1))
            ld['sameAs'] = ['https://pacifica.dance/hamayuki/']
            ld['alternateName'] = ['浜雪', 'Yuki Hamada', '濱田優貴']
            ld['subjectOf'] = [{'@type': 'Article', 'url': x['u']} for x in SRC[:3]]
            return '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False).replace('<', '\\u003c') + '</script>'
        h2 = re.sub(r'<script type="application/ld\+json">(.*?)</script>', fixld, h2, count=1, flags=re.S)
        h2 = h2.replace(f'href="{"/ja/djs/" if lang == "ja" else "/djs/"}#dj-HAMAYUKI"', f'href="{"/ja/djs/" if lang == "ja" else "/djs/"}"')
        CORR = {'ja': '<p class="topnote">訂正・掲載取り下げのご依頼は、運営元 Soluna Production の窓口 <!--email_off--><a href="mailto:info@solun.art">info@solun.art</a><!--/email_off--> まで。</p>',
                'en': '<p class="topnote">For corrections or removal, email our operator Soluna Production at <!--email_off--><a href="mailto:info@solun.art">info@solun.art</a><!--/email_off-->.</p>'}
        h2 = h2.replace('<p class="note">', CORR[lang] + '\n<p class="note">', 1)
        h2 = re.sub(r'(<p class="note">[^<]*?: 2026-11-25 · ).*?</p>', lambda mm: mm.group(1) + LIC[lang] + '</p>', h2, count=1, flags=re.S)
        assert LIC[lang] in h2
        out = SITE/('ja/djs' if lang == 'ja' else 'djs')/'hamayuki'/'index.html'
        out.parent.mkdir(parents=True, exist_ok=True); out.write_text(h2)
        print('wrote', out)
    shutil.copy(SITE/'hamayuki/og.png', SITE/'djs/og/hamayuki.png')

if __name__ == '__main__':
    main()


def epk():
    """Rebuild the 'Mixes & tracks' section of /hamayuki/ from hamayuki_music (both languages)."""
    p = SITE/'hamayuki/index.html'; s = p.read_text()
    a = s.index('<section aria-labelledby="h-sessions">'); b = s.index('</section>', a) + len('</section>')
    old = s[a:b]
    picks = ''
    def tag(html_, l):
        html_ = re.sub(r'<div class="hy-mix', f'<div data-l="{l}" class="hy-mix', html_)
        for t in ('<h4 class="hy-h"', '<p class="hy-sub"', '<ul class="hy-tr"', '<details class="hy-more"'):
            html_ = html_.replace(t, t.replace(' class', f' data-l="{l}" class', 1), 1)
        return html_
    ja = tag(re.sub(r'<script>.*?</script>', '', HM.snippet('ja', h='h4'), flags=re.S), 'ja')
    en = tag(re.sub(r'<style>.*?</style>', '', HM.snippet('en', h='h4'), flags=re.S), 'en')
    n = len(HM.TRACKS); m = int(json.load(open(pathlib.Path(__file__).parent/'master_report.json'))['mixes']['sessions-01']['minutes'] + 0.5)
    new = f'''<section aria-labelledby="h-sessions">
      <h2 id="h-sessions"><span data-l="ja">ミックスと曲</span><span data-l="en">Mixes &amp; tracks</span></h2>
      <h3>HAMAYUKI Sessions</h3>
      <p data-l="ja">夕暮れのミックスを、月1本を目標に公開していきます。いまは各曲の聴きどころを集めた #01（約{m}分）と最初の試作 #00、オリジナル曲{n}曲を聴けます。</p>
      <p data-l="en">Aiming for one sunset mix a month. For now, #01 (about {m} min, a set of highlights), the first trial #00 and {n} original tracks are here.</p>
      {ja}
      {en}
{picks}</section>'''
    p.write_text(s[:a] + new + s[b:])
    print('epk ok')

if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == 'epk':
    epk()
