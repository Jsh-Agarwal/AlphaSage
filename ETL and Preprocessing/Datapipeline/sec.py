import requests
import time
import xml.etree.ElementTree as ET
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class SECFilingFetcher:
    """Class to fetch SEC filings for companies."""
    
    def __init__(self, user_agent=None):
        """
        Initialize the SEC filing fetcher.
        
        Parameters:
            user_agent (str): Your user agent string for SEC API (email required)
        """
        self.user_agent = user_agent or os.getenv("SEC_USER_AGENT", "Sample Company Name sample@email.com")
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept-Encoding": "gzip, deflate",
            "Host": "www.sec.gov"
        }
        self.download_dir = "downloads"
        os.makedirs(self.download_dir, exist_ok=True)
        
        # Rate limiting settings
        self.request_delay = 0.1  # 100ms between requests as per SEC guidelines
        self.last_request_time = 0
    
    def _respect_rate_limit(self):
        """Ensure we respect SEC's rate limiting guidelines."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.request_delay:
            time.sleep(self.request_delay - time_since_last_request)
        
        self.last_request_time = time.time()
    
    def _make_request(self, url, params=None):
        """Make a rate-limited request to SEC."""
        self._respect_rate_limit()
        
        try:
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 429:
                logger.warning("SEC rate limit exceeded, waiting 10 seconds...")
                time.sleep(10)
                return self._make_request(url, params)
                
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to SEC: {e}")
            return None
    
    def get_cik_from_ticker(self, ticker):
        """
        Fetches the SEC CIK for a given stock ticker symbol.

        Parameters:
            ticker (str): Stock ticker symbol (e.g., 'AAPL', 'GOOG').

        Returns:
            str: The CIK number if found, else None.
        """
        ticker = ticker.upper()
        url = "https://www.sec.gov/files/company_tickers.json"

        try:
            response = self._make_request(url)
            if response and response.status_code == 200:
                data = response.json()
                for item in data.values():
                    if item["ticker"].upper() == ticker:
                        cik_str = str(item["cik_str"]).zfill(10)
                        logger.info(f"Found CIK {cik_str} for ticker {ticker}")
                        return cik_str
                logger.warning(f"Ticker {ticker} not found in SEC database")
                return None
            else:
                logger.error(f"Failed to fetch data from SEC: Status {response.status_code if response else 'No response'}")
                return None
        except Exception as e:
            logger.error(f"Error fetching CIK for {ticker}: {e}")
            return None

    def get_company_filings(self, cik, form_type="10-K", limit=10):
        """
        Get recent SEC filings for a company.
        
        Parameters:
            cik (str): The CIK number of the company
            form_type (str): The type of form to fetch (e.g., "10-K", "10-Q")
            limit (int): Maximum number of filings to return
            
        Returns:
            list: List of filing information dictionaries
        """
        cik_formatted = str(cik).zfill(10)
        url = f"https://data.sec.gov/submissions/CIK{cik_formatted}.json"

        try:
            response = self._make_request(url)
            if response and response.status_code == 200:
                data = response.json()
                filings = []

                recent_forms = data.get('filings', {}).get('recent', {})
                if not recent_forms:
                    logger.warning(f"No recent filings found for CIK {cik}")
                    return None
                    
                form_types = recent_forms.get('form', [])
                filing_dates = recent_forms.get('filingDate', [])
                accession_numbers = recent_forms.get('accessionNumber', [])
                primary_documents = recent_forms.get('primaryDocument', [])
                
                count = 0
                for i, form in enumerate(form_types):
                    if form == form_type and count < limit:
                        filing_info = {
                            'form': form,
                            'filingDate': filing_dates[i],
                            'accessionNumber': accession_numbers[i].replace('-', ''),
                            'primaryDocument': primary_documents[i],
                        }
                        filings.append(filing_info)
                        count += 1
                        
                logger.info(f"Retrieved {len(filings)} {form_type} filings for CIK {cik}")
                return filings
            else:
                logger.error(f"Error fetching filings: {response.status_code if response else 'No response'}")
                return None
        except Exception as e:
            logger.error(f"Error fetching company filings for CIK {cik}: {e}")
            return None

    def download_filing(self, cik, accession_number, primary_document, output_dir=None):
        """
        Download an SEC filing document.
        
        Parameters:
            cik (str): The CIK number of the company
            accession_number (str): The accession number of the filing
            primary_document (str): The primary document filename
            output_dir (str): Directory to save the filing (defaults to "downloads")
            
        Returns:
            str: Path to the downloaded file, or None if download failed
        """
        if output_dir is None:
            output_dir = self.download_dir
            
        os.makedirs(output_dir, exist_ok=True)
        
        url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number}/{primary_document}"

        try:
            response = self._make_request(url)
            if response and response.status_code == 200:
                # Create a file name with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_name = f"{cik}_{accession_number}_{timestamp}.html"
                file_path = os.path.join(output_dir, file_name)

                # Save the file
                with open(file_path, 'wb') as f:
                    f.write(response.content)

                logger.info(f"Downloaded filing to {file_path}")
                return file_path
            else:
                logger.error(f"Error downloading filing: {response.status_code if response else 'No response'}")
                return None
        except Exception as e:
            logger.error(f"Error downloading filing for CIK {cik}: {e}")
            return None
    
    def get_company_facts(self, cik):
        """
        Get company facts from the SEC API.
        
        Parameters:
            cik (str): The CIK number of the company
            
        Returns:
            dict: Company facts data
        """
        cik_formatted = str(cik).zfill(10)
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_formatted}.json"

        try:
            response = self._make_request(url)
            if response and response.status_code == 200:
                facts = response.json()
                logger.info(f"Retrieved company facts for CIK {cik}")
                return facts
            else:
                logger.error(f"Error fetching company facts: {response.status_code if response else 'No response'}")
                return None
        except Exception as e:
            logger.error(f"Error fetching company facts for CIK {cik}: {e}")
            return None
    
    def get_company_concept(self, cik, concept, taxonomy="us-gaap"):
        """
        Get a specific financial concept for a company.
        
        Parameters:
            cik (str): The CIK number of the company
            concept (str): The financial concept (e.g., "RevenueFromContractWithCustomerExcludingAssessedTax")
            taxonomy (str): The taxonomy to use (default: "us-gaap")
            
        Returns:
            dict: Concept data
        """
        cik_formatted = str(cik).zfill(10)
        url = f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik_formatted}/{taxonomy}/{concept}.json"

        try:
            response = self._make_request(url)
            if response and response.status_code == 200:
                concept_data = response.json()
                logger.info(f"Retrieved {concept} data for CIK {cik}")
                return concept_data
            else:
                logger.error(f"Error fetching company concept: {response.status_code if response else 'No response'}")
                return None
        except Exception as e:
            logger.error(f"Error fetching company concept for CIK {cik}: {e}")
            return None

# Maintain the original functions for backward compatibility
def get_cik_from_ticker(ticker):
    fetcher = SECFilingFetcher()
    return fetcher.get_cik_from_ticker(ticker)

def get_company_filings(cik, form_type="10-Q"):
    fetcher = SECFilingFetcher()
    return fetcher.get_company_filings(cik, form_type)

def download_filing(cik, accession_number, primary_document):
    fetcher = SECFilingFetcher()
    return fetcher.download_filing(cik, accession_number, primary_document)

# Main execution
def main():
    """CLI interface for SEC filing functions."""
    import argparse
    
    parser = argparse.ArgumentParser(description="SEC Filing ETL Tool")
    parser.add_argument("--ticker", help="Stock ticker symbol")
    parser.add_argument("--cik", help="Company CIK number (if known)")
    parser.add_argument("--form-type", default="10-K", help="SEC form type (default: 10-K)")
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of filings to retrieve")
    parser.add_argument("--output-dir", default="downloads", help="Directory to save downloaded filings")
    parser.add_argument("--user-agent", help="User agent string with email for SEC API")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    fetcher = SECFilingFetcher(user_agent=args.user_agent)
    
    if not args.cik and not args.ticker:
        print("Error: Either --ticker or --cik must be provided")
        return
    
    # Get CIK if ticker is provided
    cik = args.cik
    if not cik and args.ticker:
        print(f"Looking up CIK for {args.ticker}...")
        cik = fetcher.get_cik_from_ticker(args.ticker)
    
    if not cik:
        print("Could not find valid CIK")
        return
    
    # Get filings
    print(f"Retrieving {args.form_type} filings for CIK {cik}...")
    filings = fetcher.get_company_filings(cik, form_type=args.form_type, limit=args.limit)
    
    if not filings:
        print(f"No {args.form_type} filings found")
        return
    
    print(f"Found {len(filings)} {args.form_type} filings:")
    for i, filing in enumerate(filings):
        print(f"{i+1}. Filing Date: {filing['filingDate']}, Accession: {filing['accessionNumber']}")
    
    # Ask which filing to download
    download_option = input("Enter filing number to download (or 'all' for all filings): ")
    
    if download_option.lower() == 'all':
        for filing in filings:
            fetcher.download_filing(
                cik,
                filing['accessionNumber'],
                filing['primaryDocument'],
                output_dir=args.output_dir
            )
    elif download_option.isdigit() and 1 <= int(download_option) <= len(filings):
        selected = filings[int(download_option) - 1]
        fetcher.download_filing(
            cik,
            selected['accessionNumber'],
            selected['primaryDocument'],
            output_dir=args.output_dir
        )
    else:
        print("Invalid option. No files downloaded.")

if __name__ == "__main__":
    main()