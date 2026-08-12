# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 概要

MIDI ファイルを解析し、手回しオルガン用ロールブック（穴あけ用の紙の楽譜）を SVG で生成する。
CLI とブラウザ UI の 2 系統がある。

## コマンド

`uv` 管理。すべて `uv run` 経由で実行する。よく使うのはこれだけ。

```bash
uv run pytest -q                          # 通常テスト（browser マーカーは除外される）
uv run pytest -m browser -q               # ブラウザテスト（実 Chromium を起動）
uv run ruff check src tests               # lint（--fix で自動修正）
uv run mypy src                           # 型チェック

uv run ytstreetorgan webapp -p 10081      # Web サーバー → http://localhost:10081/storgan2/
uv run ytstreetorgan rollbook FILE.mid -m 34notes   # SVG 生成
uv run ytstreetorgan parse FILE.mid -v    # MIDI 解析結果を表示（-v で可視化）
uv run ytstreetorgan play FILE.mid        # MIDI 再生
```

**完了と報告する前に、`pytest` / `ruff` / `mypy` を通すこと。** 画面を変えたら
ブラウザで描画も確かめる（`docs/Developer.md` の「コミット前に通すもの」）。

- **実行方法の詳細は `docs/Developer.md`** — 環境の用意、絞り込み、
  カバレッジ、basedpyright、ruff の設定方針、コミット前に通すもの、
  タグを打つ手順、テストを書くときの注意
- **依存とその選定理由は `docs/tech-stack.md`** — `ytmidilib` が git 依存
  であること、hatch-vcs によるバージョン、フロントエンドの方針

## アーキテクチャ

### レイヤー分離（意図的な規約）

`__main__.py` は click のコマンド定義だけを持つ薄い層に保つ。ロジックは `apps.py` の
`RollBookApp` / `MidiApp` に置く（テスト可能にするため）。新しいサブコマンドを追加する場合も
この分離を守ること。共通オプション（`-h` / `-d` / `-V`）は `click_utils.py` の
`click_common_opts()` デコレータで付与する。

**モジュールの依存は一方向に保つ**（TODO-043）。

```
conf.py → transpose.py → rollbook.py → audition.py → base_handler.py
    → handler1.py / download.py / history.py / config_handler.py
```

| モジュール | 受け持ち |
|---|---|
| `transpose.py` | 移調。候補の作成・絞り込み・注記、`plan_transpose()`。並び順は `transpose_rank_key()`（TODO-052）。候補から画面用の値を作る `transpose_view()`（TODO-076） |
| `rollbook.py` | 穴の位置と SVG。`note2scale()` / `HoleInfo` / `RollBook` |
| `audition.py` | 試聴用の MIDI。`playable_midi_bytes()` |
| `base_handler.py` | 全ハンドラの土台（TODO-075） |

**`transpose.py` から `rollbook.py` を import しないこと**（循環する）。
移調は「どの高さで鳴らすか」だけの話で、穴の位置や SVG とは関係が無い。
`play`（`MidiApp`）もブックを作らずに移調するので、切り離してある。

`note2scale()`（穴の列を決める）と `merge_overlapping_notes()`（TODO-038。
実機は 1 音に 1 パイプ）は移調の都合ではないので `rollbook.py` に残す。

**移調の手順は `plan_transpose()` に 1 つだけ。** `RollBook.parse()` と
`MidiApp._convert_for_model()` が同じ手順をそれぞれ持っていて、
食い違いかけた（TODO-043）。増やさないこと。

同じ理由で、**機種設定の読み込みと検証は `conf.load_model_conf()` に
1 つだけ**、**移調量の正規化は `transpose.initial_transpose()` に 1 つだけ**
（TODO-073）。`RollBook.__init__` と `MidiApp.__init__` が、同じ日本語の
メッセージまで含めてそれぞれ持っていた。

### 設定ファイル（リポジトリ外にある）

モデル設定は `storgan-conf.json`。**リポジトリには含まれていない**。`Conf` が
`.` → `~/.config` → `~/etc` → `/usr/local/etc` → `/etc` の順に探索し、最初に見つかったものを使う。
実運用の設定は `~/etc/storgan-conf.json` に置いてある。`conf/storgan-conf.json` がテンプレート
（テストもこれを複製して使う）。
見つからないと `Conf.__init__` が `FileNotFoundError` を投げるので、設定に触るテストは
必ずパスを明示するかモックする。

