---
title: "C、C++: 六维力传感器数据结构体rm_force_data_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/struct/forceData/"
author:
published: 2025-05-19
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 六维力传感器数据结构体rm\_force\_data\_t

## 类成员变量说明

- ### 当前力传感器原始数据force\_data
	力的单位为N；力矩单位为Nm。
	```
	float rm_force_data_t::force_data[6]
	```
- ### 当前力传感器系统外受力数据zero\_force\_data
	力的单位为N；力矩单位为Nm。
	```
	float rm_force_data_t::zero_force_data[6]
	```
- ### 当前工作坐标系下系统外受力原始数据work\_zero\_force\_data
	力的单位为N；力矩单位为Nm。
	```
	float rm_force_data_t::work_zero_force_data[6]
	```
- ### 当前工具坐标系下系统外受力原始数据tool\_zero\_force\_data
	力的单位为N；力矩单位为Nm。
	```
	float rm_force_data_t::tool_zero_force_data[6]
	```