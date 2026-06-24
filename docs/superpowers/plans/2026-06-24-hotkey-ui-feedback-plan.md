# 快捷键即时反馈 UI + 文件结构整理 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 快捷键触发后立即弹窗提示"匹配中"，匹配完成后原地切换为结果表格；整理代码入 `src/show_island/` 包。

**Architecture:** pynput 线程处理截图+匹配，通过 `queue.Queue` 向 Tkinter 主线程发送 `matching`/`done`/`error` 事件，主线程 `poll_queue` 驱动 ResultWindow 的三态转换。所有 UI 操作在主线程完成，保证线程安全。

**Tech Stack:** Python 3.11+, Tkinter, pynput, pystray, OpenCV, Pillow

## Global Constraints

- Python >= 3.11
- 所有依赖管理使用 `uv`
- `config.toml` 和 `templates/` 保留在项目根目录
- 代码入口：`python -m show_island`（项目根目录执行）
- 托盘图标和热键监听保持不变

---

### Task 1: 创建包目录结构

**Files:**
- Create: `src/show_island/__init__.py`

**Interfaces:**
- Produces: 包目录 `src/show_island/`，`__init__.py` 使目录成为 Python 包

- [ ] **Step 1: 创建目录和 `__init__.py`**

```bash
New-Item -ItemType Directory -Force -Path src/show_island
```

- [ ] **Step 2: 写入 `__init__.py`**

```python
"""游戏截图内容识别工具 — show_island 包。"""
```

- [ ] **Step 3: 提交**

```bash
git add src/show_island/__init__.py
git commit -m "feat: create src/show_island package structure

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 2: 迁移 config.py、screenshot.py、matcher.py 到包内

**Files:**
- Create: `src/show_island/config.py`
- Create: `src/show_island/screenshot.py`
- Create: `src/show_island/matcher.py`

**Interfaces:**
- Produces:
  - `show_island.config.load_config(path="config.toml") -> dict`
  - `show_island.screenshot.capture_screen() -> np.ndarray`
  - `show_island.matcher.match_templates(screenshot, items, threshold) -> list[dict]`
  - `show_island.matcher.sort_results(items) -> list[dict]`

这三个文件当前**没有内部互相导入**，也没有导入其他项目模块，因此可以直接复制，无需修改 import 语句。

- [ ] **Step 1: 复制 config.py 到包目录**

```bash
Copy-Item config.py src/show_island/config.py
```

- [ ] **Step 2: 复制 screenshot.py 到包目录**

```bash
Copy-Item screenshot.py src/show_island/screenshot.py
```

- [ ] **Step 3: 复制 matcher.py 到包目录**

```bash
Copy-Item matcher.py src/show_island/matcher.py
```

- [ ] **Step 4: 验证新位置的文件导入无报错**

```bash
uv run python -c "import sys; sys.path.insert(0, 'src'); from show_island.config import load_config; print('config OK')"
uv run python -c "import sys; sys.path.insert(0, 'src'); from show_island.screenshot import capture_screen; print('screenshot OK')"
uv run python -c "import sys; sys.path.insert(0, 'src'); from show_island.matcher import match_templates, sort_results; print('matcher OK')"
```

预期：三行都输出 `OK`

- [ ] **Step 5: 提交**

```bash
git add src/show_island/config.py src/show_island/screenshot.py src/show_island/matcher.py
git commit -m "feat: migrate config/screenshot/matcher into show_island package

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 3: 创建 ui.py — ResultWindow 三态窗口

**Files:**
- Create: `src/show_island/ui.py`

**Interfaces:**
- Consumes: `show_island.matcher.sort_results(items) -> list[dict]`
- Produces:
  - `show_island.ui.create_tray_image() -> Image.Image`
  - `show_island.ui.ResultWindow(root: tk.Tk, on_close: callable)` — 窗口类
    - `.show_matching()` — 匹配中（300×150）
    - `.show_results(matched: list[dict])` — 结果表格（720×400）
    - `.show_empty()` — 无结果提示
    - `.show_error(msg: str)` — 错误提示
    - `.destroy()` — 销毁窗口

