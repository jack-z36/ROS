# L3 微元任务：实现 MCAP_A 输入盘点与校验服务

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：场景三：MCAP 多 topic 时间轴对齐  
L1：service_s3  
L2 能力：MCAP_A 输入盘点与校验器  
L3 编号：service_s3_005  
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g2/service_s3_005_实现MCAP_A输入盘点与校验服务.md`  
任务类别：数据计算类  
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/MCAP_A输入盘点与校验器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s3_005
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g2/service_s3_005_实现MCAP_A输入盘点与校验服务.md
  group: service-s3-g2
  branch: service-s3
  wave: 2
  parallel_group: service-s3-g2-p2
  depends_on: [service_s3_004]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [service_s3_006]
  conflict_scope:
    files:
      - src/data_clean/service/mcap_a_input_validator.py
      - src/data_clean/repo/
      - src/data_clean/tests/
      - src/data_clean/data_clean_architecture.md
    modules:
      - data_clean.service
      - data_clean.repo
    config_keys:
      - scene3_alignment
  dispatch_status: ready
```

## 3. 本次目标

```text
实现读取 MCAP_A 与 McapAWriteSummary 的输入盘点服务，输出 SourceTopicCatalog 与 McapAInputValidationSummary。
```

## 4. 本次不做

- 不接入 `./start_data_clean.sh --dev` 菜单。
- 不写 run 目录调试产物。
- 不生成 [[StepTimeline]]。
- 不实现字段对齐、插值、聚合或 aligned MCAP 写出。

## 5. 执行对象

- [[McapA]]
- [[McapAWriteSummary]]
- [[Scene3AlignmentConfig]]
- [[TargetFieldMapping]]
- [[SourceTopicCatalog]]
- [[McapAInputValidationSummary]]

## 6. 执行依赖

