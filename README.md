# HAMAYUKI — how the music and the page were made

[HAMAYUKI](https://pacifica.dance/hamayuki/)（浜雪）は濱田優貴のDJ名義です。このリポジトリでは、曲づくりから公開ページまでの制作過程を公開しています。

- 聴く: https://pacifica.dance/ja/djs/hamayuki/ ・ https://pacifica.dance/hamayuki/
- English summary: [below](#english)

## 誰が何をしたか

| 工程 | 担当 |
|---|---|
| 作曲（音そのもの） | AI作曲ツール **MUREKA**（teai.io のメディアAPI経由） |
| 新曲11曲の方向づけ（どんな曲を作るか） | HAMAYUKI → 指示文は [`prompts/tracks.json`](prompts/tracks.json) |
| 24曲の選曲・曲順・テンポの上げ方・つなぎの組み立て | HAMAYUKI |
| つなぎの処理（テンポ合わせ・拍合わせ・クロスフェード）、マスタリング | 自動（[`pipeline/`](pipeline/) のコード、AIエージェントのClaude Codeが作成） |
| 声 | 濱田優貴本人の声をもとにした合成音声（KOE）。本人の同意のもとで使用 |

24曲の内訳: HAMAYUKIのために作った曲11曲（うち1曲は声入り）と、SOLUNAのために作った既存曲13曲。

## 制作の流れ（2026-11-25〜26）

1. **曲を作る** — 夕暮れの浜で116→124BPMへ上がっていくセットを想定し、場面ごとに指示文を書いて生成（[`prompts/tracks.json`](prompts/tracks.json)）。
2. **声を作る** — 「暖かい浜に、雪が降る。」など3行と、声のタグ2本を合成（[`pipeline/voice_lines.py`](pipeline/voice_lines.py)）。「Snow Falls on the Beach (Voice)」では、声が入る所だけ曲を下げている（サイドチェーン）。
3. **マスタリング** — 元音源を1回だけデコード → 25Hzハイパス → 1.5:1の軽い圧縮 → -14 LUFS → 4倍オーバーサンプリングのリミッター（-1.5 dBFS）→ MP3 320k。24曲すべて -14.0〜-14.1 LUFS、トゥルーピーク -1.1 dBFS 以下（[`pipeline/hamayuki_master.py`](pipeline/hamayuki_master.py)、結果は [`data/master_report.json`](data/master_report.json)）。
4. **解析** — 各曲のキー（CQTクロマ＋Krumhansl-Schmuckler）とエネルギー（[`hamayuki_keys.py`](pipeline/hamayuki_keys.py)）、展開の多い約2分の区間（[`hamayuki_sections.py`](pipeline/hamayuki_sections.py)）、キックの位置（[`data/hamayuki_beats.json`](data/hamayuki_beats.json)）を測る。
5. **ミックス** — HAMAYUKIの曲順どおりに、キックの実測テンポで拍を合わせ、低域は1拍で入れ替え、つなぎ目ごとにキーを確認。合わない所は8拍の短いつなぎにし、1曲（Afro Tech）は半音上げた。中盤で声入りの曲とアマピアノでいったん落とし、Lantern Festival → Blue Hour では64拍重ねて鳴らす。曲の変わり目にフィルター、声のタグを4か所。→ **HAMAYUKI Sessions #01**（約47分）。最初の試作 #00（7曲・約21分、[`hamayuki_mix.py`](pipeline/hamayuki_mix.py)）。
6. **ページ** — DJ名鑑形式のページを生成（[`gen_hamayuki.py`](pipeline/gen_hamayuki.py)、[`hamayuki_music.py`](pipeline/hamayuki_music.py)）。経歴は公開記事を出典にし、出典で確かめられない記述は削った。
7. **波形プレーヤー** — 各曲・ミックスの音量の起伏を事前に計算し（[`build-hamayuki-peaks.py`](pipeline/build-hamayuki-peaks.py) → [`web/peaks.json`](web/peaks.json)）、ページ上に波形として表示（[`web/wave.js`](web/wave.js)）。波形を押すとその位置へ、曲目を押すとその曲へ飛ぶ。3ファイルに分かれた約47分のミックスも1本の波形として扱う。

各段階で、聴き手・出演を決める担当者になりきった独立の評価を行い、指摘を直してから公開した。

### まだ確かめていないこと

- 自動判定が割れたつなぎ目（数か所）を人の耳で聴いた確認
- 声のタグの聞こえ方と、2曲を重ねる区間の印象
- DJとしての出演歴はまだない

## 中身

```
prompts/tracks.json   新曲11曲の指示文と、合成した声の台詞
pipeline/             マスタリング・解析・ミックス・ページ生成・波形データのコード（Python, ffmpeg, librosa, rubberband）
data/                 解析とマスタリングの結果（キー、区間、拍、ラウドネス）
web/                  波形プレーヤー（wave.js）と波形データ（peaks.json）
```

`pipeline/` は制作時の作業フォルダ構成（`~/workspace/pacifica-dance` など）を前提にした記録用のコードです。音源ファイル自体はこのリポジトリに含めていません（ページで聴けます）。

## English

HAMAYUKI is the DJ name of Yuki Hamada. This repo is the full making-of for the music and the page at https://pacifica.dance/djs/hamayuki/.

- **Composition**: AI (MUREKA). HAMAYUKI wrote the direction for the 11 new tracks (`prompts/tracks.json`) and chose the selection, order, tempo ramp and transitions for all 24.
- **Automatic**: tempo/beat matching, crossfades and mastering (`pipeline/`, written with the Claude Code agent). Every track is mastered to -14 LUFS with true peak ≤ -1.1 dBFS.
- **Voice**: a synthesized voice based on Yuki Hamada's own voice (KOE), used with his consent.
- **Mix**: HAMAYUKI Sessions #01 (~47 min): the most eventful ~2 minutes of each track, key-checked at each join, a mid-set dip, a 64-beat layered section and voice tags.
- **Waveform player**: `web/wave.js` draws precomputed loudness envelopes (`web/peaks.json`); click the waveform or a track name to jump there.

## License

Code (`pipeline/`, `web/`): MIT. Prompts and data: CC BY 4.0. The audio is not included and is not licensed here.
