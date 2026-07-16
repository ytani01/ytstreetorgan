"""
Conf クラス(修正版)に対する pytest テスト

前提:
    テスト対象のソースコードはパッケージ内のモジュール
    `storgan/conf.py` として配置され、`from storgan.conf import Conf`
    でインポート可能であることを想定しています
    (`conf.py` が `from .mylog import exmsg` という相対importを
    使っているため、単体の .py ファイルではなくパッケージの一部で
    ある必要があります)。

    実際のパッケージ名やディレクトリ構成が異なる場合は、
    下記の import 文を適宜書き換えてください。

    また `storgan/mylog.py` の `exmsg()` はプロジェクト固有の実装
    のため、テスト実行環境には最小限のスタブ実装を用意しています。
    実際の実装に差し替えても、このテストの多くはそのまま動作する
    はずです(exmsg の戻り値の文字列内容そのものは検証していない
    ため)。
"""
import json

import pytest

from ytstreetorgan.conf import Conf


# ---------------------------------------------------------------------
# フィクスチャ / ヘルパー
# ---------------------------------------------------------------------

@pytest.fixture
def isolated_search_path(monkeypatch, tmp_path):
    """
    Conf.SEARCH_PATH を、テスト用の空ディレクトリ群に差し替える。
    実環境の ~/.config や /etc を一切参照せずに
    config_file='' のときの探索動作をテストできる。
    """
    dummy_dirs = [tmp_path / "dir_a", tmp_path / "dir_b", tmp_path / "dir_c"]
    for d in dummy_dirs:
        d.mkdir()
    monkeypatch.setattr(Conf, "SEARCH_PATH", dummy_dirs)
    return dummy_dirs


def make_bare_conf() -> Conf:
    """__init__ を経由せずに Conf インスタンスを作る(load/get 単体テスト用)"""
    conf = Conf.__new__(Conf)
    conf.config_file = None
    conf.data = []
    conf.models = []
    return conf


def write_json(path, obj):
    path.write_text(json.dumps(obj), encoding="utf-8")
    return path


# ---------------------------------------------------------------------
# __init__ (コンストラクタ) のテスト
# ---------------------------------------------------------------------

class TestInit:
    def test_explicit_config_file_found_and_loaded(self, tmp_path):
        """存在する config_file を指定すると、そのまま読み込まれる"""
        conf_file = write_json(
            tmp_path / "my_conf.json",
            [{"model": "a"}, {"model": "b"}],
        )

        conf = Conf(config_file=str(conf_file))

        assert conf.config_file == conf_file
        assert conf.data == [{"model": "a"}, {"model": "b"}]
        assert conf.models == ["a", "b"]

    def test_explicit_config_file_not_found_raises(self, tmp_path):
        """指定した config_file が存在しない場合は search せず FileNotFoundError"""
        missing = tmp_path / "does_not_exist.json"

        with pytest.raises(FileNotFoundError, match=missing.name):
            Conf(config_file=str(missing))

    def test_explicit_config_file_is_directory_raises(self, tmp_path):
        """config_file が(ファイルでなく)ディレクトリの場合も FileNotFoundError"""
        a_dir = tmp_path / "im_a_directory"
        a_dir.mkdir()

        with pytest.raises(FileNotFoundError):
            Conf(config_file=str(a_dir))

    def test_empty_config_file_searches_and_finds(self, isolated_search_path):
        """config_file='' の場合、SEARCH_PATH を順に探して見つけたものを使う"""
        target = isolated_search_path[1] / Conf.CONF_FNAME
        write_json(target, [{"model": "x"}])

        conf = Conf(config_file="")

        assert conf.config_file == target
        assert conf.data == [{"model": "x"}]
        assert conf.models == ["x"]

    def test_empty_config_file_search_stops_at_first_match(
        self, isolated_search_path
    ):
        """複数のディレクトリに設定ファイルがあれば、最初に見つかったものを使う"""
        first_match = isolated_search_path[0] / Conf.CONF_FNAME
        second_match = isolated_search_path[1] / Conf.CONF_FNAME
        write_json(first_match, [{"model": "first"}])
        write_json(second_match, [{"model": "second"}])

        conf = Conf(config_file="")

        assert conf.config_file == first_match
        assert conf.models == ["first"]

    def test_empty_config_file_not_found_anywhere_raises(
        self, isolated_search_path
    ):
        """SEARCH_PATH のどこにも見つからない場合、FileNotFoundError が送出される"""
        with pytest.raises(FileNotFoundError, match=Conf.CONF_FNAME):
            Conf(config_file="")

    def test_default_config_file_argument_behaves_like_empty_string(
        self, isolated_search_path
    ):
        """引数を省略した場合も config_file='' と同じ挙動になる"""
        target = isolated_search_path[0] / Conf.CONF_FNAME
        write_json(target, [{"model": "x"}])

        conf = Conf()

        assert conf.config_file == target

    def test_expanduser_is_applied_to_explicit_path(self, monkeypatch, tmp_path):
        """config_file が '~' で始まる場合、展開されること"""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setenv("HOME", str(fake_home))

        conf_file = write_json(fake_home / "my_conf.json", [])

        conf = Conf(config_file="~/my_conf.json")

        assert conf.config_file == conf_file

    def test_debug_argument_is_accepted(self, tmp_path):
        """debug 引数を渡してもインスタンス化できること(未使用の引数だが受理される)"""
        conf_file = write_json(tmp_path / "my_conf.json", [])

        conf = Conf(config_file=str(conf_file), debug=True)

        assert conf.data == []

    def test_load_error_during_init_does_not_raise(self, tmp_path):
        """
        ファイル自体は存在するが中身が不正な JSON の場合、
        load() 内で例外が握りつぶされるため、__init__ 自体は
        例外を送出せずに正常にインスタンス化できる。
        """
        conf_file = tmp_path / "bad_conf.json"
        conf_file.write_text("{ not valid json", encoding="utf-8")

        conf = Conf(config_file=str(conf_file))

        assert conf.data == []
        assert conf.models == []


