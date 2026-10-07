r"""MP1 · 学习周报生成器 —— 解析段（v0.1 步骤 2 ＋ 契约 v2）

> 测试：同目录 `test_parse_sessions.py`（跑法见 README「怎么用」，一条命令跑全部测试）。
> 用例数不写在这里——写死数字＝把会变的数据塞进本应不变的陈述，2026-09-11 那条「验收标准会腐烂」的同族。
> 改本文件的任何校验规则后，先跑测试再提交——把"记得要跑"变成"跑一下就跑了"。

## DoD（先写验收条件，再写代码）
- 解析出的条目数 == sessions.md 的数据行数（**不写死数字**：原写"当前 = 5"，
  2026-09-11 数据涨到 6 条后此条静默失效，见下方「验收标准会腐烂」）
- 每条五个字段都没有前后空格、没有空串；hours 是 float
- 坏行不沉默：连行号和原因一起带出去，运行时看得见
- 值域问题各造一条真跑一次：非法类别／越界周次／非有限时长／**非规范字面的周次（`W01`、全角 `W１`）**／**非法日历日与非法字面的日期**／**非规范字面的时长（`1_0`、全角 `１２３`）**
- 造坏行验完，**当场把测试行删掉**（改用临时文件喂解析器，真数据文件不沾测试残留）

## 验收标准会腐烂（2026-09-11 补记）
上面第一条原写"当前 = 5"，是当天数据行数的快照。数据一涨到 6 条，这条验收标准就
**静默失效**了——没有人会收到提醒，因为没有任何东西在跑它。

这是沉默型 bug 的一种形态，只不过它错在**流程**而非代码：**把会变的数据写进
本应不变的验收条件里，等于给未来埋一颗不报错的雷。**

结构化解法不是"记得改数字"，是让数字不必被记住：
- 验收条件写成比较式的**左侧不变量**（"== 数据行数"），而不是**右侧的字面快照**；
- 且必须有一条命令能真的把它跑出来 —— 见同目录 `test_parse_sessions.py`。


## 三类检查，顺序即契约（顺序决定报错能不能拿来改数据）
1. 段数  —— 不先卡这关，按位置取字段就会错位或直接 IndexError
2. 非空  —— 必须排在值域**之前**：否则空串会先被报成"类别 '' 不在词表"，
            把人往"词表少了个词"的方向带，而真相是那一栏压根没填
3. 值域  —— 受控字段（date / week / category）和 hours 一起在这一关判；
            内部顺序：**date → week → category → hours**，理由见 `value_error` 文档串

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

## 设计决定四（P1.5，2026-09-28）：日期拆两关
`date` 校验拆成两道关卡：
- **关卡一（形状）**：字符串是不是正好 `YYYY-MM-DD` 十个字符、分隔符在第 4/7 位、
  三段都是 ASCII 数字。这一层自己写。
- **关卡二（日历）**：13 月存不存在、2 月有没有 30 天、闰年怎么算。这一层交给库
  （`date.fromisoformat`，内部走 `date()` 构造器）。

为什么不能"一个库函数搞定"：库只保证"我这套方言能读通"，不保证"你的契约只允许
哪一种字面"。`fromisoformat` 收 basic 格式（`20261129`）和 ISO 周日期（`2026-W48-3`）；
`strptime("%Y-%m-%d")` 吃不补零（`2026-1-1`）并吃全角年份（`20２6-09-28` 里的
`\d` 是 Unicode 数字类）。两条路都会让同一天长出多种字面，分组会裂——与拒 `W01`
是同一理由。

对应到 `date_error` 的实现：形状关返回明确理由，形状过再 `fromisoformat`，
`ValueError` 翻译成"不是合法日历日"。返回 None 表示合法，与 `week_error`／
`hours_error` 同形。

## 已知未做（留 v1.0）
- `hours` 字面文法缺口已于 2026-10-07 关闭（契约 v2 内修订）：`hours_shape_error` 字面关＋
  `hours_error` 溢出关落地；`float()` ValueError 与负值检查随文法删除（不可达，护栏判据见
  两函数 docstring）。触发判定：排序尺子自 2026-09-12（6ec338b）已在 `category_items` 上，
  原判「暂不收紧」的前提（只累加、不比较）当时已不成立。
- **【技术债】`category` 与「学习时长」语义错位（TD-1）**：完整论证（病根／现场证据／`actor` 修法／使用约束四条）已于 2026-09-28 迁至 `aggregate.py` 模块 docstring 的「TD-1 口径偏差（契约 v2 遗留，v3 修）」段。**本文件不存这段正文**，此处只留指针。解析器对此不做处理：它忠实读入两栏、各自合法，错位在聚合阶段才让分布失真。

"""

import math
from datetime import date

FIELDS = ("date", "week", "hours", "category", "topic")         # 契约里字段的唯一真相源

# 受控词表：与 sessions.md「类别词表」段一字不差。改一处必须同时改另一处。
# （v1.0 的干净做法是让解析器直接把词表从契约里读出来，消灭这个重复。）
CATEGORIES = ("语法", "项目", "复习", "文档", "阅读")
WEEK_MAX = 28                                                   # 计划总周数，见 00 文档


