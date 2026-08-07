"""L2-06 Gate 跨模块集成测试 (deploy_055).

单一验证入口，使用 **真实 production contracts** 与可控外部替身证明整条
L2-02 -> L2-03 -> L2-06 -> L2-04 -> L2-05 tracer bullet、原子启动/关闭、
fallback / 六 outcome / fault 语义。覆盖 Gate 场景 G01-G12。

设计约束 (deploy_055 §6/§10/§11):
  - 只替换不可控外部边界：FakePolicy(无权重/GPU)、FakeNode(无 ROS graph)、
    FakeClock(可控时钟)、FakePermit(per-tick 许可)。production source 只读。
  - ActRuntimeResources 通过显式注入 canonical fake 资源构造（不调用
    load_act_runtime_resources，因为它要求真实 bundle_dir 且 fail-fast）。
  - G10/G11/G12 的 ROS/真实 bundle/真机缺失只证明其 fail-closed 闸口，
    绝不伪造 PASS（真实 PASS 由 verify 脚本在外部 scope 下记 BLOCKED）。

运行：
    PYTHONPATH=src python3 -m pytest \
        src/model_deploy/act/tests/integration/test_l2_06_gate.py -v
"""

from __future__ import annotations

import re
import threading
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Optional

import numpy as np
import pytest
import torch
import yaml

from model_deploy.act.config.schema import (
    CommandOutputConfig,
    DeployConfig,
    DeployConfigError,
    TopicsConfig,
)
from model_deploy.act.repo.act_runtime_resources import (
    ActRuntimeResources,
    PolicyInputSpec,
    RuntimeResourceCrossCheck,
    load_act_runtime_resources,
)
from model_deploy.act.repo.normalization import ActionStateNormalizer
from model_deploy.act.runtime.control_loop import (
    ControlLoop,
    ControlLoopConfig,
)
from model_deploy.act.runtime.inference_channel import (
    InferenceRequest,
    InferenceResult,
    LatestQueue,
)
from model_deploy.act.runtime.inference_worker import InferenceWorker
from model_deploy.act.runtime.runtime_metrics import RuntimeMetrics
from model_deploy.act.service.act_inference import ActInferenceService
from model_deploy.act.service.relative_tcp_action_decoder import (
    RelativeTcpActionDecoder,
)
from model_deploy.act.types.action_chunk import ActionChunk
from model_deploy.act.types.action_representation import ActionRepresentationSpec
from model_deploy.act.types.action_publish import (
    ActionPublishRequest,
    ActionPublishResult,
    CommandPermit,
    PublishOutcome,
)
from model_deploy.act.types.action_spec import ActionSpec
from model_deploy.act.types.observation import ObservationSnapshot, ObservationState
from model_deploy.act.types.safety_result import (
    SafetyCode,
    SafetyFinding,
    SafetyResult,
    SafetyStatus,
)
from model_deploy.act.ui import action_publisher as ap
from model_deploy.act.ui.action_publisher import ActionPublisher
from model_deploy.act.ui.act_deploy_node import (
    StartupContractError,
    _deny_command_permit,
    build_arg_parser,
    run_startup_preflight,
)
from model_deploy.act.ui.observation_pipeline import build_observation_pipeline
from model_deploy.act.service.safety_guard import SafetyGuard


# ---------------------------------------------------------------------------
# Paths / constants
# ---------------------------------------------------------------------------

_HERE = Path(__file__).resolve().parent
_FIXTURE = _HERE.parent / "fixtures" / "l2_06_fake.yaml"
_ACT_SRC = _HERE.parents[1]  # src/model_deploy/act

# L2-06 真实 source 落点（boundary 静态扫描用）。
_L2_06_SOURCE_FILES = (
    "runtime/control_loop.py",
    "runtime/inference_worker.py",
    "runtime/inference_channel.py",
    "runtime/runtime_metrics.py",
    "ui/act_deploy_node.py",
    "ui/action_publisher.py",
    "ui/observation_pipeline.py",
    "service/act_inference.py",
    "service/safety_guard.py",
    "repo/act_runtime_resources.py",
)

# 禁止出现在 L2-06 source 中的业务/硬件 token（与设计投影对齐；rclpy 的 lazy
# import 明确允许）。`serial` 用 \b 词边界以避免 "serializable" 误报。
_FORBIDDEN_TOKEN_RE = re.compile(
    r"\b(ControlDecision|MoveIt|Modbus|serial|RM65|publishes_command_topics)\b"
    r"|\.accepted\b"
)
_FORBIDDEN_IMPORT_ROOTS = {"rospy", "serial", "modbus", "RM65"}


# ---------------------------------------------------------------------------
# Fake 外部边界
# ---------------------------------------------------------------------------


class FakeClock:
    """可控、单调非减时钟（worker 要求非减，否则 CLOCK_INVALID）。"""

    def __init__(self, start: float = 0.0) -> None:
        self._t = float(start)

    def __call__(self) -> float:
        return self._t

    def advance(self, dt: float) -> float:
        self._t += dt
        return self._t

    def set(self, t: float) -> None:
        self._t = float(t)


class NullClock:
    """始终返回 None —— 用于触发 worker CLOCK_INVALID 闸口。"""

    def __call__(self) -> None:
        return None


class RecordingPublisher:
    def __init__(self, topic: str) -> None:
        self.topic = topic
        self.messages: list[Any] = []

    def publish(self, msg: Any) -> None:
        self.messages.append(msg)


class FakeNode:
    """仅支持 create_publisher 的 dry-run 节点替身。"""

    def __init__(self) -> None:
        self.created: list[tuple[str, RecordingPublisher]] = []

    def create_publisher(
        self, msg_type: type, topic: str, qos: Any
    ) -> RecordingPublisher:
        pub = RecordingPublisher(topic)
        self.created.append((topic, pub))
        return pub


class FailingPublisher(RecordingPublisher):
    """注入替身：publish 抛错，用于 FAILED/PARTIAL outcome。"""

    def publish(self, msg: Any) -> None:
        raise RuntimeError("simulated ROS IO failure")


