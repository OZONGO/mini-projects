# aggregate.py
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

## 预测注释
- render_markdown(report) 最终 md 形状：
  - 标题、合计：合计: X.Xh ／ N 条记录
  - 坏行有则出现在前部，无则省略；坏行按全量统计，不随 --week 过滤
  - 按周合计：W0, W1, W2, ... W10 在 W2 后；每行 X.Xh
  - 按类别合计：⚠ TD-1 事实说明；类别按 hours 降序；每行 X.Xh
- 数字以运行时 sessions.md 为准，不写死。
"""


# --- TD-1 口径偏差事实开关 ---------------------------------------------
# v0.1 步骤 3（2026-09-12 裁决方案 a）：TD-1 已确认存在——category 记产出类型、hours 记学习时间，
#       含教练代做劳动的行不计入 hours，类别分布天然偏高。
# v3 真修 TD-1 时：改这一行为 False（或改为从数据推导，比如扫描
#       是否存在带“教练代做”标记的行）。改这一行，别处不用翻。
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
