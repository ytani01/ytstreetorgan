# TODO-063. ブラウザ上で、実機で鳴る音だけを試聴できるようにする

## きっかけ

移調の候補（TODO-039、TODO-041）は「音符 98.7%」のような数字でしか比べ
られず、実際にどう聞こえるかは MIDI を持ち帰って鳴らすしかなかった。
しかも持ち帰る MIDI（TODO-042）は**元のファイルを移調しただけ**なので、
音階に無い音もそのまま鳴る。**手回しオルガンで鳴らしたときの音とは違う。**

画面で候補を押したら、その機種で実際に鳴る音だけがその場で聞けるようにする。

## 作ったもの

`rollbook.py`

- `parse()` から `load()`（解析だけ。SVG を作らない）を切り出した。
  試聴は鳴らす音符しか要らないので、SVG を組み立てずに止められる
- `playable_note_info` — `scale >= 0` の音符。移調・統合
  （`merge_overlapping_notes()`。TODO-038）・音階での絞り込みを経たもので、
  実線で描く穴と 1 対 1 に対応する。`hole_note_count` はこれに寄せた

`audition.py`（新規）

- `playable_midi_bytes(src, model, semitones)` — 上の `load()` をそのまま
  通し、`playable_note_info` を書き出すだけ。**絞り込みの手順を組み立て
  直さない**（音階に入るかどうかは移調したあとに決まる。TODO-043 と同じ失敗）
- **channel は 0 に揃える。** ブラウザ側の再生に使う Magenta は channel 9 を
  ドラムとして扱うので、揃えないと穴が開く音がキックドラムの音で鳴る
- `ytmidilib.write()` がパスしか受けないので一時ファイルを経由するが、
  それはこの関数の中だけの都合（TODO-065 で `io.BytesIO` に差し替える）

`handler1.py` / `webapp.py`

- `AuditionMidi` — `/audition/midi/<name>?t=<半音数>&model=<機種名>`。
  `Content-Type: audio/midi`、`Content-Disposition` は付けない、**保存しない**
- **既存の `DownloadTransposedMidi` は変えていない。** あちらは持ち帰る
  素材、こちらは実機の再現で目的が違う。同じ名前で中身の違う MIDI が
  2 種類出回るのを避けるため、経路を分けた

`webroot/static/vendor/`（同梱。CDN は 1 本も読まない）

- Tone.js 14.7.58 / @magenta/music 1.23.1 の `es6/core.js` /
  html-midi-player 1.6.0 の 3 本。版・サイズ・取得元は
  `docs/tech-stack.md`、ライセンス全文と sha256 は同じ場所の `LICENSES.md`
- **読み込む順は Tone → core → midi-player**（UMD なので順序が要る）。
  結果画面でだけ読む

`storgan.html` / `midi_audition.js` / `my.css` / `base.html`

- 候補の表に「試聴」列、表の下に `<midi-player>` 1 つと注記
- JS は `data-audition` の値を `src` へ写すだけ。**URL は組み立てない**
- 押した行に `is-audition`（左の縦線）。いま出しているブックの行
  （`.is-current`）とは意味が別なので、色ではなく縦線にした

落とし穴は `webroot/CLAUDE.md`「MIDI の試聴」に書いた。とくに
**`sound-font=""`（空文字）と書くと外部から音源を取りに行く**
（属性なしなら取りに行かない）のは、書きかけて気付いたもの。

## やらないと決めたこと

- **ピアノロールの可視化（`visualizer` 属性）は出さない。** 鳴らない音も
  同じ見た目で描くので、ロールブックの実線（穴）と破線（音階に無い音）の
  描き分けと食い違って読み違いを招く。同梱バイト数は変わらないので、
  後から属性を足すだけで出せる
- **JS 側で音階を判定しない。** `note2scale()` を JS に複製することになる
- **試聴した音の MIDI は持ち帰らせない。** 欲しくなったら `AuditionMidi` に
  `Content-Disposition` を足すのが答えで、`DownloadTransposedMidi` の
  中身を変えるのは答えではない
- **同じ高さの連打が 1 つの長い音に聞こえるのは直さない。**
  `merge_overlapping_notes()` による実機の再現（1 音に 1 パイプ）

## テスト

- `tests/test_audition.py` — 音階に無い音が入っていない／移調が効く／
  音符の数が `hole_note_count` と一致／統合が効く／channel が全部 0／
  何も保存しない／未知の機種名は `ValueError`。HTTP は 200 と `MThd`、
  不正な `t` は 400、未知の機種は 400、`..` を含む名前は 400、無いファイルは 404
- `tests/browser/test_audition.py` — 試聴ボタンで `src` が `/audition/` の
  URL に入れ替わり、**POST が飛ばない**こと（`data-transpose` との取り違えを
  見張る）。「MIDI」列は `/download/midi-transpose/` のまま。再生ボタンが
  enabled になる。400 以上のレスポンスが 1 本も無い
- 手で確かめたもの — `curl` で取って `ytstreetorgan play` で聴き比べ
  （`holy.mid` は 34notes・移調なしで 74 音、`parse` の「鳴らせる音符 74/150」
  と一致）。画面では行を替えての聴き比べ、暗いテーマ、`--debug` の
  live reload、**ネットを切った状態で全部動くこと**
