---
title: "C、C++: 系统配置controllerConfig | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/classes/controllerConfig/"
author:
published: 2026-03-30
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 系统配置controllerConfig

控制器状态获取、电源控制、错误清除、有线网口IP地址配置、软件信息获取。

## 获取控制器状态rm\_get\_controller\_state()

- **方法原型：**
```c
int rm_get_controller_state(rm_robot_handle * handle,float * voltage,float * current,float * temperature,int * err_flag )
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `voltage` | 输出参数 | 返回的电压。 |
| `current` | 输出参数 | 返回的电流。 |
| `temperature` | 输出参数 | 返回的温度。 |
| `err_flag` | 输出参数 | 控制器运行错误代码。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
//获取控制器状态
float voltage = 0;                                                            
float current = 0;                                                            
float temperature = 0;                                                        
int sys_err = 0;                                                         
ret = rm_get_controller_state(robot_handle, &voltage, &current, &temperature, &sys_err);
```

## 设置机械臂电源rm\_set\_arm\_power()

- **方法原型：**
```c
int rm_set_arm_power(rm_robot_handle * handle,int arm_power)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `arm_power` | 输入参数 | 1-上电状态，0 断电状态。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
//控制机械臂上电
ret = rm_set_arm_power(robot_handle, 1);
```

## 读取机械臂电源状态rm\_get\_arm\_power\_state()

- **方法原型：**
```c
int rm_get_arm_power_state(rm_robot_handle * handle,int * power_state)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `power_state` | 输出参数 | 获取到的机械臂电源状态，1-上电状态，0 断电状态。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
//读取机械臂电源状态
int power;
ret = rm_get_arm_power_state(robot_handle,&power);
```

## 读取控制器的累计运行时间rm\_get\_system\_runtime()

- **方法原型：**
```c
int rm_get_system_runtime(rm_robot_handle * handle,int * day,int * hour,int * min,int * sec
)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `day` | 输出参数 | 读取到的时间。 |
| `hour` | 输出参数 | 读取到的时间。 |
| `min` | 输出参数 | 读取到的时间。 |
| `sec` | 输出参数 | 读取到的时间。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
//获取控制器的累计运行时间
char state = 0;
int day;
int hour;
int min;
int sec;
ret = rm_get_system_runtime(robot_handle, &day, &hour, &min, &sec);
```

## 清零控制器的累计运行时间rm\_clear\_system\_runtime()

- **方法原型：**
```c
int rm_clear_system_runtime(rm_robot_handle * handle)
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
//清空控制器累计运行时间
ret = rm_clear_system_runtime(robot_handle);
```

## 读取关节的累计转动角度rm\_get\_joint\_odom()

- **方法原型：**
```c
int rm_get_joint_odom(rm_robot_handle * handle,float * joint_odom)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `joint_odom` | 输出参数 | 存放各关节累计的转动角度的数组。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
//获取关节累计转动角度
float odom[7];
ret = rm_get_joint_odom(robot_handle,odom);
```

## 清零关节累计转动的角度rm\_clear\_joint\_odom()

- **方法原型：**
```c
int rm_clear_joint_odom(rm_robot_handle * handle)
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
//清除关节累计转动角度
ret = rm_clear_joint_odom(robot_handle);
```

## 配置有线网口IP地址rm\_set\_NetIP()

- **方法原型：**
```c
int rm_set_NetIP(rm_robot_handle * handle,const char * ip, const char* netmask, const char* gw)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `ip` | 输入参数 | 有线网口 IP 地址。 |
| `netmask` | 输入参数 | 有线网口子网掩码。 |
| `gw` | 输入参数 | 有线网口网关地址。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
//配置有线网卡IP地址
ret = rm_set_NetIP(robot_handle,(char*)"192.168.1.19",(char*)"255.255.255.0",(char*)"192.168.1.1");
```

## 清除系统错误rm\_clear\_system\_err()

- **方法原型：**
```c
int rm_clear_system_err(rm_robot_handle * handle)
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
//清除系统错误代码
ret = rm_clear_system_err(robot_handle);
```

## 读取机械臂软件信息rm\_get\_arm\_software\_info()

- **方法原型：**
```c
int rm_get_arm_software_info(rm_robot_handle * handle,rm_arm_software_version_t * software_info)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 和 [rm\_arm\_software\_version\_t](https://develop.realman-robotics.com/robot4th/apic/struct/softwareVersion/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `software_info` | 输入参数 | 机械臂软件信息结构体。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
//读取机械臂软件信息
rm_arm_software_version_t info;
ret = rm_get_arm_software_info(handle, &arm_software_version);
```

## 查询控制器RS485模式rm\_get\_controller\_RS485\_mode()

