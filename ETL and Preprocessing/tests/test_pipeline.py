import pytest
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from Datapipeline.etl import FinancialDataETL
from Datapipeline.text_processor import TextProcessor
from Datapipeline.database import Neo4jDatabase
from Datapipeline.ConfigManager import ConfigManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pipeline_test.log"),
        logging.StreamHandler()
    ]
)

@pytest.fixture(scope="session")
def config():
    """Create test configuration"""
    config = ConfigManager()
    return config

@pytest.fixture(scope="session")
def neo4j_db(config):
    """Create Neo4j database connection if available"""
    try:
        credentials = config.get_neo4j_credentials()
        db = Neo4jDatabase(**credentials)
        if db.verify_connection():
            yield db
            db.close()
        else:
            yield None
    except:
        yield None

@pytest.fixture(scope="session")
def etl_pipeline(config, neo4j_db):
    """Create ETL pipeline instance"""
    pipeline = FinancialDataETL()
    if neo4j_db:
        pipeline.neo4j = neo4j_db
    return pipeline

def test_yfinance_data():
    """Test YFinance data fetching"""
    from Datapipeline.yfinance_manager import YFinanceManager
    yfm = YFinanceManager()
    
    # Test US equity
    aapl_data = yfm.get_ticker_data("AAPL")
    assert aapl_data is not None
    assert "info" in aapl_data
    assert "history" in aapl_data
    
    # Test Indian equity
    tcs_data = yfm.get_ticker_data("TCS.NS")
    assert tcs_data is not None
    assert "info" in tcs_data
    assert "history" in tcs_data

def test_technical_analysis():
    """Test technical analysis capabilities"""
    from Datapipeline.yfinance_manager import YFinanceManager
    yfm = YFinanceManager()
    
    # Get stock data
    data = yfm.get_ticker_data("AAPL")
    assert data is not None
    assert "history" in data
    
    # Calculate technical indicators
    if not data["history"].empty:
        indicators = yfm.calculate_technical_indicators(data["history"])
        assert indicators is not None
        assert "summary" in indicators
        assert isinstance(indicators["summary"], str)
        assert "analysis" in indicators
        assert isinstance(indicators["analysis"], dict)

def test_text_processing():
    """Test text processing capabilities"""
    text_processor = TextProcessor()
    
    # Test sentiment analysis
    text = "The company reported strong earnings growth and increased dividend."
    sentiment = text_processor.analyze_sentiment(text)
    assert isinstance(sentiment, float)
    assert -1 <= sentiment <= 1
    
    # Test entity extraction
    entities = text_processor.extract_entities(text)
    assert isinstance(entities, dict)
    assert "companies" in entities
    assert "amounts" in entities
    assert "dates" in entities

@pytest.mark.skipif(not os.getenv("NEO4J_URI"), reason="Neo4j credentials not configured")
def test_knowledge_graph(neo4j_db):
    """Test knowledge graph operations"""
    if not neo4j_db:
        pytest.skip("Neo4j connection not available")
        
    try:
        # Create test data
        company_data = {
            "ticker": "TEST",
            "name": "Test Company",
            "sector": "Technology",
            "industry": "Software",
            "last_updated": datetime.now().isoformat()
        }
        
        # Store in Neo4j
        neo4j_db.create_company_node("TEST", company_data)
        
        # Verify storage
        stored_data = neo4j_db.get_company_by_ticker("TEST")
        assert stored_data is not None
        assert stored_data["ticker"] == "TEST"
        assert stored_data["sector"] == "Technology"
        
        # Test relationships
        news_data = [{
            "headline": "Test News",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "sentiment": 0.8,
            "link": "http://example.com/news"
        }]
        neo4j_db.store_news("TEST", news_data)
        
        # Clean up
        neo4j_db.run_query("MATCH (c:Company {ticker: $ticker}) DETACH DELETE c", {"ticker": "TEST"})
    except Exception as e:
        logging.error(f"Error in knowledge graph test: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    pytest.main(["-v", "--tb=short"]) 