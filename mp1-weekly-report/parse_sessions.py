"""MP1 · 学习周报生成器 —— 解析段（v0.1 步骤 2 ＋ 契约 v2）

## DoD（先写验收条件，再写代码）
- 解析出的条目数 == sessions.md 的数据行数（当前 = 5）
- 每条五个字段都没有前后空格、没有空串；hours 是 float
- 坏行不沉默：连行号和原因一起带出去，运行时看得见
- 值域问题各造一条真跑一次：非法类别／越界周次／非有限时长／**非规范字面的周次（`W01`、全角 `W１`）**
- 造坏行验完，**当场把测试行删掉**（改用临时文件喂解析器，真数据文件不沾测试残留）

## 三类检查，顺序即契约（顺序决定报错能不能拿来改数据）
1. 段数  —— 不先卡这关，按位置取字段就会错位或直接 IndexError
2. 非空  —— 必须排在值域**之前**：否则空串会先被报成"类别 '' 不在词表"，
            把人往"词表少了个词"的方向带，而真相是那一栏压根没填
3. 值域  —— 受控字段（week / category）和 hours 一起在这一关判

## 设计决定一：坏行信息怎么带出去
只 print 的话，调用方（将来的聚合段）拿不到 → 还是沉默。
所以这个函数 return 两样东西：干净的数据 ＋ 问题清单。

## 设计决定二（开放题）：week 要不要也上值域校验？——要
这和"主题不该当分组键"是同一件事的两面：分组键必须受控，而"受控"不是写进契约
就算数，是**解析器拒绝契约外的值**。`W99` 会造出一个既不叫 W0 也不叫 W1 的幽灵
分组，危害与空 week 完全相同，只是它连"字段为空"这条线索都不给。
代价：合法集合随日历增长（W0–W28），枚举全集要人肉维护，所以这里校的是
**格式＋上界**，不是全集。

## 设计决定三（P1）：周次判「字面规范」，选拒绝不选归一
`W01`、全角 `W１` 经 `int()` 都等于 1，却是与 `W1` 不同的字符串字面。dict 分组只认哈希不认语义，
三者会分成三个桶——正是契约 v2 要防的幽灵分组。根因：**`str.isdigit()` 与 `float()` 都吃 Unicode
数字形式**，所以 `isdigit()` 守不住字面。
两条出路里选**拒绝**（非规范字面直接判坏行）：
- 「归一」（入库前改写成 `W1`）＝解析器悄悄改数据，文件里的值和内存里的值不一致，出错时无从对照，
  是比幽灵分组更难查的一种沉默；
- 「拒绝」＝把坏字面连着行号钉出来，由人回去改文件。代价是多一次人工，换来所见即所得。

## 已知未做（留 v1.0）
- `date` 不校验格式：`2026-13-99` 现在照样收。v1.0 加 `--week` 参数、要做真实的
  日期比较之前，必须先补这一关，否则比较结果是静默错的。
- `hours` 同理会吃 Unicode 数字与下划线字面（`float("１２３") == 123.0`、`float("1_0") == 10.0`）。
  它不是分组键、污染不了分堆，故暂不收紧；v1.0 一旦参与比较再处理。
"""

import math

SESSIONS_PATH = "E:/AI/workspace/L/learning-log/sessions.md"   # 正斜杠：反斜杠里 \b \t \n 会被吃掉
FIELDS = ("date", "week", "hours", "category", "topic")         # 契约里字段的唯一真相源

# 受控词表：与 sessions.md「类别词表」段一字不差。改一处必须同时改另一处。
# （v1.0 的干净做法是让解析器直接把词表从契约里读出来，消灭这个重复。）
CATEGORIES = ("语法", "项目", "复习", "文档", "阅读")
WEEK_MAX = 28                                                   # 计划总周数，见 00 文档


def hours_error(text):
    """hours 的值域：能转 float、是有限数、且非负。返回 None 表示合法。

    为什么要 isfinite：float('nan') 和 float('inf') 都能顺利过 float()，
    而 nan 会把整周合计污染成 nan、inf 会把它撑成无穷大——两条都不报错，
    正是沉默型 bug 的标准长相。负数同理：把学时算少了，没人会 noticed。
    """
    try:
        value = float(text)
    except ValueError:
        return f"时长不是数字：{text!r}"
    if not math.isfinite(value):
        return f"时长不是有限数：{text!r}"
    if value < 0:
        return f"时长为负：{text!r}"
    return None


def week_error(week):
    """周次值域：`W` + **无前导零的 ASCII 数字**，且 <= WEEK_MAX。返回 None 表示合法。

    判的是"字面是否规范"，不是"能不能解析成数字"——理由见模块 DoD 的设计决定三。
    """
    if week[:1] != "W":
        return f"周次 {week!r} 不合契约（应以大写字母 W 开头）"
    digits = week[1:]
    if not (digits.isascii() and digits.isdigit()):
        return f"周次 {week!r} 的序号不是 ASCII 数字（全角、混字都不收）"
    if len(digits) > 1 and digits[0] == "0":
        return f"周次 {week!r} 带前导零（同一周会长出多个字面、分组会裂；应写 W{int(digits)}）"
    if int(digits) > WEEK_MAX:
        return f"周次 {week!r} 越界（应为 W0–W{WEEK_MAX}）"
    return None


def value_error(row):
    """值域检查，按契约字段顺序：week → category → hours。

    副作用：三关全过时把 hours 就地转成 float。放在最后转，是为了让
    problems 里存的永远是**原始那一栏的字面**，方便照着它回去改数据。
    """
    error = week_error(row["week"])
    if error:
        return error

    if row["category"] not in CATEGORIES:
        return f"类别 {row['category']!r} 不在词表：{'、'.join(CATEGORIES)}"

    return hours_error(row["hours"])


def parse_sessions(path):
    """把会话日志读成 list[dict]，同时收集所有解析不了的行。

    返回 (rows, problems)：
      rows     —— 每项含 FIELDS 五个键，hours 已转成 float
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
            if empty:                    # 契约不只管段数，还管每段非空
                problems.append({
                    "lineno": lineno,
                    "line": text,
                    "reason": f"以下字段为空：{'、'.join(empty)}",
                })
                continue

            row = dict(zip(FIELDS, parts))   # zip：字段名表 × 值表 → 成对 → dict

            error = value_error(row)         # 第三关：值域
            if error:
                problems.append({
                    "lineno": lineno,
                    "line": text,
                    "reason": error,
                })
                continue

            row["hours"] = float(row["hours"])
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
