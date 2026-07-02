---
title: "C、C++: 错误代码结构体rm_err_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/struct/err/"
author:
published: 2025-05-19
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 错误代码结构体rm\_err\_t

## 类成员变量说明

- ### 错误代码个数err\_len
	```
	uint8_t rm_err_t::err_len
	```
- ### 错误代码数组err
	不超过 10 个字节，支持字母、数字、下划线。
	```
	int rm_err_t::err[24]
	```