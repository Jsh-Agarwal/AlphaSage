import logging
import yfinance as yf
import pandas as pd
import time
import ta

class YFinanceManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def get_ticker_data(self, ticker):
        """
        Get data for a ticker symbol from Yahoo Finance.
        
        Args:
            ticker (str): The ticker symbol (e.g., 'TCS.NS' for NSE stocks)
            
        Returns:
            dict: Dictionary containing ticker data or None if failed
        """
        try:
            # Don't append .NS if it's already there
            if ticker.endswith('.NS'):
                yf_ticker = yf.Ticker(ticker)
            else:
                yf_ticker = yf.Ticker(ticker)
            
            self.logger.info(f"Fetching data for {ticker}")
            
            # Try to get info - this will fail if ticker doesn't exist
            info = yf_ticker.info
            if not info:
                self.logger.error(f"No info found for ticker {ticker}")
                return None
                
            # Get historical data with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    history = yf_ticker.history(period="1y")
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        self.logger.error(f"Failed to get history for {ticker} after {max_retries} attempts: {e}")
                        history = pd.DataFrame()  # Empty DataFrame as fallback
                    else:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        
            return {
                "info": info,
                "history": history
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching data for {ticker}: {e}")
            return None
            
    def calculate_technical_indicators(self, price_history):
        """
        Calculate technical indicators for a given price history.
        
        Args:
            price_history (pd.DataFrame): DataFrame with OHLCV data
            
        Returns:
            dict: Dictionary containing technical indicators and summary
        """
        try:
            if price_history.empty:
                return {"summary": "No price data available"}
                
            # Initialize technical analysis indicators
            ta_data = {}
            
            # Moving averages
            ta_data['SMA_20'] = ta.trend.sma_indicator(price_history['Close'], window=20)
            ta_data['SMA_50'] = ta.trend.sma_indicator(price_history['Close'], window=50)
            ta_data['SMA_200'] = ta.trend.sma_indicator(price_history['Close'], window=200)
            
            # Momentum indicators
            ta_data['RSI'] = ta.momentum.rsi(price_history['Close'], window=14)
            macd = ta.trend.MACD(price_history['Close'])
            ta_data['MACD'] = macd.macd()
            ta_data['MACD_signal'] = macd.macd_signal()
            ta_data['MACD_diff'] = macd.macd_diff()
            
            # Volatility indicators
            ta_data['ATR'] = ta.volatility.average_true_range(
                price_history['High'],
                price_history['Low'],
                price_history['Close']
            )
            
            # Volume indicators
            ta_data['OBV'] = ta.volume.on_balance_volume(price_history['Close'], price_history['Volume'])
            
            # Get latest values
            latest = {k: v.iloc[-1] if isinstance(v, pd.Series) else v for k, v in ta_data.items()}
            
            # Generate summary
            current_price = price_history['Close'].iloc[-1]
            summary = []
            
            # Trend analysis
            if current_price > latest['SMA_200']:
                summary.append("Above 200-day MA (Bullish)")
            else:
                summary.append("Below 200-day MA (Bearish)")
                
            # RSI analysis
            if latest['RSI'] > 70:
                summary.append("RSI Overbought")
            elif latest['RSI'] < 30:
                summary.append("RSI Oversold")
            else:
                summary.append(f"RSI Neutral ({latest['RSI']:.2f})")
            
            # MACD analysis
            if latest['MACD'] > latest['MACD_signal']:
                summary.append("MACD Bullish")
            else:
                summary.append("MACD Bearish")
                
            # Create summary string
            summary_str = " | ".join(summary)
            
            return {
                "indicators": ta_data,
                "latest": latest,
                "summary": summary_str,
                "analysis": {  # Detailed analysis in dictionary format
                    "trend": "BULLISH" if current_price > latest['SMA_200'] else "BEARISH",
                    "momentum": "OVERBOUGHT" if latest['RSI'] > 70 else "OVERSOLD" if latest['RSI'] < 30 else "NEUTRAL",
                    "macd": "BULLISH" if latest['MACD'] > latest['MACD_signal'] else "BEARISH",
                    "rsi_value": round(latest['RSI'], 2)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating technical indicators: {e}")
            return {"summary": f"Error calculating indicators: {str(e)}"}
            
    def get_fundamentals(self, ticker):
        """
        Get fundamental data for a ticker.
        
        Args:
            ticker (str): The ticker symbol
            
        Returns:
            dict: Dictionary containing fundamental data
        """
        try:
            yf_ticker = yf.Ticker(ticker)
            
            # Get financial statements
            income_stmt = yf_ticker.financials
            balance_sheet = yf_ticker.balance_sheet
            cash_flow = yf_ticker.cashflow
            
            # Calculate key ratios
            if not income_stmt.empty and not balance_sheet.empty:
                latest_income = income_stmt.iloc[:, 0]
                latest_balance = balance_sheet.iloc[:, 0]
                
                ratios = {
                    "ROE": latest_income["Net Income"] / latest_balance["Total Stockholder Equity"]
                    if "Total Stockholder Equity" in latest_balance and latest_balance["Total Stockholder Equity"] != 0
                    else None,
                    
                    "ROA": latest_income["Net Income"] / latest_balance["Total Assets"]
                    if "Total Assets" in latest_balance and latest_balance["Total Assets"] != 0
                    else None,
                    
                    "Current Ratio": latest_balance["Total Current Assets"] / latest_balance["Total Current Liabilities"]
                    if "Total Current Assets" in latest_balance and "Total Current Liabilities" in latest_balance
                    and latest_balance["Total Current Liabilities"] != 0
                    else None
                }
            else:
                ratios = {}
                
            return {
                "income_statement": income_stmt.to_dict() if not income_stmt.empty else {},
                "balance_sheet": balance_sheet.to_dict() if not balance_sheet.empty else {},
                "cash_flow": cash_flow.to_dict() if not cash_flow.empty else {},
                "ratios": ratios
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching fundamentals for {ticker}: {e}")
            return {} 