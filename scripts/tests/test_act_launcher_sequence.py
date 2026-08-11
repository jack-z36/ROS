import importlib.util
import threading
import unittest
from pathlib import Path
from unittest import mock


WORKSPACE_DIR = Path(__file__).resolve().parents[2]
LAUNCHER_SCRIPT = WORKSPACE_DIR / "scripts" / "act_launcher.py"


def load_module():
    spec = importlib.util.spec_from_file_location("act_launcher", LAUNCHER_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeProcess:
    def __init__(self, output):
        self.stdout = iter(output)
        self.returncode = None

    def poll(self):
        return self.returncode


class SensorOutput:
    def __init__(self, octopus_started):
        self._octopus_started = octopus_started
        self._lines = iter(
            [
                "配置文件已加载\n",
                "启动结果：5/5 个节点全部通过检查。\n",
                "launch 仍在运行。\n",
            ]
        )

    def __iter__(self):
        return self

    def __next__(self):
        if not self._octopus_started["value"]:
            raise AssertionError("sensor output was read before Octopus started")
        return next(self._lines)


class FakeThread:
    def __init__(self, target=None, args=(), daemon=None):
        self.target = target
        self.args = args
        self.daemon = daemon

    def start(self):
        # The sequence itself is exercised synchronously. Log watcher threads
        # are intentionally not run in this focused orchestration test.
        return None


class ActLauncherSequenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.launcher_module = load_module()

    def test_gui_uses_same_transparent_icon_as_desktop(self):
        from PIL import Image

        icon_path = Path(self.launcher_module.APP_ICON_PATH)
        self.assertEqual(icon_path.name, "umi_launcher_icon_transparent.png")
        self.assertTrue(icon_path.is_file())

        with Image.open(icon_path) as icon:
            self.assertEqual(icon.mode, "RGBA")
            alpha = icon.getchannel("A")
            corners = (
                alpha.getpixel((0, 0)),
                alpha.getpixel((icon.width - 1, 0)),
                alpha.getpixel((0, icon.height - 1)),
                alpha.getpixel((icon.width - 1, icon.height - 1)),
            )
        self.assertEqual(corners, (0, 0, 0, 0))

    def test_octopus_starts_before_sensor_health_check_output(self):
        launcher = object.__new__(self.launcher_module.ActLauncher)
        launcher._workspace_dir = str(WORKSPACE_DIR)
        launcher._running = False
        launcher._cancel_start = threading.Event()
        launcher._sensor_proc = None
        launcher._octopus_proc = None
        launcher._sensor_labels = {
            sensor_id: None
            for sensor_id, _label in self.launcher_module.ActLauncher.SENSOR_DEFS
        }

        logs = []
        statuses = []
        launcher.after = lambda _delay, callback, *args: callback(*args)
        launcher._append_log = logs.append
        launcher._set_system_state = lambda *_args, **_kwargs: None
        launcher._update_sensor_status = (
            lambda sensor_id, status, desc="": statuses.append(
                (sensor_id, status, desc)
            )
        )
        launcher._set_buttons_running = lambda _running: None
        launcher._start_polling = lambda: None

        octopus_started = {"value": False}
        sensor = FakeProcess([])
        sensor.stdout = SensorOutput(octopus_started)
        octopus = FakeProcess(["Octopus started\n"])

        processes = iter([sensor, octopus])

        def start_process(*_args, **_kwargs):
            process = next(processes)
            if process is octopus:
                octopus_started["value"] = True
            return process

        with (
            mock.patch.object(
                self.launcher_module.subprocess,
                "Popen",
                side_effect=start_process,
            ) as popen,
            mock.patch.object(
                self.launcher_module.threading, "Thread", FakeThread
            ),
            mock.patch.object(self.launcher_module.time, "sleep"),
        ):
            launcher._run_start_sequence(smoke_test=False)

        self.assertEqual(popen.call_count, 2)
        self.assertIs(launcher._sensor_proc, sensor)
        self.assertIs(launcher._octopus_proc, octopus)
        self.assertTrue(
            any("[Phase 2] Octopus 界面已启动" in line for line in logs)
        )
        self.assertIn(("octopus", "ok", "界面运行中"), statuses)

    def test_no_tactile_mode_uses_baton_gopro_entrypoint(self):
        launcher = object.__new__(self.launcher_module.ActLauncher)
        launcher._workspace_dir = str(WORKSPACE_DIR)
        launcher._running = False
        launcher._cancel_start = threading.Event()
        launcher._sensor_proc = None
        launcher._octopus_proc = None
        launcher._startup_mode = (
            self.launcher_module.ActLauncher.STARTUP_MODE_NO_TACTILE
        )
        launcher._sensor_labels = {
            sensor_id: None
            for sensor_id, _label in self.launcher_module.ActLauncher.SENSOR_DEFS
        }

        logs = []
        statuses = []
        launcher.after = lambda _delay, callback, *args: callback(*args)
        launcher._append_log = logs.append
        launcher._set_system_state = lambda *_args, **_kwargs: None
        launcher._update_sensor_status = (
            lambda sensor_id, status, desc="": statuses.append(
                (sensor_id, status, desc)
            )
        )
        launcher._set_buttons_running = lambda _running: None
        launcher._start_polling = lambda: None

        octopus_started = {"value": False}
        sensor = FakeProcess([])
        sensor.stdout = SensorOutput(octopus_started)
        octopus = FakeProcess(["Octopus started\n"])
        processes = iter([sensor, octopus])

        def start_process(*_args, **_kwargs):
            process = next(processes)
            if process is octopus:
                octopus_started["value"] = True
            return process

        with (
            mock.patch.object(
                self.launcher_module.subprocess,
                "Popen",
                side_effect=start_process,
            ) as popen,
            mock.patch.object(
                self.launcher_module.threading, "Thread", FakeThread
            ),
            mock.patch.object(self.launcher_module.time, "sleep"),
        ):
            launcher._run_start_sequence(
                smoke_test=False,
                startup_mode=self.launcher_module.ActLauncher.STARTUP_MODE_NO_TACTILE,
            )

        self.assertEqual(popen.call_count, 2)
        self.assertEqual(
            popen.call_args_list[0].args[0][0],
            str(WORKSPACE_DIR / "start_baton_gopro.sh"),
        )
        self.assertIn(("pressure", "skipped", "当前模式跳过"), statuses)
        self.assertTrue(any("不含触觉" in line for line in logs))

    def test_skipped_pressure_does_not_make_running_profile_unhealthy(self):
        launcher = object.__new__(self.launcher_module.ActLauncher)
        launcher._running = True
        launcher._card_status = {
            "baton_mini.left": "ok",
            "baton_mini.right": "ok",
            "gopro": "ok",
            "pressure": "skipped",
        }
        states = []
        launcher._set_system_state = lambda *args: states.append(args)

        launcher._parse_sensor_status("")

        self.assertEqual(states[-1], ("running",))

    def test_gopro_card_keeps_failure_from_either_side(self):
        launcher = object.__new__(self.launcher_module.ActLauncher)
        launcher._subdevice_status = {}
        launcher._sensor_labels = {"gopro": (None, None)}
        updates = []
        launcher.after = lambda _delay, callback, *args: callback(*args)
        launcher._update_sensor_status = (
            lambda sensor_id, status, desc="": updates.append(
                (sensor_id, status, desc)
            )
        )

        launcher._match_and_update("OK   GoPro left: topics=1/1", "ok")
        launcher._match_and_update("FAIL GoPro right: 未发现", "error")

        self.assertEqual(
            updates[-1],
            ("gopro", "error", "至少一路异常"),
        )

    def test_running_window_hides_immediately_before_background_shutdown(self):
        launcher = object.__new__(self.launcher_module.ActLauncher)
        launcher._running = True
        launcher._closing = False
        launcher._cancel_start = threading.Event()
        calls = []
        launcher.withdraw = lambda: calls.append("withdraw")

        class CapturingThread:
            def __init__(self, target=None, daemon=None):
                self.target = target
                self.daemon = daemon

            def start(self):
                calls.append("thread")

        with (
            mock.patch.object(
                self.launcher_module.messagebox,
                "askyesno",
                return_value=True,
            ),
            mock.patch.object(
                self.launcher_module.threading,
                "Thread",
                CapturingThread,
            ),
        ):
            launcher._on_exit()

        self.assertEqual(calls, ["withdraw", "thread"])
        self.assertTrue(launcher._closing)
        self.assertTrue(launcher._cancel_start.is_set())


if __name__ == "__main__":
    unittest.main()
