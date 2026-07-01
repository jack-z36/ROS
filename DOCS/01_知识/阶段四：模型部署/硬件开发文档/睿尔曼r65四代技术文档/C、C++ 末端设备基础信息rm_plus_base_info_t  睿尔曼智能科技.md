---
title: "C、C++: 末端设备基础信息rm_plus_base_info_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/struct/plusBase/"
author:
published: 2025-05-19
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 末端设备基础信息rm\_plus\_base\_info\_t

## 类成员变量说明

- ### 设备厂家manu
	```
	char rm_plus_base_info_t::manu[10]
	```
- ### 设备类型type
	1：两指夹爪，2：五指灵巧手，3：三指夹爪
	```
	int rm_plus_base_info_t::type
	```
- ### 硬件版本hv
	```
	char rm_plus_base_info_t::hv[10]
	```
- ### 软件版本sv
	```
	char rm_plus_base_info_t::sv[10]
	```
- ### boot版本bv
	```
	char rm_plus_base_info_t::bv[10]
	```
- ### 设备IDid
	```
	int rm_plus_base_info_t::id
	```
- ### 自由度dof
	```
	int rm_plus_base_info_t::dof
	```
- ### 自检开关check
	```
	int rm_plus_base_info_t::check
	```
- ### 蜂鸣器开关bee
	```
	int rm_plus_base_info_t::bee
	```
- ### 力控支持force
	```
	bool rm_plus_base_info_t::force
	```
- ### 触觉支持touch
	```
	bool rm_plus_base_info_t::touch
	```
- ### 触觉个数touch\_num
	```
	int rm_plus_base_info_t::touch_num
	```
- ### 触觉开关touch\_sw
	```
	int rm_plus_base_info_t::touch_sw
	```
- ### 手方向hand
	1 ：左手，2： 右手
	```
	int rm_plus_base_info_t::hand
	```
- ### 位置上限pos\_up
	单位：无量纲
	```
	int rm_plus_base_info_t::pos_up[12]
	```
- ### 位置下限pos\_low
	单位：无量纲
	```
	int rm_plus_base_info_t::pos_low[12]
	```
- ### 角度上限angle\_up
	单位：0.01度
	```
	int rm_plus_base_info_t::angle_up[12]
	```
- ### 角度下限angle\_low
	单位：0.01度
	```
	int rm_plus_base_info_t::angle_low[12]
	```
- ### 速度上限speed\_up
	单位：无量纲
	```
	int rm_plus_base_info_t::speed_up[12]
	```
- ### 速度下限speed\_low
	单位：无量纲
	```
	int rm_plus_base_info_t::speed_low[12]
	```
- ### 力上限force\_up
	单位：0.001N
	```
	int rm_plus_base_info_t::force_up[12]
	```
- ### 力下限force\_low
	单位：0.001N
	```
	int rm_plus_base_info_t::force_low[12]
	```