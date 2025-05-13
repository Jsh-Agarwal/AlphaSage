from crewai import Agent, Task, Crew
from crewai_tools import PDFSearchTool
from dotenv import load_dotenv
import os

# 1. Load environment variables
load_dotenv()

# 2. Initialize PDFSearchTool with Gemini configuration
pdf_tool = PDFSearchTool(
    pdf_path='./documents',
    config={
        'llm': {
            'provider': 'google',
            'config': {
                'model': 'models/gemini-pro',
                'api_key': os.getenv('GEMINI_API_KEY'),  # From .env
                'temperature': 0.3
            }
        }
    }
)

# 3. Create PDF Research Agent
pdf_agent = Agent(
    role='Senior PDF Analyst',
    goal='Extract and analyze information from PDF documents',
    backstory="""You're an expert at finding key information in complex PDF documents,
    with special training in academic papers and technical documentation.""",
    tools=[pdf_tool],
    verbose=True
)

# 4. Create Search Task
pdf_task = Task(
    description="""Analyze the PDF document and:
    1. Find all mentions of 'dummy' or 'PDF'
    2. Extract the surrounding context (1 paragraph before and after)
    3. Identify which page each mention appears on""",
    agent=pdf_agent,
    expected_output="""Markdown formatted report containing:
    - List of found terms
    - Page numbers
    - Context paragraphs
    - Summary of findings""",
    tools=[pdf_tool]
)

# 5. Create and execute Crew
crew = Crew(
    agents=[pdf_agent],
    tasks=[pdf_task],
    verbose=2
)

# 6. Run the task
print("Starting PDF analysis...")
result = crew.kickoff()

# 7. Display results
print("\n=== ANALYSIS RESULTS ===")
print(result)