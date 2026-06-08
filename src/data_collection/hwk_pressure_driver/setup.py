from glob import glob
from setuptools import find_packages, setup


package_name = "hwk_pressure_driver"


setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/config", glob("config/*.yaml")),
        ("share/" + package_name + "/launch", glob("launch/*.py")),
    ],
    install_requires=["setuptools", "pyserial", "PyYAML"],
    zip_safe=True,
    maintainer="HWK Pressure Driver Maintainer",
    maintainer_email="maintainer@example.com",
    description="ROS 2 Python driver for HWK dexterous hand pressure sensors.",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "pressure_driver_node = hwk_pressure_driver.pressure_driver_node:main",
        ],
    },
)
