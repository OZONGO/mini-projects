# AGENTS.md —— MP1 学习周报生成器 · Harness Lab 强侧

## 这是什么项目

`mp1-weekly-report/` 是学习周报生成器：读 `learning-log/sessions.md`，聚合成
结构化报告，渲染 Markdown 或导出 JSON。

分层（硬约束，改动前先读文件头 DoD）：
- `parse_sessions.py` —— 解析段（库）
- `aggregate.py`      —— 聚合段（库）
- `render.py`         —— 渲染段（库）
- `generator.py`      —— 唯一 CLI 入口

## 本次任务

生成 **W2** 学习周报的 JSON 数据文件 `harness-lab/week_report.json`。

数据面以 `generator.py` 的 JSON 导出为契约基准：
- 顶层是 JSON **object**；
- `week_items` / `category_items` 是 **list[object]**（键值对对象），
  不是 list[array]；
- 中文以 **UTF-8 原文**在场，不以 `\uXXXX` 转义；
- 范围**只含 W2**（任务是 W2 周报，不是全量报告）。

## 硬约束

- 不动 MP1 主线文件（`parse_sessions.py` / `aggregate.py` / `render.py` /
  `generator.py` / 测试文件一字不改）。
- 产物只写 `harness-lab/week_report.json`，不写盘到别处。
- 数字面对账以 JSON 为准（float 原样）；不拿 14.9 比 14.899999999999999。

## 验证命令（一键反馈，退出码说话）

在 `mini-projects/mp1-weekly-report/` 下执行；每条命令的退出码即判据。

```bash
cd mini-projects/mp1-weekly-report

# 1. 测试：53 例，期望退出码 0
py -3.13 -m unittest discover

# 2. 周报渲染：W2 markdown 走 stdout，期望退出码 0
py -3.13 generator.py --week W2

# 3. JSON 导出：只走 stdout，重定向到本任务指定产物，期望退出码 0
py -3.13 generator.py --week W2 --json > harness-lab/week_report.json

# 4. JSON 契约校验：判据唯一真相源 = harness-lab/strong/check.py（四刀断言＋主线套件体检），不在 AGENTS.md 复制断言；失败即非 0
py -3.13 harness-lab/strong/check.py

# 5. 错误路径：非法周次应非 0（README 示例为 2），报错走 stderr
py -3.13 generator.py --week W99 >/dev/null 2>/dev/null
test $? -eq 2
```