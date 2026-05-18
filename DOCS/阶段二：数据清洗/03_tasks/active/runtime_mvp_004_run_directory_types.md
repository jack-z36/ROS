# L3 微元任务：定义 Run 目录 Types 与命名规则

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：Runtime MVP  
L1：`runtime_mvp`  
L2 能力：[[02_Run目录管理模块]]  
L3 编号：`runtime_mvp_004`  
任务类别：数据定义类  
来源 L2 文件：`DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/02_Run目录管理模块.md`

## 2. 本次目标

```text
在 Types / Schemas 层定义 Run 目录相关数据结构和 run_id 命名规则，让后续目录创建器可以复用同一套语义。
```

## 3. 本次不做

- 不创建真实 run 目录。
- 不写 `run_log.json`、`config_snapshot.yaml`、`processing_manifest.json`、`error_summary.json` 或 `run_result.json`。
- 不接入 Runtime 初始化流程。
- 不修改 `start_data_clean.sh`。

## 4. 执行对象

本次主要处理 Run 目录相关 Types：

- [[RunDirectory]]
- [[RunDirectoryLayout]]
- [[RunArtifactPath]]
- run_id 命名规则：`{YYYY-MM-DD}_s{scene_number}`、`{YYYY-MM-DD}_all`、重复运行追加 `_002`。

## 5. 执行依赖

- 已存在功能一相关 Runtime 数据定义，例如 [[RunContext]]、[[SceneName]]、[[RunMode]]。
- 已存在 `src/data_clean/schemas/` 目录。
- 已稳定的功能二 L2 能力说明和三个原子数据定义。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：Runtime 运行上下文定义
上游接口定义位置：DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/01_Runtime运行上下文定义.md
当前 L3 期望消费的字段 / 文件 / 返回值：RunContext 中的 run_id、target_scenes、run_dir 语义；SceneName 的受控场景名。
是否存在接口冲突：无已知冲突。
如果有冲突，本次处理策略：停止实现并在交接记录中说明冲突，不静默修改功能一边界。
```

## 7. 预期改动形态

- 在 `src/data_clean/schemas/` 下新增或扩展 Runtime run 目录相关类型定义文件。
- 如新增文件，更新 `src/data_clean/data_clean_architecture.md` 的目录结构表。
- 在 `src/data_clean/tests/` 下新增最小测试，覆盖单场景、全流程和重复序号命名规则。

## 8. 数据定义输出

### 需要定义的对象

| 对象 | 类型 | 放置位置 | 下游使用者 |
| --- | --- | --- | --- |
| `RunDirectory` | dataclass / 等价 TypedDict | `src/data_clean/schemas/` | `runtime_mvp_005`、`runtime_mvp_006` |
| `RunDirectoryLayout` | dataclass / 等价 TypedDict | `src/data_clean/schemas/` | 配置快照、日志、manifest、错误摘要模块 |
| `RunArtifactPath` | dataclass / 等价 TypedDict | `src/data_clean/schemas/` | 后续所有运行记录写入模块 |
| run_id 命名辅助能力 | function / method | `src/data_clean/schemas/` 或与类型同文件 | Run 目录创建器 |

### 字段或取值

| 字段 / 取值 | 类型 | 含义 | 默认值 | 合法性要求 |
| --- | --- | --- | --- | --- |
| `run_dir` | path-like string | 本次运行目录路径 | 无 | 必须在 `src/data_clean/runs/` 下 |
| `run_id` | string | 本次运行目录名 | 无 | 单场景 `{YYYY-MM-DD}_s{scene_number}`；全流程 `{YYYY-MM-DD}_all`；重复追加 `_002` |
| `outputs_dir` | path-like string | 调试输出目录 | `outputs/` | 必须在 `run_dir` 下 |
| `artifact_kind` | string / enum | 区分文件和目录 | 无 | `file` 或 `directory` |
| `owner_module` | string | 后续负责写入内容的模块 | 无 | 非空 |

## 9. 数据定义验收重点

- 能被 import 或被文档链接引用。
- 能实例化或能被 schema 校验工具读取。
- 字段类型、默认值和非法值处理符合 L2 定义。
- 相关原子数据定义文档已创建或复用，并在 L2/L3 中用 `[[wikilink]]` 引用。

## 10. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/02_Run目录管理模块.md`
2. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunDirectory.md`
3. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunDirectoryLayout.md`
4. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunArtifactPath.md`
5. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunContext.md`

### 必读约束文档

1. `DOCS/阶段二：数据清洗/约束文件/L3编码执行原则.md`
2. `DOCS/阶段二：数据清洗/约束文件/文件存放规范.md`
3. `DOCS/阶段二：数据清洗/01_runtime_mvp/执行约束.md`

### 必读代码

1. `src/data_clean/data_clean_architecture.md`
2. `src/data_clean/schemas/__init__.py`
3. `src/data_clean/schemas/ros2_schemas.py`

## 11. 允许修改

- `src/data_clean/schemas/`
- `src/data_clean/tests/`
- `src/data_clean/data_clean_architecture.md`
- `DOCS/阶段二：数据清洗/执行记录/`

## 12. 禁止修改

- 禁止修改真实 Service 清洗算法。
- 禁止修改 `start_data_clean.sh`。
- 禁止创建或写入 `src/data_clean/runs/`。
- 禁止创建真实数据产物到 `asset/阶段二：数据清洗/`。

## 13. 验收命令

```bash
python -m pytest src/data_clean/tests/runtime -q
```

若当前环境缺少 pytest，可至少运行对应 Python import / 构造检查，并在交接记录中说明未运行 pytest 的原因。

## 14. 成功标准

- [ ] Run 目录相关 Types 能被正常 import。
- [ ] 单场景 run_id 可生成 `YYYY-MM-DD_s1` 这类格式。
- [ ] 全流程 run_id 可生成 `YYYY-MM-DD_all`。
- [ ] 重复序号规则在测试中被覆盖。
- [ ] 未创建真实 run 目录。

## 15. 完成后交接

必须更新：

- `DOCS/阶段二：数据清洗/执行记录/<MMDDHH_runtime_mvp_004_run_directory_types>.md`
- 执行过程、当前状态、未完成事项和下一步建议写在同一个记录文件中

交接摘要必须包含：

1. 修改了哪些文件
2. 新增了哪些函数 / 测试
3. 如何运行验收
4. 当前没做什么
5. 下一步建议
