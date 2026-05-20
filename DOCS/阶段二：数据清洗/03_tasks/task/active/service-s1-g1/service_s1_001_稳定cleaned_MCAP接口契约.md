# L3 微元任务：稳定 cleaned MCAP 接口契约

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景一：提取夹爪开合以及位姿转换
L1：service_s1
功能组：service-s1-g1
L2 能力：cleaned MCAP 契约稳定
L3 编号：service_s1_001
任务类别：数据定义类

## 2. 本次目标

```text
稳定场景一对下游公开的 CleanedMcap、Scene1Config、Scene1CleanReport 契约，并同步场景二上游接口说明。
```

## 3. 本次不做

- 不修改源码。
- 不生成浏览器标定配置。
- 不实现夹爪宽度、位姿转换或输出校验算法。

## 4. 执行对象

- `DOCS/阶段二：数据清洗/02_service/场景一/功能模块清单.md`
- `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/`
- `DOCS/阶段二：数据清洗/02_service/场景一/L2能力模块/cleaned MCAP契约稳定.md`
- `DOCS/阶段二：数据清洗/02_service/场景二/功能模块清单.md`

## 5. 上游接口确认

```text
本 L3 直接依赖的上游功能：阶段一 raw MCAP 采集产物
上游接口定义位置：阶段一 raw MCAP topic 记录与场景一功能模块清单
当前 L3 期望消费的字段 / 文件 / 返回值：raw MCAP、Scene1Config、CleanedMcap、Scene1CleanReport
是否存在接口冲突：当前旧代码仍可能替换 pose payload；目标契约要求 raw pose 保留或可追溯
如果有冲突，本次处理策略：文档中明确“旧实现现实”和“目标契约”区别，代码改造交给 g5/g6
```

## 6. 预期改动形态

- `CleanedMcap` 明确 raw pose、common camera pose、common TCP pose、gripper width 的契约。
- `Scene1Config` 明确 gripper calibration 与 frame alignment 的配置入口。
- `Scene1CleanReport` 能承载配置来源、raw pose 保留状态、topic 数量和失败原因。
- 场景二文档只引用场景一已定义的数据概念，不自行发明字段。

## 7. 验收重点

- 每个被 L2/L3 引用的数据概念都有独立 `L2数据定义/*.md`。
- 功能模块清单中的数据概念使用可解析 wikilink。
- 场景二能明确知道 cleaned MCAP 的 gripper、camera pose、TCP pose 和 raw pose 追溯策略。

## 8. 必读上下文

1. `DOCS/工作流/阶段二开发范式.md`
2. `DOCS/阶段二：数据清洗/约束文件/L3功能组目录约束.md`
3. `DOCS/阶段二：数据清洗/02_service/场景一/功能模块清单.md`
4. `DOCS/阶段二：数据清洗/02_service/场景一/L2能力模块/cleaned MCAP契约稳定.md`

## 9. TDD 执行要求

本 L3 不涉及代码修改，不需要使用 `$tdd`。

## 10. 允许修改

- `DOCS/阶段二：数据清洗/02_service/场景一/`
- `DOCS/阶段二：数据清洗/02_service/场景二/功能模块清单.md`
- 当前 L3 任务文件自身

## 11. 禁止修改

- 禁止修改源码。
- 禁止把 g2-g6 的实现细节混入本任务。
- 禁止移动任务到其他功能组。

## 12. 验收命令

```bash
python3 - <<'PY'
from pathlib import Path
base = Path("DOCS/阶段二：数据清洗/02_service/场景一")
required = [
    base / "L2数据定义/CleanedMcap.md",
    base / "L2数据定义/Scene1Config.md",
    base / "L2数据定义/Scene1CleanReport.md",
    base / "L2数据定义/GripperCalibrationConfig.md",
    base / "L2数据定义/FrameAlignmentConfig.md",
    base / "L2数据定义/CommonFrameCameraPose.md",
    base / "L2数据定义/CommonFrameTcpPose.md",
]
missing = [str(p) for p in required if not p.exists()]
if missing:
    raise SystemExit("missing: " + ", ".join(missing))
print("service_s1_001 contract docs ok")
PY
```

## 13. 成功标准

- [ ] 数据定义文件齐全。
- [ ] cleaned MCAP 契约明确 raw pose 保留或可追溯。
- [ ] 场景二上游接口状态已同步。

## 14. 完成后交接

必须更新当前 L3 文件、追加执行摘要，并移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/service-s1-g1/`。
