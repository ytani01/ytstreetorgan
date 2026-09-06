# TODO-107 検証報告（2 回目）

前段の Haiku verifier が拾えなかった 3 件（穴の y 座標の向き、URL 表の
prefix の不統一、依存の表からモジュール 3 つが抜けていた）を中心に、
`docs/Architecture.md` の記述を実装から裏取りした。検証コマンド
（pytest / ruff / mypy）は前段で通っており、今回は再実行していない
（指示どおり）。

## 前段で見つかっていた 3 件の再確認

### 1. 穴の y 座標の向き（4 章、`docs/Architecture.md` 219-222 行）

**現状は実装と一致している。誤りは見当たらなかった。**

- `HoleInfo.__init__`（`src/ytstreetorgan/rollbook.py` 257 行）:
  `self.y = self.scale * self.conf['pitch'] + self.conf['margin']`
- `note2scale()`（同 43-66 行）はトラックの並び順（`'notes'` の index）を
  返すので、トラック番号が大きいほど `scale` が大きい
- `pitch` / `margin` は設定上つねに正（`conf/storgan-conf.json` 5-6, 52-53,
  85-86, 118-119 行はいずれも正の値）なので、トラック番号が大きいほど
  `y` は大きくなる
- `svg_square()`（同 154 行）は `d="M {-x},{-y} ..."` で **`-y`** を書くので、
  `y` が大きいほど実際の SVG 座標は小さく（より負に）なる
- `viewBox="-width -height width height"`（`RollBook.svg()` 512-514 行）
  なので、画面の上端は `y=-height`（最も負）、下端は `y=0`
- 以上を合わせると、**トラック番号が大きいほど画面の上に描かれる**。
  Architecture.md 219-222 行の「トラック番号が大きいほど上」、および
  209-217 行の ASCII 図（トラック 2 が上端寄り、トラック 0 が下端寄り）は
  実装と一致する

### 2. URL 表の prefix の不統一（6 章、292-303 行）

**現状、表の中に prefix の書き方の不統一は見当たらなかった。**

- 292 行「URL の頭には `URL_PREFIX`（既定 `/storgan2`）が付く。表では
  省いた。」という前置きのあと、297〜302 行の全行が prefix 抜きの表記
  （`/download/...`、`/history`、`/config` など）で統一されている
- `docs/Architecture.md` 全体を `grep` しても、`/storgan2` を書いている
  箇所は 263・292 行（prefix そのものの定義・注記）だけで、他の URL 例は
  すべて prefix 抜きで揃っている
- `webapp.py`（`src/ytstreetorgan/webapp.py` 94-121 行）の実際のルート
  定義とも突き合わせたが、パターン自体（`/download/midi/(.*)` 優先、
  `/download/(.*)` が後、`config(?:/.*)?` など）は表の記載と食い違わない

**この項目については、今回の版では該当する誤りを見つけられなかった。**
前段の指摘の時点と文書の版が違う可能性がある（判断できない）。

### 3. 依存の表からモジュール 3 つが抜けていた（2 章）

**「表」ではなく、その直前の mermaid 図（66-80 行）にまだ残っている。**

- 84-101 行の**表**（「import する先」）は 16 行あり、`src/ytstreetorgan/`
  の実装ファイル（`__init__.py` と `mylog.py` を除く 16 個）と過不足なく
  一致している（`mylog.py` は 103 行で明示的に「表では省いた」と
  断っている）。**表そのものに欠けはない**
- ただし 66-80 行の**レイヤー分離の mermaid 図**（IN / APP / BASE / CORE /
  LOW の 5 箱）に列挙されているのは 14 個
  （`__main__.py` `webapp.py` / `apps.py` `handler1.py` `download.py`
  `history.py` `config_handler.py` / `base_handler.py` / `rollbook.py`
  `storage.py` `audition.py` / `transpose.py` `conf.py` `utils.py`）で、
  **`click_utils.py` / `livereload.py` / `mylog.py` の 3 つが図から
  抜けている**。表と違い、この図には「省いた」という断りが無い