- [ ] **Step 1: 写入 `src/show_island/ui.py`**

```python
"""UI 模块 — 托盘图标、结果窗口（匹配中/结果/错误三态）。"""
import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageDraw

from .matcher import sort_results


# ── 托盘图标 ────────────────────────────────────────────────────

def create_tray_image() -> Image.Image:
    """生成 64×64 托盘图标（绿底白色十字准星）。"""
    img = Image.new("RGBA", (64, 64), (0, 128, 0, 255))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, 59, 59], outline="white", width=3)
    draw.line([32, 16, 32, 48], fill="white", width=2)
    draw.line([16, 32, 48, 32], fill="white", width=2)
    return img


# ── 结果窗口 ────────────────────────────────────────────────────

class ResultWindow:
    """管理单次截图识别的窗口生命周期。

    状态机: matching → results / empty / error → 用户关闭 → None

    使用方式:
        win = ResultWindow(root, on_close)
        win.show_matching()          # 显示"匹配中"小窗
        # ... 匹配完成后 ...
        win.show_results(matched)    # 切换为结果表格
    """

    _MATCHING_SIZE = "300x150"
    _RESULT_SIZE = "720x400"
    _SMALL_SIZE = "360x150"

    def __init__(self, root: tk.Tk, on_close: callable):
        """初始化窗口管理器。

        Args:
            root: Tkinter 根窗口（隐藏的 Tk 实例）。
            on_close: 窗口关闭时的回调，用于通知外部重置引用。
        """
        self._root = root
        self._on_close = on_close
        self._window: tk.Toplevel | None = None

    # ── 公共方法 ─────────────────────────────────────────────

    def show_matching(self) -> None:
        """展示「匹配中」小窗 (300×150)。"""
        self._ensure_window()
        self._clear()
        self._window.title("截图识别")
        self._set_size(self._MATCHING_SIZE)

        ttk.Label(
            self._window,
            text="正在匹配中...",
            font=("Microsoft YaHei UI", 14, "bold"),
        ).pack(expand=True)

    def show_results(self, matched: list[dict]) -> None:
        """切换为结果表格 (720×400)。

        Args:
            matched: 匹配命中的模板项列表。
        """
        self._ensure_window()
        self._clear()
        self._window.title("截图识别结果")
        self._set_size(self._RESULT_SIZE)

        # 标题
        header = ttk.Label(
            self._window,
            text=f"识别到 {len(matched)} 项内容",
            font=("Microsoft YaHei UI", 14, "bold"),
        )
        header.pack(pady=(12, 8))

        # 表格框架
        frame = ttk.Frame(self._window)
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

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 排序后填充数据
        sorted_items = sort_results(matched)
        color_pool = ("#FFFFFF", "#F0F5FF")
        prev_class = None
        color_idx = -1

        for item in sorted_items:
            cls = item["class"]
            if cls != prev_class:
                color_idx += 1
                prev_class = cls
            bg = color_pool[color_idx % 2]

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
            tree.tag_configure(cls, background=bg)

        # 关闭按钮
        ttk.Button(self._window, text="关闭", command=self.destroy).pack(pady=(0, 12))

    def show_empty(self) -> None:
        """显示「未识别到任何内容」。"""
        self._ensure_window()
        self._clear()
        self._window.title("提示")
        self._set_size(self._SMALL_SIZE)

        ttk.Label(
            self._window,
            text="未识别到任何内容",
            font=("Microsoft YaHei UI", 12),
        ).pack(expand=True)

        ttk.Button(self._window, text="关闭", command=self.destroy).pack(pady=(0, 12))

    def show_error(self, msg: str) -> None:
        """切换为错误提示。

        Args:
            msg: 错误消息文本。
        """
        self._ensure_window()
        self._clear()
        self._window.title("错误")
        self._set_size(self._SMALL_SIZE)

        ttk.Label(
            self._window,
            text=msg,
            font=("Microsoft YaHei UI", 11),
            wraplength=320,
        ).pack(expand=True, padx=20)

        ttk.Button(self._window, text="关闭", command=self.destroy).pack(pady=(0, 12))

    def destroy(self) -> None:
        """销毁窗口，触发 on_close 回调。"""
        if self._window is not None:
            self._window.destroy()
            self._window = None
        self._on_close()

    # ── 内部方法 ─────────────────────────────────────────────

    def _ensure_window(self) -> None:
        """确保 Toplevel 存在；不存在则创建。"""
        if self._window is None:
            self._window = tk.Toplevel(self._root)
            self._window.attributes("-topmost", True)
            self._window.resizable(False, False)
            self._window.protocol("WM_DELETE_WINDOW", self.destroy)

    def _clear(self) -> None:
        """销毁窗口内所有子控件。"""
        for child in self._window.winfo_children():
            child.destroy()

    def _set_size(self, size: str) -> None:
        """设置窗口尺寸并居中。size 格式: 'WxH'。"""
        w_str, h_str = size.split("x")
        w, h = int(w_str), int(h_str)

        self._window.update_idletasks()
        sw = self._window.winfo_screenwidth()
        sh = self._window.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self._window.geometry(f"{w}x{h}+{x}+{y}")
```

