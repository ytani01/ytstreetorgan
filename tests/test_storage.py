"""`storage.py`（置き場のファイル操作）のテスト。

**名前の検証が要点。** 履歴の画面は削除まであるので、置き場の外を指す
名前を通してしまうと事故になる。
"""
import pytest

from ytstreetorgan.storage import (
    book_from_svg,
    content_disposition,
    list_files,
    mtime_text,
    resolve_in,
    safe_name,
    size_text,
)


class TestSafeName:
    @pytest.mark.parametrize('name', ['a.mid', 'foo bar.mid', '日本語.mid',
                                      '..hidden.mid', 'a..b.mid'])
    def test_accepts_plain_names(self, name):
        assert safe_name(name) == name

    @pytest.mark.parametrize('name', [
        '', '.', '..',
        '../etc/passwd', '..\\windows',
        'sub/dir.mid', 'a/b',
        'nul\x00.mid',
    ])
    def test_rejects_dangerous_names(self, name):
        with pytest.raises(ValueError):
            safe_name(name)


class TestResolveIn:
    def test_returns_the_path_inside(self, tmp_path):
        (tmp_path / 'a.mid').write_text('x')
        assert resolve_in(tmp_path, 'a.mid') == (tmp_path / 'a.mid').resolve()

    def test_missing_file_is_not_an_error_here(self, tmp_path):
        # 存在するかどうかは呼び出し側の判断。ここは名前と位置だけ見る
        assert resolve_in(tmp_path, 'nope.mid').name == 'nope.mid'

    def test_rejects_traversal(self, tmp_path):
        with pytest.raises(ValueError):
            resolve_in(tmp_path, '../outside.mid')

    def test_rejects_symlink_pointing_outside(self, tmp_path):
        """名前が素直でも、リンクの先が外なら弾く。"""
        outside = tmp_path / 'outside'
        outside.mkdir()
        secret = outside / 'secret.txt'
        secret.write_text('x')

        inside = tmp_path / 'inside'
        inside.mkdir()
        (inside / 'link.txt').symlink_to(secret)

        with pytest.raises(ValueError):
            resolve_in(inside, 'link.txt')


class TestListFiles:
    def test_missing_dir_is_empty(self, tmp_path):
        assert list_files(tmp_path / 'nope') == []

    def test_newest_first_and_hidden_are_skipped(self, tmp_path):
        import os
        import time

        for i, name in enumerate(['old.mid', 'new.mid', '.hidden']):
            p = tmp_path / name
            p.write_text('x' * (i + 1))
            os.utime(p, (time.time() + i * 10, time.time() + i * 10))

        files = list_files(tmp_path)

        assert [f['name'] for f in files] == ['new.mid', 'old.mid']
        assert files[0]['size'].endswith('B')
        assert len(files[0]['mtime']) == 16   # 'YYYY-MM-DD HH:MM'

    def test_directories_are_skipped(self, tmp_path):
        (tmp_path / 'sub').mkdir()
        (tmp_path / 'a.mid').write_text('x')

        assert [f['name'] for f in list_files(tmp_path)] == ['a.mid']


class TestBookFromSvg:
    SVG = ('<svg xmlns="http://www.w3.org/2000/svg"'
           ' width="4133.20mm" height="126.00mm"'
           ' viewBox="-4133.20 -126.00 4133.20 126.00">\n</svg>\n')

    def test_reads_the_size(self):
        book = book_from_svg(self.SVG)

        assert book['width'] == 4133.2
        assert book['height'] == 126.0

    def test_counts_the_drawn_holes(self):
        """描かれている穴と破線は数えられる（＝分割したあとの数）。"""
        svg = self.SVG.replace('</svg>', (
            '<path style="stroke:#FF0000;" />\n'
            '<path style="stroke:#FF0000;" />\n'
            '<path style="stroke:#000000;stroke-dasharray:3 1;" />\n'
            '</svg>'
        ))
        book = book_from_svg(svg)

        assert book['holes'] == 2
        assert book['off_scale'] == 1

    def test_note_counts_and_speed_come_from_the_attributes(self):
        """分割**前**の音符の数と mm_per_sec は属性から読む。

        分割は多対一なので、描かれた穴から音符の数は逆算できない。
        そのため `RollBook` が `<svg>` に埋めている。
        """
        svg = self.SVG.replace(
            '>', ' data-storgan-mm-per-sec="50" data-storgan-notes="1033"'
                 ' data-storgan-hole-notes="562"'
                 ' data-storgan-off-scale-notes="471">', 1
        )
        book = book_from_svg(svg)

        assert book['mm_per_sec'] == 50.0
        assert book['notes'] == 1033
        assert book['model'] is None   # この SVG には入れていない
        assert book['hole_notes'] == 562
        assert book['off_scale_notes'] == 471

    def test_note_counts_are_unknown_without_the_attributes(self):
        """埋めるようにする前に作った SVG もある。無ければ '---' に落とす。"""
        book = book_from_svg(self.SVG)

        for key in ('mm_per_sec', 'notes', 'hole_notes', 'off_scale_notes',
                    'model'):
            assert book[key] is None, key

    def test_created_is_left_to_the_caller(self):
        """生成日時は SVG の中ではなくファイルの更新日時なので、ここでは None。"""
        assert book_from_svg(self.SVG)['created'] is None

    def test_broken_attributes_are_treated_as_unknown(self):
        svg = self.SVG.replace(
            '>', ' data-storgan-notes="abc" data-storgan-mm-per-sec="">', 1
        )
        book = book_from_svg(svg)

        assert book['notes'] is None
        assert book['mm_per_sec'] is None

    def test_size_is_none_when_missing(self):
        book = book_from_svg('<svg xmlns="http://www.w3.org/2000/svg"></svg>')

        assert book['width'] is None
        assert book['height'] is None

    def test_everything_is_unknown_when_not_an_svg(self):
        book = book_from_svg('これは SVG ではない')

        assert all(v is None for v in book.values())


