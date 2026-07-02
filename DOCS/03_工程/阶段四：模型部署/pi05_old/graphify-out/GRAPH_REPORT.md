# Graph Report - D:\Projects\01-doing\pi05_test  (2026-06-04)

## Corpus Check
- 122 files · ~146,352 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1067 nodes · 1880 edges · 69 communities detected
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 256 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## God Nodes (most connected - your core abstractions)
1. `Pi05CommandTopics` - 32 edges
2. `Pi05ObservationTopics` - 32 edges
3. `SharedBuffer` - 31 edges
4. `_convert_one_mcap_into_dataset()` - 30 edges
5. `_deploy_from_mapping()` - 25 edges
6. `Pi05VlaDeployNode` - 24 edges
7. `ControlLoop` - 24 edges
8. `ObservationSnapshot` - 24 edges
9. `from_mapping()` - 23 edges
10. `CommandMuxNode` - 22 edges

## Surprising Connections (you probably didn't know these)
- `ROS 2 command multiplexer for teleop and Pi0.5 VLA control.  The mux is intentio` --uses--> `DeployConfig`  [INFERRED]
  pi05_test\pi05\deploy\src\pi05\deploy\ros_nodes\command_mux_node.py → pi05_test\pi05\deploy\src\pi05\deploy\config\schema.py
- `Forward either teleop or VLA candidate commands to picotele.` --uses--> `DeployConfig`  [INFERRED]
  pi05_test\pi05\deploy\src\pi05\deploy\ros_nodes\command_mux_node.py → pi05_test\pi05\deploy\src\pi05\deploy\config\schema.py
- `Main training loop for Pi0.5 LoRA fine-tuning.` --uses--> `ExperimentConfig`  [INFERRED]
  pi05_test\pi05\train\src\pi05\train\engine\trainer.py → pi05_test\pi05\common\src\pi05\common\config\schema.py
- `Coordinates config, Accelerate, model/data builders, and the train loop.` --uses--> `ExperimentConfig`  [INFERRED]
  pi05_test\pi05\train\src\pi05\train\engine\trainer.py → pi05_test\pi05\common\src\pi05\common\config\schema.py
- `Training-only runtime utilities.` --uses--> `ExperimentConfig`  [INFERRED]
  pi05_test\pi05\train\src\pi05\train\utils\__init__.py → pi05_test\pi05\common\src\pi05\common\config\schema.py

