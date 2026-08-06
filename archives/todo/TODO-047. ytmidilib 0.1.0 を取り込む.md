# TODO-047. `ytmidilib` 0.1.0 を取り込む

TODO-045 で出した要求書への回答が来た
（[`20260806b-ytmidilib-responses.md`](../20260806b-ytmidilib-responses.md)）。
**13 項目すべて対応済み**とのことだったので、`0.0.3` → `0.1.0` に上げ、
こちら側の手当てを剥がした。

## 取り込み

```toml
ytmidilib = { git = "https://github.com/ytani01/ytmidilib.git", tag = "0.1.0" }
```

タグ `0.1.0` は `88d9fd7`。既定ブランチの先頭（`bbddb1a`）はその 1 つ先だが、
差は上流の TODO.md と回答書だけで、**コードは同一**。

## 剥がした手当て

| 場所 | 直す前 | 直したあと |
|---|---|---|
| `rollbook.py` `HoleInfo.__init__` | `note is not None` で `-1` に読み替え | `note` は `int` なのでそのまま渡す |
| `rollbook.py` `RollBook.parse()` | `parse(str(midi_file), ...)` | `Path` をそのまま渡す（要求 #11） |
| `transpose.py` `_NoteTally` | `ni.end_time - ni.abs_time` | `ni.length()`（要求 #13 で `None` は `0.0`） |
| `apps.py` `MidiApp.main()` | 「`play()` が音符ごとに print する」注意書き | 出なくなったので削除（要求 #4） |

`merge_overlapping_notes()` の `assert cur.end_time is not None` は**残した**。
`end_time` の型は `float | None` のままで（`Parser.parse()` が必ず埋めるという
のは型に出ない事実）、`max()` に渡すには絞り込みが要る。
TODO-044 が言っていた「3 通りの態度」は、これで assert 1 通りに揃った。

## pygame のバナーは、こちらで黙らせた

回答書は「`import ytmidilib` 時の `pygame-ce 2.5.7 ...` はまだ出る。
利用側が `PYGAME_HIDE_SUPPORT_PROMPT` を設定してほしい（ライブラリからは
利用者の pygame の挙動を書き換えたくない）」としていた。妥当なので受けた。

`src/ytstreetorgan/__init__.py` の先頭、`from .rollbook import RollBook`
（＝ `ytmidilib` が読み込まれる経路）**より前**に置いてある。

```python
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', 'hide')
```

`setdefault` なのは、外から明示的に設定されていればそれに従うため。

## `-d` を付けても `ytmidilib` のログは出ない（承知のうえ）

向こうは標準 `logging` でハンドラを付けない作りになった（要求 #10。
ライブラリとして正しい）。こちらは loguru なので、**`ytmidilib` の DEBUG は
どこにも出ない**。`play -d` で出る音符の行は `apps.py` 自身のもの。

TODO-040 で消したかったのは再生中の出力なので、実害は無い。向こうのログを
読みたくなったら、そのとき loguru へ橋渡しする InterceptHandler を入れる。
**先回りして書かない**（TODO-044 / 045 の注意書きと同じ理由）。

## 上流の判断が要求と違った 3 点

| # | 要求 | 上流の判断 | こちらへの影響 |
|---|---|---|---|
| 4 | `print()` をやめる（ロガー or `on_note`） | ロガーのみ。`on_note` は不採用 | 無し。`on_note` は要らない |
| 7 | 戻り値を `TypedDict` に | 対応済みだった。**型名を `ParsedMidi` に改名** | 無し。型名を import していない |
| 8 | `transpose()` の範囲外 | 1 つでも範囲外なら `ValueError` | TODO-042 で使うときに受ける |

## つまずいた点: `uv` の git キャッシュが古いタグしか持っていない

`tag = "0.1.0"` に上げて `uv sync` しても、入るのは
`ytmidilib==0.0.4.dev20+g88d9fd72b` だった。コミットは合っているのに
バージョンだけ合わない。

原因は `~/.cache/uv/git-v0/db/` の bare リポジトリに `refs/tags/0.1.0` が
無いこと。**`uv` はタグを解決してコミットを取ってくるが、キャッシュ済みの
db にタグ ref を足さない**。`ytmidilib` は hatch-vcs でバージョンを決める
ので、`git describe` が `0.0.3-20-g88d9fd7` になってこうなる。
`uv cache clean ytmidilib` だけでは db が残るので直らない。

```bash
\rm -rf ~/.cache/uv/git-v0/db/<hash> ~/.cache/uv/git-v0/checkouts/<hash>
uv cache clean ytmidilib
uv sync --reinstall-package ytmidilib
uv lock --upgrade-package ytmidilib   # uv.lock の version も直す
```

`uv.lock` には解決時のバージョン文字列がそのまま残るので、**最後の
`uv lock --upgrade-package` まで要る**（`uv lock` だけでは書き換わらない）。

## 確認

- `uv run ruff check src tests && uv run mypy src && uv run basedpyright src
  && uv run pytest -m ""` が**通った**（243 passed）。
  `docs/Developer.md`「一括で回す」が実際に通るようになったのは初めて（TODO-044）
- `set_tempo` の無い MIDI（480 tpb・四分音符 3 つ）で `length()` が 0.5 に
  なり、`rollbook` の全長も 0 でなくなった（要求 #1）
- `play` が標準出力に `channel_set=` の 1 行しか出さない（要求 #4）
- `parse -v` の可視化が従来どおり出る（要求 #12 のラッパー化で壊れていない）
