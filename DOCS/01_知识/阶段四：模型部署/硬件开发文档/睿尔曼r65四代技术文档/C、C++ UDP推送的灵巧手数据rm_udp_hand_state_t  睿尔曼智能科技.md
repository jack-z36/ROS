---
title: "C、C++: UDP推送的灵巧手数据rm_udp_hand_state_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/struct/udpHandState/"
author:
published: 2025-05-19
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## UDP推送的灵巧手数据rm\_udp\_hand\_state\_t

## 类成员变量说明

- ### 灵巧手位置 hand\_pos
	表示灵巧手位置
	```
	int rm_udp_hand_state_t::hand_pos[6]
	```
- ### 灵巧手角度 hand\_angle
	表示灵巧手角度
	```
	int rm_udp_hand_state_t::hand_angle[6]
	```
- ### 灵巧手自由度力 hand\_force
	表示灵巧手自由度力，单位mN
	```
	int rm_udp_hand_state_t::hand_force[6]
	```
- ### 灵巧手自由度状态 hand\_state
	表示灵巧手自由度状态，由灵巧手厂商定义状态含义
	```
	int rm_udp_hand_state_t::hand_state[6]
	```
- ### 灵巧手系统错误 hand\_err
	表示灵巧手系统错误，由灵巧手厂商定义错误含义，例如因时状态码如下：1表示有错误，0表示无错误
	```
	int rm_udp_hand_state_t::hand_err
	```