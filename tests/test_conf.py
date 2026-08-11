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
from pathlib import Path

import pytest

from ytstreetorgan.conf import (
    NOTE_NAMES,
    NUMERIC_FIELDS,
    Conf,
    coerce_numeric_fields,
    midi_to_note_name,
    note_name_to_midi,
    note_offsets,
    validate_config,
)

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

    def test_not_found_message_lists_where_it_looked(self, isolated_search_path):
        """探した場所が分かること。

        名前だけだと、どこに設定を置けばよいのか分からないまま
        「見つかりません」とだけ言われることになる。
        """
        with pytest.raises(FileNotFoundError) as excinfo:
            Conf(config_file="")

        msg = str(excinfo.value)
        for dir_path in isolated_search_path:
            assert str(dir_path / Conf.CONF_FNAME) in msg

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

    def test_empty_config_file_is_loaded_as_empty(self, tmp_path):
        """中身が空リストの設定でも、そのまま読み込めること"""
        conf_file = write_json(tmp_path / "my_conf.json", [])

        conf = Conf(config_file=str(conf_file))

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


# ---------------------------------------------------------------------
# validate_config() のテスト
# ---------------------------------------------------------------------

class TestValidateConfig:
    def test_valid_config(self):
        sample = {
            "model": "test_model",
            "book_height": 100,
            "margin": 5,
            "pitch": 3.5,
            "hole_height": 2.5,
            "mm_per_sec": 50,
            "notes": ["C4", "D4"],
            "base_note": 60,
            "bridge_width": 1,
            "bridge_threshold": 50,
            "memo": "sample"
        }
        valid, msg = validate_config(sample)
        assert valid is True
        assert msg == ""

    def test_invalid_type(self):
        valid, msg = validate_config("not a dict")
        assert valid is False
        assert "オブジェクト" in msg

    def test_missing_model(self):
        sample = {"book_height": 100}
        valid, msg = validate_config(sample)
        assert valid is False
        assert "機種名は必須" in msg

    def test_missing_numeric_field(self):
        sample = {
            "model": "test_model",
            "margin": 5,
        }
        valid, msg = validate_config(sample)
        assert valid is False
        assert "必須項目" in msg

    def test_invalid_numeric_field(self):
        sample = {
            "model": "test_model",
            "book_height": "abc",
            "margin": 5, "pitch": 3.5, "hole_height": 2.5, "mm_per_sec": 50,
            "base_note": 60,
            "bridge_width": 1,
            "bridge_threshold": 50,
            "notes": ["C4"]
        }
        valid, msg = validate_config(sample)
        assert valid is False
        assert "数値である必要" in msg

    def test_int_field_rejects_non_integer_string(self):
        # 'base_note' は int で変換される。float() で検証していた頃は
        # "60.5" が検証を通り、あとの int() で ValueError になっていた。
        sample = {
            "model": "test_model",
            "book_height": 100,
            "margin": 5, "pitch": 3.5, "hole_height": 2.5, "mm_per_sec": 50,
            "base_note": "60.5",
            "bridge_width": 1,
            "bridge_threshold": 50,
            "notes": ["C4"]
        }
        valid, msg = validate_config(sample)
        assert valid is False
        assert "'base_note'" in msg

    # 'notes' は音名の文字列の並び。音名は国際標準
    # （MIDI ノート番号 60 = 'C4'）で、オクターブ番号まで必須。
    # 壊れ方ごとに、どの要素が悪いのか（1 始まりの番号）が分かること。
    @pytest.mark.parametrize("bad_note, expected", [
        (60, "音名の文字列である必要"),
        (None, "音名の文字列である必要"),
        # オクターブ番号が無い（旧形式の書き方）
        ("C", "音名として読めません"),
        # フラット表記は受け付けない
        ("Db4", "音名として読めません"),
        ("H4", "音名として読めません"),
        ("", "音名として読めません"),
        # MIDI ノート番号の範囲から外れる
        ("C-2", "範囲"),
        ("A9", "範囲"),
    ])
    def test_invalid_note_item(self, bad_note, expected):
        sample = {
            "model": "test_model",
            "book_height": 100,
            "margin": 5,
            "pitch": 3.5,
            "hole_height": 2.5,
            "mm_per_sec": 50,
            "base_note": 60,
            "bridge_width": 1,
            "bridge_threshold": 50,
            "notes": ["C4", bad_note]
        }
        valid, msg = validate_config(sample)
        assert valid is False
        assert "2 番目" in msg
        assert expected in msg

    # 辞書はどちらの書き方でも旧形式として弾く（自動変換もしない）
    @pytest.mark.parametrize("old_note", [
        {"name": "D4", "offset": 2},
        {"name": "D4"},
        {},
    ])
    def test_old_style_note_is_rejected(self, old_note):
        sample = {
            "model": "test_model",
            "book_height": 100,
            "margin": 5,
            "pitch": 3.5,
            "hole_height": 2.5,
            "mm_per_sec": 50,
            "base_note": 60,
            "bridge_width": 1,
            "bridge_threshold": 50,
            "notes": ["C4", old_note]
        }
        valid, msg = validate_config(sample)
        assert valid is False
        assert "2 番目" in msg
        assert "旧形式" in msg

    @pytest.mark.parametrize("name", [
        "C-1", "C4", "C#4", "A#0", "G9", " C4 ",
    ])
    def test_valid_note_names(self, name):
        sample = {
            "model": "test_model",
            "book_height": 100,
            "margin": 5,
            "pitch": 3.5,
            "hole_height": 2.5,
            "mm_per_sec": 50,
            "base_note": 60,
            "bridge_width": 1,
            "bridge_threshold": 50,
            "notes": [name]
        }
        valid, msg = validate_config(sample)
        assert valid is True, msg

    def test_notes_must_be_a_list(self):
        sample = {
            "model": "test_model",
            "book_height": 100,
            "margin": 5,
            "pitch": 3.5,
            "hole_height": 2.5,
            "mm_per_sec": 50,
            "base_note": 60,
            "bridge_width": 1,
            "bridge_threshold": 50,
            "notes": "C4"
        }
        valid, msg = validate_config(sample)
        assert valid is False
        assert "'notes' は" in msg


