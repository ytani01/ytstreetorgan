import pytest
import os
from unittest.mock import patch, MagicMock
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
    
    assert os.path.exists(str(workdir))
    
    mock_app.assert_called_once()
    mock_httpserver.assert_called_once()
    
    server.main()
    
    mock_httpserver.return_value.listen.assert_called_once_with(8080)
    mock_ioloop.return_value.start.assert_called_once()

@patch('ytstreetorgan.webapp.logger')
def test_webserver_makedirs_exception(mock_logger, tmp_path):
    # Make tmp_path read-only so makedirs fails
    file_path = tmp_path / "file"
    file_path.write_text("")
    
    with pytest.raises(Exception):
        # file_path is a file, so makedirs will raise FileExistsError or NotADirectoryError
        WebServer(workdir=str(file_path))
