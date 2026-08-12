#
# (c) 2026 Yoichi Tanibayashi
#
"""持ち帰りと試聴のハンドラ（TODO-075）。

どれも「置き場のファイルを引いて、その場で作って返す」だけで、画面は
持たない。`Handler1`（ロールブックを作る画面）とは役割が違うので分けた。

**URL は 4 つとも別にしてある。** 同じ名前で中身の違う MIDI が出回らない
ようにするため（それぞれの docstring に理由がある）。

依存は一方向に保つこと::

    base_handler.py → handler1.py / download.py / history.py /
                      config_handler.py
"""
import tornado.web
from loguru import logger

from .audition import playable_midi_bytes
from .base_handler import StorganBaseHandler
from .mylog import exmsg
from .storage import content_disposition
from .transpose import (
    transpose_midi_bytes,
    transposed_midi_name,
    transposed_midi_zip_bytes,
    transposed_zip_name,
)


class Download(StorganBaseHandler):
    """生成した SVG と、アップロードした MIDI を持ち帰る。

    URL は `/download/<name>`（SVG）と `/download/midi/<name>`。
    SVG 側に種別が入っていないのは、生成結果の画面のリンクが
    元からこの形だったため。**どちらの置き場かはルートが
    `kind` で渡す**（URL から読み取らない）。
    """

    def initialize(self, kind: str = 'svg') -> None:
        """置き場の種別を受け取る（`WebServer` のルート定義から）。

        Args:
            kind (str): 'midi' か 'svg'。
        """
        self._kind = kind

    def get(self, fname: str = ''):
        """ファイルを返す。

        Args:
            fname (str): ファイル名。URL から来る。
        """
        logger.debug('kind={}, fname={}', self._kind, fname)

        path_name = self.stored_file(self._kind, fname)

        logger.debug('path_name={}', path_name)

        self.set_header('Content-Type', 'application/octet-stream')
        # 名前をそのまま入れると、日本語のファイル名で 500 になる
        self.set_header('Content-Disposition',
                        content_disposition(path_name.name))

        buf_size = 4096
        with path_name.open('rb') as f:
            while True:
                data = f.read(buf_size)
                if not data:
                    break
                self.write(data)

        self.finish()


class DownloadTransposedMidi(StorganBaseHandler):
    """アップロード済みの MIDI を、指定の調に移調して持ち帰る（TODO-042）。

    URL は `/download/midi-transpose/<name>?t=<半音数>`。

    **`Download` とは別にしてある。** あちらは実在するファイルを
    そのまま返す作りで、こちらは「名前 ＋ 移調量」からその場で作る
    別物。**作った MIDI は保存しない**（`webroot/midi/` を太らせない）。
    """

    def get(self, fname: str = ''):
        """元の MIDI を移調して返す。

        Args:
            fname (str): 元の MIDI のファイル名。URL から来る。
        """
        logger.debug('fname={}, t={}', fname, self.get_argument('t', ''))

        path_name = self.stored_file('midi', fname)
        semitones = self.transpose_arg()

        try:
            data = transpose_midi_bytes(path_name, semitones)
        except Exception as e:
            # 読めない MIDI など。既定の 500 ページより理由が分かる
            logger.error(exmsg(e))
            raise tornado.web.HTTPError(
                400, reason='cannot transpose'
            ) from e

        self.set_header('Content-Type', 'application/octet-stream')
        # 名前をそのまま入れると、日本語のファイル名で 500 になる
        self.set_header(
            'Content-Disposition',
            content_disposition(
                transposed_midi_name(path_name.name, semitones)
            )
        )
        self.write(data)
        self.finish()