- **方法原型：**
```c
int rm_get_controller_RS485_mode(rm_robot_handle * handle,int * mode,int * baudrate,int * timeout)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `mode` | 输出参数 | 存放模式。0-代表默认 RS485 串行通讯，1-代表 modbus-RTU 主站模式，2-代表 modbus-RTU 从站模式。 |
| `baudrate` | 输出参数 | 存放波特率。 |
| `timeout` | 输入参数 | modbus 协议超时时间，单位 100ms，仅在 modbus-RTU 模式下提供此字段。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
int mode;
int baudrate;
int timeout;
ret = rm_get_controller_RS485_mode(robot_handle, &mode, &baudrate, &timeout);
```

## 查询工具端RS485模式rm\_get\_tool\_RS485\_mode()

- **方法原型：**
```c
int rm_get_tool_RS485_mode(rm_robot_handle * handle,int * mode,int * baudrate,int * timeout)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `mode` | 输出参数 | 存放模式。0-代表默认 RS485 串行通讯，1-代表 modbus-RTU 主站模式，2-代表 modbus-RTU 从站模式。 |
| `baudrate` | 输出参数 | 存放波特率。 |
| `timeout` | 输入参数 | modbus 协议超时时间，单位 100ms，仅在 modbus-RTU 模式下提供此字段。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
int mode;
int baudrate;
int timeout;
ret = rm_get_tool_RS485_mode(robot_handle, &mode, &baudrate, &timeout);
```

## 查询关节软件版本号rm\_get\_joint\_software\_version()

获取到的关节软件版本号为字符串，可直接获取当前关节软件版本号。

- **方法原型：**
```c
int rm_get_joint_software_version(rm_robot_handle *handle,int *version, rm_version_t *joint_v);
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 和 [rm\_version\_t](https://develop.realman-robotics.com/robot4th/apic/struct/version/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `version` | 输出参数 | 预留参数，第四代控制器不适用。 |
| `joint_v` | 输出参数 | 获取到的各关节软件版本号字符串数组。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
//获取关节软件版本号
int joint_v[7] = {0};
rm_version_t joint_version[7];
ret = rm_get_joint_software_version(handle, joint_v, joint_version);
```

## 查询末端接口板软件版本号rm\_get\_tool\_software\_version()

获取到的末端接口板软件版本号为字符串，可直接获取当前末端接口板软件版本号。

- **方法原型：**
```c
int rm_get_tool_software_version(rm_robot_handle *handle, int *version, rm_version_t *end_v);
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 和 [rm\_version\_t](https://develop.realman-robotics.com/robot4th/apic/struct/version/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `version` | 输出参数 | 预留参数，第四代控制器不适用。 |
| `end_v` | 输出参数 | 获取到的末端接口板软件版本号字符串。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
//查询末端接口板软件版本号    
rm_version_t tool_version;
int tool_v = 0;
ret = rm_get_tool_software_version(handle,&tool_v, &tool_version);
```

## 设置Web服务器使能状态rm\_set\_webserver\_enabled

- **方法原型：**
```c
int rm_set_webserver_enabled(rm_robot_handle *handle, int state);
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 和 [rm\_version\_t](https://develop.realman-robotics.com/robot4th/apic/struct/version/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂控制句柄。 |
| `state` | 输入参数 | Web服务器使能状态(默认状态是使能)：非0代表使能，0代表禁使能。 |

- **返回值:**
	0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。
- **使用示例**
```c
int result = -1;
int enable = 0;

result = rm_set_webserver_enabled(handle, enable);
if (result == 0) {
    printf("rm_set_webserver_enabled runs successfully, result = %d, enable is %d\n", result, enable);
} else {
    printf("rm_set_webserver_enabled runs unsuccessfully, result = %d, enable is %d\n", result, enable);
}
```

## 获取Web服务器使能状态rm\_get\_webserver\_enabled

- **方法原型：**
```c
int rm_get_webserver_enabled(rm_robot_handle *handle, int *state);
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 和 [rm\_version\_t](https://develop.realman-robotics.com/robot4th/apic/struct/version/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂控制句柄。 |
| `state` | 输出参数 | 存储Web服务器当前使能状态(默认状态是使能)：非0代表使能，0代表禁使能。 |

- **返回值:**
	0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。
- **使用示例**
```c
int result = -1;
int enable = -1;

result = rm_get_webserver_enabled(handle, &enable);
if (result == 0) {
    printf("rm_get_webserver_enabled runs successfully, result = %d, enable is %d\n", result, enable);
} else {
    printf("rm_get_webserver_enabled runs unsuccessfully, result = %d, enable is %d\n", result, enable);
}
```