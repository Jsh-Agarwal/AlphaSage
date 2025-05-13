#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Document to Knowledge Graph Processor

This module processes documents scraped from company websites and adds their content
to a Neo4j knowledge graph for semantic search and analysis.
"""

import os
import re
import sys
import time
import logging
import json
from datetime import datetime
from pathlib import Path

import PyPDF2
from tqdm import tqdm
from neo4j import GraphDatabase

from Datapipeline.text_processor import TextProcessor
from Datapipeline.database import Neo4jDatabase
from Datapipeline.ConfigManager import ConfigManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("document_to_kg.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Process documents and add them to the knowledge graph."""
    
    def __init__(self, download_dir="downloads", neo4j=None, text_processor=None, config_path="config.json"):
        """Initialize document processor with config."""
        # Load configuration
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_all_config()
        self.download_dir = download_dir
        
        # Initialize text processor
        self.text_processor = text_processor if text_processor else TextProcessor()
        
        # Initialize Neo4j connection
        if neo4j:
            self.neo4j = neo4j
        else:
            neo4j_config = self.config.get('neo4j', {})
            self.neo4j = Neo4jDatabase(
                uri=neo4j_config.get('uri', 'bolt://localhost:7687'),
                user=neo4j_config.get('user', 'neo4j'),
                password=neo4j_config.get('password', 'password')
            )
    
    def process_pdf(self, pdf_path):
        """Extract text content from a PDF file."""
        try:
            logger.info(f"Processing PDF: {pdf_path}")
            
            # Check if file exists
            if not os.path.exists(pdf_path):
                logger.error(f"File not found: {pdf_path}")
                return None
            
            # Extract text from PDF
            text_content = ""
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                # Extract text from each page
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text_content += page.extract_text() + "\n"
            
            # Clean the text content
            text_content = self.text_processor.clean_text(text_content)
            
            logger.info(f"Extracted {len(text_content)} characters from {pdf_path}")
            return text_content
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            return None
    
    def process_document(self, document):
        """Process a document and add it to the knowledge graph."""
        try:
            logger.info(f"Processing document: {document.get('title', 'Unknown')}")
            
            # Get the filepath
            filepath = document.get('filepath')
            if not filepath:
                logger.error("Document missing filepath")
                return False
            
            # Extract text content
            if filepath.lower().endswith('.pdf'):
                text_content = self.process_pdf(filepath)
            else:
                logger.error(f"Unsupported file format: {filepath}")
                return False
            
            if not text_content:
                logger.error(f"Failed to extract text from {filepath}")
                return False
            
            # Add text content to document metadata
            document['text_content'] = text_content
            
            # Extract entities
            entities = self.text_processor.extract_entities(text_content)
            document['entities'] = entities
            
            # Analyze sentiment
            sentiment = self.text_processor.analyze_sentiment(text_content)
            document['sentiment'] = sentiment
            
            # Extract key metrics
            metrics = self.text_processor.extract_key_metrics(text_content)
            document['metrics'] = metrics
            
            # Create chunks for semantic search
            chunks = self.text_processor.chunk_text(
                text_content,
                doc_id=Path(filepath).stem,
                chunk_size=self.config.get('processing', {}).get('chunk_size', 1000),
                overlap=self.config.get('processing', {}).get('chunk_overlap', 200)
            )
            
            document['chunks'] = chunks
            
            # Store in Neo4j
            if self.neo4j and self.neo4j.driver:
                # Get company name from document metadata
                source = document.get('source', '')
                company_name = source.split('_')[0] if '_' in source else source
                
                # Store the document
                self.neo4j.store_report(company_name, document)
                
                # Store text chunks for semantic search
                self.neo4j.store_text_chunks(
                    source_id=document.get('url', filepath),
                    source_type='Report',
                    chunks=chunks
                )
                
                logger.info(f"Stored document in Neo4j: {document.get('title', 'Unknown')}")
                return True
            else:
                logger.warning("Neo4j connection not available, skipping storage")
                return False
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            return False
    
    def process_all_documents(self):
        """Process all documents in the download directory."""
        documents = []
        
        # Get all files in the download directory
        for filename in os.listdir(self.download_dir):
            filepath = os.path.join(self.download_dir, filename)
            
            # Skip directories
            if os.path.isdir(filepath):
                continue
            
            # Only process PDF files
            if filepath.lower().endswith('.pdf'):
                # Parse document type from filename
                file_parts = filename.split('_', 1)
                doc_type = file_parts[0] if len(file_parts) > 1 else "report"
                
                # Create document metadata
                document = {
                    'filepath': filepath,
                    'title': filename,
                    'type': doc_type,
                    'url': f"file://{os.path.abspath(filepath)}",
                    'source': filename.split('_')[1] if '_' in filename and len(filename.split('_')) > 1 else "Unknown"
                }
                
                documents.append(document)
        
        # Process all documents
        logger.info(f"Found {len(documents)} documents in {self.download_dir}")
        
        results = {
            'total': len(documents),
            'successful': 0,
            'failed': 0,
            'processing_time': 0
        }
        
        start_time = time.time()
        
        for doc in tqdm(documents, desc="Processing documents"):
            success = self.process_document(doc)
            if success:
                results['successful'] += 1
            else:
                results['failed'] += 1
        
        end_time = time.time()
        results['processing_time'] = end_time - start_time
        
        logger.info(f"Processed {results['successful']} out of {results['total']} documents in {results['processing_time']:.2f} seconds")
        
        return results

def main():
    """Main function to test the document processor."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Document to Knowledge Graph Processor")
    parser.add_argument("--document-dir", 
                      help="Directory containing documents to process", 
                      default="downloads")
    parser.add_argument("--config", 
                      help="Path to configuration file", 
                      default="config.json")
    args = parser.parse_args()
    
    # Initialize document processor
    processor = DocumentProcessor(config_path=args.config, download_dir=args.document_dir)
    
    # Process all documents
    results = processor.process_all_documents()
    
    # Print results
    print(f"Processing complete:")
    print(f"Total documents: {results['total']}")
    print(f"Successfully processed: {results['successful']}")
    print(f"Failed: {results['failed']}")
    print(f"Processing time: {results['processing_time']:.2f} seconds")

if __name__ == "__main__":
    main()