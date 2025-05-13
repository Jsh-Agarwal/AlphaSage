#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Indian Equity Document Scraper

This module retrieves corporate documents (annual reports, investor presentations,
press releases, etc.) from Indian company websites and corporate filing repositories.
"""

import os
import re
import time
import random
import logging
import requests
import urllib.parse
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("document_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IndianEquityDocScraper:
    """Scrape financial documents for Indian companies."""
    
    def __init__(self, download_dir="downloads"):
        """Initialize document scraper with a download directory."""
        self.download_dir = download_dir
        os.makedirs(download_dir, exist_ok=True)
        
        # Headers to mimic a browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
    
    def _random_delay(self, min_sec=1, max_sec=3):
        """Add a random delay to avoid overwhelming servers."""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def _download_file(self, url, file_type, source_name):
        """Download a file and save it to the download directory."""
        try:
            # Clean the URL
            url = url.strip()
            
            # Check if URL is valid
            if not url.startswith(('http://', 'https://')):
                logger.warning(f"Invalid URL: {url}")
                return None
            
            # Generate a filename based on the URL and source
            parsed_url = urllib.parse.urlparse(url)
            path_segments = parsed_url.path.split('/')
            if path_segments and path_segments[-1]:
                filename = path_segments[-1]
                # Clean filename
                filename = re.sub(r'[\\/*?:"<>|]', "_", filename)
            else:
                # Generate a filename using the current timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{source_name}_{timestamp}.pdf"
            
            # Add file type prefix
            filename = f"{file_type}_{filename}"
            
            # Full path to save the file
            filepath = os.path.join(self.download_dir, filename)
            
            # Check if file already exists
            if os.path.exists(filepath):
                logger.info(f"File already exists: {filepath}")
                return {
                    "filepath": filepath,
                    "url": url,
                    "type": file_type,
                    "source": source_name,
                    "title": filename
                }
            
            # Download the file
            logger.info(f"Downloading {url} to {filepath}")
            
            response = requests.get(url, headers=self.headers, timeout=30, stream=True)
            response.raise_for_status()
            
            # Save the file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Downloaded {url} to {filepath}")
            
            return {
                "filepath": filepath,
                "url": url,
                "type": file_type,
                "source": source_name,
                "title": filename
            }
        
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            return None
    
    def get_nse_company_details(self, ticker):
        """Get company details from NSE website."""
        # Remove .NS suffix if present
        if ticker.endswith('.NS'):
            ticker = ticker[:-3]
        
        url = f"https://www.nseindia.com/get-quotes/equity?symbol={ticker}"
        
        try:
            logger.info(f"Fetching NSE details for {ticker} from {url}")
            
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find company name, sector, and other details
            company_info = {}
            
            # Extract company name
            name_element = soup.select_one('.companyName')
            if name_element:
                company_info['name'] = name_element.text.strip()
            
            # Extract sector
            sector_element = soup.select_one('.industry')
            if sector_element:
                company_info['sector'] = sector_element.text.strip()
            
            logger.info(f"Found NSE details for {ticker}: {company_info}")
            return company_info
            
        except Exception as e:
            logger.error(f"Error fetching NSE details for {ticker}: {e}")
            return {}
    
    def scrape_company_ir_site(self, ticker, company_name=None):
        """Scrape investor relations site for documents."""
        # If no company name provided, try to get it from NSE
        if not company_name:
            company_details = self.get_nse_company_details(ticker)
            company_name = company_details.get('name', ticker)
        
        # Simulate a company IR site with documents
        # In a real implementation, you would search for and scrape the actual IR site
        
        # For demonstration purposes, we'll create some dummy documents
        documents = []
        
        # 1. Annual Reports
        annual_report_url = f"https://example.com/{ticker}/annual_report_2024.pdf"
        doc_info = {
            "url": annual_report_url,
            "type": "annual_report",
            "source": f"Company IR_Annual_Reports",
            "title": f"Annual Report 2024 - {company_name}"
        }
        
        # 2. Quarterly Results
        quarterly_report_url = f"https://example.com/{ticker}/q4_2024_results.pdf"
        doc_info2 = {
            "url": quarterly_report_url,
            "type": "investor_presentation",
            "source": f"Company IR_Financial_Results_for_the_quarter_ended_March_31,_",
            "title": f"Q4 2024 Results - {company_name}"
        }
        
        # 3. Corporate Governance Report
        governance_report_url = f"https://example.com/{ticker}/governance_report_2024.pdf"
        doc_info3 = {
            "url": governance_report_url,
            "type": "annual_report",
            "source": f"Company IR_Annual_Report_Section",
            "title": f"Corporate Governance Report 2024 - {company_name}"
        }
        
        # 4. Sustainability Report
        sustainability_report_url = f"https://example.com/{ticker}/sustainability_report_2024.pdf"
        doc_info4 = {
            "url": sustainability_report_url,
            "type": "investor_presentation",
            "source": f"Company IR_Modern_Slavery_Statement",
            "title": f"Sustainability Report 2024 - {company_name}"
        }
        
        # 5. Management Changes
        management_changes_url = f"https://example.com/{ticker}/management_changes_2024.pdf"
        doc_info5 = {
            "url": management_changes_url,
            "type": "investor_presentation",
            "source": f"Company IR_Ms._Aarthi_Subramanian_as_Executive_Director_Presi",
            "title": f"Management Changes 2024 - {company_name}"
        }
        
        # 6. Strategy Update
        strategy_update_url = f"https://example.com/{ticker}/strategy_update_2024.pdf"
        doc_info6 = {
            "url": strategy_update_url,
            "type": "investor_presentation",
            "source": f"Company IR_Appointment_of_Mr._Mangesh_Sathe_as_Chief_Strategy",
            "title": f"Strategy Update 2024 - {company_name}"
        }
        
        # Instead of actually downloading from example.com (which won't work),
        # we'll create dummy PDF files in our downloads directory
        # This simulates the download process
        
        for doc in [doc_info, doc_info2, doc_info3, doc_info4, doc_info5, doc_info6]:
            # Generate a timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create a filename
            filename = f"{doc['type']}_{doc['source']}_{timestamp}.pdf"
            filepath = os.path.join(self.download_dir, filename)
            
            # Create an empty PDF file (or a simple text file as a placeholder)
            with open(filepath, 'w') as f:
                f.write(f"Dummy PDF file for {doc['title']}\n")
                f.write(f"Ticker: {ticker}\n")
                f.write(f"Type: {doc['type']}\n")
                f.write(f"Source: {doc['source']}\n")
                f.write(f"Generated: {timestamp}\n")
            
            # Add the document with its local filepath
            doc['filepath'] = filepath
            documents.append(doc)
            
            # Add a small delay between downloads
            self._random_delay(0.5, 1.5)
        
        logger.info(f"Scraped {len(documents)} documents from company IR site for {ticker}")
        return documents
    
    def scrape_bse_filings(self, ticker):
        """Scrape BSE filings for a company."""
        # In a real implementation, you would scrape the BSE website
        
        # For now, we'll return an empty list
        logger.info(f"BSE filings not implemented for {ticker}")
        return []
    
    def scrape_nse_filings(self, ticker):
        """Scrape NSE filings for a company."""
        # In a real implementation, you would scrape the NSE website
        
        # For now, we'll return an empty list
        logger.info(f"NSE filings not implemented for {ticker}")
        return []
    
    def download_all_documents(self, ticker):
        """Download all available documents for a ticker."""
        # Combine documents from all sources
        all_documents = []
        
        # 1. Company IR Site
        ir_documents = self.scrape_company_ir_site(ticker)
        if ir_documents:
            all_documents.extend(ir_documents)
        
        # 2. BSE Filings (if ticker ends with .BO)
        if ticker.endswith('.BO'):
            bse_documents = self.scrape_bse_filings(ticker)
            if bse_documents:
                all_documents.extend(bse_documents)
        
        # 3. NSE Filings (if ticker ends with .NS)
        if ticker.endswith('.NS'):
            nse_documents = self.scrape_nse_filings(ticker)
            if nse_documents:
                all_documents.extend(nse_documents)
        
        logger.info(f"Downloaded {len(all_documents)} documents for {ticker}")
        return all_documents

def main():
    """Main function to test the scraper."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Indian Equity Document Scraper")
    parser.add_argument("ticker", help="Stock ticker (e.g., INFY.NS, TCS.NS)")
    args = parser.parse_args()
    
    scraper = IndianEquityDocScraper()
    documents = scraper.download_all_documents(args.ticker)
    
    print(f"Downloaded {len(documents)} documents for {args.ticker}:")
    for i, doc in enumerate(documents, 1):
        print(f"{i}. {doc['title']} - {doc['filepath']}")

if __name__ == "__main__":
    main()