import re
import logging
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import numpy as np
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextProcessor:
    """Process text documents for embedding and knowledge graph storage."""
    
    def __init__(self):
        """Initialize the text processor with required models."""
        self.sentiment_analyzer = None
        
        # Initialize nltk resources if needed
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            logger.info("Downloading NLTK punkt tokenizer")
            nltk.download('punkt', quiet=True)
            
        try:
            nltk.data.find('sentiment/vader_lexicon.zip')
        except LookupError:
            logger.info("Downloading NLTK vader lexicon")
            nltk.download('vader_lexicon', quiet=True)
            
        try:
            self.sentiment_analyzer = SentimentIntensityAnalyzer()
            logger.info("Initialized NLTK sentiment analyzer")
        except Exception as e:
            logger.error(f"Error initializing sentiment analyzer: {e}")
    
    def clean_text(self, text):
        """Clean and normalize text."""
        if not text:
            return ""
            
        # Replace special characters and extra whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s.,;:!?()-]', '', text)
        
        return text.strip()
    
    def extract_sentences(self, text):
        """Extract sentences from text."""
        if not text:
            return []
            
        try:
            return sent_tokenize(text)
        except Exception as e:
            logger.error(f"Error extracting sentences: {e}")
            # Fallback to simple period splitting
            return [s.strip() for s in text.split('.') if s.strip()]
    
    def tokenize(self, text):
        """Tokenize text into words."""
        if not text:
            return []
            
        try:
            return word_tokenize(text)
        except Exception as e:
            logger.error(f"Error tokenizing text: {e}")
            # Fallback to simple space splitting
            return [w for w in text.split() if w]
    
    def analyze_sentiment(self, text):
        """Analyze sentiment of text."""
        if not text or not self.sentiment_analyzer:
            return 0.0
            
        try:
            scores = self.sentiment_analyzer.polarity_scores(text)
            return scores['compound']  # Return compound score between -1 and 1
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return 0.0
    
    def extract_financial_metrics(self, text):
        """Extract financial metrics from text."""
        metrics = {
            'revenue': None,
            'profit': None,
            'eps': None,
            'pe_ratio': None,
            'dividend': None,
            'growth': None
        }
        
        if not text:
            return metrics
            
        try:
            # Revenue pattern
            revenue_pattern = r'revenue of (?:Rs\.|₹|USD|$)?\s?(\d+(?:\.\d+)?)\s?(billion|million|crore|lakh|thousand)?'
            revenue_match = re.search(revenue_pattern, text, re.IGNORECASE)
            if revenue_match:
                value = float(revenue_match.group(1))
                unit = revenue_match.group(2)
                
                # Normalize to millions
                if unit:
                    unit = unit.lower()
                    if unit == 'billion':
                        value *= 1000
                    elif unit == 'crore':
                        value *= 10
                    elif unit == 'lakh':
                        value *= 0.1
                    elif unit == 'thousand':
                        value *= 0.001
                
                metrics['revenue'] = value
                
            # Profit pattern
            profit_pattern = r'(?:net profit|profit after tax|PAT) of (?:Rs\.|₹|USD|$)?\s?(\d+(?:\.\d+)?)\s?(billion|million|crore|lakh|thousand)?'
            profit_match = re.search(profit_pattern, text, re.IGNORECASE)
            if profit_match:
                value = float(profit_match.group(1))
                unit = profit_match.group(2)
                
                # Normalize to millions
                if unit:
                    unit = unit.lower()
                    if unit == 'billion':
                        value *= 1000
                    elif unit == 'crore':
                        value *= 10
                    elif unit == 'lakh':
                        value *= 0.1
                    elif unit == 'thousand':
                        value *= 0.001
                
                metrics['profit'] = value
                
            # EPS pattern
            eps_pattern = r'EPS of (?:Rs\.|₹|USD|$)?\s?(\d+(?:\.\d+)?)'
            eps_match = re.search(eps_pattern, text, re.IGNORECASE)
            if eps_match:
                metrics['eps'] = float(eps_match.group(1))
                
            # Growth pattern
            growth_pattern = r'(?:growth|increase|up) of (\d+(?:\.\d+)?)%'
            growth_match = re.search(growth_pattern, text, re.IGNORECASE)
            if growth_match:
                metrics['growth'] = float(growth_match.group(1))
                
            return metrics
            
        except Exception as e:
            logger.error(f"Error extracting financial metrics: {e}")
            return metrics
    
    def extract_dates(self, text):
        """Extract dates from text."""
        dates = []
        
        if not text:
            return dates
            
        try:
            # Various date patterns
            patterns = [
                r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',  # DD/MM/YYYY or DD-MM-YYYY
                r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY/MM/DD or YYYY-MM-DD
                r'(\d{1,2})(?:st|nd|rd|th)? (Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?) (\d{2,4})'  # 1st January 2020
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    try:
                        # Extract date components based on pattern
                        if 'Jan' in pattern or 'Feb' in pattern:
                            # Handle written month format
                            day = int(match.group(1))
                            month_str = match.group(2).lower()
                            year = int(match.group(3))
                            
                            month_map = {
                                'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                                'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                            }
                            
                            month = None
                            for key, value in month_map.items():
                                if month_str.startswith(key):
                                    month = value
                                    break
                                    
                            if month and 1 <= day <= 31:
                                # Handle 2-digit years
                                if year < 100:
                                    year = 2000 + year if year < 50 else 1900 + year
                                    
                                date_obj = datetime(year, month, day)
                                dates.append(date_obj.strftime('%Y-%m-%d'))
                        else:
                            # Handle numeric date formats
                            if '/' in pattern or '-' in pattern:
                                if pattern.startswith(r'(\d{4})'):
                                    # YYYY/MM/DD
                                    year = int(match.group(1))
                                    month = int(match.group(2))
                                    day = int(match.group(3))
                                else:
                                    # DD/MM/YYYY
                                    day = int(match.group(1))
                                    month = int(match.group(2))
                                    year = int(match.group(3))
                                    
                                    # Handle 2-digit years
                                    if year < 100:
                                        year = 2000 + year if year < 50 else 1900 + year
                                
                                if 1 <= month <= 12 and 1 <= day <= 31:
                                    date_obj = datetime(year, month, day)
                                    dates.append(date_obj.strftime('%Y-%m-%d'))
                    except:
                        # Skip invalid dates
                        continue
            
            return dates
            
        except Exception as e:
            logger.error(f"Error extracting dates: {e}")
            return dates
    
    def extract_entities(self, text):
        """Extract key entities (companies, people, etc.) from text."""
        entities = {
            'companies': [],
            'people': [],
            'locations': [],
            'dates': []
        }
        
        if not text:
            return entities
        
        # Extract dates
        entities['dates'] = self.extract_dates(text)
        
        # Simple pattern matching for other entities
        # Company patterns (very basic)
        company_patterns = [
            r'([A-Z][a-z]+ (?:Inc|Ltd|Limited|Corp|Corporation|Company|Co))',
            r'([A-Z][A-Z&]+)'  # All caps company names like IBM, HDFC
        ]
        
        for pattern in company_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                company = match.group(1).strip()
                if company and company not in entities['companies']:
                    entities['companies'].append(company)
        
        # This is a placeholder - a real implementation would use NER models
        return entities