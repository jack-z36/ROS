from setuptools import find_packages, setup


package_name = 'gopro_camera_launch'


setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/gopro_pose_record.launch.py']),
        (
            'share/' + package_name + '/config',
            [
                'config/gopro_camera.yaml',
            ],
        ),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Codex',
    maintainer_email='codex@example.com',
    description='ROS 2 launch package for starting the GoPro HDMI camera node only.',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [],
    },
)