class DownloadTransposedMidiZip(StorganBaseHandler):
    """移調した MIDI を、まとめて ZIP で持ち帰る（TODO-050）。

    URL は `/download/midi-transpose-zip/<name>?t=-5,-2,0,3`。

    **半音数はクエリで受け取る**（候補をサーバー側で作り直さない）。
    `DownloadTransposedMidi` と同じく、名前と半音数だけから作れる。
    **作った MIDI も ZIP も保存しない。**
    """

    # 候補は最大 7 行（TODO-041）。外から好きな数を投げられると
    # 1 リクエストで何百回も移調させられるので、余裕を見て頭打ちにする
    MAX_ITEMS = 32

    def get(self, fname: str = ''):
        """元の MIDI を、指定された調ぶんだけ移調して ZIP で返す。

        Args:
            fname (str): 元の MIDI のファイル名。URL から来る。
        """
        transpose = self.get_argument('t', '')
        logger.debug('fname={}, t={}', fname, transpose)

        path_name = self.stored_file('midi', fname)
        semitones_list = self._parse_transpose(transpose)

        try:
            data = transposed_midi_zip_bytes(path_name, semitones_list)
        except Exception as e:
            # 読めない MIDI など。既定の 500 ページより理由が分かる
            logger.error(exmsg(e))
            raise tornado.web.HTTPError(
                400, reason='cannot transpose'
            ) from e

        self.set_header('Content-Type', 'application/zip')
        # 名前をそのまま入れると、日本語のファイル名で 500 になる
        self.set_header(
            'Content-Disposition',
            content_disposition(transposed_zip_name(path_name.name))
        )
        self.write(data)
        self.finish()

    def _parse_transpose(self, transpose: str) -> list[int]:
        """``-5,-2,0,3`` を整数の並びに直す。

        重複は**最初に出たほうを残して削除する**（同じ名前の要素が
        2 つ入った ZIP を作らないため）。並び順は画面の表と同じ。

        Raises:
            tornado.web.HTTPError: 空、整数でない、多すぎる場合は 400。
        """
        try:
            values = [int(s) for s in transpose.split(',')]
        except ValueError as e:
            logger.error(exmsg(e))
            raise tornado.web.HTTPError(400, reason='bad transpose') from e

        # dict は挿入順を保つので、これで重複だけ削除できる
        uniq = list(dict.fromkeys(values))

        if not uniq or len(uniq) > self.MAX_ITEMS:
            raise tornado.web.HTTPError(400, reason='bad transpose')

        return uniq


class AuditionMidi(StorganBaseHandler):
    """ブラウザで試聴するための MIDI を返す（TODO-063）。

    URL は `/audition/midi/<name>?t=<半音数>&model=<機種名>`。

    **`DownloadTransposedMidi` とは別にしてある。** あちらは持ち帰る
    素材（元のファイルを移調しただけ）で、こちらは実機の再現
    （音階に無い音は鳴らない）。目的が違うものを同じ URL から返すと、
    同じ名前で中身の違う MIDI が 2 種類出回ることになる。

    **`Content-Disposition` は付けない**（持ち帰らせない。試聴のための
    ものなので、欲しくなったらここに足すのが答え）。**保存もしない。**
    """

    def get(self, fname: str = ''):
        """鳴る音だけの MIDI を返す。

        Args:
            fname (str): 元の MIDI のファイル名。URL から来る。
        """
        model = self.get_argument('model', '')
        logger.debug('fname={}, t={}, model={}',
                     fname, self.get_argument('t', ''), model)

        path_name = self.stored_file('midi', fname)
        semitones = self.transpose_arg()

        try:
            data = playable_midi_bytes(path_name, model, semitones)
        except ValueError as e:
            # 知らない機種名、設定の項目が足りない
            logger.error(exmsg(e))
            raise tornado.web.HTTPError(400, reason='bad model') from e
        except Exception as e:
            # 読めない MIDI など。既定の 500 ページより理由が分かる
            logger.error(exmsg(e))
            raise tornado.web.HTTPError(400, reason='cannot audition') from e

        self.set_header('Content-Type', 'audio/midi')
        self.write(data)
        self.finish()
