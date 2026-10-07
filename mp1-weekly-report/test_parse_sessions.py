#test_parse_sessions.py



"""MP1 · 解析段单元测试 —— 把手工探针固化成一条命令自动跑

## 这个文件存在的原因

看板 2026-09-11 记：「DoD 自订『三类值域各造一条真跑一次』仍未交本人终端输出」
——「说了≠做了」第三次现形，由教练探针代证。

手工探针的问题不是"不认真"，而是**它不留痕、不可重复、不报错**：
今天跑过三条，明天加了新规则，没人会记得把老的三条再跑一遍。
所以这九条边界从此不是"记得要跑"，而是"跑 pytest 就会跑"。

## 运行方式

    cd mini-projects/mp1-weekly-report
    python -m unittest test_parse_sessions -v

或直接：

    python test_parse_sessions.py

## 设计要点

被测函数 `parse_sessions(path)` 吃的是**文件路径**，不是文本。
所以所有用例都写进 `tempfile` 造的临时文件，真数据文件 `sessions.md` **一个字节都不碰**
——这正是 DoD 第 5 条"改用临时文件喂解析器，真数据文件不沾测试残留"的落地。

文件名故意不在 `test_*` 之外另起，符合 unittest 的自动发现约定。
"""

import os
import tempfile
import unittest

from parse_sessions import parse_sessions, FIELDS

# 一条合法的基线行，各用例只改其中一段，坏在哪一眼可见
GOOD_LINE = "2026-09-10 | W1 | 0.5 | 复习 | 开场清到期6卡"


