---
title: "C、C++: 五指灵巧手配置handControl | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/classes/handControl/"
author:
published: 2026-04-22
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 五指灵巧手配置handControl

睿尔曼机械臂末端配置因时的五指灵巧手，可通过本接口对灵巧手进行设置，包含手势动作、动作角度、速度、力控范围等。

## 运行灵巧手目标手势序列号rm\_set\_hand\_posture()

- **方法原型：**
```c
int rm_set_hand_posture(rm_robot_handle * handle,int posture_num,bool block,int timeout)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `posture_num` | 输入参数 | 预先保存在灵巧手内的手势序号，范围：1~40。 |
| `block` | 输入参数 | `true` 表示阻塞模式，等待灵巧手运动结束后返回； `false` 表示非阻塞模式，发送后立即返回。 |
| `timeout` | 输入参数 | 阻塞模式下超时时间设置，单位：秒。 |

- **返回值:**

| 参数 | 类型 | 说明 | 处理建议 |
| --- | --- | --- | --- |
| 0 | `int` | 成功。 | \- |
| 1 | `int` | 控制器返回false，传递参数错误或机械臂状态发生错误。 | \- **校验JSON指令** ：   ①启用API的DEBUG日志，捕获原始JSON数据。   ②检查JSON语法：确保括号、引号、逗号等格式正确（可借助JSON校验工具）。   ③对照API文档，验证参数名称、数据类型及取值范围是否符合规范。   ④修正问题后重新发送指令，检查控制器返回的状态码及业务数据是否正常。   \- **检查机械臂状态** ： ①查看机械臂控制器或日志中的实时报错信息（如硬件故障、超限等），根据提示复位、校准或排查硬件问题。   ②修正问题后重新发送指令，检查控制器返回的状态码及业务数据是否正常。 |
| \-1 | `int` | 数据发送失败，通信过程中出现问题。 | **检查网络连通性** ：   使用ping/telnet等工具检测与控制器的通信链路是否正常。 |
| \-2 | `int` | 数据接收失败，通信过程中出现问题或者控制器超时没有返回。 | \- **检查网络连通性** ：   使用ping/telnet等工具检测与控制器的通信链路是否正常。   \- **校验版本兼容性** ：   ①核对控制器固件版本是否支持当前API功能，具体版本配套关系请参考 [版本变更说明](https://develop.realman-robotics.com/robot4th/releaseNotes/releaseNotesfour/) 。   ②若版本过低需升级控制器或使用适配的API版本。 |
| \-3 | `int` | 返回值解析失败，接收到的数据格式不正确或不完整。 | **校验版本兼容性** ：   ①核对控制器固件版本是否支持当前API功能，具体版本配套关系请参考 [版本变更说明](https://develop.realman-robotics.com/robot4th/releaseNotes/releaseNotesfour/) 。   ②若版本过低需升级控制器或使用适配的API版本。 |
| \-4 | `int` | 当前到位设备校验失败，即当前到位设备不为夹爪。 | \- **检测多设备并发控制** ：检查是否有其他设备给机械臂发送运动指令：包括机械臂、夹爪、灵巧手、升降机的运动；   \- **实时监听指令事件** ：注册回调函数 `rm_get_arm_event_call_back` ：   ①捕获设备到位事件（如运动完成、超时等）；   ②通过回调参数 device 判断触发事件的具体设备类型。 |
| \-5 | `int` | 超时未返回。 | \- **检查超时时长设置** ：阻塞模式下，支持配置等待设备运动完成的超时时间，务必确保设置超时时间大于设备运动时间；   \- **检查网络连通性** ：   使用ping/telnet等工具检测与控制器的通信链路是否正常。 |

- **使用示例**
```c
//设置灵巧手阻塞执行1号手势，10秒无返回则超时
int posture_num = 1;
ret = rm_set_hand_posture(robot_handle,posture_num,true,10);
```

## 运行灵巧手动作序列号rm\_set\_hand\_seq()

- **方法原型：**
```c
int rm_set_hand_seq(rm_robot_handle * handle,int seq_num,bool block,int timeout)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `seq_num` | 输入参数 | 预先保存在灵巧手内的动作序号，范围：1~40。 |
| `block` | 输入参数 | `true` 表示阻塞模式，等待灵巧手运动结束后返回；   `false` 表示非阻塞模式，发送后立即返回。 |
| `timeout` | 输入参数 | 阻塞模式下超时时间设置，单位：秒。 |

- **返回值:**

