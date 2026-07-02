---
title: "Python: 算法接口配置algo | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/classes/algo/"
author:
published: 2026-01-09
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 算法接口配置algo

针对睿尔曼机械臂，提供正逆解、各种位姿参数转换等工具接口。

## 初始化算法依赖数据\_\_init\_\_()

- **方法原型：**
```python
__init__(self, arm_model: rm_robot_arm_model_e, force_type: rm_force_type_e):
```

*可以跳转 [枚举类型说明](https://develop.realman-robotics.com/robot4th/apipython/type/) 查阅 `rm_robot_arm_model_e` 和 `rm_force_type_e` 枚举详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `arm_model` | `rm_robot_arm_model_e` | 机械臂型号。 |
| `force_type` | `rm_force_type_e` | 传感器型号。 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)
```

## 获取算法库版本rm\_algo\_version()

- **方法原型：**
```python
rm_algo_version(self) -> str:
```
- **返回值:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| \- | `str` | 算法库版本号。 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

# 获取当前算法使用的机械臂安装角度
print(algo_handle.rm_algo_version())
```

## 设置安装角度rm\_algo\_set\_angle()

- **方法原型：**
```python
rm_algo_set_angle(self, x: float, y: float, z: float) -> None:
```
- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `x` | `float` | X轴安装角度，单位°。 |
| `y` | `float` | Y轴安装角度，单位°。 |
| `z` | `float` | Z轴安装角度，单位°。 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

# 设置当前算法使用的机械臂安装角度
algo_handle.rm_algo_set_angle(0,90,0)
```

## 获取安装角度rm\_algo\_get\_angle()

- **方法原型：**
```python
rm_algo_get_angle(self) -> tuple[float, float, float]:
```
- **返回值:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `x` | `float` | X轴安装角度，单位°。 |
| `y` | `float` | Y轴安装角度，单位°。 |
| `z` | `float` | Z轴安装角度，单位°。 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

# 获取当前算法使用的机械臂安装角度
print(algo_handle.rm_algo_get_angle())
```

## 设置工作坐标系rm\_algo\_set\_workframe()

- **方法原型：**
```python
rm_algo_set_workframe(self, frame: rm_frame_t) -> None:
```

