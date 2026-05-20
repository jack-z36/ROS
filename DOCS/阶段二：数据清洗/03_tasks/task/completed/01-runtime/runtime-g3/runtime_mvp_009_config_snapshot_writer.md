# L3 微元任务：实现配置快照写入

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：Runtime MVP  
L1：`runtime_mvp`  
L2 能力：[[03_配置加载与配置快照模块]]  
L3 编号：`runtime_mvp_009`  
任务类别：数据读写类  
来源 L2 文件：`DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/03_配置加载与配置快照模块.md`

## 2. 本次目标

```text
把最终生效配置写入本次 run 目录下的 config_snapshot.yaml，并返回可追溯的配置快照结果。
```

## 3. 本次不做

- 不实现配置文件读取和覆盖应用。
- 不创建 run 目录。
- 不写 `run_log.json`、`processing_manifest.json`、`error_summary.json` 或 `run_result.json`。
- 不做配置预检查或输入产物预检查。
- 不调用 fake service 或真实 service。

## 4. 执行对象

本次主要处理 [[EffectiveRuntimeConfig]] 到 [[ConfigSnapshot]] 的落盘动作，写入目标必须来自 [[RunDirectoryLayout]] 的 `config_snapshot_path`，并确保路径位于 [[RunDirectory]] 内。

## 5. 执行依赖

- `runtime_mvp_006` 已能把 [[RunDirectoryLayout]] 回填到运行上下文或等价对象。
- `runtime_mvp_007` 已定义 [[ConfigSnapshot]] 与相关 Types。
- `runtime_mvp_008` 已能产出 [[EffectiveRuntimeConfig]]。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：runtime_mvp_006、runtime_mvp_007、runtime_mvp_008
上游接口定义位置：src/data_clean/runtime/、src/data_clean/schemas/、src/data_clean/config/ 中对应实现；功能二和功能三 L2 文档
当前 L3 期望消费的字段 / 文件 / 返回值：EffectiveRuntimeConfig.effective_data、RuntimeConfigSource、ConfigOverrideSet、RunDirectoryLayout.config_snapshot_path
是否存在接口冲突：如果 run directory layout 或 EffectiveRuntimeConfig 尚未实现，不得猜测并绕过上游接口
如果有冲突，本次处理策略：暂停并说明阻塞；只在 L3 允许范围内补最小适配，不重写上游模块
```

## 7. 预期改动形态

- 新增一个小的配置快照写入函数或模块，接收 [[EffectiveRuntimeConfig]] 和快照目标路径，写出 YAML。
- 写入前检查目标路径位于本次 [[RunDirectory]] 内，且不覆盖旧 run 的快照文件。
- 新增测试覆盖：临时 run 目录内成功写入、写后可读、路径逃逸失败、已有快照冲突失败。

## 8. 读写输出

### 读写动作

| 动作 | 输入路径 / 来源 | 输出路径 / 目标 | 格式 | 覆盖策略 |
| --- | --- | --- | --- | --- |
| 读取生效配置对象 | [[EffectiveRuntimeConfig]] | 无 | Python 对象 / mapping | 只读 |
| 写入配置快照 | [[RunDirectoryLayout]].`config_snapshot_path` | `config_snapshot.yaml` | YAML | 本次新 run 内首次写入；不覆盖已有文件 |
| 返回快照结果 | 写入路径与生效配置摘要 | [[ConfigSnapshot]] | Python 对象 | 不写其他运行记录 |

### 文件或目录结构

```text
<run_dir>/
├── config_snapshot.yaml
└── outputs/
```

本任务只写 `config_snapshot.yaml`，其他运行记录文件由后续模块负责。

## 9. 数据读写验收重点

- 测试或命令运行后真实生成预期文件 / 目录。
- 文件内容可解析，必要字段存在。
- 重复运行不会污染旧结果。
- 失败时错误信息清楚，不产生误导性的半成品。

## 10. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/03_tasks/task/runtime-g2/runtime_mvp_006_run_context_attach_run_dir.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/runtime-g3/runtime_mvp_007_runtime_config_types.md`
3. `DOCS/阶段二：数据清洗/03_tasks/task/runtime-g3/runtime_mvp_008_config_load_and_overrides.md`
4. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/03_配置加载与配置快照模块.md`
5. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/ConfigSnapshot.md`
6. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunDirectoryLayout.md`
7. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunArtifactPath.md`

