# L3 微元任务：稳定 cleaned MCAP 接口契约

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景一：提取夹爪开合以及位姿转换
L1：service_s1
L2 能力：cleaned MCAP 契约稳定
L3 编号：service_s1_001
当前任务文件路径：`DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s1-g1/service_s1_001_稳定cleaned_MCAP接口契约.md`
任务类别：数据定义类
来源 L2 文件：`DOCS/03_工程/阶段二：数据清洗/02_service/场景一/L2能力模块/cleaned MCAP契约稳定.md`

## 2. 本次目标

```text
补齐场景一 cleaned MCAP、配置、报告和开发者验收数据定义，使场景二和 --dev 功能检验都能按统一契约消费。
```

## 3. 本次不做

- 不修改源码。
- 不实现 `./start_data_clean.sh --dev`。
- 不实现夹爪、位姿或 validator 算法。

## 4. 执行对象

- 场景一 `功能模块清单.md`
- 场景一 `L2数据定义/`
- 场景一 cleaned MCAP 契约和 dev 验收契约。

## 5. 执行依赖

- 场景一功能模块清单已存在。
- `Scene1DevCheckItem`、`Scene1DevRun`、`Scene1DevArtifact`、`Scene1DevRunLog`、`Scene1DevConfigOverride` 必须作为原子数据定义存在或由本任务补齐。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：阶段一 raw MCAP 采集产物、场景一现有配置文件
上游接口定义位置：DOCS/03_工程/阶段二：数据清洗/02_service/场景一/功能模块清单.md
当前 L3 期望消费的字段 / 文件 / 返回值：raw MCAP、Scene1Config、CleanedMcap、Scene1CleanReport、Scene1Dev* 数据定义
是否存在接口冲突：旧代码现实可能仍复用 pose topic 替换 payload，目标契约要求 raw pose 保留或可追溯
如果有冲突，本次处理策略：文档中区分旧实现现实与目标契约，代码改造交给 g5/g6
```

## 7. 预期改动形态

- L2 数据定义齐全且可被 wikilink 引用。
- 场景一功能模块清单包含 `--dev` 开发者验收范式。
- g1-g6 每个功能组都有 dev 功能检验项。

## 8. 数据定义输出

### 需要定义的对象

| 对象 | 类型 | 放置位置 | 下游使用者 |
|---|---|---|---|
| [[CleanedMcap]] | 原子文档 | `DOCS/03_工程/阶段二：数据清洗/02_service/场景一/L2数据定义/CleanedMcap.md` | 场景二、g6 validator |
| [[Scene1Config]] | 原子文档 | `DOCS/03_工程/阶段二：数据清洗/02_service/场景一/L2数据定义/Scene1Config.md` | g2-g6 |
| [[Scene1CleanReport]] | 原子文档 | `DOCS/03_工程/阶段二：数据清洗/02_service/场景一/L2数据定义/Scene1CleanReport.md` | g6、Runtime |
| [[Scene1DevCheckItem]] | 原子文档 | `DOCS/03_工程/阶段二：数据清洗/02_service/场景一/L2数据定义/Scene1DevCheckItem.md` | `--dev` 场景一菜单 |
| [[Scene1DevRun]] | 原子文档 | `DOCS/03_工程/阶段二：数据清洗/02_service/场景一/L2数据定义/Scene1DevRun.md` | g1-g6 dev 验收 |
| [[Scene1DevArtifact]] | 原子文档 | `DOCS/03_工程/阶段二：数据清洗/02_service/场景一/L2数据定义/Scene1DevArtifact.md` | g1-g6 dev 验收 |
| [[Scene1DevRunLog]] | 原子文档 | `DOCS/03_工程/阶段二：数据清洗/02_service/场景一/L2数据定义/Scene1DevRunLog.md` | g1-g6 dev 验收 |
| [[Scene1DevConfigOverride]] | 原子文档 | `DOCS/03_工程/阶段二：数据清洗/02_service/场景一/L2数据定义/Scene1DevConfigOverride.md` | `--dev` 临时覆盖 |

### 字段或取值

| 字段 / 取值 | 类型 | 含义 | 默认值 | 合法性要求 |
|---|---|---|---|---|
| `scene_id` | string | 场景标识 | `service_s1` | 固定值 |
| `group_id` | string | 功能组 | 无 | `service-s1-g1` 到 `service-s1-g6` |
| `run_dir` | path | 独立 dev run 目录 | `asset/阶段二：数据清洗/dev_runs/scene1/...` | 不得污染生产输出 |
| `save_to_config` | bool | 是否保存临时覆盖 | `false` | 只有显式选择才为 true |

## 9. 数据定义验收重点

- 能被文档链接引用。
- 字段类型、默认值和非法值处理符合 L2 定义。
- 相关原子数据定义文档已创建或复用，并在 L2/L3 中用 `[[wikilink]]` 引用。

## 10. 开发者验收入口

`./start_data_clean.sh --dev -> 场景一 -> scene1_contract_preview`

本 L3 只定义该检验项契约，不实现入口。该检验项应读取生产配置，生成契约摘要测试产物和运行日志到独立 [[Scene1DevRun]]。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段二：数据清洗/02_service/场景一/功能模块清单.md`
2. `DOCS/03_工程/阶段二：数据清洗/02_service/场景一/L2能力模块/cleaned MCAP契约稳定.md`
3. `DOCS/03_工程/阶段二：数据清洗/03_tasks/README.md`

