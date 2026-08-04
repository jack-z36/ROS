#!/usr/bin/env node
/*
 * Phase 2 assignment builder for the model_deploy ROS2 workspace.
 *
 * Reads the structural results + the raw input nodes, classifies every file
 * node into one semantic architectural layer, runs self-checks, and writes the
 * final layers.json consumed by downstream stages.
 *
 * Classification policy (informed by Phase 1 structural data + summaries/tags):
 *  - The repo is a ROS2 multi-package workspace. Both act/ and elephant_gripper/
 *    share the SAME cross-cutting layered design (types -> config -> repo ->
 *    service -> runtime -> ui). We therefore assign by SEMANTIC ROLE (the
 *    sub-directory function + file summary), collapsing across packages.
 *  - Non-code nodes (config/document/schema) get their own cross-cutting
 *    layers; ROS msg schemas (.msg) form a Data/Interface layer.
 */
'use strict';

const fs = require('fs');

const RESULTS_PATH =
  '/home/hit/ROS/src/model_deploy/.ua/tmp/ua-arch-results.json';
const INPUT_PATH =
  '/home/hit/ROS/src/model_deploy/.ua/tmp/ua-arch-input.json';
const OUTPUT_PATH =
  '/home/hit/ROS/src/model_deploy/.ua/intermediate/layers.json';

const results = JSON.parse(fs.readFileSync(RESULTS_PATH, 'utf8'));
const input = JSON.parse(fs.readFileSync(INPUT_PATH, 'utf8'));
const nodes = input.fileNodes;
const idToNode = new Map(nodes.map((n) => [n.id, n]));

