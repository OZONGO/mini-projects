# test_generator.py
"""generator 测试（v1.0）

## DoD
- 不读真 sessions.md：全部夹具用 tempfile 写临时文件。
- 用例覆盖：
  1. --week 过滤在聚合前（R1 口径打脸）。
  2. 坏行全量统计，不随 --week 过滤；Markdown 有标注。
  3. --week 值域自拦：W99 / W01 / 全角 W１ 返回 2。
  4. JSON 形状：逐行 _asdict() + 嵌套递归 + ensure_ascii=False。
- 每条用例自查：改坏哪一处，它会红？
"""

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr

from generator import ReportGenerator, main


class GeneratorTest(unittest.TestCase):

    def write_sessions(self, text):
        fd, path = tempfile.mkstemp(suffix=".md")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        self.addCleanup(os.remove, path)
        return path

    def test_week_filter_before_aggregate(self):
        # 改坏哪红：若先 build_report 再过滤 week_items，
        # total_hours 会含 W3，record_count 变 3，week_items 出现 W3。
        path = self.write_sessions(
            "2026-09-14 | W2 | 1.5 | 语法 | 动词\n"
            "2026-09-15 | W2 | 2.0 | 项目 | 小工具\n"
            "2026-09-16 | W3 | 1.0 | 阅读 | 文章\n"
        )
        out = ReportGenerator(path).generate(week="W2", as_json=True)
        data = json.loads(out)
        self.assertEqual(data["total_hours"], 3.5)
        self.assertEqual(data["record_count"], 2)
        self.assertEqual(data["week_items"], [{"week": "W2", "hours": 3.5}])
        self.assertNotIn({"week": "W3", "hours": 1.0}, data["week_items"])

    def test_problems_full_scope_and_markdown_note(self):
        # 改坏哪红：若 problems 随 week 过滤，坏行 len 变 0；
        # 若 Markdown 不加标注，断言不成立。
        path = self.write_sessions(
            "2026-09-14 | W2 | 1.5 | 语法 | 动词\n"
            "2026-09-15 | W99 | 1.0 | 语法 | 越界\n"
        )
        gen = ReportGenerator(path)

        data = json.loads(gen.generate(week="W2", as_json=True))
        self.assertEqual(len(data["problems"]), 1)
        self.assertIn("W99", data["problems"][0]["line"])

        md = gen.generate(week="W2", as_json=False)
        self.assertIn("坏行清单按全量统计，不随 --week 过滤", md)

    def test_week_validation_rejects_bad_literals(self):
        # 改坏哪红：若不自己拦 --week，W99/W01/全角 W１ 会进入解析，
        # main 不会返回 2，stderr 也没有“--week 参数不合法”。
        path = self.write_sessions("2026-09-14 | W2 | 1.5 | 语法 | 动词\n")
        for bad in ("W99", "W01", "W１"):
            with self.subTest(bad=bad):
                err = io.StringIO()
                with redirect_stderr(err):
                    ret = main(["--sessions", path, "--week", bad])
                self.assertEqual(ret, 2)
                self.assertIn("--week 参数不合法", err.getvalue())

    def test_json_uses_asdict_and_ensure_ascii_false(self):
        # 改坏哪红：若直接 json.dumps(report)，week_items[0] 会是数组；
        # 若 ensure_ascii=True，输出会出现 \u8bed 之类转义。
        path = self.write_sessions("2026-09-14 | W2 | 1.5 | 语法 | 动词\n")
        out = ReportGenerator(path).generate(week=None, as_json=True)

        self.assertNotIn("\\u", out)
        data = json.loads(out)
        self.assertIsInstance(data["week_items"][0], dict)
        self.assertEqual(data["week_items"][0], {"week": "W2", "hours": 1.5})
        self.assertIsInstance(data["category_items"][0], dict)
        self.assertEqual(data["category_items"][0], {"category": "语法", "hours": 1.5})
        self.assertIsInstance(data["problems"], list)


if __name__ == "__main__":
    unittest.main()
