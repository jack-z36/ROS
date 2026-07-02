---
title: "C、C++: 全局路点管理globalWaypointManage | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/classes/globalWaypointManage/"
author:
published: 2025-05-19
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 全局路点管理globalWaypointManage

可用于新增、查询或者更新全局路点。

## 新增全局路点rm\_add\_global\_waypoint()

- **方法原型：**
```c
int rm_add_global_waypoint(rm_robot_handle * handle,rm_waypoint_t waypoint)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 和 [rm\_waypoint\_t](https://develop.realman-robotics.com/robot4th/apic/struct/waypoint/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `waypoint` | 输入参数 | 新增全局路点参数（无需输入新增全局路点时间）。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
// 新增全局路点p3
rm_waypoint_t waypoint;
strcpy(waypoint.point_name,"p3");
waypoint.joint[0] = 20;
waypoint.joint[1] = 30;
// 剩余关节角度均为 0
for (int i = 2; i < 6; ++i) {
    waypoint.joint[i] = 0.0;
}
// 设置位置姿态
waypoint.pose.position.x = 0.01;
waypoint.pose.position.y = 0.02;
waypoint.pose.position.z = 0.03;
waypoint.pose.euler.rx = 0.1;
waypoint.pose.euler.ry = 0.2;
waypoint.pose.euler.rz = 0.3;
strcpy(waypoint.work_frame, "World");
strcpy(waypoint.tool_frame, "Arm_Tip");
ret = rm_add_global_waypoint(robot_handle, waypoint);
```

## 更新全局路点rm\_update\_global\_waypoint()

- **方法原型：**
```c
int rm_update_global_waypoint(rm_robot_handle * handle,rm_waypoint_t waypoint)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 和 [rm\_waypoint\_t](https://develop.realman-robotics.com/robot4th/apic/struct/waypoint/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `waypoint` | 输入参数 | 更新全局路点参数（无需输入更新全局路点时间）。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
// 更新全局路点p3
rm_waypoint_t waypoint;
strcpy(waypoint.point_name,"p3");
waypoint.joint[0] = 20;
waypoint.joint[1] = 30;
// 剩余关节角度均为 0
for (int i = 2; i < 6; ++i) {
    waypoint.joint[i] = 0.0;
}
// 设置位置姿态
waypoint.pose.position.x = 0.01;
waypoint.pose.position.y = 0.02;
waypoint.pose.position.z = 0.03;
waypoint.pose.euler.rx = 0.1;
waypoint.pose.euler.ry = 0.2;
waypoint.pose.euler.rz = 0.3;
strcpy(waypoint.work_frame, "World");
strcpy(waypoint.tool_frame, "Arm_Tip");
ret = rm_update_global_waypoint(robot_handle, waypoint);
```

## 删除全局路点rm\_delete\_global\_waypoint()

- **方法原型：**
```c
int rm_delete_global_waypoint(rm_robot_handle * handle,const char * point_name)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 和 [rm\_waypoint\_t](https://develop.realman-robotics.com/robot4th/apic/struct/waypoint/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `point_name` | 输入参数 | 全局路点名称。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
// 删除全局路点p3
rm_delete_global_waypoint(robot_handle, "p3");
```

## 查询指定全局路点rm\_get\_given\_global\_waypoint()

- **方法原型：**
```c
int rm_get_given_global_waypoint(rm_robot_handle * handle,const char * name,rm_waypoint_t * point)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 和 [rm\_waypoint\_t](https://develop.realman-robotics.com/robot4th/apic/struct/waypoint/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `name` | 输入参数 | 指定全局路点名称。 |
| `point` | 输出参数 | 返回指定的全局路点参数。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
// 获取全局路点p3参数
rm_waypoint_t point;
ret = rm_get_given_global_waypoint(robot_handle, "p3", &point);
```

## 查询多个全局路点rm\_get\_global\_waypoints\_list()

- **方法原型：**
```c
int rm_get_global_waypoints_list(rm_robot_handle * handle,int page_num,int page_size,const char * vague_search,rm_waypoint_list_t * point_list)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 和 [rm\_waypoint\_t](https://develop.realman-robotics.com/robot4th/apic/struct/waypoint/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `page_num` | 输入参数 | 页码。 |
| `page_size` | 输入参数 | 每页大小。 |
| `vague_search` | 输入参数 | 模糊搜索的关键词。 |
| `point_list` | 输出参数 | 返回的全局路点列表。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
// 查询第一页10个全局路点信息
rm_waypoint_list_t point_list;
int page_num = 1;
int page_size = 10;
const char *vague_search;
ret = rm_get_global_waypoints_list(robot_handle,page_num,page_size,vague_search,&point_list);
printf("get global waypoints list result : %d\n", ret);
```