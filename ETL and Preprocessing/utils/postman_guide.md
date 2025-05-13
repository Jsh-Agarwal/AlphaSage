# Financial Data API Testing Guide for Postman

This guide provides instructions for testing the Financial Data API using Postman.

## Setup

1. Download and install Postman from [https://www.postman.com/downloads/](https://www.postman.com/downloads/)
2. Create a new collection called "Financial Data API"

## Base URL

All API requests will use this base URL:
```
http://jsh.maazmalik2004.space
```

## API Endpoints

### 1. Valuation Ratios

**Endpoint:** `/valuation_ratios`  
**Method:** POST  
**Headers:** Content-Type: application/json  
**Body:**
```json
{
  "company": "RELIANCE.NS",
  "duration": "1d"
}
```

**Expected Response:**
```json
{
  "time_series_ratios": {
    "2023-05-01": {
      "Open": 2450.0,
      "High": 2480.0,
      "Low": 2440.0,
      "Close": 2470.0,
      "Volume": 1000000,
      "StockPrice": 2470.0
    }
  },
  "current_ratios": {
    "volume": "1000000",
    "currentPrice": "$2470.00",
    "highLow": "$2480.00 / $2440.00",
    "stockPE": 25.5,
    "evbyrevenue": "$2.5",
    "roa": "12.50%",
    "evbyebita": "$15.2",
    "roe": "18.75%",
    "grossmargin": "35.20%"
  }
}
```

### 2. Company Overview

**Endpoint:** `/company_overview/{ticker}`  
**Method:** GET  
**Example:** `/company_overview/RELIANCE.NS`

**Expected Response:**
```json
{
  "name": "Reliance Industries",
  "sector": "Energy",
  "industry": "Oil & Gas",
  "description": "Reliance Industries Limited is an Indian multinational conglomerate...",
  "employees": 236000,
  "country": "India",
  "website": "https://www.ril.com",
  "market_cap": 1750000000000,
  "pe_ratio": 25.5,
  "dividend_yield": 0.5,
  "beta": 1.2,
  "exchange": "NSE"
}
```

### 3. Peer Comparison

**Endpoint:** `/peer_comparison/{ticker}`  
**Method:** GET  
**Example:** `/peer_comparison/RELIANCE.NS`

**Expected Response:**
```json
[
  {
    "name": "TCS",
    "cmp": 3500,
    "pe": 30.2,
    "divYield": 1.2,
    "npQt": 120,
    "qtrProfitVar": 15.5,
    "salesQt": 450,
    "qtrSalesVar": 12.3,
    "roce": 45.2,
    "evEbitda": 20.5
  },
  {
    "name": "HDFCBANK",
    "cmp": 1650,
    "pe": 18.5,
    "divYield": 1.5,
    "npQt": 180,
    "qtrProfitVar": 18.2,
    "salesQt": 850,
    "qtrSalesVar": 15.7,
    "roce": 18.5,
    "evEbitda": 12.3
  }
]
```

### 4. Quarterly Results

**Endpoint:** `/quarterly_results/{ticker}`  
**Method:** GET  
**Example:** `/quarterly_results/RELIANCE.NS`

**Expected Response:**
```json
[
  {
    "quarter": "Mar 2023",
    "sales": 250000000000,
    "expenses": 180000000000,
    "profit": 70000000000
  },
  {
    "quarter": "Dec 2022",
    "sales": 230000000000,
    "expenses": 170000000000,
    "profit": 60000000000
  }
]
```

### 5. Shareholding Pattern

**Endpoint:** `/shareholding_pattern/{ticker}`  
**Method:** GET  
**Example:** `/shareholding_pattern/RELIANCE.NS`

**Expected Response:**
```json
[
  {
    "date": "Mar 2023",
    "promoters": 50.31,
    "fils": 22.06,
    "dils": 16.98,
    "government": 0.19,
    "public": 10.46,
    "shareholders": 3463276
  },
  {
    "date": "Dec 2022",
    "promoters": 50.13,
    "fils": 19.16,
    "dils": 19.02,
    "government": 0.18,
    "public": 11.52,
    "shareholders": 4714599
  }
]
```

### 6. Cash Flow

**Endpoint:** `/cash_flow/{ticker}`  
**Method:** GET  
**Example:** `/cash_flow/RELIANCE.NS`

**Expected Response:**
```json
[
  {
    "year": "Mar 2023",
    "operating": 85000000000,
    "investing": -45000000000,
    "financing": -20000000000,
    "net": 20000000000
  },
  {
    "year": "Mar 2022",
    "operating": 75000000000,
    "investing": -40000000000,
    "financing": -15000000000,
    "net": 20000000000
  }
]
```

### 7. Balance Sheet

**Endpoint:** `/balance_sheet/{ticker}`  
**Method:** GET  
**Example:** `/balance_sheet/RELIANCE.NS`

**Expected Response:**
```json
[
  {
    "year": "Mar 2023",
    "equity": 500000000000,
    "reserves": 300000000000,
    "borrowings": 250000000000,
    "fixedAssets": 800000000000
  },
  {
    "year": "Mar 2022",
    "equity": 450000000000,
    "reserves": 270000000000,
    "borrowings": 230000000000,
    "fixedAssets": 750000000000
  }
]
```

### 8. Stock Price

**Endpoint:** `/stock_price/{ticker}`  
**Method:** GET  
**Query Parameters:** duration (1d, 7d, 1mo, 6mo, 1y)  
**Example:** `/stock_price/RELIANCE.NS?duration=1mo`

**Expected Response:**
```json
[
  {
    "date": "01 May 2023",
    "value": 2470.5,
    "volume": 1000000
  },
  {
    "date": "02 May 2023",
    "value": 2480.2,
    "volume": 1200000
  }
]
```

### 9. Technical Indicators

**Endpoint:** `/technical_indicators/{ticker}`  
**Method:** GET  
**Example:** `/technical_indicators/RELIANCE.NS`

**Expected Response:**
```json
{
  "indicators": {
    "SMA20": 2450.5,
    "SMA50": 2400.2,
    "RSI": 65.5,
    "MACD": 25.3,
    "BB_upper": 2520.5,
    "BB_lower": 2380.5
  }
}
```

### 10. Company News

**Endpoint:** `/company_news/{ticker}`  
**Method:** GET  
**Example:** `/company_news/RELIANCE.NS`

**Expected Response:**
```json
[
  {
    "headline": "Reliance Industries reports 15% growth in Q4 profit",
    "link": "https://example.com/news/1",
    "date": "2023-05-01"
  },
  {
    "headline": "Reliance to invest $10 billion in green energy",
    "link": "https://example.com/news/2",
    "date": "2023-04-28"
  }
]
```

### 11. Investment Thesis

**Endpoint:** `/investment_thesis/{ticker}`  
**Method:** GET  
**Example:** `/investment_thesis/RELIANCE.NS`

**Expected Response:**
```json
{
  "ticker": "RELIANCE.NS",
  "company_name": "Reliance Industries",
  "fundamental_analysis": "Reliance Industries has shown strong growth in its retail and digital businesses...",
  "news_impact": "Recent news about expansion in green energy is positive for long-term growth...",
  "investment_thesis": "Based on current valuations and growth prospects, Reliance is a good long-term investment...",
  "timestamp": "2023-05-01T12:00:00Z"
}
```

## Error Handling Tests

### 1. Invalid Ticker

**Endpoint:** `/company_overview/INVALID`  
**Method:** GET  
**Expected Response:** Status code 404

### 2. Missing Data in Request

**Endpoint:** `/valuation_ratios`  
**Method:** POST  
**Headers:** Content-Type: application/json  
**Body:** `{}`  
**Expected Response:** Status code 500

### 3. Invalid Duration

**Endpoint:** `/stock_price/RELIANCE.NS?duration=invalid`  
**Method:** GET  
**Expected Response:** Status code 400 or 500

## Rate Limiting Test

Make multiple rapid requests to any endpoint to test rate limiting:
**Endpoint:** `/company_overview/RELIANCE.NS`  
**Method:** GET  
**Expected Response:** Some requests may return status code 429 (Too Many Requests)

## Creating a Postman Collection

1. In Postman, click "New" > "Collection"
2. Name it "Financial Data API"
3. For each endpoint, create a new request:
   - Click "Add Request"
   - Set the method (GET or POST)
   - Enter the URL
   - Add headers and body as needed
   - Save the request to your collection

## Environment Variables

Create an environment in Postman with these variables:
- `base_url`: http://jsh.maazmalik2004.space
- `ticker`: RELIANCE.NS

Then use `{{base_url}}` and `{{ticker}}` in your requests.

## Automated Testing

You can use Postman's test scripts to automate testing:

```javascript
// Example test script for company overview
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Response has required fields", function () {
    const data = pm.response.json();
    pm.expect(data).to.have.property('name');
    pm.expect(data).to.have.property('sector');
    pm.expect(data).to.have.property('exchange');
    pm.expect(['NSE', 'BSE']).to.include(data.exchange);
});
```

## Known Issues and Fixes

1. **Exchange Field Issue**: The company overview endpoint should return 'NSE' or 'BSE' for the exchange field based on the ticker suffix.
   - For tickers ending with '.NS', the exchange should be 'NSE'
   - For other tickers, the exchange should be 'BSE'

2. **Error Handling for Invalid Duration**: The stock price endpoint should validate the duration parameter and return a 400 error for invalid durations.
   - Valid durations are: '1d', '7d', '1mo', '6mo', '1y'
   - Any other value should result in a 400 error

## Local Testing

For local testing, you can use the provided `local_server.py` file:

1. Run the local server:
   ```
   python local_server.py
   ```

2. Update the base URL in your Postman environment to:
   ```
   http://localhost:5000
   ```

3. Run the tests using the provided `tests/test_local_api.py` file:
   ```
   pytest tests/test_local_api.py -v
   ``` 