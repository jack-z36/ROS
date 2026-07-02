---
title: "C、C++: 全局路点列表rm_waypoint_list_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/struct/waypointList/"
author:
published: 2025-05-19
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 全局路点列表rm\_waypoint\_list\_t

## 类成员变量说明

- ### 页码 page\_num
	```
	int rm_waypoint_list_t::page_num
	```
- ### 每页大小 page\_size
	```
	int rm_waypoint_list_t::page_size
	```
- ### 列表长度 total\_size
	```
	int rm_waypoint_list_t::total_size
	```
- ### 模糊搜索 vague\_search
	```
	char rm_waypoint_list_t::vague_search[32]
	```
- ### 返回符合的全局路点列表长度 list\_len
	```
	int rm_waypoint_list_t::list_len
	```
- ### 返回符合的全局路点列表 points\_list
	```
	rm_waypoint_t rm_waypoint_list_t::points_list[100]
	```
	*可以跳转 [rm\_waypoint\_t](https://develop.realman-robotics.com/robot4th/apic/struct/waypoint/) 查阅结构体类型详细描述*