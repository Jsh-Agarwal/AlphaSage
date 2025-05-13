from flask import Flask, jsonify, request
from flask_cors import CORS
import logging

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

@app.route('/valuation_ratios', methods=['POST'])
def get_valuation_ratios():
    """Get valuation ratios and time series data for a stock."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Missing request data'
            }), 500
            
        if 'company' not in data:
            return jsonify({
                'error': 'Missing required field: company'
            }), 500
            
        company = data.get('company', '').upper()
        duration = data.get('duration', '1d')
        
        # Mock data for testing
        time_series_ratios = {
            '2023-05-01': {
                'Open': 2450.0,
                'High': 2480.0,
                'Low': 2440.0,
                'Close': 2470.0,
                'Volume': 1000000,
                'StockPrice': 2470.0
            }
        }
        
        current_ratios = {
            'volume': '1000000',
            'currentPrice': '$2470.00',
            'highLow': '$2480.00 / $2440.00',
            'stockPE': 25.5,
            'evbyrevenue': '$2.5',
            'roa': '12.50%',
            'evbyebita': '$15.2',
            'roe': '18.75%',
            'grossmargin': '35.20%'
        }
        
        return jsonify({
            'time_series_ratios': time_series_ratios,
            'current_ratios': current_ratios
        })
        
    except Exception as e:
        logger.error(f"Error processing valuation ratios: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/company_overview/<ticker>', methods=['GET'])
def get_company_overview(ticker):
    """Get detailed company overview."""
    try:
        # Check if the ticker is just the placeholder ":symbol"
        if ticker == ":symbol":
            # Default to RELIANCE.NS if it's just the placeholder
            ticker = "RELIANCE.NS"
            
        # Find the stock in our test data
        stock = None
        for s in TEST_STOCKS:
            if s['symbol'] == ticker:
                stock = s
                break
                
        if not stock:
            # If still not found, create a default response
            return jsonify({
                'name': 'Reliance Industries',
                'sector': 'Energy',
                'industry': 'Oil & Gas',
                'description': 'Reliance Industries is a leading company in the Energy sector.',
                'employees': 236000,
                'country': 'India',
                'website': 'https://www.relianceindustries.com',
                'market_cap': 1750000000000,
                'pe_ratio': 25.5,
                'dividend_yield': 0.5,
                'beta': 1.2,
                'exchange': 'NSE'
            })
            
        # Return mock data with the correct exchange field
        overview = {
            'name': stock['name'],
            'sector': stock['sector'],
            'industry': 'Oil & Gas' if stock['symbol'] == 'RELIANCE.NS' else 'Technology' if stock['symbol'] == 'TCS.NS' else 'Banking',
            'description': f"{stock['name']} is a leading company in the {stock['sector']} sector.",
            'employees': 236000,
            'country': 'India',
            'website': f"https://www.{stock['name'].lower().replace(' ', '')}.com",
            'market_cap': 1750000000000,
            'pe_ratio': 25.5,
            'dividend_yield': 0.5,
            'beta': 1.2,
            'exchange': 'NSE' if ticker.endswith('.NS') else 'BSE'  # Fixed exchange field
        }
        
        return jsonify(overview)
        
    except Exception as e:
        logger.error(f"Error fetching company overview: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/peer_comparison/<ticker>', methods=['GET'])
def get_peer_comparison(ticker):
    """Get peer comparison data."""
    try:
        # Mock data for testing
        peer_data = [
            {
                'name': 'TCS',
                'cmp': 3500,
                'pe': 30.2,
                'divYield': 1.2,
                'npQt': 120,
                'qtrProfitVar': 15.5,
                'salesQt': 450,
                'qtrSalesVar': 12.3,
                'roce': 45.2,
                'evEbitda': 20.5
            },
            {
                'name': 'HDFCBANK',
                'cmp': 1650,
                'pe': 18.5,
                'divYield': 1.5,
                'npQt': 180,
                'qtrProfitVar': 18.2,
                'salesQt': 850,
                'qtrSalesVar': 15.7,
                'roce': 18.5,
                'evEbitda': 12.3
            }
        ]
        
        return jsonify(peer_data)
        
    except Exception as e:
        logger.error(f"Error fetching peer comparison: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/quarterly_results/<ticker>', methods=['GET'])
def get_quarterly_results(ticker):
    """Get quarterly financial results."""
    try:
        # Mock data for testing
        quarterly_data = [
            {
                'quarter': 'Mar 2023',
                'sales': 250000000000,
                'expenses': 180000000000,
                'profit': 70000000000
            },
            {
                'quarter': 'Dec 2022',
                'sales': 230000000000,
                'expenses': 170000000000,
                'profit': 60000000000
            }
        ]
        
        return jsonify(quarterly_data)
        
    except Exception as e:
        logger.error(f"Error fetching quarterly results: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/shareholding_pattern/<ticker>', methods=['GET'])
def get_shareholding_pattern(ticker):
    """Get shareholding pattern data."""
    try:
        # Mock data for testing
        shareholding_data = [
            {
                'date': 'Mar 2023',
                'promoters': 50.31,
                'fils': 22.06,
                'dils': 16.98,
                'government': 0.19,
                'public': 10.46,
                'shareholders': 3463276
            },
            {
                'date': 'Dec 2022',
                'promoters': 50.13,
                'fils': 19.16,
                'dils': 19.02,
                'government': 0.18,
                'public': 11.52,
                'shareholders': 4714599
            }
        ]
        
        return jsonify(shareholding_data)
        
    except Exception as e:
        logger.error(f"Error fetching shareholding pattern: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/cash_flow/<ticker>', methods=['GET'])
def get_cash_flow(ticker):
    """Get cash flow data."""
    try:
        # Mock data for testing
        cash_flow_data = [
            {
                'year': 'Mar 2023',
                'operating': 85000000000,
                'investing': -45000000000,
                'financing': -20000000000,
                'net': 20000000000
            },
            {
                'year': 'Mar 2022',
                'operating': 75000000000,
                'investing': -40000000000,
                'financing': -15000000000,
                'net': 20000000000
            }
        ]
        
        return jsonify(cash_flow_data)
        
    except Exception as e:
        logger.error(f"Error fetching cash flow data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/balance_sheet/<ticker>', methods=['GET'])
def get_balance_sheet(ticker):
    """Get balance sheet data."""
    try:
        # Mock data for testing
        balance_sheet_data = [
            {
                'year': 'Mar 2023',
                'equity': 500000000000,
                'reserves': 300000000000,
                'borrowings': 250000000000,
                'fixedAssets': 800000000000
            },
            {
                'year': 'Mar 2022',
                'equity': 450000000000,
                'reserves': 270000000000,
                'borrowings': 230000000000,
                'fixedAssets': 750000000000
            }
        ]
        
        return jsonify(balance_sheet_data)
        
    except Exception as e:
        logger.error(f"Error fetching balance sheet data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/stock_price/<ticker>', methods=['GET'])
def get_stock_price(ticker):
    """Get historical stock price data."""
    try:
        duration = request.args.get('duration', '1y')
        
        # Validate duration parameter
        valid_durations = ['1d', '7d', '1mo', '6mo', '1y']
        if duration not in valid_durations:
            return jsonify({'error': f'Invalid duration. Must be one of: {", ".join(valid_durations)}'}), 400
            
        # Mock data for testing
        price_data = [
            {
                'date': '01 May 2023',
                'value': 2470.5,
                'volume': 1000000
            },
            {
                'date': '02 May 2023',
                'value': 2480.2,
                'volume': 1200000
            }
        ]
        
        return jsonify(price_data)
        
    except Exception as e:
        logger.error(f"Error fetching stock price data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/technical_indicators/<ticker>', methods=['GET'])
def get_technical_indicators(ticker):
    """Get technical indicators for a stock."""
    try:
        # Mock data for testing
        indicators = {
            'indicators': {
                'SMA20': 2450.5,
                'SMA50': 2400.2,
                'RSI': 65.5,
                'MACD': 25.3,
                'BB_upper': 2520.5,
                'BB_lower': 2380.5
            }
        }
        
        return jsonify(indicators)
        
    except Exception as e:
        logger.error(f"Error calculating technical indicators: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/company_news/<ticker>', methods=['GET'])
def get_company_news(ticker):
    """Get recent news for a company."""
    try:
        # Mock data for testing
        news = [
            {
                'headline': 'Reliance Industries reports 15% growth in Q4 profit',
                'link': 'https://example.com/news/1',
                'date': '2023-05-01'
            },
            {
                'headline': 'Reliance to invest $10 billion in green energy',
                'link': 'https://example.com/news/2',
                'date': '2023-04-28'
            }
        ]
        
        return jsonify(news)
        
    except Exception as e:
        logger.error(f"Error fetching company news: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/investment_thesis/<ticker>', methods=['GET'])
def get_investment_thesis(ticker):
    """Get AI-generated investment thesis."""
    try:
        # Find the stock in our test data
        stock = None
        for s in TEST_STOCKS:
            if s['symbol'] == ticker:
                stock = s
                break
                
        if not stock:
            return jsonify({
                'ticker': ticker,
                'company_name': ticker,
                'fundamental_analysis': 'Company not found',
                'news_impact': 'Company not found',
                'investment_thesis': 'Company not found',
                'timestamp': '2023-05-01T12:00:00Z'
            }), 404
            
        # Mock data for testing
        thesis = {
            'ticker': ticker,
            'company_name': stock['name'],
            'fundamental_analysis': f"{stock['name']} has shown strong growth in its core businesses...",
            'news_impact': 'Recent news about expansion is positive for long-term growth...',
            'investment_thesis': 'Based on current valuations and growth prospects, this is a good long-term investment...',
            'timestamp': '2023-05-01T12:00:00Z'
        }
        
        return jsonify(thesis)
        
    except Exception as e:
        logger.error(f"Error generating investment thesis: {e}")
        return jsonify({
            'ticker': ticker,
            'company_name': ticker,
            'fundamental_analysis': f'Error: {str(e)}',
            'news_impact': 'Error occurred during analysis',
            'investment_thesis': 'Unable to generate thesis',
            'timestamp': '2023-05-01T12:00:00Z'
        })

if __name__ == '__main__':
    app.run(debug=True, port=7500)