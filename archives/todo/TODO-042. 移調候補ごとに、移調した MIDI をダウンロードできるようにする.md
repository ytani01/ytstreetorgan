# TODO-042. 移調候補ごとに、移調した MIDI をダウンロードできるようにする

移調の候補の表（TODO-039〜041）の各行に、**その調に移調した MIDI を
持ち帰るボタン**を足した。それまで候補の表で作り直せるのはロールブックの
SVG だけだった。

用途は「他の曲と合わせて演奏する」「別の道具に読み込ませる」。

## 決めたこと

### 元の MIDI をそのまま移調する。ロールブックの音符は使わない

`RollBook` が使う音符（`_convert_for_model()` の結果）は、統合
（TODO-038）・移調（TODO-039）・機種の音階での絞り込みを経た
「編曲された」列で、**音が消えている**。持ち帰る MIDI の元には向かない。

アップロードされた元のファイルを移調するだけにし、テンポ・チャンネル・
トラック構成・音階に無い音も全部そのまま残す。

### `ytmidilib.transpose_file()` に任せる。`mido` は直接叩かない

当初は「`mido` で元のバイト列をいじる」方針だったが、**MIDI を受け取って
MIDI を返す処理は `ytmidilib` の仕事**なので向こうに寄せた（TODO-048）。
`0.1.1` の `transpose_file()` がそれをする。

`NoteInfo` は経由しない。絶対秒に直したあとの形はテンポ変化・トラック
分割・tick 単位を持っていないので、組み立て直すと複数テンポの曲でズレる。

`mido` は**開発用の依存にだけ足した**（`[dependency-groups] dev`）。
`src/` は import しないが、テストが移調後のバイト列を読み直して確かめる。

### はみ出す音は丸める（`clip=True`）

既定の `clip=False` は 0 .. 127 を外れる音が 1 つでもあると `ValueError`。
**移調の候補は元の音域から作っているので実際に外れることはまず無い**が、
そのために持ち帰れなくなるほうが困るので丸めるほうを選んだ
（`transpose_midi_bytes()` の docstring に理由を書いてある）。

### 保存しない。リクエストごとにメモリ上で作る

`webroot/midi/` には置かない。候補は最大 7 行並ぶが、実際に
ダウンロードされるのは 1 つか 2 つ。残りまで書き出して置き場を太らせる
理由が無い（TODO-019 で「増え続けるのは対応しない」と決めたのは利用者が
上げた MIDI の話）。

### エンドポイントは `Download` と別にする

`/download/midi-transpose/<name>?t=<半音数>`（`DownloadTransposedMidi`）。
既存の `/download/midi/<name>`（`Download`）は**実在するファイルをその
まま返す**作りで、こちらは「名前 ＋ 移調量」からその場で作る別物。

- `<name>` は既存どおり `resolve_in()` で `webroot/midi/` の中にあることを
  確かめる（不正なら 400）
- `t` が整数でない・無い場合も 400。読めない MIDI も 400
- ルートは `/download/(.*)`（SVG）**より前**に置く。`midi/(.*)` とは
  文字列が食い違うので競合しない

### ダウンロード名は `<元の名前の stem>.t<符号付き半音数>.mid`

`holy.mid` を +3 なら `holy.t+3.mid`。同じ曲を複数の調で保存しても
区別できるように。**当初の書き方（`<元の名前>.t…`）だと
`holy.mid.t+3.mid` になる**ので stem にした。

### 表に出す行は全行（`±0` も）

「元のキーのまま MIDI だけ欲しい」場合があるので、`transpose == 0` の行にも
ボタンを出す。名前は `t+0` になる。

なお表そのものは、±0 より良い候補が無ければ出ない（TODO-041）。

## ついでに直したもの

アイコンの実体（`#i-save` / `#i-trash`）を `history.html` から
`base.html` へ移した。候補の表からも `#i-save` を使うため。
2 ページに同じ `<symbol>` を並べるのを避けた。

## 触ったもの

| ファイル | 内容 |
|---|---|
| `src/ytstreetorgan/transpose.py` | `transpose_midi_bytes()` / `transposed_midi_name()` |
| `src/ytstreetorgan/handler1.py` | `DownloadTransposedMidi` |
| `src/ytstreetorgan/webapp.py` | ルート追加 |
| `webroot/templates/storgan.html` | 候補の表に「MIDI」列 |
| `webroot/templates/base.html` / `history.html` | アイコンの実体を base へ |
| `pyproject.toml` | dev に `mido` |
| `tests/test_midi_transpose.py` | 新規 |
| `tests/browser/test_rollbook_page.py` | 全行にリンクがあること |