## Hyperedges (group relationships)
- **pi05.common.* subpackages form a shared layer used by both training and deployment** — common_init, config_init, data_init, model_init, robot_init, ros_init, runtime_init, utils_init [EXTRACTED 0.90]
- **Pi0.5 real-time inference+control pipeline** — ros_nodes_Pi05VlaDeployNode, runtime_ObservationCollector, runtime_SharedBuffer, runtime_InferenceWorker, runtime_ControlLoop, models_Pi05PolicyRuntime [EXTRACTED 0.90]
- **VLA command publication chain** — ros_nodes_Pi05VlaDeployNode, ros_nodes_Pi05BridgeNode, ros_nodes_CommandMuxNode, config_TopicsConfig [EXTRACTED 0.90]
- **Cross-node safety enforcement** — config_SafetyConfig, runtime_SafetyGuard, runtime_ControlLoop, ros_nodes_Pi05BridgeNode [EXTRACTED 0.90]
- **Pi0.5 LoRA training pipeline (CLI to trainer to builders/ckpt/utils)** — cli_train_main, script_train_lora, trainer_pi05loratrainer, engine_builders, engine_checkpoints [EXTRACTED 0.90]
- **MCAP to LeRobot v3 data preparation flow** — script_prepare_dataset, tool_mcap_to_lerobot_v3, concept_lerobot_v3_dataset, mcap_tactile_layout, mcap_50ms_gate, mcap_tactile_scale_q995 [EXTRACTED 0.90]
- **Training to Deploy bundle handoff** — trainer_export_bundle_call, engine_checkpoints, cli_export_bundle_main, script_export_policy, bundle_layout_required [EXTRACTED 0.90]
- **Vision-Language-Action (VLA) Policy Family** — pi05_policy, smolvla_policy, gr00t_policy, pi0fast_policy, xvla_policy [EXTRACTED 0.90]
- **Feetech Servo-Based Arm Robots** — so100_robot, so101_robot, koch_robot [EXTRACTED 0.90]
- **Pi0.5 Heterogeneous Co-Training Data Sources** — pi05_policy, hf_hub, openpi_repo, physical_intelligence [EXTRACTED 0.90]
- **LeKiwi teleop lifecycle** — lekiwi/teleoperate.py|lekiwi_leader_arm_teleop, lekiwi/record.py|lekiwi_teleop_recording, lekiwi/replay.py|lekiwi_dataset_replay, lekiwi/evaluate.py|lekiwi_act_policy_evaluation [EXTRACTED 0.90]
- **Phone->SO100 EE teleop lifecycle** — phone_to_so100/teleoperate.py|phone_to_so100_live_teleop, phone_to_so100/record.py|phone_to_so100_teleop_recording, phone_to_so100/replay.py|phone_to_so100_ee_replay, phone_to_so100/evaluate.py|phone_to_so100_policy_evaluation [EXTRACTED 0.90]
- **SO100->SO100 EE teleop lifecycle** — so100_to_so100_EE/teleoperate.py|so100_to_so100_ee_teleop, so100_to_so100_EE/record.py|so100_to_so100_ee_recording, so100_to_so100_EE/replay.py|so100_to_so100_ee_replay, so100_to_so100_EE/evaluate.py|so100_to_so100_ee_policy_evaluation [EXTRACTED 0.90]
- **HIL data collection script pair** — hil_data_collection.py|hil_data_collection_orchestration, hil_utils.py|hil_shared_utilities [EXTRACTED 0.90]
- **SLURM DROID porting pipeline** — port_datasets/port_droid.py|droid_tfds_to_lerobot_converter, port_datasets/slurm_port_shards.py|slurm_parallel_shard_porting, port_datasets/slurm_aggregate_shards.py|slurm_shard_aggregation_step, port_datasets/slurm_upload.py|slurm_hub_upload_step, port_datasets/display_error_files.py|port_datasets_missing_worker_diagnostic [EXTRACTED 0.90]
- **RTC evaluation deployment modes** — rtc/eval_dataset.py|rtc_offline_dataset_evaluation, rtc/eval_with_real_robot.py|rtc_real_robot_demo [EXTRACTED 0.90]
- **async-inference client/server** — policy_server.py|policy_server, robot_client.py|robot_client [EXTRACTED 0.90]
- **ACT train-then-deploy** — act_training_example.py|act_train, act_using_example.py|act_using [EXTRACTED 0.90]
- **Diffusion train-then-deploy** — diffusion_training_example.py|diffusion_train, diffusion_using_example.py|diffusion_using [EXTRACTED 0.90]
- **HIL-SERL RL training toolkit** — hilserl_example.py|hilserl_train, reward_classifier_example.py|reward_classifier_train [EXTRACTED 0.90]
- **User MCAP->LeRobot v3 data prep tool** — mcap_to_lerobot_v3.py|mcap_to_lerobot_v3_converter [EXTRACTED 0.90]

## Communities

### Community 0 - "Action encoding (Pi0.5 common)"
Cohesion: 0.04
Nodes (64): ensure_action_chunk(), ensure_action_vector(), Action encoding helpers for Pi0.5 deployment outputs., Validate and return one flat 14-D action vector., Validate and return a 2-D action chunk., Return a structured view of a single action vector., split_action(), BimanualAction (+56 more)

### Community 1 - "Training engine builders (optimizer/lr/dataloader)"
Cohesion: 0.06
Nodes (80): Builders for datasets, dataloaders, optimizers, and schedulers., Training-only runtime utilities., _attention_implementation(), _bool(), _bridge_topics(), BridgeConfig, BridgeTopicsConfig, BundleConfig (+72 more)