def parse_text(text):
    """把文本写进临时文件，喂给解析器，返回 (rows, problems)。

    用 tempfile 而不是在项目里造文件：测完即焚，永不留下残留。
    """
    fd, path = tempfile.mkstemp(suffix=".md", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        return parse_sessions(path)
    finally:
        os.unlink(path)          # 无论断言成功失败都删掉


class TestHappyPath(unittest.TestCase):
    """能解析的必须解析对——只测「哪些被拒」的测试是不完整的。"""

    def test_单条合法行解析成功(self):
        rows, problems = parse_text(GOOD_LINE)
        self.assertEqual(len(rows), 1)
        self.assertEqual(problems, [])
        self.assertEqual(set(rows[0].keys()), set(FIELDS))

    def test_hours_转换成_float(self):
        rows, _ = parse_text(GOOD_LINE)
        self.assertIsInstance(rows[0]["hours"], float)
        self.assertEqual(rows[0]["hours"], 0.5)

    def test_说明行与空行被跳过(self):
        text = "\n".join([
            "# 这是说明行，跳过",
            "> 这是引用行，跳过",
            "",
            GOOD_LINE,
        ])
        rows, problems = parse_text(text)
        self.assertEqual(len(rows), 1)
        self.assertEqual(problems, [])

    def test_多行文件最后一行无尾换行仍被解析(self):
        """文件末尾缺换行符不是坏行：最后一条合法记录不能被 EOF 吞掉。"""
        text = "\n".join([
            GOOD_LINE,
            "2026-09-11 | W1 | 1.0 | 阅读 | 最后一行没有换行",
        ])
        rows, problems = parse_text(text)
        self.assertEqual(len(rows), 2, f"最后一行应被解析，实际问题：{problems}")
        self.assertEqual(problems, [])
        self.assertEqual(rows[-1]["hours"], 1.0)

    def test_边界周次_W0_与_W28_不误伤(self):
        """值域的两端都是合法值——下界与上界最容易在改规则时写错。"""
        text = "\n".join([
            "2026-09-01 | W0 | 1.0 | 语法 | 下界测试",
            "2026-09-02 | W28 | 1.0 | 语法 | 上界测试",
        ])
        rows, problems = parse_text(text)
        self.assertEqual(len(rows), 2, f"W0 与 W28 都该合法，实际问题：{problems}")
        self.assertEqual(problems, [])


class TestStructural(unittest.TestCase):
    """第一关：段数。不先卡这关，按位置取字段就会错位或 IndexError。"""

    def test_段数不足被判坏行(self):
        rows, problems = parse_text("2026-09-10 | W1 | 0.5")
        self.assertEqual(rows, [])
        self.assertEqual(len(problems), 1)
        self.assertIn("切出 3 段", problems[0]["reason"])

    def test_段数过多被判坏行(self):
        rows, problems = parse_text("2026-09-10 | W1 | 0.5 | 复习 | 主题 | 多余")
        self.assertEqual(rows, [])
        self.assertIn("应为 5 段", problems[0]["reason"])

    def test_坏行带出行号(self):
        """行号是坏行信息的核心：没有它，人得自己数到第几行。"""
        text = "\n".join([GOOD_LINE, "坏行 | 只有两段"])
        _, problems = parse_text(text)
        self.assertEqual(len(problems), 1)
        self.assertEqual(problems[0]["lineno"], 2)


class TestEmptyField(unittest.TestCase):
    """第二关：非空。必须排在值域之前，否则空串会被误报成"类别不在词表"。"""

    def test_空字段被判坏行(self):
        rows, problems = parse_text("2026-09-10 | W1 |  | 复习 | 主题")
        self.assertEqual(rows, [])
        self.assertEqual(len(problems), 1)
        self.assertIn("hours", problems[0]["reason"])

    def test_空类别报的是空而不是不在词表(self):
        """顺序契约的回归测试：这一条就是「值域必须排在非空之后」的守卫。

        若哪天有人把 value_error 挪到非空检查之前，这条会立刻变红——
        空串会被报成「类别 '' 不在词表」，把人往"词表少了个词"的方向带。
        """
        _, problems = parse_text("2026-09-10 | W1 | 0.5 |  | 主题")
        self.assertIn("为空", problems[0]["reason"])
        self.assertNotIn("不在词表", problems[0]["reason"])

    def test_多个空字段一起报出(self):
        _, problems = parse_text("2026-09-10 |  |  | 复习 | 主题")
        self.assertIn("week", problems[0]["reason"])
        self.assertIn("hours", problems[0]["reason"])


class TestWeekLint(unittest.TestCase):
    """第三关之二：周次判「字面是否规范」，不是「能不能解析成数字」。

    这是 2026-09-11 那场最硬的一课：`str.isdigit()` 与 `float()` 都吃
    Unicode 数字，所以「能否解析成数字」式校验会放行 W01 与全角 W１，
    三者字面不同 → dict 分组裂成三个桶 → 幽灵分组。
    """

    def test_前导零被拒(self):
        _, problems = parse_text("2026-09-10 | W01 | 0.5 | 复习 | 主题")
        self.assertIn("前导零", problems[0]["reason"])

    def test_全角数字被拒(self):
        """全角 `W１` —— isdigit() 为 True、int() 能转，但字面不合契约。"""
        _, problems = parse_text("2026-09-10 | W\uff11 | 0.5 | 复习 | 主题")
        self.assertIn("ASCII", problems[0]["reason"])

    def test_小写_w_被拒(self):
        _, problems = parse_text("2026-09-10 | w1 | 0.5 | 复习 | 主题")
        self.assertIn("大写字母 W", problems[0]["reason"])

    def test_光杆_W_被拒(self):
        _, problems = parse_text("2026-09-10 | W | 0.5 | 复习 | 主题")
        self.assertIn("ASCII", problems[0]["reason"])

    def test_越界周次被拒(self):
        _, problems = parse_text("2026-09-10 | W29 | 0.5 | 复习 | 主题")
        self.assertIn("越界", problems[0]["reason"])


class TestCategory(unittest.TestCase):
    """第三关之三：类别必须在受控词表内。

    CATEGORIES 用的是 `in` 判字面相等，所以天然对 Unicode 免疫
    —— 与 week 的写法对照，正是那节课的要点。
    """

    def test_词表外的类别被拒(self):
        _, problems = parse_text("2026-09-10 | W1 | 0.5 | 摸鱼 | 主题")
        self.assertIn("不在词表", problems[0]["reason"])

    def test_词表内五个类别全部放行(self):
        lines = [
            f"2026-09-1{i} | W1 | 0.5 | {c} | 主题{i}"
            for i, c in enumerate(["语法", "项目", "复习", "文档", "阅读"])
        ]
        rows, problems = parse_text("\n".join(lines))
        self.assertEqual(len(rows), 5, f"五个受控类别都该放行，实际问题：{problems}")


class TestHours(unittest.TestCase):
    """第三关之四：时长拆两关（2026-10-07 起，契约 v2 内修订）。

    关卡一（字面文法）自己判，锚点＝「时长字面不合契约」；关卡二（溢出）交
    `isfinite`，锚点＝「不是有限数」。每条用例**双向钉**：`assertIn` 自己那关的词，
    `assertNotIn` 另一关的词——测的是"谁拦的"，不是"拦没拦"（同 `TestDate` 先例）。

    改写记录：原四条（`abc`／`nan`／`inf`／`-1`）拦它们的关从值关换成了字面关，
    reason 换了词族，锚点随之改；其中 `-1` 的「为负」分支已随形状关删除（不可达），
    `assertNotIn("为负")` 钉的是"不许有第二条路"。
    """

    def test_非数字被拒_字面关拦(self):
        """`abc` 现由字面关拦——`float()` 抛 ValueError 那条路已删，不再可达。"""
        _, problems = parse_text("2026-09-10 | W1 | abc | 复习 | 主题")
        self.assertIn("时长字面不合契约", problems[0]["reason"])
        self.assertNotIn("不是有限数", problems[0]["reason"])

    def test_nan被拒_字面关拦(self):
        _, problems = parse_text("2026-09-10 | W1 | nan | 复习 | 主题")
        self.assertIn("时长字面不合契约", problems[0]["reason"])
        self.assertNotIn("不是有限数", problems[0]["reason"])

    def test_inf拼写被拒_字面关拦(self):
        _, problems = parse_text("2026-09-10 | W1 | inf | 复习 | 主题")
        self.assertIn("时长字面不合契约", problems[0]["reason"])
        self.assertNotIn("不是有限数", problems[0]["reason"])

    def test_负号被拒_字面关拦(self):
        """符号位整位不收：`-1` 在字面层就没了入口，值域不再需要负检查。"""
        _, problems = parse_text("2026-09-10 | W1 | -1 | 复习 | 主题")
        self.assertIn("时长字面不合契约", problems[0]["reason"])
        self.assertNotIn("为负", problems[0]["reason"])

    def test_下划线被拒(self):
        """本关存在的理由。`float("1_0") == 10.0`（PEP 515），人读作 1.0——十倍静默。"""
        _, problems = parse_text("2026-09-10 | W1 | 1_0 | 复习 | 主题")
        self.assertIn("时长字面不合契约", problems[0]["reason"])
        self.assertNotIn("不是有限数", problems[0]["reason"])

    def test_全角数字被拒(self):
        """`float("１２３") == 123.0`：isdigit 为 True、转换能过，唯独字面不合契约。"""
        _, problems = parse_text("2026-09-10 | W1 | \uff11\uff12\uff13 | 复习 | 主题")
        self.assertIn("时长字面不合契约", problems[0]["reason"])
        self.assertNotIn("不是有限数", problems[0]["reason"])

    def test_漂浮点被拒(self):
        for text in (".5", "1."):
            with self.subTest(text=text):
                _, problems = parse_text(f"2026-09-10 | W1 | {text} | 复习 | 主题")
                self.assertIn("时长字面不合契约", problems[0]["reason"])
                self.assertNotIn("不是有限数", problems[0]["reason"])

    def test_科学计数与正号被拒(self):
        for text in ("1e2", "+3"):
            with self.subTest(text=text):
                _, problems = parse_text(f"2026-09-10 | W1 | {text} | 复习 | 主题")
                self.assertIn("时长字面不合契约", problems[0]["reason"])
                self.assertNotIn("不是有限数", problems[0]["reason"])

    def test_多个小数点被拒(self):
        _, problems = parse_text("2026-09-10 | W1 | 2.5.5 | 复习 | 主题")
        self.assertIn("小数点至多一个", problems[0]["reason"])
        self.assertNotIn("不是有限数", problems[0]["reason"])

    def test_超长数字串溢出_值关拦(self):
        """形状过关≠数值安全：`float("9"*400)` 交 `inf` 不报错，只有 `isfinite` 拦得住。

        这条是"字面关吞不掉值关"的证据，也是本次收紧不许把 `isfinite` 当死代码删掉的理由。
        """
        _, problems = parse_text(f"2026-09-10 | W1 | {'9' * 400} | 复习 | 溢出")
        self.assertIn("不是有限数", problems[0]["reason"])
        self.assertNotIn("时长字面不合契约", problems[0]["reason"])

    def test_合法字面放行(self):
        for text in ("0", "0.8", "2.5", "13.5", "2.50"):
            with self.subTest(text=text):
                rows, problems = parse_text(f"2026-09-10 | W1 | {text} | 复习 | 主题")
                self.assertEqual(len(rows), 1, f"{text} 应合法，实际问题：{problems}")

    def test_零合法(self):
        """0 是合法时长——下界是「字面为 0」，不是「大于 0」。"""
        rows, problems = parse_text("2026-09-10 | W1 | 0 | 复习 | 主题")
        self.assertEqual(len(rows), 1, f"0 应当合法，实际问题：{problems}")


class TestDate(unittest.TestCase):
    """第三关之一（2026-09-28 新增）：日期拆两关。

    关卡一（形状）自己判：长度、分隔符位置、ASCII 数字。关卡二（日历）
    交给 `date.fromisoformat`。为什么形状不能交给库——见 parse_sessions
    模块 DoD 设计决定四。
    """

    def test_非法日历日_13月被拒(self):
        """形状过、日历拒——关卡二真在办事的第一枪。"""
        _, problems = parse_text("2026-13-99 | W1 | 0.5 | 复习 | 坏日历日")
        self.assertEqual(len(problems), 1)
        self.assertIn("不是合法日历日", problems[0]["reason"])

    def test_非法日历日_2月30日被拒(self):
        """2 月 30 日：形状过，日历拒。"""
        _, problems = parse_text("2026-02-30 | W1 | 0.5 | 复习 | 坏日历日")
        self.assertIn("不是合法日历日", problems[0]["reason"])

    def test_basic格式被拒(self):
        """`20261129` 是合法日期，但不是本契约的合法字面——长度关先拦。"""
        _, problems = parse_text("20261129 | W1 | 0.5 | 复习 | basic 格式")
        self.assertIn("长度", problems[0]["reason"])
        self.assertNotIn("不是合法日历日", problems[0]["reason"])

    def test_ISO周日期被拒(self):
        """`2026-W48-3` 是合法日期，但字面不合契约——分隔符位置先拦。"""
        _, problems = parse_text("2026-W48-3 | W1 | 0.5 | 复习 | ISO 周日期")
        self.assertIn("分隔符", problems[0]["reason"])
        self.assertNotIn("不是合法日历日", problems[0]["reason"])

    def test_不补零被拒(self):
        """`2026-1-1` 是合法日期，但字面不合契约——长度关先拦。"""
        _, problems = parse_text("2026-1-1 | W1 | 0.5 | 复习 | 不补零")
        self.assertIn("长度", problems[0]["reason"])
        self.assertNotIn("不是合法日历日", problems[0]["reason"])

    def test_全角年份被拒(self):
        """全角 `２` —— isdigit() 为 True、int() 能转，但字面不合契约。
        形状关用 isascii() 挡下，不交给库去归一化——这是 N008 第⑥条
        「误放方向」的反向用法。"""
        _, problems = parse_text("20\uff126-09-28 | W1 | 0.5 | 复习 | 全角年份")
        self.assertIn("ASCII", problems[0]["reason"])

    def test_正常日期放行(self):
        """只测"哪些被拒"的测试是不完整的——正常行必须过。"""
        rows, problems = parse_text("2026-09-10 | W1 | 0.5 | 复习 | 正常日期")
        self.assertEqual(len(rows), 1, f"正常日期应放行，实际问题：{problems}")
        self.assertEqual(problems, [])
        self.assertEqual(rows[0]["date"], "2026-09-10")

    def test_多违规行_date排第一_先报date(self):
        """顺序探针：date 与 week 同时违规时，reason 只报第一条命中。

        date 按 FIELDS 契约顺序放在 value_error 第一位，所以先报 date。
        如果哪天有人把 date 挪到 week 后面，这条会立刻变红——
        与 test_空类别报的是空而不是不在词表 同一个形状（assertIn +
        assertNotIn 双向钉"第一条命中是谁"）。
        """
        _, problems = parse_text("2026-13-99 | W99 | 0.5 | 复习 | 多违规靶")
        self.assertEqual(len(problems), 1)
        self.assertIn("不是合法日历日", problems[0]["reason"])
        self.assertNotIn("越界", problems[0]["reason"])


class TestMixedFile(unittest.TestCase):
    """一条坏行不该带走好行——坏行隔离是解析器的基本职责。"""

    def test_好坏行混排只拒坏的(self):
        text = "\n".join([
            GOOD_LINE,
            "2026-09-10 | W99 | 0.5 | 复习 | 越界周次",
            GOOD_LINE,
            "2026-09-10 | W1 | 0.5 | 摸鱼 | 非法类别",
            GOOD_LINE,
        ])
        rows, problems = parse_text(text)
        self.assertEqual(len(rows), 3)
        self.assertEqual(len(problems), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)