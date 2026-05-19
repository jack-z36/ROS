# L3 微元任务：定义 Runtime 配置来源与快照 Types

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：Runtime MVP  
L1：`runtime_mvp`  
L2 能力：[[03_配置加载与配置快照模块]]  
L3 编号：`runtime_mvp_007`  
任务类别：数据定义类  
来源 L2 文件：`DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/03_配置加载与配置快照模块.md`

## 2. 本次目标

```text
定义 Runtime 配置加载与配置快照所需的最小 Types，让后续配置读取、覆盖应用和快照写入有稳定数据结构可用。
```

## 3. 本次不做

- 不实现配置文件读取逻辑。
- 不实现配置覆盖应用逻辑。
- 不写入 `config_snapshot.yaml`。
- 不做配置预检查、输入产物预检查或 Service 调度。

## 4. 执行对象

本次主要处理 [[RuntimeConfigSource]]、[[ConfigOverrideSet]]、[[EffectiveRuntimeConfig]] 和 [[ConfigSnapshot]] 的代码层表达，可使用 dataclass、enum、TypedDict 或项目现有风格中最轻量的等价结构。

## 5. 执行依赖

- 功能三 L2 能力模块说明已经存在。
- 功能三四个 L2 原子数据定义已经存在。
- Runtime 运行上下文相关 Types 已由 `runtime_mvp_001` 到 `runtime_mvp_003` 定义或应在本任务开始前检查其现状。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：Runtime 运行上下文定义、Run 目录管理模块
上游接口定义位置：DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/01_Runtime运行上下文定义.md；DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/02_Run目录管理模块.md；src/data_clean/schemas/ 中已有 Runtime Types
当前 L3 期望消费的字段 / 文件 / 返回值：RunContext.config_path、RunContext.config_snapshot_path 或等价字段；RunDirectoryLayout.config_snapshot_path 或等价路径对象
是否存在接口冲突：如果前序 Runtime Types 尚未实现，本任务只定义配置相关 Types，并在交接中说明阻塞
如果有冲突，本次处理策略：不重写上游 Types；用最小兼容引用或清晰 TODO 记录等待上游对齐
```

## 7. 预期改动形态

- 在 `src/data_clean/schemas/` 或 `src/data_clean/config/` 中新增配置来源、覆盖项、生效配置和配置快照相关 Types。
- 新增或更新轻量测试，覆盖默认来源、显式来源、空覆盖项、非空覆盖项和快照路径引用。
- 如新增源码模块，更新 `src/data_clean/data_clean_architecture.md` 的目录结构表。

## 8. 数据定义输出

### 需要定义的对象

| 对象 | 类型 | 放置位置 | 下游使用者 |
| --- | --- | --- | --- |
| [[RuntimeConfigSource]] | enum + dataclass / 等价结构 | `src/data_clean/schemas/` 或 `src/data_clean/config/` | `runtime_mvp_008`、日志、错误摘要 |
| [[ConfigOverrideSet]] | dataclass / mapping wrapper | `src/data_clean/schemas/` 或 `src/data_clean/config/` | `runtime_mvp_008`、配置快照 |
| [[EffectiveRuntimeConfig]] | dataclass / model | `src/data_clean/schemas/` 或 `src/data_clean/config/` | 配置预检查、输入预检查、调度、快照写入 |
| [[ConfigSnapshot]] | dataclass / model | `src/data_clean/schemas/` 或 `src/data_clean/config/` | `runtime_mvp_009`、日志、manifest、smoke test |

### 字段或取值

| 字段 / 取值 | 类型 | 含义 | 默认值 | 合法性要求 |
| --- | --- | --- | --- | --- |
| `source_kind` | enum / string | 配置来源类型 | 无 | 受控值，例如 `explicit_path`、`environment`、`default_calibrated`、`default_smoke_test` |
| `config_path` | path | 被读取的配置文件路径 | 无 | 必须能表达具体路径；存在性检查可留给加载任务 |
| `overrides` | mapping | 临时覆盖项集合 | 空 map | 允许为空；不得直接写回原配置 |
| `effective_data` | mapping | 最终生效配置内容 | 无 | 必须可序列化 |
| `snapshot_path` | path / RunArtifactPath | 快照目标路径 | 无 | 必须能表达 run 目录下 `config_snapshot.yaml` |

## 9. 数据定义验收重点

- 能被 import 或被文档链接引用。
- 能实例化或能被 schema 校验工具读取。
- 字段类型、默认值和非法值处理符合 L2 定义。
- 相关原子数据定义文档已创建或复用，并在 L2/L3 中用 `[[wikilink]]` 引用。

## 10. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/03_配置加载与配置快照模块.md`
2. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RuntimeConfigSource.md`
3. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/ConfigOverrideSet.md`
4. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/EffectiveRuntimeConfig.md`
5. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/ConfigSnapshot.md`
6. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunContext.md`
7. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunDirectoryLayout.md`

### 必读约束文档

1. `DOCS/阶段二：数据清洗/约束文件/L3编码执行原则.md`
2. `DOCS/阶段二：数据清洗/约束文件/文件存放规范.md`
3. `DOCS/阶段二：数据清洗/01_runtime_mvp/执行约束.md`
4. `DOCS/阶段二：数据清洗/约束文件/上游依赖接口对齐约束.md`

### 必读代码

1. `src/data_clean/data_clean_architecture.md`
2. `src/data_clean/schemas/`
3. `src/data_clean/config/mcap_process_config.py`

## 11. 允许修改

- `src/data_clean/schemas/`
- `src/data_clean/config/`，仅当配置相关 Types 放在配置层更贴合现有结构
- `src/data_clean/tests/runtime/` 或 `src/data_clean/tests/contract/`
- `src/data_clean/data_clean_architecture.md`

## 12. 禁止修改

- 禁止实现配置读取、覆盖应用或快照写入逻辑。
- 禁止修改 Service 层清洗算法。
- 禁止修改 `start_data_clean.sh`。
- 禁止生成真实 run 目录或真实数据产物。

## 13. 验收命令

```bash
python3 -m pytest src/data_clean/tests/runtime -q
```

## 14. 成功标准

- [ ] 配置来源、覆盖项、生效配置和配置快照 Types 可被 import。
- [ ] 能构造显式配置来源和默认配置来源。
- [ ] 能构造空覆盖项和非空覆盖项。
- [ ] 能构造包含最终生效配置与快照路径的配置快照对象。
- [ ] 未实现配置文件读取和快照写入行为。

- [ ] 执行摘要已追加到当前 L3 文件末尾。
- [ ] 当前 L3 已归档到对应 `task/completed/<功能组>/`。

## 15. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要
- 完成并更新任务文件后，将当前 L3 移到对应 `DOCS/阶段二：数据清洗/03_tasks/task/completed/<功能组>/`
- 不写 `DOCS/阶段二：数据清洗/执行记录/`、阶段/场景 `当前进度.md`、共享 `执行记录.md` 或 `DOCS/总执行日志.md`

- 执行过程、当前状态、未完成事项和下一步建议写在当前 L3 任务文件末尾的执行摘要中

交接摘要必须包含：

1. 修改了哪些文件
2. 新增了哪些函数 / 测试
3. 如何运行验收
4. 当前没做什么
5. 下一步建议