- `service_s3_004` 必须已完成并归档，确保输入盘点类型可用。
- 必须复用 `service_s3_001` 落地的 [[Scene3AlignmentConfig]] 和 [[TargetFieldMapping]] 类型。
- 必须使用现有 MCAP 读取方式或在 repo 层封装只读 topic catalog helper。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：场景二 MCAP_A 生成器、场景三对齐契约与配置定义、service_s3_004 类型定义
上游接口定义位置：
- DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/McapA.md
- DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/McapAWriteSummary.md
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/Scene3AlignmentConfig.md
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/TargetFieldMapping.md
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/SourceTopicCatalog.md
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/McapAInputValidationSummary.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- MCAP_A 文件路径
- mcap_a_write_summary.json
- summary.status/output_mcap_a/timestamp_policy/topic_policy
- Scene3AlignmentConfig.baseline_image_topics/target_fields
- TargetFieldMapping.source_topic/message_type/required_for_timeline
是否存在接口冲突：无已知冲突
如果有冲突，本次处理策略：不得修改上游 MCAP_A 或配置契约；停止并记录冲突，必要时建议 Win 端调整 L2
```

## 8. 预期改动形态

- 新增 `src/data_clean/service/mcap_a_input_validator.py`，提供一个可测试的输入盘点 / 校验服务函数或类。
- 必要时新增 repo 层只读 MCAP topic 盘点 helper；不得把业务 hard fail 规则放进 repo 层。
- 新增 service / contract 测试，覆盖合法输入、hard fail、warning、未映射 topic 和基准交集元数据。
- 必要时更新 `src/data_clean/data_clean_architecture.md`。

## 9. 计算输出

### 计算规则

| 输入情况 | 计算 / 判断规则 | 预期输出 | reason / error |
|---|---|---|---|
| 合法输入 | MCAP_A 可读，summary completed 且路径/policy 一致，左右图像存在且有交集 | `SourceTopicCatalog` + `McapAInputValidationSummary(status=consumable)` | 无 hard fail |
| MCAP_A 缺失 | 输入路径不存在或不可读 | `McapAInputValidationSummary(status=not_consumable)` | `missing_mcap_a` |
| summary 缺失或不可读 | summary 路径不存在或 JSON 解析失败 | `status=not_consumable` | `missing_mcap_a_write_summary` / `unreadable_mcap_a_write_summary` |
| summary 不一致 | `status != completed`、`output_mcap_a` 不匹配、policy 不匹配 | `status=not_consumable` | `summary_not_completed` / `summary_output_path_mismatch` / `summary_policy_mismatch` |
| 基准 topic 缺失或乱序 | 左右图像任一缺失或时间戳乱序 | catalog 可生成，summary 不可消费 | `missing_baseline_topic` / `baseline_topic_out_of_order` |
| 左右图像无交集 | 两个基准 topic 时间范围无交集 | summary 不可消费 | `missing_baseline_intersection` |
| 非基准字段异常 | pose/tactile/gripper 缺失、类型不匹配、乱序或空 | 主链路可继续，字段标记 warning 或 unavailable | `optional_field_*` |
| 未映射 topic | MCAP_A 存在 target_fields 未声明 topic | 进入 `unmapped_topics` | 不产生 hard fail |

### 输出结构

| 字段 | 类型 | 含义 | 有效性要求 |
|---|---|---|---|
| `catalog` | `SourceTopicCatalog` | MCAP_A topic 事实和字段映射结果 | 必须包含 topic_entries、field_entries、unmapped_topics |
| `summary` | `McapAInputValidationSummary` | 输入可消费结论 | hard fail 为空才允许 `status=consumable` |
| `baseline_intersection_start_ns` | integer/null | 左右图像共同区间开始 | 不得生成 step 序列 |
| `baseline_intersection_end_ns` | integer/null | 左右图像共同区间结束 | 不得生成 step 序列 |
| `optional_field_warnings` | list[string] | 非基准字段异常 | 不得阻塞主链路 |

## 10. 数据计算验收重点

- 合法 MCAP_A + summary 通过，并输出可消费 summary。
- MCAP_A / summary strict 一致性 hard fail 覆盖完整。
- 左右图像基准 topic 缺失、乱序、无交集会阻塞。
- 非基准字段缺失、类型不匹配或乱序只产生 warning / unavailable。
- 输出结构可被第 3 模块和第 4 模块直接消费，不需要下游再次猜字段。

## 11. 现有程序盘点

- `src/data_clean/repo/mcap_a_writer.py` 已使用 `mcap.reader.make_reader` 遍历 MCAP message，并有 `_topic_message_counts`、`_build_output_contract` 等只读统计写法可参考；这些 helper 目前属于 writer 内部私有方法，不应直接跨模块调用私有方法。
- `src/data_clean/schemas/mcap_a_writer.py` 已定义 MCAP_A writer 的上游结果类型，不表达场景三输入盘点。
- `src/data_clean/service/` 尚无场景三 MCAP_A 输入校验服务；本 L3 应新增服务而不是把规则塞进 repo 或 runtime。
- `src/data_clean/tests/contract/test_mcap_a_scene3_compat.py` 由场景二 L3 生成，用于证明 MCAP_A 可被下游读取；本 L3 可复用其 fixture 思路，但应新增场景三输入盘点自己的测试。

## 12. 本 L3 的真实改造边界

- 允许新增 service 层输入校验服务和必要 repo 层只读 MCAP topic catalog helper。
- 允许新增测试 fixture 生成逻辑，用最小 MCAP 覆盖左右图像、可选字段和未映射 topic。
- 禁止修改 MCAP_A 写出器核心逻辑。
- 禁止修改 `Scene3AlignmentConfig` / `TargetFieldMapping` 字段语义；发现缺口时停止并记录。
- 禁止实现开发者入口或 run 目录写出。

## 13. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/MCAP_A输入盘点与校验器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/SourceTopicCatalog.md`
3. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/McapAInputValidationSummary.md`
4. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/Scene3AlignmentConfig.md`
5. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/TargetFieldMapping.md`
6. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/McapA.md`
7. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/McapAWriteSummary.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g2/service_s3_004_定义MCAP_A输入盘点与校验类型.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g1/service_s3_001_定义场景三配置与schema.md`
3. `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g5/service_s2_019_补充MCAP_A契约与场景三兼容验收.md`

### 必读约束文档

1. `DOCS/阶段二：数据清洗/约束文件/L3编码执行原则.md`
2. `DOCS/阶段二：数据清洗/约束文件/L3任务文件身份校验约束.md`
3. `DOCS/阶段二：数据清洗/约束文件/L3调度元数据约束.md`
4. `DOCS/阶段二：数据清洗/约束文件/L3执行TDD与归档约束.md`
5. `DOCS/阶段二：数据清洗/约束文件/功能分支接力流程.md`
6. `DOCS/阶段二：数据清洗/约束文件/L3功能组目录约束.md`
7. `DOCS/阶段二：数据清洗/约束文件/开发者验收入口约束.md`
8. `DOCS/阶段二：数据清洗/约束文件/上游依赖接口对齐约束.md`
9. `DOCS/阶段二：数据清洗/约束文件/文件存放规范.md`
10. `DOCS/阶段二：数据清洗/02_service/场景三/执行约束.md`

### 必读代码

1. `src/data_clean/schemas/alignment_input.py`
2. `src/data_clean/schemas/alignment_config.py`
3. `src/data_clean/repo/mcap_a_writer.py`
4. `src/data_clean/service/`
5. `src/data_clean/tests/`

## 14. TDD 执行要求

执行前必须完成任务文件身份校验、dispatch 校验和 `service-s3` 分支校验。

执行代码前必须运行：

```bash
bash scripts/init_data_clean_dev.sh
```

本 L3 涉及代码新增，必须使用 `$tdd` 技能。建议顺序：合法输入测试 -> 最小服务实现 -> summary hard fail 测试 -> 基准 topic hard fail 测试 -> 非基准 warning 测试 -> 未映射 topic 测试。

## 15. 开发者验收入口关联

| 项目 | 内容 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景三：MCAP 多 topic 时间轴对齐 |
| 对应功能检验项 | `scene3_mcap_a_input_check` |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 否，本 L3 提供底层服务 |
| 是否需要写测试产物 | 否，开发者产物由 service_s3_006 写出 |
| 是否需要写运行日志 | 否，运行日志由 service_s3_006 写出 |
| 是否允许临时覆盖配置 | 服务应接受调用方传入配置对象；本 L3 不实现交互覆盖 |
| 是否允许保存覆盖到配置文件 | 否 |
| 最终人工验收提示 | 本 L3 完成后仍需 service_s3_006 接入开发者入口，再由用户运行 `scene3_mcap_a_input_check` |

## 16. 允许修改

- `src/data_clean/service/mcap_a_input_validator.py`
- `src/data_clean/repo/`
- `src/data_clean/tests/`
- `src/data_clean/data_clean_architecture.md`
- 当前 L3 任务文件自身

## 17. 禁止修改

- 禁止修改场景二 MCAP_A 写出器核心逻辑。
- 禁止修改场景三配置类型语义来绕过测试。
- 禁止生成 [[StepTimeline]] 或字段对齐结果。
- 禁止接入开发者菜单或写 run 目录产物。
- 禁止写 `DOCS/阶段二：数据清洗/执行记录/`、阶段/场景 `当前进度.md`、共享 `执行记录.md` 或 `DOCS/总执行日志.md`。

## 18. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
python3 -m pytest src/data_clean/tests/contract -q
```

## 19. 成功标准

- [ ] 合法 MCAP_A + completed summary 可输出 `SourceTopicCatalog` 和 `McapAInputValidationSummary(status=consumable)`。
- [ ] MCAP_A 缺失、summary 缺失 / 不可读 / 不一致会输出 hard fail。
- [ ] 左右图像基准 topic 缺失、乱序、无共同有效时间范围会阻塞。
- [ ] 非基准字段问题只进入 warning 或 unavailable，不阻塞主链路。
- [ ] 未映射 topic 被记录为只读盘点，不作为错误。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系，或说明由哪个功能检验项 / smoke test 间接覆盖。

## 20. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要。
- 完成并更新任务文件后，将当前 L3 移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g2/`。
- 移动后如果 `DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g2/` 已经为空，删除该空 active 功能组目录。
- 不写 `DOCS/阶段二：数据清洗/执行记录/`、阶段/场景 `当前进度.md`、共享 `执行记录.md` 或 `DOCS/总执行日志.md`。

交接摘要必须包含模板要求的 12 项内容，尤其说明已读取 `service_s3_004` 与 MCAP_A 兼容验收记录、TDD red / green / refactor、验收命令结果和建议用户后续运行 `scene3_mcap_a_input_check`。
