# Configuration

This guide covers all configuration options for the IntellectScout Trading Bot.

## Environment Variables

### Required Variables

```bash
# Secret key for Flask sessions (generate with: python -c "import secrets; print(secrets.token_hex(32))")
SECRET_KEY=your-secret-key-here

# Encryption key for storing Alpaca credentials (generate with: python -c "from src.utils.encryption import generate_encryption_key; print(generate_encryption_key())")
ENCRYPTION_KEY=your-encryption-key-here

# Database URL
SQLALCHEMY_DATABASE_URI=postgresql://user:password@localhost/trading_bot
# Or for SQLite: sqlite:///trading_bot.db
```

### Email Configuration

```bash
# Resend API key for sending emails
RESEND_API_KEY=your-resend-api-key

# Email sender address
EMAIL_FROM=noreply@intellectscout.com

# Application URL (for email links)
APP_URL=https://intellectscout.com
```

### Trading Configuration

```bash
# Default trading symbols (comma-separated)
DEFAULT_TRADING_SYMBOLS=AAPL,MSFT,GOOGL

# Default strategy symbols
DEFAULT_STRATEGY_SYMBOLS=AAPL,MSFT,GOOGL
```

### Server Configuration

```bash
# Flask port
FLASK_RUN_PORT=5002

# Frontend port
VITE_PORT=5173

# Flask environment
FLASK_ENV=development  # or production
```

## Configuration Files

### Backend Configuration

Configuration is managed through:
- `src/config/constants.py` - Application constants
- `src/config/development.py` - Development settings
- `src/config/staging.py` - Staging settings
- `src/config/production.py` - Production settings

### Frontend Configuration

Frontend configuration uses Vite environment variables:
- `VITE_API_URL` - Backend API URL (set at build time)

## Security Best Practices

1. **Never commit `.env` files** - They contain sensitive credentials
2. **Use strong secret keys** - Generate unique keys for each environment
3. **Rotate encryption keys** - If compromised, users must re-enter credentials
4. **Use HTTPS in production** - Always use SSL/TLS for production deployments

## Environment-Specific Configuration

### Development

```bash
FLASK_ENV=development
DEBUG=True
SQLALCHEMY_DATABASE_URI=sqlite:///dev.db
```

### Staging

```bash
FLASK_ENV=staging
DEBUG=False
SQLALCHEMY_DATABASE_URI=postgresql://user:pass@staging-db/trading_bot
```

### Production

```bash
FLASK_ENV=production
DEBUG=False
SQLALCHEMY_DATABASE_URI=postgresql://user:pass@prod-db/trading_bot
ALLOWED_ORIGINS=https://intellectscout.com
```

## Next Steps

- [Quick Start Guide](quick-start.md)
- [User Guide](../user-guide/authentication.md)
