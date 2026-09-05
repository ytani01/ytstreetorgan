# TODO-090 検証報告

## 検証内容と結果

### 1. 検証コマンドの実行

すべて正常に完了：

- `uv run pytest -q` → 303 passed, 49 deselected (2.15s)
- `uv run ruff check src tests` → All checks passed!
- `uv run mypy src` → Success: no issues found in 18 source files

### 2. 内容の欠落・改変

移す前の `CLAUDE.md` の「## アーキテクチャ」節（元の `### レイヤー分離` から `### ロギング` まで）の記述は、`docs/Architecture.md` に正しく移されている。意図的に `CLAUDE.md` に残された 3 節（「画面に出す用語」「フロントエンド / 確認の出し方」「テスト」）は指示通りに残っている。

**ただし 1 つの内容の変更あり**：

- 9 章「ロギング」：元の `docs/tech-stack.md` のリンクが `[tech-stack.md](tech-stack.md)` に変更された。これは **正しい変更**。Architecture.md は docs/ ディレクトリにあるため、相対リンクを修正したもの。リンク先は確認済みで有効。

### 3. 重複情報

- 「画面に出す用語」：CLAUDE.md にのみ存在（Architecture.md には無し）✓
- 「フロントエンド / 確認の出し方」：CLAUDE.md にのみ存在（Architecture.md には無し）✓
- 「テスト」：CLAUDE.md にのみ存在（Architecture.md には無し）✓
- 「ロギング」：Architecture.md にのみ存在（CLAUDE.md には無し）✓

重複はない。

### 4. 実装との食い違い

#### 問題を発見した：穴の数え方（8 章）のプロパティ名

**Architecture.md（line 469-472 の表）の プロパティ名が実装と一致していない。**

Architecture.md に書かれているプロパティ名：
```
| `note_count` | MIDI から読んだ音符の数（実線と破線の合計） |
| `hole_note_count` / `hole_count` | 実線（音階にある音）の音符 → 分割後 |
| `off_scale_note_count` / `off_scale_count` | 破線（音階に無い音）の音符 → 分割後 |
```

実装（`src/ytstreetorgan/storage.py` の `BookInfo` TypedDict）の実際のプロパティ名：
```python
notes: int | None                    # note_count ではなく notes
hole_notes: int | None              # hole_note_count ではなく hole_notes
holes: int | None                   # hole_count ではなく holes
off_scale_notes: int | None         # off_scale_note_count ではなく off_scale_notes
off_scale: int | None               # off_scale_count ではなく off_scale
```

#### その他の確認事項

以下は確認済みで正確：

- 3 章の設定ファイル探索順（`.` → `~/.config` → `~/etc` → `/usr/local/etc` → `/etc`）：✓ 実装と一致（`src/ytstreetorgan/conf.py` の `SEARCH_PATH`）
- 4 章の SVG 座標系：✓ 正確
  - `svg_square()` のパス：`M {-x},{-y} h {-w} v {-h} h {w} Z` ✓
  - `viewBox` 値：`-width -height width height` ✓
- 2 章のモジュール import 表（13 モジュール）：✓ 実装と一致
- 6 章のハンドラと URL：✓ 実装と一致（Tornado ハンドラ定義と突き合わせ）

### 5. リンク確認

確認済みで有効なリンク：

- `[User.md](User.md)` ✓
- `[Developer.md](Developer.md)` ✓
- `[tech-stack.md](tech-stack.md)` ✓
- `[../webroot/CLAUDE.md](../webroot/CLAUDE.md)` ✓
- `[../tests/CLAUDE.md](../tests/CLAUDE.md)` ✓
- 目次アンカー（`#1-全体像` など）：構文正確、セクション見出しと一致

## まとめ

**合格ラインを越えていない。** 8 章「穴の数え方」のプロパティ名の誤りが確認タスクで指摘された項目であり、これは修正が必要。
