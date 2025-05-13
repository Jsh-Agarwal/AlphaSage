from Datapipeline.yfinance_manager import YFinanceManager
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_market_data(yfm, ticker):
    """Test data fetching for a specific ticker"""
    print(f"\nTesting {ticker}:")
    print("-" * 50)
    
    data = yfm.get_ticker_data(ticker)
    print("Data received:", bool(data))
    
    if data:
        print("\nData keys:", list(data.keys()))
        
        if 'history' in data and not data['history'].empty:
            print("\nHistory data head:")
            print(data['history'].head())
            
            print("\nCalculating technical indicators...")
            indicators = yfm.calculate_technical_indicators(data['history'])
            if indicators and 'summary' in indicators:
                print("\nTechnical Analysis Summary:")
                print(indicators['summary'])
        
        if 'info' in data:
            print("\nFundamental Data Available:")
            info = data['info']
            fundamental_keys = [
                'marketCap', 'trailingPE', 'priceToBook', 'returnOnEquity',
                'profitMargins', 'operatingMargins', 'sector', 'industry'
            ]
            for key in fundamental_keys:
                if key in info:
                    print(f"{key}: {info[key]}")
        
        # Get fundamentals
        fundamentals = yfm.get_fundamentals(ticker)
        if fundamentals:
            print("\nFinancial Statements Available:")
            for statement, data in fundamentals.items():
                if data:
                    print(f"- {statement}")
    
    print("\n" + "="*80 + "\n")

def test_yfinance():
    """Test YFinance functionality for both US and Indian markets"""
    try:
        yfm = YFinanceManager()
        print("Created YFinanceManager instance")
        
        # Test US equity
        test_market_data(yfm, 'AAPL')
        
        # Test Indian equity
        test_market_data(yfm, 'TCS.NS')
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        logging.error(f"Test failed with error: {str(e)}", exc_info=True)

if __name__ == "__main__":
    test_yfinance() 