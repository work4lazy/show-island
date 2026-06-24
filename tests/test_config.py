"""配置加载模块测试。"""
from pathlib import Path

import pytest

from show_island.config import load_config, REQUIRED_ITEM_FIELDS, DEFAULT_THRESHOLD, DEFAULT_TEMPLATES_DIR

VALID_CONFIG_CONTENT = """hotkey = "<ctrl>+<shift>+s"
threshold = 0.85
templates_dir = "templates"

[[items]]
image = "templates/test1.png"
text = "测试项目1"
class = "测试类别"
map = "测试地图"
content = "测试内容"
rank = "S"

[[items]]
image = "templates/test2.png"
text = "测试项目2"
class = "测试类别"
map = "测试地图2"
content = ""
rank = "A"
"""


def _write_config(path: Path, content: str) -> Path:
    """辅助函数：写入临时配置文件。"""
    path.write_text(content, encoding="utf-8")
    return path


class TestLoadValidConfig:
    """加载有效配置文件的测试。"""

    def test_returns_all_fields(self, tmp_path: Path):
        """验证返回结构包含所有顶级字段。"""
        config_path = _write_config(tmp_path / "config.toml", VALID_CONFIG_CONTENT)
        config = load_config(str(config_path))

        assert config['hotkey'] == '<ctrl>+<shift>+s'
        assert config['threshold'] == 0.85
        assert config['templates_dir'] == 'templates'
        assert len(config['items']) == 2

    def test_item_fields_are_correct(self, tmp_path: Path):
        """验证 item 的各个字段值正确。"""
        config_path = _write_config(tmp_path / "config.toml", VALID_CONFIG_CONTENT)
        config = load_config(str(config_path))

        assert config['items'][0]['text'] == '测试项目1'
        assert config['items'][0]['class'] == '测试类别'
        assert config['items'][0]['rank'] == 'S'
        assert config['items'][1]['content'] == ''


class TestDefaultValues:
    """默认值测试。"""

    def test_default_threshold(self, tmp_path: Path):
        """threshold 缺失时应使用默认值 0.8。"""
        content = """hotkey = "<ctrl>+<shift>+s"
[[items]]
image = ""
text = "测试"
class = "分类"
map = "地图"
content = ""
rank = ""
"""
        config_path = _write_config(tmp_path / "config.toml", content)
        config = load_config(str(config_path))
        assert config['threshold'] == DEFAULT_THRESHOLD

    def test_default_templates_dir(self, tmp_path: Path):
        """templates_dir 缺失时应使用默认值 "templates"。"""
        content = """hotkey = "<ctrl>+<shift>+s"
[[items]]
image = ""
text = "测试"
class = "分类"
map = "地图"
content = ""
rank = ""
"""
        config_path = _write_config(tmp_path / "config.toml", content)
        config = load_config(str(config_path))
        assert config['templates_dir'] == DEFAULT_TEMPLATES_DIR


class TestErrorHandling:
    """错误处理测试。"""

    def test_missing_file_raises(self):
        """配置文件不存在时抛出 FileNotFoundError。"""
        with pytest.raises(FileNotFoundError):
            load_config('nonexistent.toml')

    def test_missing_items_raises(self, tmp_path: Path):
        """配置缺少 items 时抛出 ValueError。"""
        content = 'hotkey = "<ctrl>+<shift>+s"\n'
        config_path = _write_config(tmp_path / "config.toml", content)
        with pytest.raises(ValueError, match="缺少.*items"):
            load_config(str(config_path))

    def test_items_not_list_raises(self, tmp_path: Path):
        """items 不是数组时抛出 ValueError。"""
        content = 'hotkey = "<ctrl>+<shift>+s"\nitems = "not a list"\n'
        config_path = _write_config(tmp_path / "config.toml", content)
        with pytest.raises(ValueError, match="不是数组"):
            load_config(str(config_path))

    def test_missing_hotkey_raises(self, tmp_path: Path):
        """配置缺少 hotkey 时抛出 ValueError。"""
        content = """[[items]]
image = ""
text = "测试"
class = "分类"
map = "地图"
content = ""
rank = ""
"""
        config_path = _write_config(tmp_path / "config.toml", content)
        with pytest.raises(ValueError, match="缺少 hotkey"):
            load_config(str(config_path))

    def test_item_missing_field_raises(self, tmp_path: Path):
        """item 缺少必填字段时抛出 ValueError。"""
        content = """hotkey = "<ctrl>+<shift>+s"
[[items]]
image = ""
text = "测试"
"""
        config_path = _write_config(tmp_path / "config.toml", content)
        with pytest.raises(ValueError, match="缺少必填字段"):
            load_config(str(config_path))


    def test_item_not_dict_raises(self, tmp_path: Path):
        """items 内元素不是对象时抛出 ValueError。"""
        content = 'hotkey = "<ctrl>+<shift>+s"\nitems = [1, 2, 3]\n'
        config_path = _write_config(tmp_path / "config.toml", content)
        with pytest.raises(ValueError, match="必须是对象"):
            load_config(str(config_path))


@pytest.mark.skipif(
    not Path("config.toml").exists(),
    reason="集成测试需要项目根目录的 config.toml"
)
class TestRealConfig:
    """对项目根 config.toml 的集成测试。"""

    def test_loads_without_error(self):
        """默认路径 config.toml 应能正常加载。"""
        config = load_config()
        assert 'hotkey' in config
        assert 'items' in config
        assert len(config['items']) >= 1

    def test_all_items_have_required_fields(self):
        """每个 item 都包含所有必需字段。"""
        config = load_config()
        for i, item in enumerate(config['items']):
            for field in REQUIRED_ITEM_FIELDS:
                assert field in item, f"items[{i}] 缺少字段 '{field}'（text='{item.get('text', '?')}'）"


def test_required_fields_constant():
    """REQUIRED_ITEM_FIELDS 模块常量包含 6 个字段。"""
    assert len(REQUIRED_ITEM_FIELDS) == 6
    assert 'image' in REQUIRED_ITEM_FIELDS
    assert 'text' in REQUIRED_ITEM_FIELDS
    assert 'class' in REQUIRED_ITEM_FIELDS
    assert 'map' in REQUIRED_ITEM_FIELDS
    assert 'content' in REQUIRED_ITEM_FIELDS
    assert 'rank' in REQUIRED_ITEM_FIELDS
