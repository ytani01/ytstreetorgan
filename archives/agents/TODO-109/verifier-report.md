# TODO-109 検証報告

## 1. 検証実行結果

すべて成功（終了コード 0）。

```
uv run pytest -q
→ 303 passed, 49 deselected in 1.85s

uv run ruff check src tests
→ All checks passed!

uv run mypy src
→ Success: no issues found in 18 source files
```

## 2. `apps.py` の `sec_min` / `sec_max` 検証

### 変更内容
- 旧：「音の長さの下限・上限 [秒]」
- 新：「1 音を鳴らす時間の下限・上限 [秒]」

### 実装との整合性
✓ 正確です。実装では `Player.play()` に渡され、個別の音を鳴らす時間を制御するパラメータです。

### `docs/User.md` との確認
✓ `docs/User.md` 326 行の説明と完全に一致：
```
| `--min` / `--max` | `0.02` / `1.2` | 1 音を鳴らす時間の下限・上限 [秒] |
```

### 用語の確認
✓ CLAUDE.md の「画面に出す用語」との矛盾なし。
- CLAUDE.md の「音の長さ」= 移調の候補で使う割合（`transpose.py` で使用）
- `apps.py` の新しい説明 = 個別の音を鳴らす時間（Player の制御）

用語が別の概念なので矛盾していません。

## 3. `handler1.py` の `_show_stored_svg()` 検証

### 変更内容
旧：「諸元は SVG から読めるぶんだけ（`width` / `height`）。穴の数と `mm_per_sec` は SVG に無いので None のまま渡し、画面では `---` と出る。」

新：「諸元は `book_from_svg()` が読む。`width` / `height` と穴の数は図から数え、`mm_per_sec` のように図に現れない値は `<svg>` の属性から読む（TODO-026）。属性が無い古い SVG では None のままで、画面に `---` と出る。」

### `book_from_svg()` 実装確認

`src/ytstreetorgan/storage.py` の 210 行目の実装を確認しました。

**`width` / `height` の読み方**
- 実装：正規表現 `_SVG_SIZE_RE` で `<svg width="…mm" height="…mm">` を検索して読む
- `storage.py` の docstring も「図から読むもの」として列挙
- ✓ 実装と新しい説明は整合性がある

**穴の数（`holes` / `off_scale`）の読み方**
- 実装：`len(_HOLE_COLOR_RE.findall(svg))` で穴の要素を検索して数える
- ✓ 「図から数える」という説明が正確

**`mm_per_sec` の読み方**
- 実装：`_meta_float(svg, 'mm-per-sec')` で `<svg>` の属性から読む
- ✓ 「属性から読む」という説明が正確

### 属性が無いときの動作
✓ `_meta()` → `_meta_float()` で確認：
- 属性が無いまたは読めないとき、`None` が返される
- `_meta()` の実装：正規表現で属性を探し、無ければ `None` を返す

### 画面表示の確認
✓ `webroot/static/js/viewer.js` 30 行目で確認：
```javascript
const UNKNOWN = window.UNKNOWN || "---";
```
- 75 行目、245 行目で `UNKNOWN` が使用
- `book.mm_per_sec` が `None` のとき、`---` が表示される

## 4. 微妙な表現上の注意点

新しい `handler1.py` の docstring で「`width` / `height` と穴の数は図から数え」と書かれていますが、実装をみると正確には：
- `width` / `height`：「図（SVG 属性）から読む」（「数える」ではない）
- 穴の数：「図から数える」

ただし、これは細微な表現の違いで、意味としては「SVG から読める」という点で統一されており、実装と矛盾はしていません。`storage.py` のコメントでも `width` / `height` は「図から読むもの」と分類されているため、「図から」という表現は許容範囲と考えられます。

## 結論

- 検証（pytest / ruff / mypy）：すべてパス
- `apps.py` docstring：実装、`docs/User.md`、用語定義との整合性あり
- `handler1.py` docstring：実装と整合性あり、画面表示も確認完了
- 食い違いなし
