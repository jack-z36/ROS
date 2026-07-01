# 02 使用睿尔曼官方函数生成基坐标系 TCP 位姿

## 问题定位

旧实现使用仓库内 SE(3) 矩阵计算，将 raw pose 转换到 `common_frame`，再叠加 TCP 外参得到 common-frame TCP pose。

新方案不再自研这段最终主链路计算，而是使用睿尔曼官方 Python SDK 算法接口完成坐标转换。

## 功能边界澄清

本文件讨论的是“位姿转换功能模块”的改造，不是删除整个转换模块。原先位姿转换功能模块实际承担两段功能：

1. 相机位姿到 TCP 位姿的转换。
   - 输入：Baton Mini 原始相机位姿、TCP 相对相机的外参或等价配置。
   - 输出：TCP 在对应侧相机坐标系下的位姿。
   - 这一段仍然保留在主链路中。

2. 相机坐标系到机械臂基坐标系的转换。
   - 输入：TCP 在相机坐标系下的位姿、工作坐标系在机械臂基坐标系下的位姿。
   - 输出：TCP 在对应侧机械臂基坐标系下的位姿。
   - 这一段必须改为调用睿尔曼官方 API，不再走 `common_frame`，也不得自研替代公式。

因此，真正废弃的是旧的 `common_frame` 配置生成和 common-frame 主链路，不是“相机位姿 -> TCP 位姿”这项基础能力。

## 官方文档依据

本方案参考以下睿尔曼 R65 四代官方技术文档：

- `/home/hit/下载/睿尔曼r65四代技术文档/机械臂Python API快速开始  睿尔曼智能科技.md`
- `/home/hit/下载/睿尔曼r65四代技术文档/Python 算法接口配置algo  睿尔曼智能科技.md`
- `/home/hit/下载/睿尔曼r65四代技术文档/Python 工作坐标系配置WorkCoordinateConfig  睿尔曼智能科技.md`
- `/home/hit/下载/睿尔曼r65四代技术文档/Python 表示一个坐标系的结构体rm_pose_t  睿尔曼智能科技.md`
- `/home/hit/下载/睿尔曼r65四代技术文档/Python 表示四元数的结构体rm_quat_t  睿尔曼智能科技.md`

关键结论：

- 睿尔曼 Python SDK 支持 Linux x86 / arm，要求 Python 3.9 以上。
- 官方快速开始给出的安装方式是 `pip install Robotic_Arm`，或从 `https://github.com/RealManRobot/RM_API2.git` 获取二次开发包。
- 官方示例统一使用 `from Robotic_Arm.rm_robot_interface import *` 导入 SDK。
- `Algo` 提供正逆解和位姿参数转换工具接口。
- `rm_algo_pos2matrix(pose)` 可把 `[x, y, z, rx, ry, rz]` 位姿转换为 `rm_matrix_t`。
- `rm_algo_workframe2base(matrix, pose_in_work, flag=1)` 是本链路的候选主函数，用于把工作坐标系下的工具端/TCP 位姿转换到基坐标系。
- `rm_pose_t.position` 的单位为 m。
- `rm_pose_t.euler` 的单位为 rad。
- `rm_quat_t` 字段顺序为 `w, x, y, z`。
- `WorkCoordinateConfig.rm_set_manual_work_frame(name, pose)` 中 `pose` 表示新工作坐标系相对于基坐标系的位姿，可作为“工作坐标系在机械臂基坐标系下的位姿”语义依据。

## 候选官方 API

主函数：

```python
Algo.rm_algo_workframe2base(
    matrix: rm_matrix_t,
    pose_in_work: rm_pose_t,
    flag: int = 1,
) -> list[float]
```

配套函数：

```python
Algo.rm_algo_pos2matrix(pose: list[float]) -> rm_matrix_t
```

必要结构：

```python
rm_pose_t
rm_position_t
rm_euler_t
rm_quat_t
rm_matrix_t
```

## 官方 API 环境搭建方案

后续实施前，需要先在阶段二 `data_clean` 实际运行所使用的 Python 环境中安装和验证睿尔曼 SDK。不能只在系统 Python 里安装后就认为运行环境可用。

### 1. 确认运行环境

需要记录以下信息：

```text
python_executable = 实际运行 start_data_clean.sh / data_clean service 的 Python
python_version >= 3.9
os = Linux x86 或 Linux arm
sdk_package = Robotic_Arm
```

如果阶段二运行在 conda、venv 或 ROS overlay 环境中，必须先激活同一个环境，再执行安装与校验。

### 2. 安装 SDK

优先按官方快速开始使用 pip 安装：

```bash
python3 -m pip install Robotic_Arm
```

如果目标机器无法访问 pip 源，使用官方二次开发包来源：

```bash
git clone https://github.com/RealManRobot/RM_API2.git
```

