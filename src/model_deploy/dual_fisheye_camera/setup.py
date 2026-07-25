import os
from glob import glob

from setuptools import setup


package_name = 'dual_fisheye_camera'


setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch',
         glob('launch/*.launch.py')),
        ('share/' + package_name + '/config',
         glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='model_deploy Maintainer',
    maintainer_email='maintainer@example.com',
    description=(
        'Dual fisheye camera node: publishes left/right fisheye Image via V4L2 '
        'and a HardwareHealth status.'
    ),
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'camera_health_node = dual_fisheye_camera.camera_health_node:main',
        ],
    },
)
