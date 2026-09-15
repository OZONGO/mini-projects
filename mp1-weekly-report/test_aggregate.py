"""MP1 · 学习周报生成器 —— 聚合段测试（v0.3 步骤 6）

## DoD：本文件守住 build_report 的哪几条契约
1. total_hours == 各行 hours 之和（手算的和写进预测注释）。
2. record_count == len(rows)，且不含坏行（坏行在 problems 里，不在 rows 里）。
3. week_items 按 week_no 数字升序：夹具含 W2 与 W10 这对“字典序反向”周次，
   断言 W2 排在 W10 前。删掉 key=week_no 这把尺子必红。
4. category_items 按 hours 降序：夹具造出“降序 ≠ 首次出现序”的组合。
   把排序键从时长换掉必红。
5. 同分保持稳定（先出现者在前）：夹具造一分真同分，首次出现序可被观测。
   把 reverse=True 换成“升序再整体翻转”的写法必红
   ——Python sorted 天生稳定，只有“排完再翻”才破坏同分序。
6. problems 原样传递：lineno/reason 一字不差；空 problems 时也是空列表。
7. td1_bias 来自 TD1_BIAS_ACTIVE 常量：用 mock.patch 翻常量，断言 report 跟着翻
   ——断“来源”，不断“当前取值”，v3 改常量不误伤。
8. 聚合只读不改：调用前后 rows 深拷贝相等。

## 不测什么，以及为什么不测
- build_report “没有 print / 没碰文件”：结构上不存在那些行，测它等于测
  “这段代码没写那几行”，是浪费。
- md 文案 / 渲染格式：那是 render 的活，归 test_render.py。
- parse → aggregate 的串联：那是集成测试，不是本层。
- total_hours 用脏浮点收口：收口是 render 的 :.1f 负责，聚合层不负责显示，
  这里用二进制精确的数（1.0/0.5/2.0）避开噪声，让断言本身更干净。

## 红线
绝不读真的 sessions.md。夹具是本文件手写的 dict，每个值我都知道。

## 预测注释先行
每条断言前用 `# 预测：...` 写下预期，再跑，再对账。

## 变异实测记录（本次验收核心，三组，逐组单独施加、跑完立即还原）
| 变异 | 改哪一处 | 期望红哪条 | 实测红哪条 | 对账 |
|---|---|---|---|---|
| A | 删 week_items 的 key=week_no | test_week_items按数字升序 | test_week_items按数字升序 | 命中：1 红 / 8 绿 |
| B | category 排序键从 item[1] 换成 item[0] | test_category_items按时长降序 | test_category_items按时长降序 | 命中：1 红 / 8 绿 |
| C | category 降序改“升序再整体翻转” | test_同分稳定 | test_同分稳定 | 命中：1 红 / 8 绿 |

三条变异各只打掉一条、互不干扰，说明每条测试只对自己的那条契约敏感。
基线（还原后无变异）：`Ran 9 tests ... OK`；`test_render.py` 8 绿；`render.py` 输出正常。

**本层最值得记住的一条**：这三处变异里，A 与 C 同时生效时 `render.py` 的输出
**一个字都不会变**——因为真数据只有 W1/W2（字典序＝数字序）且类别无同分，
恰好落在盲区。变异测试的价值不在“改坏了会红”，而在
“改坏了外面看不出来时，只有反向夹具能看见它”。
"""

import copy
import unittest
from unittest import mock

import aggregate
from aggregate import build_report