*可以跳转 [rm\_frame\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/frame/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `frame` | `rm_frame_t` | 坐标系数据。 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

# 设置当前使用的工作坐标系位姿
frame = rm_frame_t("", [0.186350, 0.062099, 0.2, 3.141, 0, 1.569])
algo_handle.rm_algo_set_workframe(frame)
```

## 获取当前工作坐标系rm\_algo\_get\_curr\_workframe()

- **方法原型：**
```python
rm_algo_get_curr_workframe(self) -> dict[str, any]:
```
- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `dict[str, any]` | `rm_frame_t` | 返回当前工作坐标系字典，键为rm\_frame\_t结构体的字段名称。 |

*可以跳转 [rm\_frame\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/frame/) 查阅结构体详细描述。*

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

# 设置当前使用的工作坐标系位姿
frame = rm_frame_t("", [0.186350, 0.062099, 0.2, 3.141, 0, 1.569])
algo_handle.rm_algo_set_workframe(frame)

# 获取当前使用的工作坐标系位姿
print(algo_handle.rm_algo_get_curr_workframe())
```

## 设置工具坐标系rm\_algo\_set\_toolframe()

- **方法原型：**
```python
rm_algo_set_toolframe(self, frame: rm_frame_t) -> None:
```

*可以跳转 [rm\_frame\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/frame/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `frame` | `rm_frame_t` | 坐标系数据。 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

# 设置当前使用的工具坐标系
frame = rm_frame_t("", [0.186350, 0.062099, 0.2, 3.141, 0, 1.569], 5, 1, 1, 1)
algo_handle.rm_algo_set_toolframe(frame)
```

## 获取算法当前工具坐标系rm\_algo\_get\_curr\_toolframe()

- **方法原型：**
```python
rm_algo_get_curr_toolframe(self) -> dict[str, any]:
```
- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `dict[str, any]` | `rm_frame_t` | 返回当前工具坐标系字典，键为rm\_frame\_t结构体的字段名称。 |

*可以跳转 [rm\_frame\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/frame/) 查阅结构体详细描述。*

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

# 设置当前使用的工具坐标系
frame = rm_frame_t("", [0.186350, 0.062099, 0.2, 3.141, 0, 1.569], 5, 1, 1, 1)
algo_handle.rm_algo_set_toolframe(frame)

# 获取当前使用的工具坐标系
print(algo_handle.rm_algo_get_curr_toolframe())
```

## 设置算法关节最大限位rm\_algo\_set\_joint\_max\_limit()

- **方法原型：**
```python
rm_algo_set_joint_max_limit(self, joint_limit: list[float]) -> None:
```
- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `joint_limit` | `list[float]` | 关节最大限位数组，单位：°。 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

# 设置算法使用的关节最大限位
joint_max_limit = [178.0, 130.0, 135.0, 178.0, 128.0, 180.0]
algo_handle.rm_algo_set_joint_max_limit(joint_max_limit)
```

## 获取算法关节最大限位rm\_algo\_get\_joint\_max\_limit()

- **方法原型：**
```python
rm_algo_get_joint_max_limit(self) -> list[float]:
```
- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| \\ | `list[float]` | 返回关节最大限位数组，单位：°。 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

# 获取算法使用的关节最大限位
print(algo_handle.rm_algo_get_joint_max_limit())
```

## 设置算法关节最小限位rm\_algo\_set\_joint\_min\_limit()

- **方法原型：**
```python
rm_algo_set_joint_min_limit(self, joint_limit: list[float]) -> None:
```
- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `joint_limit` | list\[float\] | 关节最小限位数组，单位：°。 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

# 设置算法使用的关节最小限位
joint_min_limit = [-178.0, -130.0, -135.0, -178.0, -128.0, -180.0]
algo_handle.rm_algo_set_joint_min_limit(joint_min_limit)
```

## 获取算法关节最小限位rm\_algo\_get\_joint\_min\_limit()

- **方法原型：**
```python
rm_algo_get_joint_min_limit(self) -> list[float]:
```
- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| \\ | list\[float\] | 关节最小限位数组，单位：°。 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

# 获取算法使用的关节最小限位
print(algo_handle.rm_algo_get_joint_min_limit())
```

## 设置算法关节最大速度rm\_algo\_set\_joint\_max\_speed()

- **方法原型：**
```python
rm_algo_set_joint_max_speed(self, joint_limit: list[float]) -> None:
```
- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `joint_limit` | `list[float]` | 最大转速（RPM），单位转/分。 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

# 设置算法使用的关节最大速度
joint_max_speed = [30.0, 30.0, 37.5, 37.5, 37.5, 37.5]
algo_handle.rm_algo_set_joint_max_speed(joint_max_speed)
```

## 获取算法关节最大速度rm\_algo\_get\_joint\_max\_speed()

- **方法原型：**
```python
rm_algo_get_joint_max_speed(self) -> list[float]:
```
- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `list[float]` | `float` | 存放返回的最大转速（RPM），单位转/分。 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

# 获取算法使用的关节最小限位
print(algo_handle.rm_algo_get_joint_max_speed())
```

## 设置算法关节最大加速度rm\_algo\_set\_joint\_max\_acc()

- **方法原型：**
```python
rm_algo_set_joint_max_acc(self, joint_limit: list[float]) -> None:
```
- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `joint_limit` | `float` | 最大加速度，单位RPM/s。 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

# 设置算法使用的关节最大加速度
joint_max_acc = [166.6666717529297, 166.6666717529297, 166.6666717529297, 166.6666717529297, 166.6666717529297, 166.6666717529297]
algo_handle.rm_algo_set_joint_max_acc(joint_max_acc)
```

## 获取算法关节最大加速度rm\_algo\_get\_joint\_max\_acc()

- **方法原型：**
```python
rm_algo_get_joint_max_acc(self) -> list[float]:
```
- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `list[]` | `float` | 存放返回的最大加速度，单位RPM/s。 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

# 获取算法使用的关节最小限位
print(algo_handle.rm_algo_get_joint_max_acc())
```

## 设置逆解求解模式rm\_algo\_set\_redundant\_parameter\_traversal\_mode()

- **方法原型：**
```python
rm_algo_set_redundant_parameter_traversal_mode(self, mode: bool) -> None:
```
- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `mode` | `bool` | \- true：遍历模式，冗余参数遍历的求解策略。适于当前位姿跟要求解的位姿差别特别大的应用场景，如MOVJ\_P、位姿编辑等，耗时较长   \- false：单步模式，自动调整冗余参数的求解策略。适于当前位姿跟要求解的位姿差别特别小、连续周期控制的场景，如笛卡尔空间规划的位姿求解等，耗时短 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

# 设置逆解求解为遍历模式
algo_handle.rm_algo_set_redundant_parameter_traversal_mode(true)
```

## 逆解函数rm\_algo\_inverse\_kinematics()

- **方法原型：**
```python
rm_algo_inverse_kinematics(self, params: rm_inverse_kinematics_params_t) -> tuple[int, list[float]]:
```
- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `params` | `rm_inverse_kinematics_params_t` | 逆解输入参数结构体。 |

*可以跳转 [rm\_inverse\_kinematics\_params\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/inverseKinematicsParams/) 查阅结构体详细描述。*

- **返回值:** tuple\[int,list\[float\]\]: 包含两个元素的元组。
	- int 逆解结果:
		| 参数 | 类型 | 说明 | 处理建议 |
		| --- | --- | --- | --- |
		| 0 | `int` | 逆解成功。 | \- |
		| 1 | `int` | 逆解失败。 | 如果您认为目标位姿是可解的而逆解失败，以下是一些可能的步骤和考虑因素：   1.检查输入参数：确保上一时刻关节角度及目标位姿输入正确，例如位置单位要求米，是否错误使用了毫米。   2.设置逆解求解模式：调用rm\_algo\_set\_redundant\_parameter\_traversal\_mode 设置合适的求解模式。   3.检查handle句柄是否有效：如连接机械臂使用，需确保句柄是有效的，API内部会根据句柄将机械臂当前配置同步算法。   4.检查安装角度、坐标系、限位等是否设置：在不连接机械臂时，如果不使用默认的配置，需调用对应算法接口进行设置。   5.联系技术支持：如以上建议都没有解决问题，且确定目标位姿是可解的，可联系睿尔曼公司技术支持，我们将协助您进行验证。 |
		| \-1 | `int` | 上一时刻关节角度输入为空。 | 检查上一时刻的关节角度输入是否为空。 |
		| \-2 | `int` | 目标位姿四元数不合法。 | 检查params中的目标位姿四元数是否合法。 |
		- `list[float]` ：输出的关节角度 单位°，长度为机械臂自由度.
- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

# 逆解从关节角度[0, 0, -90, 0, -90, 0]到目标位姿[0.186350, 0.062099, 0.200000, 3.141, 0, 1.569]。目标位姿姿态使用欧拉角表示。
params = rm_inverse_kinematics_params_t([0, 0, -90, 0, -90, 0], [0.186350, 0.062099, 0.200000, 3.141, 0, 1.569], 1)
q_out = algo_handle.rm_algo_inverse_kinematics(params)
print(q_out)
```

## 计算逆运动学全解(当前仅支持六自由度机器人)rm\_algo\_inverse\_kinematics\_all()

- **方法原型：**
```python
rm_algo_inverse_kinematics_all(self, params: rm_inverse_kinematics_params_t) -> rm_inverse_kinematics_all_solve_t:
```

*可以跳转 [rm\_inverse\_kinematics\_params\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/inverseKinematicsParams/) 、 [rm\_inverse\_kinematics\_all\_solve\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/inverseKinematicsAllSolve/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `params` | `rm_inverse_kinematics_params_t` | 逆解输入参数结构体。 |

- **返回值:**
	`rm_inverse_kinematics_all_solve_t` 逆解的全解结构体
- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *
arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type) 

params = rm_inverse_kinematics_params_t([1.943, 21.305, -2.819, 78.314, 1.013, 80.404], [0.3, 0, 0.3, 3.14, 0, 3.14], 1)
result = algo_handle.rm_algo_inverse_kinematics_all(params)
print(f"Inverse kinematics calculation: {result.result} num: {result.num}")
for solve in result.q_solve:
    print(list(solve))
```

## 从多解中选取最优解（当前仅支持六自由度机器人）rm\_algo\_ikine\_select\_ik\_solve()

- **方法原型：**
```python
rm_algo_ikine_select_ik_solve(self, weight: list[float], params: rm_inverse_kinematics_all_solve_t) -> int:
```

*可以跳转 [rm\_inverse\_kinematics\_all\_solve\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/inverseKinematicsAllSolve/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `weight` | `list[float]` | 权重,建议默认值为 `[1,1,1,1,1,1]` |
| `params` | `rm_inverse_kinematics_all_solve_t` | 待选解的全解结构体 |

- **返回值:**
	`int` 最优解索引，选解结果为ik\_solve.q\_solve\[i\] -1：当前机器人非六自由度，当前仅支持六自由度机器人
- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *
arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号  
algo_handle = Algo(arm_model, force_type)
result = algo_handle.rm_algo_inverse_kinematics_all(params)
print(f"Inverse kinematics calculation: {result.result} num: {result.num}")

ret = algo_handle.rm_algo_ikine_select_ik_solve([1.0, 1.0, 1.0, 1.0, 1.0, 1.0], result)
print(f"rm_algo_ikine_select_ik_solve ret: {ret}")
if ret != -1:
  print("best solution :",list(result.q_solve[ret]))
```

## 检查逆解结果是否超出关节限位（当前仅支持六自由度机器人）rm\_algo\_ikine\_check\_joint\_position\_limit()

- **方法原型：**
```python
rm_algo_ikine_check_joint_position_limit(self, q_solve_i:list[float]) -> int:
```
- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `q_solve_i` | `list[float]` | 一组解，即一组关节角度，单位:° |

- **返回值:**
	`int` 0:表示未超限 i:表示关节i超限，优先报序号小的关节 -1：当前机器人非六自由度，当前仅支持六自由度机器人
- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *
arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type) 
params = rm_inverse_kinematics_params_t([1.943, 21.305, -2.819, 78.314, 1.013, 80.404], [0.3, 0, 0.3, 3.14, 0, 3.14], 1)
result = algo_handle.rm_algo_inverse_kinematics_all(params)
print(f"Inverse kinematics calculation: {result.result} num: {result.num}")
for solve in result.q_solve:
  ret = algo_handle.rm_algo_ikine_check_joint_position_limit(list(solve))
  print(f"rm_algo_ikine_check_joint_position_limit ret: {ret}")
```

## 检查逆解结果是否超出速度限位（当前仅支持六自由度机器人）rm\_algo\_ikine\_check\_joint\_velocity\_limit()

- **方法原型：**
```python
rm_algo_ikine_check_joint_velocity_limit(self, dt:float, q_ref:list[float], q_solve_i:list[float]) -> int:
```
- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `dt` | `float` | 两帧数据之间的时间间隔，即控制周期，单位sec |
| `q_ref` | `list[float]` | 参考关节角度或者第一帧数据角度，单位：° |
| `q_solve_i` | `list[float]` | 一组解，即一组关节角度，单位:° |

- **返回值:**
	`int` 0:表示未超限 i:表示关节i超限，优先报序号小的关节 -1：当前机器人非六自由度，当前仅支持六自由度机器人。
- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *
arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号  
algo_handle = Algo(arm_model, force_type)
params = rm_inverse_kinematics_params_t([1.943, 21.305, -2.819, 78.314, 1.013, 80.404], [0.3, 0, 0.3, 3.14, 0, 3.14], 1)
result = algo_handle.rm_algo_inverse_kinematics_all(params)
print(f"Inverse kinematics calculation: {result.result} num: {result.num}")
for solve in result.q_solve:
  ret = algo_handle.rm_algo_ikine_check_joint_velocity_limit(0.01, params.q_ref, list(solve))
  print(f"rm_algo_ikine_check_joint_velocity_limit ret: {ret}")
```

## 根据参考位形计算臂角大小（仅支持RM75）rm\_algo\_calculate\_arm\_angle\_from\_config\_rm75()

- **方法原型：**
```python
rm_algo_calculate_arm_angle_from_config_rm75(self,q_ref:list[float]) -> tuple[int, float]:
```
- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `q_ref` | `list[float]` | 当前参考位形的关节角度，单位° |

- **返回值:**
	`tuple[int, float]` 包含两个元素的元组。
	- `int` 计算结果:
		| 参数 | 类型 | 说明 |
		| --- | --- | --- |
		| 0 | `int` | 求解成功。 |
		| \-1 | `int` | 求解失败。 |
		- `float` 计算结果，当前参考位形对应的臂角大小，单位°
- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *
arm_model = rm_robot_arm_model_e.RM_MODEL_RM_75_E  # RM_75机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)
q_ref = [0.000,57.780,17.734,28.890,11.156,74.482]
ret,phi = algo_handle.rm_algo_calculate_arm_angle_from_config_rm75(q_ref)
print(f"rm_algo_calculate_arm_angle_from_config_rm75 ret: {ret} arm_angle: {phi}")
```

## 臂角法求解RM75逆运动学 rm\_algo\_inverse\_kinematics\_rm75\_for\_arm\_angle()

- **方法原型：**
```python
rm_algo_inverse_kinematics_rm75_for_arm_angle(self,params:rm_inverse_kinematics_params_t,arm_angle:float) -> tuple[int,list[float]]:
```
- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `params` | `rm_inverse_kinematics_params_t` | 逆解参数结构体 |
| `arm_angle` | `float` | 指定轴角大小,单位:° |

- **返回值:**
	`tuple[int,list[float]]` 包含两个元素的元组。
	- `int` 计算结果:
		| 参数 | 类型 | 说明 |
		| --- | --- | --- |
		| 0 | `int` | 求解成功。 |
		| \-1 | `int` | 求解失败。 |
		| \-2 | `int` | 求解结果超出限位。 |
		| \-3 | `int` | 机型非RM75。 |
		- `list[float]` 求解结果,单位:°
- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *
arm_model = rm_robot_arm_model_e.RM_MODEL_RM_75_E  # RM_75机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)
q_ref = [0.0, 110.0, 20.0, 40.0, 30.0, 180.0, 20.0]
ret,phi = algo_handle.rm_algo_calculate_arm_angle_from_config_rm75(q_ref)
params = rm_inverse_kinematics_params_t([0.0, 110.0, 20.0, 40.0, 30.0, 180.0, 20.0], [0.3,0.0,0.3,3.14,0.0,3.14], 1)
ret,q_out = algo_handle.rm_algo_inverse_kinematics_rm75_for_arm_angle(params,phi)
print(f"rm_algo_inverse_kinematics_rm75_for_arm_angle ret: {ret} q_out: {q_out}")
```

## 正解算法rm\_algo\_forward\_kinematics()

- **方法原型：**
```python
rm_algo_forward_kinematics(self, joint: list[float], flag: int = 1) -> list[float]:
```
- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `joint` | `list[float]` | 关节角度，单位：°。 |
| `flag` | `int` | 选择姿态表示方式，默认欧拉角表示姿态。 - 0: 返回使用四元数表示姿态的位姿列表\[x,y,z,w,x,y,z\]；- 1: 返回使用欧拉角表示姿态的位姿列表\[x,y,z,rx,ry,rz\]。 |

- **返回值:**

`list[float]`: 解得目标位姿列表。

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

# 正解关节角度[0, 0, -90, 0, -90, 0]返回位姿，使用欧拉角表示姿态
pose = algo_handle.rm_algo_forward_kinematics([0, 0, -90, 0, -90, 0])
print(pose)
```

## 欧拉角转四元数rm\_algo\_euler2quaternion()

- **方法原型：**
```python
rm_algo_euler2quaternion(self, eul: list[float]) -> list[float]:
```
- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `eul` | `list[float]` | 欧拉角列表\[rx.ry,rz\]，单位：rad。 |

- **返回值:**

`list[float]`: 四元数列表\[w,x,y,z\]

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

# 将欧拉角[-0.259256, -0.170727, 0.35621]转换为四元数
print(algo_handle.rm_algo_euler2quaternion([-0.259256, -0.170727, 0.35621]))
```

## 四元数转欧拉角rm\_algo\_quaternion2euler()

- **方法原型：**
```python
rm_algo_quaternion2euler(self, quat: list[float]) -> list[float]:
```
- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `quat` | `list[float]` | 四元数列表\[w,x,y,z\]。 |

- **返回值:**

`list[float]`: 欧拉角列表\[rx.ry,rz\]，单位：rad。

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

# 将四元数(0,0,0,1)转为欧拉角
print(algo_handle.rm_algo_quaternion2euler([0,0,0,1]))
```

## 欧拉角转旋转矩阵rm\_algo\_euler2matrix()

- **方法原型：**
```python
rm_algo_euler2matrix(self, eu: list[float]) -> rm_matrix_t:
```

*可以跳转 [rm\_matrix\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/matrix/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `eu` | `list[float]` | 欧拉角列表\[rx.ry,rz\]，单位：rad。 |

- **返回值:**

`rm_matrix_t`: 旋转矩阵。

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

# 将欧拉角(3.14, 0, 0)转为旋转矩阵
mat = algo_handle.rm_algo_euler2matrix([3.14, 0, 0])
```

## 位姿转旋转矩阵rm\_algo\_pos2matrix()

- **方法原型：**
```python
rm_algo_pos2matrix(self, pose: list[float]) -> rm_matrix_t:
```
- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `pose` | `list[float]` | 位置姿态列表\[x,y,z,rx,ry,rz\]。 |

- **返回值:**

`rm_matrix_t`: 旋转矩阵。

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

# 将位姿转为旋转矩阵
mat = algo_handle.rm_algo_pos2matrix([-0.177347, 0.438112, -0.215102, 2.09078, 0.942362, 2.39144])
```

## 旋转矩阵转位姿rm\_algo\_matrix2pos()

- **方法原型：**
```python
rm_algo_matrix2pos(self, matrix: rm_matrix_t, flag: int = 1) -> list[float]:
```

*可以跳转 [rm\_matrix\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/matrix/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `matrix` | `rm_matrix_t` | 旋转矩阵。 |
| `flag` | `int` | 选择姿态表示方式，默认欧拉角表示姿态。- 0: 返回使用四元数表示姿态的位姿列表\[x,y,z,w,x,y,z\]；- 1: 返回使用欧拉角表示姿态的位姿列表\[x,y,z,rx,ry,rz\]。 |

- **返回值:**

`list[float]`: 解得目标位姿。

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

# 将旋转矩阵转为位姿
data = [1.0, 0.0, 0.0, 10.0],[0.0, 1.0, 0.0, 20.0],[0.0, 0.0, 1.0, 30.0],[0.0, 0.0, 0.0, 1.0]
mat = rm_matrix_t(4,4,data)

print(algo_handle.rm_algo_matrix2pos(mat))
```

## 基坐标系转工作坐标系rm\_algo\_base2workframe()

- **方法原型：**
```python
rm_algo_base2workframe(self, matrix: rm_matrix_t, pose_in_base: rm_pose_t, flag: int = 1) -> list[float]:
```
- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `matrix` | `rm_matrix_t` | 工作坐标系在基坐标系下的矩阵。 |
| `pose_in_base` | `rm_pose_t` | 工具端坐标在基坐标系下位姿。 |
| `flag` | `int` | 选择姿态表示方式，默认欧拉角表示姿态；   \- 0: 返回使用四元数表示姿态的位姿列表\[x,y,z,w,x,y,z\]；   \- 1: 返回使用欧拉角表示姿态的位姿列表\[x,y,z,rx,ry,rz\]。 |

*可以跳转 [rm\_matrix\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/matrix/) 和 [rm\_pose\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/pose/) 查阅结构体详细描述。*

- **返回值:**

`list[float]`: 基坐标系在工作坐标系下的位姿。

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

# 基坐标系转工作坐标系，work_matrix为工作坐标系在基坐标系下的矩阵，end_pose为工具端坐标在基坐标系下的位姿
work_matrix = algo_handle.rm_algo_pos2matrix([-0.177347, 0.438112, -0.215102, 2.09078, 0.942362, 2.39144])
end_pose =  rm_pose_t()
end_pose.position = rm_position_t(0.186350, 0.062099, 0.2)
end_pose.euler = rm_euler_t(3.141, 0, 1.569)
print(algo_handle.rm_algo_base2workframe(work_matrix, end_pose))
```

## 工作坐标系转基坐标系rm\_algo\_workframe2base()

- **方法原型：**
```python
rm_algo_workframe2base(self, matrix: rm_matrix_t, pose_in_work: rm_pose_t, flag: int = 1) -> list[float]:
```

*可以跳转 [rm\_matrix\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/matrix/) 和 [rm\_pose\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/pose/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `matrix` | `rm_matrix_t` | 工具端坐标在工作坐标系下矩阵。 |
| `pose_in_work` | `rm_pose_t` | 工具端坐标在工作坐标系下位姿。 |
| `flag` | `int` | 选择姿态表示方式，默认欧拉角表示姿态；   \- 0: 返回使用四元数表示姿态的位姿列表\[x,y,z,w,x,y,z\]；   \- 1: 返回使用欧拉角表示姿态的位姿列表\[x,y,z,rx,ry,rz\]。 |

- **返回值:**

`list[float]`: 工作坐标系在基坐标系下的位姿。

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

# 工作坐标系转基坐标系，work_matrix为工具端坐标在工作坐标系下矩阵，end_pose为工具端坐标在工作坐标系下位姿
work_matrix = algo_handle.rm_algo_pos2matrix([-0.177347, 0.438112, -0.215102, 2.09078, 0.942362, 2.39144])
end_pose =  rm_pose_t()
end_pose.position = rm_position_t(0.186350, 0.062099, 0.2)
end_pose.euler = rm_euler_t(3.141, 0, 1.569)
print(algo_handle.rm_algo_workframe2base(work_matrix, end_pose))
```

## 末端位姿转成工具位姿rm\_algo\_end2tool()

- **方法原型：**
```python
rm_algo_end2tool(self, eu_end: rm_pose_t, flag: int = 1) -> list[float]:
```

*可以跳转 [rm\_pose\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/pose/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `eu_end` | `rm_pose_t` | 基于世界坐标系和默认工具坐标系的末端位姿。 |
| `flag` | `int` | 选择姿态表示方式，默认欧拉角表示姿态；   \- 0: 返回使用四元数表示姿态的位姿列表\[x,y,z,w,x,y,z\]；   \- 1: 返回使用欧拉角表示姿态的位姿列表\[x,y,z,rx,ry,rz\]。 |

`list[float]`: 基于工作坐标系和工具坐标系的末端位姿。

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

# 末端位姿转工具位姿
eu_end = rm_pose_t()
eu_end.position = rm_position_t(-0.259256, -0.170727, 0.35621)
eu_end.euler = rm_euler_t(3.14, 0, 0)
print(algo_handle.rm_algo_end2tool(eu_end))
```

## 工具位姿转末端位姿rm\_algo\_tool2end()

- **方法原型：**
```python
rm_algo_tool2end(self, eu_tool: rm_pose_t, flag: int = 1) -> list[float]:
```

*可以跳转 [rm\_pose\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/pose/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `eu_tool` | `rm_pose_t` | 基于工作坐标系和工具坐标系的末端位姿。 |
| `flag` | `int` | 选择姿态表示方式，默认欧拉角表示姿态；   \- 0: 返回使用四元数表示姿态的位姿列表\[x,y,z,w,x,y,z\]；   \- 1: 返回使用欧拉角表示姿态的位姿列表\[x,y,z,rx,ry,rz\]。 |

`list[float]` 基于世界坐标系和默认工具坐标系的末端位姿。

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

# 末端位姿转工具位姿
eu_tool = rm_pose_t()
eu_tool.position = rm_position_t(-0.259256, -0.170727, 0.35621)
eu_tool.euler = rm_euler_t(3.14, 0, 0)
print(algo_handle.rm_algo_tool2end(eu_tool))
```

## 计算环绕运动位姿rm\_algo\_rotate\_move()

- **方法原型：**
```python
rm_algo_rotate_move(self, curr_joint: list[float], rotate_axis: int, rotate_angle: float, choose_axis: rm_pose_t, flag: int = 1) -> list[float]:
```

*可以跳转 [rm\_pose\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/pose/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `curr_joint` | `list[float]` | 当前关节角度,单位°。 |
| `rotate_axis` | `int` | 旋转轴: 1:x轴, 2:y轴, 3:z轴。 |
| `rotate_angle` | `float` | 旋转角度: 旋转角度, 单位°。 |
| `choose_axis` | `rm_pose_t` | 指定计算时使用的坐标系。 |
| `flag` | `int` | 选择姿态表示方式，默认欧拉角表示姿态；   \- 0: 返回使用四元数表示姿态的位姿列表\[x,y,z,w,x,y,z\]；   \- 1: 返回使用欧拉角表示姿态的位姿列表\[x,y,z,rx,ry,rz\]。 |

- **返回值:**

`list[float]`:目标位姿。

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

# 计算当前角度绕pose坐标系X轴旋转5度。返回位姿用欧拉角表示
current_joint = [0, 0, -60, 0, 60, 0]
choose_axis =  rm_pose_t()
choose_axis.position.x = 0
choose_axis.position.y = 0
choose_axis.position.z = 0
choose_axis.euler.rx = 0
choose_axis.euler.ry = 0
choose_axis.euler.rz = 0
print(algo_handle.rm_algo_rotate_move(current_joint, 1, 5, choose_axis))
```

## 计算沿工具坐标系运动位姿rm\_algo\_cartesian\_tool()

- **方法原型：**
```python
rm_algo_cartesian_tool(self, curr_joint: list[float], move_lengthx: float, move_lengthy: float, move_lengthz: float, flag: int = 1) -> list[float]:
```
- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `curr_joint` | `list[float]` | 当前关节角度，单位：度。 |
| `move_lengthx` | `float` | 沿X轴移动长度，单位：米。 |
| `move_lengthy` | `float` | 沿Y轴移动长度，单位：米。 |
| `move_lengthz` | `float` | 沿Z轴移动长度，单位：米。 |
| `flag` | `int` | 选择姿态表示方式，默认欧拉角表示姿态；   \- 0: 返回使用四元数表示姿态的位姿列表\[x,y,z,w,x,y,z\]；   \- 1: 返回使用欧拉角表示姿态的位姿列表\[x,y,z,rx,ry,rz\]。 |

- **返回值:**

`list[float]`:目标位姿。

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

# 计算当前角度沿工具坐标系运动位姿
current_joint = [0, 0, -60, 0, 60, 0]
algo_handle.rm_algo_cartesian_tool(current_joint, 0.01, 0, 0.01)
```

## 计算Pos和Rot沿某坐标系有一定的位移和旋转角度后，所得到的位姿数据rm\_algo\_pose\_move()

- **方法原型：**
```python
rm_algo_pose_move(self, poseCurrent: list[float], deltaPosAndRot: list[float], frameMode: int) -> list[float]
```
- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `poseCurrent` | `list[float]` | 当前时刻位姿（欧拉角形式） |
| `deltaPosAndRot` | `list[float]` | 移动及旋转数组，位置移动（单位：m），旋转（单位：度） |
| `frameMode` | `int` | 坐标系模式选择 0:Work（work即可任意设置坐标系），1:Tool |

- **返回值:**

`list[float]`: 平移旋转后的位姿。

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

# 设置当前使用的工具坐标系
frame = rm_frame_t("", [0.01, 0.01, 0.01, 0.5, 0.5, 0.5], 1, 0, 0, 0)
algo_handle.rm_algo_set_toolframe(frame)

# 当前位姿
current_joint = [0,-30,90,30,90,0]
poseCurrent = algo_handle.rm_algo_forward_kinematics(current_joint)
print("当前位姿:", poseCurrent)

# 计算变化后的位姿
deltaPosAndRot = [0.01,0.01,0.01,20,20,20]
afterPosAndRot = algo_handle.rm_algo_pose_move(poseCurrent, deltaPosAndRot,1)
print("平移旋转后的位姿:", afterPosAndRot)
```

## 设置算法DH参数rm\_algo\_set\_dh()

- **方法原型：**
```python
rm_algo_set_dh(self, dh_data: rm_dh_t) -> None:
```

*可以跳转 [rm\_dh\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/dh/) 查阅结构体详细描述。*

- **参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `dh_data` | `rm_dh_t` | DH参数。 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

# 设置机械臂当前DH参数（仅作示例，根据实际dh参数修改）
dh_data = rm_dh_t(a=[0, 0, 0, 0, 0, 0], d=[0, 0, 0, 0, 0, 0], alpha=[0, 0, 0, 0, 0, 0], offset=[0, 0, 0, 0, 0, 0])
arm.rm_algo_set_dh(dh_data)
```

## 获取算法DH参数rm\_algo\_get\_dh()

- **方法原型：**
```python
rm_algo_get_dh(self) -> rm_dh_t:
```
- **参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `dh` | `rm_dh_t` | 返回当前DH参数。 |

*可以跳转 [rm\_dh\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/dh/) 查阅结构体详细描述。*

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

# 获取算法DH参数
print(arm.rm_algo_get_dh().to_dict())
```

## 数值法判断机器人是否处于奇异位形 rm\_algo\_universal\_singularity\_analyse()

- **方法原型：**
```python
rm_algo_universal_singularity_analyse(self, q:list[float], singluar_value_limit:float) -> int:
```
- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `q` | `list[float]` | 要判断的关节角度（机械零位描述），单位deg。 |
| `singluar_value_limit` | `float` | 最小奇异值阈值。 |

- **返回值:**
	`int` 0：表示在当前阈值条件下正常；-1：表示在当前阈值条件下判断为奇异区；-2：表示计算失败。
- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

# 肩部奇异区关节角度
q_s = [0, 43.4, -105.7, 0, -30, 0]
singularity_limit = 0.01
ret_qs = algo_handle.rm_algo_universal_singularity_analyse(q_s, singularity_limit)
```

## 设置自定义阈值(仅适用于解析法分析机器人奇异状态)rm\_algo\_kin\_set\_singularity\_thresholds()

- **方法原型：**
```python
rm_algo_kin_set_singularity_thresholds(self,limit_qe:float,limit_qw:float, limit_d:float)-> None:
```
- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `limit_qe` | `float` | 肘部奇异区域范围设置(即J3接近0的范围,若为RML63，则是J3接近-9.68的范围),单位: °,default: 10°。 |
| `limit_qw` | `float` | 腕部奇异区域范围设置(即J5接近0的范围),单位: °,default: 10°。 |
| `limit_d` | `float` | 肩部奇异区域范围设置(即腕部中心点距离奇异平面的距离), 单位: m, default: 0.05。 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

limit_qe = 12; # 肘部奇异阈值， 单位deg
limit_qw = 12; # 腕部奇异阈值， 单位deg
limit_d  = 0.05;  # 肩部奇异阈值， 单位m
algo_handle.rm_algo_kin_set_singularity_thresholds(limit_qe, limit_qw, limit_d)
```

## 恢复初始阈值(仅适用于解析法分析机器人奇异状态)rm\_algo\_kin\_singularity\_thresholds\_init()

阈值初始化为：limit\_qe=10deg,limit\_qw=10deg,limit\_d = 0.05m

- **方法原型：**
```python
rm_algo_kin_singularity_thresholds_init(self)-> None:
```
- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

algo_handle.rm_algo_kin_singularity_thresholds_init() #将阈值初始化为默认值
```

## 获取自定义阈值(仅适用于解析法分析机器人奇异状态)rm\_algo\_kin\_get\_singularity\_thresholds()

- **方法原型：**
```python
rm_algo_kin_get_singularity_thresholds(self)-> tuple[float,float,float]:
```
- **返回值:**
	- tuple\[float,float,float\] 自定义阈值:
		| 参数 | 类型 | 说明 | 处理建议 |
		| --- | --- | --- | --- |
		| `limit_qe` | `float` | 肘部奇异区域范围设置(即J3接近0的范围,若为RML63，则是J3接近-9.68的范围),单位: °,default: 10°。 | \- |
		| `limit_qw` | `float` | 腕部奇异区域范围设置(即J5接近0的范围),单位: °,default: 10°。 | \- |
		| `limit_d` | `float` | 肩部奇异区域范围设置(即腕部中心点距离奇异平面的距离), 单位: m, default: 0.05。 | \- |
- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type)

print(algo_handle.rm_algo_kin_get_singularity_thresholds())
```

## 解析法判断机器人是否处于奇异位形（仅支持六自由度）rm\_algo\_kin\_robot\_singularity\_analyse()

- **方法原型：**
```python
rm_algo_kin_robot_singularity_analyse(self,q:list[float]) -> tuple[int,float]:
```
- **参数说明:**
	| 参数 | 类型 | 说明 |
	| --- | --- | --- |
	| `q` | `list[float]` | 要判断的关节角度,单位°。 |
- **返回值:**
	- int：奇异位形判断结果。
		| 参数 | 类型 | 说明 | 处理建议 |
		| --- | --- | --- | --- |
		| 0 | `int` | 在当前阈值条件下正常 | \- |
		| \-1 | `int` | 肩部奇异。 | \- |
		| \-2 | `int` | 肘部奇异。 | \- |
		| \-3 | `int` | 腕部奇异。 | \- |
		- float：返回腕部中心点到肩部奇异平面的距离，该值越接近0说明越接近肩部奇异,单位m。
- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *
arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type) 

limit_qe = 12; # 肘部奇异阈值， 单位deg
limit_qw = 12; # 腕部奇异阈值， 单位deg
limit_d  = 0.05;  # 肩部奇异阈值， 单位m
algo_handle.rm_algo_kin_set_singularity_thresholds(limit_qe, limit_qw, limit_d)

# 肩部奇异区关节角度
q_s = [0, 43.4, -105.7, 0, -30, 0]
ret_qs,distance = algo_handle.rm_algo_kin_robot_singularity_analyse(q_s)
print(f"q_s singularity: {ret_qs} distance : {distance}")
```

## 设置工具包络球参数 rm\_algo\_set\_tool\_envelope()

- **方法原型：**
```python
rm_algo_set_tool_envelope(self, toolSphere_i: int, data: rm_tool_sphere_t) -> None:
```

*可以跳转 [rm\_tool\_sphere\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/toolToolEnvelope/) 查阅结构体详细描述。*

- **参数说明:**
	| 参数 | 类型 | 说明 |
	| --- | --- | --- |
	| `toolSphere_i` | `int` | 工具包络球编号 (0~4)。 |
	| `data` | `rm_tool_sphere_t` | 工具包络球参数,注意其参数在末端法兰坐标系下描述。 |
- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *
arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type) 
# 设置工具包络球参数
toolSphere_i = 0
data = rm_tool_sphere_t()
data.radius = 0.01
data.center = rm_position_t(0.01, 0.01, 0.01)
algo_handle.rm_algo_set_tool_envelope(toolSphere_i, data)
```

## 获取工具包络球参数 rm\_algo\_get\_tool\_envelope()

- **方法原型：**
```python
rm_algo_get_tool_envelope(self, toolSphere_i: int) -> rm_tool_sphere_t:
```

*可以跳转 [rm\_tool\_sphere\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/toolToolEnvelope/) 查阅结构体详细描述。*

- **参数说明:**
	| 参数 | 类型 | 说明 |
	| --- | --- | --- |
	| `toolSphere_i` | `int` | 工具包络球编号 (0~4)。 |
- **返回值:**
	`rm_tool_sphere_t` 工具包络球参数,注意其参数在末端法兰坐标系下描述
- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *
arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E  # RM_65机械臂
force_type = rm_force_type_e.RM_MODEL_RM_B_E  # 标准版
# 初始化算法的机械臂及末端型号
algo_handle = Algo(arm_model, force_type) 
# 获取工具包络球参数
toolSphere_i = 0  
print(algo_handle.rm_algo_get_tool_envelope(toolSphere_i))
```

## 遥操作运动学结构体初始化遥操作运动学结构体 rm\_algo\_ik\_remote\_init

- **方法原型：**
```python
rm_algo_ik_remote_init(self, dT: float, tool_or_work: int) -> None:
```
- **参数说明:**
	| 参数 | 类型 | 说明 |
	| --- | --- | --- |
	| `dT` | `float` | 用户下发周期设置。 |
	| `tool_or_work` | `int` | 0: 相对工具坐标系 1: 相对工作坐标系。 |
- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)
enable_state = None  
print(arm.rm_get_collision_remove_enable())