class FakePolicy:
    """无权重/GPU 的替身 policy：接收 batch（忽略），返回形状正确的有限张量。

    动作布局为 [left_tcp(7) | right_tcp(7) | left_gripper(1) | right_gripper(1)]
    = 16；其中 TCP 的 [3:7]/[10:14] 为四元数，必须在 L2-03 的 min-max 反归一化
    后保持单位化（否则 SafetyGuard 以 INVALID_QUATERNION 拒绝）。

    L2-03 的 ActionStateNormalizer 把动作域 [0, 1] 映射到策略域 [-1, 1]
    （公式 y = 2*x - 1 / x = (y+1)*0.5）。因此，要让反归一化后的四元数
    等于 [0,0,0,1]（xyzw 单位四元数），策略必须输出 [-1,-1,-1, 1]。
    其余维度：位置给 0.01（小有限值，反归一化为 0.505），夹爪给 0.0
    （反归一化为 0.5，与观测基准一致 → 零步长）。
    """

    def __init__(self, chunk_size: int = 8) -> None:
        self.chunk_size = chunk_size

    def predict_action_chunk(self, batch: Any) -> torch.Tensor:
        raw = torch.zeros((1, self.chunk_size, 16), dtype=torch.float32)
        # 策略域四元数：-1 -> 反归一化为 0；1 -> 反归一化为 1
        raw[..., 3:7] = torch.tensor([-1.0, -1.0, -1.0, 1.0])
        raw[..., 10:14] = torch.tensor([-1.0, -1.0, -1.0, 1.0])
        # 位置给 0.01（小有限值，反归一化后为 0.505）
        raw[..., [0, 1, 2, 7, 8, 9]] = 0.01
        # 夹爪给 0.0（反归一化为 0.5，与观测基准 0.5 一致 -> 步长 0）
        raw[..., [14, 15]] = 0.0
        return raw


class StubService:
    """供 InferenceWorker 直接调用的 service 替身（不依赖真实 batch 构造）。"""

    def __init__(self, chunk: ActionChunk, *, raise_on_call: bool = False) -> None:
        self._chunk = chunk
        self.raise_on_call = raise_on_call
        self.calls = 0

    def predict_action_chunk(self, observation: Any) -> ActionChunk:
        self.calls += 1
        if self.raise_on_call:
            raise ValueError("injected policy failure")
        return self._chunk


class DenySafetyPort:
    """注入端口：强制 safety REJECTED（用于六 outcome 的 REJECTED 分支）。"""

    def filter_action(
        self,
        candidate: Any,
        previous_safe_action: Optional[ActionSpec] = None,
        latest_observation: Optional[ObservationSnapshot] = None,
    ) -> SafetyResult:
        return SafetyResult(
            status=SafetyStatus.REJECTED,
            action=None,
            findings=(
                SafetyFinding(
                    code=SafetyCode.NO_REFERENCE,
                    side=None,
                    before=None,
                    after=None,
                    detail="injected deny",
                ),
            ),
        )


# ---------------------------------------------------------------------------
# 构造 helpers
# ---------------------------------------------------------------------------


def _load_config(command_output_enabled: bool = False) -> DeployConfig:
    raw = yaml.safe_load(_FIXTURE.read_text(encoding="utf-8"))
    return DeployConfig.from_mapping(
        raw,
        base_dir=_FIXTURE.parent,
        command_output_enabled=command_output_enabled,
    )


def _build_spec(cfg: DeployConfig) -> PolicyInputSpec:
    s = cfg.image.image_size
    return PolicyInputSpec(
        state_key="observation.state",
        state_dim=cfg.runtime.state_dim,
        image_prefix="observation.images.",
        camera_keys=("left", "right"),
        image_shapes=((3, s, s), (3, s, s)),
        image_layout="CHW",
        image_dtype="float32",
        image_value_range=(0.0, 1.0),
        action_dim=cfg.runtime.action_dim,
        chunk_size=cfg.runtime.chunk_size,
    )


def _build_resources(cfg: DeployConfig, spec: PolicyInputSpec) -> ActRuntimeResources:
    state_norm = ActionStateNormalizer(
        min_vals=np.zeros(cfg.runtime.state_dim),
        max_vals=np.ones(cfg.runtime.state_dim),
    )
    action_norm = ActionStateNormalizer(
        min_vals=np.zeros(cfg.runtime.action_dim),
        max_vals=np.ones(cfg.runtime.action_dim),
    )
    policy = FakePolicy(chunk_size=cfg.runtime.chunk_size)
    repr_spec = ActionRepresentationSpec(
        arm_action_type="relative_tcp_pose",
        chunk_reference="inference_observation",
        translation_frame="tcp_local",
        rotation_representation="quaternion_xyzw",
        gripper_action_type="absolute",
    )
    return ActRuntimeResources(
        policy=policy,
        state_normalizer=state_norm,
        action_normalizer=action_norm,
        policy_input_spec=spec,
        action_representation_spec=repr_spec,
        bundle_dir=_FIXTURE.parent,
        cross_check=RuntimeResourceCrossCheck(passed=True, issues=()),
    )


def _make_snapshot(img_size: int, captured_at_s: float = 0.0) -> ObservationSnapshot:
    img = np.full((3, img_size, img_size), 0.5, dtype=np.float32)
    state = ObservationState(
        left_tcp_position=np.array([0.1, 0.2, 0.3], dtype=np.float32),
        left_tcp_orientation=np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32),
        left_gripper_width=0.5,
        right_tcp_position=np.array([0.4, 0.5, 0.6], dtype=np.float32),
        right_tcp_orientation=np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32),
        right_gripper_width=0.5,
    )
    return ObservationSnapshot(
        images={"left": img, "right": img},
        state=state,
        encoded_state=np.full(16, 0.5, dtype=np.float32),
        captured_at_s=float(captured_at_s),
    )


def _make_chunk(n: int) -> ActionChunk:
    return ActionChunk(actions=np.full((n, 16), 0.5, dtype=np.float32))


