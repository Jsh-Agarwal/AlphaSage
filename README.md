# AlphaSage: AI-Powered Financial Analysis for Indian Markets

AlphaSage is a cutting-edge AI-powered financial intelligence platform targeting the Indian listed markets. The platform transforms unstructured disclosures and investor-facing documents into actionable insights and valuations at scale, uncovering hidden alpha in the market.

## Project Overview

AlphaSage combines NLP-driven document understanding with automated financial modeling to process:

- Investor presentations
- Regulatory filings
- MD&A (Management Discussion and Analysis)
- Call transcripts

The platform delivers comprehensive financial intelligence through:

- **Deep KPI Extraction**: Automatically extracts key financial metrics and non-financial drivers from corporate disclosures
- **Assumption-driven Scenario Models**: Generates dynamic 3-statement financial models and scenario analyses based on document-derived drivers
- **Real-time Event Alerts**: Monitors corporate events (fundraises, key developments, new orders) to provide actionable investment insights

## Architecture & Components

### Document Ingestion Pipeline

- Supports multiple input formats (PDFs, scanned reports, HTML)
- Processes documents through an intelligent parsing system

### AI-Driven Analysis Engine

- **Document Parsing**: Extracts structured data from unstructured documents
- **Semantic Search**: Utilizes Gemini API + ChromaDB to understand document context
- **KPI Extraction**: Uses fine-tuned LLMs and LayoutLMv3 to identify key metrics
- **LangChain & LangGraph**: Powers assumption-based simulations and alerts

### Scenario Modeling System

- Builds financial models based on key business drivers:
  - Capacity utilization
  - Pricing trends
  - Working capital movements
  - Macroeconomic factors
- Supports base, bull, and bear case simulations
- Visualizes impact of various assumptions on financial performance

### Real-time Alert System

- Triggers notifications based on:
  - Fundraising events
  - New orders
  - Capex announcements
  - Other material developments

## Features

- **Comprehensive Document Analysis**: Processes various financial documents to extract actionable insights
- **Dynamic Financial Modeling**: Creates scenario-based financial projections with adjustable parameters
- **Interactive Scenario Engine**: Allows users to modify assumptions and visualize different business outcomes
- **Real-time Monitoring**: Provides alerts on key developments affecting investment decisions
- **Deep Market Coverage**: Focuses on under-researched small and mid-cap companies in the Indian market

## Project Structure & Setup

The AlphaSage project is organized into four key directories, each serving a specific purpose in the financial analysis pipeline:

### `/AgenticAI`

Contains the AI agent components for autonomous financial analysis.

- **Agent Workflows**: Implementation of LangChain and LangGraph for orchestrating analysis tasks
- **Knowledge Bases**: Vector stores and retrieval augmented generation components
- **Reasoning Engines**: Modules for financial reasoning and inference

### `/backend`

Houses the backend API and server components.

- **API Routes**: Endpoints for frontend communication
- **Controllers**: Business logic implementation
- **Middleware**: Authentication and request processing components
- **Database Models**: Data schemas and database interactions

### `/ETL and Preprocessing`

Manages data ingestion, transformation, and loading processes.

- **Document Parsers**: Tools for extracting text from different document formats
- **Data Transformers**: Components for structuring extracted information
- **Data Loaders**: Database and vector store population utilities
- **KPI Extractors**: Financial metrics identification systems

### `/frontend`

Contains the user interface components.

- **Components**: Reusable UI elements
- **Pages**: Application page templates
- **Public Assets**: Static files like images and fonts
- **State Management**: Frontend data and state handling

## Complete Setup Instructions

To set up the project:

1. Clone the repository:

   ```bash
   git clone https://github.com/Jsh-Agarwal/AlphaSage.git
   cd AlphaSage
   ```
2. Set up Python environment for backend and AI components:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Set up Node.js environment for frontend:

   ```bash
   cd frontend
   npm install
   cd ..
   ```
4. Configure environment variables:

   ```bash
   # Create environment file
   cp .env.example .env

   # Edit .env file with your specific configuration
   # Required variables include:
   # - GEMINI_API_KEY: For document analysis
   # - DATABASE_URL: For data storage
   # - CHROMA_DB_PATH: For vector database storage
   ```
5. Start the development services:

   ```bash
   # Start backend server
   python backend/server.py

   # In a separate terminal, start the frontend
   cd frontend
   npm start
   ```

## Usage

1. Access the application:
   Open your browser and navigate to `http://localhost:3000` (or the configured port).
2. Upload Documents:

   - Use the interface to upload financial documents for analysis
   - The system will process and extract key information through the ETL pipeline
3. Interact with Models:

   - The AgenticAI components will analyze the documents and generate insights
   - Adjust assumptions to create different financial scenarios
   - View the impact on key financial metrics
   - Set up alerts for specific events or thresholds

## Component Dependencies

Each component of AlphaSage has specific dependencies:

- **ETL and Preprocessing**:

  - PyMuPDF, pytesseract, pdf2image for document processing
  - langchain for document chunking and processing
- **AgenticAI**:

  - Google Gemini API for advanced text processing
  - ChromaDB for vector database operations
  - LangChain for workflow orchestration
  - PyTorch and Hugging Face Transformers for model hosting
- **backend**:

  - FastAPI/Flask for API development
  - SQLAlchemy for database operations
  - JWT for authentication
- **frontend**:

  - React for UI components
  - Streamlit for data visualization dashboards
  - Chart.js for interactive financial charts

## Team

- **Jsh Agarwal** – Lead ML Engineer (Finance + GenAI specialization)
- **Jiten Ganwani** – Backend & API Architecture (Cloud + LangChain backend)
- **Maaz Malik** – Data Engineer (End to End Ingestion pipeline)
- **Khush Kothari** – Domain Expertise (FSA and affiliated work)
- **Madhura Kanfade** – Frontend + UX (React, Streamlit)

## Recognition

- 1st Prize at the National Hackathon organized by SVNIT Surat, in partnership with Odoo and Vijaybhoomi University
- Strategic guidance from Endeavor Global, a U.S.-based hedge fund

## Contribution Guidelines

We welcome contributions to AlphaSage! To contribute:

1. Fork the repository.
2. Create a new branch for your feature or bug fix:
   ```bash
   git checkout -b feature-name
   ```
3. Commit your changes:
   ```bash
   git commit -m "Add feature-name"
   ```
4. Push to your branch:
   ```bash
   git push origin feature-name
   ```
5. Open a pull request.

Please ensure your code adheres to the project's coding standards and includes appropriate tests.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Acknowledgments

Special thanks to all contributors, the open-source community, and our partners at SVNIT Surat, Odoo, Vijaybhoomi University, and Endeavor Global for their support.
