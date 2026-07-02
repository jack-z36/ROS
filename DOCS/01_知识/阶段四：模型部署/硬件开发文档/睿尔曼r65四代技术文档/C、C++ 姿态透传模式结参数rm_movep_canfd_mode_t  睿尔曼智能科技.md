---
title: "C、C++: 姿态透传模式结参数rm_movep_canfd_mode_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/struct/movepCanfdMode/"
author:
published: 2025-05-19
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 姿态透传模式结参数rm\_movep\_canfd\_mode\_t

## 类成员变量说明

### 透传的目标位姿pose

当前坐标系下的目标位姿，支持四元数/欧拉角表示姿态。位置精度：0.001mm，欧拉角表示姿态，姿态精度：0.001rad，四元数方式表示姿态，姿态精度：0.000001

```
rm_pose_t rm_movep_canfd_mode_t::pose
```

*可以跳转 [rm\_pose\_t](https://develop.realman-robotics.com/robot4th/apic/struct/pose/) 查阅结构体详细描述。*

### 是否高跟随follow

表示驱动器的运动跟随效果，true 为高跟随，false 为低跟随。

```
bool rm_movep_canfd_mode_t::follow
```

### 透传模式trajectory\_mode

高跟随模式下，0-完全透传模式、1-曲线拟合模式、2-滤波模式

```
int rm_movep_canfd_mode_t::trajectory_mode
```

### 平滑系数radio

曲线拟合模式时radio是平滑系数（0-100），滤波模式时radio是滤波参数（范围在0至1000之间）

```
int rm_movep_canfd_mode_t::radio
```