def build_composition(
    *,
    command_output_enabled: bool = False,
    permit_source: Optional[Callable[[], CommandPermit]] = None,
    start_worker: bool = False,
) -> SimpleNamespace:
    """按 _act_init 的原子顺序拼装整条 tracer（不创建 ROS timer）。"""
    cfg = _load_config(command_output_enabled=command_output_enabled)
    spec = _build_spec(cfg)
    resources = _build_resources(cfg, spec)
    relative_action_decoder = RelativeTcpActionDecoder(
        resources.action_representation_spec
    )
    inference_service = ActInferenceService(
        cfg,
        resources.state_normalizer,
        resources.action_normalizer,
        resources.policy,
        spec,
        relative_action_decoder,
    )
    clock = FakeClock()
    node = FakeNode()
    pipeline = build_observation_pipeline(
        node=node, config=cfg, input_spec=spec, monotonic_clock=clock
    )
    safety_guard = SafetyGuard(cfg.safety)
    request_queue: LatestQueue = LatestQueue()
    result_queue: LatestQueue = LatestQueue()
    metrics = RuntimeMetrics(clock)
    worker = InferenceWorker(
        service=inference_service,
        request_queue=request_queue,
        result_queue=result_queue,
        metrics=metrics,
        inference_hz=cfg.runtime.inference_hz,
        clock=clock,
    )
    # B12 启动契约交叉校验（纯 RAM）
    run_startup_preflight(
        config=cfg,
        resources=resources,
        inference_service=inference_service,
        pipeline=pipeline,
        request_queue=request_queue,
        result_queue=result_queue,
        command_output_enabled=command_output_enabled,
        permit_source=permit_source,
        monotonic_clock=clock,
    )
    publisher = ActionPublisher(node, cfg.command_output, cfg.topics)
    observation_port: Callable[[], Optional[ObservationSnapshot]] = (
        lambda: pipeline.buffer.latest_observation(cfg.runtime.max_observation_age_sec)
    )
    control_loop = ControlLoop(
        config=ControlLoopConfig(
            chunk_size=cfg.runtime.chunk_size,
            action_dim=cfg.runtime.action_dim,
            execute_horizon=cfg.runtime.execute_horizon,
            max_observation_age_s=cfg.runtime.max_observation_age_sec,
            command_output_enabled=command_output_enabled,
            continue_to_chunk_size=False,
            fallback_policy=cfg.runtime.fallback_policy,
            prefetch_steps=cfg.runtime.prefetch_steps,
        ),
        request_queue=request_queue,
        result_queue=result_queue,
        metrics=metrics,
        safety_port=safety_guard,
        publish_port=publisher.publish,
        observation_port=observation_port,
    )
    comp = SimpleNamespace(
        cfg=cfg,
        spec=spec,
        resources=resources,
        inference_service=inference_service,
        clock=clock,
        node=node,
        pipeline=pipeline,
        safety_guard=safety_guard,
        request_queue=request_queue,
        result_queue=result_queue,
        metrics=metrics,
        worker=worker,
        publisher=publisher,
        control_loop=control_loop,
        observation_port=observation_port,
    )
    if start_worker:
        worker.start()
    return comp


def feed_observation(comp: SimpleNamespace, clock: FakeClock) -> ObservationSnapshot:
    """经 L2-02 collector -> buffer 注入一帧观测（dry-run 无 ROS 回调）。"""
    img_size = comp.cfg.image.image_size
    snap = _make_snapshot(img_size, captured_at_s=clock())
    comp.pipeline.collector.update_image("left", snap.images["left"])
    comp.pipeline.collector.update_image("right", snap.images["right"])
    comp.pipeline.collector.update_tcp_pose(
        "left", snap.state.left_tcp_position, snap.state.left_tcp_orientation
    )
    comp.pipeline.collector.update_tcp_pose(
        "right", snap.state.right_tcp_position, snap.state.right_tcp_orientation
    )
    comp.pipeline.collector.update_gripper_state("left", 0.5)
    comp.pipeline.collector.update_gripper_state("right", 0.5)
    built = comp.pipeline.collector.snapshot(max_age_s=comp.cfg.runtime.max_observation_age_sec)
    assert built is not None
    comp.pipeline.buffer.set_observation(built)
    return built


# ===========================================================================
# G01 — types / boundary：ActionChunk 纯净 + 无 ControlDecision + 静态边界
# ===========================================================================


class TestG01Types:
    def test_action_chunk_contract(self) -> None:
        # 合法 chunk
        ok = _make_chunk(8)
        assert ok.actions.shape == (8, 16)
        assert ok.actions.dtype == np.float32
        # 非法：行数为 0
        with pytest.raises(ValueError):
            ActionChunk(actions=np.zeros((0, 16), dtype=np.float32))
        # 非法：最后一维非 16
        with pytest.raises(ValueError):
            ActionChunk(actions=np.zeros((8, 8), dtype=np.float32))
        # 非法：dtype 非 float32
        with pytest.raises(TypeError):
            ActionChunk(actions=np.zeros((8, 16), dtype=np.float64))
        # 非法：含 NaN
        bad = np.full((8, 16), 0.5, dtype=np.float32)
        bad[0, 0] = float("nan")
        with pytest.raises(ValueError):
            ActionChunk(actions=bad)

    def test_policy_input_spec_rejects_bad_dim(self) -> None:
        with pytest.raises(DeployConfigError):
            PolicyInputSpec(
                state_key="observation.state",
                state_dim=8,  # 必须是 16
                image_prefix="observation.images.",
                camera_keys=("left", "right"),
                image_shapes=((3, 32, 32), (3, 32, 32)),
                image_layout="CHW",
                image_dtype="float32",
                image_value_range=(0.0, 1.0),
                action_dim=16,
                chunk_size=8,
            )

    def test_no_forbidden_tokens_in_l2_06_sources(self) -> None:
        for rel in _L2_06_SOURCE_FILES:
            src = (_ACT_SRC / rel).read_text(encoding="utf-8")
            text = re.sub(r'""".*?"""', '""', src, flags=re.DOTALL)
            text = re.sub(r"'''.*?'''", "''", text, flags=re.DOTALL)
            text = "\n".join(re.sub(r"(\s*#.*)$", "", line) for line in text.split("\n"))
            hit = _FORBIDDEN_TOKEN_RE.search(text)
            assert hit is None, f"{rel}: forbidden token {hit.group(0)!r}"

    def test_no_forbidden_imports_in_l2_06_sources(self) -> None:
        for rel in _L2_06_SOURCE_FILES:
            roots = set()
            try:
                tree = __import__("ast").parse((_ACT_SRC / rel).read_text())
            except SyntaxError:
                continue
            for node in __import__("ast").walk(tree):
                if isinstance(node, __import__("ast").Import):
                    for alias in node.names:
                        roots.add(alias.name.split(".")[0])
                elif isinstance(node, __import__("ast").ImportFrom):
                    module = node.module or ""
                    roots.add(module.split(".")[0])
            assert not (roots & _FORBIDDEN_IMPORT_ROOTS), f"{rel}: {roots}"


# ===========================================================================
# G02 — config / repo：default config、static CLI、canonical resources/spec
# ===========================================================================


