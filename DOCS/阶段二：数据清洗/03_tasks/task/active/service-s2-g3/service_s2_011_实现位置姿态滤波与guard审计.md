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

- [ ] 位置 Savitzky-Golay 平滑结果可复现。
- [ ] 姿态滤波处理四元数符号连续化并输出单位四元数。
- [ ] guard 超过 2cm/5deg 时保留原值并生成样本级审计。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

## 20. 完成后交接

完成后归档到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g3/`。
