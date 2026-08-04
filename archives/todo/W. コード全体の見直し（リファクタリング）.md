# W. コード全体の見直し（リファクタリング）

`src/` を一通り読んだ棚卸し。**全項目が片付いた。**
上から順に、放っておくと事故になるもの → 重複 → 使っていないもの →
様式の順に並べてある。

進め方（次に同じことをするときも同じでよい）:

- **1 コミット 1 テーマ。** まとめて直すと、落ちたときにどれが原因か分からない
- 意味を変えない変更でも、**都度 `uv run pytest -q` と `-m browser`** を通す
- 図が変わらないはずの変更は、**変更前のコードと SVG を突き合わせる**
  （`git worktree` で前の版を出し、4 機種 × 3 曲で `cmp`）
- CLAUDE.md に書いてある取り決め（座標系・穴の数え方・`storage.py` を通す・
  `isolate_user_config` など）は**仕様**。壊さない。直すなら CLAUDE.md も直す

## W-1. 放っておくと事故になるもの

- [x] 1. **`RollBook.parse()` が 2 回呼べなかった。** `_holes` を初期化せず
  `append` するので穴が二重になり、`_width` も `max()` で伸びたままだった。
  → `parse()` の先頭で捨てる（`0b49d16`）
- [x] 2. **設定値が欠けていても 0 で描いていた。** `Conf.get()` は知らない
  機種名に `{}` を返し、`HoleInfo` は足りない項目を既定値 0 で読む。この
  2 つが重なって、機種名を打ち間違えるだけで「高さ 0 の空のブック」が
  何事もなく出ていた。→ `RollBook.__init__` が `validate_config()` で弾き、
  Web 側は `Handler1._rollbook_of()` が捕まえて画面に理由を出す（`be0979a`）
- [x] 3. 設定が見つからないときに**探した場所が分からなかった**。
  → 候補を全部並べたメッセージにする（`f7919bf`）
- [x] 4. **リクエストのたびの設定読み直しは、このままとする（対応しない）。**
  `Handler1.__init__` / `HistoryHandler.get` / `ConfigHandler` /
  `RollBook.__init__` がそれぞれ `Conf()` を作るので、1 回の生成で 2 回開く。
  設定ファイルは数 KB で、実測できるほどの遅さではない。キャッシュを
  入れると「設定エディタで保存した内容が即座に反映されるか」を mtime で
  担保する複雑さが増える。**割に合わないので入れない。**
- [x] 5. 誰も読まない `app.settings['models']` を外した（`41a3bc9`）
- [x] 27. **`tests/test_webapp_async.py` が実物の `webroot/` を使っていた。**
  R で直したことになっていて、**コミット `dbcbfe0` の説明文もそう書いている
  が、実際にはこのファイルに手が入っていない**（`webapp_base.py` を作って
  `test_history.py` を載せただけ）。`TestWebAppAsync` は
  `webroot=Path('./webroot')` を渡し、`webroot/midi/dummy.mid` と
  `webroot/svg/dummy.mid.svg` を実際に書いて `tearDown` で消していた。
  途中で落ちれば消し残る。→ 3 クラスとも `WebAppTestCase` に載せ替えた
  （`687e0ab`）。わざと落として実物が汚れないことも確認した

## W-2. 同じものが 2 か所以上にあった（済）

- [x] 6. サイズの書式を `storage.size_text()` に集約。ついでに
  `StorganBaseHandler.get_filesize()`（`tuple | None` を返して呼び出し側が
  `assert` していた）を廃止（`4ba5b04`）
- [x] 7. 全ページ共通の render 引数を
  `StorganBaseHandler.render_page()` に集約（`b3c8fff`）
- [x] 8/9. 置き場の引き方（`resolve_in` → `is_file` → エラー描画）を
  `_stored_path()` に、失敗メッセージを `UNREADABLE_MSG` に（`119b65e`）
- [x] 10. `Conf` の線形探索を `_index_of()`、機種名の取り出しを
  `_model_names()`、`load()` の 4 つの except を 1 つに（`9b01157`）
- [x] 11. 線の色と属性の接頭辞は **rollbook が持ち主**。storage は
  import して使う（`a0f7679`）
- [x] 12. `showAlert()` を `static/js/alert.js` に（`6655170`）
- [x] 13. `'---'` はサーバーが `unknown` として渡す（`c960b00`）

## W-3. 使っていなかったもの（済）

`0e6dbb8` でまとめて削除。**4 機種 × 3 曲で、変更前と SVG がバイト単位で
一致することを確認した。**

- [x] 14. `RollBook.svg()` の色・線幅・破線の引数（既定値でしか
  呼ばれていなかった）
- [x] 15. `divide_length_by_max_len()` の `n` と `unit_len`
  （`DivisionResult` ごと削除）
- [x] 16. `RollBookApp` の `version` / `debug`。**`end()` は残した**
  （`main()` と対の掛け金で、テストも呼び出しを見ている）
- [x] 17. `Conf.__init__(debug=...)`
- [x] 18. `# pylint: disable=` 3 か所

## W-4. 様式（済）

- [x] 19. docstring を**日本語 + Google 形式**に統一（`3419da3`）。
  副産物として click の help も日本語になった
- [x] 20/21. `-d` のとき tornado の Application や `dir(request)` を
  丸ごと出していたのをやめ、ログの書式を `{}` 形式に揃えた（`5a1781b`）。
  実測（起動 + リクエスト 1 回）で 3829 → 2226 文字、最長 843 → 134 字
- [x] 22. ルーティングの形を揃えた（`401ab35`）。`/config.*` は
  `/configXYZ` まで拾っていた。`download` の種別はルート定義の引数で
  渡すようにして、`kind: str | None` という不自然な型を無くした
- [x] 23. **`RollBook.DEF_CONF_FILE = ''` はこのままとする（対応しない）。**
  「空文字＝`SEARCH_PATH` を探す」という約束は `Conf` の docstring に
  書いてある。`str | None` に変えると `Conf` の引数・呼び出し・テストに
  広く波及するわりに、得られるのは型の見た目だけ

## W-5. テストとフロント（済）

- [x] 24. ブラウザテストのアップロード用ヘルパを
  `tests/browser/conftest.py` の `upload_midi()` に 1 本化（`48c4a74`）。
  **2 本で完了待ちの有無が違っていた**ので、待つほうを既定にした
- [x] 25. `test_webapp.py` → `test_webserver_init.py`、
  `test_webapp_async.py` → `test_rollbook_page_http.py`（同上）
- [x] 26. ビューアを `viewer.js` に分けた（`06ab09b`）。
  storgan.js は 386 → 160 行

---

**これは記録で、現行仕様ではない**（仕様は `CLAUDE.md` と `docs/`）。
一覧は [TODO.md](../../TODO.md) にある。
