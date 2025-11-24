# IntellectScout Trading Bot

Welcome to the IntellectScout Trading Bot documentation!

## Overview

IntellectScout is a production-ready automated trading bot that enables users to:

- **Automated Trading**: Execute trading strategies automatically using Alpaca API
- **Real-time Monitoring**: Track positions, performance, and bot status in real-time
- **User Management**: Secure authentication with email verification and role-based access
- **Strategy Management**: Create, configure, and manage multiple trading strategies
- **Risk Management**: Built-in risk controls and position management

## Key Features

### 🔐 Security
- Encrypted credential storage
- Email verification
- Role-based access control (Trader, Admin, Owner)
- Secure session management

### 📊 Trading
- Paper and live trading modes
- Multiple strategy support
- Real-time position tracking
- Portfolio performance analytics

### 🛠️ Developer Experience
- Comprehensive test coverage
- Code quality tools (Ruff, mypy, bandit)
- Pre-commit hooks
- CI/CD pipeline

## Quick Links

- [Installation Guide](getting-started/installation.md) - Get started quickly
- [Configuration](getting-started/configuration.md) - Configure your environment
- [API Reference](api-reference/overview.md) - Complete API documentation
- [Development Guide](development/setup.md) - Contribute to the project

## Architecture

The trading bot consists of:

- **Backend**: Flask-based REST API with WebSocket support
- **Frontend**: React application with real-time updates
- **Database**: PostgreSQL (production) / SQLite (development)
- **Trading Engine**: Alpaca API integration

## Getting Help

- Check the [User Guide](user-guide/authentication.md) for common tasks
- Review the [API Reference](api-reference/overview.md) for technical details
- See [Development Guide](development/contributing.md) for contributing

## License

This project is licensed under the MIT License.
