# L3 微元任务：实现输入产物最小边界检查

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：Runtime MVP  
L1：`runtime_mvp`  
L2 能力：[[05_输入产物预检查模块]]  
L3 编号：`runtime_mvp_012`  
任务类别：数据计算类  
来源 L2 文件：`DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/05_输入产物预检查模块.md`

## 2. 本次目标

```text
对输入产物需求解析出的候选路径执行存在性、可读性和文件/目录类型匹配检查，并生成结构化预检查汇总。
```

## 3. 本次不做

- 不实现配置预检查。
- 不读取 MCAP topic、Parquet schema 或 canonical dataset 内部结构。
- 不自动运行上游场景补齐缺失产物。
- 不调用 fake service 或真实 service。
- 不写 `run_log.json`、`processing_manifest.json` 或 `error_summary.json`。

## 4. 执行对象

本次主要处理 [[EffectiveRuntimeConfig]]、[[InputArtifactRequirement]] 到 [[InputArtifactCheckResult]] 和 [[InputArtifactPrecheckSummary]] 的最小计算闭环。

## 5. 执行依赖

- `runtime_mvp_010` 已定义输入产物预检查相关 Types。
- `runtime_mvp_011` 已能生成目标场景的 [[InputArtifactRequirement]] 列表。
- `runtime_mvp_008` 已能产出 [[EffectiveRuntimeConfig]]。
- 功能4配置预检查接口尚未稳定；本任务可以假定调用方已完成配置预检查，但不得实现功能4职责。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：runtime_mvp_008、runtime_mvp_010、runtime_mvp_011
上游接口定义位置：配置加载 L3；输入产物预检查 Types L3；场景输入需求解析 L3
当前 L3 期望消费的字段 / 文件 / 返回值：EffectiveRuntimeConfig.effective_data、InputArtifactRequirement.path_config_key、required_kind、InputArtifactCheckResult、InputArtifactPrecheckSummary
是否存在接口冲突：功能4配置预检查尚未定义；本任务不得把配置合法性判断并入当前实现
如果有冲突，本次处理策略：只检查候选路径边界；配置字段缺失时返回输入路径缺失错误，不扩展为配置校验器
```

## 7. 预期改动形态

- 新增一个输入产物检查函数或小模块，接收生效配置和需求列表，返回预检查汇总。
- 新增测试覆盖：合法文件、合法目录、缺路径键、路径不存在、类型不匹配。
- 错误结果必须包含可消费的 [[RuntimeErrorRef]]。

## 8. 计算输出

### 计算规则

| 输入情况 | 计算 / 判断规则 | 预期输出 | reason / error |
| --- | --- | --- | --- |
| 合法输入 | 配置中能解析路径，路径存在、可读且类型匹配 | [[InputArtifactCheckResult]] 成功，汇总成功 | 无 |
| 缺失输入 | 配置中缺少 `path_config_key` 或候选路径为空 | 单项失败，汇总失败 | `input_path_missing_in_config` |
| 边界输入 | 期望目录但候选路径是文件，或期望文件但候选路径是目录 | 单项失败，汇总失败 | `input_artifact_kind_mismatch` |
| 路径不存在 | 候选路径不存在 | 单项失败，汇总失败 | `input_artifact_not_found` |
| 路径不可读 | 候选路径存在但不可读 | 单项失败，汇总失败 | `input_artifact_not_readable` |

### 输出结构

| 字段 | 类型 | 含义 | 有效性要求 |
| --- | --- | --- | --- |
| `results` | list of [[InputArtifactCheckResult]] | 单项输入产物检查结果 | 每个需求都必须有结果 |
| `status` | [[RunStatus]] 或受控字符串 | 汇总状态 | 任一阻塞错误必须失败 |
| `blocking_errors` | list of [[RuntimeErrorRef]] | 阻塞调度的错误 | 失败时不能为空 |

## 9. 数据计算验收重点

- 合法输入通过。
- 缺失或非法输入失败。
- 错误信息能说明具体缺口。
- 输出结构可被下游直接消费。

## 10. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/05_输入产物预检查模块.md`
2. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/InputArtifactRequirement.md`
3. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/InputArtifactCheckResult.md`
4. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/InputArtifactPrecheckSummary.md`
5. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/03_配置加载与配置快照模块.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/runtime-g3/runtime_mvp_008_config_load_and_overrides.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/runtime-g5/runtime_mvp_010_input_artifact_precheck_types.md`
3. `DOCS/阶段二：数据清洗/03_tasks/task/runtime-g5/runtime_mvp_011_scene_input_requirements.md`

