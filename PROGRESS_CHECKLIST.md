# 機種別設定編集機能 進捗管理チェックリスト

## 概況
- **進捗状況**: 100% (全機能実装・テスト完了)
- **計画書**: [MODEL_CONFIG_EDIT_PLAN.md](file:///home/ytani/work/ytstreetorgan/MODEL_CONFIG_EDIT_PLAN.md)

---

## taskList

### Phase 1: バックエンド `Conf` クラス拡張
- [x] **Task 1.1**: `Conf` クラスへの `save()` メソッド追加（アトミック書き込み・バックアップ作成機能）
- [x] **Task 1.2**: 機種設定の操作メソッド追加 (`update_model`, `add_model`, `delete_model`)
- [x] **Task 1.3**: 入力設定データの整合性検証メソッド (`validate_config`) の追加
- [x] **Task 1.4**: `tests/test_conf.py` に編集・保存機能の単体テストケースを追加・合格確認

### Phase 2: Tornado Handler & API 実装
- [x] **Task 2.1**: `src/ytstreetorgan/config_handler.py` の新規作成 (`ConfigHandler` クラス)
- [x] **Task 2.2**: 設定一覧・機種データ取得用 API (GET エンドポイント) の実装
- [x] **Task 2.3**: 設定更新・保存処理用 API (POST エンドポイント) の実装
- [x] **Task 2.4**: `webapp.py` へのルーティング (`/storgan2/config.*`) の統合
- [x] **Task 2.5**: ConfigHandler の動作テスト（REST API テスト）の作成・確認

### Phase 3: Web UI / フロントエンド実装
- [x] **Task 3.1**: `storgan.html` に「設定編集」画面への遷移ナビゲーションを追加
- [x] **Task 3.2**: `webroot/templates/config_editor.html` の作成
  - [x] 機種切替タブ / ドロップダウン
  - [x] パラメータ入力フォーム (数値・テキスト)
  - [x] `note name` / `note offset` 動的編集テーブル
  - [x] 新規機種追加 / 削除モーダル
- [x] **Task 3.3**: `webroot/static/js/config_editor.js` の作成
  - [x] 非同期データ取得とフォームバインド
  - [x] 音階テーブルの行追加/削除/順序変更ロジック
  - [x] fetch API による保存処理および成功/エラーアラート表示

### Phase 4: テスト・動作検証・仕上げ
- [x] **Task 4.1**: `pytest` による既存および新規の全単体テスト実行 (75/75 PASS, カバレッジ 95%)
- [x] **Task 4.2**: ローカル Web サーバーを起動し、ブラウザ上での全機能動作確認
  - [x] 既存機種設定の編集・保存確認
  - [x] 設定ファイル `storgan-conf.json` への反映確認
  - [x] 自動バックアップ `storgan-conf.json.bak` 生成の確認
- [x] **Task 4.3**: コードクリーンアップとドキュメント更新