| 参数 | 类型 | 说明 | 处理建议 |
| --- | --- | --- | --- |
| 0 | `int` | 成功。 | \- |
| 1 | `int` | 控制器返回false，传递参数错误或机械臂状态发生错误。 | \- **校验JSON指令** ：   ①启用API的DEBUG日志，捕获原始JSON数据。   ②检查JSON语法：确保括号、引号、逗号等格式正确（可借助JSON校验工具）。   ③对照API文档，验证参数名称、数据类型及取值范围是否符合规范。   ④修正问题后重新发送指令，检查控制器返回的状态码及业务数据是否正常。   \- **检查机械臂状态** ： ①查看机械臂控制器或日志中的实时报错信息（如硬件故障、超限等），根据提示复位、校准或排查硬件问题。   ②修正问题后重新发送指令，检查控制器返回的状态码及业务数据是否正常。 |
| \-1 | `int` | 数据发送失败，通信过程中出现问题。 | **检查网络连通性** ：   使用ping/telnet等工具检测与控制器的通信链路是否正常。 |
| \-2 | `int` | 数据接收失败，通信过程中出现问题或者控制器超时没有返回。 | \- **检查网络连通性** ：   使用ping/telnet等工具检测与控制器的通信链路是否正常。   \- **校验版本兼容性** ：   ①核对控制器固件版本是否支持当前API功能，具体版本配套关系请参考 [版本变更说明](https://develop.realman-robotics.com/robot4th/releaseNotes/releaseNotesfour/) 。   ②若版本过低需升级控制器或使用适配的API版本。 |
| \-3 | `int` | 返回值解析失败，接收到的数据格式不正确或不完整。 | **校验版本兼容性** ：   ①核对控制器固件版本是否支持当前API功能，具体版本配套关系请参考 [版本变更说明](https://develop.realman-robotics.com/robot4th/releaseNotes/releaseNotesfour/) 。   ②若版本过低需升级控制器或使用适配的API版本。 |
| \-4 | `int` | 当前到位设备校验失败，即当前到位设备不为夹爪。 | \- **检测多设备并发控制** ：检查是否有其他设备给机械臂发送运动指令：包括机械臂、夹爪、灵巧手、升降机的运动；   \- **实时监听指令事件** ：注册回调函数 `rm_get_arm_event_call_back` ：   ①捕获设备到位事件（如运动完成、超时等）；   ②通过回调参数 device 判断触发事件的具体设备类型。 |
| \-5 | `int` | 超时未返回。 | \- **检查超时时长设置** ：阻塞模式下，支持配置等待设备运动完成的超时时间，务必确保设置超时时间大于设备运动时间；   \- **检查网络连通性** ：   使用ping/telnet等工具检测与控制器的通信链路是否正常。 |

- **使用示例**
```c
//设置灵巧手阻塞执行1号动作序列，15秒无返回则超时
int posture_num = 1;
ret = rm_set_hand_seq(robot_handle,posture_num,true,15);
```

## 设置灵巧手各自由度角度rm\_set\_hand\_angle()

设置灵巧手角度，灵巧手：6个主动自由度，自由度1（大拇指弯曲）、自由度2（食指）、自由度3（中指）、自由度4（无名指）、自由度5（小指）、自由度6（大拇指旋转），大拇指旋转。

- **方法原型：**
```c
int rm_set_hand_angle(rm_robot_handle * handle,const int * hand_angle, bool block, int timeout)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `hand_angle` | 输入参数 | 预手指角度数组，范围：0~1000.   另外，-1代表该自由度不执行任何操作，保持当前状态。 |
| `block` | 输入参数 | `true` ：表示非阻塞模式，发送成功后返回， `false` ：表示阻塞模式，接收设置成功指令后返回。 |
| `timeout` | 输入参数 | 阻塞模式下超时时间设置，单位：秒。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
//设置灵巧手各手指动作
int ret;
int hand_angle[6] = {-1,100,200,300,400,500};
bool block = true;
int timeout = 1;
ret = rm_set_hand_angle(handle, hand_angle, block, timeout);
```

## 设置灵巧手速度rm\_set\_hand\_speed()

- **方法原型：**
```c
int rm_set_hand_speed(rm_robot_handle * handle,int speed)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `speed` | 输入参数 | 手指速度，范围：1~1000。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
//设置灵巧手各手指速度
int speed = 500;
ret = rm_set_hand_speed(robot_handle,speed);
```

## 设置灵巧手力阈值rm\_set\_hand\_force()

- **方法原型：**
```c
int rm_set_hand_force(rm_robot_handle * handle,int hand_force)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `hand_force` | 输入参数 | 手指力，范围：1~1000。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
//设置灵巧手力阈值500
int force = 500;
ret = rm_set_hand_force(robot_handle,force);
```

## 设置灵巧手角度跟随控制 rm\_set\_hand\_follow\_angle()

- 设置灵巧手跟随角度，灵巧手：6个主动自由度，自由度1（大拇指弯曲）、自由度2（食指）、自由度3（中指）、自由度4（无名指）、自由度5（小指）、自由度6（大拇指旋转），最高50Hz的控制频率。
- 灵巧手角度的定义（int16）：
	1. 傲意：第一指关节1的角度\*100。
		2. 因时：0-1000，通过联系技术支持得到驱动器行程与角度关系表。

注意

如果要使用此功能，需要联系技术支持发送定制的灵巧手固件升级包（傲意或者因时）。

- **方法原型：**
```c
int rm_set_hand_follow_angle(rm_robot_handle *handle, const int *hand_angle, bool block);
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `hand_angle` | 输入参数 | 设置灵巧手各手指动作，hand\_angle表示手指角度数组，按照灵巧手厂商定义的角度做控制，例如：   1\. 因时的角度范围为0到+1000；   2\. 傲意的角度范围为-32768到+32767。 |
| `block` | 输入参数 | `true` ：表示非阻塞模式，发送成功后返回， `false` ：表示阻塞模式，接收设置成功指令后返回。 |

- **因时各自由度的角度定义和运动范围说明如下。**

| 角度 | 图例说明 | 范围 |
| --- | --- | --- |
| 小拇指   无名指   中指   食指 | ![image6](https://develop.realman-robotics.com/realman/docs/attachments/multimedia/zh/robot4th/apic/classes/handControl/image6.png) | 19°~176.7° |
| 大拇指弯曲角度 | ![image7](https://develop.realman-robotics.com/realman/docs/attachments/multimedia/zh/robot4th/apic/classes/handControl/image7.png) | \-130~53.6° |
| 大拇旋转曲角度 | ![image8](https://develop.realman-robotics.com/realman/docs/attachments/multimedia/zh/robot4th/apic/classes/handControl/image8.png) | 90°~165° |

- **傲意各自由度的角度定义和运动范围说明如下。**

| 角度 | 图例说明 | 范围 |
| --- | --- | --- |
| 食指   中指   无名指   小拇指 | ![image9](https://develop.realman-robotics.com/realman/docs/attachments/multimedia/zh/robot4th/apic/classes/handControl/image9.png) | 100.22°~178.37°   97.81° ~ 176.06°   101.38°~176.54°   98.84°~174.86° |
| 大拇指弯曲角度 | ![image10](https://develop.realman-robotics.com/realman/docs/attachments/multimedia/zh/robot4th/apic/classes/handControl/image10.png) | 2.26° ~ 36.76° |
| 大拇旋转曲角度 | ![image11](https://develop.realman-robotics.com/realman/docs/attachments/multimedia/zh/robot4th/apic/classes/handControl/image11.png) | 0° ~ 90° |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
// 高速控制灵巧手，非阻塞模式
const int angle[6]= {0,100,200,300,400,500};
bool block = true;
ret = rm_set_hand_follow_angle(robot_handle,angle,block);
```

## 设置灵巧手位置跟随控制rm\_set\_hand\_follow\_pos()

设置灵巧手跟随位置，灵巧手：6个主动自由度，自由度1（大拇指弯曲）、自由度2（食指）、自由度3（中指）、自由度4（无名指）、自由度5（小指）、自由度6（大拇指旋转），最高50Hz的控制频率。

注意

如果要使用此功能，需要联系技术支持发送定制的灵巧手固件升级包（傲意或者因时）。

- **方法原型：**
```c
int rm_set_hand_follow_pos(rm_robot_handle *handle, const int *hand_pos, bool block);
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `hand_pos` | 输入参数 | 设置灵巧手各手指动作，hand\_pos表示手指位置数组，按照灵巧手厂商定义的角度做控制，例如：   1\. 因时的位置范围为0-2000；   2\. 傲意的位置范围为0-65535。 |
| `block` | 输入参数 | `true` ：表示非阻塞模式，发送成功后返回， `false` ：表示阻塞模式，接收设置成功指令后返回。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
// 高速控制灵巧手，非阻塞模式
const int pos[6]= {0,100,200,300,400,500};
bool block = true;
ret = rm_set_hand_follow_pos(robot_handle,pos,block);
```
