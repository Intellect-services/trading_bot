from setuptools import find_packages, setup

setup(
    name="trading_bot",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "flask",
        "flask-socketio",
        "alpaca-py",
        "pandas",
        "python-dotenv",
    ],
)
