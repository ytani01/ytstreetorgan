# Tech Stack

`pyproject.toml` が正。ここはその要約と、なぜそれを選んでいるかの覚え書き。

## 言語・ランタイム

- Python >= 3.13
- パッケージ管理: `uv`（すべて `uv run` 経由で実行する）
- バージョンは **hatch-vcs が git タグから生成**する（ビルドは hatchling）。
  **未インストールのチェックアウトで直接実行すると `__version__` が
  `0.0.0` になる**（画面のフッターにもそう出る）

## 主要ライブラリ

| ライブラリ | 用途 |
|---|---|
| **click** | CLI |
| **tornado** | Web サーバー（テンプレートも tornado のもの） |
| **ytmidilib** | MIDI の解析・再生・書き出し。**git 依存**（`[tool.uv.sources]`） |
| **pygame-ce** | MIDI 再生の実体（ytmidilib が使う） |
| **loguru** >= 0.7.3 | ログ。標準 `logging` は使わない |

### `ytmidilib`（別リポジトリ）

**タグで固定してある**（`tag = "0.5.1"`。`v` は付かない）。既定ブランチを
追わせない。上流を直したらタグを打ち、こちらで上げる。

```bash
uv sync --upgrade-package ytmidilib
```

**タグを上げたのにバージョンが `0.0.4.dev20+g...` のように入ることがある。**
`uv` の git キャッシュ（`~/.cache/uv/git-v0/db/`）に新しいタグの ref が
入らず、hatch-vcs の `git describe` が古いタグからの距離を返すため。
db と checkouts を消してから入れ直す（TODO-047 に手順がある）。

`ytmidilib` も **loguru** を使う（0.2.0 から。それまでは標準 `logging` で、
**向こうのログはどこにも出なかった**）。同じグローバル `logger` なので、
こちらの `loggerInit()` が張ったシンクへ向こうのログも流れる。
**`-d` を付けると `ytmidilib` の DEBUG も混ざって出る**（`Player.play()` の
音符ごとの行など）。

向こうの `parse(debug=)` / `Player(debug=)` は引数としては残っているが、
**水準には影響しない**（上流が互換のために残しただけ）。水準を決めるのは
`loggerInit()` だけなので、こちらからは渡していない（TODO-058）。

0.3.0 でパージングと可視化が `Parser` のメソッドからモジュール関数
（`parse()` / `mk_visual()` / `print_visual()`）へ切り出された。`Parser`
自体は互換のために残っているが、状態を持たないので、こちらは
インスタンスを作らずモジュール関数を直に呼ぶ（TODO-085）。

`pygame` は import されるだけでバナーを出す。`ytmidilib.Player` 経由で
必ず読み込まれるので、`src/ytstreetorgan/__init__.py` の先頭で
`PYGAME_HIDE_SUPPORT_PROMPT` を設定して黙らせている（**`ytmidilib` を
読み込むより前**でないと効かない）。

## フロントエンド

**外部 CDN は 1 本も読まない。** ローカルで動かす道具なので、ネットに
繋がっていなくてもレイアウトが崩れないこと。

- **Pico.css v2.1.1** を `webroot/static/css/pico.min.css` に同梱
- jQuery / Bootstrap / アイコンフォントへの依存は無い。**アイコンは
  インライン SVG**、フォントはシステムフォント
- ビルド工程は無い。`webroot/static/js/*.js` を素の JS で書いて、
  テンプレートから `static_url()` で読む

### MIDI の試聴（TODO-063）に同梱した 3 本

`https://unpkg.com/<パッケージ>@<版>/<パス>` から curl で取得した。
ライセンス全文と sha256 は `webroot/static/vendor/LICENSES.md` にある。

| ファイル | パッケージ | 版 | サイズ | ライセンス |
|---|---|---|---|---|
| `webroot/static/vendor/Tone.js` | tone | 14.7.58 | 347,852 バイト | MIT |
| `webroot/static/vendor/core.js` | @magenta/music の `es6/core.js` | 1.23.1 | 241,786 バイト | Apache-2.0 |
| `webroot/static/vendor/html-midi-player.js` | html-midi-player の `dist/midi-player.min.js` | 1.6.0 | 13,994 バイト | BSD 2-Clause |

- **Tone は 14.x に固定する。** @magenta/music 1.23.1 が想定しているのが
  14 系で、上げると鳴らなくなる
- **`sound-font` 属性は付けない。** 付けると音源を
  `storage.googleapis.com` から取りに行く。「外部 CDN は 1 本も読まない」
  方針に反する
- **`.map`（ソースマップ）は同梱しない**

詳しくは `webroot/CLAUDE.md`。

## ロギング設計

- **入口**: `mylog.py`（loguru の薄い包み）
- **初期化**: 各 CLI コマンドの先頭で `loggerInit(debug)` を 1 度だけ呼ぶ
- **クラス**: クラス本体に `__log = getLogger(__qualname__)` を置き、
  `self.__log.debug(...)` で書く（TODO-086）
- **クラスの無いモジュール**: 先頭に `_log = getLogger('<モジュール名>')`
  を置く（`__main__.py` だけは `'main'`）
- **`from loguru import logger` は書かない**（`mylog.py` の中だけ）
- **書式**: `self.__log.debug('x={}', x)` の形にする（f-string にしない。
  水準で抑止されるときに整形しなくて済む）
- **例外**: `exmsg(e)` で 1 行に整形する

**名前ごとに水準を変えられる**（TODO-086）。`getLogger(name, level)` か
`setLevel(name, level)` で、そこだけ `-d` 無しで DEBUG にしたり、逆に
黙らせたりできる。`setLevel(name, None)` で既定に戻る。既定の水準（名前は
`''`）は `loggerInit(debug)` が決める。仕掛けは `logger.bind(log_name=...)`
と、`loggerInit()` が張るシンクの `filter=_filter`。

**名前そのものはログに出ない**（`LOG_FMT` に入れていない）。水準を
切り替える単位でしかなく、どこから出たかは `{file}:{line} {function}()`
で分かる。

## 開発ツール

| ツール | 用途 |
|---|---|
| **pytest** / **pytest-cov** | テストとカバレッジ |
| **pytest-playwright** | ブラウザテスト（`-m browser`。実 Chromium を起動する） |
| **ruff** | lint と import の並べ替え（flake8 は使っていない） |
| **mypy** / **basedpyright** | 型チェック（対象は `src` のみ） |

実行方法は `docs/Developer.md`。