离线安装方式以后续实际 SDK 包结构为准；执行端不得自行复制零散 `.so` 或 Python 文件来绕过安装步骤，除非已记录来源、版本和加载路径。

### 3. 导入校验

安装后必须在同一个 Python 环境中验证：

```bash
python3 -c "from Robotic_Arm.rm_robot_interface import *; print(Algo)"
```

验收点：

- 能导入 `Robotic_Arm.rm_robot_interface`。
- 能访问 `Algo`。
- 能访问 `rm_robot_arm_model_e`、`rm_force_type_e`、`rm_pose_t`、`rm_position_t`、`rm_euler_t`。

### 4. 算法接口离线校验

位姿转换链路只依赖算法接口时，应优先设计为不需要连接真实机械臂即可运行。后续需要用最小脚本验证：

```text
1. 初始化 Algo(rm_robot_arm_model_e.RM_MODEL_RM_65_E, 实际 force_type)。
2. 调用 rm_algo_version()，确认算法库可用。
3. 调用 rm_algo_pos2matrix([0, 0, 0, 0, 0, 0])。
4. 构造 rm_pose_t 的 position/euler。
5. 调用 rm_algo_workframe2base(identity_work_matrix, pose_in_work, flag=1)。
```

验收点：

- 不连接真实机械臂时，算法接口也能完成基础位姿转换。
- 若 SDK 要求连接机械臂或读取控制器配置，必须在文档和实现中显式记录该依赖，不能隐藏成普通离线转换函数。
- 左臂和右臂的转换环境必须能分别提供自己的 `work_frame_in_arm_base_pose`，不得依赖某个全局当前工作坐标系状态。

### 5. 版本与路径记录

后续实现应在运行报告或 debug 日志中记录：

- Python 可执行文件路径。
- `Robotic_Arm` 包是否可导入。
- 算法库版本，优先使用 `Algo.rm_algo_version()`。
- `arm_model` 和 `force_type`。
- 是否连接真实机械臂。
- 官方 API 调用路径：`rm_algo_pos2matrix -> rm_algo_workframe2base`。

执行端后续实现时必须遵守：

1. 必须调用 `Algo.rm_algo_workframe2base()` 完成 work-frame 到 base-frame 的主转换。
2. 工作坐标系在基坐标系下的位姿先用 `rm_algo_pos2matrix()` 转成 `rm_matrix_t`，再传入 `rm_algo_workframe2base()`。
3. TCP 在相机坐标系下的位姿按本链路语义映射为 `pose_in_work`，即“TCP 在工作坐标系下的位姿”。
4. 不得用自研矩阵公式替代 `rm_algo_workframe2base()`。
5. 若实际 SDK 版本中函数签名与文档不一致，必须暂停并以本地 SDK introspection 或官方示例确认，不得猜测实现。

## 输入与输出映射

官方函数输入：

```text
1. TCP 在相机坐标系下的位姿
   -> 映射为 rm_algo_workframe2base 的 pose_in_work

2. 工作坐标系在机械臂基坐标系下的位姿
   -> 先通过 rm_algo_pos2matrix 转成 matrix
```

官方函数输出：

```text
TCP 在机械臂基坐标系下的位姿 list[float]
```

左右手必须分别调用：

```text
left:
  TCP 在左手相机坐标系下的位姿
  + 左手工作坐标系在左手机械臂基坐标系下的位姿
  -> rm_algo_workframe2base(...)
  -> TCP 在左手机械臂基坐标系下的位姿

right:
  TCP 在右手相机坐标系下的位姿
  + 右手工作坐标系在右手机械臂基坐标系下的位姿
  -> rm_algo_workframe2base(...)
  -> TCP 在右手机械臂基坐标系下的位姿
```

## 位姿表示要求

睿尔曼算法接口默认使用欧拉角位姿：

```text
[x, y, z, rx, ry, rz]
```

其中：

- `x, y, z` 单位为 m。
- `rx, ry, rz` 单位为 rad。
- `flag = 1` 返回欧拉角位姿 `[x, y, z, rx, ry, rz]`。
- `flag = 0` 返回四元数位姿 `[x, y, z, w, x, y, z]`。
- 若项目内部存储使用四元数，必须显式记录睿尔曼四元数字段顺序为 `w, x, y, z`，并避免与 ROS 常见 `x, y, z, w` 顺序混用。

## 建议调用流程

后续真正实施时，每一侧机械臂独立执行两段转换：

