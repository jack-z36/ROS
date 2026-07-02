---
title: "C、C++: UDP数据自定义上报项配置rm_udp_custom_config_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/struct/udpCustomConfig/"
author:
published: 2025-05-19
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## UDP数据自定义上报项配置rm\_udp\_custom\_config\_t

## 类成员变量说明

- ### 关节速度 joint\_speed
	关节速度。1：上报；0：关闭上报；-1：不设置，保持之前的状态
	```
	int rm_udp_custom_config_t::joint_speed
	```
- ### 升降关节信息 lift\_state
	升降关节信息。1：上报；0：关闭上报；-1：不设置，保持之前的状态
	```
	int rm_udp_custom_config_t::lift_state
	```
- ### 扩展关节信息 expand\_state
	扩展关节信息（升降关节和扩展关节为二选一，优先显示升降关节）1：上报；0：关闭上报；-1：不设置，保持之前的状态
	```
	int rm_udp_custom_config_t::expand_state
	```
- ### 机械臂状态 arm\_current\_status
	机械臂当前状态。1：上报；0：关闭上报；-1：不设置，保持之前的状态
	```
	int rm_udp_custom_config_t::arm_current_status
	```
- ### 灵巧手状态 hand\_state
	灵巧手状态。1：上报；0：关闭上报；-1：不设置，保持之前的状态
	```
	int rm_udp_custom_config_t::hand_state
	```
- ### aloha主臂状态 aloha\_state
	aloha主臂状态。1：上报；0：关闭上报；-1：不设置，保持之前的状态
	```
	int rm_udp_custom_config_t::aloha_state
	```
- ### 末端设备基础信息 plus\_base
	末端设备基础信息。1：上报；0：关闭上报；-1：不设置，保持之前的状态
	```
	int rm_udp_custom_config_t::plus_base
	```
- ### 末端设备实时信息 plus\_state
	末端设备实时信息。1：上报；0：关闭上报；-1：不设置，保持之前的状态
	```
	int rm_udp_custom_config_t::plus_state
	```