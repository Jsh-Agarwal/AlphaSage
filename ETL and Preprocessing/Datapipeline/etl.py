from bs4 import BeautifulSoup
from nltk.tokenize import sent_tokenize
from datetime import datetime, timedelta
from neo4j import GraphDatabase
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
from nselib import capital_market
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from GoogleNews import GoogleNews
from transformers import pipeline
import logging
import threading
import functools
import json
import os
import pandas as pd
import numpy as np
import argparse
import yfinance as yf
import requests
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("Groq package not available. GROQ analysis will be disabled.")
from .indian_ir_scraper import IndianIRScraper

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Neo4jDatabase:
    """Handle connection and operations for Neo4j graph database."""
    
    def __init__(self, uri, user, password):
        """Initialize Neo4j connection."""
        self.uri = uri       
        self.user = user
        self.password = password
        self.driver = None
        self.connect()
    
    def connect(self):
        """Establish connection to Neo4j."""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            logger.info("Connected to Neo4j database")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j database: {e}")
            self.driver = None
    
    def close(self):
        """Close the Neo4j connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def verify_connection(self):
        """Verify the Neo4j connection."""
        if not self.driver:
            logger.error("Neo4j driver is not initialized")
            return False
        
        try:
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("Neo4j connection verified")
            return True
        except Exception as e:
            logger.error(f"Neo4j connection verification failed: {e}")
            return False

class TextProcessor:
    """Process text documents for embedding and knowledge graph storage."""  
    # Placeholder for TextProcessor implementation

class RateLimiter:
    """Handle API rate limiting and backoff strategies."""
    
    def __init__(self):
        """Initialize rate limiter with default settings.""" 
        # Ensure time module is available
        import time
        self.time = time
        
        self.rate_limits = {
            # API name: [requests_per_minute, min_interval_seconds]
            "default": [60, 1.0],
            "sec_edgar": [10, 0.1],  # SEC EDGAR has strict rate limiting (10 requests per second)
            "yfinance": [2000, 0.05],  # Yahoo Finance is more permissive
            "nse": [60, 1.0],  # NSE API
            "bse": [60, 1.0],  # BSE API
            "screener": [20, 3.0],  # Screener.in website
            "moneycontrol": [20, 3.0]  # MoneyControl website
        }
        
        # Keep track of last API call time
        self.last_call_time = {}
        
        # Locks for thread safety
        self.locks = {api: threading.Lock() for api in self.rate_limits}
    
    def with_rate_limit(self, func, api_name="default"):
        """
        Decorator to apply rate limiting to a function.
        
        Args:
            func: The function to decorate
            api_name: The name of the API to apply rate limits for
            
        Returns:
            Decorated function with rate limiting
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal api_name
            if api_name not in self.rate_limits:
                api_name = "default"
                
            # Get rate limit settings
            _, min_interval = self.rate_limits[api_name]
            
            with self.locks[api_name]:
                # Check if we need to wait
                current_time = self.time.time()
                last_time = self.last_call_time.get(api_name, 0)
                elapsed = current_time - last_time
                
                if elapsed < min_interval:
                    wait_time = min_interval - elapsed
                    self.time.sleep(wait_time)
                
                # Update last call time
                self.last_call_time[api_name] = self.time.time()
            
            # Call the function
            return func(*args, **kwargs)
        
        return wrapper
    
    def exponential_backoff(self, func, max_retries=5, initial_wait=1, api_name="default"):
        """
        Apply exponential backoff for handling API failures.
        
        Args:
            func: The function to retry
            max_retries: Maximum number of retry attempts
            initial_wait: Initial wait time in seconds
            api_name: The API name for rate limiting
            
        Returns:
            Function result or raises the last exception
        """
        # Create a wrapped rate-limited function
        rate_limited_func = self.with_rate_limit(func, api_name)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            wait_time = initial_wait
            
            while retries < max_retries:
                try:
                    # Call the rate-limited function
                    result = rate_limited_func(*args, **kwargs)
                    return result
                except (requests.exceptions.RequestException, TimeoutError) as e:
                    retries += 1
                    if retries == max_retries:
                        logger.error(f"Max retries reached for {func.__name__}. Last error: {e}")
                        raise
                    
                    logger.warning(f"Attempt {retries} failed for {func.__name__}. Retrying in {wait_time} seconds...")
                    self.time.sleep(wait_time)
                    wait_time *= 2  # Exponential backoff
            
            # This should never be reached due to the raise in the exception handler
            return None
        
        return wrapper

class ConfigManager:
    """Manage configuration settings for the ETL pipeline."""
    
    def __init__(self, config_file=None):
        """Initialize configuration manager.""" 
        self.config = {
            "api_keys": {
                "alpha_vantage": None,
                "finnhub": None,
                "iex_cloud": None,
                "intrinio": None,
                "groq": None
            },
            "neo4j": {
                "uri": "bolt://localhost:7687",
                "user": "neo4j",
                "password": "password"
            },
            "data_sources": {
                "sec_filings": True,
                "nse_data": True,
                "bse_data": True,
                "yahoo_finance": True,
                "screener_in": True,
                "money_control": True,
                "trendlyne": True,
                "news": True
            },
            "scraping": {
                "user_agent": "Financial Research Assistant/1.0",
                "request_timeout": 30,
                "chrome_driver_path": None,
                "download_path": "./downloads"
            },
            "processing": {
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "max_pdf_size_mb": 50,
                "ocr_enabled": True,
                "max_threads": 5
            }
        }
        
        # Load from file if provided
        if config_file and os.path.exists(config_file):
            self.load_config(config_file)
            
        # Create download directory if it doesn't exist
        os.makedirs(self.config["scraping"]["download_path"], exist_ok=True)
    
    def load_config(self, config_file):
        """Load configuration from a JSON file.""" 
        try:
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                # Update the default config with file values
                self._update_nested_dict(self.config, file_config)
            logger.info(f"Loaded configuration from {config_file}")
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_file}: {e}")
    
    def _update_nested_dict(self, d, u):
        """Recursively update a nested dictionary.""" 
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._update_nested_dict(d[k], v)
            else:
                d[k] = v
    
    def save_config(self, config_file):
        """Save current configuration to a JSON file.""" 
        try:
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            logger.info(f"Saved configuration to {config_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save configuration to {config_file}: {e}")
            return False
    
    def get(self, key_path, default=None):
        """
        Get a configuration value using a dot-separated path.
        
        Args:
            key_path: Dot-separated path to the config value (e.g., "neo4j.uri")
            default: Default value if the path doesn't exist
            
        Returns:
            The configuration value or the default
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path, value):
        """
        Set a configuration value using a dot-separated path.
        
        Args:
            key_path: Dot-separated path to the config value (e.g., "neo4j.uri")
            value: Value to set
            
        Returns:
            Success (True/False)
        """
        keys = key_path.split('.')
        current = self.config
        
        # Navigate to the nested dictionary
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]
        
        # Set the value
        current[keys[-1]] = value
        return True

class DataFrameEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles pandas DataFrames and numpy types.""" 
    
    def default(self, obj):
        # Convert pandas DataFrame to a serializable format
        if isinstance(obj, pd.DataFrame):
            return {
                "data": obj.to_dict(orient="records"),
                "index": [str(idx) for idx in obj.index],
                "columns": list(obj.columns),
                "dtype": str(obj.dtypes.to_dict())
            }
        
        # Handle numpy types
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        # Handle pandas Timestamp
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        
        # Let the base encoder handle the rest
        return super().default(obj)