### 必读相关微元任务记录

如果没有找到相关 L3 历史记录，执行摘要中必须明确写明“未找到相关 L3 历史记录”。

### 必读约束文档

1. `DOCS/02_约束/阶段二任务体系/L3编码执行原则.md`
2. `DOCS/02_约束/阶段二任务体系/L3任务文件身份校验约束.md`
3. `DOCS/02_约束/阶段二任务体系/L3执行TDD与归档约束.md`
4. `DOCS/02_约束/阶段二任务体系/功能分支接力流程.md`
5. `DOCS/02_约束/阶段二任务体系/L3功能组目录约束.md`
6. `DOCS/02_约束/阶段二任务体系/上游依赖接口对齐约束.md`
7. `DOCS/02_约束/阶段二任务体系/文件存放规范.md`
8. `DOCS/02_约束/阶段二任务体系/L3现有实现盘点约束.md`
9. `DOCS/03_工程/阶段二：数据清洗/02_service/场景一/执行约束.md`

### 必读代码

本任务不要求读取代码。

## 12. TDD 执行要求

执行前必须先完成 L3 任务文件身份校验。本 L3 不涉及代码修改，不需要使用 `$tdd`。

## 13. 允许修改

- `DOCS/03_工程/阶段二：数据清洗/02_service/场景一/功能模块清单.md`
- `DOCS/03_工程/阶段二：数据清洗/02_service/场景一/L2数据定义/`
- `DOCS/03_工程/阶段二：数据清洗/02_service/场景一/L2能力模块/cleaned MCAP契约稳定.md`
- 当前 L3 任务文件自身

## 14. 禁止修改

- 禁止修改源码。
- 禁止实现 `./start_data_clean.sh --dev`。
- 禁止移动其他功能组 L3。

## 15. 验收命令

```bash
python3 - <<'PY'
from pathlib import Path
base = Path("DOCS/03_工程/阶段二：数据清洗/02_service/场景一")
required = [
    "Scene1DevCheckItem.md",
    "Scene1DevRun.md",
    "Scene1DevArtifact.md",
    "Scene1DevRunLog.md",
    "Scene1DevConfigOverride.md",
]
missing = [name for name in required if not (base / "L2数据定义" / name).exists()]
if missing:
    raise SystemExit("missing dev definitions: " + ", ".join(missing))
text = (base / "功能模块清单.md").read_text(encoding="utf-8")
for needle in ["开发者验收范式", "scene1_smoke_test", "Scene1DevRun"]:
    assert needle in text, needle
print("service_s1_001 dev contract docs ok")
PY
```

## 16. 成功标准

- [ ] dev 验收相关数据定义齐全。
- [ ] 功能模块清单包含 `--dev` 场景一验收范式。
- [ ] g1-g6 每个功能组都有 dev 功能检验项。

## 17. 完成后交接

必须更新当前 L3 任务文件本身，追加执行摘要，并将当前 L3 移动到 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/02-service-s1/service-s1-g1/`。移动后如果 active 功能组为空，删除该空目录。不写共享执行记录。
