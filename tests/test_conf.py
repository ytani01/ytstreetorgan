"""
Conf クラスに対する pytest テスト

前提:
    テスト対象のソースコードはモジュール `conf.py`
    (`from conf import Conf` でインポート可能な場所) に
    配置されていることを想定しています。
    実際のファイル名・パッケージ構成が異なる場合は、
    下記の import 文を適宜書き換えてください。
"""
import json

import pytest

from ytstreetorgan.conf import Conf


# ---------------------------------------------------------------------
# フィクスチャ
# ---------------------------------------------------------------------

@pytest.fixture
def isolated_search_path(monkeypatch, tmp_path):
    """
    Conf.SEARCH_PATH を、テスト用の空ディレクトリ群に差し替える。
    これにより、実環境の ~/.config や /etc を一切参照せずに
    search() の挙動をテストできる。
    """
    dummy_dirs = [tmp_path / "dir_a", tmp_path / "dir_b", tmp_path / "dir_c"]
    for d in dummy_dirs:
        d.mkdir()
    monkeypatch.setattr(Conf, "SEARCH_PATH", dummy_dirs)
    return dummy_dirs


def make_bare_conf() -> Conf:
    """__init__ を経由せずに Conf インスタンスを作る(search/load 単体テスト用)"""
    conf = Conf.__new__(Conf)
    conf.config_file = None
    conf.data = None
    return conf


# ---------------------------------------------------------------------
# __init__ (コンストラクタ) のテスト
# ---------------------------------------------------------------------

class TestInit:
    def test_explicit_config_file_found(self, tmp_path, isolated_search_path):
        """指定した config_file が実在すれば、それがそのまま使われる(search()は呼ばれない)"""
        conf_file = tmp_path / "my_conf.json"
        conf_file.write_text("{}", encoding="utf-8")

        conf = Conf(config_file=str(conf_file))

        assert conf.config_file == conf_file

    def test_explicit_config_file_not_found_falls_back_to_search(
        self, isolated_search_path
    ):
        """指定した config_file が存在しない場合、search() にフォールバックする"""
        target = isolated_search_path[1] / Conf.CONF_FNAME
        target.write_text("{}", encoding="utf-8")

        conf = Conf(config_file="/no/such/file.json")

        assert conf.config_file == target

    def test_no_config_file_found_anywhere(self, isolated_search_path):
        """どこにも見つからない場合、config_file は None のまま"""
        conf = Conf(config_file="")

        assert conf.config_file is None

    def test_default_config_file_argument(self, isolated_search_path):
        """引数なしで Conf() を呼んだ場合も config_file='' と同じ挙動になる"""
        conf = Conf()

        assert conf.config_file is None

    def test_data_is_none_before_load(self, tmp_path, isolated_search_path):
        """load() を呼ぶ前は data は None"""
        conf_file = tmp_path / "my_conf.json"
        conf_file.write_text("{}", encoding="utf-8")

        conf = Conf(config_file=str(conf_file))

        assert conf.data is None

    def test_expanduser_is_applied(self, monkeypatch, tmp_path):
        """config_file が '~' で始まる場合、展開されること"""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setenv("HOME", str(fake_home))

        conf_file = fake_home / "my_conf.json"
        conf_file.write_text("{}", encoding="utf-8")

        conf = Conf(config_file="~/my_conf.json")

        assert conf.config_file == conf_file

    def test_debug_argument_is_accepted(self, isolated_search_path):
        """debug 引数を渡してもインスタンス化できること(未使用の引数だが受理される)"""
        conf = Conf(config_file="", debug=True)

        assert conf.config_file is None


# ---------------------------------------------------------------------
# search() のテスト
# ---------------------------------------------------------------------

class TestSearch:
    def test_finds_file_in_first_directory(self, isolated_search_path):
        target = isolated_search_path[0] / Conf.CONF_FNAME
        target.write_text("{}", encoding="utf-8")

        conf = make_bare_conf()
        result = conf.search()

        assert result == target
        assert conf.config_file == target

    def test_finds_file_in_later_directory(self, isolated_search_path):
        """最初のディレクトリになくても、後続のディレクトリを探し続けること"""
        target = isolated_search_path[2] / Conf.CONF_FNAME
        target.write_text("{}", encoding="utf-8")

        conf = make_bare_conf()
        result = conf.search()

        assert result == target

    def test_returns_none_when_not_found(self, isolated_search_path):
        conf = make_bare_conf()
        result = conf.search()

        assert result is None
        assert conf.config_file is None

    def test_stops_at_first_match(self, isolated_search_path):
        """複数の候補ディレクトリに設定ファイルがある場合、最初に見つかったものを使う"""
        first_match = isolated_search_path[0] / Conf.CONF_FNAME
        second_match = isolated_search_path[1] / Conf.CONF_FNAME
        first_match.write_text("{}", encoding="utf-8")
        second_match.write_text("{}", encoding="utf-8")

        conf = make_bare_conf()
        result = conf.search()

        assert result == first_match


# ---------------------------------------------------------------------
# load() のテスト
# ---------------------------------------------------------------------

class TestLoad:
    def test_load_valid_json(self, tmp_path):
        conf_file = tmp_path / "my_conf.json"
        payload = {"key": "value", "num": 42}
        conf_file.write_text(json.dumps(payload), encoding="utf-8")

        conf = Conf(config_file=str(conf_file))
        result = conf.load()

        assert result == payload
        assert conf.data == payload

    def test_load_returns_none_when_config_file_is_none(self, isolated_search_path):
        conf = Conf(config_file="")  # どこにも見つからない -> config_file is None

        result = conf.load()

        assert result is None
        assert conf.data is None

    def test_load_invalid_json_returns_none(self, tmp_path):
        conf_file = tmp_path / "bad_conf.json"
        conf_file.write_text("{ this is not valid json ", encoding="utf-8")

        conf = Conf(config_file=str(conf_file))
        result = conf.load()

        assert result is None
        assert conf.data is None

    def test_load_empty_file_returns_none(self, tmp_path):
        """空ファイルは有効な JSON ではないので JSONDecodeError になり None を返す"""
        conf_file = tmp_path / "empty_conf.json"
        conf_file.write_text("", encoding="utf-8")

        conf = Conf(config_file=str(conf_file))
        result = conf.load()

        assert result is None

    def test_load_generic_exception_returns_none(self, tmp_path):
        """
        config_file にディレクトリを指定すると、read_text() 呼び出し時に
        IsADirectoryError (JSONDecodeError ではない一般的な Exception) が発生する。
        except Exception 節で捕捉され None が返ることを確認する。
        """
        a_directory = tmp_path / "im_a_directory"
        a_directory.mkdir()

        conf = make_bare_conf()
        conf.config_file = a_directory

        result = conf.load()

        assert result is None
        assert conf.data is None

    def test_load_json_array_is_valid(self, tmp_path):
        """load() は object 以外の valid な JSON 値(配列など)も受理すること"""
        conf_file = tmp_path / "array_conf.json"
        conf_file.write_text(json.dumps([1, 2, 3]), encoding="utf-8")

        conf = Conf(config_file=str(conf_file))
        result = conf.load()

        assert result == [1, 2, 3]
