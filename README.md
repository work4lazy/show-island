# Show Island

游戏截图内容识别工具 — 全局快捷键触发截图，OpenCV 模板匹配识别预设图片内容。

## 功能

- 托盘常驻后台运行
- 全局快捷键触发截图识别
- 多尺度 OpenCV 模板匹配
- 快捷键按下立即弹窗反馈，匹配完成后原地切换为结果

## 环境要求

- Python >= 3.11
- Windows 10+

## 安装与运行

```bash
# 克隆仓库
git clone https://github.com/work4lazy/show-island.git
cd show-island

# 安装依赖
uv sync

# 运行
uv run python src/main.py
```

## 配置

编辑 `config.toml` 配置文件：

```toml
hotkey = "<ctrl>+1"          # 全局快捷键
threshold = 0.8               # 模板匹配阈值 (0.0-1.0)
templates_dir = "templates"   # 模板图片目录

[[items]]
image = "templates/example.png"
text = "示例名称"
class = "类别"
map = "地图名"
content = "内容描述"
rank = "A"
```

## 打包为 EXE

使用 Nuitka 打包：

```bash
uv add --dev nuitka
uv run python -m nuitka --standalone --windows-console-mode=disable --enable-plugin=tk-inter src/main.py
```

## 开发

```bash
uv sync --dev         # 安装开发依赖
uv run pytest         # 运行测试
```