# ---------------------------------------------------------------------
# load() のテスト
# ---------------------------------------------------------------------

class TestLoad:
    def test_load_valid_json_builds_models_list(self, tmp_path):
        conf = make_bare_conf()
        conf.config_file = write_json(
            tmp_path / "conf.json",
            [{"model": "alpha", "opt": 1}, {"model": "beta", "opt": 2}],
        )

        result = conf.load()

        assert result == [{"model": "alpha", "opt": 1}, {"model": "beta", "opt": 2}]
        assert conf.data == result
        assert conf.models == ["alpha", "beta"]

    def test_load_invalid_json_returns_empty_list(self, tmp_path):
        conf = make_bare_conf()
        conf.config_file = tmp_path / "bad_conf.json"
        conf.config_file.write_text("{ not valid json", encoding="utf-8")

        result = conf.load()

        assert result == []
        # 例外は json.loads() の時点で起きるため self.data は書き換わらない
        assert conf.data == []
        assert conf.models == []

    def test_load_empty_file_returns_empty_list(self, tmp_path):
        """空ファイルは JSONDecodeError になる"""
        conf = make_bare_conf()
        conf.config_file = tmp_path / "empty_conf.json"
        conf.config_file.write_text("", encoding="utf-8")

        result = conf.load()

        assert result == []

    def test_load_missing_model_key_raises_keyerror_internally(self, tmp_path):
        """
        JSON 自体は正しくパースできるが、要素に 'model' キーが
        無い場合は KeyError が発生する。
        self.data はパース結果で更新されるが、self.models は
        (リスト内包表記が完了しないため)更新されない。
        """
        conf = make_bare_conf()
        conf.config_file = write_json(
            tmp_path / "conf.json",
            [{"model": "alpha"}, {"no_model_key": True}],
        )

        result = conf.load()

        assert result == []
        assert conf.data == [{"model": "alpha"}, {"no_model_key": True}]
        assert conf.models == []  # 更新されずに初期値のまま

    def test_load_non_dict_items_raises_generic_exception(self, tmp_path):
        """
        JSON が dict のリストでない場合(例: 文字列のリスト)、
        d['model'] は TypeError となり、汎用の except Exception で
        捕捉される。
        """
        conf = make_bare_conf()
        conf.config_file = write_json(tmp_path / "conf.json", ["a", "b", "c"])

        result = conf.load()

        assert result == []
        assert conf.data == ["a", "b", "c"]
        assert conf.models == []

    def test_load_json_object_instead_of_list(self, tmp_path):
        """
        トップレベルが list ではなく dict の場合、
        `for d in self.data` は dict のキーを走査するため、
        d['model'] が TypeError(文字列インデックス)になり
        汎用 Exception で捕捉される。
        """
        conf = make_bare_conf()
        conf.config_file = write_json(tmp_path / "conf.json", {"model": "x"})

        result = conf.load()

        assert result == []
        assert conf.data == {"model": "x"}
        assert conf.models == []

    def test_load_unicode_decode_error_returns_empty_list(self, tmp_path):
        """UTF-8として不正なバイト列を含むファイルは UnicodeDecodeError になる"""
        conf = make_bare_conf()
        conf.config_file = tmp_path / "invalid_utf8.json"
        conf.config_file.write_bytes(b"\xff\xfe\x00\x01")

        result = conf.load()

        assert result == []
        assert conf.data == []
        assert conf.models == []

    def test_load_generic_exception_for_missing_file(self, tmp_path):
        """
        (通常は __init__ 側で存在チェックされるが)存在しないファイルを
        直接 load() すると FileNotFoundError が汎用 except Exception で
        捕捉され、[] が返る。
        """
        conf = make_bare_conf()
        conf.config_file = tmp_path / "no_such_file.json"

        result = conf.load()

        assert result == []


# ---------------------------------------------------------------------
# get() のテスト
# ---------------------------------------------------------------------

class TestGet:
    def test_get_returns_matching_entry(self, tmp_path):
        conf = make_bare_conf()
        conf.data = [
            {"model": "alpha", "value": 1},
            {"model": "beta", "value": 2},
        ]

        result = conf.get("beta")

        assert result == {"model": "beta", "value": 2}

    def test_get_returns_empty_dict_when_not_found(self):
        conf = make_bare_conf()
        conf.data = [{"model": "alpha", "value": 1}]

        result = conf.get("does_not_exist")

        assert result == {}

    def test_get_with_default_model_name(self):
        """引数を省略した場合、model_name='' として扱われる"""
        conf = make_bare_conf()
        conf.data = [{"model": "alpha"}]

        result = conf.get()

        assert result == {}

    def test_get_returns_first_match_when_duplicates_exist(self):
        conf = make_bare_conf()
        conf.data = [
            {"model": "dup", "value": "first"},
            {"model": "dup", "value": "second"},
        ]

        result = conf.get("dup")

        assert result == {"model": "dup", "value": "first"}

    def test_get_when_data_is_none_returns_empty_dict(self):
        """self.data が None の場合(通常経路では発生しないが)安全に {} を返す"""
        conf = make_bare_conf()
        conf.data = None

        result = conf.get("anything")

        assert result == {}

    def test_get_when_data_is_empty_list(self):
        conf = make_bare_conf()
        conf.data = []

        result = conf.get("anything")

        assert result == {}
