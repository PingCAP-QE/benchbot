from setuptools import setup

setup(
    name="benchbot",
    version="0.0.1",
    python_requires=">=3.8",
    entry_points={
        'console_scripts': [
            'tpcc = packages.tpcc.cli:main',
            'sysbench = packages.sysbench.cli:main',
            'ycsb = packages.ycsb.cli:main',
        ]
    }
)
