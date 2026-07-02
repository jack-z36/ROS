---
title: "C、C++: 升降机构、扩展关节状态结构体rm_expand_state_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/struct/expandState/"
author:
published: 2025-05-19
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 升降机构、扩展关节状态结构体rm\_expand\_state\_t

## 类成员变量说明

- ### 扩展关节角度pos
	单位度，精度 0.001°(若为升降机构高度，则单位：mm，精度：1mm，范围：0 ~2300)。
	```
	int rm_expand_state_t::pos
	```
- ### 驱动电流current
	单位：mA，精度：1mA。
	```
	int rm_expand_state_t::current
	```
- ### 驱动错误代码err\_flag
	错误代码类型参考关节错误代码。
	```
	int rm_expand_state_t::err_flag
	```
- ### 当前状态mode
	0-空闲，1-正方向速度运动，2-正方向位置运动，3-负方向速度运动，4-负方向位置运动。
	```
	int rm_expand_state_t::mode
	```