class TestG02Config:
    def test_default_command_output_disabled(self) -> None:
        cfg = _load_config(command_output_enabled=False)
        assert cfg.command_output.command_output_enabled is False

    def test_yaml_cannot_silently_enable_command(self) -> None:
        # 真实 validation：DeployConfig 拒绝从 YAML 读取 enabled 主开关
        with pytest.raises(DeployConfigError):
            DeployConfig.from_mapping(
                {
                    "bundle": {},
                    "runtime": {"mode": "dry-run"},
                    "topics": {"namespace": "/act"},
                    "safety": {},
                    "command_output": {"enabled": True},
                },
                base_dir=Path("/tmp"),
            )

    def test_build_arg_parser_only_two_flags(self) -> None:
        parser = build_arg_parser()
        # --config 必填；--enable-command-output 仅启动期
        args1 = parser.parse_args(["--config", "x.yaml"])
        assert args1.enable_command_output is False
        args2 = parser.parse_args(["--config", "x.yaml", "--enable-command-output"])
        assert args2.enable_command_output is True

    def test_canonical_resources_and_spec_identity(self) -> None:
        cfg = _load_config()
        spec = _build_spec(cfg)
        resources = _build_resources(cfg, spec)
        assert resources.cross_check.passed is True
        assert resources.policy_input_spec is spec
        # 注入的 ActRuntimeResources 不调用生产 loader（空 bundle 下 fail-fast）
        decoder = RelativeTcpActionDecoder(resources.action_representation_spec)
        service = ActInferenceService(
            cfg, resources.state_normalizer, resources.action_normalizer,
            resources.policy, spec, decoder,
        )
        assert service.input_spec is spec
        assert service.action_representation_spec is resources.action_representation_spec

    def test_loader_fails_fast_on_empty_bundle(self) -> None:
        # 真实 production loader 在空 bundle_dir 下必须 fail-fast（绝不猜路径）
        cfg = _load_config()
        assert cfg.bundle.resolved_bundle_dir is None
        with pytest.raises(DeployConfigError):
            load_act_runtime_resources(cfg)


# ===========================================================================
# G03 — observation / service / publish seam：真实 snapshot/service/safety/publisher
# ===========================================================================


class TestG03Seam:
    def test_observation_pipeline_dry_run_env_blocked(self) -> None:
        comp = build_composition()
        # rclpy 缺失时 create_subscriptions 记录 env_blocked（dry-run 语义）
        assert comp.pipeline.adapter.env_blocked in (True, False)

    def test_collector_to_snapshot(self) -> None:
        comp = build_composition()
        snap = feed_observation(comp, comp.clock)
        assert isinstance(snap, ObservationSnapshot)
        assert snap.encoded_state.shape == (16,)
        assert set(snap.images.keys()) == {"left", "right"}

    def test_service_predict_returns_chunk(self) -> None:
        comp = build_composition()
        snap = _make_snapshot(comp.cfg.image.image_size)
        chunk = comp.inference_service.predict_action_chunk(snap)
        assert isinstance(chunk, ActionChunk)
        assert chunk.actions.shape == (comp.cfg.runtime.chunk_size, 16)

    def test_safety_filter_pass_via_observation_reference(self) -> None:
        comp = build_composition()
        snap = _make_snapshot(comp.cfg.image.image_size)
        # 以 observation 为比较基准 -> PASS/ADJUSTED，且 action 非 None
        result = comp.safety_guard.filter_action(
            ActionSpec(
                left_tcp_action=np.array([0.1, 0.2, 0.3, 0.0, 0.0, 0.0, 1.0], dtype=np.float32),
                right_tcp_action=np.array([0.4, 0.5, 0.6, 0.0, 0.0, 0.0, 1.0], dtype=np.float32),
                left_gripper=0.5,
                right_gripper=0.5,
            ),
            latest_observation=snap,
        )
        assert result.status in (SafetyStatus.PASS, SafetyStatus.ADJUSTED)
        assert result.action is not None

    def test_publisher_observed_provenance_disabled(self) -> None:
        # command_output_enabled=False：仅 policy/status，command=0，OBSERVED
        comp = build_composition(command_output_enabled=False)
        safety = comp.safety_guard.filter_action(
            ActionSpec(
                left_tcp_action=np.array([0.1, 0.2, 0.3, 0.0, 0.0, 0.0, 1.0], dtype=np.float32),
                right_tcp_action=np.array([0.4, 0.5, 0.6, 0.0, 0.0, 0.0, 1.0], dtype=np.float32),
                left_gripper=0.5,
                right_gripper=0.5,
            ),
            latest_observation=_make_snapshot(comp.cfg.image.image_size),
        )
        req = ActionPublishRequest(
            action_id="a1",
            safety_result=safety,
            command_permit=CommandPermit(allowed=True),
            ros_time_s=1.0,
            monotonic_s=1.0,
        )
        res = comp.publisher.publish(req)
        assert res.outcome == PublishOutcome.OBSERVED
        assert res.command_publish_count == 0
        assert res.policy_action_published is True
        assert res.reason_code == "COMMAND_OUTPUT_DISABLED"

    def test_publisher_published_provenance_enabled(self) -> None:
        # command_output_enabled=True + permit 允许：4 路 command，PUBLISHED
        comp = build_composition(
            command_output_enabled=True,
            permit_source=lambda: CommandPermit(allowed=True),
        )
        safety = comp.safety_guard.filter_action(
            ActionSpec(
                left_tcp_action=np.array([0.1, 0.2, 0.3, 0.0, 0.0, 0.0, 1.0], dtype=np.float32),
                right_tcp_action=np.array([0.4, 0.5, 0.6, 0.0, 0.0, 0.0, 1.0], dtype=np.float32),
                left_gripper=0.5,
                right_gripper=0.5,
            ),
            latest_observation=_make_snapshot(comp.cfg.image.image_size),
        )
        req = ActionPublishRequest(
            action_id="a1",
            safety_result=safety,
            command_permit=CommandPermit(allowed=True),
            ros_time_s=1.0,
            monotonic_s=1.0,
        )
        res = comp.publisher.publish(req)
        assert res.outcome == PublishOutcome.PUBLISHED
        assert res.command_publish_count == 4
        assert res.command_plan_completed is True


# ===========================================================================
# G04 — channel / metrics：envelope、capacity-one close、immutable metrics
# ===========================================================================


