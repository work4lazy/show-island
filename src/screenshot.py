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
