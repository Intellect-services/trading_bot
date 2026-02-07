from setuptools import find_packages, setup

setup(
    name="trading_bot",
    version="0.1",
    packages=find_packages(where="src", exclude=["tests", "tests.*"]),
    package_dir={"": "src"},
)
