"""配置加载模块 — 读取 TOML 格式的模板配置文件。"""
import tomllib
from pathlib import Path
from typing import Any

DEFAULT_THRESHOLD = 0.8
DEFAULT_TEMPLATES_DIR = "templates"
REQUIRED_ITEM_FIELDS = ("image", "text", "class", "map", "content", "rank")


def load_config(path: str | Path = "config.toml") -> dict[str, Any]:
    """加载并校验配置文件。

    Args:
        path: TOML 配置文件路径，默认为项目根目录下的 config.toml

    Returns:
        dict with keys: hotkey, threshold, templates_dir, items

    Raises:
        FileNotFoundError: 配置文件不存在
        ValueError: 配置格式错误
    """
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    # 校验必填字段
    if "items" not in data or not isinstance(data["items"], list):
        raise ValueError("配置文件缺少 [[items]] 数组，或 items 不是数组类型")

    if "hotkey" not in data:
        raise ValueError("配置文件缺少 hotkey 字段")

    data.setdefault("threshold", DEFAULT_THRESHOLD)
    data.setdefault("templates_dir", DEFAULT_TEMPLATES_DIR)

    # 校验每个 item 的必填字段
    for i, item in enumerate(data["items"]):
        if not isinstance(item, dict):
            raise ValueError(
                f"items[{i}] 必须是对象，实际类型为 {type(item).__name__}"
            )
        for field in REQUIRED_ITEM_FIELDS:
            if field not in item:
                raise ValueError(
                    f"items[{i}] 缺少必填字段 '{field}'（text='{item.get('text', '?')}'）"
                )

    return data
