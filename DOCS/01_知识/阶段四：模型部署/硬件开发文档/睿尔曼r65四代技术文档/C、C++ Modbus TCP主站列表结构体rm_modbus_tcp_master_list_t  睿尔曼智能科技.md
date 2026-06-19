---
title: "C、C++: Modbus TCP主站列表结构体rm_modbus_tcp_master_list_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/struct/modbustcpmasterlist/"
author:
published: 2025-05-19
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## Modbus TCP主站列表结构体rm\_modbus\_tcp\_master\_list\_t

## 类成员变量说明

### 页码page\_num

```
int rm_modbus_tcp_master_list_t::page_num
```

### 每页大小page\_size

```
int rm_modbus_tcp_master_list_t::page_size
```

### 列表长度total\_size

```
int rm_modbus_tcp_master_list_t::total_size
```

### 模糊搜索vague\_search

```
char rm_modbus_tcp_master_list_t::vague_search[32]
```

### 返回符合的Modbus TCP主站列表长度list\_len

```
int rm_modbus_tcp_master_list_t::list_len
```

### 返回符合的Modbus TCP主站列表master\_list

```
rm_modbus_tcp_master_info_t rm_modbus_tcp_master_list_t::master_list[100]
```

*可以跳转 [rm\_modbus\_tcp\_master\_info\_t](https://develop.realman-robotics.com/robot4th/apic/struct/modbustcpmaster/) 查阅结构体详细描述。*