arm.rm_delete_robot_arm()
```

## 设置末端位姿误差权重 rm\_algo\_set\_error\_weight

- **方法原型：**
```python
rm_algo_set_error_weight(self, weight: list[float]) -> None:
```
- **参数说明:**
	| 参数 | 类型 | 说明 |
	| --- | --- | --- |
	| `weight` | `list[float]` | 长度为6的数组，对应末端位姿x,y,z,rx,ry,rz的权重，取值0~1权重越大对应的位姿到达精确度越高。 |
- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)
weight = [0.5, 0.5, 0.5, 0.0, 0.0, 0.0, 0.0]
print(arm.rm_algo_set_error_weight(weight))

arm.rm_delete_robot_arm()
```

## 设置关节速度权重rm\_algo\_set\_dq\_weight

- **方法原型：**
```python
rm_algo_set_dq_weight(self, dq_weight: list[float]) -> None:
```
- **参数说明:**
	| 参数 | 类型 | 说明 |
	| --- | --- | --- |
	| `dq_weight` | `list[float]` | 长度为自由度个数的数组，为关节最大限速乘以权重，取值0~1 权重越大则跟踪效果越好。 |
- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)
dq_weight = [0.5, 0.5, 0.5, 0.0, 0.0, 0.0]
print(arm.rm_algo_set_dq_weight(dq_weight))

