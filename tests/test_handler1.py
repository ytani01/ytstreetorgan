import pytest
import os
from unittest.mock import patch, MagicMock
from ytstreetorgan.handler1 import Handler1, Download

def test_handler1_size_unit():
    app = MagicMock()
    app.settings = {
        'urlprefix': '/',
        'webroot': '/tmp',
        'workdir': '/tmp',
        'size_limit': 1024,
        'url_prefix_handler1': '/handler1',
        'version': '1.0.0'
    }
    req = MagicMock()
    
    # We patch __init__ of RequestHandler to avoid calling the real one
    with patch('tornado.web.RequestHandler.__init__'):
        handler = Handler1(app, req)
        # Manually set what super().__init__ would set
        handler.application = app
        handler.request = req
        
        # Test get_size_unit
        assert handler.get_size_unit(1023) == (1023, 'B')
        assert handler.get_size_unit(1024) == (1.0, 'KB')
        assert handler.get_size_unit(1024 * 1024) == (1.0, 'MB')

def test_handler1_get_filesize(tmp_path):
    app = MagicMock()
    app.settings = {
        'urlprefix': '/',
        'webroot': '/tmp',
        'workdir': '/tmp',
        'size_limit': 1024,
        'url_prefix_handler1': '/handler1',
        'version': '1.0.0'
    }
    req = MagicMock()
    
    with patch('tornado.web.RequestHandler.__init__'):
        handler = Handler1(app, req)
        handler.application = app
        handler.request = req
        
        # Test non-existent file
        assert handler.get_filesize(str(tmp_path / "non_existent")) is None
        
        # Test existing file
        file_path = tmp_path / "test.txt"
        file_path.write_text("hello")
        size, unit = handler.get_filesize(str(file_path))
        assert size == 5
        assert unit == 'B'

def test_download_init():
    app = MagicMock()
    app.settings = {
        'urlprefix': '/',
        'webroot': '/tmp',
        'workdir': '/tmp',
        'size_limit': 1024,
        'url_prefix_handler1': '/handler1',
        'version': '1.0.0'
    }
    req = MagicMock()
    
    with patch('tornado.web.RequestHandler.__init__'):
        download = Download(app, req)
        assert download._urlprefix == '/'
