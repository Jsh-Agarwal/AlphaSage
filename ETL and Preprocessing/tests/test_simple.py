import unittest
import re
from datetime import datetime

class SimpleDocumentAnalyzer:
    """A simplified document analyzer for testing."""
    
    def analyze_document(self, text):
        """Analyze document text using simple regex patterns."""
        return {
            'metrics': self._extract_metrics(text),
            'segments': self._analyze_segments(text),
            'sentiment': self._analyze_sentiment(text)
        }
    
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
        
        return metrics
    
    def _analyze_segments(self, text):
        """Analyze segment performance."""
        segments = {}
        
        # Split text into sentences for better context
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        for sentence in sentences:
            # Look for segment information with various patterns
            patterns = [
                # Pattern 1: "In the X segment, revenue reached $Y"
                r'(?:In the |The )?([A-Za-z ]+?)(?:\s+segment).*?(?:revenue|sales).*?\$?([\d.]+)\s*(billion|million|B|M)',
                # Pattern 2: "X segment delivered $Y in revenue"
                r'(?:In the |The )?([A-Za-z ]+?)(?:\s+segment).*?delivered.*?\$?([\d.]+)\s*(billion|million|B|M)',
                # Pattern 3: "X segment contributed $Y"
                r'(?:In the |The )?([A-Za-z ]+?)(?:\s+segment).*?contributed.*?\$?([\d.]+)\s*(billion|million|B|M)'
            ]
            
            for pattern in patterns:
                segment_match = re.search(pattern, sentence, re.IGNORECASE)
                if segment_match:
                    # Clean up segment name by removing prefixes
                    segment_name = segment_match.group(1).strip()
                    segment_name = re.sub(r'^(?:In the |The )', '', segment_name, flags=re.IGNORECASE)
                    
                    value = float(segment_match.group(2))
                    unit = segment_match.group(3).lower()
                    
                    if 'billion' in unit or 'b' in unit:
                        value *= 1000
                        
                    segments[segment_name] = {'revenue': value}
                    break  # Stop after first match for this sentence
        
        return segments
    
    def _analyze_sentiment(self, text):
        """Simple sentiment analysis."""
        positive_words = {'growth', 'improvement', 'increased', 'higher', 'strong', 'positive'}
        negative_words = {'decline', 'decreased', 'lower', 'weak', 'negative', 'headwind'}
        
        words = set(text.lower().split())
        pos_count = len(words.intersection(positive_words))
        neg_count = len(words.intersection(negative_words))
        
        return 'positive' if pos_count > neg_count else 'negative' if neg_count > pos_count else 'neutral'

class TestDocumentAnalyzer(unittest.TestCase):
    """Test cases for the document analyzer."""
    
    def setUp(self):
        """Set up test cases."""
        self.analyzer = SimpleDocumentAnalyzer()
        self.sample_text = """
        Our revenue for Q4 2023 was $1.2 billion, representing a growth of 15%.
        
        In the Cloud Services segment, revenue reached $450 million.
        The Enterprise Solutions segment delivered $550 million in revenue.
        
        We expect strong growth in the coming quarters.
        """
    
    def test_revenue_extraction(self):
        """Test revenue extraction."""
        results = self.analyzer.analyze_document(self.sample_text)
        self.assertIn('revenue', results['metrics'])
        self.assertEqual(results['metrics']['revenue'][0], 1200)  # $1.2 billion
    
    def test_segment_analysis(self):
        """Test segment analysis."""
        results = self.analyzer.analyze_document(self.sample_text)
        segments = results['segments']
        
        self.assertIn('Cloud Services', segments)
        self.assertEqual(segments['Cloud Services']['revenue'], 450)
        
        self.assertIn('Enterprise Solutions', segments)
        self.assertEqual(segments['Enterprise Solutions']['revenue'], 550)
    
    def test_sentiment_analysis(self):
        """Test sentiment analysis."""
        results = self.analyzer.analyze_document(self.sample_text)
        self.assertEqual(results['sentiment'], 'positive')

if __name__ == '__main__':
    unittest.main() 