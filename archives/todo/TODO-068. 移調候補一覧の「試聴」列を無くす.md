# TODO-068. 移調候補一覧の「試聴」列を無くす

## きっかけ

TODO-063 で移調の候補ごとに「試聴」のボタンを置いたが、列が 1 つ増えるうえ、
**移調を選ぶ操作と試聴する操作が別々**になっていた。ロールブックを作り直せば
その移調量を聴きたいのが普通なので、選んだものがそのまま試聴の対象になれば
列は要らない。

## 決めごと

**プレーヤーに読み込むところまでで、自動再生はしない。**

「移調」は `#transpose-form` の POST でページごと作り直す作りなので、生成後の
画面で、いま選ばれている移調量の音を `<midi-player>` に読み込んでおく。
再生は利用者が押す。自動再生はブラウザが止めることがあり、環境によって
鳴ったり鳴らなかったりする。

## やったこと

- `storgan.html` — 表から「試聴」の `<th>` と `<td>` を削除（5 列になった）。
  `<midi-player>` の `src` に、**いま出しているブックの移調量**の試聴 URL を
  直接書く。注記も「押すと読み込みます」から「読み込んであります」に直し、
  移調量（`+11 半音の移調` / `移調しない場合`）を出すようにした
- **`midi_audition.js` を削除した。** ボタンが無くなり、URL はテンプレートが
  `src` に書くので、JS ですることが無くなった
- `my.css` — 行の印（`.is-audition`）と、注記の中のアイコンの指定を削除
- 「移調」列の見出しの説明を「押すと、その設定で作り直して試聴も切り替える」に

**URL をテンプレートに丸ごと書く決めごと（TODO-063）はそのまま。**
書く先が `data-audition` から `src` に変わっただけで、JS で組み立てないのは
同じ（prefix と引数の付け方が 2 か所に分かれるため）。

## テスト

`tests/browser/test_audition.py` を書き直した。

- `test_player_loads_the_current_transpose` — プレーヤーの `src` が、
  いま出しているブックの行（`.is-current`）の移調量と一致する。
  持ち帰る MIDI のリンクは別の経路のまま
- `test_transpose_table_has_no_audition_column` — `[data-audition]` が
  無く、見出しは 5 列
- `test_selecting_transpose_switches_the_audition` — 別の移調を選ぶと、
  作り直したページで試聴の対象も切り替わる
- `test_audition_player_enables_play_button_after_loading` — 読み込みが
  済むと再生ボタンが押せる（ボタンを押す手順が要らなくなった）

結果: `pytest -q` 291 passed、`pytest -m browser -q` 49 passed、
`ruff check src tests` と `mypy src` は問題なし。ブラウザでも、+11 を選んで
作り直したページのプレーヤーに +11 の音が入っていることを確かめた。
