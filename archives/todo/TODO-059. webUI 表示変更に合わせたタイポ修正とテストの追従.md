# TODO-059. webUI 表示変更に合わせたタイポ修正とテストの追従

## きっかけ

直近のコミット（`b5e99971`）での webUI 表示調整により、「MIDIアプロード」というタイポおよび画面文言・レイアウトの変更が発生し、関連するテストが失敗していたため。

## やったこと

- `base.html` のナビゲーションリンクおよび `storgan.html` の見出しにおける「MIDIアプロード」を「MIDIアップロード」にタイポ修正（`develop` マージにより取り込み）。
- 意図的な webUI 表示変更（ナビゲーション文言、諸元表記、移調候補の表示等）に合わせて失敗していた単体・HTTP・ブラウザテスト（`tests/test_history.py`, `tests/test_rollbook_page_http.py`, `tests/browser/test_history_page.py`, `tests/browser/test_rollbook_page.py`）を更新。

## テスト

- `uv run pytest` 236 件成功
- `uv run pytest -m browser` 42 件成功
