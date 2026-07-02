---
title: "C、C++: 动作配置 | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/classes/toolActionConfig/"
author:
published: 2025-10-09
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 动作配置

支持进行动作的相关配置，包括查询、运行、删除、保存和更新等操作。

## 查询动作列表rm\_get\_tool\_action\_list

- **方法原型：**
```c
int rm_get_tool_action_list(rm_robot_handle *handle, int page_num, int page_size, const char *vague_search, rm_tool_action_list_t *list);
```
- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `page_num` | 输入参数 | 页码。 |
| `page_size` | 输入参数 | 每页大小。 |
| `vague_search` | 输入参数 | 模糊搜索字符串。 |
| `list` | 输出参数 | 动作列表。 |

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 和 [rm\_tool\_action\_list\_t](https://develop.realman-robotics.com/robot4th/apic/struct/actionlist/) 查阅结构体详细描述。*

- **返回值:**

| 参数 | 说明 |
| --- | --- |
| 0 | 成功。 |
| 1 | 控制器返回false，传递参数错误或机械臂状态发生错误。 |
| \-1 | 数据发送失败，通信过程中出现问题。 |
| \-2 | 数据接收失败，通信过程中出现问题或者控制器超时没有返回。 |
| \-3 | 返回值解析失败，接收到的数据格式不正确或不完整。 |
| \-4 | 三代控制器不支持该接口. |

- **使用示例**
```c
int page_num = 1;
int page_size = 20;
const char* vague_search = NULL;
rm_tool_action_list_t list;
ret = rm_get_tool_action_list(handle, page_num, page_size, vague_search, &list);
printf("%d\n", ret);
printf("=== 工具动作列表 ===\n");
printf("返回动作数: %d\n", list.list_len);
printf("\n");
const int THRESHOLD = 1000000;
for (int i = 0; i < list.list_len; i++) {
    printf("动作 %d:\n", i + 1);
    printf("  名称: %s\n", list.act_list[i].name);
    int hasValidPos = 0;
    for (int j = 0; j < 100; j++) {
        if (abs(list.act_list[i].hand_pos[j]) < THRESHOLD) {
            hasValidPos = 1;
            break;
        }
    }
    int hasValidAngle = 0;
    for (int j = 0; j < 100; j++) {
        if (abs(list.act_list[i].hand_angle[j]) < THRESHOLD) {
            hasValidAngle = 1;
            break;
        }
    }
    if (hasValidPos) {
        printf("  handpos: [");
        for (int j = 0; j < 100; j++) {
            if (abs(list.act_list[i].hand_pos[j]) < THRESHOLD) {
                if (j > 0) printf(", ");
                printf("%d", list.act_list[i].hand_pos[j]);
            }
        }
        printf("]\n");
    }
    else if (hasValidAngle) {
        printf("  handangle: [");
        for (int j = 0; j < 100; j++) {
            if (abs(list.act_list[i].hand_angle[j]) < THRESHOLD) {
                if (j > 0) printf(", ");
                printf("%d", list.act_list[i].hand_angle[j]);
            }
        }
        printf("]\n");
    }
    printf("--------------------\n");
}
```

## 运行指定末端动作rm\_run\_tool\_action

- **方法原型：**
```c
int rm_run_tool_action(rm_robot_handle *handle, const char *action_name);
```
- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂控制句柄。 |
| `action_name` | 输入参数 | 动作名称。 |

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **返回值:**

| 参数 | 说明 |
| --- | --- |
| 0 | 成功。 |
| 1 | 控制器返回false，传递参数错误或机械臂状态发生错误。 |
| \-1 | 数据发送失败，通信过程中出现问题。 |
| \-2 | 数据接收失败，通信过程中出现问题或者控制器超时没有返回。 |
| \-3 | 返回值解析失败，接收到的数据格式不正确或不完整。 |
| \-4 | 三代控制器不支持该接口. |
| \-5 | 当前到位设备校验失败，即当前到位设备不为末端工具动作。 |

- **使用示例**

运行指定末端动作run\_tool\_action

```c
const char* action_name = "1";
ret = rm_run_tool_action(handle, action_name);
printf("%d\n", ret);
```

## 删除指定末端动作rm\_delete\_tool\_action

- **方法原型：**
```c
int rm_delete_tool_action(rm_robot_handle *handle, const char *action_name);
```
- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂控制句柄。 |
| `action_name` | 输入参数 | 动作名称。 |

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **返回值:**

| 参数 | 说明 |
| --- | --- |
| 0 | 成功。 |
| 1 | 控制器返回false，传递参数错误或机械臂状态发生错误。 |
| \-1 | 数据发送失败，通信过程中出现问题。 |
| \-2 | 数据接收失败，通信过程中出现问题或者控制器超时没有返回。 |
| \-3 | 返回值解析失败，接收到的数据格式不正确或不完整。 |
| \-4 | 三代控制器不支持该接口 |

- **使用示例**

删除指定末端动作delete\_tool\_action

```c
const char* action_name = "p";
ret = rm_delete_tool_action(handle, action_name);
printf("%d\n", ret);
```

## 保存动作到控制器rm\_save\_tool\_action

- **方法原型：**
```c
int rm_save_tool_action(rm_robot_handle *handle, const char *action_name,int *selected_array,int array_size, int array_type);
```
- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入数据 | 机械臂控制句柄。 |
| `action_name` | 输入数据 | 动作名称。 |
| `selected_array` | 输入数据 | 保存数组的值。 |
| `array_size` | 输入数据 | 保存数组的大小。 |
| `array_type` | 输入数据 | 保存数字的类型（0-表示保存类型为hand\_pos。 1-表示保存类型为hand\_angle） |

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **返回值:**

| 参数 | 说明 |
| --- | --- |
| 0 | 成功。 |
| 1 | 控制器返回false，传递参数错误或机械臂状态发生错误。 |
| \-1 | 数据发送失败，通信过程中出现问题。 |
| \-2 | 数据接收失败，通信过程中出现问题或者控制器超时没有返回。 |
| \-3 | 返回值解析失败，接收到的数据格式不正确或不完整。 |
| \-4 | 三代控制器不支持该接口 |

- **使用示例**

保存动作save\_tool\_action

```c
const char* action_name = "12";
int selected_array[6] = {1,1,1,1,1,1};
int array_size = 6;
int array_type = 0;
ret = rm_save_tool_action(handle, action_name, selected_array, array_size, array_type);
printf("%d\n", ret);
```

## 更新动作到控制器rm\_update\_tool\_action

- **方法原型：**
```c
int rm_update_tool_action(rm_robot_handle *handle, const char *action_name, const char *new_name, int *selected_array,int array_size, int array_type);
```
- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入数据 | 机械臂控制句柄。 |
| `action_name` | 输入数据 | 动作名称。 |
| `new_name` | 输入数据 | 新动作名称。 |
| `selected_array` | 输入数据 | 保存数组的值。 |
| `array_size` | 输入数据 | 保存数组的大小。 |
| `array_type` | 输入数据 | 保存数字的类型（0-表示保存类型为hand\_pos。 1-表示保存类型为hand\_angle） |

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **返回值:**

| 参数 | 说明 |
| --- | --- |
| 0 | 成功。 |
| 1 | 控制器返回false，传递参数错误或机械臂状态发生错误。 |
| \-1 | 数据发送失败，通信过程中出现问题。 |
| \-2 | 数据接收失败，通信过程中出现问题或者控制器超时没有返回。 |
| \-3 | 返回值解析失败，接收到的数据格式不正确或不完整。 |
| \-4 | 三代控制器不支持该接口 |

- **使用示例**
```c
const char* action_name = "121";
const char* new_name = "12";
int selected_array[6] = { 2,1,1,1,1,1 };
int array_size = 6;
int array_type = 1;
ret = rm_update_tool_action(handle, action_name, new_name, selected_array, array_size, array_type);
printf("%d\n", ret);
```