class TestContentDisposition:
    """ヘッダは latin-1 しか通らない。名前をそのまま入れると 500 になる。"""

    def test_ascii_name_is_quoted(self):
        value = content_disposition('holy.mid')

        assert 'filename="holy.mid"' in value
        assert "filename*=UTF-8''holy.mid" in value

    def test_space_is_kept_inside_the_quotes(self):
        assert 'filename="a b.mid"' in content_disposition('a b.mid')

    def test_japanese_name_goes_to_filename_star(self):
        value = content_disposition('テスト曲.mid')

        assert "filename*=UTF-8''%E3%83%86%E3%82%B9%E3%83%88%E6%9B%B2.mid" in value
        # ASCII に落ちると名前が消えるので、代わりの名前を使う
        assert 'filename="download.mid"' in value

    def test_accents_are_folded_for_the_ascii_version(self):
        assert 'filename="naive.mid"' in content_disposition('naïve.mid')

    @pytest.mark.parametrize('name', ['a"b.mid', 'a\\b.mid', 'a\nb.mid'])
    def test_quoted_string_is_not_broken(self, name):
        """引用符・バックスラッシュ・制御文字を ASCII 版に残さない。"""
        value = content_disposition(name)
        ascii_part = value.split('filename="', 1)[1].split('"', 1)[0]

        assert '"' not in ascii_part
        assert '\\' not in ascii_part
        assert '\n' not in ascii_part

    def test_the_whole_value_is_latin_1_safe(self):
        """組み立てた値がヘッダに載ること（載らないと 500 になる）。"""
        content_disposition('テスト曲.mid').encode('latin-1')


class TestBookFromSvgMatchesRollBook:
    """生成した SVG を読み直すと、`RollBook` の値が**全部**戻ること。

    穴と破線は色で数え、それ以外は `<svg>` に埋めた属性から読む。
    **色や属性名を変えるとここが落ちる。** 落ちたら `storage.py` を
    `rollbook.py` に合わせ直すこと。
    """

    def test_round_trip(self):
        from pathlib import Path

        from ytstreetorgan.rollbook import RollBook

        midi = Path('webroot/midi/d-kaeru.mid')
        if not midi.exists():
            return

        for model in ('34notes', '20notes a'):
            rb = RollBook(model)
            svg = rb.parse(midi)

            book = book_from_svg(svg)

            assert book == {
                'model': model,
                'created': None,   # ファイルの更新日時。呼び出し側が入れる
                'width': round(rb.width, 2),
                'height': round(rb.height, 2),
                'mm_per_sec': rb.mm_per_sec,
                'notes': rb.note_count,
                'hole_notes': rb.hole_note_count,
                'holes': rb.hole_count,
                'off_scale_notes': rb.off_scale_note_count,
                'off_scale': rb.off_scale_count,
                'merged': rb.merged_count,
            }, model


class TestMtimeText:
    """SVG は生成したときに書かれるので、更新日時 = 生成日時として出す。"""

    def test_formats_the_mtime(self, tmp_path):
        import os
        from datetime import datetime

        p = tmp_path / 'a.svg'
        p.write_text('x')
        when = datetime(2026, 8, 4, 19, 30).timestamp()
        os.utime(p, (when, when))

        assert mtime_text(p) == '2026-08-04 19:30'

    def test_missing_file_is_none(self, tmp_path):
        assert mtime_text(tmp_path / 'nope.svg') is None


def test_size_text_is_the_one_place_for_the_format(tmp_path):
    """サイズの書式はここ 1 か所。一覧も生成結果の画面も同じ形になる。"""
    f = tmp_path / 'a.bin'
    f.write_bytes(b'x' * 2048)

    assert size_text(f) == '2.0 KB'

    # 一覧も同じ関数を通っている
    assert list_files(tmp_path)[0]['size'] == '2.0 KB'