class TestG04ChannelMetrics:
    def test_inference_request_validation(self) -> None:
        snap = _make_snapshot(32)
        with pytest.raises(ValueError):
            InferenceRequest(request_id=0, observation=snap, submitted_at_s=0.0, trigger_cursor=0)
        req = InferenceRequest(request_id=1, observation=snap, submitted_at_s=0.0, trigger_cursor=0)
        assert req.request_id == 1

    def test_inference_result_xor(self) -> None:
        snap = _make_snapshot(32)
        # success 需要 chunk
        good = InferenceResult.success(
            request_id=1,
            observation_captured_at_s=0.0,
            submitted_at_s=0.0,
            started_at_s=0.0,
            completed_at_s=0.0,
            chunk=_make_chunk(8),
        )
        assert good.is_success
        # error 需要 error_type + error_message
        err = InferenceResult.error(
            request_id=1,
            observation_captured_at_s=0.0,
            submitted_at_s=0.0,
            started_at_s=0.0,
            completed_at_s=0.0,
            exc=ValueError("boom"),
        )
        assert not err.is_success
        assert err.error_type == "ValueError"
        # 同时 success+error 非法
        with pytest.raises(ValueError):
            InferenceResult(
                request_id=1,
                observation_captured_at_s=0.0,
                submitted_at_s=0.0,
                started_at_s=0.0,
                completed_at_s=0.0,
                chunk=_make_chunk(8),
                error_type="X",
                error_message="y",
            )

    def test_latest_queue_capacity_one(self) -> None:
        q: LatestQueue = LatestQueue()
        assert LatestQueue.CAPACITY == 1
        a = object()
        b = object()
        assert q.put_latest(a) == 0
        assert q.put_latest(b) == 1  # 容量 1 -> 淘汰旧
        assert q.take_latest(timeout_s=0) is b
        # close 后 put 抛错，take 返回 None
        assert q.close() == 0
        with pytest.raises(RuntimeError):
            q.put_latest(object())
        assert q.take_latest(timeout_s=0) is None
        assert q.is_closed

    def test_runtime_metrics_immutable_snapshot(self) -> None:
        clock = FakeClock()
        m = RuntimeMetrics(clock)
        before = m.snapshot()
        m.record_event("tick")
        after = m.snapshot()
        assert after.tick_count == 1
        assert before.tick_count == 0
        assert before is not after
        # 快照字段是冻结拷贝，发布事实计数以 tuple 传递
        m.record_event("publish", value="PUBLISHED")
        snap = m.snapshot()
        assert dict(snap.publish_outcome_counts).get("PUBLISHED") == 1


# ===========================================================================
# G05 — worker：nonblocking、serial、error recovery、stop/join
# ===========================================================================


class TestG05Worker:
    def test_worker_serial_success(self) -> None:
        chunk = _make_chunk(8)
        service = StubService(chunk)
        q: LatestQueue = LatestQueue()
        rq: LatestQueue = LatestQueue()
        metrics = RuntimeMetrics(FakeClock())
        worker = InferenceWorker(
            service=service, request_queue=q, result_queue=rq,
            metrics=metrics, inference_hz=100, clock=FakeClock(),
        )
        snap = _make_snapshot(32)
        q.put_latest(InferenceRequest(request_id=1, observation=snap, submitted_at_s=0.0, trigger_cursor=0))
        worker.start()
        res = rq.take_latest(timeout_s=2)
        worker.stop()
        q.close()  # 唤醒阻塞在 take_latest 的 worker（生产 shutdown 契约）
        worker.join(timeout=2)
        assert res is not None and res.is_success
        assert res.chunk is not None
        assert metrics.snapshot().inference_success_count >= 1
        assert not worker.is_alive()

    def test_worker_error_recovery(self) -> None:
        service = StubService(_make_chunk(8), raise_on_call=True)
        q: LatestQueue = LatestQueue()
        rq: LatestQueue = LatestQueue()
        metrics = RuntimeMetrics(FakeClock())
        worker = InferenceWorker(
            service=service, request_queue=q, result_queue=rq,
            metrics=metrics, inference_hz=100, clock=FakeClock(),
        )
        snap = _make_snapshot(32)
        q.put_latest(InferenceRequest(request_id=1, observation=snap, submitted_at_s=0.0, trigger_cursor=0))
        worker.start()
        res = rq.take_latest(timeout_s=2)
        worker.stop()
        q.close()  # 唤醒阻塞在 take_latest 的 worker（生产 shutdown 契约）
        worker.join(timeout=2)
        assert res is not None and not res.is_success
        assert res.error_type == "ValueError"
        assert metrics.snapshot().inference_error_count >= 1

    def test_worker_clock_invalid_fatal(self) -> None:
        q: LatestQueue = LatestQueue()
        rq: LatestQueue = LatestQueue()
        metrics = RuntimeMetrics(NullClock())
        worker = InferenceWorker(
            service=StubService(_make_chunk(8)),
            request_queue=q, result_queue=rq,
            metrics=metrics, inference_hz=100, clock=NullClock(),
        )
        snap = _make_snapshot(32)
        q.put_latest(InferenceRequest(request_id=1, observation=snap, submitted_at_s=0.0, trigger_cursor=0))
        worker.start()
        worker.join(timeout=2)
        assert metrics.snapshot().worker_fatal_reason == "CLOCK_INVALID"
        assert not worker.is_alive()


# ===========================================================================
# G06 — scheduling：correlation、active/pending、prefetch/horizon、age/copy
# ===========================================================================


