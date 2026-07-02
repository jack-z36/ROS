---
title: "C、C++: 机械臂软件信息结构体rm_arm_software_version_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/struct/softwareVersion/"
author:
published: 2025-05-19
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 机械臂软件信息结构体rm\_arm\_software\_version\_t

## 类成员变量说明

- ### 机械臂型号product\_version
	```
	char rm_arm_software_version_t::product_version[10]
	```
- ### 机械臂控制器版本robot\_controller\_version
	该字段为"4.0"，表明为四代控制器。
	```
	char rm_arm_software_version_t::robot_controller_version[10]
	```
- ### 算法库信息algorithm\_info
	```
	rm_algorithm_version_t rm_arm_software_version_t::algorithm_info
	```
	*可以跳转 [rm\_algorithm\_version\_t](https://develop.realman-robotics.com/robot4th/apic/struct/algorithmVersion/) 查阅结构体详细描述。*
- ### ctrl 层软件信息ctrl\_info
	```
	rm_software_build_info_t rm_arm_software_version_t::ctrl_info
	```
	*可以跳转 [rm\_software\_build\_info\_t](https://develop.realman-robotics.com/robot4th/apic/struct/softwarinfo/) 查阅结构体详细描述。*
- ### Communication模块软件信息com\_info
	```
	rm_software_build_info_t rm_arm_software_version_t::com_info
	```
	*可以跳转 [rm\_software\_build\_info\_t](https://develop.realman-robotics.com/robot4th/apic/struct/softwarinfo/) 查阅结构体详细描述。*
- ### 流程图编程模块软件信息program\_info
	```
	rm_software_build_info_t rm_arm_software_version_t::program_info
	```
	*可以跳转 [rm\_software\_build\_info\_t](https://develop.realman-robotics.com/robot4th/apic/struct/softwarinfo/) 查阅结构体详细描述。*