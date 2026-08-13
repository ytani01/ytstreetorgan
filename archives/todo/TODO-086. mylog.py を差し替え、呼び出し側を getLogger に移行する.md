# TODO-086. `mylog.py` を差し替え、呼び出し側を `getLogger` に移行する

## きっかけ

名前ごとにログの水準を持てる版の `mylog.py` を書いた
（`src/ytstreetorgan/mylog-new.py` として置いてあった）。

- `getLogger(name, level)` — `logger.bind(log_name=name)` した logger を返す
- `setLevel(name, level)` — 名前ごとの水準を設定する（`None` で既定に戻る）
- `loggerInit()` が張るシンクは `level=0` + `filter=_filter` で、
  `_filter()` が `extra['log_name']` と `_levels` を突き合わせる

既存の API（`LOG_FMT` / `logLevel` / `loggerInit` / `exmsg`）はそのまま
残っているので、差し替えだけなら呼び出し側は無変更でも動く（`log_name`
が無ければ既定水準で判定される）。**が、それでは名前を付けた意味が無い**
ので、呼び出し側も移行した。

## やったこと

- `mylog-new.py` を `mylog.py` へ移した（差分は `getLogger()` /
  `setLevel()` / `_filter()` の追加と、`out: TextIO` などの型注記）
- 名前の付け方を決めた
  - クラス: クラス本体に `__log = getLogger(__qualname__)` を置き、
    `self.__log.debug(...)` で書く
  - クラスの無いモジュール: 先頭に `_log = getLogger('<モジュール名>')`
    （`__main__.py` だけは `'main'`）
- `src/` の 15 ファイル、`logger.` の呼び出し 100 か所ほどを書き換え、
  `from loguru import logger` を `mylog.py` の中だけにした
  - クラスに紐づけたもの — `StorganBaseHandler` / `Handler1` /
    `Download` / `DownloadTransposedMidi` / `DownloadTransposedMidiZip` /
    `AuditionMidi` / `HistoryHandler` / `ConfigHandler` /
    `LiveReloadHandler` / `WebServer` / `Conf` / `RollBook` /
    `HoleInfo` / `RollBookApp` / `MidiApp`
  - モジュールに紐づけたもの — `main`（`__main__.py`）/ `transpose` /
    `rollbook`（`svg_square()` と `divide_length_by_max_len()`）/
    `storage` / `audition` / `livereload`（`watch_webroot()`）
- `__init__.py` の再エクスポートを `logger` から `getLogger` に変えた
  （`__all__` も）
- `tests/test_webserver_init.py` の `@patch('ytstreetorgan.webapp.logger')`
  を外した。モックは使っておらず、`pytest.raises` で確かめている
- `tests/test_mylog.py` に `TestNamedLogger` を足した（6 件）
- `docs/tech-stack.md` の「ロギング設計」と `CLAUDE.md` の「ロギング」を
  書き直した

### 決めたこと

- **名前はログに出さない。** `LOG_FMT` には入れていない。水準を切り替える
  単位でしかなく、どこから出たかは `{file}:{line} {function}()` で分かる
- **名前ごとの水準はモジュールの辞書 `_levels` に残る。** `conftest.py` の
  `reset_logger` は loguru のシンクしか消さないので、テストで `setLevel()`
  を使ったら `setLevel(name, None)` で必ず戻す

## テスト

- `uv run pytest -q` → 303 件すべて成功
- `uv run pytest -m browser -q` → 49 件すべて成功
- `uv run ruff check src tests` / `uv run mypy src` → 問題なし
- `uv run ytstreetorgan -d rollbook tests/data/sample.mid -m 34notes -o ...`
  と、`-d` 無しの両方で出力を確認
- `loggerInit(debug=False)` ＋ `setLevel('RollBook', 'DEBUG')` で、
  `RollBook` の DEBUG だけが出ることを確認した（`Conf` や
  `rollbook` モジュールの関数は INFO のまま）
