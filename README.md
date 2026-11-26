# HAMAYUKI — how the music and the page were made

HAMAYUKI (浜雪) is the DJ name of Yuki Hamada. This repository is the full making-of, from composing the tracks to publishing the page.

- Listen: https://pacifica.dance/djs/hamayuki/ · https://pacifica.dance/ja/djs/hamayuki/
- 日本語の説明: [下記](#日本語)

## Who did what

| Step | By |
|---|---|
| Composition (the sound itself) | AI music tool **MUREKA** (via the teai.io media API) |
| Direction of the 11 new tracks (what to make) | HAMAYUKI → prompts in [`prompts/tracks.json`](prompts/tracks.json) |
| Selection, order, tempo ramp and transition design for all 24 tracks | HAMAYUKI |
| Transitions (tempo/beat matching, crossfades) and mastering | Automatic (code in [`pipeline/`](pipeline/), written with the Claude Code agent) |
| Voice | A synthesized voice based on Yuki Hamada's own voice (KOE), used with his consent |

The 24 tracks: 11 made for HAMAYUKI (one with voice) and 13 existing tracks made for SOLUNA.

## How it was made (2026-11-25 to 26)

1. **Compose** — For a sunset-beach set that rises from 116 to 124 BPM, write a prompt per scene and generate ([`prompts/tracks.json`](prompts/tracks.json)).
2. **Voice** — Synthesize three lines such as "Snow falls on the warm beach." plus two voice tags ([`pipeline/voice_lines.py`](pipeline/voice_lines.py)). In "Snow Falls on the Beach (Voice)" the music is ducked only where the voice enters (sidechain).
3. **Mastering** — Decode the source once → 25 Hz high-pass → gentle 1.5:1 compression → -14 LUFS → 4× oversampled limiter (-1.5 dBFS) → MP3 320k. All 24 tracks land at -14.0 to -14.1 LUFS with true peak ≤ -1.1 dBFS ([`pipeline/hamayuki_master.py`](pipeline/hamayuki_master.py), results in [`data/master_report.json`](data/master_report.json)).
4. **Analysis** — Measure each track's key (CQT chroma + Krumhansl-Schmuckler) and energy ([`hamayuki_keys.py`](pipeline/hamayuki_keys.py)), its most eventful ~2-minute section ([`hamayuki_sections.py`](pipeline/hamayuki_sections.py)), and kick positions ([`data/hamayuki_beats.json`](data/hamayuki_beats.json)).
5. **Mix** — Follow HAMAYUKI's order, beat-match by measured kick tempo, swap the low end on a single beat, and check the key at each join. Mismatches become short 8-beat transitions, and one track (Afro Tech) is pitched up a semitone. The set dips mid-way with the voice track and an amapiano track, and Lantern Festival → Blue Hour layer for 64 beats. A filter marks each track change, with voice tags in four places. → **HAMAYUKI Sessions #01** (~46 min). The first draft #00 (7 tracks, ~21 min) is [`hamayuki_mix.py`](pipeline/hamayuki_mix.py).
6. **Page** — Generate a DJ-directory-style page ([`gen_hamayuki.py`](pipeline/gen_hamayuki.py), [`hamayuki_music.py`](pipeline/hamayuki_music.py)). Biography is sourced from public articles; anything not verifiable from sources was removed.
7. **Waveform player** — Precompute each track's and the mix's loudness envelope ([`build-hamayuki-peaks.py`](pipeline/build-hamayuki-peaks.py) → [`web/peaks.json`](web/peaks.json)) and draw it on the page ([`web/wave.js`](web/wave.js)). Click the waveform to seek, or a track name to jump to that track. The ~46-minute mix, split into three files, is treated as a single waveform.

At each stage we ran an independent review in the persona of a listener and of the person who decides bookings, and fixed the findings before publishing.

### Not yet verified

- A human-ear check of the few joins where automatic key detection disagreed
- How the voice tags sound, and the impression of the two-track layered section
- No past DJ bookings yet

## Contents

```
prompts/tracks.json   Prompts for the 11 new tracks and the synthesized voice lines
pipeline/             Mastering, analysis, mixing, page generation and waveform code (Python, ffmpeg, librosa, rubberband)
data/                 Analysis and mastering results (keys, sections, beats, loudness)
web/                  Waveform player (wave.js) and waveform data (peaks.json)
```

`pipeline/` is record-keeping code that assumes the working-folder layout used at production time (e.g. `~/workspace/pacifica-dance`). The audio files themselves are not in this repository (you can listen on the page).

## License

Code (`pipeline/`, `web/`): MIT. Prompts and data: CC BY 4.0. The audio is not included and is not licensed here.

## 日本語

[HAMAYUKI](https://pacifica.dance/ja/djs/hamayuki/)（浜雪）は濱田優貴のDJ名義です。このリポジトリでは、曲づくりから公開ページまでの制作過程を公開しています。

- 聴く: https://pacifica.dance/ja/djs/hamayuki/ ・ https://pacifica.dance/djs/hamayuki/

### 誰が何をしたか

| 工程 | 担当 |
|---|---|
| 作曲（音そのもの） | AI作曲ツール **MUREKA**（teai.io のメディアAPI経由） |
| 新曲11曲の方向づけ（どんな曲を作るか） | HAMAYUKI → 指示文は [`prompts/tracks.json`](prompts/tracks.json) |
| 24曲の選曲・曲順・テンポの上げ方・つなぎの組み立て | HAMAYUKI |
| つなぎの処理（テンポ合わせ・拍合わせ・クロスフェード）、マスタリング | 自動（[`pipeline/`](pipeline/) のコード、AIエージェントのClaude Codeが作成） |
| 声 | 濱田優貴本人の声をもとにした合成音声（KOE）。本人の同意のもとで使用 |

24曲の内訳: HAMAYUKIのために作った曲11曲（うち1曲は声入り）と、SOLUNAのために作った既存曲13曲。

### 制作の流れ（2026-11-25〜26）

1. **曲を作る** — 夕暮れの浜で116→124BPMへ上がっていくセットを想定し、場面ごとに指示文を書いて生成（[`prompts/tracks.json`](prompts/tracks.json)）。
2. **声を作る** — 「暖かい浜に、雪が降る。」など3行と、声のタグ2本を合成（[`pipeline/voice_lines.py`](pipeline/voice_lines.py)）。「Snow Falls on the Beach (Voice)」では、声が入る所だけ曲を下げている（サイドチェーン）。
3. **マスタリング** — 元音源を1回だけデコード → 25Hzハイパス → 1.5:1の軽い圧縮 → -14 LUFS → 4倍オーバーサンプリングのリミッター（-1.5 dBFS）→ MP3 320k。24曲すべて -14.0〜-14.1 LUFS、トゥルーピーク -1.1 dBFS 以下（[`pipeline/hamayuki_master.py`](pipeline/hamayuki_master.py)、結果は [`data/master_report.json`](data/master_report.json)）。
4. **解析** — 各曲のキー（CQTクロマ＋Krumhansl-Schmuckler）とエネルギー（[`hamayuki_keys.py`](pipeline/hamayuki_keys.py)）、展開の多い約2分の区間（[`hamayuki_sections.py`](pipeline/hamayuki_sections.py)）、キックの位置（[`data/hamayuki_beats.json`](data/hamayuki_beats.json)）を測る。
5. **ミックス** — HAMAYUKIの曲順どおりに、キックの実測テンポで拍を合わせ、低域は1拍で入れ替え、つなぎ目ごとにキーを確認。合わない所は8拍の短いつなぎにし、1曲（Afro Tech）は半音上げた。中盤で声入りの曲とアマピアノでいったん落とし、Lantern Festival → Blue Hour では64拍重ねて鳴らす。曲の変わり目にフィルター、声のタグを4か所。→ **HAMAYUKI Sessions #01**（約46分）。最初の試作 #00（7曲・約21分、[`hamayuki_mix.py`](pipeline/hamayuki_mix.py)）。
6. **ページ** — DJ名鑑形式のページを生成（[`gen_hamayuki.py`](pipeline/gen_hamayuki.py)、[`hamayuki_music.py`](pipeline/hamayuki_music.py)）。経歴は公開記事を出典にし、出典で確かめられない記述は削った。
7. **波形プレーヤー** — 各曲・ミックスの音量の起伏を事前に計算し（[`build-hamayuki-peaks.py`](pipeline/build-hamayuki-peaks.py) → [`web/peaks.json`](web/peaks.json)）、ページ上に波形として表示（[`web/wave.js`](web/wave.js)）。波形を押すとその位置へ、曲目を押すとその曲へ飛ぶ。3ファイルに分かれた約46分のミックスも1本の波形として扱う。

各段階で、聴き手・出演を決める担当者になりきった独立の評価を行い、指摘を直してから公開した。

### まだ確かめていないこと

- 自動判定が割れたつなぎ目（数か所）を人の耳で聴いた確認
- 声のタグの聞こえ方と、2曲を重ねる区間の印象
- DJとしての出演歴はまだない

### 中身

```
prompts/tracks.json   新曲11曲の指示文と、合成した声の台詞
pipeline/             マスタリング・解析・ミックス・ページ生成・波形データのコード（Python, ffmpeg, librosa, rubberband）
data/                 解析とマスタリングの結果（キー、区間、拍、ラウドネス）
web/                  波形プレーヤー（wave.js）と波形データ（peaks.json）
```

`pipeline/` は制作時の作業フォルダ構成（`~/workspace/pacifica-dance` など）を前提にした記録用のコードです。音源ファイル自体はこのリポジトリに含めていません（ページで聴けます）。