// ---------------------------------------------------------------------------
// Classifier. Returns one of the 8 layer ids. Order matters: the first rule
// that matches wins. Rules are derived from Phase 1 directory grouping +
// per-file summaries/tags (Phase 2 Step 4).
// ---------------------------------------------------------------------------
function classify(n) {
  const p = n.filePath.replace(/\\/g, '/');
  const type = n.type;
  const tags = (n.tags || []).join('|').toLowerCase();

  // --- non-code layers first ------------------------------------------------

  // ROS2 message definitions -> Data / Interface layer
  if (type === 'schema' || /\.msg$/.test(n.name)) return 'layer:ros-interface';

  // Documents (README, architecture docs, build manifests like CMakeLists.txt
  // that are descriptive at this workspace level, SDK vendor notes).
  if (type === 'document') return 'layer:documentation';

  // Configs: package.xml, setup.cfg, deploy.yaml, *.yaml params, .ua config,
  // test fixture yaml, environment.yml. Note: *.msg handled above.
  if (type === 'config') return 'layer:config';

  // --- tests layer ----------------------------------------------------------
  // Any file under a tests/ directory, or conftest.py, or test fixtures.
  if (/(^|\/)tests?\//.test(p)) return 'layer:test';
  if (/(^|\/)conftest\.py$/.test(p)) return 'layer:test';
  // rm65 gtest sources live under tests/
  if (/rm65_dual_arm\/tests\/test_.*\.cpp$/.test(p)) return 'layer:test';

  // --- CI / verification scripts (act L2 verify scripts) -------------------
  // These are CI/CD-adjacent acceptance scripts. Tagged ci-cd + shell.
  if (/^act\/scripts\/l2_.*_verify\.sh$/.test(p)) return 'layer:test';

  // --- infrastructure / deployment scripting --------------------------------
  // launch files, udev rules, vendor SDK install scripts, start scripts.
  if (/(^|\/)launch\/.*\.launch\.py$/.test(p)) return 'layer:infrastructure';
  if (/act_system\/scripts\/start_act_system\.sh$/.test(p)) return 'layer:infrastructure';
  if (/rm65_dual_arm\/lib\/install_libs\.sh$/.test(p)) return 'layer:infrastructure';
  if (/\.rules$/.test(n.name)) return 'layer:infrastructure'; // udev rules
  // ament resource markers + setup.py (build/packaging) -> infrastructure
  if (/(^|\/)resource\//.test(p)) return 'layer:infrastructure';
  if (/(^|\/)setup\.py$/.test(p)) return 'layer:infrastructure';

  // --- the act/ & elephant_gripper/ shared cross-cutting stack --------------
  // types/ subpackage -> Types layer
  if (/(^|\/)types\/[^/]*\.py$/.test(p) && !/(^|\/)tests?\//.test(p)) {
    return 'layer:types';
  }
  // config/ subpackage (schema.py, __init__.py barrels) -> Configuration layer
  // BUT we already routed `config:` typed files above. Handle the *file*-typed
  // schema.py / config barrels here.
  if (/(^|\/)elephant_gripper\/elephant_gripper\/config\//.test(p)) return 'layer:config';
  if (/^act\/config\//.test(p)) return 'layer:config';

  // repo/ subpackage (bundle/manifest/normalizer loaders) -> Service layer
  // These are the ACT resource/repository layer; collapsed into Service.
  if (/(^|\/)repo\/[^/]*\.py$/.test(p)) return 'layer:service';

  // service/ subpackage (inference, safety, frame_codec, mapping, etc.)
  if (/(^|\/)service\/[^/]*\.py$/.test(p)) return 'layer:service';

  // runtime/ subpackage (control loop, worker, supervisor, serial link)
  if (/(^|\/)runtime\/[^/]*\.py$/.test(p)) return 'layer:runtime';

  // ui/ subpackage (ROS nodes, publishers, observation pipeline) -> API/UI layer
  if (/(^|\/)ui\/[^/]*\.py$/.test(p)) return 'layer:ui';

  // --- rm65_dual_arm C++ sources & headers ----------------------------------
  // headers (.hpp) under include/ are declarations for the node + guards +
  // SDK wrapper + pose conversion. They are the node/service implementation
  // surface (analogous to act/ ui+service). Classify by role:
  if (/rm65_dual_arm\/include\//.test(p) || /rm65_dual_arm\/src\//.test(p)) {
    // *_guard.* and target_validator.* are safety/validation -> Service layer
    // pose_conversion.* is a pure utility -> Service layer (math/serialization)
    // rm65_arm.* is the SDK hardware wrapper -> Service layer
    // rm65_dual_arm_node.* is the ROS node -> UI/API layer
    if (/rm65_dual_arm_node\.(hpp|cpp)$/.test(p)) return 'layer:ui';
    return 'layer:service';
  }

  // --- dual_fisheye_camera --------------------------------------------------
  // camera_health_node.py is the ROS node -> UI/API layer
  if (/dual_fisheye_camera\/dual_fisheye_camera\/camera_health_node\.py$/.test(p)) {
    return 'layer:ui';
  }
  // dual_fisheye package __init__.py marker -> Config (packaging) — small, fold into Config.
  if (/dual_fisheye_camera\/dual_fisheye_camera\/__init__\.py$/.test(p)) {
    return 'layer:config';
  }

  // --- package markers / barrels / root files ------------------------------
  // __init__.py barrels and package roots -> fold into Configuration (they are
  // packaging/structure concerns). act/__init__.py, act/<sub>/__init__.py,
  // elephant_gripper/__init__.py, root __init__.py.
  if (n.name === '__init__.py') return 'layer:config';

  // Root-level gripper_ctrl.py CLI debug script -> Infrastructure (tooling)
  if (p === 'gripper_ctrl.py') return 'layer:infrastructure';

  // .understandignore tooling config -> Configuration
  if (/\.ua\/\.understandignore$/.test(p)) return 'layer:config';

  // --- fallback -------------------------------------------------------------
  return 'layer:utility';
}

// ---------------------------------------------------------------------------
// Assign every node
// ---------------------------------------------------------------------------
const layers = {
  'layer:ui': {
    name: 'ROS 节点与适配层 (UI/API)',
    description:
      'ROS 2 节点与对外适配组件，是工作空间中唯一导入 rclpy / rclcpp 的层：负责 ROS 消息与 RAM 类型互转、topic/service 订阅发布、定时器驱动的控制循环装配与生命周期管理，涵盖 ACT 部署组合根、动作发布器、观测 ROS 适配器、相机健康节点与 RM65 双臂节点。',
    nodeIds: [],
  },
  'layer:runtime': {
    name: '运行时调度层',
    description:
      '进程内运行时中枢，将推理执行与控制解耦：包含 ACT 控制环、推理 worker/信道、观测缓冲与运行时指标，以及 elephant_gripper 的串行链路工作线程与双夹爪 supervisor，负责 tick 调度、chunk 接受/丢弃、急停与指数退避重连。',
    nodeIds: [],
  },
  'layer:service': {
    name: '服务与领域逻辑层',
    description:
      'ROS 解耦的核心业务/领域逻辑：ACT 推理服务、观测批处理与采集、安全守卫、动作后处理与输出适配、bundle/manifest/normalizer 仓库加载，以及 elephant_gripper 的 Modbus 帧编解码、健康聚合、许可门控与宽度-角度映射，外加 RM65 的安全闸、目标校验与厂商 SDK 封装。',
    nodeIds: [],
  },
  'layer:types': {
    name: '类型与契约层',
    description:
      '跨模块共享的冻结数据类与契约定义：ACT 的动作/观测/状态规范、安全与发布结果类型、ActionChunk 值对象，以及 elephant_gripper 的侧别枚举、健康等级与命令许可 dataclass，作为各层之间唯一的内存数据契约。',
    nodeIds: [],
  },
  'layer:config': {
    name: '配置与构建清单层',
    description:
      '部署参数与 ROS2 包构建清单：各包 package.xml/setup.cfg、deploy.yaml 与节点参数 YAML、conda/pip 环境定义、L2 测试 fixture、Understand-Anything 工具配置，以及 act/ 与 elephant_gripper/ 的配置 schema 模块与 __init__.py 包结构标记。',
    nodeIds: [],
  },
  'layer:ros-interface': {
    name: 'ROS 消息接口层',
    description:
      'act_interfaces 自定义 ROS2 消息定义（.msg）：CommandPermit 人类许可令牌、GripperHealth 与 HardwareHealth 硬件健康总线，作为跨节点通信的 schema 契约，由 rosidl 生成对应语言绑定。',
    nodeIds: [],
  },
  'layer:test': {
    name: '测试与验收层',
    description:
      'pytest 单元测试、L2 集成门测试、GoogleTest C++ 测试、conftest 引导与 L2_*_verify.sh 验收脚本，覆盖类型契约、配置校验、推理链路、安全闸、控制环、动作发布与全栈集成门，断言层间边界与 fail-closed 语义。',
    nodeIds: [],
  },
  'layer:infrastructure': {
    name: '部署与启动基础设施层',
    description:
      'ROS2 launch 编排、一键启动脚本、act_system 总 launch 入口、vendor SDK 部署脚本、udev 设备规则、ament_index 资源标记、各包 setup.py 构建脚本与 gripper_ctrl CLI 调试工具，负责把多个节点组装成可运行的部署栈。',
    nodeIds: [],
  },
  'layer:documentation': {
    name: '文档层',
    description:
      '工作空间与各 ROS2 包的说明文档：ENVIRONMENT.md 环境与构建说明、各包 README、elephant_gripper 分层架构设计文档、CMakeLists.txt 构建清单描述与厂商 SDK 取用指引。',
    nodeIds: [],
  },
  'layer:utility': {
    name: '工具层',
    description:
      '兜底层：尚未被其它规则覆盖的通用工具与辅助文件（本项目按当前结构基本为空）。',
    nodeIds: [],
  },
};

const assignment = {}; // id -> layerId
for (const n of nodes) {
  const lid = classify(n);
  assignment[n.id] = lid;
  layers[lid].nodeIds.push(n.id);
}

// ---------------------------------------------------------------------------
// Self-checks
// ---------------------------------------------------------------------------
const errors = [];

// 1. full coverage + exactly one layer each
const seen = new Map(); // id -> count
for (const n of nodes) seen.set(n.id, 0);
for (const [lid, layer] of Object.entries(layers)) {
  for (const id of layer.nodeIds) {
    seen.set(id, (seen.get(id) || 0) + 1);
    // validate id exists in input
    if (!idToNode.has(id)) {
      errors.push(`layer ${lid} references unknown node id: ${id}`);
    }
  }
}
for (const [id, c] of seen) {
  if (c === 0) errors.push(`UNASSIGNED node: ${id}`);
  if (c > 1) errors.push(`DUPLICATE node (${c}x): ${id}`);
}

// 2. total count
const totalAssigned = Object.values(layers).reduce(
  (s, l) => s + l.nodeIds.length,
  0
);
if (totalAssigned !== nodes.length) {
  errors.push(
    `COUNT MISMATCH: assigned ${totalAssigned} but input has ${nodes.length}`
  );
}

// 3. layer count in [3,10], no empty layers included
const nonEmpty = Object.values(layers).filter((l) => l.nodeIds.length > 0);
if (nonEmpty.length < 3 || nonEmpty.length > 10) {
  errors.push(`LAYER COUNT out of [3,10]: ${nonEmpty.length}`);
}

// Drop empty layers from output (utility fallback expected empty here).
const out = Object.entries(layers)
  .filter(([, l]) => l.nodeIds.length > 0)
  .map(([id, l]) => ({ id, name: l.name, description: l.description, nodeIds: l.nodeIds }));

// 4. report per-layer counts
const counts = {};
for (const l of out) counts[l.id] = l.nodeIds.length;

if (errors.length) {
  console.error('SELF-CHECK FAILED:');
  for (const e of errors) console.error('  - ' + e);
  process.exit(1);
}

fs.writeFileSync(OUTPUT_PATH, JSON.stringify(out, null, 2), 'utf8');
console.log('OK layers=' + out.length + ' total=' + totalAssigned);
console.log('per-layer:', JSON.stringify(counts, null, 2));
process.exit(0);
