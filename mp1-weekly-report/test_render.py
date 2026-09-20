#test_render.py
"""MP1 · 学习周报生成器 —— 渲染段测试（v0.1 步骤 4.5）

## DoD：本文件守住 render_markdown 的哪几条契约
1. problems 非空 → 输出里出现一个“## 坏行”二级标题，且每条的行号与 reason
   原文出现。整句标题文案归单独一条测试守（见 test_坏行标题的当前文案）。
2. problems 为空 → 坏行段整段不出现（“有才出现”的另一半，沉默型 bug 高发区）。
3. td1_bias 为 True → TD-1 警示语出现；为 False → 警示语不出现。
4. 浮点收口：脏数（0.1+0.2 家族）在输出里显示为 :.1f，不露 0.30000000000000004。
5. 周序不重排：夹具故意给与契约相反的序，输出 = 夹具序。
6. 类别序不重排：同上，类别也守一条。

## 夹具顺序原则（本文件的核心纪律）
base 的顺序必须“刻意与契约相反”，这样任何一条用 base 的测试都天生免疫
“排对了 vs 没排序观测不可分”的盲点。
- week_items 契约是 W0→W28 升序 → base 给 W10 在前。
- category_items 契约是时长降序 → base 给升序。
任何一条顺序类断言，都必须喂与正确答案相反的数据才有观测效力。

## 不测什么，以及为什么不测
- “零 print、零 IO”：结构上不可能——render_markdown 没有 print、没有 open、
  没有路径参数，测它等于测“这段代码没写那几行”，是浪费。
- markdown 语法是否合法：那是 markdown 解析器的活。
- 措辞/emoji 风格：会变。若某句当前文案值得守，单开一条名字里带“当前文案”
  的测试，红的时候一眼知道该红谁（见 test_坏行标题的当前文案）。

## 红线
绝不读真的 sessions.md。夹具是本文件手写的 dict，每个值我都知道。

## 预测注释先行
每条断言前用 `# 预测：...` 写下预期，再跑，再对账。
"""

import unittest

from render import render_markdown


def make_report(**overrides):
    """夹具工厂：每个字段都是我亲手定的，不用生产数据。

    关键：base 的顺序刻意与契约相反——
    - week_items 契约是 W0→W28 升序 → base 给 W10 在前；
    - category_items 契约是时长降序 → base 给升序。
    这样任何用 base 的测试，在“render 擅自重排”时都会红。
    若 base 恰好等于契约顺序，“排对了”和“没排序”观测上无法区分。
    """
    base = {
        "total_hours": 3.0,
        "record_count": 2,
        "week_items": [("W10", 2.0), ("W2", 1.0)],        # 契约要求升序，故反着给
        "category_items": [("复习", 1.0), ("语法", 2.0)],  # 契约要求降序，故反着给
        "problems": [],
        "td1_bias": False,
    }
    base.update(overrides)
    return base


class Test渲染段契约(unittest.TestCase):

    def test_坏行非空_是二级标题_且行号与reason原文出现(self):
        report = make_report(problems=[
            {"lineno": 12, "reason": "列数不对"},
            {"lineno": 27, "reason": "hours 不是数字"},
        ])
        md = render_markdown(report)

        # 预测：输出里出现一个二级标题 “## 坏行”
        # （只卡“它是二级标题”这一件事；整句文案归下面那条专门的测试守）
        self.assertIn("## 坏行", md)

        # 预测：逐条出现 “第 12 行：列数不对”“第 27 行：hours 不是数字”
        self.assertIn("第 12 行：列数不对", md)
        self.assertIn("第 27 行：hours 不是数字", md)

    def test_坏行标题的当前文案(self):
        """这条锁的是“当前措辞”，不是契约。
        将来产品要改成 emoji 风，就连这条测试一起改——
        别让别的测试因为文案变了而红，那会红错人。
        """
        report = make_report(problems=[{"lineno": 1, "reason": "x"}])

        # 预测：输出含完整标题 “## 坏行（1 条，已隔离，不计入聚合）”
        self.assertIn("## 坏行（1 条，已隔离，不计入聚合）", render_markdown(report))

    def test_坏行为空_整段不出现(self):
        report = make_report(problems=[])
        md = render_markdown(report)

        # 预测：输出里完全不出现“坏行”这个词——标题、正文都不该有
        self.assertNotIn("坏行", md)
        self.assertNotIn("已隔离", md)

    def test_td1为真_警示语出现(self):
        report = make_report(td1_bias=True)
        md = render_markdown(report)

        # 预测：输出含 “TD-1” 与 “口径偏差”
        self.assertIn("TD-1", md)
        self.assertIn("口径偏差", md)

    def test_td1为假_警示语不出现(self):
        report = make_report(td1_bias=False)
        md = render_markdown(report)

        # 预测：输出里不出现 “TD-1”，也不出现“口径偏差”
        self.assertNotIn("TD-1", md)
        self.assertNotIn("口径偏差", md)

    def test_浮点收口_脏数显示一位小数(self):
        # 0.1 + 0.2 = 0.30000000000000004，这是夹具里的“脏数”
        dirty = 0.1 + 0.2
        report = make_report(
            total_hours=dirty,
            week_items=[("W2", dirty)],
            category_items=[("语法", dirty)],
            record_count=1,
        )
        md = render_markdown(report)

        # 预测：出现 “0.3h”（合计行、周行、类别行都该是 0.3h）
        self.assertIn("0.3h", md)

        # 预测：不出现 “0.30000000000000004” 或任何长尾
        self.assertNotIn("0.30000000000000004", md)

    def test_周序不重排_夹具顺序即输出顺序(self):
        # 显式喂与契约相反的顺序：W10 在 W2 前
        report = make_report(week_items=[("W10", 2.0), ("W2", 1.0)])
        md = render_markdown(report)

        # 预测：W10 行出现在 W2 行之前——render 没动过手
        self.assertLess(md.index("| W10 |"), md.index("| W2 |"))

    def test_类别序不重排_夹具顺序即输出顺序(self):
        # 显式喂与契约相反的顺序：升序（契约是降序）
        report = make_report(category_items=[("复习", 1.0), ("语法", 2.0)])
        md = render_markdown(report)

        # 预测：复习行出现在语法行之前——render 没动过手
        self.assertLess(md.index("| 复习 |"), md.index("| 语法 |"))


if __name__ == "__main__":
    unittest.main(verbosity=2)