arm.rm_delete_robot_arm()
```

## 使能七轴机械臂肘部追踪功能rm\_algo\_enable\_q3\_tracker

- **方法原型：**
```python
rm_algo_enable_q3_tracker(self, is_open: int) -> None:
```
- **参数说明:**
	| 参数 | 类型 | 说明 |
	| --- | --- | --- |
	| `is_open` | `int` | 1: 启动追踪； 0: 关闭追踪。 |
- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)
is_open = 1
print(arm.rm_algo_enable_q3_tracker(is_open))

arm.rm_delete_robot_arm()
```

## 设置七轴机械臂肘部追踪等级rm\_algo\_set\_q3\_tracker\_velocity\_level

- **方法原型：**
```python
rm_algo_set_q3_tracker_velocity_level(self, level: float) -> None:
```
- **参数说明:**
	| 参数 | 类型 | 说明 |
	| --- | --- | --- |
	| `level` | `float` | 追踪等级，取值0~1，等级越高，追踪速度越快。 |
- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)
level = 0.5
print(arm.rm_algo_set_q3_tracker_velocity_level(level))

arm.rm_delete_robot_arm()
```

## 设置七轴机械臂肘部追踪下的关节3的追踪角度rm\_algo\_set\_7dof\_q3\_track\_angle

- **方法原型：**
```python
rm_algo_set_7dof_q3_track_angle(self, obj_angle: float) -> int:
```
- **参数说明:**
	| 参数 | 类型 | 说明 |
	| --- | --- | --- |
	| `obj_angle` | `float` | 关节3的目标追踪角度。 |
- **返回值:**
	| 参数 | 类型 | 说明 |
	| --- | --- | --- |
	| \-2 | `int` | angle is over joint\_limit（角度超出关节限位）。 |
	| 0 | `int` | success（成功）。 |
- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)
obj_angle = 50.0
print(arm.rm_algo_set_7dof_q3_track_angle(obj_angle))

arm.rm_delete_robot_arm()
```

