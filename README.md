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
