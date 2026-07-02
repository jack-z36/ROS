---
title: "Python: 流程图程序运行状态rm_flowchart_run_state_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/flowchartstate/"
author:
published: 2025-06-10
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 流程图程序运行状态rm\_flowchart\_run\_state\_t

## 参数说明

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `run_state` | `int` | 运行状态 0 未开始 1运行中 2暂停中。 |
| `id` | `int` | 当前使能的文件id。 |
| `name` | `str` | 当前使能的文件名称。 |
| `plan_speed` | `int` | 当前使能的文件全局规划速度比例 1-100。 |
| `step_mode` | `int` | 单步模式，0为空，1为正常, 2为单步。 |
| `modal_id` | `str` | 运行到的流程图块的id。未运行则不返回。 |