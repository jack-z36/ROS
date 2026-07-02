---
title: "C、C++: 数字IO配置结构体rm_io_config_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/struct/ioConfig/"
author:
published: 2025-05-19
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 数字IO配置结构体rm\_io\_config\_t

## 类成员变量说明

- ### 数字io模式0~14io\_mode
	0-通用输入模式
	1-通用输出模式
	2-输入开始功能复用模式
	3-输入暂停功能复用模式
	4-输入继续功能复用模式
	5-输入急停功能复用模式
	6-输入进入电流环拖动复用模式
	7-输入进入力只动位置拖动模式（六维力版本可配置）
	8-输入进入力只动姿态拖动模式（六维力版本可配置）
	9-输入进入力位姿结合拖动复用模式（六维力版本可配置）
	10-输入外部轴最大软限位复用模式（外部轴模式可配置）
	11-输入外部轴最小软限位复用模式（外部轴模式可配置）
	12-输入初始位姿功能复用模式
	13-输出碰撞功能复用模式
	14-实时调速功能复用模式。
	```
	int rm_io_config_t::io_mode
	```
- ### 实时调速功能复用配置项io\_real\_time\_config\_t
	当io模式为14时生效。
	```
	struct
	{
	    int speed;  // speed:速度取值范围0-100
	    int mode;   // mode :模式取值范围1或2
	}io_real_time_config_t;
	```