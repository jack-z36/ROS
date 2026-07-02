---
title: "C、C++: 末端设备实时信息(末端生态协议支持)rm_plus_state_info_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/struct/plusState/"
author:
published: 2025-05-19
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 末端设备实时信息(末端生态协议支持)rm\_plus\_state\_info\_t

## 类成员变量说明

- ### 系统状态sys\_state
	0:正常 1:设备故障
	```
	int rm_plus_state_info_t::sys_state
	```
- ### 各自由度当前状态dof\_state
	0：正在松开 1：正在闭合 2：位置到位停止 3：力控到位停止 4：触觉到位停止 5：电流保护停止 6：发生故障
	```
	int rm_plus_state_info_t::dof_state[12]
	```
- ### 各自由度错误信息dof\_err
	0：正常 1：FOC错误 2：过压 3：欠压 4：过温 5：启动错误 6：编码器错误 7：过流 8：软件错误 9：传感器错误 10：位置超限位 11：DRV8320错误 12：位置跟踪误差 13：电流检测错误 14：自检错误 15：位置指令超限 16：多圈丢数
	```
	int rm_plus_state_info_t::dof_err[12]
	```
- ### 各自由度当前位置pos
	单位：无量纲
	```
	int rm_plus_state_info_t::pos[12]
	```
- ### 各自由度当前速度speed
	闭合正，松开负，单位：无量纲
	```
	int rm_plus_state_info_t::speed[12]
	```
- ### 各自由度当前角度angle
	单位：0.01度
	```
	int rm_plus_state_info_t::angle[12]
	```
- ### 各自由度当前电流current
	单位：mA
	```
	int rm_plus_state_info_t::current[12]
	```
- ### 自由度触觉三维力的法向力normal\_force
	```
	int rm_plus_state_info_t::normal_force[18]
	```
- ### 自由度触觉三维力的切向力tangential\_force
	```
	int rm_plus_state_info_t::tangential_force[18]
	```
- ### 自由度触觉三维力的切向力方向tangential\_force\_dir
	```
	int rm_plus_state_info_t::tangential_force_dir[18]
	```
- ### 自由度触觉自接近tsa
	```
	uint32_t rm_plus_state_info_t::tsa[12]
	```
- ### 自由度触觉互接近tma
	```
	uint32_t rm_plus_state_info_t::tma[12]
	```
- ### 触觉传感器原始数据touch\_data
	```
	int rm_plus_state_info_t::touch_data[18]
	```
- ### 自由度力矩force
	闭合正，松开负，单位0.001N
	```
	int rm_plus_state_info_t::force[12]
	```