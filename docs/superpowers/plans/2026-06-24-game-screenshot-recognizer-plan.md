# 游戏截图内容识别工具 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个后台运行的截图识别工具，全局快捷键触发截图，OpenCV 多尺度模板匹配，结果弹窗按类别分组展示。

**Architecture:** 4 个 Python 文件 + 1 个 TOML 配置。单进程，Tkinter 主线程处理 GUI，pystray 守护线程托盘，pynput 守护线程监听快捷键。热键回调执行截图+匹配，通过 `root.after()` 将结果窗口调度到主线程。

**Tech Stack:** Python 3.11+, uv (包管理), OpenCV, Pillow, pynput, pystray, Tkinter (内置), tomllib (内置)

---

## 文件结构

```
show_island/
├── config.toml          # 用户可编辑的配置（含 19 条模板项）
├── config.py            # 配置加载器
├── screenshot.py        # 屏幕截图
├── matcher.py           # 多尺度模板匹配引擎
├── main.py              # 入口：托盘 + 热键 + 结果弹窗
├── templates/           # 模板图片目录
└── tests/
    ├── test_config.py   # 配置加载测试
    └── test_matcher.py  # 匹配引擎测试
```

---

### Task 1: 项目初始化与依赖

**Files:**
- Create: `config.toml`
- Create: `templates/.gitkeep`

- [ ] **Step 1: 创建 config.toml（含用户提供的真实数据）**

```toml
hotkey = "<ctrl>+<shift>+s"
threshold = 0.8
templates_dir = "templates"

# 首领传言
[[items]]
image = ""
text = "陨落的源头"
class = "首领传言"
map = "无名之岛"
content = "欧罗什：英雄悲剧珠宝，欧罗什的太阳徽记，破碎三曲"
rank = "B"

[[items]]
image = ""
text = "吞星者"
class = "首领传言"
map = "静谧神庙"
content = "乌崔德：魔力符文任务道具，乌特雷系列技能（待确认）"
rank = "B"

[[items]]
image = ""
text = "最后一个倒下"
class = "首领传言"
map = "恸哭悬崖"
content = "沃拉娜"
rank = ""

[[items]]
image = ""
text = "循环的尽头"
class = "首领传言"
map = "蔓生丛林"
content = "梅德维德：沃拉娜的围攻"
rank = "B"

# 炸坟岛传言
[[items]]
image = ""
text = "未知的废墟"
class = "炸坟岛传言"
map = "掘尸遗迹"
content = "免费日志"
rank = "A"

[[items]]
image = ""
text = "无尽的悬崖"
class = "炸坟岛传言"
map = "乱石半岛"
content = ""
rank = "B"

[[items]]
image = ""
text = "荒凉而可怕"
class = "炸坟岛传言"
map = "褪色浅滩"
content = ""
rank = "B"

[[items]]
image = ""
text = "肆意奔走的野性"
class = "炸坟岛传言"
map = "牧野荒原"
content = "小精灵"
rank = "B"

[[items]]
image = ""
text = "至少很干燥"
class = "炸坟岛传言"
map = "脱落沟壑"
content = ""
rank = "B"

[[items]]
image = ""
text = "亚硫酸！"
class = "炸坟岛传言"
map = "焦灼小岛"
content = ""
rank = "B"

[[items]]
image = ""
text = "有点可疑"
class = "炸坟岛传言"
map = "贫瘠环礁"
content = "保险箱"
rank = "B"

[[items]]
image = ""
text = "寒冷如冰"
class = "炸坟岛传言"
map = "凛风悬崖"
content = ""
rank = "B"

[[items]]
image = ""
text = "温暖但危险"
class = "炸坟岛传言"
map = "笼葱海岛"
content = ""
rank = "B"

[[items]]
image = ""
text = "没东西喝"
class = "炸坟岛传言"
map = "死水盆地"
content = ""
rank = "B"

# 传奇地图传言
[[items]]
image = ""
text = "一个好人"
class = "传奇地图传言"
map = "顿悟时刻"
content = "无名先知"
rank = "D"

[[items]]
image = ""
text = "倒映的水面"
class = "传奇地图传言"
map = "千裂泽"
content = "碎裂的魔镜"
rank = "D"

[[items]]
image = ""
text = "近乎天堂"
class = "传奇地图传言"
map = "纯净乐园"
content = "经验图"
rank = "B"

[[items]]
image = ""
text = "坠落的星辰"
class = "传奇地图传言"
map = "天陨荒原"
content = "8孔遗物"
rank = "S"

[[items]]
image = ""
text = "所有闪闪发光之物"
class = "传奇地图传言"
map = "颠沛领域"
content = "金币图"
rank = "A"
```

