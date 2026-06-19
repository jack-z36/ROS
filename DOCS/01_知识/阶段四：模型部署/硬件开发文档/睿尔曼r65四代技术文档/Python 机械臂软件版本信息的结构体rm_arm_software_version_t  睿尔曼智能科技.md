---
title: "Python: 机械臂软件版本信息的结构体rm_arm_software_version_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/armSoftwareVersion/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 机械臂软件版本信息的结构体rm\_arm\_software\_version\_t

## 属性

| 属性名 | 类型 | 说明 |
| --- | --- | --- |
| `product_version` | `bytes` | 机械臂型号。 |
| `robot_controller_version` | `bytes` | 该字段为"4.0"，表明当前为四代控制器。 |
| `algorithm_info` | [`rm_algorithm_version_t`](https://develop.realman-robotics.com/robot4th/apipython/struct/algorithmVersion/) | 算法库信息。 |
| `ctrl_info` | [`rm_software_build_info_t`](https://develop.realman-robotics.com/robot4th/apipython/struct/softwarinfo/) | ctrl 层软件信息。 |
| `com_info` | [`rm_software_build_info_t`](https://develop.realman-robotics.com/robot4th/apipython/struct/softwarinfo/) | communication 模块软件信息。 |
| `program_info` | [`rm_software_build_info_t`](https://develop.realman-robotics.com/robot4th/apipython/struct/softwarinfo/) | 流程图编程模块软件信息。 |

## 成员函数

```python
rm_arm_software_version_t.to_dict(self,recurse = True)
```

将类的变量返回为字典，如果recurse为True，则递归处理ctypes结构字段。