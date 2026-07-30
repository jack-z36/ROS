import importlib.util
import subprocess
import unittest
from pathlib import Path
from unittest import mock


WORKSPACE_DIR = Path(__file__).resolve().parents[2]


def load_script_module(name, relative_path):
    path = WORKSPACE_DIR / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HardwareIdentityBaudrateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.identity_scan = load_script_module(
            "hardware_identity_scan", "scripts/hardware_identity_scan.py"
        )
        cls.sensor_status = load_script_module(
            "all_sensor_status", "scripts/all_sensor_status.py"
        )

    def test_hwk_query_passes_requested_baudrate(self):
        completed = subprocess.CompletedProcess(
            [], 0, "result: OK\nvalue: test-uid\n", ""
        )
        with mock.patch.object(self.identity_scan, "run", return_value=completed) as run:
            value = self.identity_scan.query_hwk_info(
                "/dev/ttyUSB0", "uid", addr=1, package_id=29, baudrate=921600
            )

        self.assertEqual(value, "test-uid")
        command = run.call_args.args[0]
        baudrate_index = command.index("--baudrate")
        self.assertEqual(command[baudrate_index + 1], "921600")

    def test_hwk_query_uses_ros_python_in_conda_shell(self):
        completed = subprocess.CompletedProcess(
            [], 0, "result: OK\nvalue: test-uid\n", ""
        )
        with mock.patch.object(
            self.identity_scan, "run", return_value=completed
        ) as run:
            self.identity_scan.query_hwk_info(
                "/dev/ttyUSB0", "uid", addr=0, package_id=29, baudrate=921600
            )

        command = run.call_args.args[0]
        expected = self.identity_scan.ROS_PYTHON_EXECUTABLE
        if not Path(expected).is_file():
            expected = self.identity_scan.sys.executable
        self.assertEqual(command[0], expected)

    def test_hwk_query_retries_after_initial_timeout(self):
        timeout = subprocess.CompletedProcess(
            [], 1, "result: timeout/no matching ACK\n", ""
        )
        success = subprocess.CompletedProcess(
            [], 0, "result: OK\nvalue: recovered-uid\n", ""
        )
        with (
            mock.patch.object(
                self.identity_scan, "run", side_effect=[timeout, success]
            ) as run,
            mock.patch.object(self.identity_scan.time, "sleep") as sleep,
        ):
            value = self.identity_scan.query_hwk_info(
                "/dev/ttyUSB0", "uid", addr=1, package_id=29, baudrate=921600
            )

        self.assertEqual(value, "recovered-uid")
        self.assertEqual(run.call_count, 2)
        sleep.assert_called_once_with(
            self.identity_scan.HWK_QUERY_RETRY_DELAY_SEC
        )

    def test_identity_validator_forwards_pressure_baudrate(self):
        completed = subprocess.CompletedProcess([], 0, "", "")
        with mock.patch.object(self.sensor_status, "run", return_value=completed) as run:
            status = self.sensor_status.validate_hardware_identity(
                "identity.yaml", hwk_baudrate=921600
            )

        self.assertEqual(status, 0)
        command = run.call_args.args[0]
        baudrate_index = command.index("--hwk-baudrate")
        self.assertEqual(command[baudrate_index + 1], "921600")

    def test_all_sensor_config_resolves_pressure_baudrate(self):
        config, config_path = self.sensor_status.load_config(
            WORKSPACE_DIR / "config" / "all_sensor_nodes.yaml"
        )

        self.assertEqual(
            self.sensor_status.pressure_default_baudrate(config, config_path.parent),
            921600,
        )


if __name__ == "__main__":
    unittest.main()
