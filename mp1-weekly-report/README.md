# MP1 · 学习周报生成器

> 起草：AI ｜ 内容确认：OZONGO

## 做什么

读取学习记录里的会话日志，统计本周学习情况（总学时、主题分布），生成一份 markdown 周报。

## 输入 / 输出

- 输入：`learning-log/sessions.md`（会话日志，契约 v2 五个字段：`日期 | 周次 | 时长h | 类别 | 主题`；相对本目录为 `../../learning-log/sessions.md`）
- 输出：markdown 周报（计划写入 `learning-log/weeks/`）

## 架构（三段式流水线）

```
自由文本  --parse-->  结构化数据  --aggregate-->  统计结果  --render-->  md 周报
```

三段各自独立、各自会变：改输入格式只动 parse，改统计口径只动 aggregate，改排版只动 render。

## 进度

- [x] v0.1 · 步骤 0：仓库骨架
- [x] v0.1 · 步骤 1：立 `sessions.md` 输入契约 ＋ 样本
- [x] v0.1 · 步骤 2：`parse_sessions.py` 解析器（parse 段）——三类检查：段数 → 非空 → 值域（周次／类别／时长）
- [x] v0.1 · 步骤 2.5：契约 v1 → v2，新增受控字段 `类别`（词表 5 值，解析器拒绝词表外的值）
- [ ] v0.1 · aggregate 段
- [ ] v0.1 · render 段
- [ ] v1.0：`ReportGenerator` 类 ＋ CLI 参数（`--week 2026-W40`）＋ JSON 导出 ＋ 3 个测试

## 怎么用

（v0.1 跑通后补）