- [ ] **Step 2: 验证 ui.py 无语法错误**

```bash
uv run python -c "import sys; sys.path.insert(0, 'src'); from show_island.ui import create_tray_image, ResultWindow; print('ui OK')"
```

预期：`ui OK`

- [ ] **Step 3: 提交**

```bash
git add src/show_island/ui.py
git commit -m "feat: add ResultWindow with matching/results/error states

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 4: 创建 __main__.py — 事件驱动的入口

**Files:**
- Create: `src/show_island/__main__.py`

**Interfaces:**
- Consumes:
  - `show_island.config.load_config() -> dict`
  - `show_island.screenshot.capture_screen() -> np.ndarray`
  - `show_island.matcher.match_templates(screenshot, items, threshold) -> list[dict]`
  - `show_island.ui.create_tray_image() -> Image.Image`
  - `show_island.ui.ResultWindow(root, on_close)` — 窗口类
- Produces: 可运行的 `python -m show_island` 入口

- [ ] **Step 1: 写入 `src/show_island/__main__.py`**

```python
"""游戏截图内容识别工具 — 主入口。

托盘常驻后台，全局快捷键触发截图识别。
快捷键按下立即弹窗提示，匹配完成后原地切换为结果。
"""
import logging
import queue
import threading
from pathlib import Path

from pynput import keyboard
from pystray import Icon, Menu, MenuItem
import tkinter as tk
from tkinter import messagebox

from show_island.config import load_config
from show_island.screenshot import capture_screen
from show_island.matcher import match_templates
from show_island.ui import create_tray_image, ResultWindow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ── 模板校验 ────────────────────────────────────────────────────

def _validate_template_images(items: list[dict]) -> list[str]:
    """校验所有模板图片是否存在。返回错误信息列表（空列表表示全部通过）。"""
    errors: list[str] = []
    for i, item in enumerate(items):
        image_path = item["image"]
        text = item.get("text", "?")
        if not image_path:
            errors.append(
                f"第 {i+1} 项「{text}」: image 路径为空，请填写模板图片路径"
            )
        elif not Path(image_path).exists():
            errors.append(
                f"第 {i+1} 项「{text}」: 模板图片不存在\n  → {image_path}"
            )
    return errors


# ── 快捷键回调 ──────────────────────────────────────────────────

