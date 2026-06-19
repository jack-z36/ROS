---
title: "C、C++: 动作列表结构体rm_tool_action_list_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/struct/actionlist/"
author:
published: 2025-10-09
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 动作列表结构体rm\_tool\_action\_list\_t

## 类成员变量说明

### 页码page\_num

```
int rm_tool_action_list_t::page_num
```

### 每页大小page\_size

```
int rm_tool_action_list_t::page_size
```

### 列表长度total\_size

```
int rm_tool_action_list_t::total_size
```

### 模糊搜索vague\_search

```
char rm_tool_action_list_t::vague_search[32]
```

### 返回符合的动作列表长度list\_len

```
int rm_tool_action_list_t::list_len
```

### 返回符合的动作列表act\_list

```
rm_tool_action_info_t rm_tool_action_list_t::act_list[100]
```

*可以跳转 [rm\_tool\_action\_info\_t](https://develop.realman-robotics.com/robot4th/apic/struct/actioninfo/) 查阅结构体详细描述。*