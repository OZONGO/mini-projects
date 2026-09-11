"""MP1 · 学习周报生成器 —— 解析段（v0.1 步骤 2）

## DoD（先写验收条件，再写代码）
- 解析出的条目数 == sessions.md 的数据行数（当前 = 2）
- 每条四个字段都没有前后空格、没有空串；hours 是 float
- 坏行不沉默：连行号和原因一起带出去，运行时看得见
- 造一条坏行真跑一次，能看到它被跳过并计数

## 设计决定：坏行信息怎么带出去
只 print 的话，调用方（将来的聚合段）拿不到 → 还是沉默。
所以这个函数 return 两样东西：干净的数据 + 问题清单。
"""

SESSIONS_PATH = "E:/AI/workspace/L/learning-log/sessions.md"   # 正斜杠：反斜杠里 \b \t \n 会被吃掉
FIELDS = ("date", "week", "hours", "topic")                     # 契约里字段的唯一真相源


def parse_sessions(path):
    """把会话日志读成 list[dict]，同时收集所有解析不了的行。

    返回 (rows, problems)：
      rows     —— 每项 {"date", "week", "hours", "topic"}，hours 已转成 float
      problems —— 每项 {"lineno", "line", "reason"}
    """
    rows = []
    problems = []

    # encoding 必须写：不写＝用系统默认（Windows/3.13 是 GBK）继续翻译，
    # 而这份文件是 UTF-8 存的，碰到中文那行当场 UnicodeDecodeError
    with open(path, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            text = line.strip()          # 换行符和行首行尾空白，在这一步一次清干净

            if not text:                 # strip 之后再判空，才不会把 "   \n" 当成有内容
                continue
            if text.startswith("#") or text.startswith(">"):
                continue                 # 契约：以 # 或 > 开头的行不参与解析

            parts = [p.strip() for p in text.split("|")]

            if len(parts) != len(FIELDS):
                problems.append({
                    "lineno": lineno,
                    "line": text,
                    "reason": f"切出 {len(parts)} 段，应为 {len(FIELDS)} 段",
                })
                continue

            empty = [FIELDS[i] for i, p in enumerate(parts) if p == ""]
            if empty:                        # 契约不只管段数，还管每段非空
                problems.append({
                    "lineno": lineno,
                    "line": text,
                    "reason": f"以下字段为空：{'、'.join(empty)}",
                })
                continue

            row = dict(zip(FIELDS, parts))   # zip：字段名表 × 值表 → 成对 → dict

            try:
                row["hours"] = float(row["hours"])
            except ValueError:               # 只接这一种，不用 except Exception 吞掉一切
                problems.append({
                    "lineno": lineno,
                    "line": text,
                    "reason": f"时长不是数字：{row['hours']!r}",
                })
                continue

            rows.append(row)

    return rows, problems


if __name__ == "__main__":
    sessions, problems = parse_sessions(SESSIONS_PATH)

    print(f"解析成功 {len(sessions)} 条，坏行 {len(problems)} 条")
    for s in sessions:
        print("  ", s)

    if sessions:                            # 空表时 sessions[0] 会 IndexError
        print("hours 的类型：", type(sessions[0]["hours"]))

    for p in problems:
        print(f"坏行 第{p['lineno']}行：{p['reason']}  ->  {p['line']}")