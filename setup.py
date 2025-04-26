from setuptools import setup, find_packages

setup(
    name="trading_bot",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "alpaca-trade-api==2.3.0",
        "flask==2.2.5",
        "flask-socketio==5.3.6",
        "python-dotenv==0.19.0",
        "pandas==1.5.3",
        "numpy==1.24.3",
        "aiohttp==3.8.1",
        "requests==2.31.0",
        "websockets==10.4",
        "pytz==2023.3",
        "python-dateutil==2.8.2",
    ],
    python_requires=">=3.10",
) 