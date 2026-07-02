---
title: "C、C++: 外设数据读写参数结构体rm_peripheral_read_write_params_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/struct/peripheralReadWriteParams/"
author:
published: 2025-05-19
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 外设数据读写参数结构体rm\_peripheral\_read\_write\_params\_t

## 类成员变量说明

- ### 通讯端口port
	0-控制器RS485端口，1-末端接口板RS485接口，3-控制器ModbusTCP设备
	```
	int rm_peripheral_read_write_params_t::port
	```
- ### 数据起始地址address
	```
	int rm_peripheral_read_write_params_t::address
	```
- ### 外设设备地址device
	```
	int rm_peripheral_read_write_params_t::device
	```
- ### 要读的数据的数量num
	```
	int rm_peripheral_read_write_params_t::num
	```