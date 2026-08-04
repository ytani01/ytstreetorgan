#
# (c) 2026 Yoichi Tanibayashi
#
import json

from loguru import logger

from .conf import Conf
from .handler1 import StorganBaseHandler
from .mylog import exmsg
from .rollbook import RollBook


class ConfigHandler(StorganBaseHandler):
    """機種設定のエディタ（`/config`）。

    `?api=1` または `/config/api/data` なら JSON を返す。
    POST は save / update / add / delete を JSON で受ける。
    """
    HTML_FILE = 'config_editor.html'
    TITLE = 'Organ Model Config Editor'

    def __init__(self, app, req):
        """設定ファイルの位置を決めてから、土台の初期化を呼ぶ。"""
        self._conf_file = RollBook.DEF_CONF_FILE
        super().__init__(app, req)

    def get(self):
        """エディタの画面を出す。API として呼ばれたら JSON を返す。"""
        logger.debug('request uri={}', self.request.uri)

        # Check if API request for JSON data
        if (self.get_argument('api', '0') == '1'
                or self.request.path.endswith('/api/data')):
            conf = Conf(self._conf_file)
            selected_model = self.get_argument('model', '')
            model_data = conf.get(selected_model) if selected_model else {}

            self.set_header('Content-Type', 'application/json')
            self.write(json.dumps({
                'status': 'ok',
                'models': conf.models,
                'data': conf.data,
                'selected_model': selected_model,
                'selected_data': model_data
            }, ensure_ascii=False))
            return

        conf = Conf(self._conf_file)
        self.render_page(
            self.HTML_FILE,
            title=self.TITLE,
            nav='config',
            models=conf.models,
            conf_data=json.dumps(conf.data, ensure_ascii=False),
        )

    def post(self):
        """機種の追加・更新・削除。JSON でもフォームでも受ける。

        `action` は save / update / add / delete。結果は JSON で返し、
        **`message` はそのまま画面に出る**（日本語で書くこと）。
        """
        self.set_header('Content-Type', 'application/json')
        logger.debug('request body={}', self.request.body)

        req_data = {}
        try:
            if self.request.body:
                req_data = json.loads(self.request.body.decode('utf-8'))
            else:
                req_data = {
                    'action': self.get_argument('action', 'save'),
                    'model_name': self.get_argument('model_name', ''),
                    'config': json.loads(self.get_argument('config', '{}'))
                }
        except Exception as ex:
            logger.error('リクエストを読めません: {}', exmsg(ex))
            self.set_status(400)
            self.write(json.dumps({
                'status': 'error',
                'message': 'リクエストの形式が不正です（JSON として読めません）'
            }))
            return

        action = req_data.get('action', 'save')
        model_name = req_data.get('model_name', '')
        config_payload = req_data.get('config', {})

        conf = Conf(self._conf_file)

        if action == 'save' or action == 'update':
            ok, msg = conf.update_model(model_name, config_payload)
        elif action == 'add':
            ok, msg = conf.add_model(config_payload)
        elif action == 'delete':
            ok, msg = conf.delete_model(model_name)
        else:
            ok, msg = False, f"不明な操作です: '{action}'"

        if ok:
            self.write(json.dumps({
                'status': 'ok',
                'message': msg,
                'models': conf.models,
                'data': conf.data
            }, ensure_ascii=False))
        else:
            self.set_status(400)
            self.write(json.dumps({
                'status': 'error',
                'message': msg
            }, ensure_ascii=False))
