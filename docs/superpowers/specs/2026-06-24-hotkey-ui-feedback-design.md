# Spec: 快捷键即时反馈 UI + 文件结构整理

**日期:** 2026-06-24
**状态:** 已确认

---

## 目标

1. 快捷键触发后**立即**弹出"匹配中"提示窗口，匹配完成后原地切换为结果表格
2. 用户关闭结果窗口后可再次触发，重新弹窗
3. 整理项目文件结构，代码入包、用户文件留根目录

---

## 一、文件结构整理

### 现状

所有 Python 源码散落在项目根目录，与配置文件、模板目录混在一起。

### 整理后

```
show_island/
├── src/
│   └── show_island/          # Python 包
│       ├── __init__.py
│       ├── __main__.py       # 入口（原 main.py）
│       ├── config.py         # 配置加载
│       ├── screenshot.py     # 截图
│       ├── matcher.py        # 模板匹配
│       └── ui.py             # 新增：所有 Tkinter UI 逻辑
├── config.toml               # 用户配置（根目录）
├── templates/                # 模板图片（根目录）
├── tests/
├── docs/
├── pyproject.toml
└── uv.lock
```

### 决策理由

- `config.toml`、`templates/` 留在根目录 — 用户需要频繁编辑，放根目录直观
- 代码全部迁入 `src/show_island/` 包
- `pyproject.toml` 更新 `packages = ["src/show_island"]`
- 运行时：`python -m show_island`（在项目根目录下）
- `config.toml` 和 `templates/` 的路径仍以**当前工作目录**为基准，保持不变

---

## 二、UI 交互流程

```
用户按快捷键
    │
    ▼
┌──────────────┐   queue.put({"status": "matching"})   ← 立即入队
│  pynput 线程  │
│  截图 + 匹配   │
│              │   queue.put({"status": "done", ...})   ← 匹配完成
└──────────────┘
    ║  (queue.Queue)
    ▼
┌──────────────┐
│  poll_queue  │  主线程每 500ms 轮询队列
│  (Tk 主线程)  │
│              │  "matching" → 创建 matching 小窗
│              │  "done"     → 同一窗口切换为结果表格
│              │  "error"    → 同一窗口切换为错误提示
└──────────────┘
```

### 窗口状态机

```
 [无窗口] ──matching──▶ [小窗: "正在匹配中..." (300×150)]
                            │
              done ─────────┤
                            ▼
                     [大窗: 结果表格 (720×400)]
                            │
              error ────────┤
                            ▼
                     [中窗: 错误信息]
                            │
                    用户关闭 │
                            ▼
                       [无窗口]
```

### 转换方式

同一个 `Toplevel` 实例，状态切换时销毁旧子控件、重建新内容，`geometry` 调整尺寸。

### 线程安全说明

- **必须多线程的原因**：Tkinter 要求 `mainloop()` 在主线程运行；pynput 的 `GlobalHotKeys` 内部启用自己的后台线程执行回调
- **队列作用**：pynput 线程和 Tk 主线程之间唯一安全通信通道
- **竞态处理**：pynput 默认不并发执行同一回调，匹配期间再次按键要么排队要么被 OS 丢弃

---

## 三、ui.py 设计

```
ui.py
├── create_tray_image()           # 生成托盘图标（从 main.py 迁入）
├── class ResultWindow:           # 管理窗口生命周期的类
│   ├── show_matching()           # 展示"匹配中"小窗（300×150）
│   ├── show_results(matched)     # 切换为结果表格（720×400）
│   ├── show_error(msg)           # 切换为错误提示
│   └── close()                   # 销毁窗口，重置状态
```

`ResultWindow` 持有对 `Toplevel` 的引用，每次快捷键触发创建新实例。用户关闭窗口后实例作废，下次触发创建新的。

---

## 四、__main__.py 职责

精简为编排层：

1. 加载配置
2. 校验模板
3. 创建托盘图标 + 启动托盘线程
4. 创建隐藏 Tk root
5. 启动队列轮询（处理 matching/done/error 事件）
6. 注册全局热键
7. 进入 `root.mainloop()`

---

## 五、改动清单

| 操作 | 文件 |
|------|------|
| **新建** | `src/show_island/__init__.py` |
| **新建** | `src/show_island/__main__.py`（原 main.py 重构） |
| **新建** | `src/show_island/ui.py` |
| **迁移** | `config.py` → `src/show_island/config.py` |
| **迁移** | `matcher.py` → `src/show_island/matcher.py` |
| **迁移** | `screenshot.py` → `src/show_island/screenshot.py` |
| **修改** | `pyproject.toml` — packages 路径 |
| **删除** | 根目录旧 `main.py`、`config.py`、`matcher.py`、`screenshot.py` |

### 不变文件

- `config.toml` — 不移动
- `templates/` — 不移动
- `tests/`、`docs/` — 不移动

---

## 六、边界情况

| 场景 | 行为 |
|------|------|
| 匹配中再次按快捷键 | pynput 回调同步执行，不并发，第二次按键排队或丢弃 |
| 结果窗口未关再按快捷键 | 旧窗口自动关闭，新 matching 窗口弹出 |
| 匹配结果为空 | 显示"未识别到任何内容"（沿用现有逻辑） |
| 截图/匹配异常 | 窗口切换为错误提示 |
| 程序启动时模板图片缺失 | 弹出错误提示后退出（沿用现有逻辑） |
