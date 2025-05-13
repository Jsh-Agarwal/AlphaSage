import os
import logging
from datetime import datetime
from Datapipeline.etl import FinancialDataETL
from Datapipeline.database import Neo4jDatabase
from Datapipeline.text_processor import TextProcessor
from Datapipeline.document_analyzer import DocumentAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_document_processing():
    """Test document processing and knowledge graph integration."""
    try:
        # Initialize components
        etl = FinancialDataETL()
        text_processor = TextProcessor()
        doc_analyzer = DocumentAnalyzer()
        
        # Connect to Neo4j
        neo4j = Neo4jDatabase(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="password"
        )
        
        # Test company ticker
        ticker = "TCS.NS"
        
        # Process company data
        logger.info(f"Processing company data for {ticker}")
        success = etl.process_company(ticker, exchange="NSE")
        assert success, "Failed to process company data"
        
        # Test document scraping
        logger.info("Testing document scraping")
        documents = etl.document_scraper.scrape_ir_documents(ticker)
        assert documents, "No documents found"
        
        # Process each document
        for doc_type, docs in documents.items():
            for doc in docs:
                # Extract text
                text = text_processor.clean_text(doc.get('text_content', ''))
                if text:
                    # Analyze document
                    analysis = doc_analyzer.analyze_document(
                        text=text,
                        doc_type=doc_type,
                        doc_date=datetime.now()
                    )
                    
                    # Store in Neo4j
                    neo4j.store_document(ticker, {
                        **doc,
                        'analysis': analysis
                    })
        
        # Verify data in Neo4j
        logger.info("Verifying data in Neo4j")
        company = neo4j.get_company_by_ticker(ticker)
        assert company, f"Company {ticker} not found in Neo4j"
        
        logger.info("All tests passed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_document_processing() 