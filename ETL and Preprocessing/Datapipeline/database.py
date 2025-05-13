from neo4j import GraphDatabase
import logging
import pandas as pd
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class Neo4jDatabase:
    """Class to handle Neo4j database operations for the financial data ETL pipeline."""
    
    def __init__(self, uri=None, user=None, password=None):
        """Initialize the Neo4j connection."""
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        if uri and user and password:
            self.connect()
    
    def connect(self):
        """Create a connection to Neo4j."""
        try:
            # Initialize the driver first
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            
            # Create constraints and indexes if they don't exist
            with self.driver.session() as session:
                # Company constraints
                session.run("""
                    CREATE CONSTRAINT company_ticker IF NOT EXISTS
                    FOR (c:Company) REQUIRE c.ticker IS UNIQUE
                """)
                
                # Document constraints
                session.run("""
                    CREATE CONSTRAINT document_id IF NOT EXISTS
                    FOR (d:Document) REQUIRE d.id IS UNIQUE
                """)
                
                # Create indexes for better performance
                session.run("CREATE INDEX company_sector IF NOT EXISTS FOR (c:Company) ON (c.sector)")
                session.run("CREATE INDEX document_type IF NOT EXISTS FOR (d:Document) ON (d.type)")
                session.run("CREATE INDEX news_date IF NOT EXISTS FOR (n:News) ON (n.date)")
                
                logger.info("Neo4j connection established and schema initialized")
                return True
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self.driver = None
            return False
    
    def close(self):
        """Close the Neo4j connection."""
        if self.driver:
            self.driver.close()
            self.driver = None
            logger.info("Neo4j connection closed")
    
    def verify_connection(self):
        """Verify that the connection to Neo4j is working."""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 'Connection successful' AS message")
                message = result.single()["message"]
                logger.info(f"Neo4j connection test: {message}")
                return True
        except Exception as e:
            logger.error(f"Neo4j connection test failed: {e}")
            return False
    
    def run_query(self, query, params=None):
        """Run a Cypher query against the Neo4j database."""
        try:
            with self.driver.session() as session:
                result = session.run(query, params or {})
                return result
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
    
    def create_company_node(self, ticker, company_data):
        """Create a company node in the knowledge graph."""
        query = """
        MERGE (c:Company {ticker: $ticker})
        SET c += $properties
        RETURN c
        """
        params = {
            "ticker": ticker,
            "properties": company_data
        }
        return self.run_query(query, params)
    
    def create_stock_data_nodes(self, ticker, stock_data):
        """Store stock price data as Price nodes connected to a Company."""
        # First make sure the data is in the right format
        if stock_data is None or stock_data.empty:
            return None
        
        # Reset index to make date a column
        stock_data = stock_data.reset_index()
        
        # Convert to list of dictionaries for Neo4j
        records = stock_data.to_dict('records')
        
        # Store each price point
        query = """
        MATCH (c:Company {ticker: $ticker})
        WITH c
        UNWIND $records AS record
        CREATE (p:Price {
            date: date(record.Date),
            open: record.Open,
            high: record.High,
            low: record.Low,
            close: record.Close,
            volume: record.Volume
        })
        CREATE (c)-[:HAS_PRICE]->(p)
        """
        
        # Batch process 1000 records at a time to avoid memory issues
        batch_size = 1000
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            params = {
                "ticker": ticker,
                "records": batch
            }
            self.run_query(query, params)
        
        return True
    
    def store_technical_indicators(self, ticker, indicators_data):
        """Store technical indicators for a stock."""
        if indicators_data is None or indicators_data.empty:
            return None
        
        # Reset index to make date a column
        indicators_data = indicators_data.reset_index()
        
        # Get just the technical indicators (not price data)
        indicator_columns = [col for col in indicators_data.columns if col not in ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
        
        # For each date, store the indicators
        records = indicators_data.to_dict('records')
        
        query = """
        MATCH (c:Company {ticker: $ticker})-[:HAS_PRICE]->(p:Price {date: date($date)})
        SET p += $indicators
        """
        
        for record in records:
            date_str = record['Date'].strftime('%Y-%m-%d')
            indicators = {col: record[col] for col in indicator_columns if pd.notna(record[col])}
            
            params = {
                "ticker": ticker,
                "date": date_str,
                "indicators": indicators
            }
            
            self.run_query(query, params)
        
        return True
    
    def store_financial_statements(self, ticker, statements):
        """Store financial statement data in the knowledge graph."""
        if statements is None:
            return None
        
        # Store balance sheet
        bs = statements.get("balance_sheet")
        if bs is not None and not bs.empty:
            self._store_financial_statement(ticker, bs, "BalanceSheet")
        
        # Store income statement
        is_stmt = statements.get("income_statement")
        if is_stmt is not None and not is_stmt.empty:
            self._store_financial_statement(ticker, is_stmt, "IncomeStatement")
        
        # Store cash flow
        cf = statements.get("cash_flow")
        if cf is not None and not cf.empty:
            self._store_financial_statement(ticker, cf, "CashFlow")
        
        # Store quarterly statements
        q_bs = statements.get("quarterly_balance_sheet")
        if q_bs is not None and not q_bs.empty:
            self._store_financial_statement(ticker, q_bs, "QuarterlyBalanceSheet")
        
        q_is = statements.get("quarterly_income_statement")
        if q_is is not None and not q_is.empty:
            self._store_financial_statement(ticker, q_is, "QuarterlyIncomeStatement")
        
        q_cf = statements.get("quarterly_cash_flow")
        if q_cf is not None and not q_cf.empty:
            self._store_financial_statement(ticker, q_cf, "QuarterlyCashFlow")
        
        return True
    
    def _store_financial_statement(self, ticker, df, statement_type):
        """Helper method to store a financial statement dataframe."""
        # Reset the index
        df = df.reset_index()
        
        # Convert columns to strings (Neo4j doesn't like non-string column names)
        df.columns = df.columns.astype(str)
        
        # Get a list of dictionaries
        records = []
        for _, row in df.iterrows():
            record = {"date": row["index"].strftime('%Y-%m-%d')}
            for col in df.columns:
                if col != "index" and not pd.isna(row[col]):
                    # Convert numpy/pandas numeric types to Python native types
                    if hasattr(row[col], 'item'):
                        record[col] = row[col].item()
                    else:
                        record[col] = row[col]
            records.append(record)
        
        # Create statement nodes
        query = f"""
        MATCH (c:Company {{ticker: $ticker}})
        WITH c
        UNWIND $records AS record
        CREATE (s:{statement_type} {{date: date(record.date)}})
        SET s += record
        CREATE (c)-[:HAS_{statement_type.upper()}]->(s)
        """
        
        params = {
            "ticker": ticker,
            "records": records
        }
        
        self.run_query(query, params)
    
    def store_financial_ratios(self, ticker, ratios):
        """Store financial ratios for a company."""
        if not ratios:
            return None
        
        query = """
        MATCH (c:Company {ticker: $ticker})
        SET c.financial_ratios = $ratios
        """
        
        params = {
            "ticker": ticker,
            "ratios": ratios
        }
        
        self.run_query(query, params)
        return True
    
    def store_company_filings(self, ticker, filings):
        """Store SEC/regulatory filings in the knowledge graph."""
        if not filings:
            return None
        
        query = """
        MATCH (c:Company {ticker: $ticker})
        WITH c
        UNWIND $filings AS filing
        CREATE (f:Filing {
            type: filing.type,
            filing_date: date(filing.filing_date),
            url: filing.url,
            id: filing.accessionNumber
        })
        SET f.content = filing.content
        CREATE (c)-[:HAS_FILING]->(f)
        """
        
        # Clean the filings data
        clean_filings = []
        for filing in filings:
            # Convert filing date to ISO format
            if 'filing_date' in filing and filing['filing_date']:
                try:
                    date_obj = datetime.strptime(filing['filing_date'], '%Y-%m-%d')
                    filing['filing_date'] = date_obj.strftime('%Y-%m-%d')
                except:
                    # If date parsing fails, use today's date
                    filing['filing_date'] = datetime.now().strftime('%Y-%m-%d')
            else:
                filing['filing_date'] = datetime.now().strftime('%Y-%m-%d')
                
            # Make sure we have an accession number
            if 'accessionNumber' not in filing or not filing['accessionNumber']:
                filing['accessionNumber'] = f"filing_{len(clean_filings)}_{datetime.now().timestamp()}"
                
            clean_filings.append(filing)
        
        params = {
            "ticker": ticker,
            "filings": clean_filings
        }
        
        self.run_query(query, params)
        return True
    
    def store_news(self, ticker, news_items):
        """Store news items for a company."""
        if not news_items:
            return None
        
        query = """
        MATCH (c:Company {ticker: $ticker})
        WITH c
        UNWIND $news AS item
        CREATE (n:News {
            headline: item.headline,
            link: item.link,
            id: item.link
        })
        SET n.date = CASE WHEN item.date IS NOT NULL THEN date(item.date) ELSE null END,
            n.time = item.time,
            n.sentiment = item.sentiment
        CREATE (c)-[:HAS_NEWS]->(n)
        """
        
        # Clean the news items
        clean_news = []
        for item in news_items:
            # Convert date to ISO format if it exists
            if 'date' in item and item['date']:
                try:
                    date_obj = datetime.strptime(item['date'], '%Y-%m-%d')
                    item['date'] = date_obj.strftime('%Y-%m-%d')
                except:
                    # If date parsing fails, set to null
                    item['date'] = None
            else:
                item['date'] = None
                
            clean_news.append(item)
        
        params = {
            "ticker": ticker,
            "news": clean_news
        }
        
        self.run_query(query, params)
        return True
    
    def store_report(self, company_name, report):
        """Store a company report with text content."""
        if not report:
            return None
        
        query = """
        MATCH (c:Company {name: $company_name})
        WITH c
        CREATE (r:Report {
            title: $title,
            url: $url,
            type: $type,
            id: $url
        })
        SET r.content = $content
        CREATE (c)-[:HAS_REPORT]->(r)
        """
        
        params = {
            "company_name": company_name,
            "title": report.get("title", ""),
            "url": report.get("url", ""),
            "type": report.get("type", ""),
            "content": report.get("text_content", "")
        }
        
        self.run_query(query, params)
        return True
    
    def store_text_chunks(self, source_id, source_type, chunks):
        """Store text chunks for semantic search and retrieval."""
        if not chunks:
            return None
        
        query = """
        MATCH (s)
        WHERE s.id = $source_id AND $source_label in labels(s)
        WITH s
        UNWIND $chunks AS chunk
        CREATE (c:TextChunk {
            content: chunk.content,
            chunk_id: chunk.chunk_id
        })
        CREATE (s)-[:HAS_CHUNK]->(c)
        """
        
        params = {
            "source_id": source_id,
            "source_label": source_type,
            "chunks": chunks
        }
        
        self.run_query(query, params)
        return True
    
    def create_sector_node(self, sector_name, sector_data):
        """Create a sector node in the knowledge graph."""
        query = """
        MERGE (s:Sector {name: $sector_name})
        SET s += $properties
        RETURN s
        """
        params = {
            "sector_name": sector_name,
            "properties": sector_data
        }
        return self.run_query(query, params)
    
    def connect_company_to_sector(self, ticker, sector_name):
        """Connect a company to its sector."""
        query = """
        MATCH (c:Company {ticker: $ticker})
        MATCH (s:Sector {name: $sector_name})
        MERGE (c)-[:BELONGS_TO]->(s)
        """
        params = {
            "ticker": ticker,
            "sector_name": sector_name
        }
        return self.run_query(query, params)
    
    def store_sector_report(self, sector_name, report):
        """Store a sector analysis report."""
        if not report:
            return None
        
        query = """
        MATCH (s:Sector {name: $sector_name})
        WITH s
        CREATE (r:SectorReport {
            title: $title,
            url: $url,
            date: date($date),
            id: $url
        })
        SET r.content = $content
        CREATE (s)-[:HAS_REPORT]->(r)
        """
        
        params = {
            "sector_name": sector_name,
            "title": report.get("title", ""),
            "url": report.get("url", ""),
            "date": report.get("date", datetime.now().strftime('%Y-%m-%d')),
            "content": report.get("content", "")
        }
        
        self.run_query(query, params)
        return True
    
    def get_companies_by_sector(self, sector_name):
        """
        Get all companies belonging to a specific sector.
        
        Parameters:
            sector_name (str): Name of the sector
            
        Returns:
            list: List of company dictionaries with their properties
        """
        query = """
        MATCH (c:Company)-[:BELONGS_TO]->(s:Sector {name: $sector_name})
        RETURN c
        """
        
        params = {
            "sector_name": sector_name
        }
        
        try:
            result = self.run_query(query, params)
            companies = []
            for record in result:
                company_node = record["c"]
                companies.append(dict(company_node))
            
            logger.info(f"Retrieved {len(companies)} companies for sector {sector_name}")
            return companies
        except Exception as e:
            logger.error(f"Error retrieving companies for sector {sector_name}: {e}")
            return []
    
    def store_analysis(self, ticker, analysis_data):
        """Store AI-generated analysis for a company."""
        if not analysis_data:
            return None
        
        query = """
        MATCH (c:Company {ticker: $ticker})
        MERGE (a:Analysis {ticker: $ticker})
        SET a.fundamental_analysis = $fundamental_analysis,
            a.news_impact = $news_impact,
            a.investment_thesis = $investment_thesis,
            a.timestamp = datetime($timestamp),
            a.updated_at = datetime()
        MERGE (c)-[:HAS_ANALYSIS]->(a)
        """
        
        params = {
            "ticker": ticker,
            "fundamental_analysis": analysis_data.get('fundamental_analysis', ''),
            "news_impact": analysis_data.get('news_impact', ''),
            "investment_thesis": analysis_data.get('investment_thesis', ''),
            "timestamp": analysis_data.get('timestamp', datetime.now().isoformat())
        }
        
        self.run_query(query, params)
        return True
    
    def store_sentiment_analysis(self, ticker, sentiment_data):
        """Store sentiment analysis results for a company."""
        if not sentiment_data:
            return None
        
        query = """
        MATCH (c:Company {ticker: $ticker})
        MERGE (s:SentimentAnalysis {ticker: $ticker})
        SET s.average_score = $average_score,
            s.sentiment_volatility = $sentiment_volatility,
            s.positive_ratio = $positive_ratio,
            s.negative_ratio = $negative_ratio,
            s.sentiment_trend = $sentiment_trend,
            s.timestamp = datetime()
        MERGE (c)-[:HAS_SENTIMENT]->(s)
        """
        
        params = {
            "ticker": ticker,
            "average_score": sentiment_data.get('average_score', 0.0),
            "sentiment_volatility": sentiment_data.get('sentiment_volatility', 0.0),
            "positive_ratio": sentiment_data.get('positive_ratio', 0.0),
            "negative_ratio": sentiment_data.get('negative_ratio', 0.0),
            "sentiment_trend": sentiment_data.get('sentiment_trend', 'NEUTRAL')
        }
        
        self.run_query(query, params)
        return True
    
    def create_market_relationship(self, ticker, related_ticker, relationship_type, properties):
        """Create a relationship between companies in the market."""
        query = """
        MATCH (c1:Company {ticker: $ticker})
        MATCH (c2:Company {ticker: $related_ticker})
        CREATE (c1)-[r:%s]->(c2)
        SET r += $properties
        """ % relationship_type
        
        params = {
            "ticker": ticker,
            "related_ticker": related_ticker,
            "properties": properties
        }
        
        self.run_query(query, params)
        return True
    
    def store_peer_comparison(self, ticker, peer_data):
        """Store peer comparison data for a company."""
        if not peer_data or not peer_data.get('peers'):
            return None
        
        # Store the comparison metrics
        query = """
        MATCH (c:Company {ticker: $ticker})
        MERGE (p:PeerComparison {ticker: $ticker})
        SET p.metrics = $metrics,
            p.timestamp = datetime()
        MERGE (c)-[:HAS_PEER_COMPARISON]->(p)
        """
        
        params = {
            "ticker": ticker,
            "metrics": peer_data.get('metrics', {})
        }
        
        self.run_query(query, params)
        
        # Create peer relationships
        for peer in peer_data.get('peers', []):
            peer_ticker = peer.get('ticker')
            if peer_ticker and peer_ticker != ticker:
                similarity = peer.get('similarity', 0.5)
                self.create_market_relationship(
                    ticker, 
                    peer_ticker, 
                    "HAS_PEER", 
                    {"similarity": similarity}
                )
        
        return True
    
    def get_company_by_ticker(self, ticker):
        """Get a company node by ticker symbol."""
        query = """
        MATCH (c:Company {ticker: $ticker})
        RETURN c
        """
        
        params = {"ticker": ticker}
        
        try:
            result = self.run_query(query, params)
            record = result.single()
            if record:
                return dict(record["c"])
            return None
        except Exception as e:
            logger.error(f"Error retrieving company {ticker}: {e}")
            return None
            
    def semantic_search(self, query_text, limit=5):
        """Perform semantic search on text chunks in the graph."""
        # This is a placeholder - in a real implementation, 
        # we would use vector embeddings or a full-text index
        search_query = """
        MATCH (c:TextChunk)
        WHERE c.content CONTAINS $search_term
        RETURN c.content AS content, c.chunk_id AS chunk_id
        LIMIT $limit
        """
        
        params = {
            "search_term": query_text,
            "limit": limit
        }
        
        try:
            result = self.run_query(search_query, params)
            return [{"content": record["content"], "id": record["chunk_id"]} for record in result]
        except Exception as e:
            logger.error(f"Error performing semantic search: {e}")
            return []
    
    def store_document(self, company_ticker, document_data):
        """
        Store a document (annual report, filing, transcript) in the knowledge graph.
        
        Args:
            company_ticker (str): Company ticker symbol
            document_data (dict): Document metadata and content
        """
        try:
            # Create unique document ID
            doc_id = f"{company_ticker}_{document_data['type']}_{document_data.get('date', datetime.now().strftime('%Y%m%d'))}"
            
            query = """
            MATCH (c:Company {ticker: $ticker})
            MERGE (d:Document {id: $doc_id})
            SET d += $properties
            MERGE (c)-[:HAS_DOCUMENT]->(d)
            """
            
            properties = {
                "id": doc_id,
                "type": document_data["type"],
                "title": document_data.get("title", ""),
                "date": document_data.get("date", datetime.now().strftime("%Y-%m-%d")),
                "source": document_data.get("source", ""),
                "url": document_data.get("url", ""),
                "content": document_data.get("content", ""),
                "sentiment_score": document_data.get("sentiment_score", 0.0),
                "last_updated": datetime.now().isoformat()
            }
            
            self.run_query(query, {
                "ticker": company_ticker,
                "doc_id": doc_id,
                "properties": properties
            })
            
            # Store text chunks for semantic search if content exists
            if document_data.get("content"):
                self.store_text_chunks(
                    doc_id,
                    "Document",
                    self._create_text_chunks(document_data["content"], doc_id)
                )
            
            return True
        except Exception as e:
            logger.error(f"Error storing document for {company_ticker}: {e}")
            return False
    
    def store_transcript(self, company_ticker, transcript_data):
        """
        Store an earnings call transcript with special processing.
        
        Args:
            company_ticker (str): Company ticker symbol
            transcript_data (dict): Transcript data including speakers and segments
        """
        try:
            # Create unique transcript ID
            transcript_id = f"{company_ticker}_transcript_{transcript_data.get('date', datetime.now().strftime('%Y%m%d'))}"
            
            # Store basic transcript info
            query = """
            MATCH (c:Company {ticker: $ticker})
            MERGE (t:Transcript {id: $transcript_id})
            SET t += $properties
            MERGE (c)-[:HAS_TRANSCRIPT]->(t)
            """
            
            properties = {
                "id": transcript_id,
                "type": "earnings_call",
                "title": transcript_data.get("title", ""),
                "date": transcript_data.get("date", datetime.now().strftime("%Y-%m-%d")),
                "quarter": transcript_data.get("quarter", ""),
                "year": transcript_data.get("year", ""),
                "sentiment_score": transcript_data.get("sentiment_score", 0.0),
                "last_updated": datetime.now().isoformat()
            }
            
            self.run_query(query, {
                "ticker": company_ticker,
                "transcript_id": transcript_id,
                "properties": properties
            })
            
            # Store speaker segments
            if transcript_data.get("segments"):
                for segment in transcript_data["segments"]:
                    self._store_transcript_segment(transcript_id, segment)
            
            return True
        except Exception as e:
            logger.error(f"Error storing transcript for {company_ticker}: {e}")
            return False
    
    def _store_transcript_segment(self, transcript_id, segment):
        """Store a transcript segment with speaker information."""
        query = """
        MATCH (t:Transcript {id: $transcript_id})
        CREATE (s:TranscriptSegment {
            id: $segment_id,
            speaker: $speaker,
            role: $role,
            content: $content,
            sentiment_score: $sentiment_score,
            start_time: $start_time,
            end_time: $end_time
        })
        CREATE (t)-[:HAS_SEGMENT]->(s)
        """
        
        segment_id = f"{transcript_id}_seg_{uuid.uuid4().hex[:8]}"
        
        self.run_query(query, {
            "transcript_id": transcript_id,
            "segment_id": segment_id,
            "speaker": segment.get("speaker", "Unknown"),
            "role": segment.get("role", "Unknown"),
            "content": segment.get("content", ""),
            "sentiment_score": segment.get("sentiment_score", 0.0),
            "start_time": segment.get("start_time", ""),
            "end_time": segment.get("end_time", "")
        })
    
    def _create_text_chunks(self, text, doc_id, chunk_size=1000, overlap=200):
        """Create overlapping text chunks for semantic search."""
        from Datapipeline.text_processor import TextProcessor
        
        text_processor = TextProcessor()
        return text_processor.chunk_text(text, doc_id, chunk_size, overlap)