class DataCache:
    """Cache financial data locally to reduce API calls.""" 
    
    def __init__(self, cache_dir="cache"):
        """Initialize the cache.""" 
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def _get_cache_path(self, ticker, data_type):
        """Get the cache file path for a ticker and data type.""" 
        return os.path.join(self.cache_dir, f"{ticker}_{data_type}.json")
    
    def _is_cache_valid(self, cache_path, max_age_hours=24):
        """Check if cached data is still valid.""" 
        if not os.path.exists(cache_path):
            return False
            
        # Check file age
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
        age = datetime.now() - file_time
        return age.total_seconds() < max_age_hours * 3600
    
    def get(self, ticker, data_type):
        """Get data from cache if available and valid.""" 
        cache_path = self._get_cache_path(ticker, data_type)
        
        if self._is_cache_valid(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                self.logger.info(f"Retrieved {data_type} data for {ticker} from cache")
                return data
            except Exception as e:
                self.logger.warning(f"Failed to read cache for {ticker}: {e}")
                return None
        return None
    
    def save(self, ticker, data_type, data):
        """Save data to cache.""" 
        cache_path = self._get_cache_path(ticker, data_type)
        try:
            with open(cache_path, 'w') as f:
                json.dump(data, f, cls=DataFrameEncoder)
            self.logger.info(f"Cached {data_type} data for {ticker}")
            return True
        except Exception as e:
            self.logger.warning(f"Failed to cache data for {ticker}: {e}")
            return False

class DocumentScraper:
    """Scrapes financial documents from various sources.""" 
    
    def __init__(self, config_manager):
        """Initialize the document scraper.""" 
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self.rate_limiter = RateLimiter()
        self.options = None
        self.driver = None
        self.initialize_selenium()
    
    def initialize_selenium(self):
        """Initialize Selenium WebDriver if needed.""" 
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument(f"user-agent={self.config_manager.get('scraping.user_agent')}")
            
            # Set download path
            download_path = self.config_manager.get("scraping.download_path", "./downloads")
            os.makedirs(download_path, exist_ok=True)
            prefs = {
                "download.default_directory": download_path,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "plugins.always_open_pdf_externally": True
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            self.options = chrome_options
            self.logger.info("Selenium WebDriver options initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Selenium options: {e}")
    
    def get_driver(self):
        """Get or create a Selenium WebDriver instance.""" 
        if self.driver is not None:
            return self.driver
            
        try:
            # Check for Chrome WebDriver path
            driver_path = self.config_manager.get("scraping.chrome_driver_path")
            if driver_path:
                # Create driver with specified path
                from selenium.webdriver.chrome.service import Service
                service = Service(executable_path=driver_path)
                self.driver = webdriver.Chrome(service=service, options=self.options)
            else:
                # Create driver using auto-download
                self.driver = webdriver.Chrome(options=self.options)
                
            self.logger.info("Selenium WebDriver initialized")
            return self.driver
        except Exception as e:
            self.logger.error(f"Failed to initialize Selenium WebDriver: {e}")
            return None
    
    def close_driver(self):
        """Close the Selenium WebDriver.""" 
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                self.logger.info("Selenium WebDriver closed")
            except Exception as e:
                self.logger.error(f"Error closing Selenium WebDriver: {e}")
    
    def download_sec_filing(self, ticker, filing_type="10-K", count=1):
        """
        Download SEC filings for a company.
        
        Args:
            ticker: Company ticker symbol
            filing_type: Type of filing (10-K, 10-Q, 8-K, etc.)
            count: Number of most recent filings to download
            
        Returns:
            List of downloaded file paths
        """
        try:
            if not self.config_manager.get("data_sources.sec_filings"):
                return []
                
            self.logger.info(f"Downloading {filing_type} filings for {ticker}")
            
            # Create a simplified SEC filing object without using the edgar module
            # which has compatibility issues
            download_dir = self.config_manager.get("scraping.download_path", "./downloads")
            os.makedirs(download_dir, exist_ok=True)
            
            # Use a direct URL to SEC EDGAR
            if filing_type == "10-K":
                filing_type_code = "10-K"
            elif filing_type == "10-Q":
                filing_type_code = "10-Q"
            else:
                filing_type_code = filing_type
                
            # Try to fetch directly from SEC.gov search
            base_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type={filing_type_code}&count={count}"
            
            headers = {
                "User-Agent": self.config_manager.get("scraping.user_agent", "Financial Research Assistant/1.0")
            }
            
            try:
                response = requests.get(base_url, headers=headers)
                if response.status_code != 200:
                    self.logger.error(f"Failed to access SEC EDGAR for {ticker}: HTTP {response.status_code}")
                    return []
                    
                # Use BeautifulSoup to parse the response
                soup = BeautifulSoup(response.content, "html.parser")
                
                # Find filing links
                filing_links = []
                for table in soup.find_all("table", {"class": "tableFile2"}):
                    for row in table.find_all("tr"):
                        cells = row.find_all("td")
                        if len(cells) >= 3 and filing_type_code in cells[0].text:
                            # Find the document link
                            for a_tag in row.find_all("a"):
                                if "documentsbutton" in a_tag.get("id", ""):
                                    doc_href = a_tag.get("href")
                                    if doc_href:
                                        filing_links.append(f"https://www.sec.gov{doc_href}")
                                    break
                
                if not filing_links:
                    self.logger.warning(f"No {filing_type} filings found for {ticker} in SEC EDGAR")
                    return []
                
                # Download each filing
                downloaded_files = []
                for i, link in enumerate(filing_links[:count]):
                    try:
                        # Get the filing page
                        filing_page = requests.get(link, headers=headers)
                        if filing_page.status_code != 200:
                            continue
                            
                        filing_soup = BeautifulSoup(filing_page.content, "html.parser")
                        
                        # Find the main filing document (usually the first table entry)
                        main_doc = None
                        table = filing_soup.find("table", {"class": "tableFile"})
                        if table:
                            for row in table.find_all("tr"):
                                cells = row.find_all("td")
                                if len(cells) >= 3:
                                    # Look for the main document
                                    if ".htm" in cells[2].text:
                                        doc_link = cells[2].find("a")
                                        if doc_link and doc_link.get("href"):
                                            main_doc = f"https://www.sec.gov{doc_link.get('href')}"
                                            break
                        
                        if not main_doc:
                            continue
                            
                        # Download the main document
                        doc_response = requests.get(main_doc, headers=headers)
                        if doc_response.status_code == 200:
                            # Generate filename
                            filing_date = datetime.now().strftime("%Y-%m-%d")  # Default date
                            
                            # Try to extract the actual filing date from the page if possible
                            date_div = filing_soup.find("div", {"class": "info"})
                            if date_div:
                                date_text = date_div.text
                                import re
                                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_text)
                                if date_match:
                                    filing_date = date_match.group(1)
                            
                            filename = f"{ticker}_{filing_type}_{filing_date}_{i+1}.html"
                            file_path = os.path.join(download_dir, filename)
                            
                            with open(file_path, "wb") as f:
                                f.write(doc_response.content)
                                
                            self.logger.info(f"Downloaded {filing_type} filing for {ticker} to {file_path}")
                            downloaded_files.append(file_path)
                    except Exception as e:
                        self.logger.error(f"Error downloading filing {i+1} for {ticker}: {e}")
                        continue
                
                return downloaded_files
                
            except Exception as e:
                self.logger.error(f"Error parsing SEC EDGAR page for {ticker}: {e}")
                return []
            
        except Exception as e:
            self.logger.error(f"Error getting SEC filings for {ticker}: {e}")
            return []

    def scrape_nse_company_info(self, ticker):
        """
        Scrape company information from NSE.
        
        Args:
            ticker: NSE ticker symbol
            
        Returns:
            Dictionary with company information
        """
        if not self.config_manager.get("data_sources.nse_data"):
            return {}
            
        try:
            self.logger.info(f"Scraping NSE data for {ticker}")
            
            # Fallback to direct scraping without using nselib API
            driver = self.get_driver()
            if not driver:
                return {}
                
            # Open NSE page
            url = f"https://www.nseindia.com/get-quotes/equity?symbol={ticker}"
            driver.get(url)
            
            # Wait for page to load with a longer timeout and better wait strategy
            wait = WebDriverWait(driver, 20)
            
            # First check if page loaded at all by looking for a more general element
            try:
                wait.until(EC.presence_of_element_located((By.ID, "quoteLtp")))
            except:
                # Try refreshing the page once
                driver.refresh()
                time.sleep(3)
            
            # Extract data - use try/except for each element since page structure might vary
            company_info = {"symbol": ticker}
            
            try:
                price_elem = driver.find_element(By.ID, "quoteLtp")
                company_info["price"] = price_elem.text
            except:
                pass
                
            try:
                # Try different class names that might contain the company name
                for class_name in ["w-75", "companyName", "company-name"]:
                    try:
                        name_elem = driver.find_element(By.CLASS_NAME, class_name)
                        company_info["name"] = name_elem.text
                        break
                    except:
                        continue
            except:
                pass
                
            try:
                change_elem = driver.find_element(By.ID, "priceInfoLtp")
                company_info["change"] = change_elem.text
            except:
                pass
                
            try:
                # Try different ID names that might contain market cap
                for id_name in ["marketValLbl", "marketCap", "market-cap"]:
                    try:
                        cap_elem = driver.find_element(By.ID, id_name)
                        company_info["market_cap"] = cap_elem.text
                        break
                    except:
                        continue
            except:
                pass
            
            # If we got at least some data, return it
            if len(company_info) > 1:
                return company_info
            
            # If we get here, we failed to scrape the NSE page,
            # create a minimal company info object with just the symbol
            return {"symbol": ticker, "name": ticker, "exchange": "NSE"}
            
        except Exception as e:
            self.logger.error(f"Error scraping NSE data for {ticker}: {e}")
            # Return minimal info
            return {"symbol": ticker, "name": ticker, "exchange": "NSE"}
    
    def download_annual_report(self, ticker, exchange="NSE", year=None):
        """
        Download annual reports for a company.
        
        Args:
            ticker: Company ticker symbol
            exchange: Stock exchange (NSE, BSE)
            year: Year of the annual report (None for latest)
            
        Returns:
            Path to the downloaded report or None
        """
        try:
            self.logger.info(f"Downloading annual report for {ticker} ({exchange})")
            
            driver = self.get_driver()
            if not driver:
                return None
                
            if exchange == "NSE":
                # For NSE listed companies, try to get from NSE website
                url = f"https://www.nseindia.com/companies-listing/corporate-filings-financial-results"
                driver.get(url)
                
                # Wait for search box
                wait = WebDriverWait(driver, 10)
                search_box = wait.until(EC.presence_of_element_located((By.ID, "symbol-search")))
                
                # Search for company
                search_box.send_keys(ticker)
                search_box.send_keys(webdriver.Keys.RETURN)
                
                # Wait for results
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "financial-results-table")))
                
                # Find annual report link
                report_links = driver.find_elements(By.XPATH, "//a[contains(text(), 'Annual Report')]")
                
                if report_links:
                    # Get the first (most recent) annual report
                    report_link = report_links[0]
                    report_link.click()
                    
                    # Wait for download (5 seconds)
                    time.sleep(5)
                    
                    # Get the latest file in the download directory
                    download_dir = self.config_manager.get("scraping.download_path")
                    files = [os.path.join(download_dir, f) for f in os.listdir(download_dir) if f.endswith('.pdf')]
                    
                    if files:
                        latest_file = max(files, key=os.path.getmtime)
                        return latest_file
            
            elif exchange == "BSE":
                # For BSE listed companies
                url = f"https://www.bseindia.com/stock-share-price/{ticker}/"
                driver.get(url)
                
                # Similar implementation for BSE...
                pass
            
            # Fallback to screener.in for any exchange
            url = f"https://www.screener.in/company/{ticker}/"
            driver.get(url)
            
            # Wait for page to load
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "company-reports")))
            
            # Find annual report links
            report_links = driver.find_elements(By.XPATH, "//div[@class='company-reports']//a[contains(text(), 'Annual Report')]")
            
            if report_links:
                # Get the first (most recent) annual report
                report_link = report_links[0]
                report_link.click()
                
                # Wait for download (5 seconds)
                time.sleep(5)
                
                # Get the latest file in the download directory
                download_dir = self.config_manager.get("scraping.download_path")
                files = [os.path.join(download_dir, f) for f in os.listdir(download_dir) if f.endswith('.pdf')]
                
                if files:
                    latest_file = max(files, key=os.path.getmtime)
                    return latest_file
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error downloading annual report for {ticker}: {e}")
            return None
    
    def extract_text_from_pdf(self, pdf_path):
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text
        """
        try:
            text = ""
            
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                num_pages = len(reader.pages)
                
                self.logger.info(f"Extracting text from {pdf_path} ({num_pages} pages)")
                
                # Process each page
                for page_num in range(num_pages):
                    page = reader.pages[page_num]
                    page_text = page.extract_text()
                    
                    if page_text:
                        text += page_text
                    else:
                        # If text extraction fails, try OCR if enabled
                        if self.config_manager.get("processing.ocr_enabled", True):
                            self.logger.info(f"Using OCR for page {page_num+1}")
                            
                            # Convert PDF page to image
                            images = pdf2image.convert_from_path(
                                pdf_path, 
                                first_page=page_num+1, 
                                last_page=page_num+1
                            )
                            
                            if images:
                                # OCR the image
                                ocr_text = pytesseract.image_to_string(images[0])
                                text += ocr_text
            
            return text
            
        except Exception as e:
            self.logger.error(f"Error extracting text from PDF: {e}")
            return ""
    
    def __del__(self):
        """Clean up resources.""" 
        self.close_driver()

class YFinanceManager:
    """Handle interactions with the Yahoo Finance API through yfinance.""" 
    
    def __init__(self):
        """Initialize the YFinance manager.""" 
        self.logger = logging.getLogger(__name__)
        self.rate_limiter = RateLimiter()
        # Ensure time module is available
        import time
        self.time = time
        # Initialize yfinance module
        self.yf = yf
    
    @property
    def _rate_limited_get(self):
        """Get a rate-limited version of the ticker data fetching function.""" 
        return self.rate_limiter.with_rate_limit(self._get_ticker_data, "yfinance")
    
    def _get_ticker_data(self, ticker_symbol):
        """
        Fetch data for a ticker symbol directly from yfinance.
        
        Args:
            ticker_symbol: The stock ticker symbol
            
        Returns:
            Dictionary with ticker data or None if failed
        """
        try:
            ticker = self.yf.Ticker(ticker_symbol)
            
            # Get basic info
            info = ticker.info
            
            # Get historical data
            history = ticker.history(period="1y")
            
            # Get additional data if available
            try:
                financials = ticker.financials.to_dict() if hasattr(ticker, 'financials') else {}
            except:
                financials = {}
                
            try:
                balance_sheet = ticker.balance_sheet.to_dict() if hasattr(ticker, 'balance_sheet') else {}
            except:
                balance_sheet = {}
                
            try:
                cash_flow = ticker.cashflow.to_dict() if hasattr(ticker, 'cashflow') else {}
            except:
                cash_flow = {}
                
            try:
                earnings = ticker.earnings.to_dict() if hasattr(ticker, 'earnings') else {}
            except:
                earnings = {}
            
            # Convert pandas DataFrames to dictionaries
            if not history.empty:
                history_dict = history.to_dict('index')
                # Convert index datetime objects to strings
                history_dict = {str(date): values for date, values in history_dict.items()}
            else:
                history_dict = {}
            
            return {
                "info": info,
                "history": history,
                "history_dict": history_dict,
                "financials": financials,
                "balance_sheet": balance_sheet,
                "cash_flow": cash_flow,
                "earnings": earnings
            }
        except Exception as e:
            self.logger.error(f"Error fetching data for {ticker_symbol}: {e}")
            return None
    
    def get_ticker_data(self, ticker_symbol):
        """
        Get data for a ticker symbol with rate limiting.
        
        Args:
            ticker_symbol: The stock ticker symbol
            
        Returns:
            Dictionary with ticker data or None if failed
        """
        return self._rate_limited_get(ticker_symbol)
    
    def calculate_technical_indicators(self, price_data):
        """
        Calculate technical indicators for price data.
        
        Args:
            price_data: Pandas DataFrame with OHLC price data
            
        Returns:
            Dictionary with technical indicators
        """
        if price_data is None or price_data.empty:
            return {
                "indicators": {},
                "summary": {
                    "trend": "NEUTRAL",
                    "momentum": "NEUTRAL",
                    "volatility": "MEDIUM",
                    "trend_strength": "WEAK"
                }
            }
        
        try:
            # Extract price series
            close = price_data['Close'].values
            high = price_data['High'].values
            low = price_data['Low'].values
            volume = price_data['Volume'].values if 'Volume' in price_data else None
            
            # Calculate indicators
            indicators = {}
            
            # Moving Averages
            try:
                indicators['SMA20'] = talib.SMA(close, timeperiod=20)[-1]
                indicators['SMA50'] = talib.SMA(close, timeperiod=50)[-1]
                indicators['SMA200'] = talib.SMA(close, timeperiod=200)[-1]
            except:
                indicators['SMA20'] = None
                indicators['SMA50'] = None
                indicators['SMA200'] = None
            
            # RSI (Relative Strength Index)
            try:
                rsi = talib.RSI(close, timeperiod=14)
                indicators['RSI'] = rsi[-1]
            except:
                indicators['RSI'] = None
            
            # MACD (Moving Average Convergence Divergence)
            try:
                macd, macd_signal, macd_hist = talib.MACD(close)
                indicators['MACD'] = macd[-1]
                indicators['MACD_signal'] = macd_signal[-1]
                indicators['MACD_hist'] = macd_hist[-1]
            except:
                indicators['MACD'] = None
                indicators['MACD_signal'] = None
                indicators['MACD_hist'] = None
            
            # Bollinger Bands
            try:
                upper, middle, lower = talib.BBANDS(close, timeperiod=20)
                indicators['BB_upper'] = upper[-1]
                indicators['BB_middle'] = middle[-1]
                indicators['BB_lower'] = lower[-1]
            except:
                indicators['BB_upper'] = None
                indicators['BB_middle'] = None
                indicators['BB_lower'] = None
            
            # ATR (Average True Range) - Volatility
            try:
                indicators['ATR'] = talib.ATR(high, low, close, timeperiod=14)[-1]
            except:
                indicators['ATR'] = None
            
            # Stochastic Oscillator
            try:
                slowk, slowd = talib.STOCH(high, low, close)
                indicators['Stoch_K'] = slowk[-1]
                indicators['Stoch_D'] = slowd[-1]
            except:
                indicators['Stoch_K'] = None
                indicators['Stoch_D'] = None
            
            # Generate summary
            summary = {}
            
            # Trend
            if (indicators['SMA20'] is not None and indicators['SMA50'] is not None and 
                indicators['SMA200'] is not None and close[-1] is not None):
                if close[-1] > indicators['SMA200'] and indicators['SMA20'] > indicators['SMA50']:
                    summary['trend'] = 'BULLISH'
                elif close[-1] < indicators['SMA200'] and indicators['SMA20'] < indicators['SMA50']:
                    summary['trend'] = 'BEARISH'
                else:
                    summary['trend'] = 'NEUTRAL'
            else:
                summary['trend'] = 'NEUTRAL'
            
            # Momentum
            if indicators['RSI'] is not None:
                rsi = indicators['RSI']
                if rsi > 70:
                    summary['momentum'] = 'OVERBOUGHT'
                elif rsi < 30:
                    summary['momentum'] = 'OVERSOLD'
                elif rsi > 50:
                    summary['momentum'] = 'POSITIVE'
                elif rsi < 50:
                    summary['momentum'] = 'NEGATIVE'
                else:
                    summary['momentum'] = 'NEUTRAL'
            else:
                summary['momentum'] = 'NEUTRAL'
            
            # Volatility
            if indicators['ATR'] is not None and close[-1] is not None:
                atr_percent = (indicators['ATR'] / close[-1]) * 100
                if atr_percent > 3:
                    summary['volatility'] = 'HIGH'
                elif atr_percent < 1:
                    summary['volatility'] = 'LOW'
                else:
                    summary['volatility'] = 'MEDIUM'
            else:
                summary['volatility'] = 'MEDIUM'
            
            # Trend Strength
            if indicators['MACD'] is not None and indicators['MACD_signal'] is not None:
                macd_diff = abs(indicators['MACD'] - indicators['MACD_signal'])
                if macd_diff > 1:
                    summary['trend_strength'] = 'STRONG'
                elif macd_diff < 0.2:
                    summary['trend_strength'] = 'WEAK'
                else:
                    summary['trend_strength'] = 'MODERATE'
            else:
                summary['trend_strength'] = 'WEAK'
            
            return {
                "indicators": {k: float(v) if v is not None else None for k, v in indicators.items()},
                "summary": summary
            }
        except Exception as e:
            self.logger.error(f"Error calculating technical indicators: {e}")
            return {
                "indicators": {},
                "summary": {
                    "trend": "NEUTRAL",
                    "momentum": "NEUTRAL",
                    "volatility": "MEDIUM",
                    "trend_strength": "WEAK"
                }
            }

class NewsAnalyzer:
    """Analyze sentiment of news articles"""
    
    def __init__(self):
        self.sentiment_analyzer = None
        try:
            logger.info("Initializing sentiment analyzer...")
            from transformers import pipeline
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="ProsusAI/finbert",
                tokenizer="ProsusAI/finbert"
            )
            logger.info("Initialized FinBERT sentiment analyzer")
        except Exception as e:
            logger.error(f"Error initializing sentiment analyzer: {e}", exc_info=True)
            # Create a simplified fallback analyzer
            self.text_processor = TextProcessor()

    def analyze_news(self, news_items):
        """Analyze news sentiment"""
        if not news_items:
            return []
            
        logger.info(f"Analyzing {len(news_items)} news items")
        results = []
        
        for idx, item in enumerate(news_items):
            try:
                title = item.get('headline', '') or item.get('title', '')
                if not title:
                    continue

                # Get sentiment
                sentiment_score = 0
                sentiment_label = 'NEUTRAL'
                
                if self.sentiment_analyzer:
                    sentiment = self.sentiment_analyzer(title)[0]
                    
                    # Map FinBERT labels
                    label_mapping = {
                        'positive': 'POSITIVE',
                        'negative': 'NEGATIVE',
                        'neutral': 'NEUTRAL'
                    }
                    
                    sentiment_label = label_mapping.get(sentiment['label'], 'NEUTRAL')
                    sentiment_score = float(sentiment['score'])
                    
                    # For negative sentiment, convert score to negative range
                    if sentiment['label'] == 'negative':
                        sentiment_score = -sentiment_score
                else:
                    # Fallback to TextProcessor's analyze_sentiment
                    sentiment_score = self.text_processor.analyze_sentiment(title)
                    if sentiment_score > 0.2:
                        sentiment_label = 'POSITIVE'
                    elif sentiment_score < -0.2:
                        sentiment_label = 'NEGATIVE'
                    else:
                        sentiment_label = 'NEUTRAL'
                
                processed_article = {
                    'headline': title,
                    'link': item.get('link', ''),
                    'date': item.get('date', None),
                    'time': item.get('time', None),
                    'summary': item.get('summary', '') or item.get('desc', ''),
                    'publisher': item.get('publisher', '') or item.get('media', ''),
                    'sentiment_score': sentiment_score,
                    'sentiment': sentiment_label
                }
                results.append(processed_article)
                logger.info(f"Article {idx + 1}: {title[:30]}... Score: {sentiment_score:.2f} ({sentiment_label})")
            
            except Exception as e:
                logger.error(f"Error processing news item {idx}: {str(e)}")
                continue
        
        logger.info(f"Successfully analyzed {len(results)} out of {len(news_items)} articles")
        return results

    def get_aggregate_sentiment(self, analyzed_news):
        """Calculate aggregate sentiment metrics"""
        if not analyzed_news:
            return {
                'average_score': 0.0,
                'sentiment_volatility': 0.0,
                'positive_ratio': 0.0,
                'negative_ratio': 0.0,
                'sentiment_trend': 'NEUTRAL'
            }
            
        try:
            import numpy as np
            scores = [item.get('sentiment_score', 0.0) for item in analyzed_news]
            labels = [item.get('sentiment', 'NEUTRAL') for item in analyzed_news]
            
            total = len(labels)
            pos_count = sum(1 for l in labels if l == 'POSITIVE')
            neg_count = sum(1 for l in labels if l == 'NEGATIVE')
            
            return {
                'average_score': float(np.mean(scores)) if scores else 0.0,
                'sentiment_volatility': float(np.std(scores)) if scores else 0.0,
                'positive_ratio': pos_count / total if total > 0 else 0.0,
                'negative_ratio': neg_count / total if total > 0 else 0.0,
                'sentiment_trend': 'NEUTRAL'
            }
        except Exception as e:
            logger.error(f"Error calculating aggregate sentiment: {e}")
            return {
                'average_score': 0.0,
                'sentiment_volatility': 0.0,
                'positive_ratio': 0.0,
                'negative_ratio': 0.0,
                'sentiment_trend': 'NEUTRAL'
            }

class GroqAnalyzer:
    """Analyze company data using GROQ AI models"""
    
    def __init__(self, api_key=None):
        self.client = None
        if GROQ_AVAILABLE and api_key:
            try:
                self.client = Groq(api_key=api_key)
                logger.info("Initialized GROQ analyzer successfully")
            except Exception as e:
                logger.error(f"Error initializing GROQ client: {e}")
        
    def analyze_company_fundamentals(self, company_info, ratios, tech_indicators):
        """Analyze company fundamentals"""
        if not self.client:
            return "GROQ analysis unavailable"
            
        prompt = f"""
        As a financial analyst, analyze this company data:
        
        Company: {company_info.get('name', '')}
        Sector: {company_info.get('sector', '')}
        
        Key Ratios:
        - P/E (TTM): {ratios.get('trailingPE')}
        - Forward P/E: {ratios.get('forwardPE')}
        - P/B: {ratios.get('priceToBook')}
        
        Technical Indicators Summary:
        - RSI: {tech_indicators.get('summary', {}).get('momentum')}
        - Trend Strength: {tech_indicators.get('summary', {}).get('trend_strength')}
        - Volatility: {tech_indicators.get('summary', {}).get('volatility')}
        
        Provide a concise analysis of the company's valuation, momentum, and overall market position.
        Include specific insights about whether the stock appears overvalued or undervalued,
        and what the technical indicators suggest about near-term price movement.
        """
        
        try:
            completion = self.client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "user", "content": prompt}]
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Error in GROQ analysis: {e}")
            return f"Analysis unavailable due to error: {str(e)}"

    def analyze_news_impact(self, company_name, news_items, sentiment_scores):
        """Analyze news impact"""
        if not self.client:
            return "GROQ analysis unavailable"
            
        news_summary = "\n".join([f"- {item['title']}" for item in news_items[:5]])
        
        prompt = f"""
        Analyze the recent news and sentiment for {company_name}:
        
        Recent News:
        {news_summary}
        
        Sentiment Metrics:
        - Average Score: {sentiment_scores.get('average_score')}
        - Volatility: {sentiment_scores.get('sentiment_volatility')}
        - Positive Ratio: {sentiment_scores.get('positive_ratio')}
        
        Provide a concise analysis of:
        1. The key themes in recent news
        2. The potential impact on stock price
        3. Any significant risks or opportunities indicated
        """
        
        try:
            completion = self.client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "user", "content": prompt}]
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Error in GROQ news analysis: {e}")
            return f"News impact analysis unavailable due to error: {str(e)}"

    def generate_investment_thesis(self, company_analysis, news_impact, peer_comparison):
        """Generate comprehensive investment thesis"""
        if not self.client:
            return "GROQ analysis unavailable"
            
        prompt = f"""
        Based on the following analyses, generate a comprehensive investment thesis:
        
        Fundamental Analysis:
        {company_analysis}
        
        News & Sentiment Analysis:
        {news_impact}
        
        Peer Comparison:
        {peer_comparison}
        
        Provide:
        1. Investment recommendation (Buy/Hold/Sell)
        2. Key supporting factors
        3. Main risks to consider
        4. 6-month price outlook
        """
        
        try:
            completion = self.client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "user", "content": prompt}]
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating investment thesis: {e}")
            return f"Investment thesis unavailable due to error: {str(e)}"

class FinancialDataETL:
    """Process financial data from various sources and load it into a knowledge graph.""" 
    
    def __init__(self, config_file="config.json"):
        """Initialize the ETL pipeline components.""" 
        self.config_manager = ConfigManager(config_file)
        self.data_cache = DataCache()
        self.rate_limiter = RateLimiter()
        self.yfinance_manager = YFinanceManager()
        self.document_scraper = DocumentScraper(self.config_manager)
        self.text_processor = TextProcessor()
        self.news_analyzer = NewsAnalyzer()
        self.neo4j = None
        
        # Initialize GROQ analyzer if API key is available
        groq_api_key = self.config_manager.get("api_keys.groq")
        self.groq_analyzer = GroqAnalyzer(api_key=groq_api_key) if groq_api_key else None
        
        # Initialize Neo4j if config is available - with graceful failure
        try:
            neo4j_config = self.config_manager.get_neo4j_credentials()
            if neo4j_config and all(neo4j_config.values()):
                self.connect_to_neo4j(
                    neo4j_config["uri"],
                    neo4j_config["user"],
                    neo4j_config["password"]
                )
                if not self.neo4j or not self.neo4j.verify_connection():
                    logger.warning("Neo4j connection failed - continuing without graph database")
                    self.neo4j = None
            else:
                logger.info("Neo4j configuration incomplete - continuing without graph database")
        except Exception as e:
            logger.warning(f"Neo4j initialization skipped: {e} - continuing without graph database")
            self.neo4j = None
        
        # Initialize Indian IR scraper
        self.ir_scraper = IndianIRScraper()

    def connect_to_neo4j(self, uri, user, password):
        """Establish connection to Neo4j database.""" 
        try:
            self.neo4j = Neo4jDatabase(uri, user, password)
            if not self.neo4j.verify_connection():
                logger.error("Failed to connect to Neo4j database")
                self.neo4j = None
            return self.neo4j is not None
        except Exception as e:
            logger.error(f"Error connecting to Neo4j: {e}")
            return False

    def get_company_news(self, ticker):
        """Get recent news for a company.""" 
        try:
            if not self.config_manager.get("data_sources.news"):
                return []
                
            # Check cache first
            cached_news = self.data_cache.get(ticker, "news")
            if cached_news:
                return cached_news
            
            # Use GoogleNews to get news
            googlenews = GoogleNews(lang='en', period='7d')
            googlenews.search(ticker)
            news_items = googlenews.result()
            
            # Process news items
            processed_news = []
            for item in news_items:
                try:
                    # Extract data
                    news = {
                        'headline': item.get('title', ''),
                        'link': item.get('link', ''),
                        'date': item.get('date', None),
                        'time': item.get('time', None),
                        'summary': item.get('desc', ''),
                        'publisher': item.get('media', '')
                    }
                    
                    processed_news.append(news)
                except Exception as e:
                    logger.error(f"Error processing news item: {e}")
                    continue
            
            # Use advanced sentiment analysis if available
            if self.news_analyzer and self.news_analyzer.sentiment_analyzer:
                analyzed_news = self.news_analyzer.analyze_news(processed_news)
                for i, news in enumerate(processed_news):
                    if i < len(analyzed_news):
                        news['sentiment_score'] = analyzed_news[i].get('sentiment_score', 0.0)
                        news['sentiment'] = analyzed_news[i].get('sentiment', 'NEUTRAL')
            else:
                # Fallback to basic sentiment analysis
                for news in processed_news:
                    if news['headline']:
                        news['sentiment'] = self.text_processor.analyze_sentiment(news['headline'])
                    else:
                        news['sentiment'] = 0.0
            
            # Cache the results
            if processed_news:
                self.data_cache.save(ticker, "news", processed_news)
                
            return processed_news
            
        except Exception as e:
            logger.error(f"Error getting news for {ticker}: {e}")
            return []

    def generate_investment_thesis(self, ticker):
        """Generate comprehensive investment thesis for a ticker.""" 
        if not self.groq_analyzer or not self.groq_analyzer.client:
            logger.warning("GROQ analyzer not available for generating investment thesis")
            return None
            
        try:
            # Get company info
            company_data = self.get_company_info(ticker)
            if not company_data or not company_data.get("info"):
                logger.error(f"Failed to get company info for {ticker}")
                return None
                
            company_info = company_data["info"]
            
            # Get technical indicators
            stock_data = company_data.get("history")
            if stock_data is None or stock_data.empty:
                logger.error(f"Failed to get historical data for {ticker}")
                return None
                
            indicators = self.calculate_technical_indicators(stock_data)
            
            # Get company news
            news = self.get_company_news(ticker)
            sentiment_scores = self.news_analyzer.get_aggregate_sentiment(news) if self.news_analyzer else {}
            
            # Get peer comparison
            sector = company_info.get("sector", "Unknown")
            peer_comparison = f"Comparing with peers in {sector} sector"
            
            # Generate analysis components
            company_analysis = self.groq_analyzer.analyze_company_fundamentals(
                company_info,
                company_info,  # Use company_info as a proxy for ratios
                indicators
            )
            
            news_impact = self.groq_analyzer.analyze_news_impact(
                company_info.get('shortName', ticker),
                news,
                sentiment_scores
            )
            
            # Generate investment thesis
            thesis = self.groq_analyzer.generate_investment_thesis(
                company_analysis,
                news_impact,
                peer_comparison
            )
            
            # Store analysis if Neo4j is available
            if self.neo4j:
                analysis_data = {
                    'fundamental_analysis': company_analysis,
                    'news_impact': news_impact,
                    'investment_thesis': thesis,
                    'timestamp': datetime.now().isoformat()
                }
                self.neo4j.store_analysis(ticker, analysis_data)
            
            return {
                'ticker': ticker,
                'company_name': company_info.get('shortName', ticker),
                'fundamental_analysis': company_analysis,
                'news_impact': news_impact,
                'investment_thesis': thesis,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating investment thesis for {ticker}: {e}")
            return None

    def process_company(self, ticker, exchange=None):
        """
        Process a single company's data.
        
        Args:
            ticker: The stock ticker symbol
            exchange: Optional stock exchange (NYSE, NASDAQ, NSE, BSE)
            
        Returns:
            Boolean indicating success or failure
        """
        try:
            logger.info(f"Processing company {ticker} on {exchange if exchange else 'default exchange'}")
            
            # Adjust ticker format for Indian exchanges
            yf_ticker = ticker
            if exchange == "NSE":
                yf_ticker = f"{ticker}.NS"
            elif exchange == "BSE":
                yf_ticker = f"{ticker}.BO"
            
            # For Indian companies, scrape IR website first
            if exchange in ["NSE", "BSE"]:
                logger.info(f"Scraping IR documents for {ticker}")
                ir_documents = self.ir_scraper.scrape_ir_documents(ticker, exchange_code=ticker)
                
                if ir_documents:
                    logger.info(f"Found {sum(len(docs) for docs in ir_documents.values())} IR documents")
                    
                    # Process concall transcripts
                    for transcript in ir_documents.get('concall_transcript', []):
                        transcript_data = self.ir_scraper.extract_concall_text(transcript['filepath'])
                        if transcript_data:
                            # Store transcript in Neo4j
                            if self.neo4j:
                                self.neo4j.store_transcript(ticker, transcript_data)
                    
                    # Store other documents
                    if self.neo4j:
                        for doc_type, docs in ir_documents.items():
                            if doc_type != 'concall_transcript':  # Already processed above
                                for doc in docs:
                                    self.neo4j.store_document(ticker, doc)
            
            # Get company information from Yahoo Finance
            logger.info(f"Fetching data for {yf_ticker} from Yahoo Finance")
            ticker_data = self.yfinance_manager.get_ticker_data(yf_ticker)
            
            if not ticker_data or not ticker_data.get("info"):
                logger.error(f"Failed to get data for {yf_ticker} from Yahoo Finance")
                return False
                
            # Cache the data
            self.data_cache.save(ticker, "yfinance", ticker_data)
            logger.info(f"Cached Yahoo Finance data for {ticker}")
            
            # Calculate technical indicators
            logger.info(f"Calculating technical indicators for {ticker}")
            price_history = ticker_data.get("history")
            if price_history is not None and not price_history.empty:
                technical_indicators = self.yfinance_manager.calculate_technical_indicators(price_history)
                self.data_cache.save(ticker, "technical_indicators", technical_indicators)
                logger.info(f"Technical analysis for {ticker}: {technical_indicators['summary']}")
            else:
                logger.warning(f"No price history available for {ticker}, skipping technical analysis")
            
            # Get news articles
            logger.info(f"Fetching news for {ticker}")
            news = self.get_company_news(ticker)
            if news:
                logger.info(f"Found {len(news)} news articles for {ticker}")
                
                # Analyze sentiment if news analyzer is available
                if self.news_analyzer and hasattr(self.news_analyzer, "analyze_news"):
                    logger.info(f"Analyzing news sentiment for {ticker}")
                    analyzed_news = self.news_analyzer.analyze_news(news)
                    
                    # Generate aggregate sentiment metrics
                    if hasattr(self.news_analyzer, "get_aggregate_sentiment"):
                        sentiment_metrics = self.news_analyzer.get_aggregate_sentiment(analyzed_news)
                        logger.info(f"News sentiment for {ticker}: {sentiment_metrics}")
            else:
                logger.warning(f"No news found for {ticker}")
            
            # Store data in Neo4j if available
            if self.neo4j:
                logger.info(f"Storing data for {ticker} in Neo4j")
                
                # Create company node
                company_info = ticker_data.get("info", {})
                company_node = {
                    "symbol": ticker,
                    "name": company_info.get("shortName", ""),
                    "sector": company_info.get("sector", ""),
                    "industry": company_info.get("industry", ""),
                    "country": company_info.get("country", ""),
                    "exchange": exchange or company_info.get("exchange", ""),
                    "market_cap": company_info.get("marketCap", 0),
                    "beta": company_info.get("beta", 0),
                    "pe_ratio": company_info.get("trailingPE", 0),
                    "dividend_yield": company_info.get("dividendYield", 0),
                    "last_updated": datetime.now().isoformat()
                }
                
                self.neo4j.create_company_node(ticker, company_node)
                
                # Store price history
                if price_history is not None and not price_history.empty:
                    self.neo4j.create_stock_data_nodes(ticker, price_history)
                
                # Store technical indicators
                if technical_indicators:
                    self.neo4j.store_technical_indicators(ticker, technical_indicators)
                
                # Store news and sentiment
                if news:
                    self.neo4j.store_news(ticker, news)
            
            logger.info(f"Successfully processed data for {ticker}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing company {ticker}: {e}")
            return False

class FinancialETLPipeline:
    """High-level pipeline for running the financial data ETL process.""" 
    
    def __init__(self, config_file="config.json"):
        """Initialize the ETL pipeline.""" 
        self.etl = FinancialDataETL(config_file)
        self.logger = logging.getLogger(__name__)
    
    def verify_connections(self):
        """Verify all necessary connections.""" 
        results = {
            "neo4j": False,
            "yfinance": False,
            "edgar": False
        }
        
        # Check Neo4j
        if self.etl.neo4j and self.etl.neo4j.verify_connection():
            results["neo4j"] = True
        
        # Check YFinance connection
        try:
            test_ticker = "AAPL"
            data = self.etl.yfinance_manager.get_ticker_data(test_ticker)
            results["yfinance"] = data is not None and "info" in data
        except:
            pass
        
        # Check EDGAR API
        try:
            company = Company("AAPL")
            results["edgar"] = company is not None
        except:
            pass
        
        return results
    
    def process_tickers_from_file(self, ticker_file, exchange=None):
        """Process a list of tickers from a file.""" 
        try:
            # Read tickers from file
            with open(ticker_file, 'r') as f:
                tickers = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            self.logger.info(f"Processing {len(tickers)} tickers from {ticker_file}")
            
            # Use async processing
            import asyncio
            results = asyncio.run(self.etl.run_batch_process(tickers, exchange))
            
            return results
        except Exception as e:
            self.logger.error(f"Error processing tickers from file {ticker_file}: {e}")
            return {"success": 0, "failure": 0, "error": str(e)}
    
    def process_sectors_from_file(self, sectors_file):
        """Process sectors and companies from a JSON file.""" 
        try:
            # Read sectors data
            with open(sectors_file, 'r') as f:
                sectors_data = json.load(f)
            
            self.logger.info(f"Processing {len(sectors_data)} sectors from {sectors_file}")
            
            # Run sector analysis
            results = self.etl.run_sector_analysis(sectors_data)
            
            return results
        except Exception as e:
            self.logger.error(f"Error processing sectors from file {sectors_file}: {e}")
            return {"sectors_processed": 0, "companies_processed": 0, "failures": 0, "error": str(e)}

def run_cli():
    """Run the command-line interface for the ETL pipeline.""" 
    import argparse
    
    parser = argparse.ArgumentParser(description="Financial Data ETL Pipeline")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Verify connections
    verify_parser = subparsers.add_parser("verify", help="Verify connections to data sources")
    
    # Process a single company
    company_parser = subparsers.add_parser("company", help="Process a single company")
    company_parser.add_argument("ticker", help="Company ticker symbol")
    company_parser.add_argument("--exchange", help="Stock exchange (NYSE, NASDAQ, NSE, BSE)")
    
    # Process a sector
    sector_parser = subparsers.add_parser("sector", help="Process a sector with multiple companies")
    sector_parser.add_argument("sector", help="Sector name")
    sector_parser.add_argument("--tickers", nargs="+", help="List of ticker symbols")
    
    # Process a batch from file
    batch_parser = subparsers.add_parser("batch", help="Process a batch of companies from a file")
    batch_parser.add_argument("file", help="File containing ticker symbols")
    batch_parser.add_argument("--exchange", help="Stock exchange (NYSE, NASDAQ, NSE, BSE)")
    
    # Process sectors from file
    sectors_parser = subparsers.add_parser("sectors", help="Process sectors from a JSON file")
    sectors_parser.add_argument("file", help="JSON file containing sector data")
    
    # Configuration management
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_parser.add_argument("action", choices=["show", "set", "reset"], help="Configuration action")
    config_parser.add_argument("--key", help="Configuration key (e.g., neo4j.uri)")
    config_parser.add_argument("--value", help="Configuration value")
    
    args = parser.parse_args()
    
    # Create pipeline
    pipeline = FinancialETLPipeline()
    
    # Handle commands
    if args.command == "verify":
        results = pipeline.verify_connections()
        for source, status in results.items():
            print(f"{source}: {'Connected' if status else 'Not connected'}")
            
    elif args.command == "company":
        success = pipeline.etl.process_company(args.ticker, args.exchange)
        print(f"Company processing {'succeeded' if success else 'failed'}")
        
    elif args.command == "sector":
        if not args.tickers:
            print("Error: Must provide --tickers")
            return
            
        sector_data = {args.sector: args.tickers}
        results = pipeline.etl.run_sector_analysis(sector_data)
        print(f"Processed {results['companies_processed']} companies with {results['failures']} failures")
        
    elif args.command == "batch":
        results = pipeline.process_tickers_from_file(args.file, args.exchange)
        print(f"Processed {results['success']} tickers with {results['failure']} failures")
        
    elif args.command == "sectors":
        results = pipeline.process_sectors_from_file(args.file)
        print(f"Processed {results['sectors_processed']} sectors with {results['companies_processed']} companies and {results['failures']} failures")
        
    elif args.command == "config":
        config_manager = pipeline.etl.config_manager
        
        if args.action == "show":
            import pprint
            pprint.pprint(config_manager.config)
            
        elif args.action == "set":
            if not args.key or args.value is None:
                print("Error: Must provide --key and --value")
                return
                
            success = config_manager.set(args.key, args.value)
            if success:
                print(f"Set {args.key} to {args.value}")
                config_manager.save_config("config.json")
            else:
                print(f"Failed to set {args.key}")
                
        elif args.action == "reset":
            config_manager = ConfigManager()
            config_manager.save_config("config.json")
            print("Reset configuration to defaults")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    run_cli()