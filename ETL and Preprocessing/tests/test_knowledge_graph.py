import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from Datapipeline.database import Neo4jDatabase
from Datapipeline.text_processor import TextProcessor
from Datapipeline.yfinance_manager import YFinanceManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("knowledge_graph_test.log"),
        logging.StreamHandler()
    ]
)

def test_knowledge_graph_pipeline():
    """Test the complete knowledge graph pipeline."""
    
    # Initialize components
    neo4j = Neo4jDatabase(
        uri=os.getenv("NEO4J_URI"),
        user=os.getenv("NEO4J_USER"),
        password=os.getenv("NEO4J_PASSWORD")
    )
    
    text_processor = TextProcessor()
    yf_manager = YFinanceManager()
    
    # Test company: TCS
    ticker = "TCS.NS"
    
    try:
        print("\nTesting Knowledge Graph Pipeline for", ticker)
        print("=" * 80)
        
        # 1. Get company data from Yahoo Finance
        print("\n1. Fetching company data...")
        company_data = yf_manager.get_ticker_data(ticker)
        if company_data and company_data.get("info"):
            print("✓ Successfully fetched company data")
            
            # Store company in Neo4j
            neo4j.create_company_node(ticker, company_data["info"])
            print("✓ Stored company data in Neo4j")
        
        # 2. Process a sample document
        print("\n2. Processing sample document...")
        sample_text = """
        TCS reported strong financial results for Q4 FY2024. 
        Revenue grew by 15% YoY to reach ₹59,162 crore.
        The company's operating margin expanded by 150 basis points to 25.8%.
        The Board has recommended a final dividend of ₹27 per share.
        """
        
        doc_analysis = text_processor.analyze_document(sample_text, "earnings_release")
        if doc_analysis:
            print("Document Analysis Results:")
            print(f"- Sentiment: {doc_analysis['sentiment']['label']} (score: {doc_analysis['sentiment']['score']:.2f})")
            print(f"- Entities found: {len(doc_analysis['entities']['amounts'])} amounts, {len(doc_analysis['entities']['dates'])} dates")
            print(f"- Metrics found: {list(doc_analysis['metrics'].keys())}")
            
            # Store document in Neo4j
            document_data = {
                "type": "earnings_release",
                "title": "TCS Q4 FY2024 Results",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "content": sample_text,
                "sentiment_score": doc_analysis['sentiment']['score']
            }
            neo4j.store_document(ticker, document_data)
            print("✓ Stored document in Neo4j")
        
        # 3. Process an earnings call transcript
        print("\n3. Processing earnings call transcript...")
        transcript_text = """
        Operator: Good morning, ladies and gentlemen. Welcome to TCS Q4 earnings call.
        
        CEO: Thank you. We are pleased to report another strong quarter.
        Our digital transformation initiatives continue to gain traction.
        
        CFO: Our revenue grew by 15% year-over-year, with strong margin expansion.
        
        Analyst: Can you provide color on the deal pipeline?
        
        CEO: We see robust demand across markets, particularly in AI and cloud services.
        """
        
        # Split into segments
        transcript_segments = [
            {
                "speaker": "Operator",
                "role": "moderator",
                "content": "Good morning, ladies and gentlemen. Welcome to TCS Q4 earnings call.",
                "start_time": "00:00"
            },
            {
                "speaker": "CEO",
                "role": "executive",
                "content": "Thank you. We are pleased to report another strong quarter. Our digital transformation initiatives continue to gain traction.",
                "start_time": "00:30"
            },
            {
                "speaker": "CFO",
                "role": "executive",
                "content": "Our revenue grew by 15% year-over-year, with strong margin expansion.",
                "start_time": "01:00"
            }
        ]
        
        # Analyze transcript
        for segment in transcript_segments:
            segment_analysis = text_processor.analyze_sentiment(segment["content"])
            segment["sentiment_score"] = segment_analysis
        
        # Store transcript
        transcript_data = {
            "title": "TCS Q4 FY2024 Earnings Call",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "quarter": "Q4",
            "year": "2024",
            "segments": transcript_segments
        }
        
        neo4j.store_transcript(ticker, transcript_data)
        print("✓ Stored transcript in Neo4j")
        
        # 4. Test semantic search
        print("\n4. Testing semantic search...")
        search_results = neo4j.semantic_search("revenue growth margin", limit=2)
        if search_results:
            print("Found relevant content:")
            for result in search_results:
                print(f"- {result['content'][:100]}...")
        
        print("\n✓ Knowledge graph pipeline test completed successfully")
        
    except Exception as e:
        print(f"\n❌ Error in pipeline test: {str(e)}")
        raise
    finally:
        neo4j.close()

if __name__ == "__main__":
    test_knowledge_graph_pipeline() 