`ModelConf` の**キーは生の JSON フィールド名**（`'book_height'`, `'pitch'` …）。
**すべて Python の識別子**なので、`class ...(TypedDict)` の形で定義してある。
**型は 2 つある**（TODO-078）。`ModelConf` は生の JSON の形（どのキーも
欠けうる）で、設定を読み書きする側（`Conf.data` と設定エディタ）が使う。
図を描く側は `ValidModelConf`（`total=True`）を受け取り、`conf['pitch']` の形で
読む。**`.get(key, 0.0)` で読まないこと**（0 が入ると黙って高さ 0 の図が出る）。
`validate_config()` を通してこの型にするのが `load_model_conf()`。
かつては `'book height'` のように空白入りで、関数形式でしか書けなかった。
**旧形式はもう読めない。**
`'1sec'` は数字始まりで識別子にできないため `'mm_per_sec'` に改名した
（`RollBook.mm_per_sec` に合わせた）。
`Conf.save()` は `.bak` を作ってから一時ファイル経由で原子的に置換する。

トラックの定義は `'notes'`（`list[str]`。要素は `'F4'` のような音名）。
リストの**並び順がそのままトラック番号**で、`note2scale()` はその index を返す。
音名は国際標準（scientific pitch notation。MIDI ノート番号 60 = `C4`、
範囲は `C-1`〜`G9`、変化記号はシャープのみ）で、`note_name_to_midi()` /
`midi_to_note_name()` が MIDI ノート番号との変換を受け持つ。穴の位置は
音名だけで決まる（`note_name_to_midi()` で MIDI ノート番号に変換するだけ）。
かつては `'note name'` と `'note offset'` の 2 本の並行配列、その後は
`{'name': str, 'offset': int}` の辞書のリストで、半音単位のオフセットを
起点の音（`'base_note'`）との差として持たせていたが、`'offset'` を
設定に持たせず導出する形に変え（TODO-013、TODO-064）、さらに `'base_note'`
自体と、そこから導出していた「半音単位のオフセット」という中間の概念も
無くした（TODO-067）。
**旧形式（`'note name'` / `'note offset'` の並行配列、`'offset'` を持つ
辞書のリスト）はもう読めない**（`validate_config()` が弾く。自動変換はしない）。
`'base_note'` は違う扱いで、設定に残っていても**黙って無視する**
（`validate_config()` はエラーにしない。値を使わなくなっただけなので、
古い設定ファイルがそのまま読める）。

### 画面に出す用語

「ノート」「音名」「音階」が混ざって分かりにくかったので、次のように使い分ける。
**新しい文言を足すときもこれに合わせること。**

| 画面の語 | 指すもの | 設定ファイル |
|---|---|---|
| トラック | 穴の列。並び順がそのまま番号 | `'notes'` の要素（位置） |
| 音名 | `F4` のような、そのまま鳴る高さを表すラベル | `'notes'` の要素（値） |
| 音階 | その機種が出せる音の集まり | （設定項目ではない） |
| 移調 | 曲全体を上下させる半音数 | （設定項目ではない） |
| 調 | 移調量のうち、キーを動かすぶん（-5〜+6）。**CLI の表示だけ** | （同上） |
| 音の長さ | 鳴らせる音符の**長さの合計**が占める割合 | （同上） |
| 試聴 | その機種で実際に鳴る音だけを、ブラウザで鳴らして確かめること | （設定項目ではない） |

- **「ノート」は必ず「MIDI ノート番号」と書く**（音名と紛れるため）。
  裸の「ノート」は使わない
- **半音単位のオフセットという概念は無い**（TODO-064 で画面から外し、
  TODO-067 で内部からも無くした）。設定エディタは音名のドロップダウン
  1 つで入力し、選択肢には参考として MIDI ノート番号を丸括弧で添える
  （`F4 (65)`）。穴の位置は音名（＝MIDI ノート番号）だけで決まる
- **「落とす」は単独で使わない。** このリポジトリでは削除（「引数を落とす」）・
  変換（「`str` に落とす」）・減色（「彩度を落とす」）の 3 通りに使っていて、
  目的語が無いとどれか分からない。コメントや文書でも「削除する」
  「色を薄くする」のように書く
- **「音の長さ」と「演奏時間」を混ぜない。** 「演奏時間」はブック全体の
  総時間（`#dur-t`）で、「音の長さ」は移調の候補で使う割合。
  同じ理由で「全長」（ブックの mm）とも分ける
