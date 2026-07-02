---
title: "C、C++: 力位混合控制参数rm_force_position_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/struct/forcePosition/"
author:
published: 2025-05-28
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 力位混合控制参数rm\_force\_position\_t

## 类成员变量说明

### 传感器类型sensor

1-六维力

```
int rm_force_position_t::sensor
```

### 力坐标系mode

0-基坐标系力控；1-工具坐标系力控；

```
int rm_force_position_t::mode
```

### 各轴的力控模式数组control\_mode

6个力控方向（Fx Fy Fz Mx My Mz）的模式 0-固定模式 1-浮动模式 2-弹簧模式 3-运动模式 4-力跟踪模式 8-力跟踪+姿态自适应模式

```
int rm_force_position_t::control_mode[6]
```

### 各轴的期望力/力矩数组desired\_force

力控轴维持的期望力/力矩，力控轴的力控模式为力跟踪模式时，期望力/力矩设置才会生效 ，精度0.1N。

```
float rm_force_position_t::desired_force[6]
```

### 各轴的最大线速度/最大角速度限制数组limit\_vel

力控轴的最大线速度和最大角速度限制，只对开启力控方向生效。（x、y、z）轴的最大线速度，精度为0.001 m/s，（rx、ry、rz）轴的最大角速度，精度为0001 °/s

```
float rm_force_position_t::limit_vel[6]
```