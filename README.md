# Street Organ Roll Book Maker

【未完成】

MIDIデータを解析して、手回しオルガン用のロール・ブックを自動作成します。


## 1. 機能

* **ロール・ブック生成** — MIDIファイルから、穴あけ用のSVGを出力する。
  長さの単位はmmで、そのまま原寸で印刷・カットできる。
* **Webインターフェース** — ブラウザからMIDIファイルをアップロードし、
  生成結果をプレビューしてSVGをダウンロードする。
* **オルガン設定の編集** — トラック数や寸法の異なる機種を「モデル」として登録し、
  ブラウザ上で編集できる。34音/20音の設定を同梱。
* **履歴** — アップロードしたMIDIと生成したSVGを一覧し、
  作り直し・再表示・ダウンロード・削除ができる。
* **MIDIの解析・再生** — ロール・ブックにする前に、
  音の一覧表示や試聴ができる。

オルガンの音階に無い音は、捨てずに破線で描画される。
どの音が鳴らないかを目視で確認してから、MIDI側を調整できる。

穴が長くなりすぎる場合は、自動的に分割してブリッジ（紙のつなぎ)を残す。
ロール・ブックが切れてしまうのを防ぐため。


## 2. 準備

[uv](https://docs.astral.sh/uv/) で管理している。

```bash
$ git clone https://github.com/ytani01/ytstreetorgan.git
$ cd ytstreetorgan
$ uv sync
$ uv tool install .        # ytstreetorgan コマンドを使えるようにする
```

`uv tool install` を使わず、`uv run ytstreetorgan ...` と打っても同じことが
できる（そのときはリポジトリのディレクトリで実行する）。

**コードを更新したら入れ直すこと。** `git pull` しただけでは、
インストール済みのコマンドは古いままになる。

```bash
$ uv tool install . --reinstall
```

### 設定ファイルを置く

**オルガンの機種を定義した `storgan-conf.json` が要る。**
これが無いと、どのコマンドも「見つかりません」と言って終わる。

同梱のテンプレートを、次のどれか1か所へコピーする。

```bash
$ mkdir -p ~/.config && cp conf/storgan-conf.json ~/.config/
```

探す順番は `.` → `~/.config` → `~/etc` → `/usr/local/etc` → `/etc`。
最初に見つかったものを使う。中身はブラウザの「機種設定」から編集できる。


## 3. 使い方

コマンドラインとWebインターフェースの2通り。

```bash
$ ytstreetorgan --help
$ ytstreetorgan SUB_COMMAND --help

$ ytstreetorgan rollbook FILE.mid -m 34notes   # SVGを作る
$ ytstreetorgan parse FILE.mid -v              # 解析結果を見る
$ ytstreetorgan play FILE.mid                  # 試聴する
```

`rollbook` は、出力先を省略すると `~/Desktop` に「MIDI名.svg」で書く。

### Webインターフェース

**リポジトリのディレクトリで**起動する。テンプレートや、アップロードした
ファイルの置き場（`webroot/`）をそこから読み書きするため。

```bash
$ cd ytstreetorgan
$ ytstreetorgan webapp -p 10081
```

起動したら <http://localhost:10081/storgan2/> を開く。

開発者向けの情報（テスト・lint・依存）は `docs/` にある。


## A. 手回しオルガン用ロール・ブック

### A.1 基本

* 右から左
* 34音、低音部で、一部半音がない
* D#がない
* 1秒 = 約5cm


## B. Reference

* [てまわしオルガン キノ(紀あさ)](http://www.temawashi.org/)
