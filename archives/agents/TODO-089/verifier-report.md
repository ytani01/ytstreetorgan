# TODO-089 確認担当（verifier）の報告

## 1. プロジェクトの検証（`docs/Developer.md`「一括で回す」の 4 つ）

すべて終了コード 0。

| コマンド | 結果 |
|---|---|
| `uv run ruff check src tests` | `All checks passed!`（exit 0） |
| `uv run mypy src` | `Success: no issues found in 18 source files`（exit 0） |
| `uv run basedpyright src` | `0 errors, 0 warnings, 0 notes`（exit 0） |
| `uv run pytest -m "" -q` | `352 passed in 45.26s`（exit 0。`-m ""` で既定の `-m 'not browser'` を上書きしているので、browser マーカーのテストも含めて 352 件） |

## 2. CLI コマンド例の実行（`docs/User.md` 4 章）

環境に設定ファイルが無いこと（`~/etc/storgan-conf.json` / `~/.config/storgan-conf.json`
とも無い）を確認したうえで、`-f conf/storgan-conf.json` を付けて `tests/data/sample.mid`
などで実行した。`-o` は一時ディレクトリを指定した。すべて exit 0。

- `ytstreetorgan --help` / `rollbook -h` / `parse -h` / `play -h` / `webapp -h` — いずれも正常表示
- `rollbook tests/data/sample.mid -m 34notes -t auto -f conf/storgan-conf.json -o ...`
  の出力が、`docs/User.md` 264〜274 行の移調候補の表と**完全に一致**した
  （`-t -1` を直接指定しても同じ結果になった。使ったのは `sample.mid`）
- `parse tests/data/sample.mid -v` の出力が、`docs/User.md` 300〜306 行の図と**完全に一致**
- `parse tests/data/sample.mid -m 34notes -f conf/storgan-conf.json` の
  1 行目（`apps.py` の `transpose_summary()`）が
  `[34notes] 移調しません → 鳴らせる音符 7 個（87.5%、音の長さ 87.5%）` で、
  `docs/User.md` 333 行目と**完全に一致**（`play` の該当行と同じ関数と指示にある
  とおり、こちらで代替確認した。`play` 自体は鳴らしていない）
- `~/etc/storgan-conf.json` / `~/.config/storgan-conf.json` はいずれの実行後も作られていない

## 3. `--help` とオプション表の突き合わせ

4 サブコマンドすべてで、オプション名・既定値・説明とも食い違いは無かった
（表の列の並び順は `--help` の出現順と違うところがあるが、内容は一致しており
問題ではない）。

`-v` の扱いについて、`docs/User.md` 243〜244 行の
「`-v` も普通はバージョンだが、`parse` だけは `-v` が図の表示」は実際の `--help` と一致。
`rollbook` / `play` / `webapp` は `-V, -v, --version`、`parse` だけ `-V, --version`
（`-v` が無い）だった。

## 4. 出力例の一致（重複を除き 2 で確認済み）

3 つとも実際の出力と一致した（2 に記載）。

## 5. 画面の記述と実装の突き合わせ（`docs/User.md` 3 章）

`webroot/templates/storgan.html` / `history.html` / `config_editor.html` と
`webroot/static/js/config_editor.js` を読み、指示にある項目を突き合わせた。
食い違いは見つからなかった。

- 同名ファイルのダイアログ 3 ボタン: `キャンセル` / `前回のファイルで変換`
  （`btn-same-reuse`）/ `置き換えて変換`（`btn-same-replace`）— 文言・働きとも
  `docs/User.md` 80〜84 行と一致（表の掲載順は違うが内容は同じ）
- 生成結果の諸元（演奏時間・全長・高さ・1 秒 = ◯ mm・移調・音符・統合・演奏・無音）
  — `storgan.html` のマークアップと `docs/User.md` 93〜105 行が完全一致
