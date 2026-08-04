# I. ブラウザ側の live reload（開発時のみ）

`webapp --debug` で起動すると、テンプレート / CSS / JS を直したときに
ブラウザが勝手に再読み込みされるようにした。実装は `livereload.py`。

方針は計画どおり。サーバー側にファイル監視のロジックは無く、
**「切断そのものが更新の合図」**になっている。

1. `watch_webroot()` が `templates/` と `static/` を `tornado.autoreload` の
   監視対象に足す（`.py` 以外でもプロセスが再起動する）
2. `LiveReloadHandler` は繋がるだけの WebSocket。何も送らない
3. `static/js/livereload.js` が切断を検出し、繋ぎ直せるようになった時点で
   `location.reload()`

**base.html は切らなかった。** live reload 単体には要らず、テンプレート 2 本の
共通化はそれ自体が別の変更になるため。`<script>` の 1 行は 2 箇所に書いてある
（片方だけ直して食い違う余地が残っている点は計画時の指摘のまま）。

テスト 5 本追加。`--debug` のとき `<script>` が両ページに出て WebSocket が
繋がること、既定では出ずエンドポイントも 404 になること。

実際に動かして、テンプレートと CSS のどちらを直しても
ブラウザが自動で更新されることを確認済み。

---

**これは記録で、現行仕様ではない**（仕様は `CLAUDE.md` と `docs/`）。
一覧は [TODO.md](../../TODO.md) にある。