- **「調」「オクターブ」は画面に出さない**（TODO-054）。移調の候補の表も
  用語説明も**移調（合計の半音数）だけ**にしてある。`transpose_notices()` の
  文面も移調量で書く。`key` / `octave` のデータは残っているが、使うのは
  候補の絞り込み・並べ替えと CLI の表示だけ
- **「調が ±0」は「変更なし」ではない**（CLI の表）。オクターブが動いていれば
  キーだけが同じ。「移調しない」と書けるのは**移調量が 0** のときだけ
- 利用者に見えるメッセージは日本語で書く（`conf.py` の `validate_config()` や
  `Conf` が返す文字列も `showAlert` でそのまま画面に出る）。
  `'notes'` の要素を指す番号は**1 始まり**で書く（画面の行番号に合わせるため）

### SVG 座標系

**すべての座標が負値**（`svg_square()` は `M {-x},{-y} h {-w} v {-h}`、viewBox の原点も負）。
ロールブックは右から左へ流れるため。単位は mm で、`'mm_per_sec'`（既定 50.0）が秒→mm の変換係数。
線は `vector-effect:non-scaling-stroke` + `-inkscape-stroke:hairline` を付ける
（カッティング用にヘアラインが要る）。

### 穴の扱い

- `note2scale()` はオルガンの音階に無い MIDI ノートに対して `-1` を返す。そうした音は
  **捨てずに黒の破線で描く**（`RollBook.svg()`）。演奏者が欠落を目視できるようにするため。
  scale が `-1` の穴はブックの全長（`_width`）を伸ばさない。
- 穴の長さが `'bridge threshold'` を超えると `divide_length_by_max_len()` が
  `'bridge width'` の隙間（ブリッジ）を挟んで複数に分割する。紙のブックが切れないようにする措置。
  分割数は `n = ceil((全長 + 隙間) / (隙間 + 上限))`。

### Web 層

Tornado。URL プレフィックスは `/storgan2`（`WebServer.URL_PREFIX`）。全ハンドラは
`base_handler.py` の `StorganBaseHandler` を継承し、設定を `app.settings` から取り出す。
`_url_path` の**末尾のスラッシュは必須**（`Handler1.get()` がこれと突き合わせてリダイレクトする）。

**ハンドラは画面ごとにモジュールを分ける**（TODO-075）。かつては
`handler1.py` に土台も持ち帰りも入っていて、`history.py` と
`config_handler.py` が「ロールブックを作る画面」のモジュールから
基底クラスを import していた。

| モジュール | 中身 |
|---|---|
| `base_handler.py` | `StorganBaseHandler` だけ |
| `handler1.py` | `Handler1` だけ |
| `download.py` | 持ち帰りと試聴の 4 つ |
| `history.py` / `config_handler.py` | 履歴 / 機種設定の画面 |

- `Handler1`（`handler1.py`） — MIDI アップロード → SVG 生成 → プレビュー。
  履歴からの `stored_midi`（再生成）/ `stored_svg`（再表示）もここが受ける
- `Download` — `webroot/svg/` と `webroot/midi/` からのダウンロード
- `DownloadTransposedMidi` — `/download/midi-transpose/<name>?t=<半音数>`。
  **アップロード済みの MIDI を、その場で移調して返す**（TODO-042）。
  ロールブックの音符ではなく元のファイルを移調するだけ。**保存しない**
- `AuditionMidi` — `/audition/midi/<name>?t=<半音数>&model=<機種名>`。
  **その機種で実際に鳴る音だけ**を返す（移調・統合・音階での絞り込みを
  経たもの）。`Content-Type: audio/midi`、`Content-Disposition` は付けない、
  **保存しない**（TODO-063）。`DownloadTransposedMidi`（持ち帰る素材）とは
  目的が違うので経路を分けてある
- `DownloadTransposedMidiZip` — `/download/midi-transpose-zip/<name>?t=-5,0,3`。
  候補ぶんをまとめて ZIP で返す（TODO-050）。**半音数はクエリで受け取り、
  候補を作り直さない**（1 件版と同じく、名前と半音数だけから作れる形に
  揃えてある）。こちらも保存しない
- `ConfigHandler` — `/storgan2/config` のモデル設定エディタ。`?api=1` で JSON を返す
- `HistoryHandler` — `/storgan2/history` の一覧。POST は削除の JSON API