- [ ] **Step 2: 创建 templates 目录**

```bash
mkdir -p templates
```

- [ ] **Step 3: 安装 Python 依赖**

```bash
uv add opencv-python pillow pynput pystray
```

- [ ] **Step 4: 验证配置可被 Python tomllib 解析**

```bash
uv run python -c "import tomllib; data = tomllib.load(open('config.toml', 'rb')); print(f'加载 {len(data[\"items\"])} 条模板项')"
```
Expected: `加载 19 条模板项`

---

### Task 2: 配置加载模块

**Files:**
- Create: `config.py`
- Create: `tests/test_config.py`
- Create: `tests/fixtures/valid_config.toml`
- Create: `tests/fixtures/invalid_config.toml`

- [ ] **Step 1: 创建测试 fixtures — 有效配置**

Write `tests/fixtures/valid_config.toml`:

```toml
hotkey = "<ctrl>+<shift>+s"
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
```

- [ ] **Step 2: 创建测试 fixtures — 无效配置**

Write `tests/fixtures/invalid_config.toml`:

```toml
hotkey = 123
```

- [ ] **Step 3: 编写 config 模块的测试**

Write `tests/test_config.py`:

```python
import sys
import os
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import load_config


def test_load_valid_config():
    """加载有效配置文件，验证返回结构"""
    fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures')
    config_path = os.path.join(fixtures_dir, 'valid_config.toml')
    
    config = load_config(config_path)
    
    assert config['hotkey'] == '<ctrl>+<shift>+s'
    assert config['threshold'] == 0.85
    assert config['templates_dir'] == 'templates'
    assert len(config['items']) == 2
    assert config['items'][0]['text'] == '测试项目1'
    assert config['items'][0]['class'] == '测试类别'
    assert config['items'][0]['rank'] == 'S'


def test_load_config_missing_file():
    """配置文件不存在时抛出 FileNotFoundError"""
    with pytest.raises(FileNotFoundError):
        load_config('nonexistent.toml')


def test_load_config_default_path():
    """不传路径时默认加载 config.toml（项目根目录）"""
    # 此测试依赖项目根目录的 config.toml 存在
    config = load_config()
    assert 'hotkey' in config
    assert 'items' in config
    assert len(config['items']) >= 1


def test_item_fields_are_present():
    """每个 item 都包含 6 个必需字段"""
    config = load_config()
    for item in config['items']:
        for field in ('image', 'text', 'class', 'map', 'content', 'rank'):
            assert field in item, f"字段 {field} 缺失于 item: {item.get('text', '?')}"
```

- [ ] **Step 4: 运行测试，确认失败**

```bash
uv run pytest tests/test_config.py -v
```
Expected: 全部 FAIL（`config.py` 尚未创建）

- [ ] **Step 5: 实现 config.py**

Write `config.py`:

```python
"""配置加载模块 — 读取 TOML 格式的模板配置文件。"""
import tomllib
from pathlib import Path
from typing import Any


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
    if "items" not in data:
        raise ValueError("配置文件缺少 [[items]] 数组")

    if "hotkey" not in data:
        raise ValueError("配置文件缺少 hotkey 字段")

    data.setdefault("threshold", 0.8)
    data.setdefault("templates_dir", "templates")

    # 校验每个 item 的必填字段
    required_fields = ("image", "text", "class", "map", "content", "rank")
    for i, item in enumerate(data["items"]):
        for field in required_fields:
            if field not in item:
                raise ValueError(
                    f"items[{i}] 缺少必填字段 '{field}'（text='{item.get('text', '?')}'）"
                )

    return data
```

- [ ] **Step 6: 运行测试，确认通过**

```bash
uv run pytest tests/test_config.py -v
```
Expected: 全部 PASS

---

### Task 3: 截图模块

**Files:**
- Create: `screenshot.py`

- [ ] **Step 1: 实现 screenshot.py**

Write `screenshot.py`:

