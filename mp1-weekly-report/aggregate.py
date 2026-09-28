"""MP1 · 学习周报生成器 —— 聚合段（v0.1 步骤 3）

## DoD（先写验收条件，再写代码）
- build_report(rows, problems) 只算账、排序、判事实，return 结构化 report；
  不 print、不碰文件、不拼展示文案。
- report 结构契约（顺序由 aggregate 定，render 不得再排序）：
    {
      "total_hours": float,
      "record_count": int,
      "week_items": list[tuple[str, float]],      # 已按 week_no 数字升序：W0→W28
      "category_items": list[tuple[str, float]],  # 已按 hours 降序，同分保持稳定
      "problems": list[dict],                     # 原样带 lineno/line/reason
      "td1_bias": bool,                           # True=存在 TD-1 口径偏差这一事实
    }
- 坏行不沉默：problems 原样交 render 展示，aggregate 不打印。
- 周序用 week_no 数字尺子，不信字典序（W10 不能排在 W2 前）。
- 浮点报表数字由 render 用 :.1f 收口；aggregate 不拼文案。
- 聚合只读不改：不动 sessions.md，不动解析结果。
- 本模块是库，不是入口：全链路 CLI 唯一入口在 generator.py。
  这样串联代码与硬编码路径只存在一份，改路径/改链路只改一处。

## TD-1 口径偏差（契约 v2 遗留，v3 修）

**一句话**：`category` 与 `hours` 测的不是同一件事，**按 `category` 求和得到的
时长分布天然偏高**。

**病根**：契约 v2 的 `hours` 记的是**学习时间**（只有学习者本人动手/动脑的
时段才计数，口径见 `sessions.md`），而 `category` 记的是**产出类型**。教练代做
的劳动产出的是「文档」，但它不计入 `hours`——于是同一行里，「产出是文档」
与「时长属学习」并存。**这不是数据错，是字段设计把两个不相干的维度压进了
一个格子。**

**现场证据**：`sessions.md` 中 `2026-09-11 | W1 | 1.1 | 项目` 一行，含教练代做的
仓库与文档劳动，实际学习时长低于 1.1h，只能靠一行注释标"已知偏高"。

**修法（v3 级改动）**：给数据加 `actor` 字段，取值 `self` / `coach`，聚合时只算
`self`。会动契约版本号与全部既有行，应由学习者在写 `aggregate.py` 时亲自主导
决策——**这不是解析器该替他决定的取舍**。解析器对那一行做得没错：它忠实读入
`category=项目`、`hours=1.1`，两栏各自合法。错位在聚合阶段才让分布失真。

**使用约束（v3 修好之前）**：**任何按 `category` 出的时长分布都不可信**。
面试若被问"你的学习时间怎么统计的"，须能当场解释这个已知偏差——**知道偏差
存在、且知道它在哪，就叫"已知"；不知道就叫沉默 bug**。

**当前处理（v0.1 步骤 3，2026-09-12 方案 a）**：偏差事实由本模块的
`TD1_BIAS_ACTIVE` 常量显式带进 `report["td1_bias"]`，`render.py` 据此加
⚠ 文案——**事实归 aggregate，措辞归 render**。v3 真修后只改这一行。

## 预测注释
- render_markdown(report) 最终 md 形状：
  - 标题、合计：合计: X.Xh ／ N 条记录
  - 坏行有则出现在前部，无则省略；坏行按全量统计，不随 --week 过滤
  - 按周合计：W0, W1, W2, ... W10 在 W2 后；每行 X.Xh
  - 按类别合计：⚠ TD-1 事实说明；类别按 hours 降序；每行 X.Xh
- 数字以运行时 sessions.md 为准，不写死。
"""


# --- TD-1 口径偏差事实开关 ---------------------------------------------
# v3 真修 TD-1 时：改这一行为 False（或改为从数据推导，比如扫描
#       是否存在带“教练代做”标记的行）。改这一行，别处不用翻。
# 完整论证、现场证据、修法与使用约束见模块 docstring 的「TD-1」段。
TD1_BIAS_ACTIVE = True


def group_sum(rows, key):
    """分组聚合：按 key(row) 分组、组内累加 hours，返回 {组名: 合计}。"""
    totals = {}
    for row in rows:
        k = key(row)
        totals[k] = totals.get(k, 0) + row["hours"]
    return totals


def week_no(label):
    """周次排序尺子："W10" → 10。"""
    return int(label[1:])


def by_week(row):
    return row["week"]


def by_category(row):
    return row["category"]


def build_report(rows, problems):
    """算账、排序、判事实，return 结构化 report。不 print。"""
    week_totals = group_sum(rows, key=by_week)
    category_totals = group_sum(rows, key=by_category)

    week_items = sorted(
        week_totals.items(),
        key=lambda item: week_no(item[0]),
    )

    category_items = sorted(
        category_totals.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    return {
        "total_hours": sum(row["hours"] for row in rows),
        "record_count": len(rows),
        "week_items": week_items,
        "category_items": category_items,
        "problems": problems,
        "td1_bias": TD1_BIAS_ACTIVE,   # 判断来自上面那个命名常量，不是内联字面量
    }


# 本文件不提供 __main__：全链路入口只在 generator.py。
# 如果要在开发时快速看聚合中间结果，用：
#   python -c "from parse_sessions import parse_sessions; \
#              from aggregate import build_report; \
#              rows, problems = parse_sessions('请传入路径'); \
#              print(build_report(rows, problems))"