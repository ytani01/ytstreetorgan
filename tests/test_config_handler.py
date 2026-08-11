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
            "book_height": 100,
            "margin": 5,
            "pitch": 3.5,
            "hole_height": 2.5,
            "mm_per_sec": 50,
            "base_note": 60,
            "bridge_width": 1,
            "bridge_threshold": 50,
            "notes": ["C4"], "memo": "test"
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

    def _add_with_notes(self, notes):
        """'notes' だけ差し替えて追加を試みる。"""
        new_conf = {
            "model": "test_rejected_model",
            "book_height": 100,
            "margin": 5,
            "pitch": 3.5,
            "hole_height": 2.5,
            "mm_per_sec": 50,
            "base_note": 60,
            "bridge_width": 1,
            "bridge_threshold": 50,
            "notes": notes, "memo": "test"
        }
        return self.fetch(
            f'{TEST_URL_PREFIX}/config/save',
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({'action': 'add', 'config': new_conf}),
        )

    def test_post_api_rejects_old_style_notes(self):
        # 辞書を並べた旧形式は、画面から保存できない
        response = self._add_with_notes([{"name": "C", "offset": 0}])
        assert response.code == 400
        data = json.loads(response.body.decode('utf-8'))
        assert data['status'] == 'error'
        assert "旧形式" in data['message']

    def test_post_api_rejects_invalid_note_name(self):
        # オクターブ番号の無い音名も受け付けない
        response = self._add_with_notes(["C"])
        assert response.code == 400
        data = json.loads(response.body.decode('utf-8'))
        assert data['status'] == 'error'
        assert "1 番目" in data['message']