```python
"""截图模块 — 截取主屏幕全屏并转换为 OpenCV 格式。"""
import numpy as np
from PIL import ImageGrab


def capture_screen() -> np.ndarray:
    """截取主屏幕全屏。

    Returns:
        numpy array in BGR format (OpenCV compatible), shape (H, W, 3)
    """
    img = ImageGrab.grab(all_screens=False)  # 仅主屏幕
    # PIL Image (RGB) → numpy array → BGR for OpenCV
    return np.array(img)[:, :, ::-1].copy()
```

- [ ] **Step 2: 手动验证截图功能**

```bash
uv run python -c "from screenshot import capture_screen; import cv2; img = capture_screen(); print(f'截图尺寸: {img.shape}'); print('截图成功')"
```
Expected: 输出截图尺寸（如 `(1080, 1920, 3)`）和成功信息

---

### Task 4: 模板匹配引擎

**Files:**
- Create: `matcher.py`
- Create: `tests/test_matcher.py`

- [ ] **Step 1: 编写 matcher 模块的测试**

Write `tests/test_matcher.py`:

```python
import sys
import os
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from matcher import match_templates, _rank_sort_key


class TestRankSortKey:
    """rank 排序键测试"""
    
    def test_s_rank_is_highest(self):
        assert _rank_sort_key("S") < _rank_sort_key("A")
    
    def test_rank_order(self):
        ranks = ["D", "B", "", "S", "A", "C"]
        sorted_ranks = sorted(ranks, key=_rank_sort_key)
        assert sorted_ranks == ["S", "A", "B", "C", "D", ""]
    
    def test_lowercase_normalized(self):
        assert _rank_sort_key("s") == _rank_sort_key("S")
        assert _rank_sort_key("a") == _rank_sort_key("A")


class TestMatchTemplates:
    """模板匹配测试 — 使用合成图片"""
    
    @pytest.fixture
    def template(self):
        """创建一个 50x50 的白色方块模板"""
        img = np.ones((50, 50, 3), dtype=np.uint8) * 255
        return img
    
    @pytest.fixture
    def screenshot(self, template):
        """创建一个 500x500 的黑色背景，左上角放一个白色方块（与模板匹配）"""
        img = np.zeros((500, 500, 3), dtype=np.uint8)
        img[100:150, 200:250] = template  # 嵌入模板
        return img
    
    @pytest.fixture
    def items(self):
        return [
            {
                "image": "templates/white_square.png",
                "text": "白色方块",
                "class": "测试",
                "map": "测试地图",
                "content": "测试内容",
                "rank": "S",
            },
            {
                "image": "templates/nonexistent.png",
                "text": "不存在",
                "class": "测试",
                "map": "不存在地图",
                "content": "",
                "rank": "",
            },
        ]
    
    def test_match_finds_embedded_template(self, screenshot, items):
        """截图中嵌入的模板应该被匹配到"""
        # 将模板写入临时文件供 matcher 读取
        import cv2
        os.makedirs("templates", exist_ok=True)
        cv2.imwrite(items[0]["image"], np.ones((50, 50, 3), dtype=np.uint8) * 255)
        
        try:
            results = match_templates(screenshot, items, threshold=0.7)
            assert len(results) == 1
            assert results[0]["text"] == "白色方块"
        finally:
            os.remove(items[0]["image"])
    
    def test_match_skips_missing_template(self, screenshot, items):
        """不存在的模板图片应被跳过"""
        results = match_templates(screenshot, items[1:], threshold=0.7)
        assert len(results) == 0
    
    def test_match_empty_screenshot_returns_empty(self, items):
        """空（全黑）截图不应匹配到任何模板"""
        import cv2
        os.makedirs("templates", exist_ok=True)
        cv2.imwrite(items[0]["image"], np.ones((50, 50, 3), dtype=np.uint8) * 255)
        
        try:
            black_screen = np.zeros((500, 500, 3), dtype=np.uint8)
            results = match_templates(black_screen, items[:1], threshold=0.7)
            assert len(results) == 0
        finally:
            os.remove(items[0]["image"])
    
    def test_deduplication(self, screenshot, items):
        """同一模板多次出现只报告一次"""
        import cv2
        os.makedirs("templates", exist_ok=True)
        template_img = np.ones((50, 50, 3), dtype=np.uint8) * 255
        cv2.imwrite(items[0]["image"], template_img)
        
        # 在截图中嵌入两个相同的模板
        dup_screenshot = np.zeros((500, 500, 3), dtype=np.uint8)
        dup_screenshot[50:100, 50:100] = template_img
        dup_screenshot[300:350, 300:350] = template_img
        
        try:
            results = match_templates(dup_screenshot, items[:1], threshold=0.7)
            assert len(results) == 1
        finally:
            os.remove(items[0]["image"])
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
uv run pytest tests/test_matcher.py -v
```
Expected: 全部 FAIL（`matcher.py` 尚未创建）