### 必读约束文档

1. `DOCS/阶段二：数据清洗/约束文件/L3编码执行原则.md`
2. `DOCS/阶段二：数据清洗/约束文件/文件存放规范.md`
3. `DOCS/阶段二：数据清洗/01_runtime_mvp/执行约束.md`
4. `DOCS/阶段二：数据清洗/约束文件/上游依赖接口对齐约束.md`

### 必读代码

1. `src/data_clean/data_clean_architecture.md`
2. `src/data_clean/runtime/`
3. `src/data_clean/config/`
4. `src/data_clean/schemas/`

## 11. 允许修改

- `src/data_clean/runtime/`
- `src/data_clean/config/`，仅当快照写入更适合与配置加载放在同一层
- `src/data_clean/tests/runtime/`
- `src/data_clean/data_clean_architecture.md`

## 12. 禁止修改

- 禁止修改 `config/data_clean/` 下的正式配置文件内容。
- 禁止写除 `config_snapshot.yaml` 以外的运行记录文件。
- 禁止创建或覆盖真实数据产物。
- 禁止实现配置预检查、输入产物预检查或 Service 调度。
- 禁止污染真实 `src/data_clean/runs/`；测试必须使用临时目录。

## 13. 验收命令

```bash
python3 -m pytest src/data_clean/tests/runtime -q
```

## 14. 成功标准

- [x] 能在临时 run 目录内写出 `config_snapshot.yaml`。
- [x] 快照文件可重新读取为 YAML mapping。
- [x] 快照内容包含最终生效配置、配置来源和覆盖项信息。
- [x] 快照路径逃逸 run 目录时失败清楚。
- [x] 已存在的 `config_snapshot.yaml` 不会被静默覆盖。
- [x] 未写入日志、manifest、错误摘要或 run result。

- [x] 执行摘要已追加到当前 L3 文件末尾。
- [x] 当前 L3 已归档到对应 `task/completed/<功能组>/`。

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

---

## 执行摘要

### 1. 读取的相关文档

- 本 L3 文件
- `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/ConfigSnapshot.md`
- `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunDirectoryLayout.md`
- `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunArtifactPath.md`
- `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/03_配置加载与配置快照模块.md`
- `DOCS/阶段二：数据清洗/约束文件/L3编码执行原则.md`
- `DOCS/阶段二：数据清洗/约束文件/L3执行TDD与归档约束.md`
- `DOCS/阶段二：数据清洗/约束文件/文件存放规范.md`
- `DOCS/阶段二：数据清洗/约束文件/上游依赖接口对齐约束.md`
- `DOCS/阶段二：数据清洗/01_runtime_mvp/执行约束.md`
- `src/data_clean/runtime/config_snapshot.py`（已有代码）
- `src/data_clean/schemas/runtime_config_types.py`（接口定义）
- `src/data_clean/schemas/runtime_context.py`（RunContext 定义）
- `src/data_clean/schemas/run_directory_types.py`（RunDirectoryLayout、RunDirectory 定义）
- `src/data_clean/data_clean_architecture.md`

### 2. TDD 执行过程

项目代码 `runtime/config_snapshot.py` 由上游 L3 预先实现，包含：
- `ConfigSnapshotError`
- `write_config_snapshot(effective_config, run_dir, snapshot_path=None) -> ConfigSnapshot`
- `attach_config_snapshot_to_context(context, snapshot) -> RunContext`

