# TODO

作成: 2026-08-02（コミット `82aaa65` 時点）

**残っているのは 2 件（TODO-048 → TODO-042）。**
これまでに 46 件を決着させた。

新しく足すときは、この上に節を作る（完了したら「完了済み」へ移す）。
**番号は `TODO-049` から。** かつては A・B・C … の 1 文字だったが、
X まで来て Z が近かったので通し番号にした。**旧番号は各ファイルの
冒頭に残してある**（コミットメッセージはそちらの記号で書いてある）。

**やらないと決めたものもある。** 目次で（対応しない）と付いたもののほか、
TODO-029 のホイール拡縮、TODO-031 の設定キャッシュなど、項目の中の
一部だけ見送ったものもある。蒸し返す前に記録を読むこと。

---

## TODO-048. `ytmidilib` に 2 通目の要求書を出す（ファイルの移調）

**［回答待ち］** TODO-042 の実装方針を変えるための要求。

- [x] 要求書を書く → [`docs/20260806c-ytmidilib-requests-2.md`](docs/20260806c-ytmidilib-requests-2.md)
- [ ] `ytmidilib` 側の回答・修正を待つ
- [ ] タグを上げて取り込み、TODO-042 に着手する

### なぜ

TODO-042 は当初「`mido` を直接使って元の MIDI のバイト列をいじる」方針
だった。**MIDI を受け取って MIDI を返す処理は `ytmidilib` の仕事**なので、
向こうに寄せる。こちらが `mido.MidiTrack` を組み立て始めると、MIDI の
低レベル処理が 2 リポジトリに散る。

`ytmidilib 0.1.0` の `transpose(note_info, n)` では**代用できない**
（実測）。`NoteInfo` は絶対秒・チャンネル・note・velocity しか持たないので、
`write()` で組み立て直すと音色（`program_change`）・音量・ピッチベンド・
トラック構成・テンポ変化が消える。**元のバイト列から `note` だけずらす
API が要る。**

### 要求の骨子

```python
transpose_file(src, dst, n, clip=False)   # src / dst とも path | file-like
transpose(note_info, n, clip=False)       # 既存にも同じ引数を足す
```

- **file-like を受ける**こと（TODO-042 はディスクに残さずメモリ上で返す）。
  `mido.MidiFile` を返す形にはしない。**`mido` を公開 API に出させない**
- **範囲外の扱いを既存の `transpose()` と揃える。** いまは `ValueError`
  （回答書 #8。「クリップは曲が変わったのに成功して返る」は妥当）。
  ファイル版だけ黙って丸めると、同じ「移調」で意味論が 2 つになる。
  `clip=True` を**呼び出し側が明示的に書く**なら、曲が変わることを承知で
  丸めたという判断が呼び出しに現れる

ほかに、打楽器チャンネル（ch 9）を移調するかどうかと、`write()` の
docstring に「何が失われるか」を書くことも要求した。

---

## TODO-042. 移調候補ごとに、移調した MIDI をダウンロードできるようにする

**［保留中］** TODO-048 の回答待ち。**下の「実装方針」は `mido` を直接
使う前提で書いてあり、`ytmidilib` に寄せると決めたので古い。**
要求が通ったら書き直すこと。

- [ ] Web の移調候補の表に、各行の移調量で MIDI を作ってダウンロードする
      ボタンを足す

いまの候補の表（TODO-039〜041）で作り直すのはロールブックの SVG だけ。
**MIDI そのものを、選んだ調で手元に持ち帰れるようにする**（他の曲と
合わせて演奏する、別の道具に読み込ませる、といった使い方）。

### 元の MIDI をそのまま移調する。ロールブックの音符は使わない

`RollBook` が使う音符（`_convert_for_model()` の結果）は、統合（TODO-038）
・移調（TODO-039）・機種の音階での絞り込みを経た「編曲された」列で、
**音が消えている**。持ち帰る MIDI の元には向かない。

アップロードされた元のファイルを移調するだけにし、テンポ・チャンネル・
トラック構成・音階に無い音も全部そのまま残す。

### 実装方針 — `mido` でバイト列を直接いじる。`NoteInfo` は経由しない

`NoteInfo` は絶対時刻（秒）に直したあとの形で、**テンポ変化・トラック分割
・tick 単位を持っていない**。そこから組み立て直すと複数テンポの曲でズレる。
`mido.MidiFile` を読んで `note` だけずらせば、**note 以外は無変更**で済む。

`holy.mid` で動作を確認した手順:

```python
mf = mido.MidiFile(src_path)
out = mido.MidiFile(type=mf.type, ticks_per_beat=mf.ticks_per_beat)
for track in mf.tracks:
    new_track = mido.MidiTrack()
    for msg in track:
        if msg.type in ('note_on', 'note_off'):
            msg = msg.copy(note=max(0, min(127, msg.note + semitones)))
        new_track.append(msg)
    out.tracks.append(new_track)
out.save(file=io.BytesIO())  # ファイルに書かずメモリ上でも作れる
```

はみ出す音は 0〜127 に丸める（潰れて重なっても許容する）。

