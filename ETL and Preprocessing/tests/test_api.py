import pytest
import json
import requests
import pandas as pd
from datetime import datetime, timedelta

# Production base URL
BASE_URL = 'http://jsh.maazmalik2004.space'

# Test data for Indian stocks
TEST_STOCKS = [
    {
        'symbol': 'RELIANCE.NS',
        'name': 'Reliance Industries',
        'sector': 'Energy'
    },
    {
        'symbol': 'TCS.NS',
        'name': 'Tata Consultancy Services',
        'sector': 'Technology'
    },
    {
        'symbol': 'HDFCBANK.NS',
        'name': 'HDFC Bank',
        'sector': 'Financial Services'
    }
]

def test_valuation_ratios_endpoint():
    """Test the valuation ratios endpoint with real stocks."""
    for stock in TEST_STOCKS:
        response = requests.post(
            f"{BASE_URL}/valuation_ratios",
            json={
                'company': stock['symbol'],
                'duration': '1d'
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert 'time_series_ratios' in data
        assert 'current_ratios' in data
        
        # Verify current ratios format
        current_ratios = data['current_ratios']
        assert all(key in current_ratios for key in [
            'volume', 'currentPrice', 'highLow', 'stockPE',
            'evbyrevenue', 'roa', 'evbyebita', 'roe', 'grossmargin'
        ])
        
        # Verify data types
        assert isinstance(current_ratios['volume'], str)
        assert isinstance(current_ratios['currentPrice'], str)
        assert isinstance(current_ratios['highLow'], str)
        
        # Verify time series data if available
        if data['time_series_ratios']:
            first_date = list(data['time_series_ratios'].keys())[0]
            first_data = data['time_series_ratios'][first_date]
            assert all(key in first_data for key in [
                'Open', 'High', 'Low', 'Close', 'Volume', 'StockPrice'
            ])

def test_company_overview_endpoint():
    """Test the company overview endpoint with real stocks."""
    for stock in TEST_STOCKS:
        response = requests.get(f"{BASE_URL}/company_overview/{stock['symbol']}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert all(key in data for key in [
            'name', 'sector', 'industry', 'description', 'employees',
            'country', 'website', 'market_cap', 'pe_ratio',
            'dividend_yield', 'beta', 'exchange'
        ])
        
        # Verify company specific data
        assert data['sector'] == stock['sector']
        assert data['name'] == stock['name']
        assert data['exchange'] in ['NSE', 'BSE']

def test_peer_comparison_endpoint():
    """Test the peer comparison endpoint with real stocks."""
    for stock in TEST_STOCKS:
        response = requests.get(f"{BASE_URL}/peer_comparison/{stock['symbol']}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if data:
            first_peer = data[0]
            assert all(key in first_peer for key in [
                'name', 'cmp', 'pe', 'divYield', 'npQt', 'qtrProfitVar',
                'salesQt', 'qtrSalesVar', 'roce', 'evEbitda'
            ])
            
            # Verify data types
            assert isinstance(first_peer['name'], str)
            assert isinstance(first_peer['cmp'], (int, float))
            assert isinstance(first_peer['pe'], (int, float))

def test_quarterly_results_endpoint():
    """Test the quarterly results endpoint with real stocks."""
    for stock in TEST_STOCKS:
        response = requests.get(f"{BASE_URL}/quarterly_results/{stock['symbol']}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if data:
            first_quarter = data[0]
            assert all(key in first_quarter for key in [
                'quarter', 'sales', 'expenses', 'profit'
            ])
            
            # Verify data types and values
            assert isinstance(first_quarter['quarter'], str)
            assert isinstance(first_quarter['sales'], (int, float))
            assert isinstance(first_quarter['expenses'], (int, float))
            assert isinstance(first_quarter['profit'], (int, float))
            assert first_quarter['sales'] >= first_quarter['profit']

def test_shareholding_pattern_endpoint():
    """Test the shareholding pattern endpoint with real stocks."""
    for stock in TEST_STOCKS:
        response = requests.get(f"{BASE_URL}/shareholding_pattern/{stock['symbol']}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if data:
            first_pattern = data[0]
            assert all(key in first_pattern for key in [
                'date', 'promoters', 'fils', 'dils', 'government',
                'public', 'shareholders'
            ])
            
            # Verify data types and values
            assert isinstance(first_pattern['date'], str)
            assert isinstance(first_pattern['promoters'], (int, float))
            assert isinstance(first_pattern['shareholders'], int)
            
            # Verify total percentage is approximately 100%
            total_percentage = (
                first_pattern['promoters'] +
                first_pattern['fils'] +
                first_pattern['dils'] +
                first_pattern['government'] +
                first_pattern['public']
            )
            assert abs(total_percentage - 100) < 1  # Allow 1% margin of error

def test_cash_flow_endpoint():
    """Test the cash flow endpoint with real stocks."""
    for stock in TEST_STOCKS:
        response = requests.get(f"{BASE_URL}/cash_flow/{stock['symbol']}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if data:
            first_flow = data[0]
            assert all(key in first_flow for key in [
                'year', 'operating', 'investing', 'financing', 'net'
            ])
            
            # Verify data types
            assert isinstance(first_flow['year'], str)
            assert all(isinstance(first_flow[key], (int, float)) 
                      for key in ['operating', 'investing', 'financing', 'net'])
            
            # Verify net cash flow calculation
            calculated_net = (
                first_flow['operating'] +
                first_flow['investing'] +
                first_flow['financing']
            )
            assert abs(calculated_net - first_flow['net']) < 1  # Allow rounding differences

def test_balance_sheet_endpoint():
    """Test the balance sheet endpoint with real stocks."""
    for stock in TEST_STOCKS:
        response = requests.get(f"{BASE_URL}/balance_sheet/{stock['symbol']}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if data:
            first_sheet = data[0]
            assert all(key in first_sheet for key in [
                'year', 'equity', 'reserves', 'borrowings', 'fixedAssets'
            ])
            
            # Verify data types
            assert isinstance(first_sheet['year'], str)
            assert all(isinstance(first_sheet[key], (int, float))
                      for key in ['equity', 'reserves', 'borrowings', 'fixedAssets'])

def test_stock_price_endpoint():
    """Test the stock price endpoint with real stocks."""
    durations = ['1d', '7d', '1mo', '6mo', '1y']
    
    for stock in TEST_STOCKS:
        for duration in durations:
            response = requests.get(
                f"{BASE_URL}/stock_price/{stock['symbol']}",
                params={'duration': duration}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert isinstance(data, list)
            if data:
                first_price = data[0]
                assert all(key in first_price for key in ['date', 'value', 'volume'])
                
                # Verify data types
                assert isinstance(first_price['date'], str)
                assert isinstance(first_price['value'], (int, float))
                assert isinstance(first_price['volume'], int)
                
                # Verify chronological order
                if len(data) > 1:
                    dates = [datetime.strptime(price['date'], '%d %b %Y') for price in data]
                    assert all(dates[i] <= dates[i+1] for i in range(len(dates)-1))

def test_technical_indicators_endpoint():
    """Test the technical indicators endpoint with real stocks."""
    for stock in TEST_STOCKS:
        response = requests.get(f"{BASE_URL}/technical_indicators/{stock['symbol']}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify indicators structure
        if 'indicators' in data:
            indicators = data['indicators']
            assert any(indicator in indicators for indicator in [
                'SMA20', 'SMA50', 'RSI', 'MACD', 'BB_upper', 'BB_lower'
            ])
            
            # Verify data types
            for value in indicators.values():
                assert isinstance(value, (int, float, type(None)))

def test_company_news_endpoint():
    """Test the company news endpoint with real stocks."""
    for stock in TEST_STOCKS:
        response = requests.get(f"{BASE_URL}/company_news/{stock['symbol']}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if data:
            first_news = data[0]
            assert all(key in first_news for key in ['headline', 'link', 'date'])
            
            # Verify data types
            assert isinstance(first_news['headline'], str)
            assert isinstance(first_news['link'], str)
            assert isinstance(first_news['date'], str)

def test_investment_thesis_endpoint():
    """Test the investment thesis endpoint with real stocks."""
    for stock in TEST_STOCKS:
        response = requests.get(f"{BASE_URL}/investment_thesis/{stock['symbol']}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert all(key in data for key in [
            'ticker', 'company_name', 'fundamental_analysis',
            'news_impact', 'investment_thesis', 'timestamp'
        ])
        
        # Verify data types
        assert isinstance(data['ticker'], str)
        assert isinstance(data['company_name'], str)
        assert isinstance(data['fundamental_analysis'], str)
        assert isinstance(data['news_impact'], str)
        assert isinstance(data['investment_thesis'], str)
        assert isinstance(data['timestamp'], str)

def test_error_handling():
    """Test error handling for invalid requests."""
    # Test invalid ticker
    response = requests.get(f"{BASE_URL}/company_overview/INVALID")
    assert response.status_code == 404
    
    # Test missing data in request
    response = requests.post(f"{BASE_URL}/valuation_ratios", json={})
    assert response.status_code == 500
    
    # Test invalid duration
    response = requests.get(
        f"{BASE_URL}/stock_price/RELIANCE.NS",
        params={'duration': 'invalid'}
    )
    assert response.status_code in [400, 500]  # Either is acceptable

def test_rate_limiting():
    """Test rate limiting by making rapid requests."""
    # Make 10 rapid requests
    responses = []
    for _ in range(10):
        response = requests.get(f"{BASE_URL}/company_overview/RELIANCE.NS")
        responses.append(response.status_code)
        
    # Verify that not all requests were rejected
    assert 200 in responses
    
    # If rate limiting is implemented, some requests should be rejected
    if 429 in responses:  # HTTP 429 Too Many Requests
        print("Rate limiting is active")

if __name__ == '__main__':
    pytest.main(['-v', '--tb=short']) 