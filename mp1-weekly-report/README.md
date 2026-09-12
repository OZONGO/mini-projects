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
- [x] v0.1 · 步骤 2.6：`test_parse_sessions.py` 测试固化（23 用例，把九条手工探针变成一条命令）
- [x] v0.1 · 步骤 3：`aggregate.py` 聚合段——同构 `group_sum` 一函数吃两本账；`week_no` 尺子按数字排周序（字典序毒已解）；TD-1 口径偏差显著入输出（方案 a，`actor` 留 v3）
- [ ] v0.1 · render 段
- [ ] v1.0：`ReportGenerator` 类 ＋ CLI 参数（`--week 2026-W40`）＋ JSON 导出 ＋ 3 个测试

## 怎么用

```bash
# 跑解析器（打印解析结果与坏行）
python parse_sessions.py

# 跑测试（改任何校验规则后都该跑一遍）
python test_parse_sessions.py

# 跑聚合（必须在 mp1-weekly-report 目录里跑：相对路径从 CWD 起算）
python aggregate.py
```

## 已知技术债

| 位置 | 问题 | 处理时机 |
|---|---|---|
| `date` 字段 | 完全未校验格式，`2026-13-99` 照收 | v1.0 加 `--week` 做日期比较前 |
| `hours` 字段 | 吃 Unicode 数字与下划线字面（`float("１２３")`、`float("1_0")`） | v1.0 参与比较前 |
| `category` 语义 | 与「学习时长」口径错位——教练劳动产出"文档"但不计入时长，按类别求和天然偏高 | **已裁决（2026-09-12，方案 a）**：偏差显著标注于 aggregate 输出正文；`actor` 字段留契约 v3（详见 `parse_sessions.py` 末尾技术债条目） |