- ビューアの操作（拡縮 −/＋/スライダー、高さ合わせ/全体/原寸、先頭へ、下の帯）
  — 一致。`原寸` の title 属性「画面上で実際の紙と同じ大きさ（96dpi 換算）」も
  `docs/User.md` 124 行と一致
- 移調の候補の表の 5 列（移調・音符・音の長さ・移調後の音域・MIDI）と ▼ の意味、
  ZIP のリンク文言「すべての候補の MIDI をダウンロード（ZIP）」— 一致
- 履歴の 2 一覧（MIDI 名を押すと再生成／SVG 名を押すとそのまま表示）、
  保存アイコン・ゴミ箱・「すべて削除」— 一致
- 機種設定の上段ボタン（編集中・変更を保存・＋ 機種を追加・機種を削除）、
  基本寸法の 7 項目（ラベル・キー名・単位）、音階マッピングの並べ替え
  （`config_editor.js` の `sortNoteRows()` が MIDI ノート番号の昇順に並べ替え、
  トラック番号もその場で振り直す）、「＋ トラックを追加」「✕」— いずれも一致

## 6. `docs/images/make_shots.py` の実行

`uv run python docs/images/make_shots.py` は exit 0 で完走し、
`/home/ytani/work/ytstreetorgan/docs/images に書きました。` と出た。

- 実行前後で `~/etc/storgan-conf.json` / `~/.config/storgan-conf.json` は
  どちらも作られていない（存在しないまま）
- 5 枚のうち `web-history.png` と `web-result.png` の md5 が変わった
  （生成日時のタイムスタンプが撮影時刻に変わるため。`web-upload.png` /
  `web-transpose.png` / `web-config.png` は日時を表示しないので変化なし）。
  これは実行のたびに起きる想定内の差分で、内容としての不一致ではない
- 5 枚の画像を実際に開いて見た内容は、いずれも `docs/User.md` の説明・
  ラベルと一致していた（機種選択の下に出る寸法、生成結果の諸元とビューア、
  移調候補の表、履歴の 2 一覧、機種設定のフォーム）

## 7. リンクとパスの実在確認

- `docs/User.md` が参照する画像 5 枚（`web-upload.png` ほか）は
  すべて `docs/images/` に実在する
- 目次のアンカー（`#1-できること` 〜 `#5-困ったとき`）は、見出しの文字列から
  機械的に作られる形と一致する（数字・句点の扱いを含めて見出しと対応している）
- README・Developer.md から `docs/User.md` へのリンクは実在するファイルを指している

## 8. `git status` によるファイル範囲の確認

```
modified:   README.md
modified:   docs/Developer.md
untracked:  archives/agents/TODO-089/
untracked:  docs/User.md
untracked:  docs/images/
```

指示にある対象範囲と一致していた。範囲外のファイルへの変更は無い。

## 9. `docs/User.md` に関する既知の懸念（wording 担当の報告を確認）

`archives/agents/TODO-089/wording-report.md` に、`play` の `--min` / `--max` の
説明「音の長さの下限・上限 [秒]」が、`CLAUDE.md` の「画面に出す用語」の表にある
「音の長さ＝割合」という定義と別の意味で同じ語を使っている、という指摘が
記録されている。ソース側（`apps.py` の docstring）も同じ表記なので、
文書だけでは直せない旨が書かれている。**自分（verifier）でも `apps.py` の
該当 docstring を確認し、この記述の食い違いは事実**だが、直すかどうかは
判断が要る点として管理者に委ねる。

## 確かめられなかったこと

- `play` を実際に鳴らして音を聴く確認は、指示どおり行っていない
  （`parse -m` の `transpose_summary()` 出力で代替確認した）
- ブラウザでの実際のクリック操作（ダイアログのボタンを押す、拡縮のドラッグなど）は
  行っていない。テンプレートと JS のコードを読んで文書と突き合わせただけで、
  実際の見た目は `make_shots.py` が撮った画像で確認した
