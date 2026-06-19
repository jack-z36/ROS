---
title: "C、C++: 末端运动参数配置armTipVelocityParameters | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/classes/armTipVelocityParameters/"
author:
published: 2025-12-17
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 末端运动参数配置armTipVelocityParameters

机械臂末端运动参数设置及查询，包含线速度设置与查询、角速度设置与查询、角加速度设置与查询、碰撞等级设置与查询等。

## 设置末端最大线速度rm\_set\_arm\_max\_line\_speed()

- **方法原型：**
```c
int rm_set_arm_max_line_speed(rm_robot_handle * handle,float speed)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `speed` | 输入参数 | 末端最大线速度，单位m/s。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
//设置机械臂末端最大线速度0.1m/s
float speed = 0.1;
ret = rm_set_arm_max_line_speed(robot_handle,speed);
```

## 设置末端最大线加速度rm\_set\_arm\_max\_line\_acc()

- **方法原型：**
```c
int rm_set_arm_max_line_acc(rm_robot_handle * handle,float acc)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `acc` | 输入参数 | 末端最大线加速度，单位m/s^2。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
//设置机械臂末端最大线加速度2m/s²
float acc = 2;
ret = rm_set_arm_max_line_acc(robot_handle,acc);
```

## 设置末端最大角速度rm\_set\_arm\_max\_angular\_speed()

- **方法原型：**
```c
int rm_set_arm_max_angular_speed(rm_robot_handle * handle,float speed)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `speed` | 输入参数 | 末端最大角速度，单位rad/s。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
//设置机械臂末端最大角速度0.2rad/s
float speed = 0.2;
ret=rm_set_arm_max_angular_speed(robot_handle,speed);
```

## 设置末端最大角加速度rm\_set\_arm\_max\_angular\_acc()

- **方法原型：**
```c
int rm_set_arm_max_angular_acc(rm_robot_handle * handle,float acc)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `acc` | 输入参数 | 末端最大角加速度，单位rad/s^2。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
//设置机械臂末端最大角加速度4rad/s²
float acc = 4;
ret = rm_set_arm_max_angular_acc(robot_handle,acc);
```

## 设置末端参数为默认值rm\_set\_arm\_tcp\_init()

- **方法原型：**
```c
int rm_set_arm_tcp_init(rm_robot_handle * handle)
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
//初始化机械臂参数，机械臂的末端参数回复到默认值。默认参数为：
// 末端线速度：0.1m/s末端线加速度：0.5m/s²
// 末端角速度：0.2rad/s末端角加速度：1rad/s²
ret = rm_set_arm_tcp_init(robot_handle);
```

## 设置碰撞防护等级rm\_set\_collision\_state()

- **方法原型：**
```c
int rm_set_collision_state(rm_robot_handle * handle,int collision_stage)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `collision_stage` | 输入参数 | 等级：0~8，0-无碰撞检测，8-碰撞检测最灵敏。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
//设置机械臂碰撞防护等级为1
int stage = 1;
ret=rm_set_collision_state(robot_handle,stage,RM_BLOCK);
```

## 查询碰撞防护等级rm\_get\_collision\_stage()

- **方法原型：**
```c
int rm_get_collision_stage(rm_robot_handle * handle,int * collision_stage)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `collision_stage` | 输出参数 | 存放返回的碰撞等级值的变量，数据为0-8，0-无碰撞检测，8-碰撞检测最灵敏。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
//查询机械臂动力学碰撞等级
int stage = -1;
ret = rm_get_collision_stage(robot_handle,&stage);
```

## 获取末端最大线速度rm\_get\_arm\_max\_line\_speed()

- **方法原型：**
```c
int rm_get_arm_max_line_speed(rm_robot_handle * handle,float * speed)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `speed` | 输出参数 | 存放返回的末端最大线速度值的变量，单位m/s。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
//获取机械臂末端线速度
float speed = 0;                                                              
ret = rm_get_arm_max_line_speed(robot_handle,&speed);
```

## 获取末端最大线加速度rm\_get\_arm\_max\_line\_acc()

- **方法原型：**
```c
int rm_get_arm_max_line_acc(rm_robot_handle * handle,float * acc)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `acc` | 输出参数 | 存放返回的末端最大线加速度值的变量，单位m/s^2。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
//获取机械臂末端线加速度
float acc = 0;                                                            
ret = rm_get_arm_max_line_acc(robot_handle,&acc);
```

## 获取末端最大角速度rm\_get\_arm\_max\_angular\_speed()