def date_shape_error(text):
    """关卡一：日期字面形状。返回 None 表示形状通过。

    判的是"字符串长什么样"：长度、分隔符位置、三段都是 ASCII 数字。
    这些都是字符串层面的事，库不欠你这个——库只负责"我这套方言能不能
    读通"，不负责"你的契约要求哪一种字面"。

    `p.isascii() and p.isdigit()` 的方向：这是**字符集过滤器**（只放行
    ASCII 那十个数字），数值合法性完全交给关卡二。反过来（先 isdigit()
    再 int()）就是 9/21「误放方向」那条病根。isascii() 现在的真实身份是
    "防以后有人把关卡二换成 strptime('%Y-%m-%d')" 的护栏：那种情况下
    `20２6-09-28` 会从"响亮拒绝"翻成"静默归一化成 2026"。
    """
    if len(text) != 10:
        return f"日期长度 {len(text)}，应为 10（YYYY-MM-DD）"
    if text[4] != "-" or text[7] != "-":
        return f"日期分隔符位置不对：{text!r}"
    for p in (text[0:4], text[5:7], text[8:10]):
        if not (p.isascii() and p.isdigit()):
            return f"日期 {text!r} 含非 ASCII 数字"
    return None


def date_error(text):
    """日期校验：形状关（自己判）+ 日历关（交库）。返回 None 表示合法。

    形状钉死后再 `fromisoformat`：此时字面只剩一种可能，`fromisoformat`
    的作用就纯粹是问历法。为什么不手工 `date(int(y), int(m), int(d))`——
    等价，但少两次转换就少一处自己写的 bug。

    关卡二交给库而不是自己判闰年的原因：手写闰年规则你会写出 1900 年
    那种 bug（400 年规则），而 `date()` 构造器是唯一入口，非法日历日
    当场抛。
    """
    error = date_shape_error(text)
    if error:
        return error
    try:
        date.fromisoformat(text)
    except ValueError as e:
        return f"日期 {text!r} 不是合法日历日：{e}"
    return None


def hours_shape_error(text):
    """关卡一：时长字面文法。返回 None 表示字面通过。

    契约只收 ASCII 数字＋至多一个小数点，且点两侧都要有数字：`0`、`2.5`、`13.5`。
    一律坏行：符号 `+3`／`-1`、下划线 `1_0`、全角 `１２３`、科学计数 `1e2`、
    漂浮点 `.5`／`1.`、多小数点 `2.5.5`、拼写出来的 `nan`／`inf`、`abc`。

    为什么要自己写这一关而不交给 `float()`：`float()` 的接受集比契约宽得多，
    且宽在两个方向上——PEP 515（3.6）起它连字符串里的下划线都吞
    （`float("1_0") == 10.0`，人读作 1.0，值直接翻十倍），Unicode 十进制数字也吞
    （`float("１２３") == 123.0`）。拿"能不能转 float"当校验＝把库的方言当契约，
    与设计决定三（`W01`／全角 `W１`）、设计决定四（`2026-1-1`）同一条病根。

    形状关一过，两条值域检查就没有活可干，已随本次收紧删除：
    - `float()` 不再可能抛 ValueError（本文法交出的每个串都是合法十进制字面）；
    - 负值不再可能出现（文法里没有符号位，非负由结构保证，强于一个 `if value < 0`）。
    **若将来放宽符号位，负值检查必须加回来。**
    仍留在值关办的只剩一件事：见 `hours_error` 的溢出。
    """
    parts = text.split(".")
    if len(parts) > 2:
        return f"时长字面不合契约：{text!r}（小数点至多一个）"
    for part in parts:
        if not (part.isascii() and part.isdigit()):
            return (
                f"时长字面不合契约：{text!r}"
                "（应为 ASCII 数字，小数点两侧都要有数字；"
                "符号／下划线／全角／科学计数不收）"
            )
    return None


def hours_error(text):
    """hours 的值域：先字面文法（自己判），再溢出（`isfinite`）。返回 None 表示合法。

    `isfinite` 不是死代码，形状关吞不掉它：`"9" * 400` 全是 ASCII 数字、字面关放行，
    `float()` 交回 `inf` 而**不报错**（3.13 实测）。字面关拒的是 `inf` 这个**拼写**，
    拒不了 `inf` 这个**值**——所以拼写走关卡一，数值走关卡二，两条都要有测试。
    nan 侧由关卡一整族拦掉（含 `nan`／`NaN` 拼写），这里头 `inf` 是双保险。
    """
    error = hours_shape_error(text)
    if error:
        return error
    if not math.isfinite(float(text)):
        return f"时长不是有限数：{text!r}"
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
    """值域检查，顺序：**date → week → category → hours**。

    顺序即契约。多违规行只报第一条命中的 reason，所以顺序一变，"报哪句"
    就变了；凡是以多违规行做断言的用例会跟着漂。

    date 按 FIELDS 契约顺序放第一位——日期是行的主键之一，日历错通常意味
    着整行数据没有意义，优先报出来。代价：原先把 date+week 同时违规的行
    报的是 week 越界，现在报的是 date 不是合法日历日。现有测试里没有
    多违规行用例（`TestMixedFile` 两条坏行各自只踩一条规则），所以代价
    暂时"未来会付"；探针见
    `test_parse_sessions.py::TestDate::test_多违规行_date排第一_先报date`。

    副作用：三关全过时把 hours 就地转成 float。放在最后转，是为了让
    problems 里存的永远是**原始那一栏的字面**，方便照着它回去改数据。
    row["date"] **不**就地转 date 对象——problems／render 那边看到的
    类型一变，就牵对外契约。
    """
    error = date_error(row["date"])
    if error:
        return error

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


# 本模块是纯库：不提供 CLI 入口，路径由调用方传入。