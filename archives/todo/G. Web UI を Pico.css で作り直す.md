# G. Web UI を Pico.css で作り直す

CDN 6 本（Bootstrap CSS/JS、Font Awesome、jQuery、popper、socket.io）を全廃した。
**ローカルで動かす道具なのに、ネットに繋がっていないとレイアウトが崩れていた。**
Pico.css v2.1.1 を `webroot/static/css/pico.min.css` に同梱し、アイコンは
インライン SVG、フォントはシステムフォントに統一した。

モック（3 画面、実データ入り、明暗両テーマ）:
<https://claude.ai/code/artifact/05378ca3-d845-4e9d-8b95-6e591105684e>

- 配色は生成される SVG から採った（外枠の青 `#0000FF` → 主要アクション `#2947c8`、
  穴の赤 `#FF0000` → 破壊的操作 `#c8392f`）。数値は等幅 + `tabular-nums`
- `config_editor.js` は jQuery をやめて素の DOM API に書き直した。文字列連結で
  HTML を組み立てていた箇所も `createElement` にしたので、値の中の引用符で
  壊れることがなくなった。モーダルは Bootstrap から `<dialog>` へ
- `storgan.js` を新設（機種を選ぶと寸法サマリを出す。生成してから
  「機種が違った」と気づくのを避けるため）。空だった `my.js` は削除

作業中に判明したこと（`CLAUDE.md` にも書いた）:

- **`:root` で Pico の変数を上書きしても効かない。** Pico は
  `:root:not([data-theme=dark])`（詳細度 (0,2,0)）で書いているので、あとから
  読み込んでも負ける。`:root:root` にして解決した
- **テンプレートは `autoreload=True` でも再読み込みされない**
  （`compiled_template_cache`）。直したらサーバーの再起動が要る
- 静的ファイルは `{{ static_url(...) }}` に変えた。`?v=<hash>` が付くので、
  CSS を直したのに古いキャッシュを掴む、という事故が起きない

テスト: `test_upload_midi_renders_svg_preview` の `page.locator('svg')` だけ
`#svgbox svg` に変えた（ロゴがインライン SVG になり、複数該当するため）。
その他はすべて要素 ID で操作しているのでそのまま通った。

---

**これは記録で、現行仕様ではない**（仕様は `CLAUDE.md` と `docs/`）。
一覧は [TODO.md](../../TODO.md) にある。
