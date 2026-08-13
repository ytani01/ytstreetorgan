# TODO-087. ドキュメントと実装の食い違いを直す

## きっかけ

ドキュメントと実装の全体を突き合わせたところ、複数の食い違いが見つかった。

## やったこと

1. `docs/Developer.md` のテスト件数を実測に合わせた（297 / 49 / 346 →
   303 / 49 / 352）。`pytest --collect-only` で実測した。
2. `CLAUDE.md` の `long-notes.mid` 分割後の穴の数を直した
   （`20notes a` が 608 → 677）。実際は `~/etc/storgan-conf.json`
   （実運用の設定）と `conf/storgan-conf.json`（テンプレート、テストが使う）
   とで `'20notes a'` の `bridge_threshold` が違っていた（2.8 と 2.7）。
   `CLAUDE.md` が指しているのはテンプレート側の値（テストの前提）なので、
   テンプレートで計算した 677 に直した。
3. `CLAUDE.md` のモジュール依存図に `storage.py` と `utils.py` を入れた。
   実際の import 関係を `grep` で確かめ、`rollbook.py → storage.py →
   base_handler.py`（`audition.py` ではない）、`rollbook.py → audition.py
   → download.py`、`storage.py` / `handler1.py` → `utils.py` の形に直した。
4. `CLAUDE.md` が参照する `docs/Developer.md` の見出し名を直した
   （「コミット前に通すもの」→「一括で回す」）。
5. `TODO.md` の TODO-064 のリンクを直した。実ファイル名の括弧が生のままで、
   Markdown のリンク構文と衝突していた（`(国際標準)` の部分だけ URL 側を
   `%28` / `%29` にした。表示テキストとファイル名は生のまま）。
6. `docs/multi_agent_token_savings.md` をどうするか決めた。
   Gemini CLI の `define_subagent` / `invoke_subagent` を前提にした内容で、
   現行の運用（`~/.claude/CLAUDE.md` に記載）と重なっており、テスト件数や
   `CLAUDE.md` のサイズなど数値も古かった。**削除はせず**
   `archives/20260814a-multi_agent_token_savings.md` へ移した
   （検討過程の記録として残すため）。

## テスト

`uv run pytest -q` / `uv run ruff check src tests` / `uv run mypy src` を実行し、
いずれも問題なし（303 件成功）。
