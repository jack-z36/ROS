from glob import glob

from setuptools import find_packages, setup

package_name = "elephant_gripper"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["tests", "tests.*"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/config", glob("config/*.yaml")),
        ("share/" + package_name + "/config", glob("config/*.rules")),
        ("share/" + package_name + "/launch", glob("launch/*.py")),
    ],
    install_requires=["setuptools", "pyserial", "PyYAML"],
    zip_safe=True,
    maintainer="ACT Model Deploy Maintainer",
    maintainer_email="maintainer@example.com",
    description=(
        "ROS 2 driver node for the dual Elephant myGripper-F100 force grippers "
        "over USB-485 (custom Modbus frames)."
    ),
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "elephant_gripper_node = elephant_gripper.ui.elephant_gripper_node:main",
        ],
    },
)
