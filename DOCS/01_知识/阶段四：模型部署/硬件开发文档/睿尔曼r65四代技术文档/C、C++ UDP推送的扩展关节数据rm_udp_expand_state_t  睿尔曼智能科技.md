---
title: "C、C++: UDP推送的扩展关节数据rm_udp_expand_state_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/struct/udpExpandState/"
author:
published: 2025-05-19
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## UDP推送的扩展关节数据rm\_udp\_expand\_state\_t

## 类成员变量说明

- ### 当前角度 pos
	精度 0.001°，单位：°
	```
	float rm_udp_expand_state_t::pos
	```
- ### 当前驱动电流 current
	单位：mA，精度：1mA
	```
	int rm_udp_expand_state_t::current
	```
- ### 驱动错误代码 err\_flag
	错误代码类型参考关节错误代码
	```
	int rm_udp_expand_state_t::err_flag
	```
- ### 当前关节使能状态 en\_flag
	1 为上使能，0 为掉使能
	```
	int rm_udp_expand_state_t::en_flag
	```
- ### 关节id号 joint\_id
	```
	int rm_udp_expand_state_t::joint_id
	```
- ### 当前升降状态 mode
	0-空闲，1-正方向速度运动，2-正方向位置运动，3-负方向速度运动，4-负方向位置运动
	```
	int rm_udp_expand_state_t::mode
	```