- `click_utils.py`（依存なし）と `livereload.py`（`mylog` のみに依存、
  `webapp.py` から import される）は、実装上は LOW 層相当の場所に置ける
  はずだが図には出てこない。前段の指摘はこの mermaid 図を指していた
  可能性が高い（表と図のどちらを指していたかまでは分からない）

## その他、9 点の確認結果

### 3 章 設定ファイル

- 探索順 `.` → `~/.config` → `~/etc` → `/usr/local/etc` → `/etc`:
  `Conf.SEARCH_PATH`（`src/ytstreetorgan/conf.py` 267-273 行）と一致
- `ModelConf`（92-126 行、`total=False`）/ `ValidModelConf`（129-154 行、
  `total=True`、`memo` だけ `NotRequired`）の使い分け、
  `load_model_conf()`（500 行）が `validate_config()` を通す流れも一致
- `'notes'` は `list[str]`（125, 153 行）。`validate_config()`
  （229-249 行）は要素が `dict` なら「旧形式です」と弾き（235-239 行）、
  `str` でなければ弾く（241-244 行）。旧形式は読めない、という記述と一致
- `'base_note'` は `src/ytstreetorgan/` 全体で 162 行のコメント以外に
  出てこない。値として読まれることはなく黙って無視される、という記述と一致

### 4 章 SVG 座標系

- `svg_square()` のパス（154 行）: `M {-x:.2f},{-y:.2f} h {-w:.2f} v
  {-h:.2f} h {w:.2f} Z`。書式指定を除けば文書の記載と一致
- `viewBox`（512-515 行）、`x = start_sec * mm_per_sec`（256 行）、
  `y = scale * pitch + margin`（257 行）はいずれも一致
- ヘアライン指定（150-152 行）も一致

### 5 章 穴の扱い

- `note2scale()` が見つからないとき `-1` を返す（59-66 行）
- `_width` は `hi.scale >= 0` のときだけ伸ばす（`RollBook.load()`
  585-587 行）。`-1` の穴は伸ばさない、という記述と一致
- 分割数の式 `n = math.ceil((total_len + gap) / (gap + unit_len_max))`
  （`divide_length_by_max_len()` 196 行）は文書の式と一致

**新たに見つけた食い違い（1 章の図）**: 1 章の 2 つ目の mermaid 図
（46-58 行）は、「音階にあるか」の分岐で「ある→実線→分割する」
「ない→黒の破線→（分割を経ずに）SVG」という流れに読める。しかし実装は
`HoleInfo.__init__`（`rollbook.py` 233-268 行）内で `scale` の値に関わらず
必ず `self.segments = divide_length_by_max_len(...)` を計算しており、
`HoleInfo.svg()`（297-304 行）も `self.segments` を使って描画するのは
実線・破線どちらも同じ。実際、`off_scale_count`（458-465 行）は
`sum(len(hi.segments) for hi in self._holes if hi.scale < 0)` で、
**破線の穴も分割される前提**で数えている。つまり「長い穴の分割」は
実線・破線の両方に効くが、1 章の図は実線側にしか掛かっていないように
描かれている。5 章の本文（228-259 行）自体は実線・破線を区別せずに
書いてあるので、この食い違いは 1 章の図に限られる。

### 6 章 Web 層

- `webapp.py` のルート定義（94-121 行）と、6 章の表（294-303 行）・
  mermaid 図（281-290 行）を突き合わせ、ハンドラの対応・URL のパターン・
  クエリパラメータ名（`t` / `model`）とも一致
  （`AuditionMidi.get()` は `model` と `t` を読む、`download.py`
  208-219 行）
- 全ハンドラが `StorganBaseHandler` を継承していることも `grep` で確認
  （`config_handler.py` 12 行、`handler1.py` 31 行、`history.py` 18 行、
  `download.py` 31, 78, 122, 192 行）
- `stored_file()` / `transpose_arg()`（`base_handler.py` 103-150 行）の
  説明も実装と一致
- テンプレート側の `{{urlprefix}}` / `static_url()` の使い分けも
  `webroot/templates/base.html` 12-46 行、`storgan.html` / `history.html`
  / `config_editor.html` の各所と一致。3 テンプレートがいずれも
  `{% extends "base.html" %}` であることも確認（各ファイル 1 行目）

