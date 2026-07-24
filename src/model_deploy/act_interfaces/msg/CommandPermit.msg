# 人工安全许可（对齐 src/model_deploy/act/types/action_publish.py 中 CommandPermit frozen dataclass）
#
# 不变量：
#   allowed=true  -> reason_code 必须为空字符串
#   allowed=false -> reason_code 必须是非空稳定 code
#
# 过期机制：本消息不带 TTL/expiry 字段。消费方按"每 tick 重新求值 + fail-closed"
# 处理：消息 stale（超过 permit_stale_sec 未更新）即视为 allowed=false。
# reason_code 复用 act 侧已定义的稳定码：
#   ESTOP_ACTIVE / PERMIT_STALE / PERMIT_SOURCE_ERROR / COMMAND_OUTPUT_DISABLED
bool allowed
string reason_code
