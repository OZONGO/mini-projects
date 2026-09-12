"""MP1 · 学习周报生成器 —— 聚合段（v0.2 步骤 3）

## DoD（先写验收条件，再写代码）
- 吃 parse_sessions 交回的 (rows, problems)：坏行打印出来，绝不沉默
- 输出两张账：按周合计（W0→W28 真周序）、按类别合计（总额降序）
- 两本账由同一个分组函数吃掉——只有"取哪个字段当键"不同（同构）
- 周次排序用自造的尺子按数字比，不信字典序（W10 排在 W2 前是毒）
- 类别账显著标注口径偏差（TD-1：category 记产出类型、hours 记学习时间，
  教练代做劳动产出"文档"却不计入 hours，按类别分布天然偏高——方案 a 拍板）
- 浮点求和有显示噪声（0.1+0.2 家族），报表数字一律 :.1f 收口
- 聚合只读不改：不动 sessions.md，不动解析结果

## 运行
    cd mini-projects/mp1-weekly-report && python aggregate.py
    （相对路径从【当前工作目录】起算，必须在这个目录里跑）
"""

from parse_sessions import parse_sessions


def group_sum(rows, key):
    """分组聚合：按 key(row) 分组、组内累加 hours，返回 {组名: 合计}。

    按周/按类别两本账骨架相同，唯一可变点是分组键——抽成参数（尺子）。
    """
    totals = {}
    for row in rows:
        k = key(row)                          # 调用递进来的尺子：这条归哪个组
        totals[k] = totals.get(k, 0) + row["hours"]   # word_freq3 的 get 累加，原样搬家
    return totals


def week_no(label):
    """周次排序尺子："W10" → 10。

    敢直接 int() 是因为解析段保证字面规范（W+无前导零 ASCII 数字）。
    """
    return int(label[1:])


def by_week(row):
    return row["week"]


def by_category(row):
    return row["category"]


def main():
    rows, problems = parse_sessions("../../learning-log/sessions.md")

    if problems:                              # 坏行不沉默：上一段记的行号到这儿必须交出来
        print(f"== 坏行 {len(problems)} 条（已隔离，不计入聚合）==")
        for p in problems:
            print(f"  第 {p['lineno']} 行：{p['reason']}")

    week_totals = group_sum(rows, key=by_week)          # 尺子①：按周
    category_totals = group_sum(rows, key=by_category)  # 尺子②：按类别——函数没换

    print("\n== 按周合计 ==")
    for w in sorted(week_totals, key=week_no):        # 命名尺子：def 出来的那种
        print(f"  {w}: {week_totals[w]:.1f}h")

    print("\n== 按类别合计 ==")
    print("  ⚠ 口径偏差（TD-1）：category 记产出、hours 记学习时间，")
    print("    含教练代做劳动的行，本分布天然偏高（契约 v3 时再修）。")
    for c in sorted(category_totals, key=lambda k: category_totals[k], reverse=True):
        print(f"  {c}: {category_totals[c]:.1f}h")    # 行内尺子：lambda 那种，两种都给你看

    print(f"\n合计: {sum(row['hours'] for row in rows):.1f}h ／ {len(rows)} 条记录")


if __name__ == "__main__": 
    main()