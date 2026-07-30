import importlib.util
import subprocess
import unittest
from pathlib import Path
from unittest import mock


WORKSPACE_DIR = Path(__file__).resolve().parents[2]
STATUS_SCRIPT = WORKSPACE_DIR / "scripts" / "all_sensor_status.py"


def load_module():
    spec = importlib.util.spec_from_file_location("all_sensor_status", STATUS_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BatonNetworkPreflightTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.status = load_module()

    def test_direct_usb_subnet_is_accepted(self):
        route = subprocess.CompletedProcess(
            [],
            0,
            '[{"dst":"192.168.1.10","dev":"enx123","prefsrc":"192.168.1.18"}]',
            "",
        )
        address = subprocess.CompletedProcess(
            [],
            0,
            '[{"ifname":"enx123","addr_info":['
            '{"family":"inet","local":"192.168.1.18","prefixlen":24}]}]',
            "",
        )
        with mock.patch.object(self.status, "run", side_effect=[route, address]):
            ok, device, source, reason = self.status.baton_direct_route(
                "192.168.1.10"
            )

        self.assertTrue(ok)
        self.assertEqual(device, "enx123")
        self.assertEqual(source, "192.168.1.18")
        self.assertEqual(reason, "")

    def test_tun_gateway_route_is_rejected(self):
        route = subprocess.CompletedProcess(
            [],
            0,
            '[{"dst":"192.168.1.10","gateway":"198.18.0.2",'
            '"dev":"Meta","prefsrc":"198.18.0.1"}]',
            "",
        )
        with mock.patch.object(self.status, "run", return_value=route) as run:
            ok, device, source, reason = self.status.baton_direct_route(
                "192.168.1.10"
            )

        self.assertFalse(ok)
        self.assertEqual(device, "Meta")
        self.assertEqual(source, "198.18.0.1")
        self.assertIn("不是 Baton USB 直连网卡", reason)
        run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
