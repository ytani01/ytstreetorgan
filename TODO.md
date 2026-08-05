# TODO

作成: 2026-08-02（コミット `82aaa65` 時点）

**残っているのは 1 件（TODO-042）。** これまでに 42 件を決着させた。

新しく足すときは、この上に節を作る（完了したら「完了済み」へ移す）。
**番号は `TODO-044` から。** かつては A・B・C … の 1 文字だったが、
X まで来て Z が近かったので通し番号にした。**旧番号は各ファイルの
冒頭に残してある**（コミットメッセージはそちらの記号で書いてある）。

**やらないと決めたものもある。** 目次で（対応しない）と付いたもののほか、
TODO-029 のホイール拡縮、TODO-031 の設定キャッシュなど、項目の中の
一部だけ見送ったものもある。蒸し返す前に記録を読むこと。

---

## TODO-042. 移調候補ごとに、移調した MIDI をダウンロードできるようにする

- [ ] Web の移調候補の表に、各行の移調量で MIDI を作ってダウンロードする
      ボタンを足す

いまの候補の表は「試しに作り直して見比べる」ためのもの（TODO-039〜041）で、
作り直すのはロールブックの SVG だけ。**MIDI そのものを、選んだ調で
手元に持ち帰れるようにする。** 他の曲と合わせて演奏する、別の道具に
読み込ませる、といった使い方を想定。

### ロールブックの移調とは別物として作る

RollBook が使う音符（`_convert_for_model()` の結果）は、TODO-038 で
**同じ MIDI ノート番号どうしを統合**し、TODO-039 で**移調**し、機種の
音階で**絞り込んで**ある。ロールブックの穴を決めるための、いわば
「編曲された」音符列で、ダウンロードする MIDI の元にするには向かない
（統合で音が消える、機種の音階に無い音が落ちる）。

**ダウンロードする MIDI は、アップロードされた元の MIDI ファイルを
そのまま移調するだけにする。** テンポ・チャンネル・トラック構成・
音階に無い音も含めて、全部そのまま残す。統合も絞り込みもしない。
「ロールブックの穴になる音」と「持ち帰る MIDI の音」は別の関心事。

### 実装方針 — バイト列を直接いじる。`NoteInfo` は経由しない

検討した 2 案:

| 案 | 判定 |
|---|---|
| 元の MIDI ファイルを `mido` で読み、`note_on`/`note_off` の `note` を
  そのままずらして書き出す | ◎ 採用 |
| `Parser.parse()` の `NoteInfo` から MIDI を組み立て直す | ✗ |

`NoteInfo` は `Parser.parse()` が絶対時刻（秒）に変換したあとの形で、
**テンポ変化・トラック分割・もともとの tick 単位を持っていない**。
そこから作り直すと、複数テンポの曲でズレるか、単一テンポで妥協することに
なる。**バイト列（`mido.MidiFile`）を直接いじれば、note 以外は無変更**
で済み、迷う余地が無い。

実際に確認した手順（`holy.mid` で動作済み）:

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

音域からはみ出す音は 0〜127 に丸める（MIDI の仕様上の制約。丸めた結果
潰れて重なっても、ダウンロードする MIDI としては許容する）。

### 保存しない。リクエストごとにその場で作る

**`webroot/midi/` には置かない。** 表には最大 7 個の候補が並ぶが、
実際にダウンロードされるのはそのうち多くて 1 つか 2 つ。生成しても
まず開かれない残り 5 個ぶんまで書き出すと、`webroot/midi/` を無駄に
太らせる（TODO-019 で「増え続けるのは対応しない」と決めたが、それは
利用者が上げた MIDI の話で、こちらは輪をかけて増やす理由が無い）。

ダウンロードのリクエストが来たときだけ、その場でメモリ上に組み立てて
返す。ディスクに残さない。

### エンドポイント

**既存の `/download/midi/<name>` とは別にする。** あちらは
`webroot/midi/` に実在するファイルをそのまま返すだけの単純な作り
（`Download` ハンドラ）で、`resolve_in()` が「置き場の中にあること」を
確かめる前提になっている。移調は「元のファイル名 ＋ 移調量」から**その場で
作る**別物なので、`Download` に混ぜずに新しいハンドラにする。

`/download/midi-transpose/<name>?t=<半音数>` のような形にし、
`<name>` は既存どおり `resolve_in()` で `webroot/midi/` の中にあることを
確かめる（外部から来る名前を扱う以上、ここは他のハンドラと同じ扱いにする）。
`t` は整数でなければ 400 で断る。

ダウンロードのファイル名は `content_disposition()`（既存）を使い、
`<元の名前>.t<符号付き半音数>.mid` のように移調量が分かる名前にする
（同じ曲を複数の調でダウンロードしても、あとで区別できるように）。

### 表に出す行

移調しない（`transpose == 0`）行も含めて、**表に出ている行すべてに**
ボタンを出す。「元のキーのまま MIDI だけ欲しい」場合もありうるため、
±0 の行を特別扱いして隠さない。

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
