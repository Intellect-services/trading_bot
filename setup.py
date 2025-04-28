from setuptools import setup, find_packages

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