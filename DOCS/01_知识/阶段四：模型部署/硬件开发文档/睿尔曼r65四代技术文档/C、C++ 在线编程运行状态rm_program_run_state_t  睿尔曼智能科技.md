---
title: "C、C++: 在线编程运行状态rm_program_run_state_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/struct/programRunState/"
author:
published: 2025-06-10
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 在线编程运行状态rm\_program\_run\_state\_t

## 类成员变量说明

- ### 运行状态run\_state
	0 未开始 1运行中 2暂停中。
	```
	int rm_program_run_state_t::run_state
	```
- ### 运行轨迹编号id
	```
	int rm_program_run_state_t::id
	```
- ### 上次编辑的在线编程编号 idedit\_id
	```
	int rm_program_run_state_t::edit_id
	```
- ### 运行行数plan\_num
	```
	int rm_program_run_state_t::plan_num
	```
- ### 循环指令数量total\_loop
	```
	int rm_program_run_state_t::total_loop
	```
- ### 单步模式step\_mode
	1 为单步模式，0 为非单步模式。
	```
	int rm_program_run_state_t::step_mode
	```
- ### 全局规划速度比例plan\_speed
	比例值1-100。
	```
	int rm_program_run_state_t::plan_speed
	```
- ### 循环行数loop\_num
	比例值1-100。
	```
	int rm_program_run_state_t::loop_num[100]
	```
- ### 对应循环次数loop\_cont
	比例值1-100。
	```
	int rm_program_run_state_t::loop_cont[100]
	```