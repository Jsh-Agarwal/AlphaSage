# # from typing import List, Optional
# # from pydantic import BaseModel, Field
# # from agno.agent import Agent
# # from agno.models.google import Gemini
# # from agno.tools.wikipedia import WikipediaTools
# # from agno.tools.duckduckgo import DuckDuckGoTools
# # from agno.tools.yfinance import YFinanceTools
# # import os
# # from dotenv import load_dotenv
# # from google import genai

# # # Load environment variables
# # load_dotenv()

# # # Set up Google API credentials
# # os.environ['GOOGLE_API_KEY'] = os.getenv("GEMINI_API_KEY")
# # api_key = os.getenv("GEMINI_API_KEY")
# # client = genai.Client(api_key=api_key)

# # # Define the response model structure
# # class CompanyInfo(BaseModel):
# #     name: str = Field(..., description="Name of the company")
# #     location: str = Field(..., description="Headquarters location of the company")
# #     industry: str = Field(..., description="Industry the company operates in")
# #     description: str = Field(..., description="Brief description of what the company does")
# #     founded: Optional[str] = Field(None, description="When the company was founded")
# #     key_products: List[str] = Field(..., description="Main products or services offered by the company")
# #     summary: str = Field(..., description="Comprehensive summary about the company based on collected data")

# # # Create the agent with structured output
# # agent = Agent(
# #     model=Gemini(id="gemini-2.0-flash"),
# #     tools=[
# #         WikipediaTools(),
# #         DuckDuckGoTools(),
# #         YFinanceTools(stock_price=False, analyst_recommendations=False, company_info=True, company_news=False),
# #     ],
# #     show_tool_calls=False,
# #     instructions=[
# #         'Provide comprehensive information about the company in a structured format.',
# #         'Focus on location, business activities, and general information rather than technical financial data.',
# #         'Collect and summarize the information in a clear, concise format.'
# #     ],
# #     response_model=CompanyInfo,
# #     use_json_mode=True,
# # )



# # # Example usage
# # if __name__ == "__main__":
# #     company_name = input("Enter a company name: ")
# #     print(agent.run(company_name))

# from typing import List, Optional
# from pydantic import BaseModel, Field
# from agno.agent import Agent
# from agno.models.google import Gemini
# from agno.tools.wikipedia import WikipediaTools
# from agno.tools.duckduckgo import DuckDuckGoTools
# from agno.tools.yfinance import YFinanceTools
# import os
# from dotenv import load_dotenv
# from google import genai
# import json  # Import json module

# # Load environment variables
# load_dotenv()

# # Set up Google API credentials
# os.environ['GOOGLE_API_KEY'] = os.getenv("GEMINI_API_KEY")
# api_key = os.getenv("GEMINI_API_KEY")
# client = genai.Client(api_key=api_key)

# # Define the response model structure
# class CompanyInfo(BaseModel):
#     name: str = Field(..., description="Name of the company")
#     location: str = Field(..., description="Headquarters location of the company")
#     industry: str = Field(..., description="Industry the company operates in")
#     description: str = Field(..., description="Brief description of what the company does")
#     founded: Optional[str] = Field(None, description="When the company was founded")
#     key_products: List[str] = Field(..., description="Main products or services offered by the company")
#     summary: str = Field(..., description="Comprehensive summary about the company based on collected data")

# # Create the agent with structured output
# agent = Agent(
#     model=Gemini(id="gemini-2.0-flash"),
#     tools=[
#         WikipediaTools(),
#         DuckDuckGoTools(),
#         YFinanceTools(stock_price=False, analyst_recommendations=False, company_info=True, company_news=False),
#     ],
#     show_tool_calls=False,
#     instructions=[
#         'Provide comprehensive information about the company in a structured format.',
#         'Focus on location, business activities, and general information rather than technical financial data.',
#         'Collect and summarize the information in a clear, concise format.'
#     ],
#     response_model=CompanyInfo,
#     use_json_mode=True,
# )

# # Example usage
# if __name__ == "__main__":
#     company_name = input("Enter a company name: ")
#     response = agent.run(company_name)

#     # Convert response content to structured JSON format and print it
#     response_json = response.content.dict()  # Convert Pydantic model to a dictionary
#     formatted_json = json.dumps(response_json, indent=4)  # Format it as a pretty-printed JSON string
#     print(formatted_json)

from typing import List, Optional
from pydantic import BaseModel, Field
from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.wikipedia import WikipediaTools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.yfinance import YFinanceTools
import os
from dotenv import load_dotenv
from google import genai
import json
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas


# Load environment variables
load_dotenv()

# Set up Google API credentials
os.environ['GOOGLE_API_KEY'] = os.getenv("GEMINI_API_KEY")
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# Define the response model structure
class CompanyInfo(BaseModel):
    name: str = Field(..., description="Name of the company")
    location: str = Field(..., description="Headquarters location of the company")
    industry: str = Field(..., description="Industry the company operates in")
    description: str = Field(..., description="Brief description of what the company does")
    founded: Optional[str] = Field(None, description="When the company was founded")
    key_products: List[str] = Field(..., description="Main products or services offered by the company")
    summary: str = Field(..., description="Comprehensive summary about the company based on collected data")

# Create the agent with structured output
agent = Agent(
    model=Gemini(id="gemini-2.0-flash"),
    tools=[
        WikipediaTools(),
        DuckDuckGoTools(),
        YFinanceTools(stock_price=False, analyst_recommendations=False, company_info=True, company_news=False),
    ],
    show_tool_calls=False,
    instructions=[
        'Provide comprehensive information about the company in a structured format.',
        'Focus on location, business activities, and general information rather than technical financial data.',
        'Collect and summarize the information in a clear, concise format.'
    ],
    response_model=CompanyInfo,
    use_json_mode=True,
)

# Function to create the PDF
def create_pdf(data: dict, filename: str):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter  # Default page size
    
    # Set up a starting point for the content
    x = 50
    y = height - 50  # Start from the top of the page
    
    # Loop through the JSON data and add it to the PDF
    for key, value in data.items():
        # Add the header (key) with a larger font
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.black)
        c.drawString(x, y, f"{key}:")
        y -= 20
        
        # Add the content (value) with a normal font
        c.setFont("Helvetica", 10)
        if isinstance(value, list):
            # If the value is a list (e.g., key_products), join the items
            value = "\n".join(value)
        c.drawString(x, y, f"{value}")
        y -= 40  # Move down for the next section
        
        # Check if we've reached the bottom of the page
        if y < 100:
            c.showPage()  # Start a new page if needed
            y = height - 50  # Reset y position for new page
    
    # Save the PDF file
    c.save()

# Example usage
if __name__ == "__main__":
    company_name = input("Enter a company name: ")
    response = agent.run(company_name)

    # Convert response content to structured JSON format using model_dump()
    response_json = response.content.model_dump()  # Use model_dump() instead of dict()

    # Create the PDF file
    create_pdf(response_json, "company_info.pdf")

    print("PDF created successfully!")
