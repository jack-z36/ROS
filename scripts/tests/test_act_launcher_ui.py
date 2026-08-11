import importlib.util
import unittest
from pathlib import Path

import yaml
from PIL import Image


WORKSPACE_DIR = Path(__file__).resolve().parents[2]
UI_SCRIPT = WORKSPACE_DIR / "scripts" / "act_launcher_ui.py"


def load_ui_module():
    spec = importlib.util.spec_from_file_location("act_launcher_ui", UI_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ActLauncherUiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ui = load_ui_module()
        with (WORKSPACE_DIR / "config" / "all_sensor_nodes.yaml").open(
            "r", encoding="utf-8"
        ) as stream:
            cls.config = yaml.safe_load(stream) or {}
        with (WORKSPACE_DIR / "config" / "hardware_identity_map.yaml").open(
            "r", encoding="utf-8"
        ) as stream:
            cls.identity = yaml.safe_load(stream) or {}

    def test_overview_metadata_uses_real_configuration(self):
        metadata = self.ui._device_metadata(self.config, self.identity)
        self.assertIn("192.168.2.10", metadata["baton_mini.left"])
        self.assertIn("192.168.1.10", metadata["baton_mini.right"])
        self.assertEqual(metadata["pressure"], "4/4 UID 已映射")
        self.assertIn("2 路相机", metadata["gopro"])
        self.assertIn("本机 GUI", metadata["octopus"])

    def test_generated_device_assets_have_transparent_corners(self):
        for filename in (
            "device_baton.png",
            "device_camera.png",
            "device_pressure.png",
            "device_octopus_controller.png",
        ):
            path = WORKSPACE_DIR / "assets" / "launcher" / filename
            with self.subTest(filename=filename), Image.open(path) as image:
                self.assertEqual(image.mode, "RGBA")
                alpha = image.getchannel("A")
                corners = (
                    alpha.getpixel((0, 0)),
                    alpha.getpixel((image.width - 1, 0)),
                    alpha.getpixel((0, image.height - 1)),
                    alpha.getpixel((image.width - 1, image.height - 1)),
                )
                self.assertEqual(corners, (0, 0, 0, 0))

    def test_chinese_brand_copy_is_rendered_by_gui(self):
        source = UI_SCRIPT.read_text(encoding="utf-8")
        self.assertIn('text="  |  具感时代"', source)
        self.assertIn('text="感知万物 · 同步采集"', source)
        self.assertIn('"Noto Sans CJK SC"', source)

    def test_native_titlebar_is_default_and_custom_mode_is_opt_in(self):
        self.assertTrue(self.ui._use_native_titlebar({}))
        self.assertTrue(
            self.ui._use_native_titlebar(
                {
                    "ACT_LAUNCHER_NATIVE_TITLEBAR": "1",
                    "ACT_LAUNCHER_CUSTOM_TITLEBAR": "1",
                }
            )
        )
        self.assertFalse(
            self.ui._use_native_titlebar(
                {"ACT_LAUNCHER_CUSTOM_TITLEBAR": "1"}
            )
        )

    def test_overview_layout_fills_tall_viewport(self):
        source = UI_SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            "class _FillHeightScrollableFrame(ctk.CTkScrollableFrame)",
            source,
        )
        self.assertIn("page = _FillHeightScrollableFrame(", source)
        self.assertIn("height=292", source)

    def test_startup_mode_selector_exposes_both_profiles(self):
        source = UI_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("CTkSegmentedButton", source)
        self.assertIn('"全部节点"', source)
        self.assertIn('"Baton Mini + GoPro（不含触觉）"', source)


if __name__ == "__main__":
    unittest.main()
