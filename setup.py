from setuptools import setup

setup(
    name="benchmark",
    version="0.0.1",
    python_requires=">=3.8",
    entry_points={
        'console_scripts': [
            'main = packages.ycsb.cli:main',
        ]
    }
)