**ファイル名を外（URL やフォーム）から受け取るときは必ず `storage.py` を通す。**
`safe_name()` が区切り文字と `..` を弾き、`resolve_in()` が解決後も置き場の
中にあることを確かめる。履歴は削除まであるので、ここを迂回すると事故になる。

持ち帰り系の 4 つは、この確認とクエリの `t` の読み取りを
`StorganBaseHandler.stored_file()` / `.transpose_arg()` で済ませる
（TODO-072。4 回写してあった）。**`Handler1._stored_path()` と混ぜないこと。**
あちらは画面に理由を出す版で、こちらは HTTP のエラー（400 / 404）を投げる版。

`webroot` / `workdir` は `WebServer` が `Path` に正規化し、`app.settings` にも
`Path` のまま渡す。各ハンドラは `self._webroot / 'svg' / fname` のように組み立てる。

`webroot/midi/` と `webroot/svg/` は実行時に書き込まれる作業ディレクトリ（`.gitignore` 済み）。

テンプレート内で URL を組み立てるときは、必ず `{{urlprefix}}` を使う（JS からは
`window.URL_PREFIX`）。直書きすると prefix を変えたときに 404 になる。
テストは既定値以外の prefix で走らせているので、直書きすると
`tests/browser/test_rollbook_page.py::test_static_assets_load` が落ちる。

静的ファイル（CSS / JS / favicon）は `{{ static_url('css/my.css') }}` を使う。
prefix が付くうえに `?v=<hash>` が付くので、更新したときに古いキャッシュを
掴まれない。

`autoreload=True` **だけでは `.py` しか反映されない**（テンプレートは
`compiled_template_cache`、`?v=<hash>` は `static_hash_cache` が握っている）。
かつて再起動せずに「直したのに変わらない」と悩んだ実績が二度あるので、
`WebServer` はこの 2 つも `False` にしてある。**再起動は不要**。
消すと元の落とし穴に戻る。

### live reload（`webapp --debug` のときだけ）

`--debug` を付けて起動すると、テンプレート / CSS / JS を直したときに
**ブラウザが勝手に再読み込みされる**。`livereload.py` に置いてある。

- `watch_webroot()` が `templates/` と `static/` を `tornado.autoreload` の
  監視対象に足す。これで `.py` 以外でも**プロセスが再起動する**
- `LiveReloadHandler` は繋がるだけの WebSocket。**何も送らない**
- `static/js/livereload.js` は繋いだまま待ち、**切れたら**＝再起動が始まった
  と見なして、繋ぎ直せるようになった時点で `location.reload()` する

「切断そのものが更新の合図」なので、サーバー側にファイル監視のロジックは無い。

注意点:

- `<script>` の 1 行は `base.html` に 1 か所あれば全ページに効く。
  `storgan.html` / `config_editor.html` / `history.html` はどれも
  `base.html` を継承している（`{% extends "base.html" %}`）ので、
  ページを増やしてもここは触らなくてよい
- `tornado.autoreload.watch()` は**起動時にあるファイルしか見ない**。
  テンプレートを新規に足したら一度手で再起動する
- 生成結果の画面でリロードすると、表示中のブックは消えて作り直しになる

### フロントエンド / 確認の出し方

`webroot/CLAUDE.md` にある（Pico.css の同梱と `:root:root` の話、
`confirm()` と `<dialog>` の使い分け）。`webroot/` 配下を触ると読み込まれる。

### ロールブックのビューア

`webroot/static/js/viewer.js`。**transform で拡縮していない。SVG の描画サイズ
（`.svgbox > svg` の `height: calc(var(--book-h) * var(--z))`）そのものを変える。**
こうするとブラウザ標準のスクロールがそのまま効き、スクロールバーが全体の中の
現在位置を示す。SVG が mm 単位で出力されているので倍率 1.0 が原寸になる。
汎用の panzoom ライブラリは transform ベースで、縦横比 33:1 のロールブックでは
スクロールバーが消えて現在位置を見失うので使わない。

- **初期表示は右端**（`viewBox` が負で、曲の先頭が x=0 側 = 右端にあるため）。
  既定の倍率は「高さ合わせ」。「全体」だと 7% になって何も読めない。
  **先頭へ戻すのは初期表示のときだけ**（TODO-049）。「高さ合わせ」
  「全体」のボタンは倍率を変えるだけで、位置は他の拡縮と同じく保つ
