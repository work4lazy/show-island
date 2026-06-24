"""模板匹配引擎测试。"""
import numpy as np
import pytest

from show_island.matcher import match_templates, sort_results, _rank_sort_key


def _make_textured_square(size: int = 50) -> np.ndarray:
    """创建一个有方差的白色方块（适合 TM_CCOEFF_NORMED 匹配）。"""
    img = np.ones((size, size, 3), dtype=np.uint8) * 255
    # 在角落加一个暗像素产生方差，避免 TM_CCOEFF_NORMED 退化
    img[0, 0] = [200, 200, 200]
    return img


class TestRankSortKey:
    """rank 排序键测试。"""

    def test_s_rank_is_highest(self):
        assert _rank_sort_key("S") < _rank_sort_key("A")

    def test_rank_order(self):
        ranks = ["D", "B", "", "S", "A", "C"]
        sorted_ranks = sorted(ranks, key=_rank_sort_key)
        assert sorted_ranks == ["S", "A", "B", "C", "D", ""]

    def test_lowercase_normalized(self):
        assert _rank_sort_key("s") == _rank_sort_key("S")
        assert _rank_sort_key("a") == _rank_sort_key("A")


class TestSortResults:
    """结果排序测试。"""

    def test_sort_by_class_then_rank(self):
        items = [
            {"text": "B级传奇", "class": "传奇地图传言", "rank": "B"},
            {"text": "S级传奇", "class": "传奇地图传言", "rank": "S"},
            {"text": "A级炸坟", "class": "炸坟岛传言", "rank": "A"},
            {"text": "空级首领", "class": "首领传言", "rank": ""},
        ]
        result = sort_results(items)
        # 按 class 字母序: 传奇地图传言 < 炸坟岛传言 < 首领传言
        # 但实际中文按 unicode 排序，此处只验证组内 rank 顺序
        classes = [r["class"] for r in result]
        for cls in set(classes):
            group = [r for r in result if r["class"] == cls]
            ranks = [r["rank"] for r in group]
            assert ranks == sorted(ranks, key=_rank_sort_key), f"class={cls} rank 排序错误: {ranks}"


class TestMatchTemplates:
    """模板匹配测试 — 使用合成图片验证核心逻辑。"""

    @pytest.fixture
    def template_img(self):
        """50x50 有纹理的白色方块模板（含方差避免 TM_CCOEFF_NORMED 退化）。"""
        return _make_textured_square()

    @pytest.fixture
    def screenshot_with_template(self, template_img):
        """500x500 黑色背景，在 (100,200) 处嵌入模板。"""
        img = np.zeros((500, 500, 3), dtype=np.uint8)
        img[100:150, 200:250] = template_img
        return img

    def test_match_finds_embedded_template(self, tmp_path, screenshot_with_template):
        """截图中嵌入的模板应该被匹配到。"""
        import cv2

        template_path = tmp_path / "textured_square.png"
        cv2.imwrite(str(template_path), _make_textured_square())

        items = [{
            "image": str(template_path),
            "text": "有纹理方块",
            "class": "测试",
            "map": "测试地图",
            "content": "测试内容",
            "rank": "S",
        }]

        results = match_templates(screenshot_with_template, items, threshold=0.7)
        assert len(results) == 1
        assert results[0]["text"] == "有纹理方块"

    def test_match_skips_missing_template(self, screenshot_with_template):
        """不存在的模板图片应被跳过，不报错。"""
        items = [{
            "image": "nonexistent.png",
            "text": "不存在",
            "class": "测试",
            "map": "不存在地图",
            "content": "",
            "rank": "",
        }]
        results = match_templates(screenshot_with_template, items, threshold=0.7)
        assert len(results) == 0

    def test_empty_screenshot_no_match(self, tmp_path):
        """全黑截图不应匹配到任何模板。"""
        import cv2

        template_path = tmp_path / "textured_square.png"
        cv2.imwrite(str(template_path), _make_textured_square())

        items = [{
            "image": str(template_path),
            "text": "有纹理方块",
            "class": "测试",
            "map": "测试地图",
            "content": "",
            "rank": "S",
        }]

        black_screen = np.zeros((500, 500, 3), dtype=np.uint8)
        results = match_templates(black_screen, items, threshold=0.7)
        assert len(results) == 0

    def test_deduplication(self, tmp_path):
        """同一模板出现多次只报告一次。"""
        import cv2

        template_img = _make_textured_square()
        template_path = tmp_path / "textured_square.png"
        cv2.imwrite(str(template_path), template_img)

        items = [{
            "image": str(template_path),
            "text": "有纹理方块",
            "class": "测试",
            "map": "测试地图",
            "content": "",
            "rank": "S",
        }]

        # 截图中嵌入两个相同模板
        dup_screenshot = np.zeros((500, 500, 3), dtype=np.uint8)
        dup_screenshot[50:100, 50:100] = template_img
        dup_screenshot[300:350, 300:350] = template_img

        results = match_templates(dup_screenshot, items, threshold=0.7)
        assert len(results) == 1

    def test_empty_image_path_skipped(self, screenshot_with_template):
        """image 为空字符串的 item 应被跳过。"""
        items = [{
            "image": "",
            "text": "空路径",
            "class": "测试",
            "map": "测试地图",
            "content": "",
            "rank": "",
        }]
        results = match_templates(screenshot_with_template, items, threshold=0.7)
        assert len(results) == 0
