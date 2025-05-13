import pytest
from pytest_lazyfixture import lazy_fixture
from Datapipeline.etl import FinancialDataETL
import logging

logger = logging.getLogger(__name__)

# Integration tests get longer timeout
pytestmark = [
    pytest.mark.timeout(600),  # 10 minutes
    pytest.mark.integration    # Mark all tests as integration tests
]

@pytest.fixture(scope="session")
def mock_neo4j():
    """Session-scoped Neo4j mock"""
    from unittest.mock import MagicMock
    neo4j = MagicMock()
    neo4j.verify_connection.return_value = True
    return neo4j

class TestIntegration:
    """Integration tests for the ETL pipeline"""
    
    def test_full_pipeline(self, mock_neo4j):
        """Test the full ETL pipeline end-to-end"""
        pipeline = FinancialDataETL()
        pipeline.neo4j = mock_neo4j
        
        # Process a test ticker
        success = pipeline.process_company_data("TEST")
        assert success == True
        
        # Verify data was stored in Neo4j
        mock_neo4j.create_company_node.assert_called_once()
        mock_neo4j.create_stock_data_nodes.assert_called_once()
    
    @pytest.mark.slow
    def test_sector_analysis(self, mock_neo4j):
        """Test sector analysis functionality"""
        pipeline = FinancialDataETL()
        pipeline.neo4j = mock_neo4j
        
        sector_data = {
            "Technology": ["AAPL", "MSFT", "GOOGL"]
        }
        
        results = pipeline.run_sector_analysis(sector_data)
        assert results["sectors_processed"] == 1
        assert results["companies_processed"] == 3
