# TODO-071. `conf/` に、もう読めない旧形式の設定ファイルが 4 つ残っている

## きっかけ

`validate_config()` が弾く形式の設定ファイルが、テンプレートと同じ
`conf/` に置いてあった。`CLAUDE.md` は `conf/storgan-conf.json` が
テンプレートだと書いているのに、隣に紛らわしいものが 4 つ並んでいて、
複製して `~/etc/storgan-conf.json` に置くと動かない。

## 決めごと

**`archives/conf/` へ移す**（消さない）。`archives/` は現行仕様ではない、
という既にある扱いに揃う。

## 中身を先に確かめた

「現行の `conf/storgan-conf.json` に無い情報が入っていないか」を
移す前に確かめた。**無かった。**

- `storgan-conf-new.json` と `storgan-new.conf-dist` は
  **バイト単位で同一**。4 機種（`34notes` / `20notes` / `20notes a` /
  `34notes-a`）の寸法も音名も現行と全部一致し、差は TODO-067 で廃止した
  `base_note` だけ
- `storgan.conf-20notes` / `-34notes` は `model` が `"ModelName"` の雛形。
  音名は現行の `20notes` / `34notes` と一致する。寸法の差は
  `bridge_threshold` が 50（現行 2.7）、`bridge_width` が 1（現行
  0.1 / 0.0）で、**現行のほうが新しい値**

## やったこと

- 4 つを `git mv` で `archives/conf/` へ移した
- `archives/conf/README.md` に、それぞれの形式と、上の確かめた結果を書いた
- `conf/` に残るのは `storgan-conf.json`（テンプレート）だけになった

## テスト

`pytest -q` 292 passed。`conf/` の 4 つは import も参照もされていない
（`grep` で確かめた。テストが複製するのは `conf/storgan-conf.json` だけ）。
