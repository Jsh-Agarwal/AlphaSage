import os
import sys
import argparse
import logging
import warnings

# Suppress specific deprecation warnings more aggressively
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*'Ticker.earnings' is deprecated.*")

# Set up logging with appropriate levels to reduce noise
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("etl_pipeline.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Reduce verbosity of external libraries
logging.getLogger('neo4j').setLevel(logging.WARNING)
logging.getLogger('yfinance').setLevel(logging.WARNING)  # Changed to WARNING level
logging.getLogger('peewee').setLevel(logging.WARNING)
logging.getLogger('transformers').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

from Datapipeline.etl import run_cli

if __name__ == "__main__":
    # Make sure the downloads directory exists
    os.makedirs("downloads", exist_ok=True)
    
    # Run the command-line interface
    run_cli()