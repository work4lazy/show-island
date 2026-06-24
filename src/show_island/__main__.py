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