class Test聚合段契约(unittest.TestCase):

    def test_total_hours等于各行之和(self):
        # 夹具：1.0 + 0.5 + 2.0 = 3.5，全是二进制精确数，无浮点噪声
        rows = [
            {"week": "W1", "hours": 1.0, "category": "语法"},
            {"week": "W1", "hours": 0.5, "category": "复习"},
            {"week": "W2", "hours": 2.0, "category": "语法"},
        ]
        # 预测：total_hours == 3.5
        report = build_report(rows, [])
        self.assertEqual(report["total_hours"], 3.5)

    def test_record_count等于len_rows且不含坏行(self):
        rows = [
            {"week": "W1", "hours": 1.0, "category": "语法"},
            {"week": "W1", "hours": 0.5, "category": "复习"},
            {"week": "W2", "hours": 2.0, "category": "语法"},
        ]
        problems = [
            {"lineno": 99, "line": "坏行1", "reason": "切出 3 段，应为 5 段"},
            {"lineno": 100, "line": "坏行2", "reason": "hours 不是数字"},
        ]
        # 预测：record_count == 3，坏行不计入
        report = build_report(rows, problems)
        self.assertEqual(report["record_count"], 3)

    def test_week_items按数字升序_W2在W10前(self):
        # 夹具故意让 W10 先出现、W2 后出现，首次出现序与数字序相反
        rows = [
            {"week": "W10", "hours": 1.0, "category": "语法"},
            {"week": "W2", "hours": 2.0, "category": "语法"},
        ]
        # 预测：week_items == [("W2", 2.0), ("W10", 1.0)]
        # 若 key=week_no 被删，字典序会给 [("W10", 1.0), ("W2", 2.0)]，必红
        report = build_report(rows, [])
        self.assertEqual(report["week_items"], [("W2", 2.0), ("W10", 1.0)])

    def test_category_items按时长降序_与首次出现序相反(self):
        # 夹具：语法先出现但只有 1.0，复习后出现但有 3.0
        # 首次出现序 = [语法, 复习]；降序 = [复习, 语法]——两者相反
        rows = [
            {"week": "W1", "hours": 1.0, "category": "语法"},
            {"week": "W1", "hours": 3.0, "category": "复习"},
        ]
        # 预测：category_items == [("复习", 3.0), ("语法", 1.0)]
        report = build_report(rows, [])
        self.assertEqual(report["category_items"], [("复习", 3.0), ("语法", 1.0)])

    def test_同分稳定_先出现者在前(self):
        # 夹具：语法与复习都是 1.0（真同分），语法先出现
        # Python sorted 稳定 → 同分时保留先出现者在前
        rows = [
            {"week": "W1", "hours": 1.0, "category": "语法"},
            {"week": "W1", "hours": 1.0, "category": "复习"},
        ]
        # 预测：category_items == [("语法", 1.0), ("复习", 1.0)]
        # 若降序改成“升序再整体翻转”，同分被倒过来 → [复习, 语法]，必红
        report = build_report(rows, [])
        self.assertEqual(report["category_items"], [("语法", 1.0), ("复习", 1.0)])

    def test_problems原样传递(self):
        problems_in = [
            {"lineno": 12, "line": "坏行甲", "reason": "列数不对"},
            {"lineno": 27, "line": "坏行乙", "reason": "hours 不是数字"},
        ]
        # 预测：problems 一字不差传回，连 line 都在
        report = build_report([], problems_in)
        self.assertEqual(report["problems"], problems_in)

    def test_problems为空时也是空列表(self):
        # 预测：problems == []
        report = build_report([], [])
        self.assertEqual(report["problems"], [])

    def test_td1_bias来自常量_翻常量report跟着翻(self):
        # 断“来源”而不是“当前取值”：把常量翻成相反值，report 应跟着翻。
        # v3 真修 TD-1 改常量取值，这条不红——它锁的是“读常量”这件事。
        flipped = not aggregate.TD1_BIAS_ACTIVE
        with mock.patch("aggregate.TD1_BIAS_ACTIVE", flipped):
            # 预测：report["td1_bias"] == flipped（跟着被 patch 的常量走）
            report = build_report([], [])
        self.assertEqual(report["td1_bias"], flipped)

    def test_聚合只读不改_rows前后一致(self):
        rows = [
            {"week": "W1", "hours": 1.0, "category": "语法"},
            {"week": "W2", "hours": 2.0, "category": "复习"},
        ]
        problems = [{"lineno": 3, "line": "坏行", "reason": "x"}]
        snapshot_rows = copy.deepcopy(rows)
        snapshot_problems = copy.deepcopy(problems)

        build_report(rows, problems)

        # 预测：rows 与 problems 调用前后一模一样
        self.assertEqual(rows, snapshot_rows)
        self.assertEqual(problems, snapshot_problems)


if __name__ == "__main__":
    unittest.main(verbosity=2)