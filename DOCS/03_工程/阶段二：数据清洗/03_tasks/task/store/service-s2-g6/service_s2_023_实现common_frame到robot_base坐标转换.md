# L3 微元任务：实现 common_frame 到 robot_base 坐标转换

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：IK 求解与 MCAP_B 生成器
L3 编号：service_s2_023
当前任务文件路径：`DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g6/service_s2_023_实现common_frame到robot_base坐标转换.md`
任务类别：数据计算类
来源 L2 文件：`DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/IK 求解与 MCAP_B 生成器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_023
  task_file: DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g6/service_s2_023_实现common_frame到robot_base坐标转换.md
  group: service-s2-g6
  branch: service-s2
  wave: 2
  parallel_group: service-s2-g6-p2
  depends_on: [service_s2_022]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [service_s2_024]
  conflict_scope:
    files: [src/data_clean/service/tcp_transform.py, src/data_clean/service/, src/data_clean/tests/]
    modules: [data_clean.service]
    config_keys: [scene2.ik_mcap_b.common_to_base]
  dispatch_status: ready
```

## 3. 本次目标

```text
复用或抽取场景一 pose transform helper，实现左右 common-frame TCP pose 到 RM65 robot-base TCP pose 的转换。
```

## 4. 本次不做

- 不调用睿尔曼 SDK。
- 不写 MCAP_B。
- 不修改场景一已有转换行为。

## 5. 执行对象

- `src/data_clean/service/tcp_transform.py`
- 新增或复用的通用 pose transform helper
- [[CommonToRobotBaseTransform]]
- [[RobotBaseTcpPose]]

## 6. 执行依赖

- `service_s2_022` 完成并归档。
- 场景一 common frame 位姿转换文档和现有代码已读取。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：场景一 common frame 位姿转换、MCAP_A 生成器。
上游接口定义位置：
- DOCS/03_工程/阶段二：数据清洗/02_service/场景一/L2能力模块/common frame位姿转换.md
- src/data_clean/service/tcp_transform.py
- DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/McapA.md
当前 L3 期望消费的字段 / 文件 / 返回值：x/y/z/qx/qy/qz/qw，四元数 xyzw，单位 m。
是否存在接口冲突：现有 `tcp_transform.py` 只有 start->common 专用函数，缺通用 matrix->pose helper。
如果有冲突，本次处理策略：抽取通用 helper，保持原函数兼容。
```

## 8. 预期改动形态

- `tcp_transform.py` 或同层 service helper 出现通用 pose->matrix、matrix->pose、compose transform 能力。
- 新增 common->robot_base 转换函数。
- 测试覆盖单位外参、平移、旋转、左右外参隔离和非法四元数。

## 现有程序盘点

- `src/data_clean/service/tcp_transform.py` 已实现 `_pose_to_matrix`、`build_start_from_common_transform`、`transform_pose_to_common_camera`。
- 现有实现使用 `scipy.spatial.transform.Rotation` 和 4x4 齐次矩阵，四元数顺序为 xyzw。
- 现有实现面向场景一 raw/start pose 到 common camera pose，尚未暴露通用 matrix->pose 或 common->base 转换。
- 本 L3 必须复用该数学路径，不得另写一套方向不明的四元数转换。

## 本 L3 的真实改造边界

- 可以抽取通用 helper，但不得改变 `transform_pose_to_common_camera` 的输入输出和现有测试行为。
- 可以新增 service 层转换函数和测试。
- 不允许修改 MCAP 读写器或开发者入口。

## 9. 计算输出

### 计算规则

| 输入情况 | 计算 / 判断规则 | 预期输出 | reason / error |
|---|---|---|---|
| 合法输入 | `T_robot_base_tcp = T_robot_base_common * T_common_tcp` | [[RobotBaseTcpPose]] | 无 |
| 缺失外参 | 左右任一侧缺 `robot_base_from_common` | strict 失败 | `missing_common_to_robot_base_transform` |
| 边界输入 | 单位外参 | 输出等于输入 common pose | 无 |
| 非法四元数 | 外参或 pose 四元数不可归一化 | 失败 | `invalid_quaternion` |

### 输出结构

| 字段 | 类型 | 含义 | 有效性要求 |
|---|---|---|---|
| `arm_side` | string | left/right | 必须合法 |
| `timestamp_ns` | int | 来源时间戳 | 原样保留 |
| `x/y/z` | float | base frame 位置 | 单位 m |
| `qx/qy/qz/qw` | float | base frame 姿态 | xyzw，单位四元数 |
| `source_topic` | string | 来源 topic | 必须可追溯 |

## 10. 数据计算验收重点

- 合法输入通过。
- 缺失或非法输入失败。
- 错误信息能说明具体缺口。
- 输出结构可被 IK 求解器直接消费。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/IK 求解与 MCAP_B 生成器.md`
2. `DOCS/03_工程/阶段二：数据清洗/02_service/场景一/L2能力模块/common frame位姿转换.md`
3. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/CommonToRobotBaseTransform.md`

### 必读相关微元任务记录

1. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g6/service_s2_022_定义IK与MCAP_B数据契约.md`

### 必读约束文档

1. `DOCS/02_约束/阶段二任务体系/L3编码执行原则.md`
2. `DOCS/02_约束/阶段二任务体系/L3任务文件身份校验约束.md`
3. `DOCS/02_约束/阶段二任务体系/L3调度元数据约束.md`
4. `DOCS/02_约束/阶段二任务体系/L3执行TDD与归档约束.md`
5. `DOCS/02_约束/阶段二任务体系/功能分支接力流程.md`
6. `DOCS/02_约束/阶段二任务体系/L3功能组目录约束.md`
7. `DOCS/02_约束/阶段二任务体系/开发者验收入口约束.md`
8. `DOCS/02_约束/阶段二任务体系/上游依赖接口对齐约束.md`
9. `DOCS/02_约束/阶段二任务体系/文件存放规范.md`
10. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/执行约束.md`
11. `DOCS/02_约束/阶段二任务体系/L3现有实现盘点约束.md`

### 必读代码

1. `src/data_clean/service/tcp_transform.py`
2. `src/data_clean/service/`
3. `src/data_clean/tests/`

## 12. TDD 执行要求

```bash
bash scripts/init_data_clean_dev.sh
```

必须使用 `$tdd`。

## 13. 开发者验收入口关联

| 项目 | 内容 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景二 |
| 对应功能检验项 | `scene2_ik_mcap_b_writer` |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 否 |
| 是否需要写测试产物 | 否 |
| 是否需要写运行日志 | 否 |
| 是否允许临时覆盖配置 | 是；外参仅本次运行生效 |
| 是否允许保存覆盖到配置文件 | 默认否 |
| 最终人工验收提示 | 由 `scene2_ik_mcap_b_writer` 间接覆盖 |

## 14. 允许修改

- `src/data_clean/service/tcp_transform.py`
- `src/data_clean/service/`
- `src/data_clean/tests/`
- 当前 L3 文件自身

## 15. 禁止修改

- 不修改 MCAP_A 生成器行为。
- 不调用睿尔曼 SDK。
- 不写 MCAP_B。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests/ -k "common_to_robot_base or pose_transform"
```

## 17. 成功标准

- [ ] common->base 转换函数已实现。
- [ ] 场景一现有 common frame 转换行为未倒退。
- [ ] 单位外参、平移、旋转和左右隔离测试通过。
- [ ] 非法四元数或缺外参有明确失败。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系，或说明由哪个功能检验项 / smoke test 间接覆盖。

## 18. 完成后交接

完成后归档到：

```text
DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g6/
```

