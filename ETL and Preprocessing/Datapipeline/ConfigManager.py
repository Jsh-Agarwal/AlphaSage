"""
Configuration Manager for the Financial Data Pipeline

This module handles loading, validating, and managing configuration settings
for the financial data ETL pipeline.
"""

import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging - set higher level for neo4j and yfinance to reduce debug output
logging.getLogger('neo4j').setLevel(logging.WARNING)
logging.getLogger('yfinance').setLevel(logging.INFO)
logging.getLogger('peewee').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manage configuration settings for the financial data pipeline."""
    
    def __init__(self, config_file="config.json"):
        """Initialize the configuration manager."""
        self.config_file = config_file
        self.config = self._load_config()
        
        # Override with environment variables if available
        self._override_from_env()
    
    def _override_from_env(self):
        """Override configuration with environment variables."""
        # Neo4j settings
        if os.getenv("NEO4J_URI"):
            self.config["neo4j"]["uri"] = os.getenv("NEO4J_URI")
        if os.getenv("NEO4J_USER"):
            self.config["neo4j"]["user"] = os.getenv("NEO4J_USER")
        if os.getenv("NEO4J_PASSWORD"):
            self.config["neo4j"]["password"] = os.getenv("NEO4J_PASSWORD")
            
        # API keys
        if os.getenv("ALPHA_VANTAGE_KEY"):
            self.config["api_keys"]["alpha_vantage"] = os.getenv("ALPHA_VANTAGE_KEY")
        if os.getenv("FINNHUB_KEY"):
            self.config["api_keys"]["finnhub"] = os.getenv("FINNHUB_KEY")
        if os.getenv("GROQ_API_KEY"):
            self.config["api_keys"]["groq"] = os.getenv("GROQ_API_KEY")
    
    def _load_config(self):
        """Load configuration from a JSON file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_file}")
                return config
            else:
                logger.warning(f"Configuration file {self.config_file} not found, using defaults")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading configuration from {self.config_file}: {e}")
            return self._get_default_config()
    
    def _get_default_config(self):
        """Get default configuration settings."""
        # Create default directories
        for dir_name in ["downloads", "cache", "logs", "reports"]:
            os.makedirs(dir_name, exist_ok=True)
            
        return {
            "api_keys": {
                "alpha_vantage": os.getenv("ALPHA_VANTAGE_KEY"),
                "finnhub": os.getenv("FINNHUB_KEY"),
                "groq": os.getenv("GROQ_API_KEY")
            },
            "neo4j": {
                "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                "user": os.getenv("NEO4J_USER", "neo4j"),
                "password": os.getenv("NEO4J_PASSWORD", "password"),
                "database": os.getenv("NEO4J_DATABASE", "neo4j"),
                "max_connection_lifetime": 3600,
                "max_connection_pool_size": 50,
                "connection_timeout": 30
            },
            "data_sources": {
                "sec_filings": True,
                "nse_data": True,
                "bse_data": True,
                "yahoo_finance": True,
                "screener_in": True,
                "money_control": True,
                "trendlyne": True,
                "news": True
            },
            "scraping": {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "request_timeout": 30,
                "chrome_driver_path": None,
                "download_path": "downloads"
            },
            "processing": {
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "max_pdf_size_mb": 50,
                "ocr_enabled": True,
                "max_threads": 5,
                "cache_dir": "cache",
                "log_dir": "logs",
                "report_dir": "reports"
            },
            "ml_models": {
                "sentiment_model": "ProsusAI/finbert",
                "ner_model": "dbmdz/bert-large-cased-finetuned-conll03-english",
                "use_gpu": True,
                "batch_size": 32,
                "max_sequence_length": 512
            },
            "api": {
                "host": "0.0.0.0",
                "port": 8000,
                "workers": 4,
                "timeout": 60,
                "cors_origins": ["*"],
                "rate_limit": 100
            }
        }
    
    def save_config(self):
        """Save current configuration to the JSON file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            logger.info(f"Saved configuration to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration to {self.config_file}: {e}")
            return False
    
    def get_neo4j_credentials(self):
        """Get Neo4j database credentials."""
        neo4j_config = self.config.get("neo4j", {})
        return {
            "uri": os.getenv("NEO4J_URI", neo4j_config.get("uri", "bolt://localhost:7687")),
            "user": os.getenv("NEO4J_USER", neo4j_config.get("user", "neo4j")),
            "password": os.getenv("NEO4J_PASSWORD", neo4j_config.get("password", "password"))
        }
    
    def get_api_key(self, service_name):
        """Get API key for a specific service."""
        api_keys = self.config.get("api_keys", {})
        return api_keys.get(service_name)
    
    def set_api_key(self, service_name, api_key):
        """Set API key for a specific service."""
        if "api_keys" not in self.config:
            self.config["api_keys"] = {}
        
        self.config["api_keys"][service_name] = api_key
        logger.info(f"Updated API key for {service_name}")
    
    def is_data_source_enabled(self, source_name):
        """Check if a specific data source is enabled."""
        data_sources = self.config.get("data_sources", {})
        return data_sources.get(source_name, False)
    
    def toggle_data_source(self, source_name, enabled=True):
        """Enable or disable a specific data source."""
        if "data_sources" not in self.config:
            self.config["data_sources"] = {}
        
        self.config["data_sources"][source_name] = enabled
        logger.info(f"{'Enabled' if enabled else 'Disabled'} data source: {source_name}")
    
    def get_scraping_settings(self):
        """Get web scraping settings."""
        return self.config.get("scraping", {})
    
    def get_processing_settings(self):
        """Get data processing settings."""
        return self.config.get("processing", {})
    
    def update_setting(self, section, key, value):
        """Update a specific configuration setting."""
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section][key] = value
        logger.info(f"Updated configuration: {section}.{key} = {value}")
    
    def get_all_config(self):
        """Get the entire configuration."""
        return self.config