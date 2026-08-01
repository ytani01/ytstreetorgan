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

1. **A-2（`note name` の位置づけ）** — 小さい。ドキュメント上の整理のみ。
2. **B（pathlib）** — 動作は今のままで正しいので急ぎではない。やるなら
   `handler1.py` + `webapp.py` + B-1 の配線変更を 1 セットで。

---

## 完了済み

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
