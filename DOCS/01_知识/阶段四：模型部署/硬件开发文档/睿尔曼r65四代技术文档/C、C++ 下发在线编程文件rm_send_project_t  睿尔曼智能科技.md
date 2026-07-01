---
title: "C、C++: 下发在线编程文件rm_send_project_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/struct/sendProject/"
author:
published: 2025-12-17
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 下发在线编程文件rm\_send\_project\_t

## 类成员变量说明

- ### 下发文件路径文件名project\_path
	```
	char rm_send_project_t::project_path[300]
	```
- ### 名称长度project\_path\_len
	```
	int rm_send_project_t::project_path_len
	```
- ### 规划速度比例系数plan\_speed
	```
	int rm_send_project_t::plan_speed
	```
- ### 0-运行文件，1-仅保存文件，不运行only\_save
	```
	int rm_send_project_t::only_save
	```
- ### 保存到控制器中的编号save\_id
	```
	int rm_send_project_t::save_id
	```
- ### 设置单步运行方式模式，1-设置单步模式 0-设置正常运动模式step\_flag
	```
	int rm_send_project_t::step_flag
	```
- ### 下发文件类型。0-在线编程文件，1-拖动示教轨迹文件project\_type
	```
	int rm_send_project_t::project_type
	```