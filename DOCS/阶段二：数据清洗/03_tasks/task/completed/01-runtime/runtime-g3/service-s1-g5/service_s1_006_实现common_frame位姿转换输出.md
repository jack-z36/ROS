# L3 微元任务：实现 common frame 位姿转换输出

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景一：提取夹爪开合以及位姿转换
L1：service_s1
L2 能力：common frame 位姿转换
L3 编号：service_s1_006
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s1-g5/service_s1_006_实现common_frame位姿转换输出.md`
任务类别：数据计算类
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景一/L2能力模块/common frame位姿转换.md`

## 2. 本次目标

```text
基于 frame_alignment 配置，把 raw pose 转换为 common camera pose 和 common TCP pose，并保留 raw pose 可追溯。
```

## 3. 本次不做

- 不生成 frame_alignment 配置。
- 不修改夹爪宽度提取。
- 不实现统一 `--dev` 一级入口。

## 4. 执行对象

- `src/data_clean/service/tcp_transform.py`
- `src/data_clean/service/mcap_io.py`
- `src/data_clean/config/mcap_process_config.py`
- [[CommonFrameCameraPose]]
- [[CommonFrameTcpPose]]

## 5. 执行依赖

- service_s1_004 已定义 `frame_alignment` 配置加载。
- raw MCAP 包含左右 Baton Mini pose topic。
- `common_anchor = left` 时，`common_from_right_start` 必须来自 `inverse(T_right_start_common)`，其中 `T_right_start_common` 是右手 Baton Mini 位于 common frame 标定位姿时输出的 raw pose。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：位姿转换配置生成
上游接口定义位置：DOCS/阶段二：数据清洗/03_tasks/task/active/service-s1-g4/service_s1_004_落地frame_alignment配置契约.md
当前 L3 期望消费的字段 / 文件 / 返回值：common_anchor、common_from_left_start、common_from_right_start、camera_from_left_tcp、camera_from_right_tcp；其中 common_from_right_start 已由上游配置生成器对 T_right_start_common 求逆得到
是否存在接口冲突：旧代码可能替换原 pose payload
如果有冲突，本次处理策略：raw pose 必须保留或有 raw 备份 topic；common camera/TCP pose 使用独立输出语义
```

## 7. 预期改动形态

- raw pose 不被不可追溯地覆盖。
- camera common pose 数量等于 raw pose 数量。
- TCP common pose 数量等于 raw pose 数量。
- dev 检验项输出 common pose 样本和 run log。

## 8. 现有程序盘点

- `tcp_transform.py` 已有 SE(3) 位姿变换基础逻辑，但旧配置基于 `start_from_common`。
- `mcap_io.py` 已在第一遍读取时生成 pose replacement payload，第二遍写出时可能替换原 pose payload。
- 现有风险是 raw pose 追溯不足，以及 TCP 外参方向此前命名混乱。

## 9. 本 L3 的真实改造边界

- 复用现有 pose 解码/编码和矩阵工具。
- 改造为 `frame_alignment` + `camera_from_*_tcp`。
- 不改 gripper 逻辑，不生成配置。

## 10. 计算输出

### 计算规则

| 输入情况 | 计算 / 判断规则 | 预期输出 | reason / error |
|---|---|---|---|
| 合法输入 | `T_common_camera = T_common_start * T_start_camera`；`T_common_tcp = T_common_camera * T_camera_tcp` | common camera/TCP pose | 无 |
| 缺失输入 | pose topic 缺失 | 清洗失败 | missing configured pose topic |
| 边界输入 | TCP 外参非单位 | 平移方向随 camera 姿态旋转 | 方向错误时测试失败 |
| 右手标定帧 | `T_common_right_start = inverse(T_right_start_common)`，再乘回该标定帧 raw pose | 结果应接近单位位姿 | inverse convention mismatch |

### 输出结构

| 字段 | 类型 | 含义 | 有效性要求 |
|---|---|---|---|
| `raw_pose` | ROS pose | Baton Mini 原始 pose | 可追溯 |
| `camera_pose_common` | ROS pose | common frame 下 camera pose | 数量等于 raw pose |
| `tcp_pose_common` | ROS pose | common frame 下 TCP pose | 数量等于 raw pose |

## 11. 数据计算验收重点

- 合法输入通过。
- 缺失或非法输入失败。
- 错误信息能说明具体缺口。
- 输出结构可被下游直接消费。

## 12. 开发者验收入口

`./start_data_clean.sh --dev -> 场景一 -> scene1_common_pose_transform`

测试产物：`artifacts/common_pose_samples.json`、可选 `artifacts/debug_common_pose.mcap`、`logs/run_log.json`。

## 13. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景一/L2能力模块/common frame位姿转换.md`
2. `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/FrameAlignmentConfig.md`
3. `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/CommonFrameTcpPose.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/active/service-s1-g4/service_s1_004_落地frame_alignment配置契约.md`

如果没有找到已完成相关 L3 历史记录，执行摘要中必须明确写明“未找到相关 L3 历史记录”。

### 必读约束文档

1. `DOCS/阶段二：数据清洗/约束文件/L3编码执行原则.md`
2. `DOCS/阶段二：数据清洗/约束文件/L3任务文件身份校验约束.md`
3. `DOCS/阶段二：数据清洗/约束文件/L3执行TDD与归档约束.md`
4. `DOCS/阶段二：数据清洗/约束文件/功能分支接力流程.md`
5. `DOCS/阶段二：数据清洗/约束文件/L3功能组目录约束.md`
6. `DOCS/阶段二：数据清洗/约束文件/上游依赖接口对齐约束.md`
7. `DOCS/阶段二：数据清洗/约束文件/文件存放规范.md`
8. `DOCS/阶段二：数据清洗/约束文件/L3现有实现盘点约束.md`
9. `DOCS/阶段二：数据清洗/02_service/场景一/执行约束.md`

### 必读代码

1. `src/data_clean/service/tcp_transform.py`
2. `src/data_clean/service/mcap_io.py`
3. `src/data_clean/config/mcap_process_config.py`

## 14. TDD 执行要求

执行前必须先完成 L3 任务文件身份校验。本 L3 涉及代码行为变更，必须先读取并使用 `$tdd`。

```text
$tdd
```

## 15. 允许修改

- `src/data_clean/service/`
- `src/data_clean/config/`
- `src/data_clean/tests/`
- 当前 L3 任务文件自身

## 16. 禁止修改

- 禁止让 raw pose 不可追溯地消失。
- 禁止把 `camera_from_*_tcp` 当成反方向外参。
- 禁止在本 L3 重新估计 `common_from_right_start`；这里只消费上游已由 `inverse(T_right_start_common)` 生成的配置。
- 禁止修改 gripper width 提取逻辑。

## 17. 验收命令

```bash
python3 -m pytest src/data_clean/tests/service -q
python3 -m pytest src/data_clean/tests/contract -q
```

## 18. 成功标准

- [ ] raw pose 保留或备份策略有测试覆盖。
- [ ] camera common pose 数量等于 raw pose 数量。
- [ ] TCP common pose 数量等于 raw pose 数量。
- [ ] 右手标定帧使用 `common_from_right_start * T_right_start_common` 后接近单位位姿。
- [ ] 非单位 TCP 外参方向测试通过。
- [ ] dev 检验项产物和日志契约明确。

## 19. 完成后交接

必须更新当前 L3 任务文件本身，追加执行摘要，并将当前 L3 移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/02-service-s1/service-s1-g5/`。移动后如果 active 功能组为空，删除该空目录。不写共享执行记录。
