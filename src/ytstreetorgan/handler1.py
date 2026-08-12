#
# (c) 2026 Yoichi Tanibayashi
#
"""ロールブックを作る画面（TODO-075）。

土台のクラスは `base_handler.py`、持ち帰りと試聴は `download.py` にある。

依存は一方向に保つこと::

    base_handler.py → handler1.py / download.py / history.py /
                      config_handler.py
"""
from pathlib import Path

from loguru import logger

from .base_handler import StorganBaseHandler
from .conf import Conf
from .mylog import exmsg
from .rollbook import RollBook
from .storage import (
    UNKNOWN,
    BookInfo,
    book_from_svg,
    mtime_text,
    resolve_in,
    size_text,
)
from .transpose import transpose_view
from .utils import get_size_unit


class Handler1(StorganBaseHandler):
    """ロールブックを作る画面（`/`）。

    MIDI のアップロード → SVG 生成 → プレビュー。履歴からの
    再生成（`stored_midi`）と再表示（`stored_svg`）もここが受ける。
    """
    TITLE = 'Street Organ Roll Book Maker'

    HTML_FILE = 'storgan.html'

    def __init__(self, app, req, **kwargs):
        """設定を読む（機種の一覧と、画面に出す寸法に使う）。"""
        self._conf_file = RollBook.DEF_CONF_FILE
        self._model_name = RollBook.DEF_MODEL_NAME

        # 画面上で「選んだ機種の寸法」を出すため、名前だけでなく設定本体も渡す
        conf = Conf(self._conf_file)
        self._conf_data = conf.data
        self._models = conf.models
        self._model = ''

        super().__init__(app, req, **kwargs)

        logger.debug(
            "conf_file={}, model_name={}", self._conf_file, self._model_name
        )

    DEF_MSG = 'MIDI ファイルを選んでください'

    # 解析に失敗したときの文言。アップロードと履歴からの再生成で共用する
    UNREADABLE_MSG = ('{} を読み込めませんでした。'
                      'MIDI ファイルではないか、壊れている可能性があります。')

    def get(self):
        """ファイル選択の画面を出す。

        末尾のスラッシュが無ければ、付けた URL へリダイレクトする。
        """
        logger.debug('uri={}', self.request.uri)

        if self.request.uri != self._url_path:
            self.redirect(self._url_path, permanent=True)
            return

        self._render()

    def _render(self, svg_data='', svg_filename='', msg=DEF_MSG, book=None,
                src_size='', msg_error=False, reused_name='',
                from_history=False, candidates=None, midi_name=''):
        """テンプレートを描画する。

        ``svg_data`` が空なら「ファイル選択」、そうでなければ「生成結果」の
        画面になる。

        SVG は文字列のままテンプレートに埋め込む（別リクエストにすると
        ビューアの初期表示までに 2 往復かかるため）。ただし**寸法は SVG から
        は取り出せない**ので、``book`` に入れて別に渡す。ビューアはこれで
        初期倍率とスクロール位置を決める。

        Args:
            svg_data (str): 埋め込む SVG。空ならファイル選択の画面になる。
            svg_filename (str): 生成した SVG のファイル名。
            msg (str): 画面に出す知らせ。
            book (dict | None): ブックの諸元（寸法・穴の数・mm_per_sec）。
                ファイル選択の画面では None。
            src_size (str): 元 MIDI のサイズ（'12.3 KB'）。ファイル名は
                SVG 名（＝ MIDI 名 + '.svg'）に含まれるので渡さない。
            msg_error (bool): ``msg`` が失敗の知らせなら True
                （画面上で赤くする）。
            reused_name (str): 今回送られたファイルではなく、サーバーに
                あった同名のファイルから作った場合、その名前。結果の
                画面にその旨を出す（空なら普通に生成した場合）。
            from_history (bool): 履歴から保存済みの SVG をそのまま出した
                場合は True。諸元が SVG から読めるぶんしか無いことを
                画面に断る。
            candidates (list | None): 移調の候補（TODO-039）。**移調を
                指定していなくても渡す。** 最適解が 1 つに定まらないことが
                多いので、画面で比べて選び直せるようにするのが目的。
                **添える文も表を出すかも `transpose_view()` が決める**ので、
                呼ぶ側は候補だけ渡せばよい（TODO-043）。
            midi_name (str): 候補を押したときに作り直す元の MIDI 名。
                これが無いと再生成できないので、候補も出さない。

        Note:
            候補から決まるもの（注記・表を出すか・±0 の成績）は、
            **呼ぶ側に作らせず `transpose_view()` でまとめて作る**
            （TODO-043 / TODO-076）。
        """
        size_limit, size_unit = get_size_unit(self._size_limit)

        # 候補から決まるものは、呼ぶ側に作らせず**まとめて作る**。
        # 片方だけ渡し忘れる余地を無くすため（TODO-043）。
        # 中身は transpose.py にある（HTTP 抜きで確かめられる。TODO-076）
        view = transpose_view(candidates)

        self.render_page(self.HTML_FILE,
                         title=self.TITLE,
                         nav='top',
                         size_limit=size_limit,
                         size_unit=size_unit,
                         # 分からない値の出し方。テンプレートと JS が
                         # それぞれ '---' を持たないよう、ここから渡す
                         unknown=UNKNOWN,
                         # 表示用に丸めた値とは別に、素のバイト数も渡す。
                         # JS が送信前に大きさを比べるのに使う。
                         size_limit_bytes=self._size_limit,
                         msg_error=msg_error,
                         uploaded_names=self.uploaded_midi_names(),
                         reused_name=reused_name,
                         from_history=from_history,
                         models=self._models,
                         models_data=self._conf_data,
                         svg_data=svg_data,
                         svg_filename=svg_filename,
                         book=book or {},
                         src_size=src_size,
                         candidates=candidates or [],
                         zero_note_pct=view.zero_note_pct,
                         zero_sec_pct=view.zero_sec_pct,
                         notices=view.notices,
                         show_transpose_table=view.show_table,
                         midi_name=midi_name,
                         msg=msg)

    async def post(self):
        """MIDI を受け取って SVG を作る。

        履歴からの操作（`stored_svg` / `stored_midi`）もここで受ける。
        どちらもファイルは送られてこない。
        """
        # 履歴の画面からの操作。どちらもファイルは送られてこない
        stored_svg = self.get_argument('stored_svg', '')
        if stored_svg:
            self._show_stored_svg(stored_svg)
            return

        stored_midi = self.get_argument('stored_midi', '')
        if stored_midi:
            self._generate_from_stored(stored_midi)
            return

        file1 = self.request.files['file1'][0]
        file1_fname = file1['filename']
        file1_path = self._webroot / 'midi' / file1_fname
        svg1_fname = f'{file1_fname}.svg'
        svg1_path = self._webroot / 'svg' / svg1_fname

        self._model = self.get_argument('model')
        logger.debug('model=\'{}\'', self._model)

        rollbook = self._rollbook_of(
            self._model, self.get_argument('transpose', '0')
        )
        if rollbook is None:
            return

        # 同じ名前が既にあるときの扱いは、画面 (storgan.js) が先に訊いて
        # overwrite / reuse のどちらかを立ててくる。
        #
        # - overwrite: 送られてきた中身で置き換える
        # - reuse:     置き換えず、サーバーにある前回のファイルから作り直す
        #
        # どちらも無いまま同名を送るのは断る。かつては送られてきた中身を
        # 捨てて古いほうを解析していたため、MIDI を直して同じ名前で上げ直すと
        # **前回の結果がそのまま返っていた**。成功したように見えるぶん、
        # エラーになるより質が悪い。
        overwrite = self.get_argument('overwrite', '') == '1'
        reuse = self.get_argument('reuse', '') == '1' and file1_path.exists()

        if file1_path.exists() and not (overwrite or reuse):
            self._render(
                msg=f'{file1_fname} は既にあります。'
                    '置き換えるか、名前を変えてください。',
                msg_error=True,
            )
            return

        # reuse のときは、送られてきた中身を使わない（捨てる）。
        # 画面はファイル選択の form ごと送ってくるので中身は届いているが、
        # ここで書かないことが「前回のファイルのまま」の意味になる。
        if not reuse:
            file1_path.write_bytes(file1['body'])

        src_size = size_text(file1_path)

        try:
            svg_data = rollbook.parse_to_file(file1_path, svg1_path)
        except Exception as e:
            # 捕まえないと tornado 既定の 500 ページに置き換わり、
            # 画面ごと失われて選び直すこともできなくなる。
            logger.error(exmsg(e))

            # 読めなかったものは残さない。残すと、次に同じ名前で正しい
            # ファイルを送るたびに「既にあります」と言われることになる。
            file1_path.unlink(missing_ok=True)

            self._render(
                msg=self.UNREADABLE_MSG.format(file1_fname), msg_error=True
            )
            return

        logger.debug('len(svg_data)={}', len(svg_data))

        self._render(
            svg_data=svg_data,
            svg_filename=svg1_fname,
            src_size=src_size,
            reused_name=file1_fname if reuse else '',
            book=self._book_of(rollbook, svg1_path),
            candidates=rollbook.candidates,
            midi_name=file1_fname,
        )

    def _rollbook_of(
        self, model: str, transpose: str = '0'
    ) -> RollBook | None:
        """機種名から `RollBook` を作る。作れなければ画面に理由を出す。

        `RollBook` は知らない機種名や項目の足りない設定、整数にも
        ``'auto'`` にもならない移調量を `ValueError` で断る。捕まえないと
        tornado 既定の 500 ページに置き換わり、選び直すこともできなくなる。

        Args:
            model (str): 機種名。フォームから来る。
            transpose (str): 移調量。フォームから来るので**文字列**
                （``'auto'`` もありうる）。

        Returns:
            RollBook | None: 作れなければ None（描画はここで済ませてある）。
        """
        try:
            return RollBook(model, self._conf_file, transpose)
        except ValueError as e:
            logger.error(exmsg(e))
            self._render(msg=str(e), msg_error=True)
            return None

    def _stored_path(self, subdir: str, name: str) -> Path | None:
        """置き場（`webroot/<subdir>/`）の中のファイルを引く。

        名前は履歴の画面から来るので、**必ず `resolve_in()` を通す**
        （置き場の外を指していないか確かめる）。引けなければ理由を
        画面に出して None を返す。

        Returns:
            Path | None: 引けなければ None（描画はここで済ませてある）。
        """
        try:
            path = resolve_in(self._webroot / subdir, name)
        except ValueError as e:
            logger.error(exmsg(e))
            self._render(msg=f'{name} は開けません。', msg_error=True)
            return None

        if not path.is_file():
            self._render(msg=f'{name} は見つかりません。', msg_error=True)
            return None

        return path

    def _book_of(self, rollbook: RollBook, svg_path: Path) -> BookInfo:
        """ビューアに渡す諸元を組み立てる。

        穴の数は「音符の数」と「ブリッジで分割したあとの数」の 2 段階あり、
        さらに実線（穴を開ける）と破線（開けない）で分かれる。

        履歴から出し直すときは `storage.book_from_svg()` が同じ形を作る。
        **項目を増やすときは両方を直すこと**（`BookInfo` に足せば、
        片側の付け忘れは mypy が拾う。TODO-074）。
        """
        return {
            'model': self._model,
            # SVG は今書いたので、更新日時がそのまま生成日時になる
            'created': mtime_text(svg_path),
            'width': round(rollbook.width, 2),
            'height': round(rollbook.height, 2),
            'mm_per_sec': rollbook.mm_per_sec,
            'notes': rollbook.note_count,
            'hole_notes': rollbook.hole_note_count,
            'holes': rollbook.hole_count,
            'off_scale_notes': rollbook.off_scale_note_count,
            'off_scale': rollbook.off_scale_count,
            'merged': rollbook.merged_count,
            'transpose': rollbook.transpose,
        }

    def _show_stored_svg(self, name: str) -> None:
        """保存済みの SVG を、生成し直さずにそのまま表示する。

        諸元は SVG から読めるぶんだけ（`width` / `height`）。
        穴の数と `mm_per_sec` は SVG に無いので None のまま渡し、
        画面では `---` と出る。
        """
        path = self._stored_path('svg', name)
        if path is None:
            return

        svg_data = path.read_text(encoding='utf-8')

        book = book_from_svg(svg_data)
        # 生成日時は SVG の中ではなくファイルの更新日時から取る
        book['created'] = mtime_text(path)

        self._render(
            svg_data=svg_data,
            svg_filename=path.name,
            src_size=size_text(path),
            book=book,
            from_history=True,
        )

    def _generate_from_stored(self, name: str) -> None:
        """保存済みの MIDI から、いま選んでいる機種・移調量で作り直す。

        履歴の画面からも、生成結果の画面の移調の候補からも、ここへ来る。
        """
        midi_path = self._stored_path('midi', name)
        if midi_path is None:
            return

        self._model = self.get_argument('model')
        rollbook = self._rollbook_of(
            self._model, self.get_argument('transpose', '0')
        )
        if rollbook is None:
            return

        svg_path = self._webroot / 'svg' / f'{midi_path.name}.svg'

        try:
            svg_data = rollbook.parse_to_file(midi_path, svg_path)
        except Exception as e:
            logger.error(exmsg(e))
            self._render(
                msg=self.UNREADABLE_MSG.format(midi_path.name), msg_error=True
            )
            return

        self._render(
            svg_data=svg_data,
            svg_filename=svg_path.name,
            src_size=size_text(midi_path),
            book=self._book_of(rollbook, svg_path),
            candidates=rollbook.candidates,
            midi_name=midi_path.name,
        )
