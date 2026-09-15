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
- [x] v0.1 · 步骤 4：`render.py` 渲染段——`render_markdown(report)` 纯函数（零 print／零路径／零 sum／零排序）；`report` 契约把顺序物化进 `list[tuple]`，render 不得再排序；数字一律 `:.1f` 收口；TD-1「事实归 aggregate、措辞归 render」（`td1_bias` 开关）；三段式流水线打通
- [x] v0.1 · 步骤 4.5：`test_render.py` 测试固化（8 用例，守住渲染段五条契约）——纯函数的夹具就是一个**手写的 report dict**，比解析段的 `tempfile` 轻一个数量级；`make_report(**overrides)` 工厂的 base 顺序**刻意与契约相反**（周次 W10 在前、类别升序），否则"排对了"与"没排序"在观测上无法区分；**测试绝不读真 `sessions.md`**
- [x] v0.1 · 步骤 4.6：`test_aggregate.py` 测试固化（9 用例，守住聚合段八条契约：合计／条数／周序数字尺子／类别降序／同分稳定／problems 原样／td1_bias 来自常量／只读不改）——夹具是**手写的 rows dict**；**变异实测三组**（①删 `key=week_no` 尺子 ②类别排序键从时长换成组名 ③降序改写成"升序再整体翻转"）各自**只打掉对应那一条**测试，其余 8 条全绿＝"一测一守"。**本步最值钱的发现是"沉默型变异"**：真数据只有 W1/W2（字典序＝数字序）且类别无同分，①②③里有两处同时生效时 `render.py` 的输出**一个字都不会变**——变异测试的价值不在"改坏了会红"，而在"改坏了外面看不出来时，只有反向夹具能看见它"
- [ ] v1.0：`ReportGenerator` 类 ＋ CLI 参数（`--week 2026-W40`）＋ JSON 导出 ＋ 3 个测试

## 怎么用

```bash
cd mini-projects/mp1-weekly-report    # 相对路径从 CWD 起算，必须在这个目录里跑

# 唯一入口：全链路 parse → aggregate → render，打印 md 周报
python render.py

# 跑解析器（打印解析结果与坏行）
python parse_sessions.py

# 跑测试（改任何校验规则或排版契约后都该跑一遍）
python test_parse_sessions.py
python test_render.py
python test_aggregate.py

# 只想看聚合中间结果——aggregate 已退回纯库，不再是入口：
python -c "from parse_sessions import parse_sessions; from aggregate import build_report; print(build_report(*parse_sessions('../../learning-log/sessions.md')))"
```

## 已知技术债

| 位置 | 问题 | 处理时机 |
|---|---|---|
| `date` 字段 | 完全未校验格式，`2026-13-99` 照收 | v1.0 加 `--week` 做日期比较前 |
| `hours` 字段 | 吃 Unicode 数字与下划线字面（`float("１２３")`、`float("1_0")`） | v1.0 参与比较前 |
| `category` 语义 | 与「学习时长」口径错位——教练劳动产出"文档"但不计入时长，按类别求和天然偏高 | **已裁决（2026-09-12，方案 a）**：事实由 `aggregate.py` 的 `TD1_BIAS_ACTIVE` 常量提供，⚠ 文案在 `render.py`；`actor` 字段留契约 v3（详见 `parse_sessions.py` 末尾技术债条目）。**v3 修好后把 `TD1_BIAS_ACTIVE` 改成 False，只改这一行** |

