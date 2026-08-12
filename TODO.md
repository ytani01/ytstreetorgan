# = TODO

更新: 2026-08-12（TODO-065 を決着。取り込みを TODO-083 に立てた）

- 新しく足すときは、 **完了済み** の上に節を作る（完了したら「完了済み」へ移す）。**番号は `TODO-084` から。**
- **やらないと決めたものもある。** 目次で（対応しない）と付いたもののほか、TODO-029 のホイール拡縮、TODO-031 の設定キャッシュなど、項目の中の一部だけ見送ったものもある。蒸し返す前に記録を読むこと。

## == 着手前 / 検討中

### **TODO-083** (優先度:中) `ytmidilib` 0.3.0 を取り込み、試聴の一時ファイルを無くす

- [ ] `uv sync --upgrade-package ytmidilib` で `0.3.0` を取り込む
- [ ] `pyproject.toml` の `tag = "0.2.1"` を `"0.3.0"` にする
- [ ] `audition.py` の一時ディレクトリ経由を `io.BytesIO` に差し替える（46 行目のコメントも直す）
- [ ] `pytest` / `ruff` / `mypy` を通す

`ytmidilib` 0.3.0 で `write()` の第 1 引数が `str | os.PathLike[str] | BinaryIO` になった（TODO-065 の要求と回答。挙動と出力バイト列は `0.2.1` から変わらない）。`playable_midi_bytes()` が「一時ディレクトリを作って書いて読み戻して消す」4 手でやっていたものが、`io.BytesIO` 1 つで済む。**試聴の MIDI は保存しない**という決めごと（TODO-063）どおりの形になる。

呼ぶ側とテストは無変更で通るはず（`playable_midi_bytes()` の戻り値は変わらない）。

前例は TODO-047（`0.1.0`）・TODO-058（`0.2.1`）。

`0.1.0` のときに当たった、タグを打った直後に `uv` 側でバージョンが `0.0.4.dev20+g...` として入る現象（`uv` の git キャッシュ）に注意。取り込んだあと `uv pip show ytmidilib` などで版を確かめること。

---

## == 完了済み

1 項目 1 ファイル。`archives/todo/` にある（新しい順）。
**やらないと決めたものの理由もそこにある。** 蒸し返す前に読むこと。

- [**TODO-065.** `ytmidilib` に 3 通目の要求書を出す（`write()` を file-like に対応させる）](archives/todo/TODO-065.%20ytmidilib%20に%203%20通目の要求書を出す（write%28%29%20を%20file-like%20に対応させる）.md)
- [**TODO-082.** 起動時の残件表示が、項目ではなくチェックボックスを数えている](archives/todo/TODO-082.%20起動時の残件表示が、項目ではなくチェックボックスを数えている.md)
- [**TODO-081.** テストがリポジトリに無い MIDI に依存している](archives/todo/TODO-081.%20テストがリポジトリに無い%20MIDI%20に依存している.md)
- [**TODO-080.** `docs/routine_verification_subagents.md` を削除する](archives/todo/TODO-080.%20routine_verification_subagents.md%20を削除する.md)
- [**TODO-079.** ドキュメントとコードの食い違いを直す](archives/todo/TODO-079.%20ドキュメントとコードの食い違いを直す.md)
- [**TODO-078.** `HoleInfo` が設定項目を `.get(key, 0.0)` で読んでいる](archives/todo/TODO-078.%20HoleInfo%20が設定項目を%20.get%28key,%200.0%29%20で読んでいる.md)
- [**TODO-077.** 画面に出ないものが残っている（文書と食い違っている）](archives/todo/TODO-077.%20画面に出ないものが残っている（文書と食い違っている）.md)
- [**TODO-076.** `Handler1._render()` が候補の表示ロジックまで抱えている](archives/todo/TODO-076.%20Handler1._render%28%29%20が候補の表示ロジックまで抱えている.md)
- [**TODO-075.** `handler1.py` が 5 ハンドラ 718 行で、土台クラスも中にある](archives/todo/TODO-075.%20handler1.py%20が%205%20ハンドラ%20718%20行で、土台クラスも中にある.md)
- [**TODO-074.** `book`（ビューアに渡す諸元）が型で守られていない](archives/todo/TODO-074.%20book（ビューアに渡す諸元）が型で守られていない.md)
- [**TODO-073.** 機種設定の読み込みと検証が `RollBook` と `MidiApp` に二重](archives/todo/TODO-073.%20機種設定の読み込みと検証が%20RollBook%20と%20MidiApp%20に二重.md)
- [**TODO-072.** ダウンロード系 4 ハンドラの前処理が 4 回写してある](archives/todo/TODO-072.%20ダウンロード系%204%20ハンドラの前処理が%204%20回写してある.md)
- [**TODO-071.** `conf/` に、もう読めない旧形式の設定ファイルが 4 つ残っている](archives/todo/TODO-071.%20conf%20に、もう読めない旧形式の設定ファイルが%204%20つ残っている.md)
- [**TODO-070.** `Conf.load()` が壊れた設定を半端に読み込んだ状態にする](archives/todo/TODO-070.%20Conf.load%28%29%20が壊れた設定を半端に読み込んだ状態にする.md)
- [**TODO-069.** 機種設定で音名を選んだら昇順に並べ替える](archives/todo/TODO-069.%20機種設定で音名を選んだら昇順に並べ替える.md)
- [**TODO-068.** 移調候補一覧の「試聴」列を無くす](archives/todo/TODO-068.%20移調候補一覧の「試聴」列を無くす.md)
- [**TODO-067.** 設定項目 base_note を廃止する](archives/todo/TODO-067.%20設定項目%20base_note%20を廃止する.md)
- [**TODO-064.** 機種設定で、音名(国際標準)でドロップダウンメニューで入力するように変更](archives/todo/TODO-064.%20機種設定で、音名(国際標準)でドロップダウンメニューで入力するように変更.md)
- [**TODO-063.** ブラウザ上で、実機で鳴る音だけを試聴できるようにする](archives/todo/TODO-063.%20ブラウザ上で、実機で鳴る音だけを試聴できるようにする.md)
- [**TODO-066.** アーカイブのファイル名が壊れている件を直す](archives/todo/TODO-066.%20アーカイブのファイル名が壊れている件を直す.md)

- [**TODO-062.** 定型検証サブエージェントドキュメントに Gemini・Claude のモデル名および Effort 設定を追記する](archives/todo/TODO-062.%20定型検証サブエージェントドキュメントに%20Gemini・Claude%20のモデル名および%20Effort%20設定を追記する.md)（対応しない）
- [**TODO-061.** 定型検証サブエージェント委任ドキュメントの作成](archives/todo/TODO-061.%20定型検証サブエージェント委任ドキュメントの作成.md)
- [**TODO-060.** ドキュメント docs／multi_agent_token_savings.md へレビューに基づく補足・提案の組み込み](archives/todo/TODO-060.%20ドキュメント%20docs／multi_agent_token_savings.md%20へレビューに基づく補足・提案の組み込み.md)
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