## 统一的关节角度限位设置接口rm\_algo\_set\_joint\_limit\_angle

- **方法原型：**
```python
rm_algo_set_joint_limit_angle(self, dof_type: rm_dofType_e, joint: rm_jointType_e, limit: rm_limitType_e, angle: float) -> int:
```
- **参数说明:**
	| 参数 | 类型 | 说明 |
	| --- | --- | --- |
	| `dof_type` | `rm_dofType_e` | 机械臂自由度类型 (DOF\_TYPE\_6 或 DOF\_TYPE\_7)。 |
	| `joint` | `rm_jointType_e` | 要设置的关节 (JOINT\_Q3 或 JOINT\_Q4；七轴支持设置关节3和关节4，六轴仅支持关节3)。 |
	| `limit` | `rm_limitType_e` | 限位类型 (LIMIT\_MAX 或 LIMIT\_MIN)。 |
	| `angle` | `float` | 要设置的角度值。 |
- **返回值:**
	| 参数 | 类型 | 说明 |
	| --- | --- | --- |
	| \-1 | `int` | 无效的参数 (自由度、关节、限位类型错误或指针为空)。 |
	| \-2 | `int` | 设置的角度值超出硬件/系统限制。 |
	| \-3 | `int` | 输入角度超出算法固有关节限位。 |
	| 0 | `int` | 成功。 |
- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)
dof_type = rm_dofType_e.DOF_TYPE_6
joint = rm_jointType_e.JOINT_Q4
limit = rm_limitType_e.LIMIT_MAX
angle = 30.0
print(arm.rm_algo_set_joint_limit_angle(dof_type, joint, limit, angle))

arm.rm_delete_robot_arm()
```

## 逆解函数rm\_algo\_ik\_remote

注意

1.建议客户在仿真模式下先验证自己下发的数据是否有异常后再开启真机使用。  
2.机械臂肘关节限位防护：禁止关节4（7轴）/关节3（6轴）完全打直为0，否则边界奇异易引发机械臂震荡、回移困难等异常；需通过限位设置接口或示教器安全配置设置非0软限位（限位值可在仿真模式下调试确定）。  
3.机械臂关节软限位防护：功能自带关节软限位效果，但应避免运动至软限位；若到位姿下发后关节仍需向限位外转动以满足位姿要求，易引发机械臂震荡等异常。

- **方法原型：**
```python
def rm_algo_ik_remote(self, T06d: rm_Mat_t, q_in: list[float], q_out: POINTER(c_float)) -> int:
```
- **参数说明:**
	| 参数 | 类型 | 说明 |
	| --- | --- | --- |
	| `T06d` | `rm_Mat_t` | 目标末端位姿矩阵。 |
	| `q_in` | `list[float]` | 当前关节角度列表（长度匹配自由度）。 |
	| `q_out` | `POINTER(c_float)` | 提前初始化的ctypes浮点数组（输出参数，接收求解结果）。 |
- **返回值:**
	| 参数 | 类型 | 说明 |
	| --- | --- | --- |
	| \-4 | `int` | UNKNOW ROBOT TYPE（未知机器人类型）。 |
	| \-1 | `int` | IK FAILED（逆解失败）。 |
	| \-2 | `int` | IK LIMITED（逆解超出限位）。 |
	| 0 | `int` | IK SUCCESSFUL（逆解成功）。 |
- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)
rm_T06d = rm_Mat_t()
rm_T06d.row = 4
rm_T06d.col = 4
for i in range(4):
    for j in range(4):
        rm_T06d.data[i][j] = 1.0 if i == j else 0.0  # 单位矩阵

# 2. 初始化当前关节角度（6自由度示例）
q_in = [30.0, 30.0, 30.0, 40.0, 40.0, 40.0]

# 3. 手动初始化q_out（ctypes数组，长度和q_in一致，必须提前分配内存）
q_out = (c_float * len(q_in))()  # 关键：提前创建ctypes数组，作为输出参数传入

# 4. 调用逆解函数（传入4个参数：self(隐式) + rm_T06d + q_in + q_out）
print(arm.rm_algo_ik_remote(rm_T06d, q_in, q_out))
  
# 5. 结果处理与打印
if ret == 0:
    # 将ctypes数组转换为Python列表，方便查看
    q_out_list = [float(val) for val in q_out]
    print(f"10run ik_remote success!ret = {ret}, q_in = {q_in}, q_out = {q_out_list}")
else:
    print(f"10run ik_remote false!ret = {ret}")

arm.rm_delete_robot_arm()
```

## 设置限位保持功能接口rm\_algo\_set\_enable\_limit\_holdon

- **方法原型：**
```python
rm_algo_set_enable_limit_holdon(self, enable: int) -> None:
```
- **参数说明:**
	| 参数 | 类型 | 说明 |
	| --- | --- | --- |
	| `enable` | `int` | 0: 关闭限位保持 1: 开启限位保持 若客户不调用此接口则默认为0即关闭限位保持功能, 当调用ik\_remote\_init时自动初始化为0。 |
- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)
enable = 0
arm.rm_algo_set_enable_limit_holdon(enable)
print(f"设置限位保持 success! enable = {enable}")

arm.rm_delete_robot_arm()
    printf("set_enable_limit_holdon (enable=0, 关闭限位保持) runs successfully!\n");
```