"""`WebServer` の組み立てのテスト（HTTP は投げない）。

実際のリクエストを通すテストは `test_rollbook_page_http.py` や
`test_history.py`（どちらも `WebAppTestCase` を継承）にある。
"""
from unittest.mock import patch

import pytest

from ytstreetorgan.webapp import WebServer


@patch('tornado.ioloop.IOLoop.current')
@patch('tornado.httpserver.HTTPServer')
@patch('tornado.web.Application')
def test_webserver_init_and_main(mock_app, mock_httpserver, mock_ioloop, tmp_path):
    workdir = tmp_path / "workdir"
    webroot = tmp_path / "webroot"

    server = WebServer(
        port=8080,
        urlprefix="/test",
        webroot=str(webroot),
        workdir=str(workdir),
        size_limit=1024
    )

    assert workdir.exists()

    mock_app.assert_called_once()
    mock_httpserver.assert_called_once()

    server.main()

    mock_httpserver.return_value.listen.assert_called_once_with(8080)
    mock_ioloop.return_value.start.assert_called_once()


@patch('tornado.ioloop.IOLoop.current')
@patch('tornado.httpserver.HTTPServer')
@patch('tornado.web.Application')
def test_main_prints_the_url(
    mock_app, mock_httpserver, mock_ioloop, tmp_path, capsys
):
    """起動したら、開く URL を 1 行で出す。

    端末がリンクとして拾えるよう、**URL だけの行**にすること
    （Shift + クリックでブラウザが開く）。ログではなく stdout に出す。
    """
    server = WebServer(
        port=8080, urlprefix="/test",
        webroot=str(tmp_path / "webroot"), workdir=str(tmp_path / "workdir"),
    )

    # 末尾のスラッシュは必須（無いと Handler1.get() がリダイレクトする）
    assert server.url == "http://localhost:8080/test/"

    server.main()

    lines = [ln.strip() for ln in capsys.readouterr().out.splitlines()]
    assert server.url in lines, "URL だけの行になっていない"

@patch('ytstreetorgan.webapp.logger')
def test_webserver_makedirs_exception(mock_logger, tmp_path):
    # Make tmp_path read-only so makedirs fails
    file_path = tmp_path / "file"
    file_path.write_text("")

    # workdir が通常ファイルなので Path.mkdir が FileExistsError を投げる。
    # Exception で受けると、その前段の Conf() が投げる FileNotFoundError
    # （設定ファイル未配置の環境）でもテストが通ってしまうため種類を絞る。
    with pytest.raises(FileExistsError):
        WebServer(workdir=str(file_path))
