---
title: "C、C++: UDP主动上报机械臂信息结构体rm_realtime_arm_joint_state_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/struct/realtimeArmJointState/"
author:
published: 2026-01-09
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## UDP主动上报机械臂信息结构体rm\_realtime\_arm\_joint\_state\_t

## 类成员变量说明

- ### 数据解析错误码errCode
	\-3为数据解析错误，代表推送的数据不完整或格式不正确。
	```
	int rm_realtime_arm_joint_state_t::errCode
	```
- ### 推送数据的机械臂的IP地址arm\_ip
	```
	char rm_realtime_arm_joint_state_t::arm_ip[16]
	```
- ### 机械臂的端口arm\_port
	```
	int rm_realtime_arm_joint_state_t :: arm_port
	```
- ### 关节状态joint\_status
	```
	rm_joint_status_t rm_realtime_arm_joint_state_t::joint_status
	```
	*可以跳转 [rm\_joint\_status\_t](https://develop.realman-robotics.com/robot4th/apic/struct/jointStatus/) 查阅结构体详细描述。*
- ### 力数据（六维力版本支持）force\_sensor
	```
	rm_force_sensor_t rm_realtime_arm_joint_state_t::force_sensor
	```
	*可以跳转 [rm\_force\_sensor\_t](https://develop.realman-robotics.com/robot4th/apic/struct/forceSensor/) 查阅结构体详细描述。*
- ### 错误码err
	```
	rm_err_t rm_realtime_arm_joint_state_t::err
	```
	*可以跳转 [rm\_err\_t](https://develop.realman-robotics.com/robot4th/apic/struct/err/) 查阅结构体详细描述。*
- ### 当前路点信息waypoint
	```
	rm_pose_t rm_realtime_arm_joint_state_t::waypoint
	```
	*可以跳转 [rm\_pose\_t](https://develop.realman-robotics.com/robot4th/apic/struct/pose/) 查阅结构体详细描述。*
- ### 升降关节数据liftState
	```
	rm_udp_lift_state_t rm_realtime_arm_joint_state_t::liftState
	```
	*可以跳转 [rm\_udp\_lift\_state\_t](https://develop.realman-robotics.com/robot4th/apic/struct/udpLiftState/) 查阅结构体详细描述。*
- ### 扩展关节数据expandState
	```
	rm_udp_expand_state_t rm_realtime_arm_joint_state_t::expandState
	```
	*可以跳转 [rm\_udp\_expand\_state\_t](https://develop.realman-robotics.com/robot4th/apic/struct/udpExpandState/) 查阅结构体详细描述。*
- ### 灵巧手数据handState
	```
	rm_udp_hand_state_t rm_realtime_arm_joint_state_t::handState
	```
	*可以跳转 [rm\_udp\_hand\_state\_t](https://develop.realman-robotics.com/robot4th/apic/struct/udpHandState/) 查阅结构体详细描述。*
- ### 机械臂状态arm\_current\_status
	```
	rm_udp_arm_current_status_e rm_realtime_arm_joint_state_t::arm_current_status
	```
	*可以跳转 [枚举类型说明](https://develop.realman-robotics.com/robot4th/apic/type/) 查阅 `rm_udp_arm_current_status_e` 枚举详细描述。*
- ### aloha主臂状态aloha\_state
	```
	rm_udp_aloha_state_t rm_realtime_arm_joint_state_t::aloha_state
	```
	*可以跳转 [rm\_udp\_aloha\_state\_t](https://develop.realman-robotics.com/robot4th/apic/struct/udpAlohaState/) 查阅结构体详细描述。*
- ### 末端设备状态rm\_plus\_state
	0-设备在线，1-表示协议未开启，2-表示协议开启但是设备不在线
	```
	int rm_realtime_arm_joint_state_t::rm_plus_state
	```
- ### 末端设备基础信息plus\_base\_info
	```
	rm_plus_base_info_t rm_realtime_arm_joint_state_t::plus_base_info
	```
	*可以跳转 [rm\_plus\_base\_info\_t](https://develop.realman-robotics.com/robot4th/apic/struct/plusBase/) 查阅结构体详细描述。*
- ### 末端设备实时信息plus\_state\_info
	```
	rm_plus_state_info_t rm_realtime_arm_joint_state_t::plus_state_info
	```
	*可以跳转 [rm\_plus\_state\_info\_t](https://develop.realman-robotics.com/robot4th/apic/struct/plusState/) 查阅结构体详细描述。*