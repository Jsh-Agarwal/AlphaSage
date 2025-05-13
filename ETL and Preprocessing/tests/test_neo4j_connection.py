from Datapipeline.database import Neo4jDatabase
from Datapipeline.etl import YFinanceManager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_stock(neo4j, yfm, ticker):
    """Process a single stock's data."""
    logger.info(f"\nProcessing {ticker}...")
    data = yfm.get_ticker_data(ticker)
    
    if data and data.get("info"):
        # Clean and flatten company data
        company_info = data["info"].copy()
        # Remove nested objects that Neo4j doesn't support
        if "companyOfficers" in company_info:
            del company_info["companyOfficers"]
        
        # Store company data
        logger.info(f"Storing company data for {ticker} in Neo4j...")
        neo4j.create_company_node(ticker, company_info)
        
        # Store price history
        if data.get("history") is not None:
            logger.info(f"Storing price history for {ticker}...")
            neo4j.create_stock_data_nodes(ticker, data["history"])
        
        logger.info(f"Data successfully stored for {ticker}!")
        return True
    else:
        logger.error(f"Failed to fetch data for {ticker}")
        return False

def test_neo4j_connection():
    """Test Neo4j connection and store sample data."""
    try:
        # Initialize Neo4j connection
        neo4j = Neo4jDatabase(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="password"
        )
        
        # Test connection
        if neo4j.verify_connection():
            logger.info("Successfully connected to Neo4j!")
            
            # Initialize YFinance manager
            yfm = YFinanceManager()
            
            # Process both stocks
            stocks = ["TCS.NS", "AAPL"]
            successful_stocks = []
            
            for ticker in stocks:
                if process_stock(neo4j, yfm, ticker):
                    successful_stocks.append(ticker)
            
            if successful_stocks:
                print("\nTo view the data in Neo4j Browser, use these queries:")
                
                # Basic company query
                print("\n1. View basic company info:")
                print("   MATCH (c:Company) RETURN c.ticker, c.shortName, c.sector, c.marketCap")
                
                # Price history query
                print("\n2. View recent price history:")
                print("   MATCH (c:Company {ticker: 'TCS.NS'})-[:HAS_PRICE]->(p)")
                print("   RETURN p.date, p.open, p.high, p.low, p.close, p.volume")
                print("   ORDER BY p.date DESC")
                print("   LIMIT 5")
                
                # Financial metrics query
                print("\n3. View key financial metrics:")
                print("   MATCH (c:Company)")
                print("   RETURN c.ticker, c.trailingPE, c.priceToBook, c.profitMargins")
        else:
            logger.error("Failed to connect to Neo4j")
    except Exception as e:
        logger.error(f"Error during test: {e}")

if __name__ == "__main__":
    test_neo4j_connection() 