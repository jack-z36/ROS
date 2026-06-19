---
title: "C、C++: Modbus TCP写数据结构体rm_modbus_tcp_write_params_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/struct/modbustcpswrite/"
author:
published: 2025-05-19
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## Modbus TCP写数据结构体rm\_modbus\_tcp\_write\_params\_t

## 类成员变量说明

### 数据起始地址address

```
int rm_modbus_tcp_write_params_t::address
```

### Modbus TCP主站名称master\_name

```
char rm_modbus_tcp_write_params_t::master_name[20]
```

### 主机IP地址ip

```
char rm_modbus_tcp_write_params_t::ip[16]
```

### 主机端口号port

```
int rm_modbus_tcp_write_params_t::port
```

### 数据的数量num

写入数据的数量，数据长度不超过100。

```
int rm_modbus_tcp_write_params_t::num
```

### 写入的数据data

写入的数据，数据长度不超过100。

```
int rm_modbus_tcp_write_params_t::data[120]
```