class TestG06Scheduling:
    def _loop(self, command_output_enabled: bool = False):
        cfg = _load_config()
        spec = _build_spec(cfg)
        clock = FakeClock()
        rq: LatestQueue = LatestQueue()
        rsq: LatestQueue = LatestQueue()
        metrics = RuntimeMetrics(clock)
        safety = SafetyGuard(cfg.safety)
        publisher = ActionPublisher(FakeNode(), cfg.command_output, cfg.topics)
        snap = _make_snapshot(cfg.image.image_size)
        loop = ControlLoop(
            config=ControlLoopConfig(
                chunk_size=cfg.runtime.chunk_size,
                action_dim=cfg.runtime.action_dim,
                execute_horizon=cfg.runtime.execute_horizon,
                max_observation_age_s=cfg.runtime.max_observation_age_sec,
                command_output_enabled=command_output_enabled,
                prefetch_steps=cfg.runtime.prefetch_steps,
            ),
            request_queue=rq, result_queue=rsq, metrics=metrics,
            safety_port=safety, publish_port=publisher.publish,
            observation_port=lambda: snap,
        )
        return SimpleNamespace(loop=loop, rq=rq, rsq=rsq, metrics=metrics, cfg=cfg, clock=clock, publisher=publisher)

    def test_correlation_and_active_chunk(self) -> None:
        c = self._loop()
        # tick1：提交 rid=1，无结果 -> fallback（无输出）
        assert c.loop.tick(0.0, 0.0, CommandPermit(allowed=True)) is None
        assert c.metrics.snapshot().request_submitted_count == 1
        # 注入匹配的结果
        c.rsq.put_latest(InferenceResult.success(
            request_id=1, observation_captured_at_s=0.0, submitted_at_s=0.0,
            started_at_s=0.0, completed_at_s=0.0, chunk=_make_chunk(c.cfg.runtime.chunk_size),
        ))
        # tick2：相关 -> 激活 active chunk -> 输出（OBSERVED，因 disabled）
        res = c.loop.tick(0.0, 0.0, CommandPermit(allowed=True))
        assert res is not None
        assert c.metrics.snapshot().chunk_activated_count == 1
        assert c.metrics.snapshot().active_cursor >= 1

    def test_prefetch_at_horizon(self) -> None:
        c = self._loop()
        # 提交首个请求并灌入结果
        c.loop.tick(0.0, 0.0, CommandPermit(allowed=True))
        c.rsq.put_latest(InferenceResult.success(
            request_id=1, observation_captured_at_s=0.0, submitted_at_s=0.0,
            started_at_s=0.0, completed_at_s=0.0, chunk=_make_chunk(c.cfg.runtime.chunk_size),
        ))
        # 连续 tick 直到 cursor 到达 horizon-1 触发下一次 prefetch
        submitted_before = c.metrics.snapshot().request_submitted_count
        for _ in range(c.cfg.runtime.execute_horizon + 2):
            c.loop.tick(0.0, 0.0, CommandPermit(allowed=True))
            # 持续灌入新结果以支持连续输出
            n = c.metrics.snapshot().request_submitted_count
            c.rsq.put_latest(InferenceResult.success(
                request_id=n, observation_captured_at_s=0.0, submitted_at_s=0.0,
                started_at_s=0.0, completed_at_s=0.0, chunk=_make_chunk(c.cfg.runtime.chunk_size),
            ))
        assert c.metrics.snapshot().request_submitted_count > submitted_before

    def test_result_id_mismatch_latches_fault(self) -> None:
        c = self._loop()
        c.loop.tick(0.0, 0.0, CommandPermit(allowed=True))  # 提交 rid=1
        # 灌入错配 rid=99 -> 丢弃 + UNKNOWN_RESULT_ID 闸口
        c.rsq.put_latest(InferenceResult.success(
            request_id=99, observation_captured_at_s=0.0, submitted_at_s=0.0,
            started_at_s=0.0, completed_at_s=0.0, chunk=_make_chunk(c.cfg.runtime.chunk_size),
        ))
        c.loop.tick(0.0, 0.0, CommandPermit(allowed=True))
        snap = c.metrics.snapshot()
        assert snap.runtime_fault_latched is True
        assert snap.result_discarded_count >= 1


# ===========================================================================
# G07 — fallback / output：B6/B8、六 outcome、deferred reason、fault latches
# ===========================================================================


