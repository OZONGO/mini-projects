# MP1 · 学习周报生成器

> 起草：AI ｜ 内容确认：OZONGO

## 做什么

读取学习记录里的会话日志，统计学习情况（总学时、按周、按类别分布），生成一份 markdown 周报，或改走 JSON 给别的工具消费。

## 输入 / 输出

- 输入：`learning-log/sessions.md`（会话日志，契约 v2 五个字段：`日期 | 周次 | 时长h | 类别 | 主题`；默认路径 `../../learning-log/sessions.md` 按 CWD 解析，可用 `--sessions` 覆盖）
- 输出：markdown 周报（默认）或 JSON（`--json`），**两者都只走 stdout、不写盘**；「写入 `learning-log/weeks/`」到 v1.0 仍未做，属未兑现项

## 架构（三段式流水线 ＋ 一个入口层）

```
自由文本 --parse--> rows/problems --按 --week 过滤 rows--> --aggregate--> report --render--> md / JSON
                        ↑ 过滤与分发在入口层 generator.py，三段均为纯库
```

三段各自独立、各自会变：改输入格式只动 parse，改统计口径只动 aggregate，改排版只动 render；改命令行形状只动 generator。

v1.0 立的两条口径规矩：
- **过滤发生在聚合之前**——`--week` 缩小的是"被统计的行集"，让 `total_hours`／`record_count`／`week_items`／`category_items` 同源同口径。先全量聚合再挑表格，同一份报告的合计与表格会互相打脸。
- **坏行清单按全量统计、不随 `--week` 过滤**，且这句标注由**入口层**加：`problems` 只有 `lineno`/`line`/`reason`，没有可靠 week 可筛；"是否被过滤"也不在 report 六键里，render 要提它就只能自己编事——同 `td1_bias` 必须由 aggregate 提供、不由 render 猜。

## 进度

- [x] v0.1 · 步骤 0：仓库骨架
- [x] v0.1 · 步骤 1：立 `sessions.md` 输入契约 ＋ 样本
- [x] v0.1 · 步骤 2：`parse_sessions.py` 解析器（parse 段）——三类检查：段数 → 非空 → 值域（周次／类别／时长）
- [x] v0.1 · 步骤 2.5：契约 v1 → v2，新增受控字段 `类别`（词表 5 值，解析器拒绝词表外的值）
- [x] v0.1 · 步骤 2.6：`test_parse_sessions.py` 测试固化（24 用例，把九条手工探针变成一条命令）
- [x] v0.1 · 步骤 3：`aggregate.py` 聚合段——同构 `group_sum` 一函数吃两本账；`week_no` 尺子按数字排周序（字典序毒已解）；TD-1 口径偏差显著入输出（方案 a，`actor` 留 v3）
- [x] v0.1 · 步骤 4：`render.py` 渲染段——`render_markdown(report)` 纯函数（零 print／零路径／零 sum／零排序）；`report` 契约把顺序物化进 `list[tuple]`，render 不得再排序；数字一律 `:.1f` 收口；TD-1「事实归 aggregate、措辞归 render」（`td1_bias` 开关）；三段式流水线打通
- [x] v0.1 · 步骤 4.5：`test_render.py` 测试固化（8 用例，守住渲染段五条契约）——纯函数的夹具就是一个**手写的 report dict**，比解析段的 `tempfile` 轻一个数量级；`make_report(**overrides)` 工厂的 base 顺序**刻意与契约相反**（周次 W10 在前、类别升序），否则"排对了"与"没排序"在观测上无法区分；**测试绝不读真 `sessions.md`**
- [x] v0.1 · 步骤 4.6：`test_aggregate.py` 测试固化（9 用例，守住聚合段八条契约：合计／条数／周序数字尺子／类别降序／同分稳定／problems 原样／td1_bias 来自常量／只读不改）——夹具是**手写的 rows dict**；**变异实测三组**（①删 `key=week_no` 尺子 ②类别排序键从时长换成组名 ③降序改写成"升序再整体翻转"）各自**只打掉对应那一条**测试，其余 8 条全绿＝"一测一守"。**本步最值钱的发现是"沉默型变异"**：真数据只有 W1/W2（字典序＝数字序）且类别无同分，①②③里有两处同时生效时 `render.py` 的输出**一个字都不会变**——变异测试的价值不在"改坏了会红"，而在"改坏了外面看不出来时，只有反向夹具能看见它"
- [ ] v1.0：`ReportGenerator` 类 ＋ CLI 参数（`--week W2`，字面沿用契约 v2 的 `W1` 而非 ISO `2026-W40`）＋ JSON 导出 ＋ 4 个测试 ＋ 入口层收口（`render.py`/`parse_sessions.py` 的 `__main__` 与两处硬编码路径一并删除，路径只留 `generator.py` 一份）

## 怎么用

```bash
cd mini-projects/mp1-weekly-report    # 默认路径按 CWD 解析；或用 --sessions 显式给

py -3.13 generator.py                          # 全量 md 周报
py -3.13 generator.py --week W2                # 只统计 W2（合计与表格同源）
py -3.13 generator.py --week W2 --json         # JSON 走 stdout
py -3.13 generator.py --sessions <路径> --week W2   # 喂夹具，不碰真数据

py -3.13 -m unittest discover                  # 45 例，改任何校验/口径/排版契约后跑
py -3.13 generator.py --week W99; echo $LASTEXITCODE   # 2，报错走 stderr
```

三段都是纯库，**没有各自的入口**：`python render.py`、`python parse_sessions.py` 自 v1.0 起不存在。

## 已知技术债

| 位置 | 问题 | 处理时机 |
|---|---|---|
| `date` 字段 | 完全未校验格式，`2026-13-99` 照收 | **未触发**（v1.0 的 `--week` 按 `week` 字段等值过滤，不做日期比较）。将来引入日期区间统计（如 `--since`）前必须先补这一关，否则比较结果静默错 |
| `hours` 字段 | 吃 Unicode 数字与下划线字面（`float("１２３")`、`float("1_0")`） | **未触发**（v1.0 只累加、不比较）。参与比较或排序尺子前处理 |
| md 与 JSON 的同一字段**数字面不一致** | md 经 `:.1f` 收口出 `14.9h`，JSON 直出原值 `14.899999999999999`（浮点累加噪声）。两份产物对不上眼 | **已裁决（2026-09-24，本人）**：JSON 属事实层，**原样输出、对账以 JSON 为准**；md 的数字是展示层舍入，不作对账依据 |
| `generator.py` → `week_error` | CLI 的 `--week` 值域复用 `parse_sessions.week_error`——**单一真相源、零复制**（v1.0 有意为之）。代价：`week_error` 事实上升级为公共 API，CLI 合法集与 parse 合法集绑死，改 `WEEK_MAX` 两处同变 | 契约 v3 把词表／上界从 `sessions.md` 读出来时，两处一起解绑 |
| `category` 语义 | 与「学习时长」口径错位——教练劳动产出"文档"但不计入时长，按类别求和天然偏高 | **已裁决（2026-09-12，方案 a）**：事实由 `aggregate.py` 的 `TD1_BIAS_ACTIVE` 常量提供，⚠ 文案在 `render.py`；`actor` 字段留契约 v3（详见 `parse_sessions.py` 末尾技术债条目）。**v3 修好后把 `TD1_BIAS_ACTIVE` 改成 False，只改这一行** |