### 7 章 live reload

- `livereload.py`（1-77 行）と `webroot/static/js/livereload.js`
  （1-43 行）の両方を読み、シーケンス図（365-381 行）のとおり
  「サーバーは繋がるだけで何も送らない」「切断を合図に繋ぎ直しを試み、
  繋がったら `location.reload()`」という流れと一致することを確認

### 8 章 ビューア

- `viewer.js` の `--book-h` / `--z` を書き換える方式（46, 89-113 行）、
  `webroot/static/css/my.css` 268 行の
  `height: calc(var(--book-h, 126mm) * var(--z, .2))` と対応
- `scrollWidth` を使わない理由のコメント（`viewer.js` 85-87 行）も文書と一致
- `RollBook.svg()` が埋める属性（`rollbook.py` 484-490 行）:
  `model` / `mm-per-sec` / `notes` / `hole-notes` / `off-scale-notes` /
  `merged` / `transpose`（`META_PREFIX = 'data-storgan-'` と合わせて
  `data-storgan-model` などになる）。文書の一覧と一致
- `storage.BookInfo`（`storage.py` 75-114 行）のキー名
  （`notes` / `hole_notes` / `holes` / `off_scale_notes` / `off_scale`）と
  `RollBook` のプロパティ名（`note_count` / `hole_note_count` /
  `hole_count` / `off_scale_note_count` / `off_scale_count`、
  `rollbook.py` 399-465 行）の対応表（482-488 行）は、実際に
  `Handler1._book_of()`（`handler1.py` 311-315 行）が
  `'notes': rollbook.note_count` のように対応させている実装とも一致
  （前段 Haiku が誤って指摘した箇所）
- `'20notes'` / `'20notes a'` の数字は実際に実行して確認した:

  ```
  note_count 69 69
  hole_note_count 68 68
  hole_count coarse(bridge_threshold=50.0) 76
  hole_count fine(bridge_threshold=2.7) 677
  ```

  文書の「音符 69・実線 68 は変わらないのに、分割後は 76 と 677 になる」
  （491-494 行）と完全に一致

### 9 章 ロギング

- `getLogger(name, level)` / `setLevel(name, level)`（`mylog.py` 66, 79 行）
  が実在
- `_log = getLogger('storage')`（`storage.py` 21 行）は文書中のコード例
  （521 行）と文字どおり一致
- `from loguru import logger` は `mylog.py`（47 行）以外のどこにも無いこと
  を `grep -rn` で確認

## 変更されたファイルとの整合

`git status` で見えるのは次の 6 つ（`docs/Architecture.md` と
`archives/agents/TODO-090/` は untracked、他は modified）。

```
modified:   CLAUDE.md
modified:   README.md
modified:   docs/Developer.md
modified:   docs/User.md
modified:   docs/tech-stack.md
untracked:  archives/agents/TODO-090/
untracked:  docs/Architecture.md
```

今回の依頼は `docs/Architecture.md` の内容と実装の食い違いの確認に
限定されていたため、`CLAUDE.md` などの diff の中身（`docs/Architecture.md`
に移した節が過不足なく移されたか）は検証していない。**この点は
確かめていない。**

## まとめ

- 前段で挙がっていた 3 件のうち、**y 座標の向きと URL 表の prefix は
  現行の文書で見当たらなかった**（すでに直っているか、指摘時点の版が
  違う可能性がある。判断できない）
- **依存モジュールが抜けている件は、2 章の mermaid 図（66-80 行）に
  まだ残っている**。`click_utils.py` / `livereload.py` / `mylog.py` の
  3 つが図から欠けている。表（84-101 行）自体は 16 モジュール過不足なし
- **新たに見つけた食い違い**: 1 章 2 つ目の mermaid 図（46-58 行）が、
  長い穴の分割（`divide_length_by_max_len()`）を実線側だけの処理に
  見える形で描いている。実装は破線（音階に無い音）の穴も同じ
  `HoleInfo.segments` の仕組みで分割されており、`off_scale_count` の
  数え方（`rollbook.py` 463-465 行）もそれを前提にしている
- それ以外（3, 5, 6, 7, 8, 9 章）は、確認した範囲でコードと一致していた
