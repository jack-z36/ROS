---
title: "API：附录：API2错误代码 | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apierrorList2/"
author:
published: 2025-06-24
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 附录：API2错误代码

## API2返回值定义

- C/C++：接口返回值为错误码，返回0为成功，返回其他值可查询下表。
- Python：接口返回值都是一个元组，接口的返回值形式为（RetVal，data），RetVal 为错误码，返回0为成功，返回其他值可查询下表；data 为获取的数据。

## API2错误代码

| 参数 | 类型 | 说明 | 处理建议 |
| --- | --- | --- | --- |
| 0 | `int` | 成功。 | \- |
| 1 | `int` | 控制器返回false，传递参数错误或机械臂状态发生错误。 | \- **校验JSON指令** ：   ①启用API的DEBUG日志，捕获原始JSON数据。   ②检查JSON语法：确保括号、引号、逗号等格式正确（可借助JSON校验工具）。   ③对照API文档，验证参数名称、数据类型及取值范围是否符合规范。   ④修正问题后重新发送指令，检查控制器返回的状态码及业务数据是否正常。   \- **检查机械臂状态** ：   ①查看机械臂控制器或日志中的实时报错信息（如硬件故障、超限等），根据提示复位、校准或排查硬件问题。   ②修正问题后重新发送指令，检查控制器返回的状态码及业务数据是否正常。 |
| \-1 | `int` | 数据发送失败，通信过程中出现问题。 | **检查网络连通性** ：   使用ping/telnet等工具检测与控制器的通信链路是否正常。 |
| \-2 | `int` | 数据接收失败，通信过程中出现问题或者控制器超时没有返回。 | \- **检查网络连通性** ：   使用ping/telnet等工具检测与控制器的通信链路是否正常。   \- **校验版本兼容性** ：   ①核对控制器固件版本是否支持当前API功能，具体版本配套关系请参考 [版本变更说明](https://develop.realman-robotics.com/robot4th/releaseNotes/releaseNotesfour/) 。   ②若版本过低需升级控制器或使用适配的API版本。 |
| \-3 | `int` | 返回值解析失败，接收到的数据格式不正确或不完整。 | **校验版本兼容性** ：   ①核对控制器固件版本是否支持当前API功能，具体版本配套关系请参考 [版本变更说明](https://develop.realman-robotics.com/robot4th/releaseNotes/releaseNotesfour/) 。   ②若版本过低需升级控制器或使用适配的API版本。 |
| \-4 | `int` | 当前到位设备校验失败，即当前到位设备不为关节/升降机构/夹爪/灵巧手。 | \- **检测多设备并发控制** ：检查是否有其他设备给机械臂发送运动指令：包括机械臂、夹爪、灵巧手、升降机的运动；   \- **实时监听指令事件** ：注册回调函数 `rm_get_arm_event_call_back` ：   ①捕获设备到位事件（如运动完成、超时等）；   ②通过回调参数 device 判断触发事件的具体设备类型。 |
| \-5 | `int` | 单线程阻塞模式超时未接收到返回，请确保超时时间设置合理。 | \- **检查超时时长设置** ：单线程阻塞模式下，支持配置等待设备运动完成的超时时间，务必确保设置超时时间大于设备运动时间；   \- **检查网络连通性** ：   使用ping/telnet等工具检测与控制器的通信链路是否正常。 |
| \-6 | `int` | 机械臂停止运动规划，外部发送了停止运动指令。 | \- **排查外部急停指令** ：排查是否存在外部调用急停指令，例如发送急停json协议、触发io急停或者在示教器触发急停。 |

注意

- 其中 `Modbus 配置` 和 `轨迹文件` 接口的错误代码中 `-4` 与上述错误代码不同，其定义为 `-4：三代控制器不支持该接口` 。
	- Modbus 配置 `modbusConfig` ： [C/C++](https://develop.realman-robotics.com/robot4th/apic/classes/modbusfour/) 、 [Python](https://develop.realman-robotics.com/robot4th/apipython/classes/modbusfour/) ；
		- 轨迹文件： [C/C++](https://develop.realman-robotics.com/robot4th/apic/classes/trajectoryfile/) 、 [Python](https://develop.realman-robotics.com/robot4th/apipython/classes/trajectoryfile/) ；
- 以下为不适用以上错误代码的接口，请查看对应接口中的错误码列表。
	- 逆解函数 `rm_algo_inverse_kinematics()` ： [C/C++](https://develop.realman-robotics.com/robot4th/apic/classes/algo/#6211) 、 [Python](https://develop.realman-robotics.com/robot4th/apipython/classes/algo/#6212) ；
		- 从多解中选取最优解（当前仅支持六自由度机器人） `rm_algo_ikine_select_ik_solve()` ： [C/C++](https://develop.realman-robotics.com/robot4th/apic/classes/algo/#6271) 、 [Python](https://develop.realman-robotics.com/robot4th/apipython/classes/algo/#6272) ；
		- 检查逆解结果是否超出关节限位（当前仅支持六自由度机器人） `rm_algo_ikine_check_joint_position_limit()` ： [C/C++](https://develop.realman-robotics.com/robot4th/apic/classes/algo/#6277) 、 [Python](https://develop.realman-robotics.com/robot4th/apipython/classes/algo/#6278) ；
		- 检查逆解结果是否超出速度限位（当前仅支持六自由度机器人） `rm_algo_ikine_check_joint_velocity_limit()` ： [C/C++](https://develop.realman-robotics.com/robot4th/apic/classes/algo/#6279) 、 [Python](https://develop.realman-robotics.com/robot4th/apipython/classes/algo/#6280) ；
		- 根据参考位形计算臂角大小（仅支持RM75） `rm_algo_calculate_arm_angle_from_config_rm75()` ： [C/C++](https://develop.realman-robotics.com/robot4th/apic/classes/algo/#6281) 、 [Python](https://develop.realman-robotics.com/robot4th/apipython/classes/algo/#6282) ；
		- 臂角法求解RM75逆运动学 `rm_algo_inverse_kinematics_rm75_for_arm_angle()` ： [C/C++](https://develop.realman-robotics.com/robot4th/apic/classes/algo/#6283) 、 [Python](https://develop.realman-robotics.com/robot4th/apipython/classes/algo/#6284) ；
		- 数值法判断机器人是否处于奇异位形 `rm_algo_universal_singularity_analyse()` ： [C/C++](https://develop.realman-robotics.com/robot4th/apic/classes/algo/#6285) 、 [Python](https://develop.realman-robotics.com/robot4th/apipython/classes/algo/#6286) ；
		- 解析法判断机器人是否处于奇异位形（仅支持六自由度） `rm_algo_kin_robot_singularity_analyse()` ： [C/C++](https://develop.realman-robotics.com/robot4th/apic/classes/algo/#6287) 、 [Python](https://develop.realman-robotics.com/robot4th/apipython/classes/algo/#6288) ；
		- 保存拖动示教轨迹 `rm_save_trajectory()` ： [C/C++](https://develop.realman-robotics.com/robot4th/apic/classes/dragTeach/#6213) 、 [Python](https://develop.realman-robotics.com/robot4th/apipython/classes/dragTeach/#6214) ；
		- 设置六维力拖动示教模式 `rm_set_force_drag_mode()` ： [C/C++](https://develop.realman-robotics.com/robot4th/apic/classes/dragTeach/#6215) 、 [Python](https://develop.realman-robotics.com/robot4th/apipython/classes/dragTeach/#6216) ；
		- 获取六维力拖动示教模式 `rm_get_force_drag_mode()` ： [C/C++](https://develop.realman-robotics.com/robot4th/apic/classes/dragTeach/#6217) 、 [Python](https://develop.realman-robotics.com/robot4th/apipython/classes/dragTeach/#6218) ；
		- 松开夹爪 `rm_set_gripper_release()` ： [C/C++](https://develop.realman-robotics.com/robot4th/apic/classes/gripperControl/#6219) 、 [Python](https://develop.realman-robotics.com/robot4th/apipython/classes/gripperControl/#6220) ；
		- 夹爪力控夹取 `rm_set_gripper_pick()` ： [C/C++](https://develop.realman-robotics.com/robot4th/apic/classes/gripperControl/#6221) 、 [Python](https://develop.realman-robotics.com/robot4th/apipython/classes/gripperControl/#6222) ；
		- 夹爪持续力控夹取 `rm_set_gripper_pick_on()` ： [C/C++](https://develop.realman-robotics.com/robot4th/apic/classes/gripperControl/#6223) 、 [Python](https://develop.realman-robotics.com/robot4th/apipython/classes/gripperControl/#6224) ；
		- 设置夹爪达到指定位置 `rm_set_gripper_position()` ： [C/C++](https://develop.realman-robotics.com/robot4th/apic/classes/gripperControl/#6225) 、 [Python](https://develop.realman-robotics.com/robot4th/apipython/classes/gripperControl/#6226) ；
		- 运行灵巧手目标手势序列号 `rm_set_hand_posture()` ： [C/C++](https://develop.realman-robotics.com/robot4th/apic/classes/handControl/#6227) 、 [Python](https://develop.realman-robotics.com/robot4th/apipython/classes/handControl/#6228) ；
		- 运行灵巧手动作序列号 `rm_set_hand_seq()` ： [C/C++](https://develop.realman-robotics.com/robot4th/apic/classes/handControl/#6229) 、 [Python](https://develop.realman-robotics.com/robot4th/apipython/classes/handControl/#6230) ；
		- 开始运行指定编程文件 `rm_set_program_id_run()` ： [C/C++](https://develop.realman-robotics.com/robot4th/apic/classes/projectManagement/#6233) 、 [Python](https://develop.realman-robotics.com/robot4th/apipython/classes/projectManagement/#6234) ；
		- 初始化线程模式 `rm_init()` ： [C/C++](https://develop.realman-robotics.com/robot4th/apic/classes/roboticArm/#6235) 、 [Python](https://develop.realman-robotics.com/robot4th/apipython/classes/roboticArm/#6236) ；
		- 删除指定机械臂实例 `rm_delete_robot_arm()` ： [C/C++](https://develop.realman-robotics.com/robot4th/apic/classes/roboticArm/#6237) 、 [Python](https://develop.realman-robotics.com/robot4th/apipython/classes/roboticArm/#6238) ；
		- 获取机械臂基本信息 `rm_get_robot_info()` ： [C/C++](https://develop.realman-robotics.com/robot4th/apic/classes/roboticArm/#6239) 、 [Python](https://develop.realman-robotics.com/robot4th/apipython/classes/roboticArm/#6240) ；
		- 查询流程图编程运行状态 `rm_get_flowchart_program_run_state()` ； [C/C++](https://develop.realman-robotics.com/robot4th/apic/classes/projectManagement/#6307) 、 [Python](https://develop.realman-robotics.com/robot4th/apipython/classes/projectManagement/#6308) ；
		- 设置机械臂急停状态 `rm_set_arm_emergency_stop()` ； [C/C++](https://develop.realman-robotics.com/robot4th/apic/classes/roboticArm/#6309) 、 [Python](https://develop.realman-robotics.com/robot4th/apipython/classes/roboticArm/#6310) ；