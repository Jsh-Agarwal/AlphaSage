import re
import logging
import uuid
import numpy as np
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("Transformers package not available. Advanced NLP features will be disabled.")

logger = logging.getLogger(__name__)

class TextProcessor:
    """Process text documents for embedding and knowledge graph storage."""
    
    def __init__(self):
        """Initialize text processor."""
        # Initialize regex patterns
        self.sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])'
        self.amount_pattern = r'\$?\d+(?:,\d{3})*(?:\.\d{2})?(?:\s?(?:billion|million|thousand))?'
        self.date_pattern = r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2}|\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+\d{4}\b'
        
        # Initialize NLP components
        self.nlp = None
        self.sentiment_analyzer = None
        self.entity_recognizer = None
        
        try:
            import spacy
            import torch
            from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
            
            # Load spaCy model for general NLP tasks
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                spacy.cli.download("en_core_web_sm")
                self.nlp = spacy.load("en_core_web_sm")
            
            # Initialize sentiment analyzer
            if torch.cuda.is_available():
                device = 0  # Use GPU
            else:
                device = -1  # Use CPU
                
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="ProsusAI/finbert",
                tokenizer="ProsusAI/finbert",
                device=device
            )
            
            # Initialize named entity recognition
            self.entity_recognizer = pipeline(
                "ner",
                model="dbmdz/bert-large-cased-finetuned-conll03-english",
                device=device
            )
            
            logger.info("Initialized advanced NLP components successfully")
            
        except ImportError as e:
            logger.warning(f"Advanced NLP features will be limited: {e}")
            
        except Exception as e:
            logger.error(f"Error initializing NLP components: {e}")
            
        # Initialize NLTK components for fallback
        try:
            import nltk
            nltk.download('vader_lexicon', quiet=True)
            nltk.download('punkt', quiet=True)
            from nltk.sentiment.vader import SentimentIntensityAnalyzer
            self.vader = SentimentIntensityAnalyzer()
        except Exception as e:
            logger.error(f"Error initializing NLTK components: {e}")
            self.vader = None
    
    def clean_text(self, text):
        """Clean text by removing unwanted characters and normalizing whitespace."""
        if not text:
            return ""
        
        # Remove unicode characters
        text = text.encode('ascii', 'ignore').decode()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep periods for sentence splitting
        text = re.sub(r'[^a-zA-Z0-9\s\.\!\?]', '', text)
        
        return text.strip()
    
    def chunk_text(self, text, doc_id, chunk_size=1000, overlap=200):
        """Split text into overlapping chunks for processing."""
        if not text:
            return []
        
        # Clean the text first
        clean_text = self.clean_text(text)
        
        # Split into sentences using regex
        sentences = [s.strip() for s in re.split(self.sentence_pattern, clean_text) if s.strip()]
        
        # Initialize chunks
        chunks = []
        current_chunk = []
        current_length = 0
        
        # Process sentences
        for sentence in sentences:
            sentence_length = len(sentence)
            
            # If adding this sentence would exceed chunk size, save current chunk
            if current_length + sentence_length > chunk_size and current_chunk:
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'chunk_id': f"{doc_id}_chunk_{len(chunks)}",
                    'content': chunk_text,
                    'length': len(chunk_text)
                })
                
                # Start new chunk with overlap
                overlap_point = max(0, len(current_chunk) - int(len(current_chunk) * (overlap / chunk_size)))
                current_chunk = current_chunk[overlap_point:]
                current_length = sum(len(s) for s in current_chunk)
            
            # Add sentence to current chunk
            current_chunk.append(sentence)
            current_length += sentence_length
        
        # Add final chunk if it exists
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                'chunk_id': f"{doc_id}_chunk_{len(chunks)}",
                'content': chunk_text,
                'length': len(chunk_text)
            })
        
        return chunks
    
    def extract_entities(self, text):
        """Extract entities from text using regex patterns."""
        if not text:
            return {'companies': [], 'amounts': [], 'dates': [], 'locations': []}
        
        # Clean the text
        clean_text = self.clean_text(text)
        
        # Initialize entities
        entities = {
            'companies': [],
            'amounts': [],
            'dates': [],
            'locations': []
        }
        
        # Find amounts using regex
        entities['amounts'] = re.findall(self.amount_pattern, clean_text)
        
        # Find dates using regex
        entities['dates'] = re.findall(self.date_pattern, clean_text)
        
        return entities
    
    def extract_entities_advanced(self, text):
        """Extract entities using advanced NLP if available."""
        # Start with basic extraction
        entities = self.extract_entities(text)
        
        if TRANSFORMERS_AVAILABLE:
            try:
                from transformers import pipeline
                ner_pipeline = pipeline("ner")
                
                ner_results = ner_pipeline(text)
                
                # Process NER results
                for entity in ner_results:
                    entity_text = entity['word']
                    entity_type = entity['entity']
                    
                    # Map entity types to our categories
                    if entity_type.endswith('ORG'):
                        entities['companies'].append(entity_text)
                    elif entity_type.endswith('LOC'):
                        entities['locations'].append(entity_text)
                
                # Remove duplicates
                for key in entities:
                    entities[key] = list(set(entities[key]))
                    
            except Exception as e:
                logger.warning(f"Advanced entity extraction failed: {e}")
        
        return entities
    
    def analyze_sentiment_with_groq(self, text, groq_client=None):
        """
        Analyze sentiment using GROQ's FinBERT implementation.
        
        Args:
            text (str): Text to analyze
            groq_client: Optional GROQ client instance
            
        Returns:
            dict: Sentiment analysis results
        """
        try:
            if not groq_client:
                from groq import Groq
                import os
                groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            
            # Prepare prompt for financial sentiment analysis
            prompt = f"""
            Analyze the sentiment of this financial text using FinBERT principles.
            Consider financial context, market impact, and company performance.
            
            Text: {text}
            
            Provide:
            1. Sentiment label (POSITIVE/NEGATIVE/NEUTRAL)
            2. Confidence score (0-1)
            3. Key sentiment drivers
            4. Market impact assessment
            """
            
            completion = groq_client.chat.completions.create(
                model="llama3-70b-8192",  # Using LLaMA 3 for financial analysis
                messages=[{"role": "user", "content": prompt}]
            )
            
            response = completion.choices[0].message.content
            
            # Parse the response
            sentiment_label = "NEUTRAL"
            confidence = 0.5
            drivers = []
            impact = ""
            
            # Extract sentiment label and score
            if "POSITIVE" in response.upper():
                sentiment_label = "POSITIVE"
                confidence = 0.8
            elif "NEGATIVE" in response.upper():
                sentiment_label = "NEGATIVE"
                confidence = 0.8
            
            # Convert to standard score (-1 to 1)
            score = confidence if sentiment_label == "POSITIVE" else -confidence if sentiment_label == "NEGATIVE" else 0.0
            
            return {
                "label": sentiment_label,
                "score": score,
                "confidence": confidence,
                "analysis": response,
                "source": "GROQ"
            }
            
        except Exception as e:
            logger.error(f"Error in GROQ sentiment analysis: {e}")
            # Fallback to basic sentiment analysis
            return self._basic_sentiment_analysis(text)

    def analyze_sentiment(self, text):
        """
        Analyze sentiment using available methods in order of preference:
        1. GROQ FinBERT
        2. Local FinBERT
        3. VADER
        4. Basic keyword matching
        """
        if not text:
            return 0.0
        
        try:
            # Try GROQ first if available
            try:
                from groq import Groq
                groq_result = self.analyze_sentiment_with_groq(text)
                return groq_result["score"]
            except ImportError:
                logger.info("GROQ not available, falling back to local FinBERT")
            
            # Try local FinBERT
            if self.sentiment_analyzer:
                sentiment = self.sentiment_analyzer(text)[0]
                if sentiment['label'] == 'positive':
                    return float(sentiment['score'])
                elif sentiment['label'] == 'negative':
                    return -float(sentiment['score'])
                return 0.0
            
            # Try VADER
            if self.vader:
                scores = self.vader.polarity_scores(text)
                return scores['compound']
            
            # Fallback to basic analysis
            return self._basic_sentiment_analysis(text)
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return self._basic_sentiment_analysis(text)
    
    def _basic_sentiment_analysis(self, text):
        """Basic sentiment analysis using keyword matching."""
        # Clean the text
        clean_text = self.clean_text(text.lower())
        
        # Split into words
        words = set(clean_text.split())
        
        # Define sentiment keywords
        positive_words = {
            'increase', 'growth', 'profit', 'gain', 'positive', 'improvement',
            'success', 'strong', 'higher', 'rise', 'up', 'better', 'good',
            'excellent', 'exceed', 'beat', 'record', 'attractive', 'promising',
            'opportunity', 'confident', 'optimistic', 'advantage'
        }
        
        negative_words = {
            'decrease', 'decline', 'loss', 'negative', 'weak', 'lower',
            'down', 'worse', 'poor', 'miss', 'disappoint', 'below',
            'risk', 'concern', 'threat', 'uncertain', 'challenging',
            'difficult', 'problem', 'adverse', 'unfavorable'
        }
        
        # Count word occurrences
        pos_count = len(words.intersection(positive_words))
        neg_count = len(words.intersection(negative_words))
        
        # Calculate sentiment score
        total = pos_count + neg_count
        if total == 0:
            return 0.0
        
        return (pos_count - neg_count) / total
    
    def extract_key_metrics(self, text):
        """Extract key financial metrics from text."""
        if not text:
            return {}
        
        # Clean the text
        clean_text = self.clean_text(text)
        
        # Define patterns for various metrics
        patterns = {
            'revenue': r'revenue of \$?([\d,]+(?:\.\d+)?)\s*(?:billion|million|thousand)?',
            'profit': r'(?:net income|profit) of \$?([\d,]+(?:\.\d+)?)\s*(?:billion|million|thousand)?',
            'eps': r'(?:earnings per share|eps) of \$?([\d,]+(?:\.\d+)?)',
            'ebitda': r'ebitda of \$?([\d,]+(?:\.\d+)?)\s*(?:billion|million|thousand)?',
            'operating_income': r'operating income of \$?([\d,]+(?:\.\d+)?)\s*(?:billion|million|thousand)?',
            'market_cap': r'market (?:cap|capitalization) of \$?([\d,]+(?:\.\d+)?)\s*(?:billion|million|thousand)?',
            'pe_ratio': r'(?:p/e ratio|price[- ]to[- ]earnings) of ([\d,]+(?:\.\d+)?)',
        }
        
        # Extract metrics
        metrics = {}
        for metric, pattern in patterns.items():
            match = re.search(pattern, clean_text.lower())
            if match:
                value = match.group(1)
                # Convert string number to float
                try:
                    metrics[metric] = float(value.replace(',', ''))
                except ValueError:
                    metrics[metric] = None
            else:
                metrics[metric] = None
        
        return metrics
    
    def document_lineage_tracker(self, doc_id, source_type, processing_steps):
        """Track document lineage through processing pipeline."""
        lineage = {
            "doc_id": doc_id,
            "source_type": source_type,
            "processing_history": processing_steps,
            "lineage_id": str(uuid.uuid4()),
            "timestamp": np.datetime64('now').astype(str)
        }
        return lineage
        
    def calculate_document_similarity(self, doc1, doc2):
        """Calculate similarity between two documents."""
        if not doc1 or not doc2:
            return 0.0
            
        try:
            # Use sentence transformers if available
            if TRANSFORMERS_AVAILABLE:
                try:
                    from sentence_transformers import SentenceTransformer
                    model = SentenceTransformer('all-MiniLM-L6-v2')
                    
                    # Get embeddings
                    embedding1 = model.encode(doc1)
                    embedding2 = model.encode(doc2)
                    
                    # Calculate cosine similarity
                    from sklearn.metrics.pairwise import cosine_similarity
                    similarity = cosine_similarity([embedding1], [embedding2])[0][0]
                    return float(similarity)
                except Exception as e:
                    logger.warning(f"Advanced similarity calculation failed: {e}. Falling back to basic method.")
        except ImportError:
            pass
            
        # Fallback to basic word overlap
        words1 = set(self.clean_text(doc1.lower()).split())
        words2 = set(self.clean_text(doc2.lower()).split())
        
        if not words1 or not words2:
            return 0.0
            
        # Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0

    def analyze_document(self, document_text, document_type="unknown"):
        """
        Comprehensive document analysis including sentiment, entities, and key metrics.
        
        Args:
            document_text (str): The document text to analyze
            document_type (str): Type of document (e.g., "annual_report", "transcript")
            
        Returns:
            dict: Analysis results
        """
        try:
            # Clean the text
            clean_text = self.clean_text(document_text)
            
            # Split into chunks for better processing
            chunks = self.chunk_text(clean_text, "temp", chunk_size=2000)
            
            # Analyze each chunk
            chunk_sentiments = []
            all_entities = {
                'companies': set(),
                'amounts': set(),
                'dates': set(),
                'locations': set()
            }
            
            for chunk in chunks:
                # Sentiment analysis
                sentiment = self.analyze_sentiment(chunk['content'])
                chunk_sentiments.append(sentiment)
                
                # Entity extraction
                entities = self.extract_entities(chunk['content'])
                for key in all_entities:
                    all_entities[key].update(entities.get(key, []))
            
            # Calculate average sentiment
            avg_sentiment = sum(chunk_sentiments) / len(chunk_sentiments) if chunk_sentiments else 0.0
            
            # Extract key metrics
            metrics = self.extract_key_metrics(clean_text)
            
            # Prepare results
            results = {
                "sentiment": {
                    "score": avg_sentiment,
                    "label": "POSITIVE" if avg_sentiment > 0.2 else "NEGATIVE" if avg_sentiment < -0.2 else "NEUTRAL",
                    "chunk_scores": chunk_sentiments
                },
                "entities": {k: list(v) for k, v in all_entities.items()},
                "metrics": metrics,
                "document_type": document_type,
                "word_count": len(clean_text.split()),
                "processed_at": datetime.now().isoformat()
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing document: {e}")
            return None
