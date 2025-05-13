import os
import logging
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import matplotlib.pyplot as plt
from io import BytesIO
import base64

# Set up logging
logger = logging.getLogger(__name__)

class StockReportPDF(FPDF):
    """PDF generation class for stock reports."""
    
    def __init__(self, orientation='P', unit='mm', format='A4'):
        super().__init__(orientation, unit, format)
        self.set_auto_page_break(auto=True, margin=15)
        self.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
        self.add_font('DejaVu', 'B', 'DejaVuSansCondensed-Bold.ttf', uni=True)
        
    def header(self):
        # Header with company name and logo
        self.set_font('DejaVu', 'B', 15)
        self.cell(0, 10, 'Stock Analysis Report', 0, 1, 'C')
        self.ln(5)
        
    def footer(self):
        # Footer with page numbers
        self.set_y(-15)
        self.set_font('DejaVu', '', 8)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')
        
    def chapter_title(self, title):
        # Add a chapter title
        self.set_font('DejaVu', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 6, title, 0, 1, 'L', 1)
        self.ln(4)
        
    def chapter_body(self, body):
        # Add chapter content
        self.set_font('DejaVu', '', 11)
        self.multi_cell(0, 6, body)
        self.ln()
        
    def add_metric_table(self, headers, data):
        # Add a metrics table
        line_height = 6
        col_width = self.w / len(headers)
        
        self.set_font('DejaVu', 'B', 10)
        for header in headers:
            self.cell(col_width, line_height, header, 1, 0, 'C')
        self.ln()
        
        self.set_font('DejaVu', '', 10)
        for row in data:
            for item in row:
                self.cell(col_width, line_height, str(item), 1, 0, 'C')
            self.ln()
        self.ln(5)
        
    def add_chart_image(self, image_data, caption=""):
        # Add a chart image to the PDF
        self.image(image_data, x=10, y=None, w=180)
        if caption:
            self.set_font('DejaVu', '', 8)
            self.cell(0, 5, caption, 0, 1, 'C')
        self.ln(5)


def generate_stock_report(ticker, company_data, report_data, output_path=None):
    """
    Generate a PDF report for a stock.
    
    Args:
        ticker (str): The stock ticker symbol
        company_data (dict): Data about the company and stock
        report_data (dict): Financial and analysis data
        output_path (str, optional): Path to save the PDF. If None, uses default location.
        
    Returns:
        str: Path to the generated PDF file
    """
    try:
        # Create PDF instance
        pdf = StockReportPDF()
        pdf.alias_nb_pages()
        pdf.add_page()
        
        # Company Information
        company_name = company_data.get('info', {}).get('longName', ticker)
        pdf.set_font('DejaVu', 'B', 16)
        pdf.cell(0, 10, f"{company_name} ({ticker})", 0, 1, 'C')
        pdf.set_font('DejaVu', '', 10)
        pdf.cell(0, 5, f"Report generated on {datetime.now().strftime('%Y-%m-%d')}", 0, 1, 'C')
        pdf.ln(5)
        
        # Company Overview
        pdf.chapter_title("Company Overview")
        info = company_data.get('info', {})
        overview = (
            f"Sector: {info.get('sector', 'N/A')}\n"
            f"Industry: {info.get('industry', 'N/A')}\n"
            f"Website: {info.get('website', 'N/A')}\n"
            f"Employees: {info.get('fullTimeEmployees', 'N/A')}\n\n"
            f"{info.get('longBusinessSummary', 'No description available')}"
        )
        pdf.chapter_body(overview)
        
        # Financial Highlights
        pdf.chapter_title("Financial Highlights")
        financial_data = [
            ["Metric", "Value"],
            ["Market Cap", f"${info.get('marketCap', 0)/1000000000:.2f}B"],
            ["P/E Ratio", f"{info.get('trailingPE', 'N/A')}"],
            ["Div Yield", f"{info.get('dividendYield', 0)*100:.2f}%"],
            ["Revenue (TTM)", f"${info.get('totalRevenue', 0)/1000000000:.2f}B"],
            ["Profit Margin", f"{info.get('profitMargins', 0)*100:.2f}%"],
            ["Beta", f"{info.get('beta', 'N/A')}"]
        ]
        
        # Format the financial data as a table
        pdf.set_font('DejaVu', '', 10)
        col_width = 90
        line_height = 6
        for row in financial_data:
            pdf.cell(col_width, line_height, row[0], 1, 0, 'L')
            pdf.cell(col_width, line_height, row[1], 1, 1, 'R')
        pdf.ln(10)
        
        # Add investment thesis if available
        if report_data and 'investment_thesis' in report_data:
            pdf.chapter_title("Investment Thesis")
            thesis = report_data.get('investment_thesis', {})
            analysis = (
                f"{thesis.get('fundamental_analysis', '')}\n\n"
                f"News Impact:\n{thesis.get('news_impact', '')}\n\n"
                f"Investment Recommendation:\n{thesis.get('investment_thesis', '')}"
            )
            pdf.chapter_body(analysis)
        
        # Technical Analysis
        pdf.add_page()
        pdf.chapter_title("Technical Analysis")
        
        # Try to create a stock price chart if history is available
        try:
            history = company_data.get('history')
            if history is not None and not history.empty:
                # Create stock price chart
                plt.figure(figsize=(10, 6))
                plt.plot(history.index, history['Close'])
                plt.title(f"{ticker} Stock Price")
                plt.xlabel("Date")
                plt.ylabel("Price ($)")
                plt.grid(True)
                
                # Save chart to memory
                img_buffer = BytesIO()
                plt.savefig(img_buffer, format='png')
                img_buffer.seek(0)
                
                # Add chart to PDF
                pdf.add_chart_image(img_buffer, f"{ticker} Stock Price Chart")
                plt.close()
                
                # Add technical indicators summary if available
                if 'technical_analysis' in report_data and 'summary' in report_data['technical_analysis']:
                    tech_summary = report_data['technical_analysis']['summary']
                    pdf.set_font('DejaVu', 'B', 11)
                    pdf.cell(0, 6, "Technical Indicators Summary:", 0, 1, 'L')
                    pdf.set_font('DejaVu', '', 10)
                    
                    indicators_data = [
                        ["Indicator", "Value", "Signal"],
                        ["Trend", tech_summary.get('trend', 'NEUTRAL'), ""],
                        ["RSI", f"{tech_summary.get('rsi', 'N/A')}", tech_summary.get('rsi_signal', '')],
                        ["MACD", f"{tech_summary.get('macd', 'N/A')}", tech_summary.get('macd_signal', '')],
                        ["Bollinger", f"{tech_summary.get('bollinger', 'N/A')}", tech_summary.get('bollinger_signal', '')]
                    ]
                    
                    # Format as table
                    col_width = 60
                    for row in indicators_data:
                        pdf.cell(col_width, line_height, row[0], 1, 0, 'L')
                        pdf.cell(col_width, line_height, row[1], 1, 0, 'C')
                        pdf.cell(col_width, line_height, row[2], 1, 1, 'R')
                    pdf.ln(10)
        except Exception as e:
            logger.error(f"Error creating stock chart: {e}")
            pdf.chapter_body("Could not generate price chart due to an error.")
        
        # Determine output path
        if output_path is None:
            output_dir = os.path.join(os.getcwd(), "reports")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"{ticker}_stock_report.pdf")
        
        # Save the PDF
        pdf.output(output_path)
        logger.info(f"Generated stock report for {ticker} at {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error generating PDF report: {e}")
        raise