# ---------------------------------------------------------------------
# save(), update_model(), add_model(), delete_model() のテスト
# ---------------------------------------------------------------------

class TestConfMutations:
    @pytest.fixture
    def sample_conf_file(self, tmp_path):
        data = [
            {
                "model": "m1",
                "book_height": 100,
                "margin": 5,
                "pitch": 3.5,
                "hole_height": 2.5,
                "mm_per_sec": 50,
                "base_note": 60,
                "bridge_width": 1,
                "bridge_threshold": 50,
                "notes": ["C4"], "memo": "m1 memo"
            }
        ]
        file_path = tmp_path / "storgan-conf.json"
        write_json(file_path, data)
        return file_path

    def test_save_and_backup(self, sample_conf_file):
        conf = Conf(config_file=str(sample_conf_file))
        conf.data[0]["memo"] = "updated memo"
        ok, msg = conf.save()

        assert ok is True
        # Check main file
        reloaded = Conf(config_file=str(sample_conf_file))
        assert reloaded.get("m1")["memo"] == "updated memo"

        # Check backup file
        bak_file = sample_conf_file.with_name(sample_conf_file.name + ".bak")
        assert bak_file.exists()

    def test_update_model_success(self, sample_conf_file):
        conf = Conf(config_file=str(sample_conf_file))
        updated = dict(conf.get("m1"))
        updated["memo"] = "new memo"
        ok, msg = conf.update_model("m1", updated)

        assert ok is True
        assert conf.get("m1")["memo"] == "new memo"

    def test_update_model_not_found(self, sample_conf_file):
        conf = Conf(config_file=str(sample_conf_file))
        updated = dict(conf.get("m1"))
        ok, msg = conf.update_model("non_existent", updated)

        assert ok is False
        assert "見つかりません" in msg

    def test_add_model_success(self, sample_conf_file):
        conf = Conf(config_file=str(sample_conf_file))
        new_model = {
            "model": "m2",
            "book_height": 120,
            "margin": 6,
            "pitch": 3.5,
            "hole_height": 2.5,
            "mm_per_sec": 50,
            "base_note": 60,
            "bridge_width": 1,
            "bridge_threshold": 50,
            "notes": ["D4"], "memo": "m2 memo"
        }
        ok, msg = conf.add_model(new_model)

        assert ok is True
        assert "m2" in conf.models
        assert conf.get("m2")["book_height"] == 120.0

    def test_add_model_duplicate(self, sample_conf_file):
        conf = Conf(config_file=str(sample_conf_file))
        duplicate = dict(conf.get("m1"))
        ok, msg = conf.add_model(duplicate)

        assert ok is False
        assert "既に存在" in msg

    def test_delete_model_success(self, sample_conf_file):
        conf = Conf(config_file=str(sample_conf_file))
        ok, msg = conf.delete_model("m1")

        assert ok is True
        assert "m1" not in conf.models
        assert conf.get("m1") == {}

    def test_delete_model_not_found(self, sample_conf_file):
        conf = Conf(config_file=str(sample_conf_file))
        ok, msg = conf.delete_model("not_found")

        assert ok is False
        assert "見つかりません" in msg



