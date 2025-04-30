from src.core.alpaca_service import AlpacaService
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_alpaca_connection():
    try:
        # Initialize AlpacaService
        service = AlpacaService()
        
        # Get account information
        account = service.get_account()
        if account:
            print("\nAccount Information:")
            print(f"Account ID: {account.get('account_id', 'N/A')}")
            print(f"Buying Power: ${float(account.get('buying_power', 0)):.2f}")
            print(f"Equity: ${float(account.get('equity', 0)):.2f}")
            print(f"Cash: ${float(account.get('cash', 0)):.2f}")
            print(f"Status: {account.get('status', 'N/A')}")
            
            # Get positions
            positions = service.get_positions()
            print("\nPositions:")
            for position in positions.get('positions', []):
                print(f"Symbol: {position.get('symbol')}")
                print(f"Quantity: {position.get('qty')}")
                print(f"Market Value: ${float(position.get('market_value', 0)):.2f}")
                print(f"Unrealized P/L: ${float(position.get('unrealized_pl', 0)):.2f}")
                print("---")
            
            return True
        else:
            print("Failed to get account information")
            return False
            
    except Exception as e:
        print(f"Error connecting to Alpaca: {str(e)}")
        return False

if __name__ == "__main__":
    test_alpaca_connection() 