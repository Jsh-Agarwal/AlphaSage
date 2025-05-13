"""
Indian Company IR Website Scraper

This module handles scraping of Investor Relations content from Indian company websites.
It extracts annual reports, investor presentations, earnings call transcripts, and other IR materials.
"""

import os
import re
import time
import random
import logging
import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime, timedelta
from pathlib import Path
import PyPDF2
import pytesseract
from PIL import Image
import pdf2image

logger = logging.getLogger(__name__)

class IndianIRScraper:
    """Scrape IR content from Indian company websites."""
    
    # Known IR website URLs for major companies
    KNOWN_IR_URLS = {
        'TCS': 'https://www.tcs.com/investor-relations',
        'INFY': 'https://www.infosys.com/investors.html',
        'WIPRO': 'https://www.wipro.com/investors/',
        'HDFCBANK': 'https://www.hdfcbank.com/personal/about-us/investor-relations',
        'RELIANCE': 'https://www.ril.com/InvestorRelations.aspx',
        'TATAMOTORS': 'https://www.tatamotors.com/investors/',
    }
    
    # Common IR section patterns in URLs
    IR_PATTERNS = [
        'investor-relations', 'investors', 'investor',
        'financials', 'financial-information',
        'shareholders', 'reports', 'annual-reports',
        'quarterly-results', 'presentations',
        'concall', 'earnings-call', 'transcripts'
    ]
    
    # Common IR document patterns
    DOCUMENT_PATTERNS = {
        'annual_report': [
            r'annual.?report', r'(?:FY|20)\d{2}.?\d{2}',
            r'integrated.?report', r'yearly.?report'
        ],
        'investor_presentation': [
            r'investor.?presentation', r'corporate.?presentation',
            r'quarterly.?presentation', r'results.?presentation',
            r'earnings.?presentation'
        ],
        'concall_transcript': [
            r'concall', r'conference.?call', r'earnings.?call',
            r'transcript', r'q\d.?(?:FY)?\d{2}.?\d{2}'
        ],
        'financial_results': [
            r'financial.?results', r'quarterly.?results',
            r'q\d.?results', r'results.?press.?release'
        ]
    }
    
    def __init__(self, download_dir="downloads/ir_documents", max_docs=5, lookback_quarters=2):
        """
        Initialize the IR scraper.
        
        Args:
            download_dir (str): Directory to save downloaded documents
            max_docs (int): Maximum number of documents to download per type
            lookback_quarters (int): Number of quarters to look back for documents
        """
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.max_docs = max_docs
        self.lookback_quarters = lookback_quarters
        
        # Initialize Selenium options
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('--headless')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        
        # Set download preferences
        prefs = {
            "download.default_directory": str(self.download_dir.absolute()),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True
        }
        self.options.add_experimental_option("prefs", prefs)
        
        self.driver = None
        
        # Common headers for requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive'
        }
    
    def _init_driver(self):
        """Initialize the Selenium WebDriver if not already initialized."""
        if not self.driver:
            self.driver = webdriver.Chrome(options=self.options)
    
    def _close_driver(self):
        """Close the Selenium WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def _random_delay(self, min_sec=2, max_sec=5):
        """Add random delay between requests to avoid overwhelming servers."""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def find_ir_website(self, company_name, exchange_code=None):
        """
        Find the IR website for a company.
        
        Args:
            company_name (str): Name of the company
            exchange_code (str): NSE/BSE code if known
            
        Returns:
            str: URL of the IR website section
        """
        try:
            # First check if we have a known URL
            if exchange_code and exchange_code in self.KNOWN_IR_URLS:
                logger.info(f"Using known IR URL for {exchange_code}")
                return self.KNOWN_IR_URLS[exchange_code]
            
            # Try common URL patterns
            company_slug = company_name.lower().replace(' ', '')
            possible_domains = [
                f"www.{company_slug}.com",
                f"{company_slug}.com",
                f"www.{company_slug}.co.in",
                f"{company_slug}.co.in"
            ]
            
            for domain in possible_domains:
                for pattern in self.IR_PATTERNS:
                    url = f"https://{domain}/{pattern}"
                    try:
                        response = requests.head(url, headers=self.headers, timeout=5)
                        if response.status_code == 200:
                            logger.info(f"Found IR website at {url}")
                            return url
                    except:
                        continue
            
            # If no direct URL works, try a more targeted Google search
            if exchange_code:
                search_url = f"https://www.google.com/search?q={exchange_code}+investor+relations+site:{company_slug}.com"
            else:
                search_url = f"https://www.google.com/search?q={company_name}+investor+relations+india"
            
            self._init_driver()
            self.driver.get(search_url)
            
            # Wait for search results with a longer timeout
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "a"))
                )
            except TimeoutException:
                logger.warning("Timeout waiting for search results")
                return None
            
            # Get all links
            links = self.driver.find_elements(By.TAG_NAME, "a")
            
            # Look for IR-related links
            for link in links:
                url = link.get_attribute("href")
                if url and any(pattern in url.lower() for pattern in self.IR_PATTERNS):
                    logger.info(f"Found IR website through search: {url}")
                    return url
            
            # If no IR-specific link found, try company domain
            for link in links:
                url = link.get_attribute("href")
                if url and company_slug in url.lower():
                    logger.info(f"Found company website: {url}")
                    return url
                    
        except Exception as e:
            logger.error(f"Error finding IR website for {company_name}: {e}")
        
        return None
    
    def _download_file(self, url, filename=None, doc_type=None):
        """Download a file from URL."""
        try:
            response = requests.get(url, headers=self.headers, stream=True)
            response.raise_for_status()
            
            # Get filename from URL if not provided
            if not filename:
                filename = url.split('/')[-1]
                # Clean filename
                filename = re.sub(r'[\\/*?:"<>|]', "_", filename)
            
            # Add document type prefix if provided
            if doc_type:
                filename = f"{doc_type}_{filename}"
            
            # Add timestamp if file exists
            filepath = self.download_dir / filename
            if filepath.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{filepath.stem}_{timestamp}{filepath.suffix}"
                filepath = self.download_dir / filename
            
            # Save file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return {
                'filepath': str(filepath),
                'url': url,
                'type': doc_type,
                'filename': filename
            }
            
        except Exception as e:
            logger.error(f"Error downloading file from {url}: {e}")
            return None
    
    def _is_document_link(self, url, text=""):
        """Check if URL points to a document."""
        if not url:
            return False
            
        # Check URL patterns
        doc_patterns = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']
        if any(pattern in url.lower() for pattern in doc_patterns):
            return True
            
        # Check text patterns
        text = text.lower()
        doc_keywords = ['download', 'view', 'open', 'report', 'presentation', 'transcript']
        if any(keyword in text for keyword in doc_keywords):
            return True
            
        return False
    
    def _classify_document(self, url, text=""):
        """Classify document type based on URL and text."""
        url_lower = url.lower()
        text_lower = text.lower()
        
        for doc_type, patterns in self.DOCUMENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, url_lower) or re.search(pattern, text_lower):
                    return doc_type
        
        return "other"
    
    def scrape_ir_documents(self, company_name, ir_url=None, exchange_code=None):
        """
        Scrape IR documents from company website.
        
        Args:
            company_name (str): Name of the company
            ir_url (str): URL of IR website section (optional)
            exchange_code (str): NSE/BSE code (optional)
            
        Returns:
            dict: Dictionary of downloaded documents by type
        """
        try:
            # Find IR website if not provided
            if not ir_url:
                ir_url = self.find_ir_website(company_name, exchange_code)
                if not ir_url:
                    logger.error(f"Could not find IR website for {company_name}")
                    return {}
            
            logger.info(f"Scraping IR documents from {ir_url}")
            
            self._init_driver()
            self.driver.get(ir_url)
            
            # Calculate date range for recent documents
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.lookback_quarters * 90)
            
            # Process documents
            documents = {
                'annual_report': [],
                'investor_presentation': [],
                'concall_transcript': [],
                'financial_results': [],
                'other': []
            }
            
            processed_urls = set()
            
            # Get all document links
            links = self._get_document_links(ir_url)
            
            # Sort links by date (if available) and limit by type
            for doc_type in documents.keys():
                type_links = [link for link in links if self._classify_document(link['url'], link.get('text', '')) == doc_type]
                type_links = self._sort_links_by_date(type_links)
                
                # Take only the most recent documents up to max_docs
                for link in type_links[:self.max_docs]:
                    if link['url'] not in processed_urls:
                        result = self._process_document(link['url'], doc_type)
                        if result:
                            documents[doc_type].append(result)
                            processed_urls.add(link['url'])
            
            return documents
            
        except Exception as e:
            logger.error(f"Error scraping IR documents for {company_name}: {e}")
            return {}
            
        finally:
            self._close_driver()

    def _get_document_links(self, url):
        """Get all document links from a page and its IR sections."""
        links = []
        
        # Get links from main page
        page_links = self._get_page_links(url)
        links.extend(page_links)
        
        # Look for additional IR sections
        for pattern in self.IR_PATTERNS:
            try:
                section_links = self.driver.find_elements(
                    By.XPATH,
                    f"//a[contains(@href, '{pattern}')]"
                )
                
                for link in section_links:
                    section_url = link.get_attribute("href")
                    if section_url and section_url != url:
                        self._random_delay()
                        self.driver.get(section_url)
                        section_page_links = self._get_page_links(section_url)
                        links.extend(section_page_links)
                        
            except Exception as e:
                logger.error(f"Error processing section {pattern}: {e}")
                continue
        
        return links

    def _get_page_links(self, url):
        """Get document links from a single page."""
        links = []
        
        try:
            # Wait for page load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Get all links
            elements = self.driver.find_elements(By.TAG_NAME, "a")
            
            for element in elements:
                try:
                    href = element.get_attribute("href")
                    text = element.text.strip()
                    
                    if href and self._is_document_link(href, text):
                        # Try to extract date from link or text
                        date = self._extract_date(href) or self._extract_date(text)
                        
                        links.append({
                            'url': href,
                            'text': text,
                            'date': date
                        })
                except:
                    continue
                    
        except Exception as e:
            logger.error(f"Error getting links from {url}: {e}")
        
        return links

    def _sort_links_by_date(self, links):
        """Sort links by date, with most recent first."""
        return sorted(
            links,
            key=lambda x: x.get('date', datetime.min),
            reverse=True
        )

    def _process_document(self, url, doc_type):
        """Download and process a document."""
        try:
            # Download the document
            self._random_delay(1, 3)
            result = self._download_file(url, doc_type=doc_type)
            
            if result:
                # Extract text using OCR if needed
                text = self._extract_document_text(result['filepath'])
                if text:
                    result['text_content'] = text
                    
                    # Extract metadata
                    metadata = self._extract_document_metadata(text, doc_type)
                    result.update(metadata)
                
                return result
                
        except Exception as e:
            logger.error(f"Error processing document {url}: {e}")
            return None

    def _extract_document_text(self, filepath):
        """Extract text from a document using OCR if needed."""
        try:
            if filepath.endswith('.pdf'):
                # Try normal PDF extraction first
                text = self._extract_pdf_text(filepath)
                
                # If no text found, try OCR
                if not text or len(text.strip()) < 100:  # Arbitrary minimum length
                    text = self._ocr_pdf(filepath)
                
                return text
            else:
                # For other file types, just read as text
                with open(filepath, 'r', encoding='utf-8') as f:
                    return f.read()
                    
        except Exception as e:
            logger.error(f"Error extracting text from {filepath}: {e}")
            return None

    def _extract_pdf_text(self, pdf_path):
        """Extract text from PDF using PyPDF2."""
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            return None

    def _ocr_pdf(self, pdf_path):
        """Perform OCR on a PDF file."""
        try:
            text = ""
            # Convert PDF to images
            images = pdf2image.convert_from_path(pdf_path)
            
            # Process each page
            for i, image in enumerate(images):
                # Perform OCR
                page_text = pytesseract.image_to_string(image)
                text += f"\n--- Page {i+1} ---\n" + page_text
            
            return text
        except Exception as e:
            logger.error(f"Error performing OCR: {e}")
            return None

    def _extract_document_metadata(self, text, doc_type):
        """Extract metadata from document text."""
        metadata = {
            'date': None,
            'quarter': None,
            'year': None,
            'type': doc_type
        }
        
        # Extract date
        date_match = re.search(self._get_date_pattern(), text)
        if date_match:
            metadata['date'] = date_match.group()
        
        # Extract quarter/year
        quarter_match = re.search(r'Q[1-4]\s*(?:FY)?\s*\d{2}(?:\d{2})?', text)
        if quarter_match:
            quarter_text = quarter_match.group()
            metadata['quarter'] = quarter_text
            
            # Try to extract year from quarter text
            year_match = re.search(r'\d{2}(?:\d{2})?', quarter_text)
            if year_match:
                year = year_match.group()
                if len(year) == 2:
                    year = '20' + year
                metadata['year'] = year
        
        return metadata

    def _get_date_pattern(self):
        """Get regex pattern for date matching."""
        return r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}\b'

    def _extract_date(self, text):
        """Extract date from text."""
        if not text:
            return None
            
        date_match = re.search(self._get_date_pattern(), text)
        if date_match:
            try:
                return datetime.strptime(date_match.group(), '%d %B %Y')
            except:
                try:
                    return datetime.strptime(date_match.group(), '%d %b %Y')
                except:
                    return None
        return None

    def extract_concall_text(self, transcript_file):
        """
        Extract text from a concall transcript file.
        
        Args:
            transcript_file (str): Path to the transcript file
            
        Returns:
            dict: Extracted text with metadata
        """
        try:
            if transcript_file.endswith('.pdf'):
                import PyPDF2
                with open(transcript_file, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
            else:
                with open(transcript_file, 'r', encoding='utf-8') as file:
                    text = file.read()
            
            # Extract metadata
            metadata = {
                'date': None,
                'quarter': None,
                'year': None,
                'participants': []
            }
            
            # Try to extract date
            date_pattern = r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}\b'
            date_match = re.search(date_pattern, text)
            if date_match:
                metadata['date'] = date_match.group()
            
            # Try to extract quarter/year
            quarter_pattern = r'Q[1-4]\s*(?:FY)?\s*\d{2}(?:\d{2})?'
            quarter_match = re.search(quarter_pattern, text)
            if quarter_match:
                quarter_text = quarter_match.group()
                metadata['quarter'] = quarter_text
            
            # Try to extract participants
            participant_pattern = r'(?:Participants?|Speakers?|Present|Attendees?):\s*([^\n]+)'
            participant_match = re.search(participant_pattern, text, re.IGNORECASE)
            if participant_match:
                participants = participant_match.group(1).split(',')
                metadata['participants'] = [p.strip() for p in participants]
            
            return {
                'text': text,
                'metadata': metadata,
                'file_path': transcript_file
            }
            
        except Exception as e:
            logger.error(f"Error extracting text from transcript {transcript_file}: {e}")
            return None
    
    def __del__(self):
        """Clean up resources."""
        self._close_driver()

def main():
    """CLI interface for testing the IR scraper."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Indian Company IR Scraper")
    parser.add_argument("company", help="Company name to scrape")
    parser.add_argument("--code", help="NSE/BSE code")
    parser.add_argument("--url", help="Direct IR website URL")
    
    args = parser.parse_args()
    
    scraper = IndianIRScraper()
    documents = scraper.scrape_ir_documents(args.company, args.url, args.code)
    
    print(f"\nDownloaded documents for {args.company}:")
    for doc_type, docs in documents.items():
        if docs:
            print(f"\n{doc_type.replace('_', ' ').title()}:")
            for doc in docs:
                print(f"- {doc['filename']}")

if __name__ == "__main__":
    main() 