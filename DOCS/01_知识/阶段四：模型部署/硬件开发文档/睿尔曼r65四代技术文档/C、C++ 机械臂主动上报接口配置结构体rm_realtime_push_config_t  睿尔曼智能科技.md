---
title: "C、C++: 机械臂主动上报接口配置结构体rm_realtime_push_config_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/struct/realtimePushConfig/"
author:
published: 2025-12-17
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 机械臂主动上报接口配置结构体rm\_realtime\_push\_config\_t

## 类成员变量说明

- ### 广播周期，5ms的倍数cycle
	```
	int rm_realtime_push_config_t::cycle
	```
- ### 使能，是否主动上报enable
	```
	bool rm_realtime_push_config_t::enable
	```
- ### 广播的端口号port
	```
	int rm_realtime_push_config_t::port
	```
- ### 系统外受力数据的坐标系force\_coordinate
	0为传感器坐标系 1为当前工作坐标系 2为当前工具坐标系（力传感器版本支持）
	```
	int rm_realtime_push_config_t::force_coordinate
	```
- ### 自定义的上报目标IP地址ip
	```
	char rm_realtime_push_config_t::ip[28]
	```
- ### 自定义上报项custom\_config
	```
	rm_udp_custom_config_t rm_realtime_push_config_t::custom_config
	```
	*可以跳转 [rm\_udp\_custom\_config\_t](https://develop.realman-robotics.com/robot4th/apic/struct/udpCustomConfig/) 查阅结构体详细描述。*