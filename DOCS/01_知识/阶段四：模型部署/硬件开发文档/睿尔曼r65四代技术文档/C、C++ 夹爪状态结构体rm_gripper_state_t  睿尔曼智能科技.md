---
title: "C、C++: 夹爪状态结构体rm_gripper_state_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/struct/gripperState/"
author:
published: 2025-05-19
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 夹爪状态结构体rm\_gripper\_state\_t

## 类成员变量说明

- ### 夹爪使能标志enable\_state
	0 表示未使能，1 表示使能。
	```
	int rm_gripper_state_t::enable_state
	```
- ### 夹爪在线状态status
	0 表示离线， 1表示在线。
	```
	int rm_gripper_state_t::status
	```
- ### 夹爪错误信息error
	低8位表示夹爪内部的错误信息bit5-7；保留bit4；内部通bit3；驱动器bit2；过流 bit1；过温bit0；堵转；
	```
	int rm_gripper_state_t::error
	```
- ### 夹爪当前的压力，单位gcurrent\_force
	```
	int rm_gripper_state_t::current_force
	```
- ### 当前温度，单位℃temperature
	```
	int rm_gripper_state_t::temperature
	```
- ### 夹爪开口度actpos
	```
	int rm_gripper_state_t::actpos
	```