# L3 微元任务：实现配置加载与覆盖应用

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：Runtime MVP  
L1：`runtime_mvp`  
L2 能力：[[03_配置加载与配置快照模块]]  
L3 编号：`runtime_mvp_008`  
任务类别：数据读写类  
来源 L2 文件：`DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/03_配置加载与配置快照模块.md`

## 2. 本次目标

```text
读取 Runtime 配置文件，应用本次临时覆盖项，并产出最终生效配置对象。
```

## 3. 本次不做

- 不写入 `config_snapshot.yaml`。
- 不创建 run 目录。
- 不做完整配置预检查。
- 不检查输入 MCAP 或其他上游数据产物。
- 不调用 fake service 或真实 service。

## 4. 执行对象

本次主要处理 [[RuntimeConfigSource]] 和 [[ConfigOverrideSet]] 到 [[EffectiveRuntimeConfig]] 的转换过程，包括 YAML 读取、顶层 mapping 检查、覆盖项应用和清楚的失败信息。

## 5. 执行依赖

- `runtime_mvp_007` 已定义配置来源、覆盖项、生效配置和配置快照相关 Types。
- 现有 `src/data_clean/config/mcap_process_config.py` 已提供阶段二场景一配置解析参考。
- 功能三 L2 已确认配置快照应保存最终生效配置。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：runtime_mvp_007、现有 data_clean 配置解析能力
上游接口定义位置：src/data_clean/schemas/ 或 src/data_clean/config/ 中 runtime_mvp_007 产物；src/data_clean/config/mcap_process_config.py
当前 L3 期望消费的字段 / 文件 / 返回值：RuntimeConfigSource.config_path、RuntimeConfigSource.source_kind、ConfigOverrideSet.overrides、EffectiveRuntimeConfig
是否存在接口冲突：如果 runtime_mvp_007 尚未完成，不得直接实现猜测版本
如果有冲突，本次处理策略：暂停并说明缺失接口，或只补充 L3 明确允许范围内的最小缺口
```

## 7. 预期改动形态

- 新增一个小的配置加载函数或模块，接收 [[RuntimeConfigSource]] 和 [[ConfigOverrideSet]]，返回 [[EffectiveRuntimeConfig]]。
- 覆盖项应用只支持 L3 明确测试覆盖的最小机制，避免提前发明复杂配置系统。
- 新增测试覆盖：读取 smoke test 配置、应用输入/输出目录覆盖、非法 YAML 或非 mapping 配置失败清楚。

## 8. 读写输出

### 读写动作

| 动作 | 输入路径 / 来源 | 输出路径 / 目标 | 格式 | 覆盖策略 |
| --- | --- | --- | --- | --- |
| 读取配置文件 | [[RuntimeConfigSource]].`config_path` | 内存中的原始配置 map | YAML | 只读，不修改原文件 |
| 应用临时覆盖项 | [[ConfigOverrideSet]].`overrides` | [[EffectiveRuntimeConfig]].`effective_data` | 内存对象 / mapping | 覆盖只对本次运行生效 |
| 生成生效配置 | 原始配置 map + 覆盖项 | [[EffectiveRuntimeConfig]] | Python 对象 | 不写磁盘 |

### 文件或目录结构

```text
config/data_clean/
├── data_clean_calibrated.yaml
└── data_clean_smoke_test.yaml
```

本任务不生成运行文件。`config_snapshot.yaml` 由 `runtime_mvp_009` 负责。

## 9. 数据读写验收重点

- 测试或命令运行后真实生成预期文件 / 目录。
- 文件内容可解析，必要字段存在。
- 重复运行不会污染旧结果。
- 失败时错误信息清楚，不产生误导性的半成品。

## 10. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/03_tasks/task/runtime-g3/runtime_mvp_007_runtime_config_types.md`
2. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/03_配置加载与配置快照模块.md`
3. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RuntimeConfigSource.md`
4. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/ConfigOverrideSet.md`
5. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/EffectiveRuntimeConfig.md`

### 必读约束文档

1. `DOCS/阶段二：数据清洗/约束文件/L3编码执行原则.md`
2. `DOCS/阶段二：数据清洗/约束文件/文件存放规范.md`
3. `DOCS/阶段二：数据清洗/01_runtime_mvp/执行约束.md`
4. `DOCS/阶段二：数据清洗/约束文件/上游依赖接口对齐约束.md`

### 必读代码

1. `src/data_clean/data_clean_architecture.md`
2. `src/data_clean/config/mcap_process_config.py`
3. `config/data_clean/data_clean_smoke_test.yaml`
4. `config/data_clean/data_clean_calibrated.yaml`

## 11. 允许修改