# ============================================================
# coerce_numeric_fields() のテスト
# ============================================================
class TestCoerceNumericFields:
    SAMPLE = {
        "model": "test_model",
        "book_height": "100", "margin": "5", "pitch": "3.5",
        "hole_height": "2.5", "mm_per_sec": "50",
        "base_note": "60",
        "bridge_width": "1", "bridge_threshold": "50",
        "notes": ["C4", " D4 "],
        "memo": "keep me",
    }

    def test_casts_to_declared_types(self):
        out = coerce_numeric_fields(self.SAMPLE)

        for field, cast in NUMERIC_FIELDS.items():
            assert type(out[field]) is cast, field
        # 音名の文字列だけが残り、前後の空白は取り除かれる
        assert out["notes"] == ["C4", "D4"]

    def test_does_not_mutate_input(self):
        original = dict(self.SAMPLE)
        coerce_numeric_fields(self.SAMPLE)
        assert self.SAMPLE == original

    def test_passes_through_unknown_keys(self):
        out = coerce_numeric_fields({**self.SAMPLE, "unknown_field": 10})
        # 未知のキー（手で足したものなど）は素通りさせる
        assert out["memo"] == "keep me"
        assert out["unknown_field"] == 10
        assert out["notes"] == ["C4", "D4"]

    def test_covers_every_validated_numeric_field(self):
        # validate_config() が必須にする数値項目と、変換対象が一致すること
        out = coerce_numeric_fields(self.SAMPLE)
        assert set(NUMERIC_FIELDS) <= set(out)

    def test_notes_become_plain_strings(self):
        # 数値が混ざっていても文字列に直す（validate_config() は弾く形だが、
        # ここは「変換した写しを返す」ことだけを見る）
        sample = {**self.SAMPLE, "notes": ["C4", 60]}
        out = coerce_numeric_fields(sample)
        assert out["notes"] == ["C4", "60"]


# ============================================================
# 音名 ↔ MIDI ノート番号
# ============================================================
class TestNoteNames:
    def test_note_names_are_twelve_sharps(self):
        assert len(NOTE_NAMES) == 12
        assert NOTE_NAMES[0] == 'C'
        assert NOTE_NAMES[-1] == 'B'
        assert 'b' not in ''.join(NOTE_NAMES)  # フラット表記は使わない

    @pytest.mark.parametrize("name, midi", [
        ("C-1", 0),
        ("C4", 60),      # 国際標準（MIDI ノート番号 60 = C4）
        ("F4", 65),
        ("A4", 69),
        ("C#4", 61),
        ("G9", 127),
        ("F2", 41),      # '34notes' の base_note
        ("G2", 43),      # '20notes' の base_note
    ])
    def test_round_trip(self, name, midi):
        assert note_name_to_midi(name) == midi
        assert midi_to_note_name(midi) == name

    def test_all_midi_notes_round_trip(self):
        for midi in range(128):
            assert note_name_to_midi(midi_to_note_name(midi)) == midi

    @pytest.mark.parametrize("name", [
        "C",      # オクターブ番号が無い（旧形式）
        "Db4",    # フラット表記
        "H4",
        "c4",
        "",
        "C 4",
        "C4x",
        60,
    ])
    def test_note_name_to_midi_rejects(self, name):
        with pytest.raises(ValueError):
            note_name_to_midi(name)

    @pytest.mark.parametrize("name", ["C-2", "G#9", "B9"])
    def test_note_name_to_midi_rejects_out_of_range(self, name):
        with pytest.raises(ValueError, match="範囲"):
            note_name_to_midi(name)

    @pytest.mark.parametrize("midi", [-1, 128, "60", 60.0])
    def test_midi_to_note_name_rejects(self, midi):
        with pytest.raises(ValueError):
            midi_to_note_name(midi)


# ============================================================
# note_offsets()
# ============================================================
class TestNoteOffsets:
    def test_offsets_from_base_note(self):
        model = {
            "base_note": 41,
            "notes": ["F2", "G2", "A#2"],
        }
        assert note_offsets(model) == [0, 2, 5]

    def test_offsets_can_be_negative(self):
        # 基準の音より低い音名でも導出できる
        model = {"base_note": 60, "notes": ["A3"]}
        assert note_offsets(model) == [-3]

    def test_empty(self):
        assert note_offsets({"base_note": 60, "notes": []}) == []
        assert note_offsets({}) == []

    def test_invalid_name_raises(self):
        with pytest.raises(ValueError):
            note_offsets({"base_note": 60, "notes": ["C"]})

    def test_template_conf_offsets(self):
        # テンプレートの設定が新形式で読めること
        data = json.loads(
            Path("conf/storgan-conf.json").read_text(encoding="utf-8")
        )
        for model in data:
            offsets = note_offsets(model)
            assert len(offsets) == len(model["notes"])
            assert offsets == sorted(offsets)  # 低い音から並んでいる
            valid, msg = validate_config(model)
            assert valid is True, f'{model["model"]}: {msg}'
