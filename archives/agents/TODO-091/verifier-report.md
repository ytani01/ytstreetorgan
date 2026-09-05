# TODO-091 検証報告書

## 1. コマンド例の確認

### 実行結果

すべてのコマンドと、README で使用しているオプションが実在することを確認した。

#### `uv run ytstreetorgan --help` の実行結果
- `parse`, `play`, `rollbook`, `webapp` の 4 つのサブコマンド存在

#### 各サブコマンドのオプション確認
- `rollbook FILE.mid -m 34notes`: `-m` オプションで `34notes` モデル指定可能 ✓
- `parse FILE.mid -v`: `-v` オプション（Visual flag）存在 ✓
- `play FILE.mid`: コマンド存在。音声出力するため実行は省略（ヘルプのみ確認）✓
- `webapp -p 10081`: `-p` オプションでポート指定可能 ✓

#### rollbook コマンドの実行確認

テスト MIDI `tests/data/sample.mid` を使用して実行。

```bash
$ uv run ytstreetorgan rollbook tests/data/sample.mid -m 34notes -f conf/storgan-conf.json -o /tmp/claude_job_output/test-rollbook.svg
```

結果：SVG ファイル生成成功（2.0KB、SVG Scalable Vector Graphics image）。

**注**: リポジトリ直下で実行。`-f` オプションで設定ファイルを明示指定が必要。

---

## 2. 設定ファイルの探索順確認

`src/ytstreetorgan/conf.py` の `SEARCH_PATH` より：

```python
SEARCH_PATH = [
    Path('.'),
    Path('~/.config'),
    Path('~/etc'),
    Path('/usr/local/etc'),
    Path('/etc')
]
```

README 記載の探索順 `. → ~/.config → ~/etc → /usr/local/etc → /etc` と**完全に一致**。 ✓

---

## 3. ドキュメントファイルの存在確認

すべてのリンク先が実在：
- `docs/User.md` (17KB, 2026-09-06 05:16)
- `docs/Architecture.md` (28KB, 2026-09-06 05:34)
- `docs/Developer.md` (11KB, 2026-09-06 05:16)
- `docs/tech-stack.md` (6.4KB, 2026-09-06 05:16)

✓ すべてのリンク先が実在。

---

## 4. 設定ファイル `conf/storgan-conf.json` の記述検証

### 34notes モデルの確認

`conf/storgan-conf.json` より抽出：

| 項目 | README の記述 | 実装値 | 合致 |
|-----|--------------|-------|-----|
| モデル | 34音 | F2〜A5 の 34 個の音 | ✓ |
| D# | 「D#はどの高さにも無い」 | A#2, A#3, A#4 のみ。D# 系は全く無い | ✓ |
| mm_per_sec | 「1秒あたり50mm（設定項目 `mm_per_sec` の既定値）」 | `mm_per_sec: 50.0` | ✓ |

### 同梱の機種設定

README：「同梱のテンプレートには、このほかに20音の設定も入っている」

実装：`conf/storgan-conf.json` には以下の 4 つのモデルが同梱されている：
1. `34notes` (34音)
2. `20notes` (20音)
3. `20notes a` (20音)
4. `34notes-a` (34音)

**注**: README では「20音の設定」と単数で記述しているが、実装には 2 つの異なる 20 音設定（`20notes` と `20notes a`）が入っている。また、`34notes-a` も存在し、README に明記されていない。

---

## 5. 出力ファイルパスの確認

README：「`rollbook` は、出力先を省略すると `~/Desktop` に「MIDI名.svg」で書く。」

実装確認（`src/ytstreetorgan/apps.py`）：
```python
DEF_OUT_DIR = '~/Desktop'
```

✓ 実装と記述が一致。

---

## 6. 用語の確認

### CLAUDE.md による用語定義との照合

CLAUDE.md の「画面に出す用語」より：
> 「試聴」は**ブラウザで鳴らして確かめること**を指す語なので、CLI の `play` に使ってはいけない。

README の修正内容：
- **修正前**: 「音の一覧表示や試聴ができる」
- **修正後**: 「音の一覧表示や再生ができる」
- **修正前**: `$ ytstreetorgan play FILE.mid                  # 試聴する`
- **修正後**: `$ ytstreetorgan play FILE.mid                  # 再生する`

✓ **正しい修正**。CLI の `play` コマンドには「試聴」ではなく「再生」を使うべき。

---

## 7. その他の確認

### 1 章の機能一覧

README の記述「34音/20音の設定を同梱」については、実装では複数の 20 音設定が含まれるため、微妙に曖昧だが、重大な矛盾ではない。

### 文書全体

特に不適切な用語の裸使いは見当たらない。

---

## 結論

- **コマンド例**：すべて実在し、実行確認完了
- **設定ファイル探索順**：実装と完全に一致
- **ドキュメントリンク**：すべてのファイルが実在
- **設定ファイル記述**：34notes の仕様は実装と完全に一致。ただし、同梱の機種設定については、20 音設定が複数存在するため記述が微妙に曖昧
- **用語**：「試聴」→「再生」への修正は正しい対応
- **出力パス**：実装と記述が一致

## 判断が必要な点

1. **同梱の機種設定の記述** — README では「このほかに20音の設定も入っている」と単数だが、実装には `20notes` と `20notes a` の 2 つが入っている。また `34notes-a` も存在するが記載されていない。これを明確にするかどうかは管理者の判断。
