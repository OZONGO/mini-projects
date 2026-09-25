# harness-lab/fake_agent.py
"""弱轮被试脚本：生成 week_report.json。

纪律：两轮共用本脚本、一字不改。
自评：进程没崩 + week_report.json 写出来了 → 退 0。
硬约束：不调用 generator.py 的 ReportGenerator / _report_to_jsonable。
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # harness-lab/
PROJECT_ROOT = HERE.parent                      # mp1-weekly-report/
sys.path.insert(0, str(PROJECT_ROOT))

from parse_sessions import parse_sessions
from aggregate import build_report

# 与 generator.py 的默认路径口径一致：从 mp1-weekly-report/ 往上看两级。
SESSIONS_PATH = PROJECT_ROOT.parent.parent / "learning-log" / "sessions.md"
OUT_PATH = HERE / "week_report.json"


def main():
    rows, problems = parse_sessions(SESSIONS_PATH)
    report = build_report(rows, problems)

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        # 裸序列化：week_items / category_items 里的 tuple 会变成 array；
        # 中文键走 json.dump 默认 ensure_ascii=True，会变成 \uXXXX。
        json.dump(report, f, indent=2)

    print(f"任务完成：{OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())