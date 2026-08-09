# = TODO

更新: 2026-08-09

- 新しく足すときは、 **完了済み** の上に節を作る（完了したら「完了済み」へ移す）。
- **やらないと決めたものもある。** 目次で（対応しない）と付いたもののほか、TODO-029 のホイール拡縮、TODO-031 の設定キャッシュなど、項目の中の一部だけ見送ったものもある。蒸し返す前に記録を読むこと。
- 新しく足すときは「完了済み」の上に節を作る。**番号は `TODO-062` から。**

## == 着手前 / 検討中

### **TODO-062** 定型検証サブエージェントドキュメントに Gemini/Claude のモデル名および Effort 設定を追記する

---

### **TODO-063** MIDIファイルをダウンロードせずに簡単に再生する機能について検討

**候補**: html-midi-player (**TBD**: 他にもっと良い方法がないか？)
- CDNを使うことも容認
- サンプルコード
```
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>MIDI Player</title>
  <!-- 必要なライブラリ（Tone.js, Magenta.js, html-midi-player等）を一括で読み込む -->
  <script src="https://cdn.jsdelivr.net/combine/npm/tone@14.7.58,npm/@magenta/music@1.23.1/es6/core.js,npm/focus-visible@5,npm/html-midi-player@1.5.0"></script>
</head>
<body>

  <!-- MIDIプレイヤー -->
  <!-- src属性に再生したいMIDIファイルのパスを指定します -->
  <midi-player
    src="foo.mid"
    sound-font
    visualizer="#myVisualizer">
  </midi-player>

  <!-- （任意）再生に合わせて音が降ってくるピアノロール UI -->
  <midi-visualizer type="piano-roll" id="myVisualizer"></midi-visualizer>

</body>
</html>
```
---

### **TODO-064** 機種設定で、音名(国際標準)でドロップダウンメニューで入力するように変更

- 参考として、NOTE番号も表示。
- 設定ファイルの形式も変更が必要。

---


## == 完了済み

1 項目 1 ファイル。`archives/todo/` にある（新しい順）。
**やらないと決めたものの理由もそこにある。** 蒸し返す前に読むこと。

- [**TODO-061.** 定型検証サブエージェント委任ドキュメントの作成](archives/todo/TODO-061.%20%E5%AE%9A%E5%9E%8B%E6%A4%9C%E8%A8%BC%E3%82%B5%E3%83%99%E3%82%A8%E3%83%BC%E3%82%B8%E3%82%A7%E3%83%B3%E3%83%88%E5%96%B6%E4%BB%BB%E3%83%89%E3%82%AD%E3%83%A5%E3%83%A1%E3%83%B3%E3%83%88%E3%81%AE%E4%BD%9C%E6%88%90.md)
- [**TODO-060.** ドキュメント docs/multi_agent_token_savings.md へレビューに基づく補足・提案の組み込み](archives/todo/TODO-060.%20%E3%83%89%E3%82%AD%E3%83%A5%E3%83%A1%E3%83%B3%E3%83%88%20docs/multi_agent_token_savings.md%20%E3%81%B8%E3%83%AC%E3%83%93%E3%83%A5%E3%83%BC%E3%81%AB%E5%9F%BA%E3%81%A5%E3%81%8F%E8%A3%9C%E8%B6%B3%E3%83%BB%E6%8F%90%E6%A1%88%E3%81%AE%E7%B5%84%E3%81%BF%E8%BE%BC%E3%81%BF.md)
- [**TODO-059.** webUI 表示変更に合わせたタイポ修正とテストの追従](archives/todo/TODO-059.%20webUI%20表示変更に合わせたタイポ修正とテストの追従.md)
- [**TODO-058.** `ytmidilib` 0.2.1 を取り込む](archives/todo/TODO-058.%20ytmidilib%200.2.1%20を取り込む.md)
- [**TODO-057.** TODO 運用の食い違いをグローバルの決まりに寄せる](archives/todo/TODO-057.%20TODO%20運用の食い違いをグローバルの決まりに寄せる.md)
- [**TODO-056.** トップの用語説明を削除し、候補の表を中央に置く](archives/todo/TODO-056.%20トップの用語説明を削除し、候補の表を中央に置く.md)
- [**TODO-055.** 移調まわりの画面を整理する（メニュー削除・説明の短縮・列揃え）](archives/todo/TODO-055.%20移調まわりの画面を整理する（メニュー削除・説明の短縮・列揃え）.md)
- [**TODO-054.** 移調の候補から「調」「オクターブ」の列を削除する](archives/todo/TODO-054.%20移調の候補から「調」「オクターブ」の列を削除する.md)
- [**TODO-053.** 「調」「移調」を素人にも分かるように画面で説明する](archives/todo/TODO-053.%20「調」「移調」を素人にも分かるように画面で説明する.md)
- [**TODO-052.** 移調の候補を、音符と音の長さの合計で並べる](archives/todo/TODO-052.%20移調の候補を、音符と音の長さの合計で並べる.md)
- [**TODO-051.** 移調の候補で、±0 を下回る数値に印を付ける](archives/todo/TODO-051.%20移調の候補で、±0%20を下回る数値に印を付ける.md)
- [**TODO-050.** 移調の候補をまとめて（ZIP で）持ち帰れるようにする](archives/todo/TODO-050.%20移調の候補をまとめて（ZIP%20で）持ち帰れるようにする.md)
- [**TODO-049.** 「高さ合わせ」「全体」で見ている位置を保つ](archives/todo/TODO-049.%20「高さ合わせ」「全体」で見ている位置を保つ.md)
- [**TODO-042.** 移調候補ごとに、移調した MIDI をダウンロードできるようにする](archives/todo/TODO-042.%20移調候補ごとに、移調した%20MIDI%20をダウンロードできるようにする.md)
- [**TODO-048.** `ytmidilib` に 2 通目の要求書を出す（ファイルの移調）](archives/todo/TODO-048.%20ytmidilib%20に%202%20通目の要求書を出す（ファイルの移調）.md)
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
