---
title: "C、C++: 机械臂所有状态参数结构体rm_arm_all_state_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/struct/allState/"
author:
published: 2025-05-19
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 机械臂所有状态参数结构体rm\_arm\_all\_state\_t

## 类成员变量说明

- ### 关节电流joint\_current
	单位mA。
	```
	float rm_arm_all_state_t::joint_current[ARM_DOF]
	```
- ### 关节使能状态joint\_en\_flag
	```
	int rm_arm_all_state_t::joint_en_flag[ARM_DOF]
	```
- ### 关节温度joint\_temperature
	单位℃。
	```
	float rm_arm_all_state_t::joint_temperature[ARM_DOF]
	```
- ### 关节电压joint\_voltage
	单位V。
	```
	float rm_arm_all_state_t::joint_voltage[ARM_DOF]
	```
- ### 关节错误码joint\_err\_code
	```
	int rm_arm_all_state_t::joint_err_code[ARM_DOF]
	```
- ### 机械臂错误代码err
	```
	rm_err_t rm_arm_all_state_t::err
	```
	*可以跳转 [rm\_err\_t](https://develop.realman-robotics.com/robot4th/apic/struct/err/) 查阅结构体详细描述。*