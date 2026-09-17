#render.py
"""MP1 · 学习周报生成器 —— 渲染段（v0.3 步骤 4）

## DoD
- render_markdown(report) 纯函数：吃结构化 report，return 完整 markdown 字符串。
- 零 print、零文件路径、零 sum/排序、零 parse。
- 只消费 report 中已排序的 week_items / category_items；不得再排序。
- 数字一律 :.1f。
- 坏行清单、TD-1 ⚠ 文案在本段展示；
  事实来自 report["problems"] / report["td1_bias"]。
- 本文件是全链路唯一 CLI 入口：parse → build_report → render_markdown → print。
  aggregate.py 不再放 __main__，避免串联代码和硬编码路径重复两份。
  改路径只改本文件一处。

## 预测注释
- 输出是完整 markdown：
  - 一级标题 + 合计行
  - 坏行段（有才出现）
  - 按周表格：W0→W28 真周序，W10 在 W2 后
  - 按类别表格：先 ⚠ TD-1 警示，再按时长降序
- 所有 hours 显示为 X.Xh；不写死具体数字。
"""


# --- CLI 入口用的路径：全工程只此一处 -----------------------------------
# 相对路径从【当前工作目录】起算，必须在这个目录里跑：
#   cd mini-projects/mp1-weekly-report && python render.py
SESSIONS_PATH = "../../learning-log/sessions.md"


def render_markdown(report):
    """纯函数：吃 report，return markdown 字符串。零 print、零 IO、零排序。"""
    lines = []

    lines.append("# 学习周报")
    lines.append("")
    lines.append(
        f"合计: {report['total_hours']:.1f}h ／ {report['record_count']} 条记录"
    )
    lines.append("")

    problems = report.get("problems", [])
    if problems:
        lines.append(f"## 坏行（{len(problems)} 条，已隔离，不计入聚合）")
        for p in problems:
            lines.append(f"-  第 {p['lineno']} 行：{p['reason']}")
        lines.append("")

    lines.append("## 按周合计")
    lines.append("")
    lines.append("| 周次 | 时长 |")
    lines.append("|---|---|")
    for week, hours in report["week_items"]:
        lines.append(f"| {week} | {hours:.1f}h |")
    lines.append("")

    lines.append("## 按类别合计")
    lines.append("")
    if report.get("td1_bias"):
        lines.append("⚠ 口径偏差（TD-1）：category 记产出类型、hours 记学习时间，")
        lines.append("含教练代做劳动的行，本分布天然偏高（契约 v3 时再修）。")
        lines.append("")

    lines.append("| 类别 | 时长 |")
    lines.append("|---|---|")
    for category, hours in report["category_items"]:
        lines.append(f"| {category} | {hours:.1f}h |")

    return "\n".join(lines).rstrip() + "\n"


def main():
    """全链路唯一入口。写文件/打印的活归这里，不归 render_markdown。"""
    from parse_sessions import parse_sessions
    from aggregate import build_report

    rows, problems = parse_sessions(SESSIONS_PATH)
    report = build_report(rows, problems)
    md = render_markdown(report)
    print(md)

    # 若将来要写进 learning-log/weeks/，也只写在这一个 main() 里。
    # render_markdown 永远不碰文件。


if __name__ == "__main__":
    main()