# Trading Bot

A Python-based trading bot for stock market trading using Alpaca API. This bot provides real-time market monitoring, automated trading, and a modern web-based dashboard for monitoring and analysis.

## Features

- Real-time market data monitoring
- Automated trading strategies
- Position management
- Configurable trading parameters
- Modern web dashboard with real-time updates
- Price chart visualization
- Performance metrics tracking
- Paper trading support

## Dashboard Features

### Price Chart Interpretation

The dashboard includes a real-time price chart that displays the trading symbol's price movements. Here's how to interpret the chart:

1. **Price Line**

   - The blue line represents the current price of the trading symbol
   - The area below the line is filled with a light blue gradient for better visualization
   - The line is smoothed using a tension parameter for better readability

2. **Time Scale**

   - The x-axis shows timestamps of price updates
   - Time labels are automatically adjusted to prevent overcrowding
   - The chart displays the last 50 price points for optimal performance

3. **Price Scale**

   - The y-axis shows the price in USD
   - Prices are formatted with 2 decimal places
   - The scale automatically adjusts to show the relevant price range

4. **Interactive Features**

   - Hover over the chart to see detailed price information
   - The tooltip shows the exact price and timestamp
   - The chart responds to mouse movements in real-time

5. **Visual Indicators**
   - Price increases are shown in green
   - Price decreases are shown in red
   - The chart updates automatically with new price data

The chart is designed to help you:

- Monitor price trends in real-time
- Identify support and resistance levels
- Track price volatility
- Make informed trading decisions

## Installation

1. Clone the repository:

```bash
git clone https://github.com/betintellect-com/trading_bot.git
cd trading_bot
```

2. Create a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with your Alpaca API credentials:

```
ALPACA_API_KEY=your_api_key
ALPACA_SECRET_KEY=your_secret_key
```

## Usage

### Running the Bot

```bash
python3 src/main.py
```

### Running the Mock Version (for testing)

```bash
python3 src/mock_app.py
```

The dashboard will be available at `http://localhost:5000`

## Project Structure

```
trading_bot/
├── src/
│   ├── main.py              # Main bot application
│   ├── mock_app.py          # Mock version for testing
│   ├── core/
│   │   ├── bot.py           # Trading bot core logic
│   │   └── strategy.py      # Trading strategies
│   ├── backtesting/
│   │   ├── engine.py        # Backtesting engine
│   │   └── metrics.py       # Performance metrics
│   ├── utils/
│   │   ├── config.py        # Configuration management
│   │   └── data_handler.py  # Data handling utilities
│   └── templates/
│       └── index.html       # Dashboard template
├── requirements.txt         # Project dependencies
├── .env.example            # Example environment variables
└── README.md               # Project documentation
```

## Configuration

Edit `src/utils/config.py` to modify:

- Trading parameters
- Strategy settings
- Risk management rules
- Market hours
- Data storage settings

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This trading bot is for educational purposes only. Always test thoroughly before using with real money. The developers are not responsible for any financial losses incurred through the use of this software.

# Trading Bot Manual

## Prerequisites

1. Python 3.8 or higher
2. Virtual environment (recommended)
3. Alpaca API credentials (for live trading)

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd trading_bot
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

1. Create a `.env` file in the project root with your Alpaca API credentials:

```env
ALPACA_API_KEY=your_api_key
ALPACA_SECRET_KEY=your_secret_key
```

2. Configure trading parameters in `src/utils/config.py`:

- Initial capital
- Trading symbols
- Risk management parameters
- Trading strategy parameters

## Starting the Bot

### Method 1: Web Interface (Recommended)

1. Start the web server:

```bash
PYTHONPATH=$PYTHONPATH:. python src/web_server.py
```

2. Open your web browser and navigate to:

```
http://127.0.0.1:5050
```

### Method 2: Command Line

1. Start the bot directly:

```bash
PYTHONPATH=$PYTHONPATH:. python src/core/bot.py
```

## Monitoring the Bot

### Web Dashboard Features

1. **Bot Status Panel**

   - Runtime: Shows how long the bot has been running
   - Market Status: Indicates if the market is open or closed
   - Last Update: Timestamp of the last data refresh

2. **Account Information**

   - Equity: Total account value
   - Cash: Available cash balance
   - Buying Power: Available funds for trading
   - Unrealized P&L: Current profit/loss from open positions

3. **Positions Overview**

   - Symbol: Trading symbol
   - Quantity: Number of shares held
   - Average Price: Average entry price
   - Current Price: Latest market price
   - Market Value: Current position value
   - P&L: Profit/loss for each position

4. **Price Chart**

   - Real-time price movement
   - Technical indicators (if configured)
   - Zoom and pan controls
   - Time period selection

5. **Logs Panel**
   - Real-time trading activity
   - Error messages
   - System notifications
   - Order execution details

### Important Monitoring Points

1. **Market Hours**

   - Regular trading hours: 9:30 AM - 4:00 PM EST
   - Extended hours: 4:00 PM - 8:00 PM EST
   - The bot will automatically handle market open/close

2. **Risk Management**

   - Monitor position sizes
   - Check stop-loss levels
   - Watch for margin requirements
   - Track drawdown limits

3. **Performance Metrics**
   - Daily P&L
   - Win rate
   - Average trade duration
   - Maximum drawdown

## Troubleshooting

1. **Common Issues**

   a. Connection Problems

   - Check internet connection
   - Verify API credentials
   - Ensure market is open

   b. Trading Errors

   - Insufficient funds
   - Invalid order parameters
   - Rate limit exceeded

2. **Log Analysis**

   - Check the logs panel for error messages
   - Look for "ERROR" level messages
   - Review order execution details

3. **Restarting the Bot**
   - Stop the current process (Ctrl+C)
   - Wait 30 seconds
   - Restart using the same command

## Best Practices

1. **Before Starting**

   - Verify API credentials
   - Check market hours
   - Review risk parameters
   - Ensure sufficient capital

2. **During Operation**

   - Monitor the dashboard regularly
   - Check for error messages
   - Verify order execution
   - Watch position sizes

3. **Risk Management**
   - Don't exceed position limits
   - Monitor drawdown
   - Check margin requirements
   - Review stop-loss levels

## Support

For issues or questions:

1. Check the logs for error messages
2. Review the documentation
3. Contact support with:
   - Error messages
   - Log snippets
   - Screenshots of the dashboard

## Security Notes

1. Keep your API credentials secure
2. Don't share your `.env` file
3. Use strong passwords
4. Monitor for unauthorized access

## Maintenance

1. Regular Updates

   - Check for new versions
   - Update dependencies
   - Review configuration

2. Performance Monitoring

   - Check system resources
   - Monitor API usage
   - Review trading performance

3. Backup
   - Regular configuration backups
   - Save trading logs
   - Export performance data