def _make_hotkey_callback(config: dict, result_queue: queue.Queue):
    """返回快捷键回调函数。

    回调在 pynput 后台线程执行：
    1. 立即向队列发送 "matching" 事件
    2. 截图 + 模板匹配
    3. 向队列发送 "done" 或 "error" 事件
    """
    def callback():
        # 立即通知 UI 弹出"匹配中"窗口
        result_queue.put({"status": "matching"})

        logger.info("快捷键触发，开始截图...")
        try:
            screenshot = capture_screen()
            logger.info("截图成功，尺寸: %s", screenshot.shape)
        except Exception as e:
            logger.error("截图失败: %s", e)
            result_queue.put({"status": "error", "message": f"截图失败: {e}"})
            return

        logger.info("开始模板匹配（%d 个模板）...", len(config["items"]))
        try:
            matched = match_templates(
                screenshot, config["items"], config["threshold"]
            )
            logger.info("匹配完成，命中 %d 项", len(matched))
            result_queue.put({"status": "done", "matched": matched})
        except Exception as e:
            logger.error("匹配失败: %s", e)
            result_queue.put({"status": "error", "message": f"匹配失败: {e}"})

    return callback


# ── 主入口 ──────────────────────────────────────────────────────

def main():
    logger.info("加载配置...")
    try:
        config = load_config()
    except Exception as e:
        root_err = tk.Tk()
        root_err.withdraw()
        messagebox.showerror("配置错误", f"加载配置文件失败:\n{e}")
        return

    # 启动时校验所有模板图片
    errors = _validate_template_images(config["items"])
    if errors:
        root_err = tk.Tk()
        root_err.withdraw()
        error_msg = "以下模板图片配置有误，请修正后重新启动:\n\n" + "\n\n".join(errors)
        messagebox.showerror("模板配置错误", error_msg)
        return

    result_queue: queue.Queue = queue.Queue()

    hotkey = config["hotkey"]
    logger.info("注册全局快捷键: %s", hotkey)

    # 创建托盘图标（守护线程）
    tray_image = create_tray_image()
    tray_icon = Icon(
        "screenshot_recognizer",
        tray_image,
        "截图识别工具",
        menu=Menu(MenuItem("退出", lambda icon, item: icon.stop())),
    )
    tray_thread = threading.Thread(target=tray_icon.run, daemon=True)
    tray_thread.start()
    logger.info("托盘已启动")

    # 隐藏的 Tkinter 根窗口（用于消息循环 + Toplevel 父窗口）
    root = tk.Tk()
    root.withdraw()

    # 当前活跃的结果窗口引用
    current_window: ResultWindow | None = None

    def on_window_close():
        """用户关闭窗口时清除引用，下次热键触发时创建新窗口。"""
        nonlocal current_window
        current_window = None

    def poll_queue():
        """轮询结果队列（每 500ms），在主线程中处理 UI 事件。"""
        nonlocal current_window
        try:
            while True:
                data = result_queue.get_nowait()
                status = data.get("status")

                if status == "matching":
                    # 关闭旧窗口（如果存在），创建新的 matching 窗口
                    if current_window is not None:
                        current_window.destroy()
                    current_window = ResultWindow(root, on_window_close)
                    current_window.show_matching()

                elif status == "done":
                    matched = data.get("matched", [])
                    if current_window is None:
                        # 用户在匹配期间关闭了窗口，丢弃结果
                        logger.info("窗口已关闭，丢弃匹配结果")
                    elif not matched:
                        current_window.show_empty()
                    else:
                        current_window.show_results(matched)

                elif status == "error":
                    msg = data.get("message", "未知错误")
                    if current_window is None:
                        current_window = ResultWindow(root, on_window_close)
                    current_window.show_error(msg)

        except queue.Empty:
            pass
        root.after(500, poll_queue)

    # 启动队列轮询
    root.after(500, poll_queue)

    # 启动全局热键监听
    listener = keyboard.GlobalHotKeys({
        hotkey: _make_hotkey_callback(config, result_queue),
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

- [ ] **Step 2: 验证 __main__.py 无语法错误**

```bash
uv run python -c "import sys; sys.path.insert(0, 'src'); import importlib; importlib.import_module('show_island.__main__'); print('__main__ OK')"
```

预期：`__main__ OK`（注意：这会触发 logging 和 config 加载，如果 config.toml 存在且有效则正常导入）

- [ ] **Step 3: 提交**

```bash
git add src/show_island/__main__.py
git commit -m "feat: event-driven __main__ with immediate matching feedback

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 5: 更新 pyproject.toml

**Files:**
- Modify: `pyproject.toml`

**Interfaces:**
- Produces: 包安装路径指向 `src/show_island`

- [ ] **Step 1: 修改 pyproject.toml**

修改 `[tool.hatch.build.targets.wheel]` 的 `packages`：

```toml
# 改前
packages = ["."]

# 改后
packages = ["src/show_island"]
```

用 Edit 工具精确替换：
- `old_string`: `packages = ["."]`
- `new_string`: `packages = ["src/show_island"]`

- [ ] **Step 2: 运行 uv sync 安装包**

```bash
uv sync
```

- [ ] **Step 3: 验证包可导入**

```bash
uv run python -c "from show_island.config import load_config; print('import OK')"
```

预期：`import OK`

- [ ] **Step 4: 提交**

```bash
git add pyproject.toml uv.lock
git commit -m "build: update packages path to src/show_island

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 6: 删除根目录旧文件

**Files:**
- Delete: `main.py`
- Delete: `config.py`
- Delete: `screenshot.py`
- Delete: `matcher.py`

- [ ] **Step 1: 删除旧文件并提交**

```bash
Remove-Item main.py
Remove-Item config.py
Remove-Item screenshot.py
Remove-Item matcher.py
git add -A
git commit -m "refactor: remove old root-level source files

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 7: 更新测试文件的 import 路径

**Files:**
- Modify: `tests/test_config.py`
- Modify: `tests/test_matcher.py`

**Interfaces:**
- Consumes: `show_island.config`, `show_island.matcher`

- [ ] **Step 1: 修改 tests/test_config.py 的 import**

改前：
```python
from config import load_config, REQUIRED_ITEM_FIELDS, DEFAULT_THRESHOLD, DEFAULT_TEMPLATES_DIR
```

改后：
```python
from show_island.config import load_config, REQUIRED_ITEM_FIELDS, DEFAULT_THRESHOLD, DEFAULT_TEMPLATES_DIR
```

- [ ] **Step 2: 修改 tests/test_matcher.py 的 import 和 path hack**

改前：
```python
import sys
import os
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from matcher import match_templates, sort_results, _rank_sort_key
```

改后：
```python
import numpy as np
import pytest

from show_island.matcher import match_templates, sort_results, _rank_sort_key
```

（移除 `sys.path` hack，因为 `uv sync` 后包已在环境中可用）

- [ ] **Step 3: 运行测试验证**

```bash
uv run pytest tests/ -v
```

预期：所有测试 PASS

- [ ] **Step 4: 提交**

```bash
git add tests/
git commit -m "test: update imports for show_island package

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 8: 端到端验证

- [ ] **Step 1: 运行全部测试**

```bash
uv run pytest tests/ -v
```

预期：全部 PASS

- [ ] **Step 2: 确认入口命令可导入**

```bash
uv run python -m show_island --help 2>&1 || uv run python -c "from show_island.__main__ import main; print('entrypoint OK')"
```

- [ ] **Step 3: 确认所有导入链正确**

```bash
uv run python -c "
from show_island.config import load_config
from show_island.screenshot import capture_screen
from show_island.matcher import match_templates, sort_results
from show_island.ui import create_tray_image, ResultWindow
from show_island.__main__ import main
print('All imports OK')
"
```

预期：`All imports OK`

- [ ] **Step 4: 最终提交（如有遗漏）**

```bash
git status
```