```text
第一段：相机位姿 -> TCP 在相机坐标系下的位姿
1. 读取 Baton Mini 原始相机位姿。
2. 读取 TCP 相对相机的外参或等价配置。
3. 生成 tcp_pose_in_camera。

第二段：TCP 在相机坐标系下的位姿 -> TCP 在机械臂基坐标系下的位姿
4. 初始化 Algo(arm_model=RM_MODEL_RM_65_E, force_type=实际末端/力传感器型号)。
5. 读取用户输入的 work_frame_in_arm_base_pose。
6. 将 work_frame_in_arm_base_pose 表示为 [x, y, z, rx, ry, rz]。
7. 调用 rm_algo_pos2matrix(work_frame_in_arm_base_pose) 得到 work_matrix。
8. 将 tcp_pose_in_camera 填入 rm_pose_t：
   - position = rm_position_t(x, y, z)
   - euler = rm_euler_t(rx, ry, rz)
9. 调用 rm_algo_workframe2base(work_matrix, tcp_pose_in_camera_as_work, flag=1)。
10. 将返回值记录为对应侧 arm-base TCP pose。
```

这里的“相机坐标系”在本链路中承担官方 API 的“工作坐标系”角色。也就是说，不再创建统一 `common_frame`，而是对左手、右手分别提供各自的工作坐标系在各自机械臂基坐标系下的位姿。

## 修改方法

后续真正实施时：

1. 场景一位姿转换模块保留“相机位姿 -> TCP 位姿”能力。
2. 场景一位姿转换模块新增或改造“TCP 相机坐标系 -> TCP 机械臂基坐标系”能力。
3. 第二段转换改为准备 `rm_algo_workframe2base()` 输入。
4. TCP 在相机坐标系下的位姿来自 Baton Mini 相机数据与 TCP 外参。
5. 工作坐标系在机械臂基坐标系下的位姿由用户输入，不由旧配置生成模块生成。
6. 输出写入左右机械臂基坐标系下的 TCP pose。
7. 场景二滤波直接消费该 TCP pose，不再消费 common-frame TCP pose。
8. 实现中不得把左右手共用同一个 `Algo` 状态里的工作坐标系，除非能证明每次调用前都显式重置了对应侧输入。

## 数据语义要求

输出必须明确携带或可追溯以下语义：

- `hand = left/right`
- `frame = left_arm_base/right_arm_base`
- `official_api = Algo.rm_algo_workframe2base`
- `work_frame_in_base_pose_source = 用户输入`
- `work_matrix_source = rm_algo_pos2matrix(work_frame_in_base_pose)`
- 位置单位为 m。
- 姿态欧拉角单位为 rad；若落盘为四元数，顺序必须明确为 `w, x, y, z` 或转换为项目统一顺序后写明。
- 来源输入包括 TCP 在相机坐标系下的位姿和工作坐标系在基坐标系下的位姿。

## 官方文档歧义与校验要求

官方文档中 `rm_algo_workframe2base()` 的参数表与返回值文字存在容易混淆之处：参数表把 `matrix` 描述为“工具端坐标在工作坐标系下矩阵”，返回值文字写为“工作坐标系在基坐标系下的位姿”。但同页示例使用 `work_matrix = rm_algo_pos2matrix([...])`，并注释为工作坐标系相关矩阵；与 `rm_algo_base2workframe()` 的反向接口共同看，当前方案将其解释为：

```text
matrix = 工作坐标系在基坐标系下的矩阵
pose_in_work = 工具端/TCP 在工作坐标系下的位姿
return = 工具端/TCP 在基坐标系下的位姿
```

后续实现前必须用以下最小用例确认：

1. `work_frame_in_base_pose = [0, 0, 0, 0, 0, 0]` 时，输出应与 `pose_in_work` 等价。
2. 使用同一 `work_matrix` 做 `workframe2base` 后，再调用 `base2workframe` 应能回到原 `pose_in_work`。
3. 左右手分别使用不同平移量的 work frame 时，输出必须体现各自 base frame 差异。

## 验收标准

后续完成实现后，应满足：

- 能证明位姿转换模块仍保留“相机位姿 -> TCP 在相机坐标系下位姿”的功能。
- 能证明位姿转换模块新增或改造了“TCP 在相机坐标系下位姿 -> TCP 在机械臂基坐标系下位姿”的功能。
- 能在阶段二实际运行 Python 环境中成功导入 `Robotic_Arm.rm_robot_interface`。
- 能记录 `Algo.rm_algo_version()` 或等价算法库版本信息。
- 测试能证明 `Algo.rm_algo_workframe2base()` 被调用。
- 测试能证明 `rm_algo_pos2matrix()` 用于生成工作坐标系在基坐标系下的矩阵。
- 测试能证明左手和右手不会混用基坐标系。
- 输出 TCP pose 坐标系分别为左机械臂基坐标系和右机械臂基坐标系。
- 主链路中不再出现 `common_frame -> robot_base` 后置转换。
- 测试覆盖 `flag = 1` 欧拉角输出，若项目落盘使用四元数，还必须覆盖四元数顺序转换。
