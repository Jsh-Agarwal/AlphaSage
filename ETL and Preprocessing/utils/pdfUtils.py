"""
PDF Utilities for generating stock reports and analysis documents.
"""
import os
import json
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

class StockReportGenerator:
    """Class for generating PDF stock reports"""
    
    def __init__(self, output_dir='reports'):
        """Initialize the PDF report generator
        
        Args:
            output_dir (str): Directory where reports will be saved
        """
        self.output_dir = output_dir
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        # Get the standard styles
        self.styles = getSampleStyleSheet()
        # Create custom styles
        self.title_style = ParagraphStyle(
            'TitleStyle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=12
        )
        self.section_style = ParagraphStyle(
            'SectionStyle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=8,
            spaceBefore=12
        )
        self.normal_style = self.styles['Normal']
        self.table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
    
    def generate_stock_report(self, stock_data, ticker):
        """Generate a comprehensive stock report in PDF format
        
        Args:
            stock_data (dict): Dictionary containing all the stock analysis data
            ticker (str): Stock ticker symbol
            
        Returns:
            str: Path to the generated report
        """
        # Define the report filename
        current_date = datetime.now().strftime("%Y%m%d")
        filename = f"{ticker.upper()}_stock_report_{current_date}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        # Create the document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Store all the elements to be added to the document
        elements = []
        
        # Add the title
        company_name = stock_data.get('company_name', ticker.upper())
        report_title = f"Stock Analysis Report: {company_name} ({ticker.upper()})"
        elements.append(Paragraph(report_title, self.title_style))
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.normal_style))
        elements.append(Spacer(1, 0.25*inch))
        
        # Company Overview
        elements.append(Paragraph("Company Overview", self.section_style))
        
        # Extract company info
        company_info = stock_data.get('company_info', {})
        overview_data = [
            ["Company Name", company_name],
            ["Ticker", ticker.upper()],
            ["Sector", company_info.get('sector', 'N/A')],
            ["Industry", company_info.get('industry', 'N/A')],
            ["Exchange", company_info.get('exchange', 'N/A')],
            ["Website", company_info.get('website', 'N/A')]
        ]
        
        # Create the overview table
        overview_table = Table(overview_data, colWidths=[2*inch, 3.5*inch])
        overview_table.setStyle(self.table_style)
        elements.append(overview_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Financial Highlights
        elements.append(Paragraph("Financial Highlights", self.section_style))
        
        # Format financial data properly
        financials = stock_data.get('financial_highlights', {})
        
        # Format market cap nicely
        market_cap = financials.get('market_cap', 0)
        if isinstance(market_cap, (int, float)) and market_cap > 0:
            if market_cap >= 1_000_000_000_000:
                market_cap_str = f"${market_cap / 1_000_000_000_000:.2f}T"
            elif market_cap >= 1_000_000_000:
                market_cap_str = f"${market_cap / 1_000_000_000:.2f}B"
            else:
                market_cap_str = f"${market_cap / 1_000_000:.2f}M"
        else:
            market_cap_str = "N/A"
        
        # Format percentages
        profit_margin = financials.get('profit_margin', 0)
        if isinstance(profit_margin, (int, float)):
            profit_margin_str = f"{profit_margin * 100:.2f}%"
        else:
            profit_margin_str = "N/A"
            
        dividend_yield = financials.get('dividend_yield', 0)
        if isinstance(dividend_yield, (int, float)):
            dividend_yield_str = f"{dividend_yield * 100:.2f}%"
        else:
            dividend_yield_str = "N/A"
        
        financial_data = [
            ["Market Cap", market_cap_str],
            ["P/E Ratio", str(financials.get('pe_ratio', 'N/A'))],
            ["Dividend Yield", dividend_yield_str],
            ["Beta", str(financials.get('beta', 'N/A'))],
            ["Profit Margin", profit_margin_str]
        ]
        
        # Create the financials table
        financial_table = Table(financial_data, colWidths=[2*inch, 3.5*inch])
        financial_table.setStyle(self.table_style)
        elements.append(financial_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Technical Analysis
        elements.append(Paragraph("Technical Analysis", self.section_style))
        
        technical_data = stock_data.get('technical_analysis', {})
        summary = technical_data.get('summary', {})
        
        technical_summary = [
            ["Trend", summary.get('trend', 'NEUTRAL')],
            ["Momentum", summary.get('momentum', 'NEUTRAL')],
            ["Volatility", summary.get('volatility', 'MEDIUM')],
            ["Volume", summary.get('volume', 'AVERAGE')],
            ["Overall Signal", summary.get('signal', 'NEUTRAL')]
        ]
        
        # Create the technical analysis table
        technical_table = Table(technical_summary, colWidths=[2*inch, 3.5*inch])
        technical_table.setStyle(self.table_style)
        elements.append(technical_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Investment Thesis
        elements.append(Paragraph("Investment Thesis", self.section_style))
        
        thesis = stock_data.get('investment_thesis', {})
        elements.append(Paragraph(thesis.get('fundamental_analysis', 'No fundamental analysis available.'), self.normal_style))
        elements.append(Spacer(1, 0.15*inch))
        elements.append(Paragraph("News Impact:", self.styles['Heading4']))
        elements.append(Paragraph(thesis.get('news_impact', 'No news impact analysis available.'), self.normal_style))
        elements.append(Spacer(1, 0.15*inch))
        elements.append(Paragraph("Recommendation:", self.styles['Heading4']))
        elements.append(Paragraph(thesis.get('investment_thesis', 'No investment recommendation available.'), self.normal_style))
        
        # Recent News
        news = stock_data.get('news', [])
        if news:
            elements.append(Paragraph("Recent News", self.section_style))
            
            for i, news_item in enumerate(news[:5]):  # Show only up to 5 news items
                news_date = news_item.get('date', '')
                news_title = news_item.get('title', '')
                news_source = news_item.get('source', '')
                
                elements.append(Paragraph(f"<b>{news_title}</b>", self.normal_style))
                elements.append(Paragraph(f"Source: {news_source} | Date: {news_date}", 
                                         ParagraphStyle('NewsDate', parent=self.normal_style, fontSize=8)))
                elements.append(Spacer(1, 0.1*inch))
        
        # Build the PDF
        doc.build(elements)
        
        return filepath
    
    def generate_text_report(self, stock_data, ticker):
        """Generate a plain text stock report
        
        Args:
            stock_data (dict): Dictionary containing all the stock analysis data
            ticker (str): Stock ticker symbol
            
        Returns:
            str: The report text content
        """
        company_name = stock_data.get('company_name', ticker.upper())
        
        # Start building the report
        report = f"STOCK ANALYSIS REPORT: {company_name} ({ticker.upper()})\n"
        report += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += "=" * 80 + "\n\n"
        
        # Company Overview
        company_info = stock_data.get('company_info', {})
        report += "COMPANY OVERVIEW\n"
        report += "-" * 80 + "\n"
        report += f"Name: {company_name}\n"
        report += f"Sector: {company_info.get('sector', 'N/A')}\n"
        report += f"Industry: {company_info.get('industry', 'N/A')}\n"
        report += f"Exchange: {company_info.get('exchange', 'N/A')}\n"
        report += f"Website: {company_info.get('website', 'N/A')}\n"
        report += f"Employees: {company_info.get('employees', 'N/A')}\n\n"
        
        # Financial Highlights
        financials = stock_data.get('financial_highlights', {})
        report += "FINANCIAL HIGHLIGHTS\n"
        report += "-" * 80 + "\n"
        
        # Format market cap nicely
        market_cap = financials.get('market_cap', 0)
        if isinstance(market_cap, (int, float)) and market_cap > 0:
            if market_cap >= 1_000_000_000_000:
                market_cap_str = f"${market_cap / 1_000_000_000_000:.2f}T"
            elif market_cap >= 1_000_000_000:
                market_cap_str = f"${market_cap / 1_000_000_000:.2f}B"
            else:
                market_cap_str = f"${market_cap / 1_000_000:.2f}M"
        else:
            market_cap_str = "N/A"
        
        report += f"Market Cap: {market_cap_str}\n"
        report += f"P/E Ratio: {financials.get('pe_ratio', 'N/A')}\n"
        report += f"Dividend Yield: {financials.get('dividend_yield', 0) * 100:.2f}%\n"
        report += f"Beta: {financials.get('beta', 'N/A')}\n"
        report += f"Revenue: ${financials.get('revenue', 0) / 1_000_000:.2f}M\n"
        report += f"Profit Margin: {financials.get('profit_margin', 0) * 100:.2f}%\n\n"
        
        # Technical Analysis
        technical_data = stock_data.get('technical_analysis', {})
        summary = technical_data.get('summary', {})
        
        report += "TECHNICAL ANALYSIS\n"
        report += "-" * 80 + "\n"
        report += f"Trend: {summary.get('trend', 'NEUTRAL')}\n"
        report += f"Momentum: {summary.get('momentum', 'NEUTRAL')}\n"
        report += f"Volatility: {summary.get('volatility', 'MEDIUM')}\n"
        report += f"Volume: {summary.get('volume', 'AVERAGE')}\n"
        report += f"Overall Signal: {summary.get('signal', 'NEUTRAL')}\n\n"
        
        # Investment Thesis
        thesis = stock_data.get('investment_thesis', {})
        report += "INVESTMENT THESIS\n"
        report += "-" * 80 + "\n"
        report += f"{thesis.get('fundamental_analysis', 'No fundamental analysis available.')}\n\n"
        report += "News Impact:\n"
        report += f"{thesis.get('news_impact', 'No news impact analysis available.')}\n\n"
        report += "Recommendation:\n"
        report += f"{thesis.get('investment_thesis', 'No investment recommendation available.')}\n\n"
        
        # Recent News
        news = stock_data.get('news', [])
        if news:
            report += "RECENT NEWS\n"
            report += "-" * 80 + "\n"
            
            for i, news_item in enumerate(news[:5]):  # Show only up to 5 news items
                news_date = news_item.get('date', '')
                news_title = news_item.get('title', '')
                news_source = news_item.get('source', '')
                
                report += f"{news_title}\n"
                report += f"Source: {news_source} | Date: {news_date}\n\n"
        
        return report
    
    def save_report_to_file(self, report_text, ticker):
        """Save a text report to a file
        
        Args:
            report_text (str): The report text content
            ticker (str): Stock ticker symbol
            
        Returns:
            str: Path to the saved report file
        """
        current_date = datetime.now().strftime("%Y%m%d")
        filename = f"{ticker.upper()}_stock_report_{current_date}.txt"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w') as f:
            f.write(report_text)
            
        return filepath