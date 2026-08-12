# 旧形式の設定ファイル（TODO-071）

**どれも、もう読めない。** `validate_config()` が弾く（TODO-013 /
TODO-064 / TODO-067）。ここに置いてあるのは経緯を辿るためで、
**現行の設定ではない**。複製して `~/etc/storgan-conf.json` に置いても動かない。

現行のテンプレートは `conf/storgan-conf.json`。

| ファイル | 形式 |
|---|---|
| `storgan-conf-new.json` | `'book height'`（空白入りのキー）、`'1sec'`、`notes` が `{'name', 'offset'}` の辞書 |
| `storgan-new.conf-dist` | 同上（`storgan-conf-new.json` と**同一の中身**） |
| `storgan.conf-20notes` | `notes` が辞書、`base_note` あり。`model` は `"ModelName"` の雛形 |
| `storgan.conf-34notes` | 同上 |

## 中身は現行に引き継がれている

移す前に、現行の `conf/storgan-conf.json` に無い情報が入っていないかを
確かめた。**無かった。**

- `storgan-conf-new.json`（＝ `storgan-new.conf-dist`）の 4 機種は、
  寸法も音名も現行と全部一致する。差は `base_note` だけで、これは
  TODO-067 で廃止した項目
- `storgan.conf-20notes` / `-34notes` の音名は、現行の `20notes` /
  `34notes` と一致する。寸法の差は `bridge_threshold` が 50（現行 2.7）、
  `bridge_width` が 1（現行 0.1 / 0.0）で、**現行のほうが新しい値**
