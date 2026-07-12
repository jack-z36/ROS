# ACT 微元设计与协作：L2-06

## 拟议源码与微元

| ACT 微元 | 3.5 类型 | target layer | target file | function/class | inputs | outputs | side effects | Pi0.5 reference |
|---|---|---|---|---|---|---|---|---|
| 调度状态 | 数据 | runtime | `src/model_deploy/act/runtime/control_loop.py` | `ControlLoop` fields | config / queues | active chunk、cursor、request id | 保存跨 tick 状态 | `ControlLoop.__init__` |
| chunk 验证 | 计算函数 | runtime | 同上 | `validate_chunk_for_cursor()` | ActionChunk、now、spec | reason 或可读 chunk | 无 | `is_action_chunk_usable()` |
| 收集最新结果 | 内部状态更新函数 | runtime | 同上 | `_collect_latest_chunk()` | result queue | active/pending chunk 更新 | 清空旧结果、记录 discard | `_collect_result()` |
| 请求推理 | 编排函数 | runtime | 同上 | `_maybe_submit_inference()` | latest observation、cursor | InferenceRequest | `put_latest()`、metrics | `_maybe_submit_request()` |
| 单步直取 | 内部状态更新函数 | runtime | 同上 | `_take_cursor_action()` | active chunk/cursor | raw `(16,)` 或 None | cursor += 1 | `_next_raw_action()`（去除 blend） |
| 主 tick | 编排函数 | runtime | 同上 | `tick()` | clock、所有 service | publish/fallback 调用 | 状态迁移、metrics | `tick()` |
| fallback | 编排函数 | runtime | 同上 | `_emit_fallback(reason)` | reason、policy、last safe action | L2-05 调用 | fallback count/status | `_fallback()` |
| ROS 定时装配 | 数据读写函数 | ui | `src/model_deploy/act/ui/act_deploy_node.py` | `ActDeployNode._control_tick()` | ROS timer | 调用 runtime | ROS timer/status publish | `_control_tick()` |

## tick 状态机

```text
tick(now)
  -> 收取最新 chunk；非法则 discard + fallback reason
  -> 若无可用 observation：不提交 request，进入 fallback
  -> 依据 cursor/prefetch 且无 pending request：创建 InferenceRequest，写 latest queue
  -> 由 active chunk[cursor] 直取 raw `(16,)`；没有则 fallback
  -> SafetyGuard.filter(raw, observation, previous_safe)
  -> accepted：L2-05.publish_safe(action)；rejected：L2-05.emit_fallback(reason)
  -> 更新 RuntimeMetrics/status
```

Creation order: L2-01 `DeployConfig` → L2-02 collector/buffer → L2-03 worker → L2-04 guard → L2-05 publisher → `ControlLoop` → UI timer start。

State owner: L2-06 唯一拥有 active chunk/cursor/request 状态和汇总 metrics；L2-02 拥有 observation；L2-03 拥有模型推理；L2-04 拥有安全结论；L2-05 拥有外部命令。

Pure RAM calculations: chunk 验证和 cursor 选择。External boundary reads/writes: UI timer/status 与 L2-05 publish；queue 交接是 RAM 内并发边界。Runtime orchestration point: `ControlLoop.tick()`。Failure propagation: reason → fallback output + metrics/status；启动配置失败不进 timer。

## 六层落点

| 层 | 是否新增 | 文件 | 职责 |
|---|---|---|---|
| types | 否 | — | 使用 L2-01/02/03/04 的公共对象，不重定义 |
| config | 否 | — | 使用 L2-01 `DeployConfig`，不解析配置 |
| repo | 否 | — | 无进程外资源读取 |
| service | 否 | — | 调用 L2-04/L2-05，不吞并其计算 |
| runtime | 是 | `runtime/control_loop.py` | tick 状态机、queue、cursor、fallback、metrics |
| ui | 是 | `ui/act_deploy_node.py` | ROS timer/对象装配/status 发布 |

`ControlLoop` 必须是 class：其状态跨 tick、与 worker 并发交接且有完整生命周期。chunk 验证保持模块级纯函数；不把 batch、前向、安全计算或 topic 转换塞进 class。