- [ ] **Step 3: 实现 matcher.py**

Write `matcher.py`:

```python
"""模板匹配引擎 — 多尺度 OpenCV 模板匹配，去重。"""
import logging
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# 多尺度搜索范围
SCALE_RANGE = (0.5, 2.0)
SCALE_STEPS = 10  # 在范围内采样 10 个尺度

# rank 排序映射（S 最高，空值最低）
RANK_ORDER: dict[str, int] = {
    "S": 0,
    "A": 1,
    "B": 2,
    "C": 3,
    "D": 4,
    "": 99,  # 空 rank 排最后
}


def _rank_sort_key(rank: str) -> int:
    """rank 字符串转为排序键值。"""
    return RANK_ORDER.get(rank.upper(), 99)


def _load_template(image_path: str) -> np.ndarray | None:
    """加载模板图片。失败返回 None。"""
    path = Path(image_path)
    if not path.exists():
        logger.warning("模板图片不存在，跳过: %s", image_path)
        return None
    img = cv2.imread(str(path))
    if img is None:
        logger.warning("无法读取模板图片，跳过: %s", image_path)
        return None
    return img


def _match_single_template(
    screenshot: np.ndarray,
    template: np.ndarray,
    threshold: float,
) -> bool:
    """对单个模板执行多尺度匹配。

    在 0.5x ~ 2.0x 范围内缩放模板，任一级别相似度 >= threshold 即视为命中。

    Args:
        screenshot: 截图 (H, W, 3) BGR
        template: 模板 (H, W, 3) BGR
        threshold: 相似度阈值

    Returns:
        True 如果匹配成功
    """
    th, tw = template.shape[:2]
    sh, sw = screenshot.shape[:2]

    # 模板比截图还大，无法匹配
    if th > sh or tw > sw:
        return False

    scales = np.linspace(SCALE_RANGE[0], SCALE_RANGE[1], SCALE_STEPS)

    for scale in scales:
        new_w = int(tw * scale)
        new_h = int(th * scale)

        if new_w < 10 or new_h < 10:
            continue
        if new_w > sw or new_h > sh:
            continue

        scaled = cv2.resize(template, (new_w, new_h))
        result = cv2.matchTemplate(screenshot, scaled, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)

        if max_val >= threshold:
            return True

    return False


def match_templates(
    screenshot: np.ndarray,
    items: list[dict],
    threshold: float = 0.8,
) -> list[dict]:
    """对截图执行所有模板的多尺度匹配，返回去重命中的模板项。

    Args:
        screenshot: 截图 numpy array (H, W, 3) BGR
        items: 模板项列表，每项含 image/text/class/map/content/rank
        threshold: 匹配相似度阈值

    Returns:
        命中的模板项列表（按 image 去重，每个模板只出现一次）
    """
    matched: list[dict] = []
    seen_images: set[str] = set()

    for item in items:
        image_path = item["image"]

        # 跳过空路径或已命中的模板
        if not image_path or image_path in seen_images:
            continue

        template = _load_template(image_path)
        if template is None:
            continue

        if _match_single_template(screenshot, template, threshold):
            matched.append(item)
            seen_images.add(image_path)

    return matched


def sort_results(items: list[dict]) -> list[dict]:
    """对匹配结果排序：先按 class 分组，组内按 rank 排序。"""
    # rank 排序: S > A > B > C > D > 空
    return sorted(items, key=lambda x: (x["class"], _rank_sort_key(x["rank"])))
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
uv run pytest tests/test_matcher.py -v
```
Expected: 全部 PASS

---

### Task 5: 主程序 — 托盘 + 快捷键 + 结果弹窗

**Files:**
- Create: `main.py`

- [ ] **Step 1: 实现 main.py**

Write `main.py`:

```python
"""游戏截图内容识别工具 — 主入口。

托盘常驻后台，全局快捷键触发截图识别，弹窗显示汇总结果。
"""
import logging
import queue
import threading

from pynput import keyboard
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw
import tkinter as tk
from tkinter import ttk

from config import load_config
from screenshot import capture_screen
from matcher import match_templates, sort_results

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ── 托盘图标生成 ─────────────────────────────────────────────

def _create_tray_image() -> Image.Image:
    """生成一个简单的 64x64 托盘图标（绿底白色十字准星）。"""
    img = Image.new("RGBA", (64, 64), (0, 128, 0, 255))
    draw = ImageDraw.Draw(img)
    # 外圈
    draw.ellipse([4, 4, 59, 59], outline="white", width=3)
    # 十字线
    draw.line([32, 16, 32, 48], fill="white", width=2)
    draw.line([16, 32, 48, 32], fill="white", width=2)
    return img


# ── 结果弹窗 ──────────────────────────────────────────────────

def show_result_window(matched: list[dict]) -> None:
    """弹出 Tkinter 窗口，按 class 分组、rank 排序显示匹配结果。"""
    root = tk.Tk()
    root.title("截图识别结果")
    root.attributes("-topmost", True)

    # 窗口居中
    win_w, win_h = 720, 400
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    x = (screen_w - win_w) // 2
    y = (screen_h - win_h) // 2
    root.geometry(f"{win_w}x{win_h}+{x}+{y}")

    # 标题
    header = ttk.Label(
        root,
        text=f"识别到 {len(matched)} 项内容",
        font=("Microsoft YaHei UI", 14, "bold"),
    )
    header.pack(pady=(12, 8))

    # 表格框架
    frame = ttk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

    columns = ("text", "class", "map", "content", "rank")
    col_headers = {
        "text": "文字",
        "class": "类别",
        "map": "地图",
        "content": "内容",
        "rank": "推荐等级",
    }
    col_widths = {"text": 130, "class": 90, "map": 110, "content": 260, "rank": 70}

    tree = ttk.Treeview(frame, columns=columns, show="headings", height=12)

    for col in columns:
        tree.heading(col, text=col_headers[col])
        tree.column(col, width=col_widths[col], anchor="center")

    # 滚动条
    scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # 排序后填充数据
    sorted_items = sort_results(matched)
    
    # 用 tag 区分不同 class 的行颜色
    class_colors: dict[str, str] = {}
    color_pool = ("#FFFFFF", "#F0F5FF")
    prev_class = None
    color_idx = -1
    
    for item in sorted_items:
        cls = item["class"]
        if cls != prev_class:
            color_idx += 1
            prev_class = cls
        bg = color_pool[color_idx % 2]
        class_colors[cls] = bg
        
        tree.insert(
            "",
            tk.END,
            values=(
                item["text"],
                item["class"],
                item["map"],
                item["content"],
                item["rank"],
            ),
            tags=(cls,),
        )
    
    for cls, bg in class_colors.items():
        tree.tag_configure(cls, background=bg)

    # 关闭按钮
    ttk.Button(root, text="关闭", command=root.destroy).pack(pady=(0, 12))

    root.mainloop()


# ── 截图 & 识别流程 ───────────────────────────────────────────

def on_hotkey(config: dict, result_queue: queue.Queue):
    """快捷键回调：截图 → 匹配 → 将结果放入队列。"""
    def callback():
        logger.info("快捷键触发，开始截图...")
        try:
            screenshot = capture_screen()
            logger.info("截图成功，尺寸: %s", screenshot.shape)
        except Exception as e:
            logger.error("截图失败: %s", e)
            result_queue.put({"error": f"截图失败: {e}"})
            return

        logger.info("开始模板匹配（%d 个模板）...", len(config["items"]))
        try:
            matched = match_templates(
                screenshot, config["items"], config["threshold"]
            )
            logger.info("匹配完成，命中 %d 项", len(matched))
            result_queue.put({"matched": matched})
        except Exception as e:
            logger.error("匹配失败: %s", e)
            result_queue.put({"error": f"匹配失败: {e}"})

    return callback


# ── 主入口 ────────────────────────────────────────────────────

def main():
    logger.info("加载配置...")
    config = load_config()

    result_queue: queue.Queue = queue.Queue()

    # 解析快捷键字符串（pynput 格式，如 "<ctrl>+<shift>+s"）
    hotkey = config["hotkey"]
    logger.info("注册全局快捷键: %s", hotkey)

    # 创建托盘图标
    tray_image = _create_tray_image()
    tray_icon = Icon(
        "screenshot_recognizer",
        tray_image,
        "截图识别工具",
        menu=Menu(MenuItem("退出", lambda icon, item: icon.stop())),
    )

    # 托盘运行在守护线程
    tray_thread = threading.Thread(target=tray_icon.run, daemon=True)
    tray_thread.start()
    logger.info("托盘已启动")

    # 轮询结果队列，在主线程中弹出结果窗口
    def poll_queue():
        try:
            while True:
                data = result_queue.get_nowait()
                if "error" in data:
                    # 错误弹窗
                    err_win = tk.Toplevel()
                    err_win.title("错误")
                    err_win.attributes("-topmost", True)
                    err_win.geometry("300x100")
                    ttk.Label(err_win, text=data["error"], padding=20).pack()
                    ttk.Button(err_win, text="关闭", command=err_win.destroy).pack()
                elif "matched" in data:
                    matched = data["matched"]
                    if not matched:
                        # 无匹配结果
                        info_win = tk.Toplevel()
                        info_win.title("提示")
                        info_win.attributes("-topmost", True)
                        info_win.geometry("300x100")
                        ttk.Label(
                            info_win, text="未识别到任何内容", font=("Microsoft YaHei UI", 12), padding=20
                        ).pack()
                        ttk.Button(info_win, text="关闭", command=info_win.destroy).pack()
                    else:
                        show_result_window(matched)
        except queue.Empty:
            pass
        # 每 500ms 检查一次队列
        root.after(500, poll_queue)

    # 创建隐藏的 Tkinter 根窗口（用于消息循环）
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口

    # 启动队列轮询
    root.after(500, poll_queue)

    # 启动全局热键监听（守护线程）
    listener = keyboard.GlobalHotKeys({
        hotkey: on_hotkey(config, result_queue),
    })
    listener.start()
    logger.info("热键监听已启动，按 %s 触发截图识别", hotkey)

    try:
        root.mainloop()
    finally:
        listener.stop()
        tray_icon.stop()
        logger.info("程序退出")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 手动启动验证**

```bash
uv run python main.py
```
Expected: 托盘出现绿色图标，按 Ctrl+Shift+S 截图识别（当前无模板图片故会显示"未识别到任何内容"），托盘右键"退出"可关闭程序。

---

### Task 6: 端到端集成验证

- [ ] **Step 1: 制作测试模板图片**

取一个已知会在屏幕上出现的小图标（如 Windows 开始按钮或桌面快捷方式），截取保存到 `templates/` 目录。

- [ ] **Step 2: 在 config.toml 中添加该模板项**

```toml
[[items]]
image = "templates/test_icon.png"
text = "测试图标"
class = "测试"
map = "桌面"
content = "Windows 图标"
rank = "S"
```

- [ ] **Step 3: 运行程序，快捷键触发，验证弹窗正确显示匹配结果**

预期：结果弹窗置顶显示，表格包含"测试图标"项，class 分组正确，按 rank 排序。

- [ ] **Step 4: 关闭结果窗口，确认程序仍在后台运行，快捷键仍可再次触发**

预期：关闭结果窗口后托盘图标仍在，再次按快捷键仍会截图识别。

---

## 自审清单

1. **Spec 覆盖**：
   - ✅ 配置文件加载（Task 2）— `config.py` + `tomllib`
   - ✅ 全屏截图（Task 3）— `screenshot.py` + Pillow
   - ✅ 多尺度模板匹配 + 去重（Task 4）— `matcher.py` + OpenCV
   - ✅ 托盘常驻 + 全局快捷键（Task 5）— `main.py` + pystray + pynput
   - ✅ Tkinter 结果弹窗（Task 5）— Treeview 表格
   - ✅ class 分组 + rank 排序（Task 4 `sort_results` + Task 5 Treeview）
   - ✅ 不显示 image 字段（Task 5 Treeview 列定义）
   - ✅ 错误处理：模板缺失/截图失败/无匹配/配置错误（各模块）

2. **占位符扫描**：无 TBD/TODO，所有步骤包含实际代码。

3. **类型一致性**：`load_config()` 返回 dict，`match_templates()` 接收 list[dict] 返回 list[dict]，`sort_results()` 接收 list[dict] 返回 list[dict]，接口一致。
