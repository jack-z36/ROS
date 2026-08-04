"""Regression test for the camera-to-ACT observation topic wiring."""

import importlib.util
from pathlib import Path

import yaml


MODEL_DEPLOY_DIR = Path(__file__).resolve().parents[2]
ACT_SYSTEM_LAUNCH = (
    MODEL_DEPLOY_DIR / 'act_system' / 'launch' / 'act_system.launch.py'
)
ACT_DEPLOY_CONFIG = (
    MODEL_DEPLOY_DIR / 'act' / 'config_files' / 'deploy.yaml'
)


def _load_launch_module():
    spec = importlib.util.spec_from_file_location(
        'act_system_launch_under_test',
        ACT_SYSTEM_LAUNCH,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_camera_include_topics_match_act_observation_contract(monkeypatch):
    """The hardware-side remap must stay aligned with deploy.yaml."""
    module = _load_launch_module()
    monkeypatch.setattr(module, '_executable_exists', lambda *_args: True)
    monkeypatch.setattr(
        module,
        'get_package_share_directory',
        lambda _pkg: '/tmp/package_share',
    )

    actions = module._make_hardware_includes(context=None)
    camera_include = actions[-1]
    camera_arguments = dict(camera_include.launch_arguments)

    with ACT_DEPLOY_CONFIG.open(encoding='utf-8') as stream:
        deploy_config = yaml.safe_load(stream)
    image_topics = deploy_config['topics']['observation']['images']

    assert camera_arguments == {
        'left_image_topic': image_topics['left'],
        'right_image_topic': image_topics['right'],
    }