### Community 2 - "MCAP to LeRobot v3 conversion"
Cohesion: 0.06
Nodes (68): _accumulate_tactile_scale_samples(), build_features_pi05(), _build_tactile_preprocess_stats(), _build_task_from_annotation(), _collect_tactile_scale_window(), convert_mcap_dir_to_lerobot(), convert_mcap_to_lerobot(), convert_mcap_to_lerobot_with_annotations() (+60 more)

### Community 3 - "LeRobot hardware and contribution docs"
Cohesion: 0.05
Nodes (62): Aloha Robot, Robot Calibration Procedure (homing/range), OpenCVCamera, Reachy2Camera, RealSenseCamera, Contributor Covenant Code of Conduct v2.1, LeRobot Contributing Guide, StreamingLeRobotDataset (+54 more)

### Community 4 - "Pi0.5 model builder with LoRA"
Cohesion: 0.06
Nodes (43): _as_experiment_config(), build_pi05_with_lora(), _enable_gradient_checkpointing(), _ensure_pi05_feature_specs(), _force_pi05_attention_implementation(), get_pi05_policy_config(), _image_keys_from_cameras(), _is_visual_feature() (+35 more)

### Community 5 - "HIL data collection orchestration"
Cohesion: 0.06
Nodes (41): hil_collect(), HILConfig, main(), _normalize_prev_actions_length(), Thread-safe wrapper for robot operations (used with RTC background thread)., Set a safe default max_relative_target for OpenArm followers when not provided., Convert absolute leftovers into model space for relative-action RTC policies., Pad/truncate RTC prefix actions to a fixed length for stable compiled inference. (+33 more)

### Community 6 - "Deploy bundle and safety modes"
Cohesion: 0.06
Nodes (36): Deploy bundle requires manifest.json+normalizers.json+experiment_config.yaml+adapter/, pi05.train.cli.export_bundle main(), pi05.train.cli.train main(), LeRobot v3 dataset format target, conda-pack env relocation rationale, dry-run / shadow-run / safe-run safety modes, DEPLOY_REPRODUCE.md (clone to bundle to ROS2), LeRobot AI_POLICY.md (disclose AI, human-in-loop) (+28 more)

### Community 7 - "Bundle I/O (manifest, normalizers, tactile preprocess)"
Cohesion: 0.08
Nodes (28): _copy_tactile_preprocess(), export_deploy_bundle(), _identity_indices(), _manifest_payload(), _normalizer_payload(), _prepare_output_dir(), Deploy bundle export/load helpers., Export the minimum runtime payload needed by deployment. (+20 more)

### Community 8 - "DROID TFDS to LeRobot porting pipeline"
Cohesion: 0.08
Nodes (24): PipelineStep, generate_lerobot_frames(), is_episode_successful(), main(), port_droid(), Sanity check that ensure meta data can be loaded and all files are present., validate_dataset(), AggregateDatasets (+16 more)

### Community 9 - "Deploy CLI and ROS2 config schemas"
Cohesion: 0.08
Nodes (27): BridgeConfig (forward/adapt to picotele), DeployConfig (typed YAML config root), MuxConfig (teleop vs VLA arbitration), RuntimeConfig (control/inference Hz, chunk, blend), SafetyConfig (delta limits, hand range, timeouts), TopicsConfig (observation/command/bridge/mux topics), load_deploy_config(YAML), Pi05PolicyRuntime (predict_action_chunk) (+19 more)

### Community 10 - "Dataset progress video tools"
Cohesion: 0.07
Nodes (32): _alpha_composite_region(), composite_progress_video(), convert_mp4_to_gif(), download_episode_metadata(), download_video_file(), _draw_text_outlined(), load_episode_meta(), load_progress_data() (+24 more)

### Community 11 - "LeRobot platform concepts (policies, robots, hub)"
Cohesion: 0.1
Nodes (36): ACT policy, BiOpenArm dual-arm follower, Diffusion policy, HuggingFace Hub, Keyboard teleoperator, LeKiwi mobile base + arm (client), LeRobotDataset core, Phone teleoperator (iOS/Android) (+28 more)

