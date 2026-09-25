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
