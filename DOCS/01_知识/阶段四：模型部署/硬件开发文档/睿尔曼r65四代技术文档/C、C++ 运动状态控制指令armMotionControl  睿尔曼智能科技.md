---
title: "C、C++: 运动状态控制指令armMotionControl | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/classes/armMotionControl/"
author:
published: 2025-05-19
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 运动状态控制指令armMotionControl

控制运动的急停、缓停、暂停、继续、清除轨迹以及查询当前规划类型。

## 轨迹缓停rm\_set\_arm\_slow\_stop()

说明

在当前正在运行的轨迹上停止。

- **方法原型：**
```c
int rm_set_arm_slow_stop(rm_robot_handle * handle)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
// 设置机器人缓慢停止  
if (rm_set_arm_slow_stop(robot_handle) == 0) {  
    printf("Arm set to slow stop successfully.\n");  
} else {  
    printf("Failed to set arm to slow stop.\n");  
}
```

## 轨迹急停rm\_set\_arm\_stop()

说明

关节最快速度停止，轨迹不可恢复。

- **方法原型：**
```c
int rm_set_arm_stop(rm_robot_handle * handle)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
// 设置机器人急停  
if (rm_set_arm_stop(robot_handle) == 0) {  
    printf("Arm set to stop successfully.\n");  
} else {  
    printf("Failed to set arm to stop.\n");  
}
```

## 轨迹暂停rm\_set\_arm\_pause()

说明

暂停在规划轨迹上，轨迹可恢复。

- **方法原型：**
```c
int rm_set_arm_pause(rm_robot_handle * handle)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
// 设置机器人暂停  
if (rm_set_arm_pause(robot_handle) == 0) {  
    printf("Arm set to pause successfully.\n");  
} else {  
    printf("Failed to set arm to pause.\n");  
}
```

## 暂停后继续轨迹运动rm\_set\_arm\_continue()

- **方法原型：**
```c
int rm_set_arm_continue(rm_robot_handle * handle)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
// 设置机器人暂停后继续  
if (rm_set_arm_continue(robot_handle) == 0) {  
    printf("Arm set to continue successfully.\n");  
} else {  
    printf("Failed to set arm to continue.\n");  
}
```

## 清除当前轨迹rm\_set\_delete\_current\_trajectory()

- **方法原型：**
```c
int rm_set_delete_current_trajectory(rm_robot_handle * handle)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

注意

必须在暂停后使用，否则机械臂会发生意外！！！！

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
// 删除当前轨迹  
if (rm_set_delete_current_trajectory(robot_handle) == 0) {  
    printf("Current trajectory deleted successfully.\n");
} else {  
    printf("Failed to delete Current trajectory.\n");  
}
```

## 清除所有轨迹rm\_set\_arm\_delete\_trajectory()

- **方法原型：**
```c
int rm_set_arm_delete_trajectory(rm_robot_handle * handle)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

注意

必须在暂停后使用，否则机械臂会发生意外！！！！

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
// 清除所有轨迹  
if (rm_set_arm_delete_trajectory(robot_handle) == 0) {  
    printf("Trajectory deleted successfully.\n");
} else {  
    printf("Failed to delete Trajectory.\n");  
}
```

## 获取当前正在规划的轨迹信息rm\_get\_arm\_current\_trajectory()

- **方法原型：**
```c
int rm_get_arm_current_trajectory(rm_robot_handle * handle,rm_arm_current_trajectory_e * type,float * data)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*  
*可以跳转 [rm\_arm\_current\_trajectory\_e](https://develop.realman-robotics.com/robot4th/apic/type/#rm_arm_current_trajectory_e%E6%9C%BA%E6%A2%B0%E8%87%82%E5%BD%93%E5%89%8D%E8%A7%84%E5%88%92%E7%B1%BB%E5%9E%8B) 查阅枚举类型详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `type` | 输入参数 | 返回的规划类型。 |
| `data` | 输出参数 | 存放无规划和关节空间规划为当前关节1~7角度数组；笛卡尔空间规划则为当前末端位姿。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
// 获取当前机械臂轨迹的信息
rm_arm_current_trajectory_e trajectory_type;  
float trajectory_data[7]; 
if (rm_get_arm_current_trajectory(robot_handle, &trajectory_type, trajectory_data) == 0) {  
    printf("Current arm trajectory type: %d\n", trajectory_type);    
}
```