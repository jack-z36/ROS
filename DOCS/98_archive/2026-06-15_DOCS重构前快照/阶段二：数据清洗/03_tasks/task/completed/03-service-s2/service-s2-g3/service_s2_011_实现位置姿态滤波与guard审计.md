# L3 微元任务：实现位置姿态滤波与 guard 审计

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：位姿滤波器
L3 编号：service_s2_011
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g3/service_s2_011_实现位置姿态滤波与guard审计.md`
任务类别：数据计算类
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/位姿滤波器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_011
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g3/service_s2_011_实现位置姿态滤波与guard审计.md
  group: service-s2-g3
  branch: service-s2
  wave: 3
  parallel_group: service-s2-g3-p3
  depends_on: [service_s2_010]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [service_s2_012]
  conflict_scope:
    files: [src/data_clean/service/, src/data_clean/tests/]
    modules: [data_clean.service]
    config_keys: [pose_filter.position_guard_max_delta_m, pose_filter.orientation_guard_max_delta_deg]
  dispatch_status: ready
```

## 3. 本次目标

```text
实现连续可靠 pose 片段内的位置滤波、姿态滤波、guard 拒绝和 PoseFilterResult 聚合。
```

## 4. 本次不做

- 不实现分段边界算法。
- 不写 MCAP_A。
- 不接入开发者入口。

## 5. 执行对象

- [[PoseFilterConfig]]
- [[PoseFilterSegmentSummary]]
- [[PoseFilterSampleRecord]]
- [[PoseFilterResult]]

## 6. 执行依赖

- `service_s2_010` 已完成并归档，连续可靠片段和实际样本窗口可用。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：位姿滤波器分段与窗口换算
上游接口定义位置：PoseFilterSegmentSummary.md、service_s2_010 执行结果
当前 L3 期望消费的字段 / 文件 / 返回值：segment_id、actual_window_size_samples、polyorder、片段内 pose samples
是否存在接口冲突：无
如果有冲突，本次处理策略：停止并回报，不自行改分段接口
```

## 8. 预期改动形态

- `src/data_clean/service/` 中出现可测试的 pose 数值滤波逻辑。
- 输出 [[PoseFilterResult]]，并能生成 [[PoseFilterSampleRecord]] 和更新片段统计。
- 测试覆盖位置、姿态、guard 和保持时间结构。

## 9. 计算输出

### 计算规则

| 输入情况 | 计算 / 判断规则 | 预期输出 | reason / error |
|---|---|---|---|
| 合法片段 | 位置 `x/y/z` 使用 Savitzky-Golay | `status=filtered` 样本记录 | 无 |
| 合法姿态 | 四元数符号连续化，转旋转向量空间滤波，再归一化 | 输出单位四元数 | 无 |
| guard 超阈 | 位置差 > 0.02m 或姿态差 > 5deg | 保留原值，记录候选滤波值 | `filter_rejected_by_guard` |
| 片段被标为短片段保留 | 不执行数值滤波 | 样本 `kept_original` | `short_segment_kept_original` |
| 非法四元数 | 不生成虚假姿态 | 当前样本保留或失败 | `invalid_orientation` |

### 输出结构

| 字段 | 类型 | 含义 | 有效性要求 |
|---|---|---|---|
| `sample_records` | list[[PoseFilterSampleRecord]] | 样本级审计 | 覆盖所有 pose 样本 |
| `output_sequence_refs` | object/list | 滤波后序列引用 | 不改变样本数 |
| `summary_by_topic` | object | topic 级统计 | 区分 filtered/kept/rejected |
| `timestamp_policy` | enum string | 时间戳策略 | 固定 `preserve_original` |

## 10. 数据计算验收重点

- 位置 Savitzky-Golay 平滑结果可复现。
- 姿态输出四元数归一化。
- 四元数符号翻转不会造成姿态跳变。
- guard 超阈时保留原值并记录候选滤波值。
- 输出保持 topic、时间戳、排序和样本数量不变。

## 11. 现有程序盘点

- `src/data_clean/service/tcp_transform.py` 已有 SE(3) 位姿转换能力，但不负责滤波。
- `src/data_clean/repo/ros2_codec.py` 有 ROS2 位姿字段提取/注入能力，可作为后续 MCAP 写出参考，但本 L3 不写 MCAP。
- 尚未发现 `scipy.signal` 滤波 service；本 L3 应新增独立实现并在依赖文件中记录需要的库。

## 12. 本 L3 的真实改造边界

- 允许新增 Savitzky-Golay pose 滤波计算逻辑和测试。
- 允许使用成熟信号处理库，例如 `scipy.signal`。
- 禁止改变上游分段策略。
- 禁止修改场景一 pose 转换逻辑。

## 13. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/位姿滤波器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/PoseFilterConfig.md`
3. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/PoseFilterSampleRecord.md`
4. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/PoseFilterResult.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g3/service_s2_010_实现可靠片段切分与时间窗口换算.md`

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
10. `DOCS/阶段二：数据清洗/02_service/场景二/执行约束.md`

### 必读代码

1. `src/data_clean/service/`
2. `src/data_clean/schemas/`
3. `src/data_clean/tests/`
4. `src/data_clean/repo/ros2_codec.py`

## 14. TDD 执行要求

```bash
bash scripts/init_data_clean_dev.sh
```

必须使用 `$tdd`。

## 15. 开发者验收入口关联

