"""UI 模块 — 托盘图标、结果窗口（匹配中/结果/错误三态）。"""
import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageDraw

from matcher import sort_results


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