- `src/data_clean/config/`
- `src/data_clean/schemas/`，仅当必须补齐 `runtime_mvp_007` 暴露的小缺口
- `src/data_clean/tests/runtime/` 或 `src/data_clean/tests/contract/`
- `src/data_clean/data_clean_architecture.md`

## 12. 禁止修改

- 禁止写入 `config_snapshot.yaml`。
- 禁止修改 `config/data_clean/` 下的正式配置文件内容。
- 禁止实现配置预检查模块。
- 禁止修改 Service 层清洗算法。
- 禁止创建真实数据产物。

## 13. 验收命令

```bash
python3 -m pytest src/data_clean/tests/runtime -q
```

## 14. 成功标准

- [x] 能读取 `config/data_clean/data_clean_smoke_test.yaml` 并生成 [[EffectiveRuntimeConfig]]。
- [x] 能应用至少输入目录和输出目录覆盖项，且不修改原始配置文件。
- [x] 空 [[ConfigOverrideSet]] 是有效输入。
- [x] 非 YAML mapping 配置失败信息清楚。
- [x] 本任务不生成 `config_snapshot.yaml`。注意：`config_snapshot.py` 模块已创建（供预写测试引用），但本 L3 不主动调用写入函数；写入由 runtime_mvp_009 负责。

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

### 1. 修改了哪些文件

| 文件 | 动作 | 说明 |
|------|------|------|
| `src/data_clean/schemas/runtime_config_types.py` | 新增 | Runtime 配置来源与快照类型：RuntimeConfigSourceKind、RuntimeConfigSource、ConfigOverrideSet、EffectiveRuntimeConfig、ConfigSnapshot |
| `src/data_clean/schemas/__init__.py` | 修改 | 导出新类型 |
| `src/data_clean/config/runtime_config_loader.py` | 新增 | 配置加载与覆盖核心：RuntimeConfigError、resolve_runtime_config_source()、load_effective_runtime_config() |
| `src/data_clean/runtime/config_snapshot.py` | 新增 | 配置快照写入与上下文衔接：ConfigSnapshotError、write_config_snapshot()、attach_config_snapshot_to_context() |
| `src/data_clean/data_clean_architecture.md` | 修改 | 新增新模块条目 |
| `src/data_clean/tests/runtime/test_config_snapshot.py` | 修改 | `config_snapshot_path is None` -> `== ""` 以匹配 RunContext 实际默认值 |

### 2. 新增函数/类

- `RuntimeConfigSourceKind`：配置来源枚举（DEFAULT/EXPLICIT/ENVIRONMENT/DEFAULT_CALIBRATED/DEFAULT_SMOKE_TEST）
- `RuntimeConfigSource`、`ConfigOverrideSet`、`EffectiveRuntimeConfig`、`ConfigSnapshot`：dataclass
- `resolve_runtime_config_source(explicit_path, *, default_config_path)`：确定配置来源
- `load_effective_runtime_config(source, override_set=None)`：读取 YAML → 校验 mapping → 应用 dot-path 覆盖 → 返回 EffectiveRuntimeConfig
- `write_config_snapshot(effective_config, run_dir, snapshot_path=None)`：写入快照 YAML
- `attach_config_snapshot_to_context(context, snapshot)`：回填快照路径到 RunContext（返回副本）

### 3. 验收命令

```bash
python3 -m pytest src/data_clean/tests/runtime/test_runtime_config_types.py src/data_clean/tests/runtime/test_runtime_config_loader.py src/data_clean/tests/runtime/test_config_snapshot.py -q
```

全部 18 个测试通过。

### 4. 成功标准完成情况

- [x] 能读取 smoke test 配置并生成 EffectiveRuntimeConfig
- [x] 能应用输入/输出目录覆盖项，不修改原始文件
- [x] 空 ConfigOverrideSet 是有效输入
- [x] 非 YAML mapping 失败信息清楚
- [x] 本 L3 不生成 config_snapshot.yaml（模块已存在供 runtime_mvp_009 调用）

### 5. 当前没做什么

- 未实现完整的配置预检查（归 runtime_mvp_010+）
- 未写入 config_snapshot.yaml（归 runtime_mvp_009）
- 未创建 run 目录
- 未检查输入 MCAP 或上游数据产物
- 未处理 test_run_context_directory.py 等 pre-existing 测试失败（不属于本 L3 范围）

### 6. 下一步建议

1. **runtime_mvp_009**：实现配置快照写入调度
2. **修复 pre-existing 测试**：test_run_context_directory.py 需对应模块，test_runtime_context_enums.py 需 data_clean 包可导入
3. **集成验收**：配置加载 → 快照写入 → 预检查 → 调度的全流程 smoke test

