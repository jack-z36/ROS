---
title: "C、C++: 机械臂状态查询armState | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/classes/armState/"
author:
published: 2025-05-19
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 机械臂状态查询armState

机械臂当前状态、关节温度、电流、电压查询。

## 获取机械臂当前状态rm\_get\_current\_arm\_state()

获取机械臂的位姿、角度、机械臂错误码、系统错误码等信息。

- **方法原型：**
```c
int rm_get_current_arm_state(rm_robot_handle * handle,rm_current_arm_state_t * state)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 和 [rm\_current\_arm\_state\_t](https://develop.realman-robotics.com/robot4th/apic/struct/currentState/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `state` | 输出参数 | 机械臂当前状态结构体。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
// 获取机械臂当前状态  
rm_current_arm_state_t current_state;  
if (rm_get_current_arm_state(robot_handle, &current_state) == 0) { 
    printf("Current Pose: \n");  
    printf("Position: (%.3f, %.3f, %.3f) m\n",  
           current_state.pose.position.x, current_state.pose.position.y, current_state.pose.position.z);  
    printf("Quaternion: (%.3f, %.3f, %.3f, %.3f)\n",  
           current_state.pose.quaternion.w, current_state.pose.quaternion.x, current_state.pose.quaternion.y, current_state.pose.quaternion.z);  
    printf("Euler Angles: (%.3f, %.3f, %.3f) rad\n",  
           current_state.pose.euler.rx, current_state.pose.euler.ry, current_state.pose.euler.rz);  
    printf("Joint Angles: ");  
    for (int i = 0; i < ARM_DOF; i++) {  
        printf("%.2f ", current_state.joint[i]);  
    }  
    printf("\nArm Error: %u\n", current_state.arm_err);  
    printf("System Error: %u\n", current_state.sys_err);  
} else {  
    printf("Failed to get current arm state\n");  
}
```

## 获取关节当前温度rm\_get\_current\_joint\_temperature()

- **方法原型：**
```c
int rm_get_current_joint_temperature(rm_robot_handle * handle,float * temperature)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `temperature` | 输出参数 | 存放关节1~7温度数组。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
float temperature[ARM_DOF];  
if (rm_get_current_joint_temperature(robot_handle, temperature) == 0) {  
    printf("Joint Temperature: "); 
    for (int i = 0; i < ARM_DOF; i++) {  
        printf("%.2f ", temperature[i]);  
    }
    printf("\n");  
} else {  
    printf("Failed to get joint temperature\n");  
}
```

## 获取关节当前电流rm\_get\_current\_joint\_current()

- **方法原型：**
```c
int rm_get_current_joint_current(rm_robot_handle * handle,float * current)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `current` | 输出参数 | 存放关节1~7电流数组。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
float current[ARM_DOF];  
if (rm_get_current_joint_current(robot_handle, current) == 0) {  
    printf("Joint current: "); 
    for (int i = 0; i < ARM_DOF; i++) {  
        printf("%.2f ", current[i]);  
    }
    printf("\n");  
} else {  
    printf("Failed to get joint current\n");  
}
```

## 获取关节当前电压rm\_get\_current\_joint\_voltage()

- **方法原型：**
```c
int rm_get_current_joint_voltage(rm_robot_handle * handle,float * voltage)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `voltage` | 输出参数 | 存放关节1~7电压数组。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
float voltage[ARM_DOF];  
if (rm_get_current_joint_voltage(robot_handle, voltage) == 0) {  
    printf("Joint voltage: "); 
    for (int i = 0; i < ARM_DOF; i++) {  
        printf("%.2f ", voltage[i]);  
    }
    printf("\n");  
} else {  
    printf("Failed to get joint voltage\n");  
}
```

## 获取当前关节角度rm\_get\_joint\_degree()

- **方法原型：**
```c
int rm_get_joint_degree(rm_robot_handle * handle,float * joint)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `joint` | 输出参数 | 当前7个关节的角度数组。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
float degree[ARM_DOF];  
if (rm_get_joint_degree(robot_handle, degree) == 0) {  
    printf("Joint degree: "); 
    for (int i = 0; i < ARM_DOF; i++) {  
        printf("%.2f ", degree[i]);  
    }
    printf("\n");  
} else {  
    printf("Failed to get joint degree\n");  
}
```

## 获取机械臂所有状态信息rm\_get\_arm\_all\_state()

- **方法原型：**
```c
int rm_get_arm_all_state(rm_robot_handle * handle,rm_arm_all_state_t * state)机械臂状态查询
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 和 [rm\_arm\_all\_state\_t](https://develop.realman-robotics.com/robot4th/apic/struct/allState/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| handle | 输入参数 | 机械臂句柄。 |
| state | 输出参数 | 存储机械臂信息的结构体。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
rm_arm_all_state_t all_state;  
if (rm_get_arm_all_state(robot_handle, &all_state) == 0) {  
    printf("Joint Currents: ");  
    for (int i = 0; i < ARM_DOF; i++) {  
        printf("%.2f mA ", all_state.joint_current[i]);  
    }  
    printf("\nJoint Temperatures: ");  
    for (int i = 0; i < ARM_DOF; i++) {  
        printf("%.2f C ", all_state.joint_temperature[i]);  
    }  
    // 打印其他信息...  
} else {  
    printf("Failed to get arm all state\n");  
}
```

## 设置机械臂的初始角度rm\_set\_init\_pose()

给定一组关节角度，并将这组角度设置为机械臂的初始位置。

- **方法原型：**
```c
int rm_set_init_pose(rm_robot_handle * handle,float * joint)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `joint` | 输入参数 | 机械臂初始位置关节角度数组。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
// 定义一个包含关节角度的数组（6轴机械臂）  
float joint_angles[6] = {0.1, -0.3, 1.5, 2.7, -1.2, 0.8};  

// 调用函数设置初始姿态  
int result = rm_set_init_pose(robot_handle, joint_angles);  
if (result == 0) { 
    printf("Initial pose set successfully.\n");  
} else {  
    printf("Failed to set initial pose. Error code: %d\n", result);  
}
```

## 获取机械臂初始角度rm\_get\_init\_pose()

读取设置的机械臂初始位置下各个关节的角度。

- **方法原型：**
```c
int rm_get_init_pose(rm_robot_handle * handle,float * joint)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `joint` | 输出参数 | 存放机械臂初始位置关节角度数组。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
float joint_angles[6];  
// 调用函数获取初始姿态  
int result = rm_get_init_pose(robot_handle, joint_angles);  
if (result == 0) { 
    printf("Initial pose retrieved successfully.\n");  
    // 打印关节角度或位置 
    for (int i = 0; i < 6; i++) {  
        printf("Joint %d: %.2f\n", i + 1, joint_angles[i]);  
    }  
} else {  
    printf("Failed to retrieve initial pose.\n");  
}
```