### 保存しない。リクエストごとにメモリ上で作る

**`webroot/midi/` には置かない。** 候補は最大 7 行並ぶが、実際に
ダウンロードされるのは 1 つか 2 つ。残りまで書き出して置き場を太らせる
理由が無い
（TODO-019 で「増え続けるのは対応しない」と決めたのは利用者が上げた
MIDI の話）。

### エンドポイント

**既存の `/download/midi/<name>` とは別にする。** あちらは実在する
ファイルをそのまま返す作り（`Download` ハンドラ）で、こちらは
「名前 ＋ 移調量」からその場で作る別物。

`/download/midi-transpose/<name>?t=<半音数>` のような形にし、`<name>` は
既存どおり `resolve_in()` で `webroot/midi/` の中にあることを確かめる。
`t` が整数でなければ 400。ダウンロード名は `content_disposition()` で
`<元の名前>.t<符号付き半音数>.mid`（同じ曲を複数の調で保存しても
区別できるように）。

### 表に出す行

`transpose == 0` の行も含めて**全行に**ボタンを出す。「元のキーのまま
MIDI だけ欲しい」場合もある。

### やること

- [ ] 元の MIDI ファイルをその場で移調してバイト列を返す関数を足す
      （`mido` を使う。ディスクに書かない）
- [ ] `pyproject.toml` に `mido` を明示の依存として足す
      （いまは `ytmidilib` 経由の間接依存でしかない。直接 import するので
      明示する）
- [ ] 新しいハンドラ（`/download/midi-transpose/<name>?t=`）を足す。
      名前は `resolve_in()` で確かめる。`t` は整数以外なら 400
- [ ] `storgan.html` の候補の表に、行ごとのダウンロードボタンを足す
      （±0 の行も含む）
- [ ] テスト: 移調した MIDI の音が実際にずれていること（`mido` で読み直して
      確認）／テンポ・トラック数など note 以外が変わらないこと／
      音域からはみ出す音が 0〜127 に丸まること／`webroot/midi/` に
      ファイルが増えないこと／存在しない名前や不正な `t` を断ること

---

## 完了済み

1 項目 1 ファイル。`archives/todo/` にある（新しい順）。
**やらないと決めたものの理由もそこにある。** 蒸し返す前に読むこと。