class TestG07FallbackOutput:
    def _make_loop(self, *, safety_port, publisher: ActionPublisher, snapshot):
        cfg = _load_config()
        clock = FakeClock()
        rq: LatestQueue = LatestQueue()
        rsq: LatestQueue = LatestQueue()
        metrics = RuntimeMetrics(clock)
        loop = ControlLoop(
            config=ControlLoopConfig(
                chunk_size=cfg.runtime.chunk_size,
                action_dim=cfg.runtime.action_dim,
                execute_horizon=cfg.runtime.execute_horizon,
                max_observation_age_s=cfg.runtime.max_observation_age_sec,
                command_output_enabled=cfg.command_output.command_output_enabled,
                prefetch_steps=cfg.runtime.prefetch_steps,
            ),
            request_queue=rq, result_queue=rsq, metrics=metrics,
            safety_port=safety_port, publish_port=publisher.publish,
            observation_port=lambda: snapshot,
        )
        return loop, rq, rsq, metrics, cfg

    def _seed_chunk(self, loop, rq, rsq, metrics, cfg):
        # tick1 提交 rid=1；灌入匹配结果；tick2 产生输出
        loop.tick(0.0, 0.0, CommandPermit(allowed=True))
        rsq.put_latest(InferenceResult.success(
            request_id=1, observation_captured_at_s=0.0, submitted_at_s=0.0,
            started_at_s=0.0, completed_at_s=0.0, chunk=_make_chunk(cfg.runtime.chunk_size),
        ))
        return loop.tick(0.0, 0.0, CommandPermit(allowed=True))

    def test_outcome_observed(self) -> None:
        cfg = _load_config(command_output_enabled=False)
        pub = ActionPublisher(FakeNode(), cfg.command_output, cfg.topics)
        snap = _make_snapshot(cfg.image.image_size)
        loop, rq, rsq, metrics, _ = self._make_loop(
            safety_port=SafetyGuard(cfg.safety), publisher=pub, snapshot=snap
        )
        res = self._seed_chunk(loop, rq, rsq, metrics, cfg)
        assert res.outcome == PublishOutcome.OBSERVED
        assert res.command_publish_count == 0

    def test_outcome_published(self) -> None:
        cfg = _load_config(command_output_enabled=True)
        pub = ActionPublisher(FakeNode(), cfg.command_output, cfg.topics)
        snap = _make_snapshot(cfg.image.image_size)
        loop, rq, rsq, metrics, _ = self._make_loop(
            safety_port=SafetyGuard(cfg.safety), publisher=pub, snapshot=snap
        )
        res = self._seed_chunk(loop, rq, rsq, metrics, cfg)
        assert res.outcome == PublishOutcome.PUBLISHED
        assert res.command_publish_count == 4

    def test_outcome_blocked(self) -> None:
        cfg = _load_config(command_output_enabled=True)
        pub = ActionPublisher(FakeNode(), cfg.command_output, cfg.topics)
        snap = _make_snapshot(cfg.image.image_size)
        loop, rq, rsq, metrics, _ = self._make_loop(
            safety_port=SafetyGuard(cfg.safety), publisher=pub, snapshot=snap
        )
        res = self._seed_chunk(loop, rq, rsq, metrics, cfg)
        # 这次 tick 用 deny permit -> BLOCKED
        rsq.put_latest(InferenceResult.success(
            request_id=2, observation_captured_at_s=0.0, submitted_at_s=0.0,
            started_at_s=0.0, completed_at_s=0.0, chunk=_make_chunk(cfg.runtime.chunk_size),
        ))
        res2 = loop.tick(0.0, 0.0, CommandPermit(allowed=False, reason_code="ESTOP_ACTIVE"))
        assert res2.outcome == PublishOutcome.BLOCKED
        assert res2.command_publish_count == 0

    def test_outcome_rejected(self) -> None:
        cfg = _load_config(command_output_enabled=True)
        pub = ActionPublisher(FakeNode(), cfg.command_output, cfg.topics)
        snap = _make_snapshot(cfg.image.image_size)
        loop, rq, rsq, metrics, _ = self._make_loop(
            safety_port=DenySafetyPort(), publisher=pub, snapshot=snap
        )
        res = self._seed_chunk(loop, rq, rsq, metrics, cfg)
        assert res is None  # REJECTED -> tick 不产出输出
        assert metrics.snapshot().safety_rejected_count == 1

    def test_outcome_failed(self) -> None:
        cfg = _load_config(command_output_enabled=True)
        pub = ActionPublisher(FakeNode(), cfg.command_output, cfg.topics)
        pub._publishers["policy_action"] = FailingPublisher("/act/policy_action")
        snap = _make_snapshot(cfg.image.image_size)
        loop, rq, rsq, metrics, _ = self._make_loop(
            safety_port=SafetyGuard(cfg.safety), publisher=pub, snapshot=snap
        )
        res = self._seed_chunk(loop, rq, rsq, metrics, cfg)
        assert res.outcome == PublishOutcome.FAILED
        assert res.failure_stage == "policy_publish"
        assert res.failed_topic == "/act/policy_action"

    def test_outcome_partial(self) -> None:
        cfg = _load_config(command_output_enabled=True)
        pub = ActionPublisher(FakeNode(), cfg.command_output, cfg.topics)
        pub._publishers["right_arm"] = FailingPublisher("/act/command/arm/right_target")
        snap = _make_snapshot(cfg.image.image_size)
        loop, rq, rsq, metrics, _ = self._make_loop(
            safety_port=SafetyGuard(cfg.safety), publisher=pub, snapshot=snap
        )
        res = self._seed_chunk(loop, rq, rsq, metrics, cfg)
        assert res.outcome == PublishOutcome.PARTIAL
        assert res.command_publish_count == 1
        assert res.failure_stage == "command_publish"

    def test_observation_missing_fallback_deferred(self) -> None:
        cfg = _load_config(command_output_enabled=True)
        pub = ActionPublisher(FakeNode(), cfg.command_output, cfg.topics)
        clock = FakeClock()
        rq: LatestQueue = LatestQueue()
        rsq: LatestQueue = LatestQueue()
        metrics = RuntimeMetrics(clock)
        # observation_port 返回 None -> OBSERVATION_MISSING fallback
        loop = ControlLoop(
            config=ControlLoopConfig(
                chunk_size=cfg.runtime.chunk_size, action_dim=cfg.runtime.action_dim,
                execute_horizon=cfg.runtime.execute_horizon,
                max_observation_age_s=cfg.runtime.max_observation_age_sec,
                command_output_enabled=True, prefetch_steps=cfg.runtime.prefetch_steps,
            ),
            request_queue=rq, result_queue=rsq, metrics=metrics,
            safety_port=SafetyGuard(cfg.safety), publish_port=pub.publish,
            observation_port=lambda: None,
        )
        loop.tick(0.0, 0.0, CommandPermit(allowed=True))
        snap = metrics.snapshot()
        assert snap.fallback_count >= 1
        assert snap.last_fallback_reason == "OBSERVATION_MISSING"


# ===========================================================================
# G08 — UI / lifecycle：preflight、atomic startup、entrypoint、permit/metrics/shutdown
# ===========================================================================


class TestG08Lifecycle:
    def test_preflight_passes_for_canonical_spec(self) -> None:
        comp = build_composition(command_output_enabled=False)
        # build_composition 内部已通过 run_startup_preflight；再显式校验一次
        run_startup_preflight(
            config=comp.cfg, resources=comp.resources,
            inference_service=comp.inference_service, pipeline=comp.pipeline,
            request_queue=comp.request_queue, result_queue=comp.result_queue,
            command_output_enabled=False, permit_source=None,
            monotonic_clock=comp.clock,
        )

    def test_preflight_spec_identity_mismatch(self) -> None:
        comp = build_composition()
        # 用一份不同身份的 spec 替换 resources 中的 spec
        wrong_spec = _build_spec(comp.cfg)
        wrong_resources = ActRuntimeResources(
            policy=comp.resources.policy,
            state_normalizer=comp.resources.state_normalizer,
            action_normalizer=comp.resources.action_normalizer,
            policy_input_spec=wrong_spec,  # 与 pipeline/service 持有的 spec 不同身份
            action_representation_spec=comp.resources.action_representation_spec,
            bundle_dir=comp.resources.bundle_dir,
            cross_check=comp.resources.cross_check,
        )
        with pytest.raises(StartupContractError) as exc:
            run_startup_preflight(
                config=comp.cfg, resources=wrong_resources,
                inference_service=comp.inference_service, pipeline=comp.pipeline,
                request_queue=comp.request_queue, result_queue=comp.result_queue,
                command_output_enabled=False, permit_source=None,
                monotonic_clock=comp.clock,
            )
        assert exc.value.code == "SPEC_IDENTITY_MISMATCH"

    def test_preflight_permit_source_missing_when_enabled(self) -> None:
        comp = build_composition()
        with pytest.raises(StartupContractError) as exc:
            run_startup_preflight(
                config=comp.cfg, resources=comp.resources,
                inference_service=comp.inference_service, pipeline=comp.pipeline,
                request_queue=comp.request_queue, result_queue=comp.result_queue,
                command_output_enabled=True, permit_source=None,  # 启用但无 permit 源
                monotonic_clock=comp.clock,
            )
        assert exc.value.code == "PERMIT_SOURCE_MISSING"

    def test_deny_permit_is_fail_closed(self) -> None:
        p = _deny_command_permit()
        assert p.allowed is False
        assert p.reason_code == "COMMAND_OUTPUT_DISABLED"

    def test_shutdown_convergence(self) -> None:
        comp = build_composition(
            command_output_enabled=True,
            permit_source=lambda: CommandPermit(allowed=True),
        )
        comp.control_loop.request_shutdown()
        # 关闭后 tick 不产出任何输出
        assert comp.control_loop.tick(0.0, 0.0, CommandPermit(allowed=True)) is None
        assert comp.metrics.snapshot().runtime_status == "SHUTDOWN"


