---
title: "C、C++: 透传力位混合补偿参数rm_force_position_move_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/struct/forcePositionMove/"
author:
published: 2025-05-28
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 透传力位混合补偿参数rm\_force\_position\_move\_t

## 类成员变量说明

### 透传数据标志flag\_type

0-下发目标角度，1-下发目标位姿

```
int rm_force_position_move_t::flag
```

### 透传的目标位姿pose

当前坐标系下的目标位姿，支持四元数/欧拉角表示姿态。位置精度：0.001mm，欧拉角表示姿态，姿态精度：0.001rad，四元数方式表示姿态，姿态精度：0.000001

```
rm_pose_t rm_force_position_move_t::pose
```

*可以跳转 [rm\_pose\_t](https://develop.realman-robotics.com/robot4th/apic/struct/pose/) 查阅结构体详细描述。*

### 透传的目标关节角度数组joint

目标关节角度，单位：°，精度：0.001°

```
float rm_force_position_move_t::joint[ARM_DOF]
```

### 使用的传感器类型sensor

1-六维力

```
int rm_force_position_move_t::sensor
```

### 力坐标系mode

0-基坐标系力控；1-工具坐标系力控；

```
int rm_force_position_move_t::mode
```

### 是否高跟随follow

表示驱动器的运动跟随效果，true 为高跟随，false 为低跟随。

```
bool rm_force_position_move_t::follow
```

### 各轴的力控模式数组control\_mode

6个力控方向（Fx Fy Fz Mx My Mz）的模式 0-固定模式 1-浮动模式 2-弹簧模式 3-运动模式 4-力跟踪模式 8-力跟踪+姿态自适应模式

```
int rm_force_position_move_t::control_mode[6]
```

### 各轴的期望力/力矩数组desired\_force

力控轴维持的期望力/力矩，力控轴的力控模式为力跟踪模式时，期望力/力矩设置才会生效 ，精度0.1N。

```
float rm_force_position_move_t::desired_force[6]
```

### 各轴的最大线速度/最大角速度限制数组limit\_vel

力控轴的最大线速度和最大角速度限制，只对开启力控方向生效。（x、y、z）轴的最大线速度，精度为0.001 m/s，（rx、ry、rz）轴的最大角速度，精度为0001 °/s

```
float rm_force_position_move_t::limit_vel[6]
```

### 透传模式trajectory\_mode

高跟随模式下，0-完全透传模式、1-曲线拟合模式、2-滤波模式

```
int rm_force_position_move_t::trajectory_mode
```

### 平滑系数radio

曲线拟合模式时radio是平滑系数（0-100），滤波模式时radio是滤波参数（范围在0至1000之间）

```
int rm_force_position_move_t::radio
```