- [**TODO-047.** `ytmidilib` 0.1.0 を取り込む](archives/todo/TODO-047.%20ytmidilib%200.1.0%20を取り込む.md)
- [**TODO-046.** `ytmidilib` をタグで固定する](archives/todo/TODO-046.%20ytmidilib%20をタグで固定する.md)
- [**TODO-045.** `ytmidilib` への要求書を出す](archives/todo/TODO-045.%20ytmidilib%20への要求書を出す.md)
- [**TODO-044.** `basedpyright` の 11 件を片付ける](archives/todo/TODO-044.%20basedpyright%20の%2011%20件を片付ける.md)
- [**TODO-043.** 移調まわりを整理する](archives/todo/TODO-043.%20移調まわりを整理する.md)
- [**TODO-041.** 移調の候補を絞る（改善しないものを外し、5 個以内に）](archives/todo/TODO-041.%20移調の候補を絞る（改善しないものを外し、5%20個以内に）.md)
- [**TODO-040.** play で stdout を差し替えるのをやめる](archives/todo/TODO-040.%20play%20で%20stdout%20を差し替えるのをやめる.md)
- [**TODO-039.** 機種に合わせてキーを上下させ、鳴らせる音符を増やす（移調）](archives/todo/TODO-039.%20機種に合わせてキーを上下させ、鳴らせる音符を増やす（移調）.md)
- [**TODO-038.** 同じ音が重なっている部分を 1 つの穴にまとめる](archives/todo/TODO-038.%20同じ音が重なっている部分を%201%20つの穴にまとめる.md)
- [**TODO-037.** 拡縮しても中央の位置が動かないようにする](archives/todo/TODO-037.%20拡縮しても中央の位置が動かないようにする.md)
- [**TODO-036.** ビューアの倍率の上限を 10 倍にする](archives/todo/TODO-036.%20ビューアの倍率の上限を%2010%20倍にする.md)
- [**TODO-035.** 穴を「くり抜いた」ように見せる](archives/todo/TODO-035.%20穴をくり抜いたように見せる.md)
- [**TODO-034.** 紙の色を古紙っぽくする](archives/todo/TODO-034.%20紙の色を古紙っぽくする.md)
- [**TODO-033.** ビューアで穴が見にくい](archives/todo/TODO-033.%20ビューアで穴が見にくい.md)
- [**TODO-032.** 起動したときに URL を出す](archives/todo/TODO-032.%20起動したときに%20URL%20を出す.md)（旧 X）
- [**TODO-031.** コード全体の見直し（リファクタリング）](archives/todo/TODO-031.%20コード全体の見直し（リファクタリング）.md)（旧 W）
- [**TODO-030.** 履歴の行の操作を整理する](archives/todo/TODO-030.%20履歴の行の操作を整理する.md)（旧 V）
- [**TODO-029.** ロールブックのビューアの操作性](archives/todo/TODO-029.%20ロールブックのビューアの操作性.md)（旧 U）
- [**TODO-028.** HTTP テストが実物の webroot を触っていた](archives/todo/TODO-028.%20HTTP%20テストが実物の%20webroot%20を触っていた.md)（旧 R）
- [**TODO-027.** 同名アップロードの選択肢（文言を直して決着）](archives/todo/TODO-027.%20同名アップロードの選択肢（文言を直して決着）.md)（旧 Q）
- [**TODO-026.** 図から求まらない値を SVG に埋める](archives/todo/TODO-026.%20図から求まらない値を%20SVG%20に埋める.md)（旧 T-2）
- [**TODO-025.** 保存済み SVG から穴の数を読む](archives/todo/TODO-025.%20保存済み%20SVG%20から穴の数を読む.md)（旧 T-1）
- [**TODO-024.** 新しく足したテンプレートは live reload で拾われない（対応しない）](archives/todo/TODO-024.%20新しく足したテンプレートは%20live%20reload%20で拾われない（対応しない）.md)（旧 S）
- [**TODO-023.** 確認ダイアログの出し方（方針を決めた。コードは変更なし）](archives/todo/TODO-023.%20確認ダイアログの出し方（方針を決めた。コードは変更なし）.md)（旧 P）
- [**TODO-022.** 設定エディタが未知のキーを黙って落とす（対応しない）](archives/todo/TODO-022.%20設定エディタが未知のキーを黙って落とす（対応しない）.md)（旧 N）
- [**TODO-021.** base テンプレートを切る](archives/todo/TODO-021.%20base%20テンプレートを切る.md)（旧 M）
- [**TODO-020.** 日本語のファイル名がダウンロードできない](archives/todo/TODO-020.%20日本語のファイル名がダウンロードできない.md)（旧 L）
- [**TODO-019.** webroot-midi と webroot-svg が溜まり続ける（対応しない）](archives/todo/TODO-019.%20webroot-midi%20と%20webroot-svg%20が溜まり続ける（対応しない）.md)（旧 O）
- [**TODO-018.** 履歴の画面](archives/todo/TODO-018.%20履歴の画面.md)（旧 K）
- [**TODO-017.** ブラウザ側の live reload（開発時のみ）](archives/todo/TODO-017.%20ブラウザ側の%20live%20reload（開発時のみ）.md)（旧 I）
- [**TODO-016.** 同名の MIDI を上げ直すと、古いほうが使われていた](archives/todo/TODO-016.%20同名の%20MIDI%20を上げ直すと、古いほうが使われていた.md)
- [**TODO-015.** アップロードの失敗がユーザーに伝わらない](archives/todo/TODO-015.%20アップロードの失敗がユーザーに伝わらない.md)（旧 J）
- [**TODO-014.** ブラウザテストを整備する](archives/todo/TODO-014.%20ブラウザテストを整備する.md)（旧 F）
- [**TODO-013.** note name - note offset を notes に統合（A 完了）](archives/todo/TODO-013.%20note%20name%20-%20note%20offset%20を%20notes%20に統合（A%20完了）.md)（旧 A-2）
- [**TODO-012.** 生成した SVG をブラウザ上でズーム・スクロールできるように](archives/todo/TODO-012.%20生成した%20SVG%20をブラウザ上でズーム・スクロールできるように.md)（旧 H）
- [**TODO-011.** Web UI を Pico.css で作り直す](archives/todo/TODO-011.%20Web%20UI%20を%20Pico.css%20で作り直す.md)（旧 G）
- [**TODO-010.** os.path → pathlib 移行](archives/todo/TODO-010.%20os.path%20→%20pathlib%20移行.md)（旧 B）
- [**TODO-009.** webroot-svg の古い成果物を削除](archives/todo/TODO-009.%20webroot-svg%20の古い成果物を削除.md)
- [**TODO-008.** Claude Code のプラグインをこのプロジェクトで無効化](archives/todo/TODO-008.%20Claude%20Code%20のプラグインをこのプロジェクトで無効化.md)
- [**TODO-007.** URL_PREFIX_HANDLER1 を削除](archives/todo/TODO-007.%20URL_PREFIX_HANDLER1%20を削除.md)
- [**TODO-006.** URL prefix の扱いを整理](archives/todo/TODO-006.%20URL%20prefix%20の扱いを整理.md)（旧 E）
- [**TODO-005.** archives を追跡対象に](archives/todo/TODO-005.%20archives%20を追跡対象に.md)
- [**TODO-004.** README.md を現状に合わせて書き直し](archives/todo/TODO-004.%20README.md%20を現状に合わせて書き直し.md)（旧 C）
- [**TODO-003.** 数値変換の重複を解消](archives/todo/TODO-003.%20数値変換の重複を解消.md)（旧 A-3）
- [**TODO-002.** bridge interval を設定項目から削除](archives/todo/TODO-002.%20bridge%20interval%20を設定項目から削除.md)（旧 A-1）
- [**TODO-001.** 82aaa65](archives/todo/TODO-001.%2082aaa65.md)