def generate_comparative_report(tickers, company_data_dict, output_path=None):
    """
    Generate a comparative PDF report for multiple stocks.
    
    Args:
        tickers (list): List of stock ticker symbols
        company_data_dict (dict): Dictionary of company data keyed by ticker
        output_path (str, optional): Path to save the PDF. If None, uses default location.
        
    Returns:
        str: Path to the generated PDF file
    """
    try:
        # Create PDF instance
        pdf = StockReportPDF()
        pdf.alias_nb_pages()
        pdf.add_page()
        
        # Report title
        pdf.set_font('DejaVu', 'B', 16)
        pdf.cell(0, 10, "Comparative Stock Analysis", 0, 1, 'C')
        pdf.set_font('DejaVu', '', 10)
        pdf.cell(0, 5, f"Tickers: {', '.join(tickers)}", 0, 1, 'C')
        pdf.cell(0, 5, f"Report generated on {datetime.now().strftime('%Y-%m-%d')}", 0, 1, 'C')
        pdf.ln(5)
        
        # Comparison table headers
        headers = ["Ticker", "Price", "P/E", "Market Cap", "Revenue Growth", "Profit Margin"]
        
        # Prepare data rows
        data_rows = []
        for ticker in tickers:
            if ticker in company_data_dict:
                company_data = company_data_dict[ticker]
                info = company_data.get('info', {})
                history = company_data.get('history')
                
                # Get latest price
                latest_price = "N/A"
                if history is not None and not history.empty:
                    latest_price = f"${history['Close'].iloc[-1]:.2f}"
                
                # Format market cap
                market_cap = info.get('marketCap', 0)
                if market_cap >= 1_000_000_000_000:
                    market_cap_str = f"${market_cap / 1_000_000_000_000:.2f}T"
                elif market_cap >= 1_000_000_000:
                    market_cap_str = f"${market_cap / 1_000_000_000:.2f}B"
                else:
                    market_cap_str = f"${market_cap / 1_000_000:.2f}M"
                
                # Add row
                data_rows.append([
                    ticker,
                    latest_price,
                    f"{info.get('trailingPE', 'N/A')}",
                    market_cap_str,
                    f"{info.get('revenueGrowth', 0) * 100:.2f}%",
                    f"{info.get('profitMargins', 0) * 100:.2f}%"
                ])
        
        # Add comparison table
        pdf.add_metric_table(headers, data_rows)
        
        # Try to create a comparative price chart
        try:
            plt.figure(figsize=(10, 6))
            
            # Plot normalized prices for all stocks
            for ticker in tickers:
                if ticker in company_data_dict:
                    history = company_data_dict[ticker].get('history')
                    if history is not None and not history.empty:
                        # Normalize prices to start at 100
                        normalized_prices = history['Close'] / history['Close'].iloc[0] * 100
                        plt.plot(history.index, normalized_prices, label=ticker)
            
            plt.title("Comparative Stock Performance (Normalized)")
            plt.xlabel("Date")
            plt.ylabel("Normalized Price (Initial = 100)")
            plt.legend()
            plt.grid(True)
            
            # Save chart to memory
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png')
            img_buffer.seek(0)
            
            # Add chart to PDF
            pdf.add_chart_image(img_buffer, "Comparative Stock Performance")
            plt.close()
            
        except Exception as e:
            logger.error(f"Error creating comparative chart: {e}")
            pdf.chapter_body("Could not generate comparative chart due to an error.")
        
        # Comparative analysis
        pdf.chapter_title("Comparative Analysis")
        
        # Simple comparative analysis for each stock
        for ticker in tickers:
            if ticker in company_data_dict:
                company_data = company_data_dict[ticker]
                info = company_data.get('info', {})
                company_name = info.get('longName', ticker)
                
                pdf.set_font('DejaVu', 'B', 11)
                pdf.cell(0, 6, f"{company_name} ({ticker})", 0, 1, 'L')
                pdf.set_font('DejaVu', '', 10)
                
                # Calculate some basic metrics for comparison
                pe_ratio = info.get('trailingPE', 'N/A')
                dividend_yield = info.get('dividendYield', 0) * 100
                profit_margin = info.get('profitMargins', 0) * 100
                
                analysis = (
                    f"Sector: {info.get('sector', 'N/A')}\n"
                    f"P/E Ratio: {pe_ratio}\n"
                    f"Dividend Yield: {dividend_yield:.2f}%\n"
                    f"Profit Margin: {profit_margin:.2f}%\n\n"
                )
                
                # Add some comparative insights
                if isinstance(pe_ratio, (int, float)):
                    if pe_ratio < 15:
                        analysis += "Valuation: Potentially undervalued compared to market averages.\n"
                    elif pe_ratio > 25:
                        analysis += "Valuation: Potentially overvalued compared to market averages.\n"
                    else:
                        analysis += "Valuation: In line with typical market valuations.\n"
                
                if dividend_yield > 3:
                    analysis += "Dividend: Above-average dividend yield, may be suitable for income investors.\n"
                elif dividend_yield < 1:
                    analysis += "Dividend: Low dividend yield, likely focused on growth.\n"
                
                if profit_margin > 20:
                    analysis += "Profitability: Strong profit margins compared to typical companies.\n"
                elif profit_margin < 10:
                    analysis += "Profitability: Below-average profit margins, may indicate competitive pressures.\n"
                
                pdf.multi_cell(0, 6, analysis)
                pdf.ln(5)
        
        # Determine output path
        if output_path is None:
            output_dir = os.path.join(os.getcwd(), "reports")
            os.makedirs(output_dir, exist_ok=True)
            ticker_str = "_".join(tickers)
            output_path = os.path.join(output_dir, f"comparative_report_{ticker_str}.pdf")
        
        # Save the PDF
        pdf.output(output_path)
        logger.info(f"Generated comparative report for {tickers} at {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error generating comparative PDF report: {e}")
        raise


def text_to_pdf(text, title, output_path=None):
    """
    Convert a text report to PDF.
    
    Args:
        text (str): The text to convert to PDF
        title (str): The title for the PDF
        output_path (str, optional): Path to save the PDF. If None, uses default location.
        
    Returns:
        str: Path to the generated PDF file
    """
    try:
        # Create PDF instance
        pdf = FPDF()
        pdf.add_page()
        
        # Add title
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, title, 0, 1, "C")
        pdf.ln(10)
        
        # Add text content
        pdf.set_font("Arial", "", 11)
        
        # Split the text by newlines and add each line
        for line in text.split('\n'):
            pdf.multi_cell(0, 6, line)
        
        # Determine output path
        if output_path is None:
            output_dir = os.path.join(os.getcwd(), "reports")
            os.makedirs(output_dir, exist_ok=True)
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            output_path = os.path.join(output_dir, filename)
        
        # Save the PDF
        pdf.output(output_path)
        logger.info(f"Generated text report at {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error converting text to PDF: {e}")
        raise