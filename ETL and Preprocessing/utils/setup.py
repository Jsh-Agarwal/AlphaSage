from setuptools import setup, find_packages

setup(
    name="Datapipeline",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        # Core data processing
        'pandas>=1.5.0',
        'numpy>=1.21.0',
        'scipy>=1.7.0',
        
        # Financial data sources
        'yfinance>=0.2.0',
        'ta>=0.10.0',  # Technical analysis
        'requests>=2.28.0',
        'beautifulsoup4>=4.11.0',
        'selenium>=4.1.0',
        'webdriver-manager>=3.8.0',
        'GoogleNews>=1.6.0',
        'nselib>=1.0.0',
        'edgar>=1.0.0',
        
        # NLP and ML
        'torch>=2.0.0',  # PyTorch for deep learning
        'transformers>=4.30.0',  # Hugging Face transformers
        'nltk>=3.8.0',
        'spacy>=3.5.0',  # Advanced NLP
        'scikit-learn>=1.0.0',  # Machine learning
        'sentence-transformers>=2.2.0',  # Text embeddings
        
        # Document processing
        'PyPDF2>=3.0.0',
        'pdf2image>=1.16.0',
        'pytesseract>=0.3.0',
        'Pillow>=9.0.0',
        
        # Database and storage
        'neo4j>=5.8.0',
        'pymongo>=4.3.0',  # For caching and document storage
        
        # Visualization
        'matplotlib>=3.6.0',
        'seaborn>=0.12.0',
        'plotly>=5.13.0',  # Interactive visualizations
        'dash>=2.8.0',  # Web dashboards
        
        # API and web
        'fastapi>=0.95.0',  # API framework
        'uvicorn>=0.21.0',  # ASGI server
        
        # Utilities
        'python-dotenv>=0.21.0',
        'tqdm>=4.65.0',
        'uuid>=1.30',
        'schedule>=1.1.0',  # For scheduling tasks
        'loguru>=0.7.0',  # Better logging
        
        # Optional: Advanced analytics
        'groq>=0.4.0',  # For GROQ integration
        'statsmodels>=0.13.0',  # Statistical analysis
    ],
    extras_require={
        'dev': [
            'pytest>=7.3.0',
            'pytest-cov>=4.0.0',
            'pytest-asyncio>=0.21.0',
            'black>=23.3.0',
            'flake8>=6.0.0',
            'mypy>=1.2.0',
        ],
    },
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'findata=Datapipeline.cli:main',
        ],
    },
)