---
title: "C、C++: 逆解求全解参数结构体rm_inverse_kinematics_all_solve_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/struct/inverseKinematicsAllParams/"
author:
published: 2025-05-19
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 逆解求全解参数结构体rm\_inverse\_kinematics\_all\_solve\_t

## 类成员变量说明

- ### 求解结果result
	0：成功，1：逆解失败，-1：上一时刻关节角度输入为空或超关节限位，-2：目标位姿四元数不合法， -3：当前机器人非六自由度，当前仅支持六自由度机器人
	```
	int rm_inverse_kinematics_all_solve_t::result
	```
- ### 解的个数num
	```
	int rm_inverse_kinematics_all_solve_t::num
	```
- ### 参考关节角度q\_ref
	通常是当前关节角度, 单位 °
	```
	float rm_inverse_kinematics_all_solve_t::q_ref[8]
	```
- ### 关节角全解q\_solve
	单位: °
	```
	float rm_inverse_kinematics_all_solve_t::q_solve[8][8]
	```