---
title: "C、C++: 轨迹列表结构体rm_trajectory_list_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/struct/trajectoryinfolist/"
author:
published: 2025-05-19
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 轨迹列表结构体rm\_trajectory\_list\_t

## 类成员变量说明

### 页码page\_num

```
int rm_trajectory_list_t::page_num
```

### 每页大小page\_size

```
int rm_trajectory_list_t::page_size
```

### 列表长度total\_size

```
int rm_trajectory_list_t::total_size
```

### 模糊搜索vague\_search

```
char rm_trajectory_list_t::vague_search[32]
```

### 返回符合的轨迹列表长度list\_len

```
int rm_trajectory_list_t::list_len
```

### 返回符合的轨迹列表tra\_list

```
rm_trajectory_info_t rm_trajectory_list_t::tra_list[100]
```

*可以跳转 [rm\_trajectory\_info\_t](https://develop.realman-robotics.com/robot4th/apic/struct/trajectoryinfo/) 查阅结构体详细描述。*