- **方法原型：**
```c
int rm_get_arm_max_angular_speed(rm_robot_handle * handle,float * speed)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `speed` | 输出参数 | 存放返回的末端末端最大角速度值的变量，单位rad/s。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
//获取机械臂末端角速度
float speed = 0;
ret = rm_get_arm_max_angular_speed(robot_handle,&speed);
```

## 获取末端最大角加速度rm\_get\_arm\_max\_angular\_acc()

- **方法原型：**
```c
int rm_get_arm_max_angular_acc(rm_robot_handle * handle,float * acc)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `acc` | 输出参数 | 存放返回的末端最大角加速度值的变量，单位rad/s^2。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
//获取末端角加速度
float acc = 0;
ret = rm_get_arm_max_angular_acc(robot_handle,&acc);
```

## 设置DH参数rm\_set\_DH\_data()

- **方法原型** ：
```c
int rm_set_DH_data(rm_robot_handle * handle, rm_dh_t dh)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 、 [rm\_dh\_t](https://develop.realman-robotics.com/robot4th/apic/struct/dh/) 查阅结构体详细描述。*

- **参数说明** ：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `dh` | 输入参数 | DH参数 |

- **返回值** ：

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
// 设置机械臂当前DH参数（仅作示例，dh参数根据实际修改）
rm_dh_t dh_data = {
    .a = {0.0, 0.0, 0.0, 0.0, 0.0, 0.0},
    .d = {0.0, 0.0, 0.0, 0.0, 0.0, 0.0},
    .alpha = {0.0, 0.0, 0.0, 0.0, 0.0, 0.0},
    .offset = {0.0, 0.0, 0.0, 0.0, 0.0, 0.0}
};
rm_set_DH_data(handle, dh_data);
```

## 获取DH参数rm\_get\_DH\_data()

- **方法原型** ：
```c
int rm_get_DH_data(rm_robot_handle * handle, rm_dh_t *dh)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 、 [rm\_dh\_t](https://develop.realman-robotics.com/robot4th/apic/struct/dh/) 查阅结构体详细描述。*

- **参数说明** ：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `dh` | 输出参数 | DH参数。 |

- **返回值** ：

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
//查询机械臂DH参数
rm_dh_t dh_data;
ret = rm_get_DH_data(handle, &dh_data);
```

## 恢复机械臂默认 DH 参数rm\_set\_DH\_data\_default()

- **方法原型** ：
```c
int rm_set_DH_data_default(rm_robot_handle * handle)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明** ：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |

- **返回值** ：

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
//恢复机械臂默认DH参数
ret = rm_set_DH_data_default(handle);
```

## 设置避奇异模式rm\_set\_avoid\_singularity\_mode

注意

设置避奇异模式的接口仅支持六自由度机械臂。

- **方法原型** ：
```c
int rm_set_avoid_singularity_mode(rm_robot_handle *handle, int mode);
```
- **参数说明** ：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂控制句柄。 |
| `mode` | 输入参数 | 避奇异模式：0-不规避奇异点，1-规避奇异点。 |

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **返回值** ：

| 参数 | 说明 |
| --- | --- |
| 0 | 成功。 |
| 1 | 控制器返回false，传递参数错误或机械臂状态发生错误。 |
| \-1 | 数据发送失败，通信过程中出现问题。 |
| \-2 | 数据接收失败，通信过程中出现问题或者控制器超时没有返回。 |
| \-3 | 返回值解析失败，接收到的数据格式不正确或不完整。 |

- **使用示例**
```c
int mode = 0;
ret = rm_set_avoid_singularity_mode(handle, mode);
printf("%d\n", ret);
```

## 获取避奇异模式rm\_get\_avoid\_singularity\_mode

- **方法原型** ：
```c
int rm_get_avoid_singularity_mode(rm_robot_handle *handle, int* mode);
```
- **参数说明** ：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂控制句柄。 |
| `mode` | 输出参数 | 避奇异模式 0-不规避奇异点，1-规避奇异点 |

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **返回值** ：

| 参数 | 说明 |
| --- | --- |
| 0 | 成功。 |
| 1 | 控制器返回false，传递参数错误或机械臂状态发生错误。 |
| \-1 | 数据发送失败，通信过程中出现问题。 |
| \-2 | 数据接收失败，通信过程中出现问题或者控制器超时没有返回。 |
| \-3 | 返回值解析失败，接收到的数据格式不正确或不完整。 |

- **使用示例**
```c
int mode;
ret = rm_get_avoid_singularity_mode(handle, &mode);
printf("%d\n", ret);
printf("avoid_singularity_mode:%d\n", mode);
```