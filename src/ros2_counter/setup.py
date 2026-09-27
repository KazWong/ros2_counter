from setuptools import find_packages, setup

package_name = 'ros2_counter'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ROS Counter maintainers',
    maintainer_email='maintainer@example.com',
    description='ROS counter publisher and GUI subscriber',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'counter_publisher = ros2_counter.publisher:main',
            'counter_subscriber_gui = ros2_counter.subscriber:main',
        ],
    },
)
