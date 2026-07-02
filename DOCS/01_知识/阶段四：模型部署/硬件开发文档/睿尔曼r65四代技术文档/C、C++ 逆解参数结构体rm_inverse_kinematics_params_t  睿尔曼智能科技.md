---
title: "C、C++: 逆解参数结构体rm_inverse_kinematics_params_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/struct/inverseKinematicsParams/"
author:
published: 2025-05-19
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 逆解参数结构体rm\_inverse\_kinematics\_params\_t

## 类成员变量说明

- ### 上一时刻关节角度q\_in
	单位°。
	```
	float rm_inverse_kinematics_params_t::q_in[ARM_DOF]
	```
- ### 目标位姿q\_pose
	```
	rm_pose_t rm_inverse_kinematics_params_t::q_pose
	```
	*可以跳转 [rm\_pose\_t](https://develop.realman-robotics.com/robot4th/apic/struct/pose/) 查阅结构体详细描述。*
- ### 姿态参数类别flag
	0-四元数；1-欧拉角。
	```
	uint8_t rm_inverse_kinematics_params_t::flag
	```