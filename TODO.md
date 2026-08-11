# = TODO

更新: 2026-08-12

- 新しく足すときは、 **完了済み** の上に節を作る（完了したら「完了済み」へ移す）。
- **やらないと決めたものもある。** 目次で（対応しない）と付いたもののほか、TODO-029 のホイール拡縮、TODO-031 の設定キャッシュなど、項目の中の一部だけ見送ったものもある。蒸し返す前に記録を読むこと。
- 新しく足すときは「完了済み」の上に節を作る。**番号は `TODO-067` から。**

## == 着手前 / 検討中

### **TODO-063** ブラウザ上で、実機で鳴る音だけを試聴できるようにする

#### 決まったこと

- **html-midi-player 1.6.0 を使う。CDN ではなくローカルに同梱する**（`docs/tech-stack.md` の「外部 CDN は 1 本も読まない」を守る）。同梱するのは Tone.js 14.7.58 / @magenta/music 1.23.1 の `es6/core.js` / html-midi-player 1.6.0 の 3 本、合計約 604KB
- **`sound-font` 属性は付けない。** 音源を外部（storage.googleapis.com）から取りに行かせない。音色は電子音になる
- **試聴では「この機種で実際に鳴る音」だけを鳴らす。** 移調・統合・音階の絞り込みを経たもの
- **試聴用に別エンドポイントを新設する。** `GET {prefix}/audition/midi/<name>?t=<半音数>&model=<機種名>`。既存の `DownloadTransposedMidi` は**変えない**（ダウンロードは持ち帰る素材、試聴は実機の再現で、目的が違う。同じ名前で中身の違う MIDI が 2 種類出回るのを避ける）
- **絞り込みは `RollBook` のパイプラインをそのまま通す。** 音階に入るかどうかは移調したあとに決まるので、順序を組み直さない（TODO-043 と同じ失敗を避ける）

#### やらないと決めたこと

- **ピアノロールの可視化は出さない。** 鳴らない音も同じ見た目で描くので、ロールブックの実線（穴）／破線（音階に無い音）の描き分けと食い違って読み違いを招く。同梱バイト数は変わらないので、後から `visualizer` 属性を足すだけで出せる
- **JS 側で音階を判定しない。** `note2scale()` を JS に複製することになり、同じ手順を 2 か所に持つ事故そのもの
- **ダウンロードの中身は変えない**（上記のとおり）
- **試聴した音の MIDI は持ち帰らせない。** 将来欲しくなったら `AuditionMidi` に `Content-Disposition` を足すのが答えで、`DownloadTransposedMidi` の中身を変えるのは答えではない

#### 実装の落とし穴（忘れると黙って壊れる）

- **全音符の `channel` を 0 に揃える。** Magenta は channel 9 をドラムとして合成ドラムで鳴らすため、揃えないと「穴が開く音がキックドラムの音で鳴る」
- **試聴ボタンに `data-transpose` を付けない。** `storgan.js` の委譲ハンドラが拾ってフォームを submit し、作り直しに行く。`data-audition` にする
- **試聴ボタンを `<a>` にしない。** 既存の `test_transpose_table_rows_offer_transposed_midi` が行内のリンク数を数えているので落ちる。`<button type="button">` にする
- **試聴の URL はテンプレートが `data-audition` に丸ごと書き、JS は写すだけ。** JS で URL を組み立てない
- **同梱 3 本の読み込み順は Tone → core → midi-player。** UMD なので順序が要る。`type="module"` にしない。`base.html` には入れず、結果画面でだけ読む
- **`merge_overlapping_notes()` が効くので、同じ高さの連打は 1 つの長い音に聞こえる。** これは実機の再現であって不具合ではない。直そうとしないこと

#### 作業のチェックリスト

**区切り A（サーバー側だけで完結。ここまでで `curl` と `ytstreetorgan play` で音を確かめられる）**

- [ ] `rollbook.py` に継ぎ目を入れる: `parse()` から `load()` を切り出し、`playable_note_info` プロパティ（`scale >= 0` の音符）を追加、`hole_note_count` をそれに寄せる
- [ ] `uv run pytest -q` で既存のロールブックのテストが全部緑であること（`parse()` の外形を変えていない確認）
- [ ] `audition.py` を新設し `playable_midi_bytes()` を実装（channel を 0 に揃える。`ytmidilib.write()` がパスしか受けないので当面は一時ファイル経由にし、その詳細をこの関数の中だけに閉じ込める）
- [ ] `tests/test_audition.py` を書く（音階外の音が入っていない／移調が効く／数が `hole_note_count` と一致／統合が効く／channel が全部 0／何も保存しない／未知の機種名は `ValueError`）
- [ ] `handler1.py` に `AuditionMidi` を追加、`webapp.py` にルートを 1 行追加（`Content-Type: audio/midi`、`Content-Disposition` は付けない、保存しない）
- [ ] HTTP テストを書く（200 と `MThd`／不正な `t` は 400／未知の機種は 400／`..` を含む名前は 400／無いファイルは 404）
- [ ] サーバーを起動して `curl` で取り、`ytstreetorgan play` で実際に聴いて確かめる

**区切り B（画面から聴けるようになる。ここまでで利用者に出せる）**

