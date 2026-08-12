# TODO-079. ドキュメントとコードの食い違いを直す

## きっかけ

TODO-077（画面に出ないものが残っている）と同じ種類の取り残しが、文書と
コメントに 5 か所あった。どれも書いた当時は正しく、あとからコードだけが
動いたもの。

| 場所 | 書いてあったこと | 実際 |
|---|---|---|
| `docs/Developer.md` | 163 / 35 / 198 件、25 / 20 / 45 秒 | 297 / 49 / 346 件、2 / 28 / 28 秒 |
| `CLAUDE.md:164` | `'bridge threshold'` / `'bridge width'` | `bridge_threshold` / `bridge_width`（**空白入りは読めない旧形式**。同じ `CLAUDE.md` の別の場所では正しく書けていた） |
| `CLAUDE.md:286` 付近 | SVG のメタ属性 5 つ | `_meta_attrs()` は 7 つ（`-merged` / `-transpose` が抜けていた） |
| `my.css:267` / `storgan.html:129` | 「`--book-h` / `--z` / `#dur-t` は storgan.js が入れる」 | `viewer.js`（分離したときの取り残し） |
| `webroot/CLAUDE.md:14` | 「トークンは `:root:root` で定義」 | 独自トークンは素の `:root`。`:root:root` は Pico の変数への割り当てだけ |

**文書とコメントだけ。コードの挙動は変えていない。**

## やったこと

### `docs/Developer.md` のテスト件数と所要時間

その場で 3 通りとも実測して入れ替えた。

| コマンド | 対象 | 件数 | 所要 |
|---|---|---|---|
| `uv run pytest` | 通常テスト | 297 | 約 2 秒 |
| `uv run pytest -m browser` | ブラウザテスト | 49 | 約 28 秒 |
| `uv run pytest -m ""` | 両方 | 346 | 約 28 秒 |

**所要時間は、裏で重い処理が走っていると当てにならない。** 最初の計測は
裏に負荷があるまま行ってしまい、ブラウザテストが 40 秒台、「両方」が
102 秒、さらに 15 分以上進まずに中断させた回もあった。負荷が引いてから
2 回まわし直したところ、次のとおり安定した。

```
pass 1: 1.6 秒 / 28.1 秒 / 28.5 秒
pass 2: 1.7 秒 / 27.7 秒 / 28.5 秒
```

**計測は、手元が空いていることを確かめてから行うこと**（`uptime` の
1 分平均を見る）。件数・所要時間とも、TODO を立てたときの調べ
（297 / 49 / 346 件、2.3 / 28 / 35 秒）とほぼ一致した。

通常テストが 25 秒 → 2 秒に縮んだのは、TODO-081 で実曲の MIDI を
`tests/data/` の合成 MIDI（音符 69 個）に替えたため。

### `CLAUDE.md` の `bridge_threshold` / `bridge_width`

「穴の扱い」の節だけが空白入りの旧形式のままだった。空白入りのキーは
`validate_config()` が弾く（TODO-013、TODO-064 で読めなくなった）ので、
そのまま真似すると動かない。

### `CLAUDE.md` の SVG メタ属性

`rollbook.py` の `_meta_attrs()` が埋めるのは 7 つ。列挙に `-merged` /
`-transpose` を足した。

### `my.css` / `storgan.html` の「storgan.js が入れる」

ビューアを `viewer.js` に分けたときの取り残し。`--book-h` / `--z` は
`viewer.js:46,103`、`#dur-t` は `viewer.js:242` が入れている。

**項目には挙げていなかった `storgan.html:88` も同じ間違いだった**ので
一緒に直した（`window.UNKNOWN` を読むのも `viewer.js:30`）。
`storgan.html` に残った他の `storgan.js` の言及（70 行目の送信、
376 行目の `<script>`）は正しいので触っていない。

### `webroot/CLAUDE.md` の `:root:root`

実態は 2 つに分かれている。

- 独自トークン（`--cut` / `--hole` / `--paper` など）は素の `:root`
- `:root:root` は Pico の変数（`--pico-*`）への割り当てだけ

セレクタを二重にする理由（Pico の `:root:not([data-theme=dark])` =
詳細度 (0,2,0) に素の `:root` = (0,1,0) では負ける）は Pico の変数を
上書きするときの話で、独自トークンには当てはまらない。そう書き直した。
`my.css` 側のコメント（74〜78 行目）は元から正しいので触っていない。

続く「Pico はボタン要素の中で `--pico-color` を上書きする」は別の話
なので、「同じ理由で」を「また、」に改めた。

## テスト

```
uv run pytest -q          → 297 passed
uv run pytest -m browser  → 49 passed
uv run pytest -m ""       → 346 passed
uv run ruff check src tests → All checks passed!
uv run mypy src           → Success: no issues found in 18 source files
```

コメントと文書だけなので、画面の見た目は変わらない。
