import importlib.util
import unittest
from pathlib import Path


WORKSPACE_DIR = Path(__file__).resolve().parents[2]
STATUS_SCRIPT = WORKSPACE_DIR / "scripts" / "all_sensor_status.py"


def load_status_module():
    spec = importlib.util.spec_from_file_location("all_sensor_status", STATUS_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AllSensorStatusTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.status = load_status_module()
        cls.config, cls.config_path = cls.status.load_config(
            WORKSPACE_DIR / "config" / "all_sensor_nodes.yaml"
        )

    def test_no_pressure_filter_keeps_baton_and_gopro_only(self):
        filtered = self.status.apply_startup_filters(
            self.config,
            include_pressure=False,
            validate_identity=False,
        )
        sensors = self.status.expected_sensors(
            filtered, self.config_path.parent
        )

        self.assertEqual(
            {sensor["id"] for sensor in sensors},
            {
                "baton_mini.left",
                "baton_mini.right",
                "gopro.left",
                "gopro.right",
            },
        )
        self.assertFalse(filtered["pressure"]["enabled"])
        self.assertFalse(filtered["hardware_identity"]["enabled"])

    def test_startup_filter_does_not_mutate_production_config(self):
        self.status.apply_startup_filters(
            self.config,
            include_pressure=False,
            validate_identity=False,
        )

        self.assertTrue(self.config["pressure"]["enabled"])
        self.assertTrue(self.config["hardware_identity"]["enabled"])


if __name__ == "__main__":
    unittest.main()