- [ ] `webroot/static/vendor/` に 3 本を curl で取得（サイズ 347,852 / 241,786 / 13,994 を照合）
- [ ] `webroot/static/vendor/LICENSES.md` を作る（3 本の全文・版・取得元・sha256・「手で編集しない」）
- [ ] `base.html` の `.icon-defs` に `<symbol id="i-play">` を追加
- [ ] `storgan.html` の `{% block scripts %}` に 3 本を `static_url()` でこの順に追加（結果画面でだけ読むよう条件で括る）
- [ ] 手動確認: DevTools で `customElements.get('midi-player')` が返ること（UI を足す前に読み込みだけ切り分ける）
- [ ] `storgan.html` に「試聴」列と、表の下に `<midi-player>` と注記を追加
- [ ] `webroot/static/js/midi_audition.js` を新規作成（クリック → `stop()` → `src` 差し替え → 選択行に印）
- [ ] `my.css` に `.midi-audition` の余白（Shadow DOM なので中は `::part()` でしか触れない）
- [ ] 手動確認: 行を替えて聴き比べ、±0 の行、`--debug` の live reload、暗いテーマ、**ネットを切った状態で全部動くこと**

**区切り C（固めて、書き残す）**

- [ ] ブラウザテストを追加（`src` が `/audition/` を指す／試聴ボタンで `src` が入れ替わり POST が飛ばない／MIDI 列は `/download/midi-transpose/` のまま／再生ボタンが enabled になる／400 以上のレスポンスが無い）
- [ ] `uv run pytest -q` / `uv run pytest -m browser -q` / `ruff check src tests` / `mypy src` を通す
- [ ] `docs/tech-stack.md`「フロントエンド」に追記（同梱 3 本と取得の curl、Tone は 14.x 固定、`sound-font` を付けない理由、`.map` は同梱しない）
- [ ] `webroot/CLAUDE.md` に「MIDI の試聴」節を新設（上記の落とし穴と、やらないと決めたことの理由）
- [ ] ルートの `CLAUDE.md` を更新（依存図に `audition.py` を追加／Web 層に `AuditionMidi` の項／用語の表に「試聴」／**live reload の注意点の記述を直す** — 現状は `base.html` があり `storgan.html`・`config_editor.html`・`history.html` の 3 つが継承しているので、203-205 行目の「共通の親テンプレートが無い」「両方に書いてある」「ページを増やすときは忘れずに」は誤り。「`base.html` に 1 か所あれば全ページに効く」に直す）
- [ ] 決着したら `archives/todo/` へ移す

---

### **TODO-064** 機種設定で、音名(国際標準)でドロップダウンメニューで入力するように変更

- 参考として、NOTE番号も表示。
- 設定ファイルの形式も変更が必要。

---

### **TODO-065** `ytmidilib` に 3 通目の要求書を出す（`write()` を file-like に対応させる）

`ytmidilib.write()` が `str | os.PathLike` しか受けず、file-like を受けない。そのため TODO-063 の試聴では一時ファイルに書いて読み戻している（「保存しない」という既存 3 ハンドラの原則に小さな穴が開いている）。

**同じパッケージの `transpose_file()` は既に file-like を受ける**ので、意味論を揃えるだけ。

段取り: 要求書を出す → 0.3.0 タグ → `uv sync --upgrade-package ytmidilib` → `pyproject.toml` の tag を上げる → `audition.py` の一時ファイルを `io.BytesIO` に差し替える（**呼ぶ側とテストは無変更で通るはず**）。

前例は TODO-045（1 通目）・TODO-048（2 通目）。

**要求書を出して 0.3.0 を取り込むところまでは、TODO-063 と独立に進められる。**
最後の `audition.py` の差し替えだけが TODO-063 の後になる（差し替える先の
ファイルが無いため）。逆に、TODO-063 はこの項目を待たずに進められる
（一時ファイル経由で動く）。

---

### **TODO-066** アーカイブのファイル名が壊れている 2 件を直す

- [ ] `TODO-061` のファイル名を、URL エンコードされた文字列から日本語に戻す
- [ ] `TODO-060` を、ディレクトリに分かれた状態から 1 ファイルに戻す
- [ ] `TODO.md` の目次のリンクを、それぞれ新しいファイル名に合わせる

`git ls-files archives/todo` で見える現状:

- **`TODO-061`** — 実ファイル名が
  `TODO-061.%20%E5%AE%9A%E5%9E%8B…%E4%BD%9C%E6%88%90.md` と、
  URL エンコードされた文字列そのものになっている。目次のリンクは
  それをさらにデコードした日本語を指しているので**リンクが切れている**
- **`TODO-060`** — タイトルに `docs/` が入っているため、
  `archives/todo/TODO-060. ドキュメント docs/` という**ディレクトリ**の下に
  `multi_agent_token_savings.md へ…組み込み.md` が置かれている。
  リンクはたまたま繋がっているが、「1 項目 1 ファイル」から外れている

どちらも `git mv` で直せる。ファイル名は日本語のまま、目次側だけ
スペースを `%20` にする（既存の項目と同じ書き方）。

**再発を防ぐ決まりも一緒に決める。** タイトルにスラッシュを入れない
（`docs/foo.md` のような参照は本文に書く）、ファイル名は URL エンコード
しない、の 2 点。TODO-062 では中黒に置き換えて避けた。

---

## == 完了済み

1 項目 1 ファイル。`archives/todo/` にある（新しい順）。
**やらないと決めたものの理由もそこにある。** 蒸し返す前に読むこと。

- [**TODO-062.** 定型検証サブエージェントドキュメントに Gemini・Claude のモデル名および Effort 設定を追記する](archives/todo/TODO-062.%20定型検証サブエージェントドキュメントに%20Gemini・Claude%20のモデル名および%20Effort%20設定を追記する.md)（対応しない）
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
