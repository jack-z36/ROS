---
title: "C、C++: 坐标系结构体rm_frame_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/struct/frame/"
author:
published: 2025-06-30
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 坐标系结构体rm\_frame\_t

## 类成员变量说明

- ### 坐标系名称frame\_name
	```
	char rm_frame_t::frame_name[12]
	```
- ### 坐标系位姿pose
	```
	rm_pose_t rm_frame_t::pose
	```
	*可以跳转 [rm\_pose\_t](https://develop.realman-robotics.com/robot4th/apic/struct/pose/) 查阅结构体详细描述。*
- ### 坐标系末端负载重量，单位：kgpayload
	```
	float rm_frame_t::payload
	```
- ### 坐标系末端负载质心位置，单位：mmx
	```
	float rm_frame_t::x
	```
- ### 坐标系末端负载质心位置，单位：mmy
	```
	float rm_frame_t::y
	```
- ### 坐标系末端负载质心位置，单位：mmz
	```
	float rm_frame_t::z
	```