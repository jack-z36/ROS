---
title: "C、C++: 机械臂基本信息结构体rm_robot_info_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/struct/robotInfo/"
author:
published: 2025-05-19
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 机械臂基本信息结构体rm\_robot\_info\_t

## 类成员变量说明

- ### 机械臂自由度arm\_dof
	每个工具最多支持 5 个包络球，可以没有包络。
	```
	int rm_robot_info_t::arm_dof
	```
- ### 机械臂型号arm\_model
	```
	rm_robot_arm_model_e rm_robot_info_t::arm_model
	```
	*可以跳转 [rm\_robot\_arm\_model\_e](https://develop.realman-robotics.com/robot4th/apic/type/#rm-robot-arm-model-e%E6%9C%BA%E6%A2%B0%E8%87%82%E5%9E%8B%E5%8F%B7) 查阅枚举类型详细描述*
- ### 末端力传感器版本force\_type
	```
	rm_force_type_e rm_robot_info_t::force_type
	```
	*可以跳转 [rm\_force\_type\_e](https://develop.realman-robotics.com/robot4th/apic/type/#rm-force-type-e%E6%9C%BA%E6%A2%B0%E8%87%82%E6%9C%AB%E7%AB%AF%E5%8A%9B%E4%BC%A0%E6%84%9F%E5%99%A8%E7%89%88%E6%9C%AC) 查阅枚举类型详细描述*
- ### 机械臂控制器版本robot\_controller\_version
	控制器版本参数，其中：4-四代控制器，3-三代控制器。
	```
	int rm_robot_info_t::robot_controller_version
	```