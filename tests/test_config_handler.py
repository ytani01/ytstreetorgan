import json

from tornado.testing import AsyncHTTPTestCase

from ytstreetorgan.webapp import WebServer

from .conftest import TEST_URL_PREFIX


class TestConfigHandler(AsyncHTTPTestCase):
    def get_app(self):
        self.workdir = '/tmp/storgan_test_config_workdir'
        self.webroot = './webroot'
        self.server = WebServer(
            port=10081,
            urlprefix=TEST_URL_PREFIX,
            webroot=self.webroot,
            workdir=self.workdir,
            size_limit=1024 * 1024
        )
        return self.server._app

    def test_get_api_data(self):
        response = self.fetch(f'{TEST_URL_PREFIX}/config/api/data')
        assert response.code == 200

        data = json.loads(response.body.decode('utf-8'))
        assert data['status'] == 'ok'
        assert isinstance(data['models'], list)
        assert isinstance(data['data'], list)

    def test_post_api_save_invalid_json(self):
        headers = {'Content-Type': 'application/json'}
        response = self.fetch(
            f'{TEST_URL_PREFIX}/config/save',
            method='POST',
            headers=headers,
            body='invalid json'
        )
        assert response.code == 400
        data = json.loads(response.body.decode('utf-8'))
        assert data['status'] == 'error'

    def test_get_config_page(self):
        response = self.fetch(f'{TEST_URL_PREFIX}/config')
        assert response.code == 200
        assert b"Organ Model Config Editor" in response.body

    def test_post_api_unknown_action(self):
        headers = {'Content-Type': 'application/json'}
        payload = json.dumps({'action': 'invalid_action'})
        response = self.fetch(
            f'{TEST_URL_PREFIX}/config/save',
            method='POST',
            headers=headers,
            body=payload
        )
        assert response.code == 400
        data = json.loads(response.body.decode('utf-8'))
        assert data['status'] == 'error'

    def test_post_api_add_and_delete_model(self):
        headers = {'Content-Type': 'application/json'}
        # Add new model
        new_conf = {
            "model": "test_async_model",
            "book height": 100,
            "margin": 5,
            "pitch": 3.5,
            "hole height": 2.5,
            "1sec": 50,
            "base note": 60,
            "bridge width": 1,
            "bridge threshold": 50,
            "notes": [{"name": "C", "offset": 0}], "memo": "test"
        }
        add_payload = json.dumps({'action': 'add', 'config': new_conf})
        response = self.fetch(
            f'{TEST_URL_PREFIX}/config/save',
            method='POST',
            headers=headers,
            body=add_payload
        )
        assert response.code == 200
        data = json.loads(response.body.decode('utf-8'))
        assert data['status'] == 'ok'
        assert "test_async_model" in data['models']

        # Delete the model
        del_payload = json.dumps({'action': 'delete', 'model_name': 'test_async_model'})
        response = self.fetch(
            f'{TEST_URL_PREFIX}/config/save',
            method='POST',
            headers=headers,
            body=del_payload
        )
        assert response.code == 200
        data = json.loads(response.body.decode('utf-8'))
        assert data['status'] == 'ok'
        assert "test_async_model" not in data['models']

