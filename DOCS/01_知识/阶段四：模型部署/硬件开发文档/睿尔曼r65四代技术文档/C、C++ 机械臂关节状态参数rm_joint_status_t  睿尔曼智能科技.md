---
title: "C、C++: 机械臂关节状态参数rm_joint_status_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/struct/jointStatus/"
author:
published: 2025-05-19
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 机械臂关节状态参数rm\_joint\_status\_t

## 类成员变量说明

- ### 关节电流joint\_current
	单位mA，精度：0.001mA。
	```
	float rm_joint_status_t::joint_current[ARM_DOF]
	```
- ### 当前关节使能状态joint\_en\_flag
	1为上使能，0为掉使能。
	```
	bool rm_joint_status_t::joint_en_flag[ARM_DOF]
	```
- ### 当前关节错误码joint\_err\_code
	```
	uint16_t rm_joint_status_t::joint_err_code[ARM_DOF]
	```
- ### 关节角度joint\_position
	单位°，精度：0.001°。
	```
	float rm_joint_status_t::joint_position[ARM_DOF]
	```
- ### 当前关节温度joint\_temperature
	精度0.001℃。
	```
	float rm_joint_status_t::joint_temperature[ARM_DOF]
	```
- ### 当前关节电压joint\_voltage
	精度0.001V。
	```
	float rm_joint_status_t::joint_voltage[ARM_DOF]
	```
- ### 当前关节速度joint\_speed
	精度0.01RPM。
	```
	float rm_joint_status_t::joint_speed[ARM_DOF]
	```