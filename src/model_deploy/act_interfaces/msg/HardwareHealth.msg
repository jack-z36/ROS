# RM65 双臂节点健康状态。
# 参考 DOCS/03_工程/阶段四：模型部署/01_contracts/rm65_driver_node 状态发布契约.md。
#
# 左右臂字段独立列出，避免消费方再做左右拆分；reason 是人类可读简短原因
# （连接失败 / 超时 / 急停 / DELTA_EXCEEDED / SDK 错误码等）。
std_msgs/Header header

bool left_connected
bool right_connected

bool left_estop_active
bool right_estop_active

# 最近一次 SDK 返回码：0 成功 / 1 控制器参数错误 / -1 发送失败 / -2 接收失败或超时
# / -3 解析失败 / -4 到位校验失败 / -5 单线程阻塞超时 / -6 规划被停止
# （见 睿尔曼r65四代技术文档/API：附录：API2错误代码）
int32 left_sdk_code
int32 right_sdk_code

# 控制器错误码（arm_err / sys_err，16 位）：
# 0x0000 正常 / 0x1001 关节通信异常 / 0x1009 超速 / 0x100A 超加速度
# / 0x100C 拖动超速 / 0x100D 碰撞 / 0x1010 关节掉使能 等
# （见 ROS2调用API接口功能包说明V1.0.0）
int32 left_controller_err
int32 right_controller_err

string left_reason
string right_reason