### Community 12 - "RTC offline dataset evaluation"
Cohesion: 0.1
Nodes (17): _check_matplotlib_available(), main(), Set random seed for reproducibility., Check if matplotlib is available, raise helpful error if not., Evaluator for RTC on dataset samples., Initialize a single policy instance with specified RTC configuration.          A, Apply torch.compile to the policy's predict_action_chunk method.          Args:, Explicitly destroy a policy and free all associated memory.          This method (+9 more)

### Community 13 - "RTC real-robot evaluation"
Cohesion: 0.09
Nodes (17): Configuration for RTC evaluation., RTCEvalConfig, actor_control(), _apply_torch_compile(), demo_cli(), get_actions(), Configuration for RTC demo with action chunking policies and real robots., # HACK: We parse again the cli args here to get the pretrained path if there was (+9 more)

### Community 14 - "LeRobot training tutorials (ACT, Diffusion, HIL-SERL)"
Cohesion: 0.1
Nodes (24): ACT Training Colab Notebook, ACT Policy (Action Chunking Transformer), ACT policy training, ACT policy inference (SO100), Diffusion Policy, Diffusion policy training, Diffusion policy inference (SO100), HIL-SERL actor/learner training (+16 more)

### Community 15 - "Command mux ROS node"
Cohesion: 0.17
Nodes (5): build_arg_parser(), CommandMuxNode, main(), ROS 2 command multiplexer for teleop and Pi0.5 VLA control.  The mux is intentio, Forward either teleop or VLA candidate commands to picotele.

### Community 16 - "Train dataset and normalizer adapters"
Cohesion: 0.17
Nodes (11): _apply_normalizer(), _camera_from_output_key(), _dataset_image_key(), _feature_dim(), _normalize_cameras(), _output_image_key(), Pi05LeRobotDataset, Dataset wrapper for Pi0.5-style LeRobot offline training. (+3 more)

### Community 17 - "Pi05 VLA deploy node"
Cohesion: 0.2
Nodes (5): build_arg_parser(), _decode_image(), _joint_msg(), main(), Pi05VlaDeployNode

### Community 18 - "Observation collector (ROS)"
Cohesion: 0.21
Nodes (3): _normalize_image_keys(), ObservationCollector, _required_value_keys()

### Community 19 - "Smoke test for LoRA training"
Cohesion: 0.24
Nodes (11): find_lora_gradient(), _get_policy_config(), load_yaml(), main(), make_mock_batch(), parse_args(), prepare_model_batch(), Convert the mock batch into the exact PI0.5 training batch expected by the polic (+3 more)

### Community 20 - "Tensorboard utilities"
Cohesion: 0.3
Nodes (11): _build_url(), _connect_host(), _extract_cli_flag(), _find_available_port(), _find_running_tensorboard_port(), _is_port_open(), launch_tensorboard(), _print_tensorboard_banner() (+3 more)

### Community 21 - "Dataset image transforms example"
Cohesion: 0.33
Nodes (9): example_1_default_transforms(), example_2_custom_transforms(), example_3_torchvision_transforms(), main(), Example 3: Use pure torchvision transforms and save examples, Helper function to save a tensor as an image file., Example 1: Use default transform configuration and save original vs transformed, Example 2: Create custom transform configuration and save examples (+1 more)

### Community 22 - "Project paths bootstrap"
Cohesion: 0.22
Nodes (3): bootstrap_project_paths(), Path helpers for running the project from source or editable installs., Make local source checkout imports explicit for non-installed entrypoints.

### Community 23 - "HIL-SERL actor/learner training"
Cohesion: 0.29
Nodes (7): main(), make_policy_obs(), The actor process - interacts with environment and collects data.     The policy, Main function - coordinates actor and learner processes., The learner process - trains SAC policy on transitions streamed from the actor,, run_actor(), run_learner()

### Community 24 - "Image preprocessing (Pi0.5 common)"
Cohesion: 0.43
Nodes (6): _cv2_resize_rgb(), preprocess_rgb_image(), Image preprocessing shared by Pi0.5 training checks and deployment.  The helpers, Convert an RGB image into a normalized CHW float tensor., _resize_crop(), _resize_pad()

