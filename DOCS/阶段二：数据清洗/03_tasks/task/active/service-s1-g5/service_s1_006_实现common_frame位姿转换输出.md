# L3 微元任务：实现 common frame 位姿转换输出

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景一：提取夹爪开合以及位姿转换
L1：service_s1
功能组：service-s1-g5
L2 能力：common frame 位姿转换
L3 编号：service_s1_006
任务类别：数据计算类

## 2. 本次目标

```text
基于 frame_alignment 配置，把 raw Baton Mini pose 转换为 common frame camera pose 和 common frame TCP pose，同时保留 raw pose 可追溯。
```

## 3. 本次不做

- 不生成 frame_alignment 配置。
- 不实现夹爪宽度提取。
- 不做场景二滤波或 IK。

## 4. 执行对象

- `src/data_clean/service/tcp_transform.py`
- `src/data_clean/service/mcap_io.py`
- `src/data_clean/config/mcap_process_config.py`
- `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/CommonFrameCameraPose.md`
- `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/CommonFrameTcpPose.md`

## 5. 上游接口确认

```text
本 L3 直接依赖的上游功能：位姿转换配置生成
上游接口定义位置：DOCS/阶段二：数据清洗/03_tasks/task/active/service-s1-g4/service_s1_004_落地frame_alignment配置契约.md
当前 L3 期望消费的字段 / 文件 / 返回值：common_anchor、common_from_left_start、common_from_right_start、camera_from_left_tcp、camera_from_right_tcp
是否存在接口冲突：旧代码可能直接替换原 pose payload
如果有冲突，本次处理策略：raw pose 必须保留或有 raw 备份 topic；common camera/TCP pose 使用独立输出语义
```

## 6. 计算规则

统一矩阵记号：

```text
T_A_B = B 坐标系在 A 坐标系下的位姿
```

通用计算：

```text
T_common_left_camera(t) = T_common_left_start * T_left_start_left_camera(t)
T_common_right_camera(t) = T_common_right_start * T_right_start_right_camera(t)
T_common_left_tcp(t) = T_common_left_camera(t) * T_left_camera_left_tcp
T_common_right_tcp(t) = T_common_right_camera(t) * T_right_camera_right_tcp
```

当 `common_anchor: left`：

```text
T_common_left_start = I
T_common_right_start = T_left_start_right_start
```

`camera_from_*_tcp` 表示 `T_camera_tcp`，禁止按反方向使用。

## 7. 预期改动形态

- raw pose 不被不可追溯地覆盖。
- 输出 camera common pose，数量等于 raw pose 数量。
- 输出 TCP common pose，数量等于 raw pose 数量。
- TCP 外参为单位占位时，TCP pose 等于 camera pose。
- 非单位 TCP 外参测试能检测矩阵方向错误。

## 8. 验收重点

- 左 UMI 静止在底座内时，`left_camera_pose_common` 接近单位位姿。
- 右 UMI 静止在底座内时，`right_camera_pose_common` 接近 `common_from_right_start`。
- `T_common_camera = I` 且 `T_camera_tcp.translation = [0.1, 0, 0]` 时，`T_common_tcp.translation = [0.1, 0, 0]`。
- 带旋转的 camera pose 下，TCP 平移方向随 camera 姿态正确旋转。

## 9. 必读上下文

1. `DOCS/阶段二：数据清洗/02_service/场景一/L2能力模块/common frame位姿转换.md`
2. `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/FrameAlignmentConfig.md`
3. `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/CommonFrameCameraPose.md`
4. `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/CommonFrameTcpPose.md`
5. `src/data_clean/service/tcp_transform.py`
6. `src/data_clean/service/mcap_io.py`

## 10. TDD 执行要求

执行前必须确认当前分支是 `service-s1`。本 L3 涉及代码行为和测试，必须先读取并使用 `$tdd`。

```text
$tdd
```

## 11. 允许修改

- `src/data_clean/service/`
- `src/data_clean/config/`
- `src/data_clean/tests/`
- 当前 L3 任务文件自身

## 12. 禁止修改

- 禁止让 raw pose 不可追溯地消失。
- 禁止把 `camera_from_*_tcp` 当成反方向外参。
- 禁止修改 gripper width 提取逻辑。

## 13. 验收命令

```bash
python3 -m pytest src/data_clean/tests/service -q
python3 -m pytest src/data_clean/tests/contract -q
```

## 14. 成功标准

- [ ] raw pose 保留或备份策略有测试覆盖。
- [ ] camera common pose 数量等于 raw pose 数量。
- [ ] TCP common pose 数量等于 raw pose 数量。
- [ ] 非单位 TCP 外参方向测试通过。

## 15. 完成后交接

必须更新当前 L3 文件、追加执行摘要，并移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/service-s1-g5/`。
