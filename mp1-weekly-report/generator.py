# generator.py
"""唯一 CLI 入口（v1.0）

## DoD
- 唯一入口：parse_sessions / aggregate / render 均为库；本文件是 CLI 入口。
- ReportGenerator.__init__(sessions_path) 构造期收口路径；
  generate(week=None, as_json=False) 只吃“这一次要什么”。
- 过滤落点：--week 在 parse_sessions 之后、build_report 之前过滤合法 rows。
  理由：total_hours / record_count / week_items / category_items 必须同一口径；
  先全量 build_report 再挑 week_items，会导致合计与表格互相打脸。
- 坏行口径＋标注措辞：problems 全量传给 build_report，不随 --week 过滤。
  Markdown 输出时若 --week 非空且 problems 非空，由本层加一行标注：
  “坏行清单按全量统计，不随 --week 过滤。”
  标注只在本层加，不在 render 层——render 从 report 六键无从得知过滤与否，
  替上层编事等于在 render 里复制一份口径事实。
- 入口去留：v1.0 只保留 generator.py 入口；render.py 不再提供 main()。
- JSON 落点：JSON 打 stdout，不写盘。写盘是运行产物，按 9/21 判据须删或进
  .gitignore；v1.0 不引入未跟踪运行产物。
- --week 值域自拦：W99 / W01 / 全角 W１ 均拒，返回退出码 2；
  不依赖 argparse type=，也不用 parser.error 代劳。
- JSON 形状：逐行 _asdict() + 嵌套递归 + ensure_ascii=False。
- 数字面：JSON 是事实层，浮点原样（14.899999999999999 是 float 求和的真实结果）；
  Markdown 是展示层，一律 :.1f。两份产物数字面不同，对账以 JSON 为准。
- 硬约束：parse_sessions / build_report / render_markdown 签名与 report 六键一字不动。
"""

import argparse
import json
import sys
from typing import NamedTuple

from parse_sessions import parse_sessions, week_error
from aggregate import build_report
from render import render_markdown


# --- 全工程唯一默认路径：改路径只改这一处 ---------------------------------
SESSIONS_PATH = "../../learning-log/sessions.md"


class WeekItem(NamedTuple):
    week: str
    hours: float


class CategoryItem(NamedTuple):
    category: str
    hours: float


def _to_jsonable(obj):
    """逐行 _asdict() + 嵌套递归。

    report 六键本身不动；这里只把 week_items / category_items 的 tuple
    逐行包成 NamedTuple，再用 _asdict() 转对象。
    """
    if hasattr(obj, "_asdict"):
        return {k: _to_jsonable(v) for k, v in obj._asdict().items()}
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(v) for v in obj]
    return obj


def _report_to_jsonable(report):
    """把 report 转成适合 JSON 输出的结构，不改 report 本身。"""
    data = dict(report)
    data["week_items"] = [
        WeekItem(week, hours)
        for week, hours in report["week_items"]
    ]
    data["category_items"] = [
        CategoryItem(category, hours)
        for category, hours in report["category_items"]
    ]
    data["problems"] = [dict(p) for p in report.get("problems", [])]
    return _to_jsonable(data)


class ReportGenerator:
    """构造期收口 sessions_path，方法只吃“这一次要什么”。"""

    def __init__(self, sessions_path):
        self.sessions_path = sessions_path

    def generate(self, week=None, as_json=False):
        rows, problems = parse_sessions(self.sessions_path)

        if week is not None:
            error = week_error(week)
            if error:
                raise ValueError(error)
            # 口径层过滤：在聚合前缩小被统计的合法行集。
            rows = [row for row in rows if row["week"] == week]

        report = build_report(rows, problems)

        if as_json:
            return json.dumps(
                _report_to_jsonable(report),
                ensure_ascii=False,
                indent=2,
            )

        md = render_markdown(report)
        if week is not None and report.get("problems"):
            md = f"> 坏行清单按全量统计，不随 --week 过滤。\n\n{md}"
        return md


def main(argv=None):
    parser = argparse.ArgumentParser(description="MP1 学习周报生成器")
    parser.add_argument(
        "--sessions",
        default=SESSIONS_PATH,
        help=f"sessions.md 路径（默认：{SESSIONS_PATH}）",
    )
    parser.add_argument(
        "--week",
        default=None,
        help="只统计某一周，例如 W2；坏行清单仍按全量统计",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="输出 JSON 而不是 Markdown",
    )
    args = parser.parse_args(argv)

    if args.week is not None:
        error = week_error(args.week)
        if error:
            print(f"error: --week 参数不合法：{error}", file=sys.stderr)
            return 2

    generator = ReportGenerator(args.sessions)
    output = generator.generate(week=args.week, as_json=args.json)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
