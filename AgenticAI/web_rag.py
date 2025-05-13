import os
from crewai_tools import WebsiteSearchTool
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings  # Updated import

# Load environment variables
load_dotenv()

# Create WebsiteSearchTool with updated configuration
wikipedia_india_tool = WebsiteSearchTool(
    website_url="https://en.wikipedia.org/wiki/India",
    config={
        "llm": {
            "provider": "google",
            "config": {
                "model": "models/gemini-2.0-flash",
                "api_key": os.getenv("GEMINI_API_KEY")
            }
        },
        "embedder": {
            "provider": "huggingface",
            "config": {
                "model": "sentence-transformers/all-MiniLM-L6-v2",
                "model_kwargs": {"device": "cpu"}  # Add device specification
            }
        }
    }
)

# Try a more specific query with date range
results = wikipedia_india_tool.run(
    "India's GDP growth in 2023 and major cultural festivals"
)

print("Wikipedia India Results:", results)