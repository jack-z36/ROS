# 验收卡片：deploy_057 L2-02 观测流水线契约修复

> [!info] 归属
> - 所属调度组：l2-06-control-loop
> - 接口 owner：l2-02-observation-snapshot
> - 验收 Agent 只读；本地 typed pipeline 不得因 ROS 缺失 skip。

| L3 编号 | `deploy_057` |
| 验收模式 | `direct-local` |

## 1. 检查对象

| 字段 | 值 |
|---|---|
| L3 任务文件 | DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_057_L2-02观测流水线契约修复.md |
| 源码 | observation types/preprocess/collector/buffer/adapter/pipeline/facade 与对应 tests |
| 设计 | L2-02 HTML + agent_context |
| 前置 | deploy_051/052/056 PASS_LOCAL |

## 2. 必跑命令

```bash
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/types/test_observation.py \
  src/model_deploy/act/tests/service/test_image_preprocess.py \
  src/model_deploy/act/tests/service/test_observation_collector.py \
  src/model_deploy/act/tests/runtime/test_observation_buffer.py \
  src/model_deploy/act/tests/ui/test_observation_ros_adapter.py \
  src/model_deploy/act/tests/integration/test_l2_02_gate.py -v
```

```bash
python3 skills/stage4-l2-designer/scripts/validate_l2_design_package.py \
  'DOCS/03_工程/阶段四：模型部署/02_implement/l2-02-observation-snapshot_ObservationSnapshot组装闭环'
```

## 3. PASS / FAIL / BLOCKED

### PASS_LOCAL

- [ ] factory/public aggregate 签名精确，spec/clock identity 成立。
- [ ] camera keys、CHW float32 [0,1]、shape 在 subscription 前校验。
- [ ] snapshot arrays 深拥有且无 cache/source alias。
- [ ] captured_at_s 和 buffer freshness 共用注入 monotonic clock。
- [ ] gripper message class 与 decoder 一致；代码/配置异常传播。
- [ ] 只有明确 ROS package/runtime 缺失可分类环境阻断。
- [ ] L2-02 HTML 与 agent_context 已同步。

### FAIL_LOCAL

Dict fallback、HWC、wall clock、shallow copy、Pose/Point scalar 矛盾、broad except、subscription 前无校验、设计双轨或任一 required test 失败。

### BLOCKED_ENV

只有 local PASS 后真实 ROS graph 不可用可补记 BLOCKED_ENV；不得覆盖 local FAIL。

## 4. L2 Gate 贡献

| 场景 | G03 |
|---|---|
| 贡献 | P0-05～P0-09、typed observation factory 与真实 observation seam |
| 未完成影响 | deploy_053/054/055 不得执行 |