如果没有找到相关 L3 历史记录，执行摘要中必须明确写明“未找到相关 L3 历史记录”。

### 必读约束文档

1. `DOCS/阶段二：数据清洗/约束文件/L3编码执行原则.md`
2. `DOCS/阶段二：数据清洗/约束文件/L3执行TDD与归档约束.md`
3. `DOCS/阶段二：数据清洗/约束文件/上游依赖接口对齐约束.md`
4. `DOCS/阶段二：数据清洗/约束文件/文件存放规范.md`
5. `DOCS/阶段二：数据清洗/01_runtime_mvp/执行约束.md`

### 必读代码

1. `src/data_clean/data_clean_architecture.md`
2. `src/data_clean/config/`
3. `src/data_clean/runtime/`
4. `src/data_clean/repo/`
5. `src/data_clean/tests/runtime/`

## 11. TDD 执行要求

如果本 L3 涉及代码新增、代码修改、bug 修复或行为变更，必须先读取并使用 `$tdd` 技能：

```text
$tdd
```

执行时按垂直切片推进：一个行为测试或最小复现 -> 最少实现 -> 验证通过 -> 必要整理 -> 下一个行为。

## 12. 允许修改

- `src/data_clean/runtime/`
- `src/data_clean/repo/`，仅当文件系统边界检查已有 Repo 层约定
- `src/data_clean/tests/runtime/`
- `src/data_clean/data_clean_architecture.md`

## 13. 禁止修改

- 禁止实现配置预检查模块。
- 禁止读取 MCAP、Parquet、HDF5、Zarr 或 canonical dataset 内部内容。
- 禁止调用 fake service 或真实 service。
- 禁止写运行日志、manifest、错误摘要或 run result。
- 禁止创建、覆盖或删除真实数据产物。

## 14. 验收命令

Python 命令必须使用 `python3`，不得写成 `python`。
仓库内文件和目录必须使用相对仓库根目录路径，不得写入开发者本机绝对路径。

```bash
python3 -m pytest src/data_clean/tests/runtime -q
```

## 15. 成功标准

完成后必须在本文件中把实际验证通过的条目改为 `- [x]`；未验证条目保持 `- [ ]`，并在执行摘要说明原因。

- [ ] 存在且可读的文件输入能通过检查。
- [ ] 存在且可读的目录输入能通过检查。
- [ ] 缺配置路径时失败清楚。
- [ ] 路径不存在时失败清楚。
- [ ] 文件/目录类型不匹配时失败清楚。
- [ ] 本任务未实现业务深度校验、Service 调度或日志/manifest 写入。

- [ ] 执行摘要已追加到当前 L3 文件末尾。
- [ ] 当前 L3 已归档到对应 `task/completed/<功能组>/`。

## 16. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要
- 完成并更新任务文件后，将当前 L3 移到对应 `DOCS/阶段二：数据清洗/03_tasks/task/completed/<功能组>/`
- 不写 `DOCS/阶段二：数据清洗/执行记录/`、阶段/场景 `当前进度.md`、共享 `执行记录.md` 或 `DOCS/总执行日志.md`

- 执行过程、当前状态、未完成事项和下一步建议写在当前 L3 任务文件末尾的执行摘要中

交接摘要必须包含：

1. 读取了哪些相关 L3 任务文件或历史记录
2. 修改了哪些文件
3. 新增或修改了哪些函数 / 测试
4. TDD red / green / refactor 如何执行
5. 如何运行验收，命令必须使用 `python3`
6. 成功标准勾选情况
7. 当前没做什么
8. 下一步建议

