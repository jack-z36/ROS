---
title: "C、C++: 流程图程序运行状态rm_flowchart_run_state_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/struct/flowchartstate/"
author:
published: 2025-06-10
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 流程图程序运行状态rm\_flowchart\_run\_state\_t

## 类成员变量说明

- ### 运行状态run\_state
	0未开始，1运行中，2暂停中。
	```
	int rm_flowchart_run_state_t::run_state
	```
- ### 当前使能的文件idid
	```
	int rm_flowchart_run_state_t::id
	```
- ### 当前使能的文件名称name
	```
	char rm_flowchart_run_state_t::name
	```
- ### 当前使能的文件全局规划速度比例plan\_speed
	取值范围1-100。
	```
	int rm_flowchart_run_state_t::plan_speed
	```
- ### 单步模式step\_mode
	0为空，1为正常，2为单步。
	```
	int rm_flowchart_run_state_t::step_mode
	```
- ### 运行到的流程图块的idmodal\_id
	未运行则不返回。
	```
	char rm_flowchart_run_state_t::modal_id[50]
	```