### Community 25 - "State codec (Pi0.5 common)"
Cohesion: 0.33
Nodes (6): decode_picotele_proprioception(), encode_bimanual_state(), State encoding contract for Pi0.5 bimanual deployment., Encode a structured bimanual state into the canonical 26-D vector., Decode a legacy proprioception vector ordered as [right6, left6]., _vector()

### Community 26 - "Train config tests"
Cohesion: 0.43
Nodes (4): _minimal_config(), test_config_accepts_existing_yaml_shape(), test_config_accepts_train_expert_only_with_regex_targets(), test_config_rejects_ambiguous_string_bool()

### Community 27 - "Checkpoint and LoRA adapter export"
Cohesion: 0.38
Nodes (5): export_final_adapter(), Checkpoint and final adapter export helpers., Save an epoch-level LoRA adapter without optimizer/scheduler state., _save_adapter(), save_epoch_adapter_checkpoint()

### Community 28 - "SLURM missing-worker diagnostic"
Cohesion: 0.38
Nodes (6): display_error_files(), find_missing_workers(), find_output_files(), main(), Find workers that are not completed and returns their indices., Find output files associated to worker indices, and return tuples     of (worker

### Community 29 - "Joint limit primitives"
Cohesion: 0.5
Nodes (4): broad_joint_limits(), from_values(), Joint limit primitives used by deployment safety checks., Return permissive limits used when hardware-specific bounds are absent.

### Community 30 - "Export bundle CLI"
Cohesion: 0.6
Nodes (4): main(), parse_args(), CLI for exporting a deployment-ready PI05 bundle from training artifacts., _resolve_paths()

### Community 31 - "LeKiwi / phone SO100 recording (lerobot examples)"
Cohesion: 0.4
Nodes (3): # NOTE: It is highly recommended to use the urdf in the SO-ARM100 repo: https://, # NOTE: It is highly recommended to use the urdf in the SO-ARM100 repo: https://, # NOTE: It is highly recommended to use the urdf in the SO-ARM100 repo: https://

### Community 32 - "LeKiwi / phone SO100 teleop (lerobot examples)"
Cohesion: 0.4
Nodes (3): # NOTE: It is highly recommended to use the urdf in the SO-ARM100 repo: https://, # NOTE: It is highly recommended to use the urdf in the SO-ARM100 repo: https://, # NOTE: It is highly recommended to use the urdf in the SO-ARM100 repo: https://

### Community 33 - "Pi05 + picotele launch file"
Cohesion: 0.67
Nodes (3): generate_launch_description(), _pi05_script(), Integrated launch for Pi0.5 VLA, picotele, RealSense, and command mux.  Run this

### Community 34 - "Train dataloader test"
Cohesion: 0.83
Nodes (3): describe_tensor(), main(), parse_args()

### Community 35 - "Pi0.5 LoRA training CLI"
Cohesion: 0.67
Nodes (3): main(), parse_args(), CLI for Pi0.5 LoRA training.

### Community 36 - "Batch adapters for LeRobot PI0.5"
Cohesion: 0.5
Nodes (3): Batch adapters between the local dataset and LeRobot PI0.5 preprocessor., Map local dataset keys to the official PI0.5 processor input schema., to_lerobot_pi05_batch()

### Community 37 - "ACT policy training example"
Cohesion: 0.67
Nodes (3): main(), make_delta_timestamps(), This script demonstrates how to train ACT Policy on a real-world dataset.

### Community 38 - "Diffusion policy training example"
Cohesion: 0.67
Nodes (3): main(), make_delta_timestamps(), This script demonstrates how to train Diffusion Policy on a real-world dataset.

### Community 39 - "Bridge ROS CLI"
Cohesion: 0.67
Nodes (1): ROS 2 bridge entry point for Pi0.5 command topics.

### Community 40 - "Deploy ROS CLI"
Cohesion: 0.67
Nodes (1): ROS 2 deployment entry point for the Pi0.5 VLA runtime.

### Community 41 - "Random seed utilities"
Cohesion: 0.67
Nodes (1): Reproducibility helpers.

### Community 42 - "LeKiwi / phone SO100 evaluation (lerobot examples)"
Cohesion: 0.67
Nodes (1): # NOTE: It is highly recommended to use the urdf in the SO-ARM100 repo: https://

### Community 43 - "Command mux ROS CLI"
Cohesion: 1.0
Nodes (1): ROS 2 command mux entry point.

### Community 44 - "Policy node compatibility wrapper"
Cohesion: 1.0
Nodes (1): Compatibility wrapper for the new Pi0.5 VLA deployment node.

### Community 45 - "Use dataset tools example"
Cohesion: 1.0
Nodes (0): 

### Community 46 - "Diffusion policy on PushT training"
Cohesion: 1.0
Nodes (0): 

### Community 47 - "Streaming ACT training example"
Cohesion: 1.0
Nodes (0): 

### Community 48 - "ACT using example (SO100 inference)"
Cohesion: 1.0
Nodes (0): 

### Community 49 - "Async policy server"
Cohesion: 1.0
Nodes (0): 

### Community 50 - "Phone-to-SO100 EE record"
Cohesion: 1.0
Nodes (0): 

### Community 51 - "Phone-to-SO100 EE replay"
Cohesion: 1.0
Nodes (0): 

### Community 52 - "SO100-to-SO100 EE record"
Cohesion: 1.0
Nodes (0): 

### Community 53 - "SO100-to-SO100 EE replay"
Cohesion: 1.0
Nodes (0): 

### Community 54 - "SO100-to-SO100 EE teleop"
Cohesion: 1.0
Nodes (0): 

### Community 55 - "Phone-to-SO100 EE evaluate"
Cohesion: 1.0
Nodes (2): pi05.common.data (lightweight, defers heavy helpers), Rationale: keep data package __init__ lightweight so config/codec imports work before torch loads

### Community 56 - "Robot client (async inference)"
Cohesion: 1.0
Nodes (2): LeRobot Documentation Build Process, Documentation ToC Tree (_toctree.yml)

### Community 57 - "SLURM aggregate shards"
Cohesion: 1.0
Nodes (1): This enables the parser to load config from the policy using `--policy.path=loca

### Community 58 - "SLURM upload to HuggingFace"
Cohesion: 1.0
Nodes (1): This enables the parser to load config from the policy using `--policy.path=loca

### Community 59 - "Diffusion using example (SO100 inference)"
Cohesion: 1.0
Nodes (1): pi05.common (shared package init)

### Community 60 - "PI0 using example (SO100 inference)"
Cohesion: 1.0
Nodes (1): pi05.common.config (re-exports schema)

### Community 61 - "Reward classifier training"
Cohesion: 1.0
Nodes (1): pi05.common.model (shared model package)

### Community 62 - "SmolVLA using example"
Cohesion: 1.0
Nodes (1): pi05.common.robot (robot spec helpers)

### Community 63 - "LeKiwi / SO100 lifecycle scripts"
Cohesion: 1.0
Nodes (1): pi05.common.ros (ROS naming helpers)

### Community 64 - "Load LeRobot dataset example"
Cohesion: 1.0
Nodes (1): pi05.common.runtime (re-exports bundle helpers)

### Community 65 - "RTC eval helpers"
Cohesion: 1.0
Nodes (1): pi05.common.utils (re-exports path utilities)

### Community 66 - "HIL config and command-line surface"
Cohesion: 1.0
Nodes (1): pi05.deploy (Pi0.5 VLA deployment package)

### Community 67 - "PI05 deploy config (typed schema)"
Cohesion: 1.0
Nodes (1): ZMQCamera

### Community 68 - "PI05 deploy service README"
Cohesion: 1.0
Nodes (1): Safetensors Model Format

## Knowledge Gaps
- **133 isolated node(s):** `Raised when a YAML config is missing required fields or has invalid types.`, `Image preprocessing shared by Pi0.5 training checks and deployment.  The helpers`, `Configuration for deterministic deployment image preprocessing.`, `Convert an RGB image into a normalized CHW float tensor.`, `Normalization utilities for Pi0.5 state and action vectors.  This module provide` (+128 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Command mux ROS CLI`** (2 nodes): `command_mux_ros.py`, `ROS 2 command mux entry point.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Policy node compatibility wrapper`** (2 nodes): `policy_node.py`, `Compatibility wrapper for the new Pi0.5 VLA deployment node.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Use dataset tools example`** (2 nodes): `use_dataset_tools.py`, `main()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Diffusion policy on PushT training`** (2 nodes): `train_policy.py`, `main()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Streaming ACT training example`** (2 nodes): `train_with_streaming.py`, `main()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `ACT using example (SO100 inference)`** (2 nodes): `act_using_example.py`, `main()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Async policy server`** (2 nodes): `policy_server.py`, `main()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Phone-to-SO100 EE record`** (2 nodes): `robot_client.py`, `main()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Phone-to-SO100 EE replay`** (2 nodes): `diffusion_using_example.py`, `main()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `SO100-to-SO100 EE record`** (2 nodes): `using_pi0_example.py`, `main()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `SO100-to-SO100 EE replay`** (2 nodes): `reward_classifier_example.py`, `main()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `SO100-to-SO100 EE teleop`** (2 nodes): `using_smolvla_example.py`, `main()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Phone-to-SO100 EE evaluate`** (2 nodes): `pi05.common.data (lightweight, defers heavy helpers)`, `Rationale: keep data package __init__ lightweight so config/codec imports work before torch loads`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Robot client (async inference)`** (2 nodes): `LeRobot Documentation Build Process`, `Documentation ToC Tree (_toctree.yml)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `SLURM aggregate shards`** (1 nodes): `This enables the parser to load config from the policy using `--policy.path=loca`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `SLURM upload to HuggingFace`** (1 nodes): `This enables the parser to load config from the policy using `--policy.path=loca`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Diffusion using example (SO100 inference)`** (1 nodes): `pi05.common (shared package init)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `PI0 using example (SO100 inference)`** (1 nodes): `pi05.common.config (re-exports schema)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Reward classifier training`** (1 nodes): `pi05.common.model (shared model package)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `SmolVLA using example`** (1 nodes): `pi05.common.robot (robot spec helpers)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `LeKiwi / SO100 lifecycle scripts`** (1 nodes): `pi05.common.ros (ROS naming helpers)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Load LeRobot dataset example`** (1 nodes): `pi05.common.runtime (re-exports bundle helpers)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `RTC eval helpers`** (1 nodes): `pi05.common.utils (re-exports path utilities)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `HIL config and command-line surface`** (1 nodes): `pi05.deploy (Pi0.5 VLA deployment package)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `PI05 deploy config (typed schema)`** (1 nodes): `ZMQCamera`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `PI05 deploy service README`** (1 nodes): `Safetensors Model Format`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Pi05VlaDeployNode` connect `Pi05 VLA deploy node` to `Action encoding (Pi0.5 common)`, `Observation collector (ROS)`, `Pi0.5 model builder with LoRA`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **Why does `Pi05LoraTrainer` connect `Deploy bundle and safety modes` to `Pi0.5 model builder with LoRA`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **What connects `Raised when a YAML config is missing required fields or has invalid types.`, `Image preprocessing shared by Pi0.5 training checks and deployment.  The helpers`, `Configuration for deterministic deployment image preprocessing.` to the rest of the system?**
  _133 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Action encoding (Pi0.5 common)` be split into smaller, more focused modules?**
  _Cohesion score 0.04 - nodes in this community are weakly interconnected._
- **Should `Training engine builders (optimizer/lr/dataloader)` be split into smaller, more focused modules?**
  _Cohesion score 0.06 - nodes in this community are weakly interconnected._
- **Should `MCAP to LeRobot v3 conversion` be split into smaller, more focused modules?**
  _Cohesion score 0.06 - nodes in this community are weakly interconnected._
- **Should `LeRobot hardware and contribution docs` be split into smaller, more focused modules?**
  _Cohesion score 0.05 - nodes in this community are weakly interconnected._