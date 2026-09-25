# strong/check.py
"""Harness Lab 强侧反馈件：按 feature_list.json 判据断言产物，退码说话。

退出码：
  0 = 全过
  1 = 有断言失败
  2 = 输入不可读（文件缺失 / 不是 UTF-8 / 不是 JSON）

设计纪律（照 MP1 主线）：
- 断言住 harness 侧；被试一字不改。
- 数字面用容差（若将来断言 hours），不拿 14.9 比 14.899999999999999。
- 检测必须接进判定：每条 check 的失败写进 failed 列表，最终由退出码裁决。
- 反馈质量线 = 零沉默 ＋ 零诬陷：不漏报，也不对全绿系统喊红。
- 诊断要么报真相、要么承认"无法提取"——不许把"我没看见"报告成"不存在"。
- 验证命令必须是本项目自己的尺子（unittest discover），不是课程模板示例。
"""

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # strong/
LAB_ROOT = HERE.parent                          # harness-lab/
PROJECT_ROOT = LAB_ROOT.parent                  # mp1-weekly-report/
REPORT_PATH = LAB_ROOT / "week_report.json"


# --- 产物断言 -----------------------------------------------------------

def _load_report():
    """读产物原始字节 + 解析后的对象。返回 (raw_bytes, obj) 或抛异常。"""
    raw = REPORT_PATH.read_bytes()
    text = raw.decode("utf-8")                  # 非 UTF-8 直接抛
    obj = json.loads(text)
    return raw, obj


def check_top_level_object(obj):
    if not isinstance(obj, dict):
        return f"顶层应为 object，实际是 {type(obj).__name__}"
    return None


def check_items_are_objects(obj, key):
    items = obj.get(key)
    if not isinstance(items, list):
        return f"{key} 不是 list（实际 {type(items).__name__}）"
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            return f"{key}[{i}] 应为 object，实际是 {type(item).__name__}：{item!r}"
    return None


def check_chinese_utf8_raw(raw):
    if "语法".encode("utf-8") not in raw:
        return "产物原始字节未含 UTF-8 原文“语法”"
    if b"\\u8bed" in raw:
        return "产物原始字节含 \\u8bed 转义（应为 UTF-8 原文）"
    return None


def check_week_scope_w2(obj):
    """D3：week_items 仅含 W2。

    取证纪律：条目不是 object / 缺 week 键时，**当场承认"无法提取"**并附原形，
    绝不静默过滤后报一个捏造的空集。
    """
    items = obj.get("week_items")
    if not isinstance(items, list):
        return f"week_items 不是 list（实际 {type(items).__name__}），无法判范围"

    weeks = []
    for i, it in enumerate(items):
        if not isinstance(it, dict):
            return (
                f"无法提取周次：week_items[{i}] 不是 object，"
                f"原形 {it!r}——修完形状后再判范围"
            )
        if "week" not in it:
            return (
                f"无法提取周次：week_items[{i}] 缺 'week' 键，"
                f"原形 {it!r}"
            )
        weeks.append(it["week"])

    if weeks != ["W2"]:
        return f"week_items 应只含 W2，实际含：{weeks}"
    return None


# --- MP1 主线测试套件（连带体检：确认主线未被扰动） ---------------------

def run_mp1_test_suite():
    """在 mp1-weekly-report/ 跑 MP1 自己的尺子：unittest discover。

    返回 (ok, message)。失败时 stdout 与 stderr **都**带出来——不许把
    "没装 pytest" 这种 stderr 上的真凶裁掉，只报一个孤零零的冒号。
    """
    cmd = [sys.executable, "-m", "unittest", "discover"]
    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return False, f"无法启动解释器：{sys.executable}"

    interpreter = sys.executable
    if result.returncode != 0:
        parts = []
        if result.stdout and result.stdout.strip():
            parts.append("--- stdout ---\n" + result.stdout[-800:])
        if result.stderr and result.stderr.strip():
            parts.append("--- stderr ---\n" + result.stderr[-800:])
        body = "\n".join(parts) if parts else "(stdout 与 stderr 皆空)"
        return False, (
            f"MP1 测试套件未过（exit {result.returncode}，"
            f"解释器 {interpreter}）：\n{body}"
        )
    return True, f"MP1 测试套件全过（解释器 {interpreter}）"


# --- main ---------------------------------------------------------------

def main():
    # 1) 产物可读性：不可读直接退 2
    if not REPORT_PATH.exists():
        print(f"ERROR: 找不到产物 {REPORT_PATH}", file=sys.stderr)
        return 2
    try:
        raw, obj = _load_report()
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        print(f"ERROR: 产物无法解析：{e}", file=sys.stderr)
        return 2

    # 2) 主线体检
    suite_ok, suite_msg = run_mp1_test_suite()
    print(("PASS: " if suite_ok else "FAIL: ") + f"[MP1 测试套件] {suite_msg}")

    # 3) 产物断言（每项 = feature_list.json 的一条 id）
    checks = [
        ("D1a 顶层为 object",                  lambda: check_top_level_object(obj)),
        ("D1b week_items 为 list[object]",     lambda: check_items_are_objects(obj, "week_items")),
        ("D1b category_items 为 list[object]", lambda: check_items_are_objects(obj, "category_items")),
        ("D2  中文以 UTF-8 原文在场",          lambda: check_chinese_utf8_raw(raw)),
        ("D3  仅含 W2",                        lambda: check_week_scope_w2(obj)),
    ]

    failed = []
    for name, fn in checks:
        reason = fn()
        if reason is None:
            print(f"PASS: [{name}]")
        else:
            print(f"FAIL: [{name}] —— {reason}")
            failed.append(name)

    if not suite_ok:
        failed.append("MP1 测试套件")

    if failed:
        print(f"\n{len(failed)} 项未过。", file=sys.stderr)
        return 1
    print("\n全部通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())