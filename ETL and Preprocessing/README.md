# Financial Research Assistant ETL Pipeline

A comprehensive data engineering ETL (Extract, Transform, Load) pipeline for financial data collection, processing, and storage for AI-powered research and analysis.

## Overview

This project implements a robust data pipeline for collecting financial data from various sources, including:

- SEC EDGAR filings (10-K, 10-Q, 8-K)
- Indian exchanges (NSE and BSE)
- Yahoo Finance API
- Financial websites (Screener.in, MoneyControl, Trendlyne)
- Earnings call transcripts
- Company annual reports, presentations, and other documents
- News and market reports

The data is processed, analyzed, and stored in a Neo4j graph database to create a knowledge graph that AI agents can query for comprehensive financial research and analysis.

## Features

- **Multi-source data extraction**: Collect data from APIs, websites, PDFs, and other sources
- **Company data processing**: Comprehensive company data extraction and processing
- **Sector analysis**: Group companies by sector and analyze sector trends
- **Technical analysis**: Calculate technical indicators using TA-Lib
- **Financial ratio calculation**: Extract and compute key financial ratios
- **PDF extraction and OCR**: Process annual reports and other documents with OCR when needed
- **Knowledge graph storage**: Structure data in Neo4j for semantic querying
- **Text chunking and processing**: Break down long documents for AI analysis
- **Configurable pipeline**: Customize data sources, processing parameters, and more

## Requirements

- Python 3.8+
- Neo4j database
- Chrome WebDriver (for website scraping)
- Tesseract OCR (for PDF processing)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/financial-research-assistant.git
   cd financial-research-assistant
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

3. Install Tesseract OCR:
   - Windows: Download and install from https://github.com/UB-Mannheim/tesseract/wiki
   - Mac: `brew install tesseract`
   - Linux: `sudo apt install tesseract-ocr`

4. Set up Neo4j:
   - Download and install Neo4j from https://neo4j.com/download/
   - Create a new database with username/password
   - Update `config.json` with your Neo4j credentials

5. Set up Chrome WebDriver:
   - Download the appropriate version for your Chrome browser from https://chromedriver.chromium.org/downloads
   - Update the `chrome_driver_path` in `config.json`

## Configuration

The pipeline is configurable through `config.json`:

```json
{
    "api_keys": {
        "alpha_vantage": null,
        "finnhub": null,
        "iex_cloud": null,
        "intrinio": null
    },
    "neo4j": {
        "uri": "bolt://localhost:7687",
        "user": "neo4j",
        "password": "password"
    },
    "data_sources": {
        "sec_filings": true,
        "nse_data": true,
        "bse_data": true,
        "yahoo_finance": true,
        "screener_in": true,
        "money_control": true,
        "trendlyne": true,
        "news": true
    },
    "scraping": {
        "user_agent": "Financial Research Assistant/1.0",
        "request_timeout": 30,
        "chrome_driver_path": null,
        "download_path": "./downloads"
    },
    "processing": {
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "max_pdf_size_mb": 50,
        "ocr_enabled": true,
        "max_threads": 5
    }
}
```

## Usage

The pipeline can be run through the command-line interface:

### Process a single company

```
python main.py company AAPL --exchange NASDAQ
```

### Process multiple companies

```
python main.py batch tickers.txt --exchange NYSE
```

### Process a sector

```
python main.py sector "Technology" --tickers AAPL MSFT GOOGL AMZN META
```

### Process multiple sectors

```
python main.py sector-analysis sectors.json
```

### Process specific filings

```
python main.py filing AAPL --filing-type "annual report" --limit 3
```

### Verify connections

```
python main.py verify
```

### Manage configuration

```
python main.py config show
python main.py config create --config-file custom_config.json
```

## Project Structure

- `main.py`: Main entry point for the ETL pipeline
- `Datapipeline/`: Core pipeline modules
  - `etl.py`: Main ETL functionality and data extraction
  - `database.py`: Neo4j database interaction
  - `text_processor.py`: Text processing and chunking
- `config.json`: Configuration file
- `tickers.txt`: Example list of stock tickers
- `sectors.json`: Example sector-to-tickers mapping

## Knowledge Graph Schema

The data is stored in a Neo4j graph database with the following schema:

- `Company` nodes: Basic company information
- `Price` nodes: Historical stock prices
- `Filing` nodes: SEC and other regulatory filings
- `News` nodes: News articles about companies
- `Report` nodes: Annual reports and other documents
- `TextChunk` nodes: Chunks of text for semantic search
- `Sector` nodes: Industry sectors
- `BalanceSheet`, `IncomeStatement`, `CashFlow` nodes: Financial statements

## Testing

To verify the pipeline functionality:

1. Test the connection to data sources:
   ```
   python main.py verify
   ```

2. Process a test company:
   ```
   python main.py company AAPL --exchange NASDAQ
   ```

3. Check the Neo4j database for stored data.

## Extending the Pipeline

You can extend the pipeline by:

1. Adding new data sources in `etl.py`
2. Implementing new analysis methods
3. Enhancing the database schema in `database.py`
4. Adding new text processing techniques in `text_processor.py`

## License

[Specify your license]

## Contributors

[Your Name]

## Acknowledgements

- Yahoo Finance API
- SEC EDGAR
- NSE and BSE data providers
- TA-Lib for technical analysis
- Neo4j for graph database