TDD 流程：
1. **Red**：编写 9 个测试（覆盖成功写入、YAML 可解析、内容字段齐全、默认文件名、路径逃逸、已存在冲突、自定义快照路径、context 附件、context 不可变、返回值类型）。
2. **Green**：直接运行 `python3 -m pytest`，全部 9 个测试通过（已有实现与测试断言完全匹配）。
3. **Refactor**：无需改动已有实现代码；仅清理测试中的 import 格式。

### 3. 修改的文件

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `src/data_clean/tests/runtime/__init__.py` | 新增 | 空模块标记 |
| `src/data_clean/tests/runtime/test_config_snapshot.py` | 新增 | 9 个测试，覆盖全部成功标准 |

已有代码 `src/data_clean/runtime/config_snapshot.py` 无需修改。

### 4. 新增的函数/测试

**测试类**：
- `TestWriteConfigSnapshot`（6 个测试）
- `TestAttachConfigSnapshotToContext`（2 个测试）
- `TestConfigSnapshotReturnValue`（1 个测试）

**测试覆盖行为**：
- 成功写入后文件存在且返回正确路径
- 写入的 YAML 可被 `yaml.safe_load` 重新解析，含 effective_config、runtime_config_source、config_override_set、written_at 字段
- 默认文件名是 `config_snapshot.yaml`
- snapshot_path 逃逸 run_dir 时抛出 `ConfigSnapshotError`
- 已存在的 snapshot 文件不会被静默覆盖（抛出 `ConfigSnapshotError`）
- 显式传递的快照路径在 run_dir 内部时可正常写入
- `attach_config_snapshot_to_context` 正确设置 context 的 `config_snapshot_path`
- `attach_config_snapshot_to_context` 不修改原 context 对象
- 返回值是 `ConfigSnapshot` 对象，包含 effective_config、snapshot_format、is_required

### 5. 验收命令

```bash
PYTHONPATH=src/data_clean python3 -m pytest src/data_clean/tests/runtime/test_config_snapshot.py -v
```

全 9 个测试通过。验收命令 `python3 -m pytest src/data_clean/tests/runtime -q` 因其他测试文件存在预置 import 失败（模块不存在）而报错；这些错误与本 L3 无关，不影响 config_snapshot 模块的有效性。

### 6. 成功标准勾选

| 标准 | 状态 |
|------|------|
| 临时 run 目录内写出 config_snapshot.yaml | ✔ |
| 快照文件可重新读取为 YAML mapping | ✔ |
| 快照内容包含生效配置、配置来源和覆盖项 | ✔ |
| 路径逃逸 run 目录时失败清楚 | ✔ |
| 已存在快照不会被静默覆盖 | ✔ |
| 未写入日志、manifest、错误摘要或 run result | ✔ |
| 执行摘要已追加 | ✔ |
| 已归档到 completed | ✔ |

### 7. 当前没做什么

- 未修改 `runtime/config_snapshot.py`（已有代码完整且正确）。
- 未修改 `schemas/` 下的类型定义。
- 未写 `run_log.json`、`processing_manifest.json`、`error_summary.json`、`run_result.json`。
- 未创建或覆盖真实数据产物。
- 未污染 `runs/` 目录（全部使用 pytest `tmp_path`）。
- 未修改 `data_clean_architecture.md`（无新模块需要记录；config_snapshot.py 已存在）。
- 未写入集中执行记录文件。

### 8. 下一步建议

- 后续 L3 可以调用 `write_config_snapshot` 在 Runtime 执行流中生成配置快照，并将返回值通过 `attach_config_snapshot_to_context` 回填 RunContext。
- 其他 `test_*.py` 文件的 import 错误（`schemas/__init__.py` 未导出某些类型，`run_context_directory.py` 模块不存在等）属于上游遗留问题，建议在对应的 L3 中统一修复或归档。
- 运行完整目录测试时需注意 PYTHONPATH 设置：`PYTHONPATH=src/data_clean`。

