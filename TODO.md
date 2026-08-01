# TODO

作成: 2026-08-02（コミット `82aaa65` 時点）

lint 整備の作業中に洗い出した残作業。優先順位は末尾の「着手順の目安」を参照。

---

## A. 設定項目の見直し（直近コミットの WIP に関係）

`69838d8` / `6259671` の「WIP: 設定項目の見直し」に直結する項目。

### A-1. `bridge interval` がどこからも読まれていない

- [ ] 必須項目から外すか、本来の用途を復活させるかを決める

`validate_config()` が**必須項目**として要求し、`update_model()` / `add_model()` が
float 変換し、`conf/*.conf-*` と `~/etc/storgan-conf.json` とテストの全てに存在するが、
**`rollbook.py` は一度も読んでいない**。

穴の分割に実際に使われているのは以下の 2 つだけ:

- `bridge width` — 分割してできた隙間の幅
- `bridge threshold` — この長さを超えたら分割する閾値

`bridge interval` は設計変更の名残と思われる。必須項目のまま放置すると、
設定エディタの利用者が「必須なのに効かない値」を触ることになる。

確認コマンド:

```bash
grep -rn "bridge interval" src/     # conf.py 以外に出てこない
grep -oP "conf\.get\('\K[^']+" src/ytstreetorgan/rollbook.py | sort -u
```

### A-2. `note name` はサーバー側では未使用

- [ ] 「UI 専用キー」として位置づけを明文化する（廃止はしない想定）

`conf.py` が「`note offset` と長さが一致すること」を検証するだけで、SVG 生成には
使われていない。実際に使っているのは Web の設定エディタ
（`webroot/static/js/config_editor.js:106,131`）のみ。

### A-3. `conf.py` に 11 行の完全重複

- [ ] 数値変換ブロックを共通ヘルパーに切り出す

`update_model()`（`src/ytstreetorgan/conf.py:223` 付近）と
`add_model()`（同 `:254` 付近）に、数値項目を `float` / `int` に変換する
同一のブロックが 2 箇所ある。設定項目を追加・削除するたびに 2 箇所直す必要がある。

**A-1 に着手する前にこれを片付けておくと安全。**

---

## B. `os.path` → `pathlib` 移行（26 件 / 8 ファイル）

チェックリストは `pyproject.toml` の `[tool.ruff.lint.per-file-ignores]` に仕込み済み。
**1 ファイル移行したら、その行を消す。全部消えたら移行完了。**
移行済みファイルに `os.path` が再び入ると、その時点で `ruff` が落ちる。

残数の確認:

```bash
uv run ruff check --isolated --select PTH --statistics src tests
```

| ファイル | 件数 | 備考 |
|---|---|---|
| `tests/test_webapp_async.py` | 12 | テスト内で完結。影響範囲は閉じている |
| `src/ytstreetorgan/handler1.py` | 5 | ← B-1 と同時にやる |
| `src/ytstreetorgan/webapp.py` | 3 | ← B-1 と同時にやる |
| `src/ytstreetorgan/conf.py` | 2 | 下記の注意あり |
| `tests/test_webapp.py` | 1 | |
| `tests/test_rollbook.py` | 1 | |
| `tests/test_main.py` | 1 | |
| `src/ytstreetorgan/rollbook.py` | 1 | `parse_to_file()` の `open()` のみ |

**`conf.py` の注意**: 2 件のうち片方は `SEARCH_PATH` の `Path('.')` を `Path()` に
しろという `PTH201`。あそこは明示的なほうが読みやすいので、行ごと消さずに
`"src/ytstreetorgan/conf.py" = ["PTH201"]` と**そのルールだけ残す**のを推奨。

### B-1. `webroot` / `workdir` が `str` で配線されている

- [ ] `WebServer` → `app.settings` → 各ハンドラの経路を `Path` に揃える

`WebServer.__init__` から `app.settings` 経由で各ハンドラに `str` として渡っている。
`handler1.py` と `webapp.py` の pathlib 移行は、この配線を `Path` に変える作業と
セットにしないと、`str` と `Path` が混在して逆に読みにくくなる。

**移行タスクの中で最も設計判断が要る部分。**

---

## C. `README.md` が実態と乖離

- [ ] 現行の手順に書き直す（または現状を正とする最小限の修正）

冒頭に **DEPRECATED** と書かれたまま、以下が食い違っている。

| README の記述 | 実際 |
|---|---|
| `git clone .../StreetOrgan.git` + `install.sh` | `uv sync` |
| `http://hostname:10081/storgan/` | `/storgan2/` |
| `Storgan -h` | `ytstreetorgan -h` |
| `![](docs/StreetOrgan-Book1.jpg)` | 画像ファイルが存在しない |

`CLAUDE.md` には「参照しないこと」と注記済みだが、README 自体は未修正。

---

## D. 雑多

- [ ] `webroot/svg/` の古い成果物を削除（9 件中 7 件が `127b94d` より前の生成物で、
      `stroke-width` も book height も現行と異なる）。gitignore 済みなので実害はないが、
      出力を目視比較するときに紛らわしい。
- [ ] `archives/` が `.gitignore` されている件の意図確認（過去の計画書 4 件）。
      意図的なら対応不要。
- [ ] Claude Code のプラグイン `github` / `frontend-design` が 60 起動で 0 回のまま有効。
      `/doctor` で「変更しない」を選択済みなので、気が向いたら `/plugin` から。

---

## 着手順の目安

1. **A-3 → A-1** — WIP 中のテーマそのもの。必須項目なのに未使用という状態は
   設定エディタの利用者を確実に混乱させる。A-3 の共通化を先にやると A-1 が楽になる。
2. **C（README）** — 手戻りが最も少なく、外から見える部分。
3. **B（pathlib）** — 動作は今のままで正しいので急ぎではない。やるなら
   `handler1.py` + `webapp.py` + B-1 の配線変更を 1 セットで。

---

## 完了済み（`82aaa65`）

参考までに、この TODO を作成した作業で片付いたもの:

- テスト 2 件の失敗を解消（`validate_config` の型ガード追加、古い期待値の更新）
- ruff の設定整備（`select` 拡張、`line-length = 88`、指摘 76 件を解消）
- flake8 を削除（無設定のまま ruff と併存し、8 対 102 件で食い違っていた）
- `RollBookApp` の `-o` が無視されていた問題を修正
- `uv.lock` を追跡対象に
- `CLAUDE.md` を追加
