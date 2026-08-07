from __future__ import annotations

import pytest

from schemas.lerobot_features import (
    LeRobotFeatureConfigError,
    compile_lerobot_feature_contract,
    default_lerobot_features_config,
)


def test_v1_migrates_and_compiles_dynamic_layout() -> None:
    contract = compile_lerobot_feature_contract(
        {
            "schema_version": 1,
            "state_segments": [
                {"id": "right_tcp_pose", "enabled": True},
                {"id": "left_tcp_pose", "enabled": True},
            ],
            "action_segments": [
                {"id": "right_tcp_pose_t_plus_1", "enabled": True},
                {"id": "left_tcp_pose_t_plus_1", "enabled": True},
            ],
        }
    )
    assert contract.state_dim == 14
    assert contract.action_dim == 14
    assert contract.state.offsets["left_tcp_pose"] == (7, 14)
    assert contract.config["schema_version"] == 2


def test_v2_names_order_and_fingerprint_are_stable() -> None:
    config = default_lerobot_features_config()
    config["schema_version"] = 1
    config["state_segments"] = [
        item for item in config["state_segments"]
        if item["id"] in {"left_tcp_pose", "right_tcp_pose"}
    ]
    config["action_segments"] = [
        item for item in config["action_segments"]
        if item["id"] in {"left_tcp_pose_t_plus_1", "right_tcp_pose_t_plus_1"}
    ]
    first = compile_lerobot_feature_contract(config)
    second = compile_lerobot_feature_contract(config)
    assert first.fingerprint == second.fingerprint
    config["state_segments"][0]["dimension_names"][0] = "renamed.x"
    assert compile_lerobot_feature_contract(config).fingerprint != first.fingerprint


@pytest.mark.parametrize(
    "change",
    [
        lambda value: value["state_segments"][0]["dimension_names"].__setitem__(0, "中文"),
        lambda value: value["state_segments"][1]["dimension_names"].__setitem__(0, value["state_segments"][0]["dimension_names"][0]),
    ],
)
def test_v2_rejects_invalid_machine_names(change) -> None:
    config = default_lerobot_features_config()
    change(config)
    with pytest.raises(LeRobotFeatureConfigError):
        compile_lerobot_feature_contract(config)


def test_v2_must_contain_complete_field_list() -> None:
    config = default_lerobot_features_config()
    config["action_segments"] = config["action_segments"][:-1]
    with pytest.raises(LeRobotFeatureConfigError, match="missing segment"):
        compile_lerobot_feature_contract(config)
