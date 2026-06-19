---
title: "Python: 机械臂实时状态推送信息结构体rm_realtime_arm_joint_state_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/realtimeArmJointState/"
author:
published: 2026-01-09
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 机械臂实时状态推送信息结构体rm\_realtime\_arm\_joint\_state\_t

## 属性

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `errCode` | `int` | 数据解析错误码，-3为数据解析错误，代表推送的数据不完整或格式不正确 |
| `arm_ip` | `bytes` | 推送数据的机械臂的IP地址 |
| `arm_port` | `int` | 机械臂的端口 |
| `joint_status` | [rm\_joint\_status\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/jointStatus/) | 机械臂关节状态结构体 |
| `force_sensor` | [rm\_force\_sensor\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/forceSensor/) | 力传感器数据结构体 |
| `err` | [rm\_err\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/err/) | 错误码 |
| `waypoint` | [rm\_pose\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/pose/) | 当前位置姿态结构体 |
| `liftState` | [rm\_udp\_lift\_state\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/udpLiftState/) | 升降关节数据 |
| `expandState` | [rm\_udp\_expand\_state\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/udpExpandState/) | 扩展关节数据 |
| `handState` | [rm\_udp\_hand\_state\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/udpHandState/) | 灵巧手数据 |
| `arm_current_status` | [rm\_udp\_arm\_current\_status\_e](https://develop.realman-robotics.com/robot4th/apipython/type/) | 机械臂当前状态 |
| `aloha_state` | [rm\_udp\_aloha\_state\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/udpAlohaState/) | aloha主臂状态 |
| `rm_plus_state` | `int` | 末端设备状态，0-设备在线，1-表示协议未开启，2-表示协议开启但是设备不在线 |
| `plus_base_info` | [rm\_plus\_base\_info\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/rmPlusBaseInfo/) | 末端设备基础信息 |
| `plus_state_info` | [rm\_plus\_state\_info\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/rmPlusStateInfo/) | 末端设备实时信息 |

## 成员函数

```python
rm_realtime_arm_joint_state_t.to_dict(self,recurse = True)
```

将结构体转换为字典。