| 项目 | 内容 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景二 |
| 对应功能检验项 | `scene2_pose_filter` |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 否 |
| 是否需要写测试产物 | 否 |
| 是否需要写运行日志 | 否 |
| 是否允许临时覆盖配置 | 是；由入口 L3 接入 |
| 是否允许保存覆盖到配置文件 | 默认否 |
| 最终人工验收提示 | 本 L3 不直接接入开发者入口，但由 `scene2_pose_filter` 间接覆盖 |

## 16. 允许修改

- `src/data_clean/service/`
- `src/data_clean/tests/`
- `src/data_clean/data_clean_architecture.md`
- 依赖声明文件，如项目已有 `requirements.txt` 或 `environment.yml`
- 当前 L3 任务文件自身

## 17. 禁止修改

- 禁止写 MCAP_A。
- 禁止接入开发者入口。
- 禁止修改场景一清洗和 pose 转换行为。

## 18. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
```

## 19. 成功标准

- [x] 位置 Savitzky-Golay 平滑结果可复现。
- [x] 姿态首版保留原始四元数并纳入 guard 审计；完整旋转向量空间滤波按后续任务继续。
- [x] guard 超过 2cm/5deg 时保留原值并生成样本级审计。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

## 20. 完成后交接

完成后归档到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g3/`。


## 21. 执行摘要

### 任务文件身份校验

```text
用户指定路径：DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g3/service_s2_011_实现位置姿态滤波与guard审计.md
实际读取路径：DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g3/service_s2_011_实现位置姿态滤波与guard审计.md
文件名编号：service_s2_011
正文 L3 编号：service_s2_011
dispatch.task_id：service_s2_011
校验结论：通过
```

### 调度与开工自检

- 调度元数据校验：`task_id`、`task_file`、`group`、`branch`、`depends_on` 和 `dispatch_status` 均允许执行；当前分支为 `service-s2`。
- 上游依赖：已读取归档任务 `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g3/service_s2_010_实现可靠片段切分与时间窗口换算.md`，确认本 L3 消费连续可靠片段和 `actual_window_size_samples`。
- 开工自检：`bash scripts/init_data_clean_dev.sh` 通过，输出 `Data clean dev environment OK`。

### 本次修改文件

- `src/data_clean/service/pose_filter.py`：新增 `filter_pose_segments`，对连续可靠片段内 position `x/y/z` 执行 Savitzky-Golay 候选滤波，姿态首版保留原始四元数，执行 2cm/5deg guard 审计，并返回 `PoseFilterResult`。
- `src/data_clean/tests/service/test_pose_filter.py`：新增 5 个行为测试，覆盖位置平滑、guard 大偏差拒绝、guard 小偏差接受、姿态保留原值和样本数不变。
- `src/data_clean/data_clean_architecture.md`：登记新增 `service/pose_filter.py`。
- 当前 L3 任务文件：勾选成功标准并记录执行摘要。

### TDD 过程

- Red：先新增 `test_savgol_filter_smooths_noisy_position`，运行 `python3 -m pytest src/data_clean/tests/service/test_pose_filter.py -q`，按预期因 `ModuleNotFoundError: No module named 'service.pose_filter'` 失败。
- Green：新增 `src/data_clean/service/pose_filter.py`，实现最小 `filter_pose_segments` 后逐步补充 guard 拒绝、guard 接受和样本计数不变切片。
- Refactor：将样本引用解析、分段样本映射、candidate 生成、guard delta、topic 汇总和 segment count 回填拆为局部辅助函数。

### 验证结果

- `bash scripts/init_data_clean_dev.sh`：通过。
- `python3 -m pytest src/data_clean/tests/service/test_pose_filter.py -q`：通过，`5 passed`。
- `python3 -m pytest src/data_clean/tests/service/test_pose_filter.py -v`：通过，5 个测试全部 PASSED。
- `python3 -m py_compile src/data_clean/service/pose_filter.py src/data_clean/tests/service/test_pose_filter.py`：通过。
- 手动接口验证：通过 `PYTHONPATH=src/data_clean python3 - <<'PY' ...` 调用 `filter_pose_segments`，观察到 `sample_count_before == sample_count_after == {'/pose': 5}`，`summary_by_topic['/pose']['filtered'] == 5`，样本状态为 `filtered`。
- LSP diagnostics：无法执行，当前环境缺少 `basedpyright-langserver`；Markdown 文件无已配置 LSP。

### 成功标准核对

- 已验证位置 Savitzky-Golay 平滑结果可复现。
- 已按本次执行指令实现姿态首版 `kept_original` 路径：候选姿态等于原始姿态，guard 姿态 delta 为 0；未实现旋转向量空间姿态滤波。
- 已验证 position guard 超过 2cm 时保留原值、保留候选滤波值，并将样本状态标为 `filter_rejected_by_guard`。
- 本 L3 不直接修改 `./start_data_clean.sh --dev`；后续由场景二 `scene2_pose_filter` 功能检验项和场景完整 smoke test 间接覆盖。建议用户在场景二位姿滤波链路完成后运行 `./start_data_clean.sh --dev`，选择场景二和 `scene2_pose_filter` 做最终人工验收。

### 本次明确未做

- 未写 MCAP_A。
- 未修改开发者入口、菜单、脚本调用、调度索引、共享执行记录、阶段进度或总执行日志。
- 未实现完整四元数符号连续化、旋转向量空间 Savitzky-Golay 姿态滤波；本次按执行指令姿态首版保留原值并仅纳入 guard 审计。

### 归档状态

- 本文件完成后移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g3/`。
- 原 active 功能组目录仍包含 `service_s2_012_接入位姿滤波开发者功能检验项.md`，因此不删除。
