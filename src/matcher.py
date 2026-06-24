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

    # 跳过均匀模板（方差为 0），TM_CCOEFF_NORMED 对此退化为 1.0
    if np.std(template) < 1e-6:
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

        # 跳过 NaN（均匀模板/截图的退化情况）
        if np.isnan(max_val):
            continue

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
    return sorted(items, key=lambda x: (x["class"], _rank_sort_key(x["rank"])))
