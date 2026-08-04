# TODO

作成: 2026-08-02（コミット `82aaa65` 時点）

**残っている項目は無い。** A〜X はすべて決着した。
「対応しない」で決着したのは N・O・S・U-1・W-1-4・W-4-23、
方針や文言だけ決めたのは P・Q。

新しく足すときは、この上に節を作る（完了したら「完了済み」へ移す）。

---

## 完了済み

記録は [`archives/20260805a-TODO-completed.md`](archives/20260805a-TODO-completed.md) に移した（新しい順）。
**やらないと決めたものの理由もそこにある。** 蒸し返す前に読むこと。

<!-- リンクの # のあとは「見出しの文字列」。Obsidian はこれで解決する
     （HTML の <a id="..."> は見ない）。見出しを直したらここも直すこと -->
- [**X.** 起動したときに URL を出す](archives/20260805a-TODO-completed.md#X.%20起動したときに%20URL%20を出す)
- [**W.** コード全体の見直し（リファクタリング）](archives/20260805a-TODO-completed.md#W.%20コード全体の見直し（リファクタリング）)
- [**V.** 履歴の行の操作を整理する](archives/20260805a-TODO-completed.md#V.%20履歴の行の操作を整理する)
- [**U.** ロールブックのビューアの操作性](archives/20260805a-TODO-completed.md#U.%20ロールブックのビューアの操作性)
- [**R.** HTTP テストが実物の webroot/ を触っていた](archives/20260805a-TODO-completed.md#R.%20HTTP%20テストが実物の%20webroot/%20を触っていた)
- [**Q.** 同名アップロードの選択肢（文言を直して決着）](archives/20260805a-TODO-completed.md#Q.%20同名アップロードの選択肢（文言を直して決着）)
- [**T-2.** 図から求まらない値を SVG に埋める](archives/20260805a-TODO-completed.md#T-2.%20図から求まらない値を%20SVG%20に埋める)
- [**T-1.** 保存済み SVG から穴の数を読む](archives/20260805a-TODO-completed.md#T-1.%20保存済み%20SVG%20から穴の数を読む)
- [**S.** 新しく足したテンプレートは live reload で拾われない（対応しない）](archives/20260805a-TODO-completed.md#S.%20新しく足したテンプレートは%20live%20reload%20で拾われない（対応しない）)
- [**P.** 確認ダイアログの出し方（方針を決めた。コードは変更なし）](archives/20260805a-TODO-completed.md#P.%20確認ダイアログの出し方（方針を決めた。コードは変更なし）)
- [**N.** 設定エディタが未知のキーを黙って落とす（対応しない）](archives/20260805a-TODO-completed.md#N.%20設定エディタが未知のキーを黙って落とす（対応しない）)
- [**M.** base テンプレートを切る](archives/20260805a-TODO-completed.md#M.%20base%20テンプレートを切る)
- [**L.** 日本語のファイル名がダウンロードできない](archives/20260805a-TODO-completed.md#L.%20日本語のファイル名がダウンロードできない)
- [**O.** webroot/midi/ と webroot/svg/ が溜まり続ける（対応しない）](archives/20260805a-TODO-completed.md#O.%20webroot/midi/%20と%20webroot/svg/%20が溜まり続ける（対応しない）)
- [**K.** 履歴の画面](archives/20260805a-TODO-completed.md#K.%20履歴の画面)
- [**I.** ブラウザ側の live reload（開発時のみ）](archives/20260805a-TODO-completed.md#I.%20ブラウザ側の%20live%20reload（開発時のみ）)
- [同名の MIDI を上げ直すと、古いほうが使われていた](archives/20260805a-TODO-completed.md#同名の%20MIDI%20を上げ直すと、古いほうが使われていた)
- [**J.** アップロードの失敗がユーザーに伝わらない](archives/20260805a-TODO-completed.md#J.%20アップロードの失敗がユーザーに伝わらない)
- [**F.** ブラウザテストを整備する](archives/20260805a-TODO-completed.md#F.%20ブラウザテストを整備する)
- [**A-2.** note name / note offset を notes に統合（A 完了）](archives/20260805a-TODO-completed.md#A-2.%20note%20name%20/%20note%20offset%20を%20notes%20に統合（A%20完了）)
- [**H.** 生成した SVG をブラウザ上でズーム・スクロールできるように](archives/20260805a-TODO-completed.md#H.%20生成した%20SVG%20をブラウザ上でズーム・スクロールできるように)
- [**G.** Web UI を Pico.css で作り直す](archives/20260805a-TODO-completed.md#G.%20Web%20UI%20を%20Pico.css%20で作り直す)
- [**B.** os.path → pathlib 移行](archives/20260805a-TODO-completed.md#B.%20os.path%20→%20pathlib%20移行)
- [webroot/svg/ の古い成果物を削除](archives/20260805a-TODO-completed.md#webroot/svg/%20の古い成果物を削除)
- [Claude Code のプラグインをこのプロジェクトで無効化](archives/20260805a-TODO-completed.md#Claude%20Code%20のプラグインをこのプロジェクトで無効化)
- [URL_PREFIX_HANDLER1 を削除](archives/20260805a-TODO-completed.md#URL_PREFIX_HANDLER1%20を削除)
- [**E.** URL prefix の扱いを整理](archives/20260805a-TODO-completed.md#E.%20URL%20prefix%20の扱いを整理)
- [archives/ を追跡対象に](archives/20260805a-TODO-completed.md#archives/%20を追跡対象に)
- [**C.** README.md を現状に合わせて書き直し](archives/20260805a-TODO-completed.md#C.%20README.md%20を現状に合わせて書き直し)
- [**A-3.** 数値変換の重複を解消](archives/20260805a-TODO-completed.md#A-3.%20数値変換の重複を解消)
- [**A-1.** bridge interval を設定項目から削除](archives/20260805a-TODO-completed.md#A-1.%20bridge%20interval%20を設定項目から削除)
- [82aaa65](archives/20260805a-TODO-completed.md#82aaa65)
