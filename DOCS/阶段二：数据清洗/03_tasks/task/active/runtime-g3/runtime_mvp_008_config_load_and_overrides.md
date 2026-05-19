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
- `DOCS/阶段二：数据清洗/执行记录/`

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

- [ ] 能读取 `config/data_clean/data_clean_smoke_test.yaml` 并生成 [[EffectiveRuntimeConfig]]。
- [ ] 能应用至少输入目录和输出目录覆盖项，且不修改原始配置文件。
- [ ] 空 [[ConfigOverrideSet]] 是有效输入。
- [ ] 非 YAML mapping 配置失败信息清楚。
- [ ] 本任务不生成 `config_snapshot.yaml`。

## 15. 完成后交接

必须更新：

- `DOCS/阶段二：数据清洗/执行记录/<MMDDHH_runtime_mvp_008_config_load_and_overrides>.md`
- 执行过程、当前状态、未完成事项和下一步建议写在同一个记录文件中

交接摘要必须包含：

1. 修改了哪些文件
2. 新增了哪些函数 / 测试
3. 如何运行验收
4. 当前没做什么
5. 下一步建议
