"""
Document analyzer module for processing financial documents and extracting insights.
Handles various document types including earnings calls, annual reports, and presentations.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import pandas as pd
import numpy as np
from transformers import pipeline
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MetricPattern:
    """Dataclass for storing regex patterns and their metadata for metric extraction."""
    pattern: str
    value_group: int
    unit_group: Optional[int] = None
    multiplier: float = 1.0
    description: str = ""

class DocumentAnalyzer:
    """
    Analyzes financial documents to extract insights, metrics, and correlations.
    
    Features:
    - Extracts business and operational metrics
    - Processes forward-looking statements
    - Analyzes management commentary
    - Validates metrics against historical data
    - Generates AI-powered insights
    """
    
    def __init__(self, use_groq: bool = False):
        """
        Initialize the document analyzer with necessary models and patterns.
        
        Args:
            use_groq: Whether to use GROQ for AI-powered insights
        """
        try:
            # Initialize NLP pipelines
            self.ner_pipeline = pipeline("ner", model="jean-baptiste/camembert-ner-with-dates")
            self.sentiment_pipeline = pipeline("sentiment-analysis", 
                                            model="ProsusAI/finbert")
            
            # Initialize metric patterns
            self._init_metric_patterns()
            
            self.use_groq = use_groq
            logger.info("DocumentAnalyzer initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing DocumentAnalyzer: {str(e)}")
            raise
            
    def _init_metric_patterns(self):
        """Initialize regex patterns for extracting various metrics."""
        self.metric_patterns = {
            'revenue': MetricPattern(
                pattern=r'revenue.*?[\$£€]?\s*([\d,.]+)\s*(million|billion|M|B|$)',
                value_group=1,
                unit_group=2,
                description="Total revenue"
            ),
            'profit_margin': MetricPattern(
                pattern=r'(?:profit|operating) margin.*?([\d.]+)\s*%',
                value_group=1,
                description="Profit margin percentage"
            ),
            'growth': MetricPattern(
                pattern=r'growth.*?([\d.]+)\s*%',
                value_group=1,
                description="Growth rate"
            ),
            'customer_count': MetricPattern(
                pattern=r'customer.*?([\d,.]+)\s*(million|M)?',
                value_group=1,
                unit_group=2,
                description="Number of customers"
            ),
            'utilization': MetricPattern(
                pattern=r'utilization.*?([\d.]+)\s*%',
                value_group=1,
                description="Utilization rate"
            )
        }
    
    def analyze_document(self, 
                        text: str, 
                        doc_type: str,
                        doc_date: datetime,
                        historical_financials: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Analyze a document and extract insights.
        
        Args:
            text: Document text to analyze
            doc_type: Type of document (earnings_call, annual_report, presentation)
            doc_date: Date of the document
            historical_financials: Historical financial data for validation
            
        Returns:
            Dictionary containing extracted insights
        """
        try:
            # Extract metrics and insights
            metrics = self._extract_business_metrics(text)
            operational_metrics = self._extract_operational_metrics(text)
            guidance = self._extract_guidance(text)
            management_commentary = self._analyze_management_commentary(text)
            segment_analysis = self._analyze_segments(text)
            
            # Validate metrics if historical data is available
            metrics_validation = None
            trend_analysis = None
            if historical_financials is not None:
                metrics_validation = self._validate_metrics(metrics, historical_financials)
                trend_analysis = self._analyze_trends(metrics, historical_financials)
            
            # Generate AI insights if enabled
            ai_insights = None
            if self.use_groq:
                ai_insights = self._generate_ai_insights(
                    text, metrics, guidance, management_commentary
                )
            
            return {
                'doc_type': doc_type,
                'doc_date': doc_date,
                'metrics': metrics,
                'operational_metrics': operational_metrics,
                'guidance': guidance,
                'management_commentary': management_commentary,
                'segment_analysis': segment_analysis,
                'metrics_validation': metrics_validation,
                'trend_analysis': trend_analysis,
                'ai_insights': ai_insights
            }
            
        except Exception as e:
            logger.error(f"Error analyzing document: {str(e)}")
            raise
    
    def _extract_business_metrics(self, text: str) -> Dict[str, Any]:
        """Extract business metrics from text using regex patterns."""
        metrics = {}
        
        for metric_name, pattern in self.metric_patterns.items():
            matches = re.finditer(pattern.pattern, text, re.IGNORECASE)
            for match in matches:
                value = float(match.group(pattern.value_group).replace(',', ''))
                
                # Apply unit multiplier if present
                if pattern.unit_group:
                    unit = match.group(pattern.unit_group).lower()
                    if 'billion' in unit or 'b' in unit:
                        value *= 1000
                
                if metric_name not in metrics:
                    metrics[metric_name] = []
                metrics[metric_name].append(value)
        
        return metrics
    
    def _extract_operational_metrics(self, text: str) -> Dict[str, Any]:
        """Extract operational metrics like customer count, utilization, etc."""
        metrics = {}
        
        # Extract customer metrics
        customer_matches = re.finditer(
            r'([\d,.]+)\s*(million|M)?\s*(?:customer|user|subscriber)',
            text,
            re.IGNORECASE
        )
        metrics['customers'] = [
            float(m.group(1).replace(',', '')) * (1000000 if m.group(2) else 1)
            for m in customer_matches
        ]
        
        # Extract utilization metrics
        utilization_matches = re.finditer(
            r'utilization.*?([\d.]+)\s*%',
            text,
            re.IGNORECASE
        )
        metrics['utilization'] = [float(m.group(1)) for m in utilization_matches]
        
        return metrics
    
    def _extract_guidance(self, text: str) -> List[Dict[str, Any]]:
        """Extract forward-looking statements and guidance."""
        guidance = []
        
        # Look for future-oriented statements
        future_patterns = [
            r'expect.*?(?:revenue|growth).*?([\d.]+)[-%]',
            r'guidance.*?(?:[\$£€]\s*[\d.]+\s*(?:million|billion|M|B))',
            r'project.*?(?:[\d.]+%|[\$£€]\s*[\d.]+)',
            r'forecast.*?(?:[\d.]+%|[\$£€]\s*[\d.]+)'
        ]
        
        for pattern in future_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                statement = match.group(0)
                
                # Analyze sentiment of the guidance statement
                sentiment_result = self.sentiment_pipeline(statement)[0]
                
                guidance.append({
                    'statement': statement,
                    'sentiment': sentiment_result['label'],
                    'confidence': sentiment_result['score']
                })
        
        return guidance
    
    def _analyze_management_commentary(self, text: str) -> Dict[str, Any]:
        """Analyze management commentary for sentiment and key themes."""
        # Split text into sentences
        sentences = re.split(r'[.!?]+', text)
        
        # Analyze sentiment for each sentence
        sentiments = []
        key_themes = {
            'strategy': [],
            'performance': [],
            'outlook': [],
            'challenges': []
        }
        
        for sentence in sentences:
            if len(sentence.strip()) < 10:
                continue
                
            # Get sentiment
            sentiment_result = self.sentiment_pipeline(sentence)[0]
            sentiments.append(sentiment_result['label'])
            
            # Categorize by theme
            lower_sent = sentence.lower()
            if any(word in lower_sent for word in ['strategy', 'plan', 'initiative']):
                key_themes['strategy'].append(sentence.strip())
            elif any(word in lower_sent for word in ['performance', 'achieved', 'delivered']):
                key_themes['performance'].append(sentence.strip())
            elif any(word in lower_sent for word in ['expect', 'outlook', 'future']):
                key_themes['outlook'].append(sentence.strip())
            elif any(word in lower_sent for word in ['challenge', 'risk', 'headwind']):
                key_themes['challenges'].append(sentence.strip())
        
        # Calculate sentiment distribution
        sentiment_counts = pd.Series(sentiments).value_counts().to_dict()
        
        return {
            'overall_sentiment': sentiment_counts,
            'key_themes': key_themes
        }
    
    def _analyze_segments(self, text: str) -> Dict[str, Any]:
        """Analyze segment-wise performance and metrics."""
        segments = {}
        
        # Look for segment information
        segment_pattern = r'(?:In the |The )?([A-Za-z ]+) segment.*?(?:revenue|sales) .*?([\$£€]?\s*[\d.]+\s*(?:million|billion|M|B))'
        matches = re.finditer(segment_pattern, text, re.IGNORECASE)
        
        for match in matches:
            segment_name = match.group(1).strip()
            revenue_str = match.group(2)
            
            # Extract numeric value
            value = float(re.search(r'[\d.]+', revenue_str).group())
            
            # Apply multiplier based on unit
            if 'billion' in revenue_str.lower() or 'b' in revenue_str.lower():
                value *= 1000
            
            segments[segment_name] = {'revenue': value}
            
            # Look for additional segment metrics
            segment_context = text[max(0, match.start() - 100):min(len(text), match.end() + 100)]
            
            # Extract growth
            growth_match = re.search(r'(?:growth|increase) of ([\d.]+)%', segment_context)
            if growth_match:
                segments[segment_name]['growth'] = float(growth_match.group(1))
            
            # Extract margin
            margin_match = re.search(r'margin of ([\d.]+)%', segment_context)
            if margin_match:
                segments[segment_name]['margin'] = float(margin_match.group(1))
        
        return segments
    
    def _validate_metrics(self, 
                         metrics: Dict[str, Any], 
                         historical_data: pd.DataFrame) -> Dict[str, Any]:
        """Validate extracted metrics against historical data."""
        validation = {}
        
        for metric in metrics:
            if metric in historical_data.columns:
                reported = np.mean(metrics[metric])
                historical = historical_data[metric].iloc[-1]
                
                percent_diff = ((reported - historical) / historical) * 100
                
                validation[metric] = {
                    'reported': reported,
                    'historical': historical,
                    'percent_difference': percent_diff,
                    'is_consistent': abs(percent_diff) <= 15  # 15% threshold
                }
        
        return validation
    
    def _analyze_trends(self, 
                       metrics: Dict[str, Any], 
                       historical_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trends in metrics compared to historical data."""
        trends = {}
        
        for metric in metrics:
            if metric in historical_data.columns:
                historical_values = historical_data[metric].values
                
                # Calculate growth rates
                growth_rates = np.diff(historical_values) / historical_values[:-1] * 100
                
                trends[metric] = {
                    'avg_growth': np.mean(growth_rates),
                    'growth_volatility': np.std(growth_rates),
                    'trend_direction': 'up' if np.mean(growth_rates) > 0 else 'down',
                    'consistency': 'high' if np.std(growth_rates) < 10 else 'low'
                }
        
        return trends
    
    def _generate_ai_insights(self,
                            text: str,
                            metrics: Dict[str, Any],
                            guidance: List[Dict[str, Any]],
                            management_commentary: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered insights using GROQ if available."""
        if not self.use_groq:
            return None
            
        try:
            # Prepare context for analysis
            context = {
                'metrics': metrics,
                'guidance': guidance,
                'sentiment': management_commentary['overall_sentiment'],
                'key_themes': management_commentary['key_themes']
            }
            
            # TODO: Implement GROQ analysis
            # For now, return a placeholder
            return {
                'analysis': 'AI-powered insights not yet implemented'
            }
            
        except Exception as e:
            logger.error(f"Error generating AI insights: {str(e)}")
            return None 