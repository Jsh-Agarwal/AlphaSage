#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Financial Metrics Analyzer

This script provides utility functions for analyzing financial metrics across companies
and generating comparison reports. It works with data from the Neo4j knowledge graph
and can generate both textual and visual reports.

Usage:
    python financial_metrics_analyzer.py --mode compare --tickers AAPL MSFT GOOGL
    python financial_metrics_analyzer.py --mode sector_performance --sector Technology
    python financial_metrics_analyzer.py --mode valuation_metrics --tickers AAPL MSFT --output report.pdf
"""

import os
import sys
import logging
import argparse
import json
from datetime import datetime
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Datapipeline.ConfigManager import ConfigManager
from Datapipeline.database import Neo4jDatabase
from Datapipeline.etl import YFinanceManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("financial_metrics_analyzer.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class FinancialMetricsAnalyzer:
    """Utility class for analyzing financial metrics across companies and sectors."""
    
    def __init__(self):
        """Initialize the analyzer."""
        # Load configuration
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_all_config()
        
        # Initialize Neo4j connection
        neo4j_creds = self.config_manager.get_neo4j_credentials()
        self.neo4j = Neo4jDatabase(
            uri=neo4j_creds.get("uri"),
            user=neo4j_creds.get("user"),
            password=neo4j_creds.get("password")
        )
        
        # Initialize YFinanceManager for fetching financial data
        self.yf_manager = YFinanceManager()
        
        # Create output directories
        self.reports_dir = Path("./reports/financial_metrics")
        self.reports_dir.mkdir(exist_ok=True, parents=True)
        
        self.visualizations_dir = Path("./visualizations")
        self.visualizations_dir.mkdir(exist_ok=True, parents=True)
        
    def compare_companies(self, tickers, metrics=None, output=None):
        """
        Compare financial metrics across multiple companies.
        
        Parameters:
            tickers (list): List of stock tickers to compare
            metrics (list): List of financial metrics to compare (default: key metrics)
            output (str): Output file path for the report
            
        Returns:
            dict: Comparison results
        """
        logger.info(f"Comparing {len(tickers)} companies")
        
        # Default metrics if none provided
        if not metrics:
            metrics = [
                'marketCap', 'trailingPE', 'forwardPE', 'priceToBook', 
                'priceToSales', 'returnOnEquity', 'returnOnAssets',
                'profitMargins', 'operatingMargins', 'grossMargins',
                'debtToEquity', 'currentRatio', 'quickRatio',
                'dividendYield', 'beta', 'enterpriseToEbitda'
            ]
        
        # Fetch data for each company
        company_data = {}
        for ticker in tickers:
            try:
                logger.info(f"Fetching data for {ticker}")
                # Get data from Neo4j
                company_node = self.neo4j.get_company_by_ticker(ticker)
                if not company_node:
                    logger.warning(f"Company {ticker} not found in Neo4j")
                    # Try fetching from Yahoo Finance
                    data = self.yf_manager.get_ticker_data(ticker)
                    if data and data.get("info"):
                        company_data[ticker] = {
                            "name": data["info"].get("shortName", ticker),
                            "data": data["info"]
                        }
                else:
                    # Get additional data from Yahoo Finance
                    yf_data = self.yf_manager.get_ticker_data(ticker)
                    if yf_data and yf_data.get("info"):
                        company_data[ticker] = {
                            "name": company_node.get("shortName", ticker),
                            "data": {**dict(company_node), **yf_data["info"]}
                        }
                    else:
                        company_data[ticker] = {
                            "name": company_node.get("shortName", ticker),
                            "data": dict(company_node)
                        }
            except Exception as e:
                logger.error(f"Error fetching data for {ticker}: {e}")
        
        if not company_data:
            logger.error("No company data found")
            return None
        
        # Create comparison DataFrame
        comparison_data = []
        for ticker, data in company_data.items():
            row = {"Ticker": ticker, "Name": data["name"]}
            for metric in metrics:
                if metric in data["data"]:
                    row[metric] = data["data"][metric]
                else:
                    row[metric] = np.nan
            comparison_data.append(row)
        
        df = pd.DataFrame(comparison_data)
        
        # Generate visualizations
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"company_comparison_{timestamp}"
        
        if not df.empty:
            # Create visualizations for key metrics
            self._generate_comparison_charts(df, report_filename)
            
            # Create summary report
            summary = {
                "timestamp": timestamp,
                "companies": [{"ticker": t, "name": company_data[t]["name"]} for t in tickers if t in company_data],
                "metrics": metrics,
                "comparison_file": f"{report_filename}.xlsx",
                "visualization_file": f"{report_filename}.png"
            }
            
            # Save comparison data to Excel
            excel_file = self.reports_dir / f"{report_filename}.xlsx"
            df.to_excel(excel_file, index=False)
            logger.info(f"Comparison data saved to {excel_file}")
            
            # Save summary JSON
            summary_file = self.reports_dir / f"{report_filename}.json"
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=4)
            logger.info(f"Comparison summary saved to {summary_file}")
            
            # Generate PDF report if requested
            if output and output.endswith('.pdf'):
                self._generate_pdf_report(df, output, tickers)
                logger.info(f"PDF report saved to {output}")
            
            return summary
        else:
            logger.error("Could not create comparison data")
            return None
    
    def analyze_sector_performance(self, sector_name, top_n=10, output=None):
        """
        Analyze performance metrics for companies in a sector.
        
        Parameters:
            sector_name (str): Name of the sector to analyze
            top_n (int): Number of top companies to include
            output (str): Output file path for the report
            
        Returns:
            dict: Sector performance analysis
        """
        logger.info(f"Analyzing performance for {sector_name} sector")
        
        # Get companies in the sector
        sector_companies = self.neo4j.get_companies_by_sector(sector_name)
        
        if not sector_companies:
            logger.warning(f"No companies found for sector {sector_name}")
            return None
        
        # Extract tickers
        tickers = [company.get("ticker") for company in sector_companies if company.get("ticker")]
        
        if not tickers:
            logger.warning(f"No tickers found for companies in sector {sector_name}")
            return None
        
        # Define performance metrics
        performance_metrics = [
            'returnOnEquity', 'returnOnAssets', 'profitMargins',
            'operatingMargins', 'revenueGrowth', 'earningsGrowth',
            'freeCashflow', 'operatingCashflow'
        ]
        
        # Fetch data for each company
        data = []
        for ticker in tickers:
            try:
                # Get data from Yahoo Finance
                yf_data = self.yf_manager.get_ticker_data(ticker)
                
                if not yf_data or not yf_data.get("info"):
                    logger.warning(f"No data found for {ticker}")
                    continue
                
                company_info = yf_data["info"]
                company_data = {
                    "Ticker": ticker,
                    "Name": company_info.get("shortName", ticker),
                    "MarketCap": company_info.get("marketCap", np.nan)
                }
                
                # Extract performance metrics
                for metric in performance_metrics:
                    company_data[metric] = company_info.get(metric, np.nan)
                
                data.append(company_data)
            except Exception as e:
                logger.error(f"Error fetching data for {ticker}: {e}")
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        if df.empty:
            logger.warning(f"No data available for {sector_name} sector")
            return None
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"{sector_name.lower().replace(' ', '_')}_performance_{timestamp}"
        
        # Generate sector performance visualizations
        self._generate_sector_performance_charts(df, sector_name, top_n, report_filename)
        
        # Create sector performance summary
        performance_summary = {
            "sector": sector_name,
            "timestamp": timestamp,
            "company_count": len(df),
            "avg_roe": df['returnOnEquity'].mean(),
            "avg_profit_margin": df['profitMargins'].mean(),
            "top_performer": df.loc[df['returnOnEquity'].idxmax()]['Name'] if not df.empty and not df['returnOnEquity'].isna().all() else 'N/A',
            "visualization_file": f"{report_filename}.png",
            "report_file": f"{report_filename}.xlsx"
        }
        
        # Save data to Excel
        excel_file = self.reports_dir / f"{report_filename}.xlsx"
        df.to_excel(excel_file, index=False)
        logger.info(f"Performance data saved to {excel_file}")
        
        # Save summary JSON
        summary_file = self.reports_dir / f"{report_filename}.json"
        with open(summary_file, 'w') as f:
            json.dump(performance_summary, f, indent=4)
        logger.info(f"Performance summary saved to {summary_file}")
        
        # Generate PDF report if requested
        if output and output.endswith('.pdf'):
            self._generate_pdf_report(df, output, tickers=None, sector=sector_name)
            logger.info(f"PDF report saved to {output}")
        
        return performance_summary
    
    def analyze_valuation_metrics(self, tickers=None, sector=None, output=None):
        """
        Analyze valuation metrics for companies or a sector.
        
        Parameters:
            tickers (list): List of stock tickers to analyze
            sector (str): Sector name to analyze
            output (str): Output file path for the report
            
        Returns:
            dict: Valuation metrics analysis
        """
        logger.info(f"Analyzing valuation metrics for {'tickers' if tickers else 'sector'}")
        
        # Get companies from sector if specified
        if sector and not tickers:
            sector_companies = self.neo4j.get_companies_by_sector(sector)
            if not sector_companies:
                logger.warning(f"No companies found for sector {sector}")
                return None
            tickers = [company.get("ticker") for company in sector_companies if company.get("ticker")]
        
        if not tickers:
            logger.warning("No tickers specified")
            return None
        
        # Define valuation metrics
        valuation_metrics = [
            'marketCap', 'enterpriseValue', 'trailingPE', 'forwardPE',
            'pegRatio', 'priceToBook', 'priceToSales', 'enterpriseToRevenue',
            'enterpriseToEbitda', 'ev_to_fcf', 'dividend_yield'
        ]
        
        # Fetch data for each company
        data = []
        for ticker in tickers:
            try:
                # Get data from Yahoo Finance
                yf_data = self.yf_manager.get_ticker_data(ticker)
                
                if not yf_data or not yf_data.get("info"):
                    logger.warning(f"No data found for {ticker}")
                    continue
                
                company_info = yf_data["info"]
                company_data = {
                    "Ticker": ticker,
                    "Name": company_info.get("shortName", ticker)
                }
                
                # Extract valuation metrics
                for metric in valuation_metrics:
                    company_data[metric] = company_info.get(metric, np.nan)
                
                # Calculate additional metrics if possible
                if company_info.get('enterpriseValue') and company_info.get('freeCashflow'):
                    if company_info.get('freeCashflow') != 0:
                        company_data['ev_to_fcf'] = company_info.get('enterpriseValue') / company_info.get('freeCashflow')
                
                if company_info.get('dividendRate') and company_info.get('currentPrice'):
                    if company_info.get('currentPrice') != 0:
                        company_data['dividend_yield'] = company_info.get('dividendRate') / company_info.get('currentPrice')
                
                data.append(company_data)
            except Exception as e:
                logger.error(f"Error fetching data for {ticker}: {e}")
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        if df.empty:
            logger.warning("No valuation data available")
            return None
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        title = sector if sector else "selected_companies"
        report_filename = f"{title.lower().replace(' ', '_')}_valuation_{timestamp}"
        
        # Generate valuation visualizations
        self._generate_valuation_charts(df, title, report_filename)
        
        # Create valuation summary
        valuation_summary = {
            "title": f"Valuation Analysis for {sector if sector else 'Selected Companies'}",
            "timestamp": timestamp,
            "company_count": len(df),
            "avg_pe": df['trailingPE'].mean(),
            "avg_pb": df['priceToBook'].mean(),
            "avg_ps": df['priceToSales'].mean(),
            "lowest_pe": {
                "ticker": df.loc[df['trailingPE'].idxmin()]['Ticker'] if not df['trailingPE'].isna().all() else 'N/A',
                "name": df.loc[df['trailingPE'].idxmin()]['Name'] if not df['trailingPE'].isna().all() else 'N/A',
                "value": df['trailingPE'].min()
            },
            "visualization_file": f"{report_filename}.png",
            "report_file": f"{report_filename}.xlsx"
        }
        
        # Save data to Excel
        excel_file = self.reports_dir / f"{report_filename}.xlsx"
        df.to_excel(excel_file, index=False)
        logger.info(f"Valuation data saved to {excel_file}")
        
        # Save summary JSON
        summary_file = self.reports_dir / f"{report_filename}.json"
        with open(summary_file, 'w') as f:
            json.dump(valuation_summary, f, indent=4)
        logger.info(f"Valuation summary saved to {summary_file}")
        
        # Generate PDF report if requested
        if output and output.endswith('.pdf'):
            self._generate_pdf_report(df, output, tickers=tickers, sector=sector)
            logger.info(f"PDF report saved to {output}")
        
        return valuation_summary
    
    def _generate_comparison_charts(self, df, filename_base):
        """Generate comparison charts for key metrics."""
        try:
            plt.figure(figsize=(15, 12))
            
            # 1. Market Cap Comparison
            plt.subplot(2, 2, 1)
            if 'marketCap' in df.columns:
                market_cap_data = df.sort_values('marketCap', ascending=False)
                sns.barplot(x='Ticker', y='marketCap', data=market_cap_data)
                plt.title('Market Cap Comparison')
                plt.xticks(rotation=45)
                plt.ylabel('Market Cap')
            
            # 2. P/E Ratio Comparison
            plt.subplot(2, 2, 2)
            if 'trailingPE' in df.columns:
                pe_data = df.sort_values('trailingPE')
                sns.barplot(x='Ticker', y='trailingPE', data=pe_data)
                plt.title('P/E Ratio Comparison')
                plt.xticks(rotation=45)
                plt.ylabel('Trailing P/E')
            
            # 3. Return on Equity
            plt.subplot(2, 2, 3)
            if 'returnOnEquity' in df.columns:
                roe_data = df.sort_values('returnOnEquity', ascending=False)
                sns.barplot(x='Ticker', y='returnOnEquity', data=roe_data)
                plt.title('Return on Equity Comparison')
                plt.xticks(rotation=45)
                plt.ylabel('ROE')
            
            # 4. Debt to Equity
            plt.subplot(2, 2, 4)
            if 'debtToEquity' in df.columns:
                debt_data = df.sort_values('debtToEquity')
                sns.barplot(x='Ticker', y='debtToEquity', data=debt_data)
                plt.title('Debt to Equity Comparison')
                plt.xticks(rotation=45)
                plt.ylabel('Debt/Equity')
            
            plt.tight_layout()
            
            # Save the visualization
            viz_file = self.visualizations_dir / f"{filename_base}.png"
            plt.savefig(viz_file)
            plt.close()
            
            logger.info(f"Comparison charts saved to {viz_file}")
            return str(viz_file)
        except Exception as e:
            logger.error(f"Error generating comparison charts: {e}")
            return None
    
    def _generate_sector_performance_charts(self, df, sector_name, top_n, filename_base):
        """Generate sector performance charts."""
        try:
            plt.figure(figsize=(15, 12))
            
            # Filter to top companies by market cap for better visualization
            if len(df) > top_n and 'MarketCap' in df.columns:
                top_companies = df.nlargest(top_n, 'MarketCap')
            else:
                top_companies = df
            
            # 1. Return on Equity for Top Companies
            plt.subplot(2, 2, 1)
            if 'returnOnEquity' in top_companies.columns:
                roe_data = top_companies.sort_values('returnOnEquity', ascending=False)
                sns.barplot(x='Ticker', y='returnOnEquity', data=roe_data)
                plt.title(f'Return on Equity - Top Companies in {sector_name}')
                plt.xticks(rotation=45)
                plt.ylabel('ROE')
            
            # 2. Profit Margins for Top Companies
            plt.subplot(2, 2, 2)
            if 'profitMargins' in top_companies.columns:
                margin_data = top_companies.sort_values('profitMargins', ascending=False)
                sns.barplot(x='Ticker', y='profitMargins', data=margin_data)
                plt.title(f'Profit Margins - Top Companies in {sector_name}')
                plt.xticks(rotation=45)
                plt.ylabel('Profit Margin')
            
            # 3. Free Cash Flow for Top Companies
            plt.subplot(2, 2, 3)
            if 'freeCashflow' in top_companies.columns:
                fcf_data = top_companies.sort_values('freeCashflow', ascending=False)
                sns.barplot(x='Ticker', y='freeCashflow', data=fcf_data)
                plt.title(f'Free Cash Flow - Top Companies in {sector_name}')
                plt.xticks(rotation=45)
                plt.ylabel('Free Cash Flow')
            
            # 4. Revenue Growth for Top Companies
            plt.subplot(2, 2, 4)
            if 'revenueGrowth' in top_companies.columns:
                growth_data = top_companies.sort_values('revenueGrowth', ascending=False)
                sns.barplot(x='Ticker', y='revenueGrowth', data=growth_data)
                plt.title(f'Revenue Growth - Top Companies in {sector_name}')
                plt.xticks(rotation=45)
                plt.ylabel('Revenue Growth')
            
            plt.tight_layout()
            
            # Save the visualization
            viz_file = self.visualizations_dir / f"{filename_base}.png"
            plt.savefig(viz_file)
            plt.close()
            
            logger.info(f"Sector performance charts saved to {viz_file}")
            return str(viz_file)
        except Exception as e:
            logger.error(f"Error generating sector performance charts: {e}")
            return None
    
    def _generate_valuation_charts(self, df, title, filename_base):
        """Generate valuation metrics charts."""
        try:
            plt.figure(figsize=(15, 12))
            
            # 1. P/E Ratio Comparison
            plt.subplot(2, 2, 1)
            if 'trailingPE' in df.columns:
                pe_data = df.sort_values('trailingPE')
                sns.barplot(x='Ticker', y='trailingPE', data=pe_data)
                plt.title('P/E Ratio Comparison')
                plt.xticks(rotation=45)
                plt.ylabel('Trailing P/E')
            
            # 2. P/B Ratio Comparison
            plt.subplot(2, 2, 2)
            if 'priceToBook' in df.columns:
                pb_data = df.sort_values('priceToBook')
                sns.barplot(x='Ticker', y='priceToBook', data=pb_data)
                plt.title('Price to Book Comparison')
                plt.xticks(rotation=45)
                plt.ylabel('P/B Ratio')
            
            # 3. P/S Ratio Comparison
            plt.subplot(2, 2, 3)
            if 'priceToSales' in df.columns:
                ps_data = df.sort_values('priceToSales')
                sns.barplot(x='Ticker', y='priceToSales', data=ps_data)
                plt.title('Price to Sales Comparison')
                plt.xticks(rotation=45)
                plt.ylabel('P/S Ratio')
            
            # 4. EV/EBITDA Comparison
            plt.subplot(2, 2, 4)
            if 'enterpriseToEbitda' in df.columns:
                ev_ebitda_data = df.sort_values('enterpriseToEbitda')
                sns.barplot(x='Ticker', y='enterpriseToEbitda', data=ev_ebitda_data)
                plt.title('EV/EBITDA Comparison')
                plt.xticks(rotation=45)
                plt.ylabel('EV/EBITDA')
            
            plt.tight_layout()
            plt.suptitle(f'Valuation Metrics for {title}', fontsize=16, y=1.02)
            
            # Save the visualization
            viz_file = self.visualizations_dir / f"{filename_base}.png"
            plt.savefig(viz_file)
            plt.close()
            
            logger.info(f"Valuation charts saved to {viz_file}")
            return str(viz_file)
        except Exception as e:
            logger.error(f"Error generating valuation charts: {e}")
            return None
    
    def _generate_pdf_report(self, df, output_file, tickers=None, sector=None):
        """Generate a PDF report with the analysis results."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            
            # Create document
            doc = SimpleDocTemplate(output_file, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title_style = styles["Title"]
            if sector:
                title = f"Financial Analysis Report - {sector} Sector"
            else:
                title = "Financial Analysis Report - Selected Companies"
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 12))
            
            # Date
            date_style = styles["Normal"]
            story.append(Paragraph(f"Report Date: {datetime.now().strftime('%Y-%m-%d')}", date_style))
            story.append(Spacer(1, 12))
            
            # Introduction
            heading_style = styles["Heading1"]
            normal_style = styles["Normal"]
            
            story.append(Paragraph("Introduction", heading_style))
            if sector:
                intro_text = f"""This report provides a detailed financial analysis of companies in the {sector} sector. 
                It includes valuation metrics, performance indicators, and comparative analysis of key financial ratios."""
            else:
                ticker_str = ", ".join(tickers) if tickers else "selected companies"
                intro_text = f"""This report provides a detailed financial analysis of {ticker_str}. 
                It includes valuation metrics, performance indicators, and comparative analysis of key financial ratios."""
            story.append(Paragraph(intro_text, normal_style))
            story.append(Spacer(1, 12))
            
            # Companies included
            story.append(Paragraph("Companies Included in Analysis", heading_style))
            data = [["Ticker", "Company Name"]]
            for _, row in df.iterrows():
                data.append([row["Ticker"], row["Name"]])
            
            table = Table(data, colWidths=[80, 300])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)
            story.append(Spacer(1, 12))
            
            # Key Metrics Table
            story.append(Paragraph("Key Financial Metrics", heading_style))
            key_metrics = ['trailingPE', 'priceToBook', 'priceToSales', 'returnOnEquity', 'profitMargins']
            key_metric_names = {
                'trailingPE': 'P/E Ratio',
                'priceToBook': 'Price to Book',
                'priceToSales': 'Price to Sales',
                'returnOnEquity': 'Return on Equity',
                'profitMargins': 'Profit Margin'
            }
            
            # Filter only columns that exist in df
            available_metrics = [m for m in key_metrics if m in df.columns]
            
            if available_metrics:
                metric_data = [["Ticker"] + [key_metric_names.get(m, m) for m in available_metrics]]
                for _, row in df.iterrows():
                    metric_row = [row["Ticker"]]
                    for metric in available_metrics:
                        value = row.get(metric, np.nan)
                        if pd.isna(value):
                            metric_row.append("N/A")
                        elif isinstance(value, float):
                            metric_row.append(f"{value:.2f}")
                        else:
                            metric_row.append(str(value))
                    metric_data.append(metric_row)
                
                metric_table = Table(metric_data)
                metric_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(metric_table)
            else:
                story.append(Paragraph("No key metrics data available", normal_style))
            
            story.append(Spacer(1, 12))
            
            # Analysis Summary
            story.append(Paragraph("Analysis Summary", heading_style))
            
            # Calculate some summary statistics
            summary_text = ""
            
            if 'marketCap' in df.columns and not df['marketCap'].isna().all():
                largest_company = df.loc[df['marketCap'].idxmax()]
                summary_text += f"The largest company by market capitalization is {largest_company['Name']} ({largest_company['Ticker']}).\n\n"
            
            if 'trailingPE' in df.columns and not df['trailingPE'].isna().all():
                lowest_pe = df.loc[df['trailingPE'].idxmin()]
                summary_text += f"The company with the lowest P/E ratio is {lowest_pe['Name']} ({lowest_pe['Ticker']}) with a P/E of {lowest_pe['trailingPE']:.2f}.\n\n"
            
            if 'returnOnEquity' in df.columns and not df['returnOnEquity'].isna().all():
                highest_roe = df.loc[df['returnOnEquity'].idxmax()]
                summary_text += f"The company with the highest Return on Equity is {highest_roe['Name']} ({highest_roe['Ticker']}) with an ROE of {highest_roe['returnOnEquity']:.2f}.\n\n"
            
            if 'profitMargins' in df.columns and not df['profitMargins'].isna().all():
                highest_margin = df.loc[df['profitMargins'].idxmax()]
                summary_text += f"The company with the highest profit margin is {highest_margin['Name']} ({highest_margin['Ticker']}) with a margin of {highest_margin['profitMargins']:.2f}.\n\n"
            
            if summary_text:
                story.append(Paragraph(summary_text, normal_style))
            else:
                story.append(Paragraph("Insufficient data for summary analysis.", normal_style))
            
            # Build the PDF
            doc.build(story)
            return True
        
        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
            return False

