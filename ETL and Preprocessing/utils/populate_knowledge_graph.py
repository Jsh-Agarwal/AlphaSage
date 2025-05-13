import logging
from datetime import datetime
from Datapipeline.etl import FinancialDataETL
from Datapipeline.database import Neo4jDatabase
from Datapipeline.ConfigManager import ConfigManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define stock lists
INDIAN_STOCKS = [
    # NIFTY 50 companies
    "TCS.NS", "RELIANCE.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
    "LT.NS", "AXISBANK.NS", "BAJFINANCE.NS", "ASIANPAINT.NS", "MARUTI.NS"
]

US_STOCKS = [
    # Major US tech and blue-chip companies
    "AAPL", "MSFT", "GOOGL", "AMZN", "META",
    "NVDA", "JPM", "JNJ", "WMT", "V",
    "PG", "MA", "UNH", "HD", "BAC"
]

def initialize_neo4j():
    """Initialize Neo4j connection using config."""
    config = ConfigManager()
    neo4j_config = config.get_neo4j_credentials()
    
    neo4j = Neo4jDatabase(
        uri=neo4j_config["uri"],
        user=neo4j_config["user"],
        password=neo4j_config["password"]
    )
    
    if not neo4j.verify_connection():
        raise Exception("Failed to connect to Neo4j database")
    
    return neo4j

def process_stocks(etl, stocks, exchange):
    """Process a list of stocks."""
    results = {
        "success": [],
        "failed": []
    }
    
    for ticker in stocks:
        try:
            logger.info(f"Processing {ticker} from {exchange}")
            success = etl.process_company(ticker, exchange=exchange)
            
            if success:
                logger.info(f"Successfully processed {ticker}")
                results["success"].append(ticker)
            else:
                logger.error(f"Failed to process {ticker}")
                results["failed"].append(ticker)
                
        except Exception as e:
            logger.error(f"Error processing {ticker}: {e}")
            results["failed"].append(ticker)
    
    return results

def create_sector_relationships(neo4j, etl):
    """Create sector nodes and relationships."""
    logger.info("Creating sector relationships")
    
    # Get all companies
    companies = neo4j.run_query("""
        MATCH (c:Company)
        RETURN c.ticker as ticker, c.sector as sector
    """)
    
    sectors = {}
    for record in companies:
        ticker = record["ticker"]
        sector = record["sector"]
        
        if sector:
            if sector not in sectors:
                sectors[sector] = []
            sectors[sector].append(ticker)
    
    # Create sector nodes and relationships
    for sector, tickers in sectors.items():
        try:
            # Create sector node
            neo4j.create_sector_node(sector, {
                "name": sector,
                "company_count": len(tickers),
                "created_at": datetime.now().isoformat()
            })
            
            # Connect companies to sector
            for ticker in tickers:
                neo4j.connect_company_to_sector(ticker, sector)
                
            logger.info(f"Created sector node and relationships for {sector}")
            
        except Exception as e:
            logger.error(f"Error creating sector relationships for {sector}: {e}")

def main():
    """Main function to populate the knowledge graph."""
    try:
        # Initialize Neo4j and ETL
        neo4j = initialize_neo4j()
        etl = FinancialDataETL()
        etl.neo4j = neo4j
        
        # Process Indian stocks
        logger.info("Processing Indian stocks...")
        indian_results = process_stocks(etl, INDIAN_STOCKS, "NSE")
        
        # Process US stocks
        logger.info("Processing US stocks...")
        us_results = process_stocks(etl, US_STOCKS, "NYSE")
        
        # Create sector relationships
        create_sector_relationships(neo4j, etl)
        
        # Print summary
        logger.info("\nProcessing Summary:")
        logger.info("Indian Stocks:")
        logger.info(f"- Successful: {len(indian_results['success'])}")
        logger.info(f"- Failed: {len(indian_results['failed'])}")
        if indian_results['failed']:
            logger.info(f"- Failed tickers: {', '.join(indian_results['failed'])}")
        
        logger.info("\nUS Stocks:")
        logger.info(f"- Successful: {len(us_results['success'])}")
        logger.info(f"- Failed: {len(us_results['failed'])}")
        if us_results['failed']:
            logger.info(f"- Failed tickers: {', '.join(us_results['failed'])}")
        
        # Close Neo4j connection
        neo4j.close()
        
    except Exception as e:
        logger.error(f"Error in main process: {e}")
        raise

if __name__ == "__main__":
    main() 