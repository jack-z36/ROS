# deploy_004-007 验收 — Round 1

**结论: PASS_LOCAL** (all four repo-layer L3 tasks)

## deploy_004 — manifest 解析器
- [x] `manifest_parser.py` 存在，`load_bundle_manifest` 正常解析 JSON
- [x] 缺文件抛 FileNotFoundError
- [x] 坏 JSON 抛 json.JSONDecodeError
- [x] 3/3 tests passed

## deploy_005 — normalizer 加载器
- [x] `normalization.py` ActionStateNormalizer 完整保留 Pi0.5 结构
- [x] `normalizer_loader.py` 正常加载 normalizers.json
- [x] normalize/unnormalize roundtrip 正确
- [x] identity_indices 支持
- [x] 16/16 tests passed (normalization + loader)

## deploy_006 — experiment_config 加载器
- [x] `experiment_config_loader.py` 正常加载 YAML
- [x] 维度字段原值保留，不覆写
- [x] 7/7 tests passed

## deploy_007 — bundle 读取器
- [x] `bundle_reader.py` check_bundle_files 正确检测缺失文件
- [x] resolve_checkpoint_path 双策略解析
- [x] resolve_bundle_adapter_dir 正确
- [x] 15/15 tests passed
