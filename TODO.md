# TODO

作成: 2026-08-02（コミット `82aaa65` 時点）

lint 整備の作業中に洗い出した残作業。優先順位は末尾の「着手順の目安」を参照。

---

## A. 設定項目の見直し（直近コミットの WIP に関係）

`69838d8` / `6259671` の「WIP: 設定項目の見直し」に直結する項目。

### A-2. `note name` はサーバー側では未使用

- [ ] 「UI 専用キー」として位置づけを明文化する（廃止はしない想定）

`conf.py` が「`note offset` と長さが一致すること」を検証するだけで、SVG 生成には
使われていない。実際に使っているのは Web の設定エディタ
（`webroot/static/js/config_editor.js:106,131`）のみ。

---

## F. ブラウザテストを整備する

- [ ] 代表的な 5 本から、実用的なカバレッジまで広げる

土台は `tests/browser/` に用意済み（`conftest.py` の `live_server` fixture、
`pytest -m browser` で実行）。現状は 5 本のみ。

未着手の領域:

- 設定エディタ: 機種の追加（`btn-add-model` とモーダル）、削除、
  「既存からコピー」の挙動
- 入力値の検証: 必須項目を空にした場合、数値欄に不正な値を入れた場合に
  どうなるか（サーバー側の 400 がユーザーにどう見えるか）
- エラー表示: 保存失敗時の `showAlert` の出方
- アップロード: サイズ上限超え、MIDI でないファイル
- CI で回すなら Chromium バイナリの取得（数百 MB）をどうするか

注意: `pytest-playwright` の fixture はメインスレッドにイベントループを残すため、
tornado の `AsyncHTTPTestCase` より先に実行すると後者が落ちる。
`tests/conftest.py` の `pytest_collection_modifyitems` で browser マーカーを
末尾に回して回避している（`d19ff52`）。テストを足すときはこの制約に注意。

---

## G. Web UI を Pico.css で作り直す

- [ ] `pico.min.css`（v2.1.1 / 83KB）を `webroot/static/css/` に置く
- [ ] `storgan.html` / `config_editor.html` を Pico ベースに書き換え、CDN 参照を全廃する
- [ ] `config_editor.js` の DOM 生成部分（Bootstrap のクラス名）を修正する
- [ ] `tests/browser/` が通ることを確認する

モック（3 画面、実データ入り、明暗両テーマ）:
<https://claude.ai/code/artifact/05378ca3-d845-4e9d-8b95-6e591105684e>

現状 CDN を 6 本読んでいる（Bootstrap CSS/JS、Font Awesome、jQuery、popper、socket.io）。
**ローカルで動かす道具なのに、ネットに繋がっていないとレイアウトが崩れる。**
`webroot/static/css/my.css` は 0 バイトで、ローカルには何も無い。
`storgan.html` の socket.io と jQuery/popper はどこからも使われていない。

Pico.css を選んだ理由は、画面が 2 つしかなくデザインシステムを持つ必要がないこと、
1 ファイル同梱で依存が消えること、`data-theme` によるダーク対応が標準で付くこと。

決めたこと:

- 配色は生成される SVG から採る（外枠の青 `#0000FF` → 主要アクション `#2947c8`、
  穴の赤 `#FF0000` → 破壊的操作 `#c8392f`）
- 数値は等幅 + `tabular-nums`。寸法を扱う道具なので桁が揃わないと読みにくい
- Web フォントは使わない。日本語フォントは埋め込むとサイズが現実的でないため、
  システムフォントに統一する
- Font Awesome はインライン SVG に置き換えて、アイコン用の CDN も消す

注意点:

- **Pico はボタン要素の中で `--pico-color` を上書きする。** 自前のコントロールに
  `color: var(--pico-color)` と書くとボタン内では白くなる。独自トークンが要る
- `tests/browser/` は要素 ID で操作しているので、ID を保てばテストはほぼそのまま通る

---

## H. 生成した SVG をブラウザ上でズーム・スクロールできるようにする

- [ ] `RollBook` にブックの幅・高さを取り出すプロパティを足す
- [ ] `Handler1` が SVG 全文をテンプレートに渡す設計を見直す
- [ ] `storgan.html` の SVG を `<a href=ダウンロード>` の中から出す
- [ ] ビューア本体（横スクロール + 倍率）を実装する

G のモックに実装済みで、実データでの動作は確認してある。

**transform による拡縮ではなく、SVG の描画サイズそのものを変える。** こうすると
ブラウザ標準のスクロールがそのまま効き、スクロールバーが全体の中の現在位置を示す。
SVG が `width="…mm"` で出力されているので、倍率 1.0 がそのまま原寸になる。
汎用の panzoom ライブラリ（`svg-pan-zoom` 等）は transform ベースで、
縦横比 33:1 のロールブックではスクロールバーが消えて現在位置を見失うので使わない。

モックから導出した仕様:

- 既定は「高さ合わせ」。「全体」を既定にすると 7% になって何も読めない
  （`d-kaeru.mid` / 34notes で 4133.20mm × 126.00mm、穴 1037 個）
- **初期表示は右端。** `viewBox` が `-4133.20 -126.00 …` で、曲の先頭が
  x=0 側 = 右端にあるため
- `1sec` = 50mm なので、スクロール位置がそのまま演奏時間になる。
  位置（mm）と時間の両方を出す
