---
title: "C、C++: 全局路点存储信息rm_waypoint_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/struct/waypoint/"
author:
published: 2025-05-19
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 全局路点存储信息rm\_waypoint\_t

## 类成员变量说明

- ### 路点名称 point\_name
	```
	char rm_waypoint_t::point_name[20]
	```
- ### 关节角度 joint
	```
	float rm_waypoint_t::joint[ARM_DOF]
	```
- ### 位姿信息 pose
	```
	rm_pose_t rm_waypoint_t::pose
	```
	*可以跳转 [rm\_pose\_t](https://develop.realman-robotics.com/robot4th/apic/struct/pose/) 查阅结构体类型详细描述*
- ### 工作坐标系名称 work\_frame
	```
	char rm_waypoint_t::work_frame[12]
	```
- ### 工具坐标系名称 tool\_frame
	```
	char rm_waypoint_t::tool_frame[12]
	```
- ### 路点新增或修改时间 time
	```
	char rm_waypoint_t::time[50]
	```