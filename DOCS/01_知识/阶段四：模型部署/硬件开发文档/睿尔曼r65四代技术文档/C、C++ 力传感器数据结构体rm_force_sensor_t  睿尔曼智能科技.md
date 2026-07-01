---
title: "C、C++: 力传感器数据结构体rm_force_sensor_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/struct/forceSensor/"
author:
published: 2025-05-19
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 力传感器数据结构体rm\_force\_sensor\_t

UDP主动上报机械臂信息。

## 类成员变量说明

- ### 当前力传感器原始数据force
	0.001N或0.001Nm。
	```
	float rm_force_sensor_t::force[6]
	```
- ### 当前力传感器系统外受力数据zero\_force
	0.001N或0.001Nm。
	```
	float rm_force_sensor_t::zero_force[6]
	```
- ### 当前力传感器系统外受力数据coordinate
	0.001N或0.001Nm。
	```
	int rm_force_sensor_t::coordinate
	```