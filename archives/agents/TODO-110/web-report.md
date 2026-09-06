# TODO-110 web 担当報告

## やったこと

1. `uv run python docs/images/make_shots.py` を実行。無修正でそのまま動いた
   （chromium 済み）。スクリプト自体の修正は不要。
2. 旧画像 5 枚を `.../scratchpad/old-images/` に退避してから撮り直し、
   新旧を見比べた。
3. `docs/User.md` の 3.2 を、アップロード画面のリード下の案内 3 点
   （TODO-102/103）に合わせて追記した。3.1〜3.8 全体も実画面（テンプレート
   `webroot/templates/storgan.html` と、撮り直した各画像）と突き合わせたが、
   3.2 以外に食い違いは見つからなかった。

## 画像ごとの差分の有無と判断

- **web-upload.png** — 差し替えた。リードの下に、機種の音階に無い音の扱い・
  候補一覧の表示・履歴からの削除、の 3 点の案内が新しく入っていた
  （分岐前には無かった）。
- **web-result.png / web-transpose.png / web-history.png / web-config.png** —
  見比べたところ、生成日時などのタイムスタンプ以外に見た目の差は無かった。
  撮り直しで生じる無意味な差分を残さないため、`git checkout --` で旧版に
  戻した。

## `docs/User.md` の変更点

3.2「ロールブックを作る」の画像の下に、画面の `<ul class="field__hint
field__hint--list">` にある 3 項目を箇条書きで追加した（文言は画面の表現に
揃え、用語表の「音階」「移調」「履歴」をそのまま使用）。手順 1〜3 と、
移調・同名ファイルまわりの説明は実画面と食い違いが無かったのでそのまま。

## 検証結果

- `uv run pytest -q` — 303 passed
- `uv run ruff check src tests` — 問題なし（`make_shots.py` は無修正だが
  念のため `uv run ruff check docs/images/make_shots.py` も実行し、問題なし）
- `uv run mypy src` — 問題なし
- ブラウザでの確認は `make_shots.py` が撮った実画面のスクリーンショット
  （Playwright 経由）で行った。コンソールエラーの確認は同スクリプトの
  実行ログで確認済み（エラー無し）。

## 残る懸念

特になし。
