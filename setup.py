"""Setup script for AreaScan Profiler"""
from setuptools import setup, find_packages

setup(
    name='areascan-profiler',
    version='1.0.0',
    description='AreaScan Profiler - Test inference models on production machines',
    author='Ripcord Team',
    packages=find_packages(),
    install_requires=[
        'PyQt6>=6.7.0',
        'grpcio>=1.63.0',
        'grpcio-tools>=1.63.0',
        'protobuf>=4.25.3',
        'click>=8.1.7',
        'pillow>=10.3.0',
        'numpy>=1.26.4',
    ],
    entry_points={
        'console_scripts': [
            'areascan-profiler=areascan_profiler:main',
            'areascan-profiler-ui=areascan_profiler_ui:main',
        ],
    },
    python_requires='>=3.8',
)