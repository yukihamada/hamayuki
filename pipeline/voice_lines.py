"""Synthesize HAMAYUKI's spoken lines in the user's own voice (teai voice API, voice=yukihamada, lang=ja, speed=1).
Saves original MP3s untouched; records request ids before generating so a retry can look them up."""
import json, os, time, uuid, urllib.request, pathlib

API = 'https://api.teai.io'
KEY = os.environ['TEAI_API_KEY']
OUT = pathlib.Path(__file__).parent / 'voice'
OUT.mkdir(exist_ok=True)
LEDGER = OUT / 'ledger.json'
LINES = [
    ('v1', '暖かい浜に、雪が降る。'),
    ('v2', '日が沈むまで、あと少しだけ、ここにいよう。'),
    ('v3', 'この夜を、次の人へ。'),
    ('tag1', 'ハマユキ。'),
    ('tag2', 'ハマユキ・セッションズ。'),
]
H = {'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json'}

def post(path, body):
    r = urllib.request.Request(API + path, data=json.dumps(body).encode(), headers=H)
    return json.load(urllib.request.urlopen(r, timeout=30))

def get(path):
    return urllib.request.urlopen(urllib.request.Request(API + path, headers={'Authorization': 'Bearer ' + KEY}), timeout=30)

ledger = json.loads(LEDGER.read_text()) if LEDGER.exists() else {}
for k, text in LINES:
    f = OUT / f'{k}.mp3'
    if f.exists() and f.stat().st_size > 1000:
        print(k, 'exists'); continue
    rid = ledger.get(k, {}).get('request_id')
    if not rid:
        q = post('/api/v1/voice/quote', {'voice': 'yukihamada'})
        cr = int(q.get('credits', 0))
        if cr > 20: raise SystemExit(f'quote too high: {cr}')
        rid = str(uuid.uuid4())
        ledger[k] = {'request_id': rid, 'text': text, 'credits': cr}
        LEDGER.write_text(json.dumps(ledger, ensure_ascii=False, indent=1))
        g = post('/api/v1/voice/generate', {'voice': 'yukihamada', 'text': text, 'request_id': rid,
                                            'confirmed_credits': cr, 'speed': 1.0, 'lang': 'ja'})
    else:
        g = json.load(get('/api/v1/voice/purchases/' + rid))
    for _ in range(90):
        if g.get('state') == 'complete': break
        if g.get('state') in ('failed', 'refunded'): raise SystemExit(f'{k} {g}')
        time.sleep(2); g = json.load(get('/api/v1/voice/purchases/' + rid))
    data = get('/api/v1/voice/purchases/' + rid + '/audio').read()
    f.write_bytes(data); print(k, len(data), 'bytes', ledger[k]['credits'], 'cr')
