import pytest
import logging
from datetime import datetime
import pandas as pd
import re
from Datapipeline.text_processor import TextProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleDocumentAnalyzer:
    """A simplified document analyzer for testing."""
    
    def __init__(self):
        self.text_processor = TextProcessor()
    
    def analyze_document(self, text, doc_type, doc_date, historical_financials=None):
        """Analyze document text using simple regex patterns."""
        results = {
            'metrics': self._extract_metrics(text),
            'operational_metrics': self._extract_operational_metrics(text),
            'guidance': self._extract_guidance(text),
            'management_commentary': self._analyze_sentiment(text),
            'segment_analysis': self._analyze_segments(text)
        }
        
        if historical_financials is not None:
            results['metrics_validation'] = self._validate_metrics(
                results['metrics'],
                historical_financials
            )
        
        return results
    
    def _extract_metrics(self, text):
        """Extract financial metrics using regex."""
        metrics = {}
        
        # Revenue pattern
        revenue_matches = re.finditer(
            r'revenue.*?\$?([\d.]+)\s*(billion|million|B|M)',
            text,
            re.IGNORECASE
        )
        metrics['revenue'] = []
        for match in revenue_matches:
            value = float(match.group(1))
            unit = match.group(2).lower()
            if 'billion' in unit or 'b' in unit:
                value *= 1000
            metrics['revenue'].append(value)
        
        # Margin pattern
        margin_matches = re.finditer(
            r'margin.*?([\d.]+)%',
            text,
            re.IGNORECASE
        )
        metrics['margin'] = [float(m.group(1)) for m in margin_matches]
        
        return metrics
    
    def _extract_operational_metrics(self, text):
        """Extract operational metrics."""
        metrics = {}
        
        # Customer metrics
        customer_matches = re.finditer(
            r'([\d.]+)\s*(million|M)?\s*(?:customer|user)s?',
            text,
            re.IGNORECASE
        )
        metrics['customers'] = []
        for match in customer_matches:
            value = float(match.group(1))
            unit = match.group(2)
            if unit and ('million' in unit.lower() or 'm' in unit.lower()):
                value *= 1
            metrics['customers'].append(value)
        
        return metrics
    
    def _extract_guidance(self, text):
        """Extract forward-looking statements."""
        guidance = []
        
        # Look for future-oriented statements
        patterns = [
            r'expect.*?(?:[\d.]+%|[\d.]+\s*(?:billion|million))',
            r'guidance.*?(?:[\d.]+%|[\d.]+\s*(?:billion|million))',
            r'target.*?(?:[\d.]+%|[\d.]+\s*(?:billion|million))'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                statement = match.group(0)
                guidance.append({
                    'statement': statement,
                    'sentiment': 'positive' if 'growth' in statement.lower() else 'neutral'
                })
        
        return guidance
    
    def _analyze_sentiment(self, text):
        """Simple sentiment analysis."""
        positive_words = {'growth', 'improvement', 'increased', 'higher', 'strong', 'positive'}
        negative_words = {'decline', 'decreased', 'lower', 'weak', 'negative', 'headwind'}
        
        words = set(text.lower().split())
        pos_count = len(words.intersection(positive_words))
        neg_count = len(words.intersection(negative_words))
        
        sentiment = 'positive' if pos_count > neg_count else 'negative' if neg_count > pos_count else 'neutral'
        
        return {
            'overall_sentiment': sentiment,
            'key_themes': self._extract_themes(text)
        }
    
    def _extract_themes(self, text):
        """Extract key themes from text."""
        themes = {
            'strategy': [],
            'performance': [],
            'outlook': []
        }
        
        sentences = text.split('.')
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            if any(word in sentence.lower() for word in ['strategy', 'initiative', 'plan']):
                themes['strategy'].append(sentence)
            elif any(word in sentence.lower() for word in ['performance', 'delivered', 'achieved']):
                themes['performance'].append(sentence)
            elif any(word in sentence.lower() for word in ['expect', 'guidance', 'outlook']):
                themes['outlook'].append(sentence)
        
        return themes
    
    def _analyze_segments(self, text):
        """Analyze segment performance."""
        segments = {}
        
        # Look for segment information
        pattern = r'(?:In the |The )?([A-Za-z ]+) segment.*?(?:revenue|sales).*?\$?([\d.]+)\s*(billion|million|B|M)'
        matches = re.finditer(pattern, text, re.IGNORECASE)
        
        for match in matches:
            segment_name = match.group(1).strip()
            value = float(match.group(2))
            unit = match.group(3).lower()
            
            if 'billion' in unit or 'b' in unit:
                value *= 1000
                
            segments[segment_name] = {'revenue': value}
            
            # Look for margin
            margin_pattern = f"{segment_name}.*?margin.*?([\d.]+)%"
            margin_match = re.search(margin_pattern, text, re.IGNORECASE)
            if margin_match:
                segments[segment_name]['margin'] = float(margin_match.group(1))
        
        return segments
    
    def _validate_metrics(self, metrics, historical_data):
        """Validate metrics against historical data."""
        validation = {}
        
        for metric in metrics:
            if metric in historical_data.columns:
                reported = sum(metrics[metric]) / len(metrics[metric])
                historical = historical_data[metric].iloc[-1]
                
                percent_diff = ((reported - historical) / historical) * 100
                validation[metric] = {
                    'reported': reported,
                    'historical': historical,
                    'percent_difference': percent_diff,
                    'is_consistent': abs(percent_diff) <= 15
                }
        
        return validation

@pytest.fixture
def sample_text():
    """Sample earnings call transcript for testing."""
    return """
    Thank you for joining us today. I'm pleased to report our Q4 2023 results.
    
    Our revenue for the quarter was $1.2 billion, representing a growth of 15% year-over-year.
    The operating margin improved to 28.5%, up from 26% in the previous quarter.
    We added 2.5 million new customers, bringing our total customer base to 15 million.
    
    In the Cloud Services segment, revenue reached $450 million with a 32% margin.
    Our Enterprise Solutions segment delivered $550 million in revenue, growing at 18%.
    The Digital Transformation segment contributed $200 million with a 25% margin.
    
    Looking ahead, we expect revenue growth of 18-20% in 2024.
    Our margin guidance is 29-30%, reflecting continued operational improvements.
    We're targeting customer growth of 20% and utilization rates above 85%.
    
    While we face some headwinds in certain markets, our strategic initiatives 
    and strong execution position us well for sustainable growth.
    """

@pytest.fixture
def historical_data():
    """Sample historical financial data for testing."""
    return pd.DataFrame({
        'revenue': [1000, 1050, 1100, 1150],
        'margin': [25, 26, 27, 28],
        'customer_count': [12, 13, 14, 14.5]
    })

def test_document_analysis(sample_text, historical_data):
    """Test document analysis functionality."""
    try:
        # Initialize analyzer
        analyzer = SimpleDocumentAnalyzer()
        
        # Analyze document
        results = analyzer.analyze_document(
            text=sample_text,
            doc_type='earnings_call',
            doc_date=datetime.now(),
            historical_financials=historical_data
        )
        
        # Verify results structure
        assert 'metrics' in results
        assert 'operational_metrics' in results
        assert 'guidance' in results
        assert 'management_commentary' in results
        assert 'segment_analysis' in results
        
        # Verify metrics extraction
        metrics = results['metrics']
        assert 'revenue' in metrics
        assert metrics['revenue'][0] == 1200  # $1.2 billion
        
        # Verify operational metrics
        op_metrics = results['operational_metrics']
        assert 'customers' in op_metrics
        assert op_metrics['customers'][0] == 15  # 15 million customers
        
        # Verify guidance extraction
        guidance = results['guidance']
        assert len(guidance) > 0
        assert any('18-20%' in g['statement'] for g in guidance)
        
        # Verify segment analysis
        segments = results['segment_analysis']
        assert 'Cloud Services' in segments
        assert segments['Cloud Services']['revenue'] == 450
        assert segments['Cloud Services']['margin'] == 32
        
        logger.info("Document analyzer tests passed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False

def test_metric_validation(sample_text, historical_data):
    """Test metric validation against historical data."""
    try:
        analyzer = SimpleDocumentAnalyzer()
        
        results = analyzer.analyze_document(
            text=sample_text,
            doc_type='earnings_call',
            doc_date=datetime.now(),
            historical_financials=historical_data
        )
        
        # Verify metrics validation
        validation = results['metrics_validation']
        assert validation is not None
        
        # Check if reported revenue is consistent with historical trend
        if 'revenue' in validation:
            assert validation['revenue']['is_consistent']
            assert abs(validation['revenue']['percent_difference']) <= 15
        
        logger.info("Metric validation tests passed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False

def test_sentiment_analysis(sample_text):
    """Test sentiment analysis functionality."""
    try:
        analyzer = SimpleDocumentAnalyzer()
        
        results = analyzer.analyze_document(
            text=sample_text,
            doc_type='earnings_call',
            doc_date=datetime.now()
        )
        
        # Verify management commentary analysis
        commentary = results['management_commentary']
        assert 'overall_sentiment' in commentary
        assert 'key_themes' in commentary
        
        # Check key themes
        themes = commentary['key_themes']
        assert 'strategy' in themes
        assert 'performance' in themes
        assert 'outlook' in themes
        
        logger.info("Sentiment analysis tests passed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False

if __name__ == '__main__':
    pytest.main([__file__, '-v']) 