def main():
    """Main entry point for the financial metrics analyzer."""
    parser = argparse.ArgumentParser(description="Financial Metrics Analyzer")
    
    # Define command line arguments
    parser.add_argument(
        "--mode", 
        choices=["compare", "sector_performance", "valuation_metrics"], 
        required=True,
        help="Analysis mode"
    )
    parser.add_argument(
        "--tickers", 
        nargs="+", 
        help="List of stock tickers to analyze"
    )
    parser.add_argument(
        "--sector", 
        help="Sector to analyze"
    )
    parser.add_argument(
        "--output", 
        help="Output file path for the report (e.g., report.pdf)"
    )
    parser.add_argument(
        "--metrics", 
        nargs="+", 
        help="List of financial metrics to analyze"
    )
    
    args = parser.parse_args()
    
    # Initialize the analyzer
    analyzer = FinancialMetricsAnalyzer()
    
    # Run the selected analysis mode
    if args.mode == "compare":
        if not args.tickers or len(args.tickers) < 2:
            logger.error("At least two tickers required for comparison mode")
            return
        analyzer.compare_companies(args.tickers, args.metrics, args.output)
    elif args.mode == "sector_performance":
        if not args.sector:
            logger.error("Sector name required for sector_performance mode")
            return
        analyzer.analyze_sector_performance(args.sector, output=args.output)
    elif args.mode == "valuation_metrics":
        if not args.tickers and not args.sector:
            logger.error("Either tickers or sector required for valuation_metrics mode")
            return
        analyzer.analyze_valuation_metrics(args.tickers, args.sector, args.output)

if __name__ == "__main__":
    main()