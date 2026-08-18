# TODO-102. アップロード画面での保存と削除の案内を書く

## きっかけ

アップロードした MIDI と生成した SVG は `webroot/midi/` と `webroot/svg/` に
残るが、画面のどこにも書いていなかった。削除は履歴画面からできるものの、
そこへ行けると分かる手掛かりが無かった。

## やったこと

`webroot/templates/storgan.html` のファイル選択の節（`<article>` の外、
`drop__status` の下）に 1 文足した。

> アップロードした MIDI と生成した SVG はサーバーに残ります。履歴から削除できます。

「履歴」は `{{urlprefix}}/history` へのリンク（`base.html` の nav と同じ
書き方）。`field__hint` と同じ小さい字にして、画面の高さは増やしていない。

Playwright でスクリーンショットを撮って見た目を確認した（フォームの下、
フッターの直前に 1 行で収まっている）。

## テスト

新規のテストは足さなかった。機種選択の下にある同種の静的な案内文
（`field__hint`）にもテストが無く、`tests/browser/test_rollbook_page.py` は
ボタン操作やクラスの変化を伴うものだけを見ている。今回の 1 文も同じ性質の
静的テキストなので、既存の方針に合わせた。

`pytest` / `pytest -m browser` / `ruff` / `mypy` はすべて通った。
