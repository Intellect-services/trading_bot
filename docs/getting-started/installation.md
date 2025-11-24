# Installation

This guide will help you install and set up the IntellectScout Trading Bot.

## Prerequisites

- Python 3.10 or higher
- Node.js 18+ and npm
- PostgreSQL (for production) or SQLite (for development)
- Alpaca API account (paper or live trading)

## Backend Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/betintellect-com/trading_bot.git
   cd trading_bot
   ```

2. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize the database**:
   ```bash
   python scripts/migrate_db.py
   ```

## Frontend Installation

1. **Navigate to frontend directory**:
   ```bash
   cd src/frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Set up environment variables**:
   ```bash
   # Create .env file
   echo "VITE_API_URL=http://localhost:5002" > .env
   ```

## Running the Application

### Development Mode

**Backend**:
```bash
python run.py
# Or use the isbot script
isbot start
```

**Frontend**:
```bash
cd src/frontend
npm run dev
```

### Production Mode

See the [Production Deployment](deployment/production.md) guide.

## Verification

1. Open http://localhost:5173 in your browser
2. Register a new account
3. Verify your email (check console for token in development)
4. Log in and configure your Alpaca credentials

## Next Steps

- [Configuration Guide](configuration.md)
- [Quick Start Guide](quick-start.md)