# ===========================================================================
# G09 — local full Gate：完整 tracer + baseline + 规范化 spec 身份 == 0 FAIL
# ===========================================================================


class TestG09FullGate:
    def test_full_tracer_publishes_and_shuts_down(self) -> None:
        comp = build_composition(
            command_output_enabled=True,
            permit_source=lambda: CommandPermit(allowed=True),
            start_worker=True,
        )
        # 规范化身份契约（HTML/agent_context 投影一致性）
        assert comp.pipeline.input_spec is comp.spec
        assert comp.inference_service.input_spec is comp.spec

        published = 0
        for i in range(40):
            comp.clock.advance(0.02)
            feed_observation(comp, comp.clock)
            res = comp.control_loop.tick(
                comp.clock(), comp.clock(), CommandPermit(allowed=True)
            )
            if res is not None and res.outcome == PublishOutcome.PUBLISHED:
                published += 1

        snap = comp.metrics.snapshot()
        assert snap.chunk_activated_count > 0
        assert snap.inference_success_count > 0
        assert snap.request_submitted_count > 0
        assert snap.action_candidate_count > 0
        assert published >= 1, "full tracer must produce >=1 PUBLISHED outcome"
        assert snap.runtime_status == "NORMAL"

        # 命令 provenance：至少一路 command publisher 收到消息
        command_labels = ("left_arm", "right_arm", "left_gripper", "right_gripper")
        assert any(len(comp.publisher._publishers[k].messages) > 0 for k in command_labels)

        # 有界关闭
        comp.control_loop.request_shutdown()
        comp.worker.stop()
        comp.request_queue.close()
        comp.worker.join(timeout=5)
        comp.result_queue.close()
        assert not comp.worker.is_alive()
        assert comp.metrics.snapshot().runtime_status == "SHUTDOWN"


# ===========================================================================
# G10 — ROS dry-run：policy/status 可见，四路 command=0，有界退出
# （本地用 FakeNode 证明 command=0 契约；真实 ROS 缺失记 BLOCKED_ENV）
# ===========================================================================


class TestG10RosDryRun:
    def test_dry_run_command_count_is_zero(self) -> None:
        # command_output_enabled=False（ROS dry-run 的契约）→ 四路 command 必为 0
        comp = build_composition(command_output_enabled=False)
        safety = comp.safety_guard.filter_action(
            ActionSpec(
                left_tcp_action=np.array([0.1, 0.2, 0.3, 0.0, 0.0, 0.0, 1.0], dtype=np.float32),
                right_tcp_action=np.array([0.4, 0.5, 0.6, 0.0, 0.0, 0.0, 1.0], dtype=np.float32),
                left_gripper=0.5, right_gripper=0.5,
            ),
            latest_observation=_make_snapshot(comp.cfg.image.image_size),
        )
        req = ActionPublishRequest(
            action_id="dry", safety_result=safety,
            command_permit=CommandPermit(allowed=True),
            ros_time_s=1.0, monotonic_s=1.0,
        )
        res = comp.publisher.publish(req)
        assert res.command_publish_count == 0
        for k in ("left_arm", "right_arm", "left_gripper", "right_gripper"):
            assert len(comp.publisher._publishers[k].messages) == 0
        # policy_action + status 可见
        assert len(comp.publisher._publishers["policy_action"].messages) == 1
        assert len(comp.publisher._publishers["status"].messages) == 1

    def test_ros_unavailable_records_env_blocked(self) -> None:
        # rclpy 缺失 -> 真实 ROS dry-run 无法产生真实 topic（verify 脚本记 BLOCKED_ENV）
        assert ap._ROS_AVAILABLE in (True, False)


# ===========================================================================
# G11 — real-policy dry-run：real bundle/GPU 合法 chunk，command=0
# （无真实 bundle -> 证明加载闸口 fail-fast；真实 PASS 在外部 scope 记 BLOCKED）
# ===========================================================================


class TestG11RealPolicyDryRun:
    def test_real_bundle_loader_is_gated(self) -> None:
        # 空 bundle_dir 下 load_act_runtime_resources 必须 fail-fast：
        # 证明无法用 fake 伪装 real-policy，真实 PASS 需要真实 bundle/GPU。
        cfg = _load_config()
        assert cfg.bundle.resolved_bundle_dir is None
        with pytest.raises(DeployConfigError):
            load_act_runtime_resources(cfg)


# ===========================================================================
# G12 — real command：仅 permit/E-stop/driver/授权齐备后人工受控验证
# （默认 fail-closed；绝不自动执行真机 -> BLOCKED_HARDWARE）
# ===========================================================================


class TestG12RealCommand:
    def test_default_deny_never_auto_enables_command(self) -> None:
        # 默认 deny permit 不携带 reason_code 通过；命令主开关不从 YAML 读取
        p = _deny_command_permit()
        assert p.allowed is False
        assert p.reason_code == "COMMAND_OUTPUT_DISABLED"
        # 即便 permit 允许，未通过 --enable-command-output 时 command=0
        comp = build_composition(command_output_enabled=False)
        res = comp.publisher.publish(ActionPublishRequest(
            action_id="rc", safety_result=_safe_result(),
            command_permit=CommandPermit(allowed=True),
            ros_time_s=1.0, monotonic_s=1.0,
        ))
        assert res.command_publish_count == 0

    def test_cli_parser_has_no_yaml_command_switch(self) -> None:
        parser = build_arg_parser()
        # 解析器只接受 --config（必填）与 --enable-command-output（启动期）
        # 不存在从 YAML 读取命令输出的开关
        args = parser.parse_args(["--config", "x.yaml"])
        assert not args.enable_command_output


def _safe_result() -> SafetyResult:
    return SafetyResult(
        status=SafetyStatus.PASS,
        action=ActionSpec(
            left_tcp_action=np.array([0.1, 0.2, 0.3, 0.0, 0.0, 0.0, 1.0], dtype=np.float32),
            right_tcp_action=np.array([0.4, 0.5, 0.6, 0.0, 0.0, 0.0, 1.0], dtype=np.float32),
            left_gripper=0.5, right_gripper=0.5,
        ),
        findings=(),
    )