- **拡縮の位置合わせは「ブック上の位置（mm）」で覚える**（`setZoom()`）。
  基準の点が SVG の右端・上端から何 mm かを実測し、倍率を変えたあとの
  `requestAnimationFrame` で引き戻す。**`scrollWidth` に対する比では駄目。**
  `padding` は拡縮しないので比が倍率に対して一定にならず、はみ出して
  いないときは `scrollWidth` が `clientWidth` で頭打ちになって中央へ飛ぶ
- ブックの諸元は `RollBook` のプロパティから取り、`Handler1._render()` が
  `book`（`storage.BookInfo`）として渡して、テンプレートが
  `window.BOOK_DATA` に出している。
  `width` / `height` は SVG の属性にも出ているが、**穴の数と
  `mm_per_sec` は SVG からは取り出せない**ので、まとめてここで渡す

`RollBook.svg()` は、**図からは求まらない値を `<svg>` の属性に埋める**
（`data-storgan-model` / `-mm-per-sec` / `-notes` / `-hole-notes` /
`-off-scale-notes`）。履歴から保存済みの SVG を出し直すとき、
`storage.book_from_svg()` がこれを読む。寸法と穴の数は図から読めるので
埋めない（二重に持つと手で編集したときに食い違う）。
**属性が無い古い SVG もある**ので、無ければ `---` に落とす。

生成日時は SVG の中ではなく**ファイルの更新日時**から取る
（`storage.mtime_text()`）。SVG は生成したときに書かれるので一致する。

`book` は 2 か所で組み立てる。`Handler1._book_of()`（生成したとき）と
`storage.book_from_svg()`（履歴から出し直すとき）。**項目を増やすときは
両方を直すこと。** 型は `storage.BookInfo`（TODO-074）で、`total=True` の
まま値を `X | None` にしてある（キーは必ず全部あり、読めなかった値だけが
`None`）。片側の付け忘れは mypy が拾う。往復テストもそのまま残してある。

穴の数は 2 段階 × 2 種類で数える。

| プロパティ | 意味 |
|---|---|
| `note_count` | MIDI から読んだ音符の数（実線と破線の合計） |
| `hole_note_count` / `hole_count` | 実線（音階にある音）の音符 → 分割後 |
| `off_scale_note_count` / `off_scale_count` | 破線（音階に無い音）の音符 → 分割後 |

長い穴は `divide_length_by_max_len()` が `'bridge_threshold'` ごとに分割するので、
**音符 1 個が `<path>` 複数本になる**。`'20notes'` と `'20notes a'` は音階の
定義が同じで `'bridge_threshold'` だけ違い（50.0 と 2.7）、`tests/data/`
の `long-notes.mid` では音符 69・実線 68 は変わらないのに、分割後は
76 と 608 になる。

つまり**分割後の数は `<path>` を数えれば分かるが、分割前の音符の数は
逆算できない**（多対一のため）。前者は数え、後者は属性に埋めてある。

**画面での線の見え方は `my.css` が上書きしている**（0.2px では細すぎて
読めないため、1px + 実線の穴に薄い塗り）。**生成する SVG は変えない。**
詳しくは `webroot/CLAUDE.md`「ロールブックの見え方（画面だけ）」。

### テスト

書き方は `tests/CLAUDE.md` にある（`tests/browser/` の `live_server`、
`WebAppTestCase` が `webroot` を複製すること）。`tests/` 配下を触ると
読み込まれる。

**`tests/conftest.py` の `isolate_user_config` は消さないこと。** `WebServer` と
`ConfigHandler` は `Conf()` を引数なしで生成するため、これが無いとテストが
`~/etc/storgan-conf.json`（利用者の実設定）を書き換える。実際に書き換えていた。

### ロギング

**標準 `logging` は使わない。** loguru を `mylog.py` 経由で使い、例外は
`exmsg(e)` で整形する。初期化と書式の決めごとは `docs/tech-stack.md`。

## 注意

- `RollBookApp` は `-o` 未指定のとき `~/Desktop/<MIDIファイル名>.svg` に出力する
  （`apps.py` の `DEF_OUT_DIR`）。`-o` を指定した場合はそのパスをそのまま使う。
- **CI は考慮しない。** GitHub Actions などのワークフローを足したり、
  「CI で回すなら」を前提にした作り（テストの分割、ブラウザバイナリの取得手順
  など）を持ち込まない。検証は手元で `uv run pytest` を回して行う。
