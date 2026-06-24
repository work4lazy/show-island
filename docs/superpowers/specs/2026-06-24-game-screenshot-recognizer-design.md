# 游戏截图内容识别工具 — 设计文档

## 概述

一个后台运行的工具，通过全局快捷键触发屏幕截图，使用 OpenCV 多尺度模板匹配识别截图中是否包含预设的模板图片，去重后以弹窗表格形式展示汇总信息。

## 架构

```
程序启动 → 托盘常驻（图标 + "退出"）
    │
    ↓ 快捷键触发
截图主屏幕 → 多尺度模板匹配 → 去重
    │
    ↓
弹出 Tkinter 结果窗口（可关闭，不影响后台）
```

单进程，逻辑顺序执行。截图和识别在快捷键回调中同步完成，结果弹窗独立于主循环。

## 组件

| 文件 | 职责 |
|------|------|
| `config.py` | 读取 `config.toml`，提供模板项列表、快捷键、相似度阈值等配置 |
| `screenshot.py` | 截取主屏幕全屏，返回 PIL Image |
| `matcher.py` | 对截图执行多尺度模板匹配，返回匹配命中的去重结果列表 |
| `main.py` | 托盘、全局快捷键、组装流程、结果弹窗 |

### config.py

- 使用 `tomllib`（Python 3.11+ 内置）解析 `config.toml`
- 暴露函数 `load_config()` 返回包含 `hotkey`、`threshold`、`items` 的数据对象

### screenshot.py

- 使用 Pillow `ImageGrab.grab()` 截取主屏幕
- 转换为 OpenCV 可用的 BGR 格式（numpy array）

### matcher.py

- 使用 OpenCV `matchTemplate` + `TM_CCOEFF_NORMED`
- 对每个模板图片在 0.5x ~ 2.0x 范围内多尺度缩放搜索
- 任何尺度下相似度 ≥ `threshold`（默认 0.8）视为命中
- 按模板图片路径去重（同一模板图片只报告一次）
- 输入：截图（numpy array）、模板项列表、阈值
- 输出：命中的模板项列表，每项包含 `image`、`text`、`class`、`map`、`content`、`rank`

### main.py

- 启动时调用 `config.load_config()`
- 使用 `pystray` 创建托盘图标，菜单仅含"退出"
- 使用 `pynput` 注册全局快捷键
- 快捷键回调：截图 → 匹配 → 去重 → 弹出结果窗口
- 结果窗口使用 Tkinter `Toplevel`，表格展示（`Treeview`）
- 列：文字、类别、地图、内容、推荐等级（不显示 image 字段）
- 结果按 `class` 分组，组内按 `rank` 排序（S > A > B > C ...）

## 配置文件格式 (`config.toml`)

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

- `hotkey`: pynput 格式的快捷键字符串
- `threshold`: 匹配相似度阈值，0.0 ~ 1.0
- `templates_dir`: 模板图片存放目录（可选，方便管理）
- `[[items]]`: 模板项数组，每项 6 个字段：`image`、`text`、`class`、`map`、`content`、`rank`

## 依赖

- `opencv-python` — 模板匹配
- `pillow` — 截图
- `pynput` — 全局快捷键监听
- `pystray` — 系统托盘

Python 版本要求：≥ 3.11（`tomllib` 内置）

**包管理工具：** 必须使用 `uv` 管理所有依赖，不允许直接使用 `pip` 或手动编辑 `pyproject.toml`。

## 运行方式

```bash
uv init
uv add opencv-python pillow pynput pystray
uv run python main.py
```

## 错误处理

- 模板图片不存在：跳过该项，控制台输出警告
- 截图失败：弹窗提示错误
- 无匹配结果：弹窗显示"未识别到任何内容"
- 配置文件缺失/格式错误：弹窗提示并退出

## 限制

- 仅支持 Windows 平台（pynput + pystray 行为）
- 单显示器场景（主屏幕截图）
- 无异步——匹配大量模板时可能短暂阻塞，但操作极快（<1s）