- 全長 4m に対してスクロールバーだけでは足りないので、ミニマップの帯を出す

`RollBook` の寸法プロパティが先に要るのは、いま SVG 文字列を作らないと寸法が
分からず、テンプレート側で初期倍率を計算できないため。

---

## 着手順の目安

1. **A-2（`note name` の位置づけ）** — 小さい。ドキュメント上の整理のみ。
2. **G（Pico.css への移行）** — モックがあるので、あとは適用するだけ。
   CDN 依存の解消という実利もある。
3. **H（SVG ビューア）** — G の後。テンプレートを二度書き換えずに済む。
4. **F（ブラウザテスト）** — 土台はあるので、書けば書いた分だけ増える。
   G / H で画面が変わるため、その後に広げるほうが手戻りが少ない。

---

## 完了済み

### B. `os.path` → `pathlib` 移行

26 件すべて解消。`per-file-ignores` の移行チェックリストは空になった。

B-1（`webroot` / `workdir` の `str` 配線）も同時に解消。`WebServer` が
`Path` に正規化し、`app.settings` にも `Path` のまま渡すようにしたので、
各ハンドラは `self._webroot / 'svg' / fname` と書ける。

`Conf.SEARCH_PATH` の `Path('.')` だけは `PTH201` を除外して残した
（探索対象がカレントであることを明示するほうが読みやすいため）。

検証: SVG 出力が HEAD とバイト一致（195,330 bytes）。CLI・Web とも通しで動作確認。

### `webroot/svg/` の古い成果物を削除

`127b94d`（hairline 対応）より前に生成された 7 件を削除した。`stroke-width` も
book height も現行と異なり、出力を目視比較するときに紛らわしかった。
元 MIDI は `webroot/midi/` に残っているのでいつでも再生成できる。

### Claude Code のプラグインをこのプロジェクトで無効化

`github` / `frontend-design` は 60 起動で 0 回だった。他プロジェクトでは使うため、
ユーザースコープ（`~/.claude/settings.json`）は有効のまま、このプロジェクトの
`.claude/settings.local.json` で `false` にした（設定の優先順位は
ユーザー < プロジェクト < ローカル）。`pyright-lsp` は Python なので有効のまま。
※ `settings.local.json` は gitignore されているため、リポジトリには残らない。

### `URL_PREFIX_HANDLER1` を削除

`/{prefix}/handler1.*` のルートは、テンプレートからも JS からも参照されない
死んだ経路だった。冗長だった `url_prefix_handler1` 設定も外し、`handler1.py` の
`_url_path` は `_urlprefix` から組み立てるようにした。
末尾スラッシュなしのリダイレクト（`/px` → 301 → `/px/`）は従来どおり。

### E. URL prefix の扱いを整理

テストの `/storgan2` 直書き 12 箇所を排除し、テスト全体を既定値以外の
prefix（`/storgan-test`）で動かすようにした。テンプレートや JS が prefix を
直書きすると `test_static_assets_load` が落ちる（実際に壊して検証済み）。

**併せて発覚した問題を修正**: `test_config_handler` の add/delete テストが
`~/etc/storgan-conf.json`（利用者の実設定）を書き換えていた。
`tests/conftest.py` の autouse fixture で `Conf.SEARCH_PATH` を一時ディレクトリに
差し替え、全テストから実設定を隔離した。

### `archives/` を追跡対象に

過去の計画書 4 件。最新仕様の参考にはならないが、記録として残す。

### C. README.md を現状に合わせて書き直し

インストール/ダウンロード手順を全削除し、機能の説明を中心にした。
旧リポジトリの clone 手順、廃止された URL・コマンド名、存在しない
画像への参照がすべて消えた。使い方は `--help` への誘導のみ。

### A-3. 数値変換の重複を解消

`update_model()` / `add_model()` に同一の変換ブロックが 2 箇所あり、
さらに `validate_config()` が必須項目一覧を別途持っていた（計 3 箇所）。
`NUMERIC_FIELDS`（項目名 → 変換関数の dict）に集約し、検証と変換の
両方がこれを参照するようにした。**設定項目の増減はここ 1 箇所で済む。**

副次的に、`base note` に `"60.5"` のような値を渡すと検証を通ったあとで
`int()` が `ValueError` を投げて 500 になっていた不具合が解消した
（検証に変換関数そのものを使うようにしたため 400 が返る）。回帰テスト追加済み。

### A-1. `bridge interval` を設定項目から削除

`validate_config()` が必須項目として要求していたが `rollbook.py` は一度も
読んでいなかったため、スキーマ・検証・設定エディタ・設定テンプレート・テストの
全てから削除した。穴の分割に使われるのは `bridge width` と `bridge threshold` のみ。

既存の設定ファイルにキーが残っていても検証は通る（後方互換あり）。
`~/etc/storgan-conf.json` の 4 モデルには未使用キーとして残っている。

### `82aaa65`

- テスト 2 件の失敗を解消（`validate_config` の型ガード追加、古い期待値の更新）
- ruff の設定整備（`select` 拡張、`line-length = 88`、指摘 76 件を解消）
- flake8 を削除（無設定のまま ruff と併存し、8 対 102 件で食い違っていた）
- `RollBookApp` の `-o` が無視されていた問題を修正
- `uv.lock` を追跡対象に
- `CLAUDE.md` を追加
