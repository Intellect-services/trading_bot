from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetClass

def test_alpaca_connection():
    # Initialize trading client
    trading_client = TradingClient(
        api_key='PKY35GDVCNIHIETC45OF',
        paper=True  # Use paper trading
    )
    
    try:
        # Get account information
        account = trading_client.get_account()
        print("Account Status:", account.status)
        print("Buying Power:", account.buying_power)
        print("Cash:", account.cash)
        print("Equity:", account.equity)
        
        # Get available assets
        request = GetAssetsRequest(asset_class=AssetClass.US_EQUITY)
        assets = trading_client.get_all_assets(request)
        print("\nAvailable Assets:", len(assets))
        
        return True
        
    except Exception as e:
        print("Error connecting to Alpaca:", str(e))
        return False

if __name__ == "__main__":
    test_alpaca_connection() 