import os
from flask import Flask, request, jsonify
from crewai import Crew, Agent, Task, LLM
from crewai_tools import (
    SerperDevTool,
    ScrapeWebsiteTool,
    ScrapeElementFromWebsiteTool,
    RagTool,
)
from dotenv import load_dotenv
from flask_cors import CORS
load_dotenv()
from crewai.tools import tool

from agno.agent import Agent as AgnoAgent
from agno.models.google import Gemini
from agno.tools.reasoning import ReasoningTools
from agno.tools.yfinance import YFinanceTools
import os

app = Flask(__name__)
# CORS(app)
# CORS(app, resources={r"/*": {"origins": "*"}})
CORS(app, resources={r"/*": {"origins": "*"}}, allow_headers="*", methods=["GET", "POST", "OPTIONS"])



llm = LLM(
    model="gemini/gemini-2.0-flash",
    api_key=os.getenv("GEMINI_API_KEY"),
)

search_tool = SerperDevTool(n=10)
scrape_tool = ScrapeWebsiteTool()
element_scrape_tool = ScrapeElementFromWebsiteTool()
rag_tool = RagTool(
    config={
        "llm": {
            "provider": "google",
            "config": {
                "model": "models/embedding-001",
                "api_key": os.getenv("GEMINI_API_KEY"),
            },
        },
        "embedder": {
            "provider": "huggingface",
            "config": {"model": "sentence-transformers/all-MiniLM-L6-v2"},
        },
    }
)
# rag_tool.add(data_type="directory", source="./documents")

# insert y finance related custom tool implementation
@tool("y finance tool")
def y_finance_tool(input_text: str) -> str:
    """
    This tool is used for generating detailed reports based on user query

    :param input_text: str, input text for which to retrieve secret code
    """
    agent = AgnoAgent(
    model=Gemini(id="gemini-2.0-flash"),
    tools=[
        ReasoningTools(add_instructions=True),
        YFinanceTools(stock_price=True, analyst_recommendations=True, company_info=True, company_news=True),
    ],
    instructions=[
        "Use tables to display data",
        "Only output the report, no other text",
    ],
    markdown=True,
    )

    return agent.run(input_text)

# y_finance_agent = Agent(
#     role="financial data analyst",
#     goal="use the yfinance tool to extract useful information based on user query",
#     backstory="""
#         you are given stock pertaining data
#     """,
#     verbose=True,
#     allow_delegation=False,
#     tools=[y_finance_tool],
#     llm=llm,
# )

y_finance_agent = Agent(
    role="financial data analyst",
    goal="use the yfinance tool to extract useful information based on user query",
    backstory="""
        You are a skilled financial analyst with expertise in extracting and interpreting stock market data.
        You help users understand market trends, analyze stock performance, and make informed investment decisions
        based on historical and real-time financial data. Your expertise is in translating complex financial
        information into clear, actionable insights. you will be provided with stock data, latest news and technical indicators.
    """,
    verbose=True,
    allow_delegation=False,
    tools=[y_finance_tool],
    llm=llm,
)

rag_agent = Agent(
    role="Document Research Expert",
    goal="Extract and synthesize comprehensive information from internal documents",
    backstory="""
        You are an expert research analyst skilled in extracting insights from internal documents, including annual reports,
        quarterly presentations, and earnings call transcripts. You validate data, eliminate errors, and provide detailed,
        well-organized research briefs with citations, facts, and figures.
    """,
    verbose=True,
    allow_delegation=False,
    tools=[rag_tool],
    llm=llm,
)

web_search_agent = Agent(
    role="Web Research Expert",
    goal="Research and analyze information from online sources",
    backstory="""
        You are an expert in web-based research, skilled at finding, analyzing, and synthesizing data from credible online
        sources. You provide well-organized briefs with citations, validated data, and actionable insights, including facts
        and figures.
    """,
    verbose=True,
    allow_delegation=False,
    tools=[search_tool, scrape_tool, element_scrape_tool],
    llm=llm,
)

content_writer = Agent(
    role="Content Formatter",
    goal="Transform research into structured JSON format",
    backstory="""
        You specialize in converting complex research into clean, structured JSON. You ensure all insights are captured
        accurately in a machine-readable format, preserving citations and avoiding unnecessary narrative.
    """,
    verbose=True,
    allow_delegation=False,
    llm=llm,
)

# Define Tasks
research_task = Task(
    description="""
        1. Conduct comprehensive research on {query}, covering:
           - Recent developments and news
           - Key industry trends and innovations
           - Expert opinions and analyses
           - Statistical data and market insights
        2. Use RagTool and PDFSearchTool for internal documents:
           - Query "recycling sector in India" for background
           - Query "stock performance of recycling companies" for financial data
           - Query "market trends in waste management" for industry analysis
        3. Use web tools for external data, including YFinanceTool for financial queries
        4. Evaluate source credibility and fact-check all information
        5. Organize findings into a structured research brief
        6. Include citations, distinguishing web and internal sources
    """,
    expected_output="""
        A detailed research report containing:
        - Executive summary of key findings
        - Comprehensive analysis of trends and developments
        - Verified facts and statistics
        - Citations and links to original sources
        - Clear categorization of themes and patterns
        Formatted with clear sections and bullet points.
    """,
    agent=rag_agent,  # Primary research through documents
)

web_research_task = Task(
    description="""
        1. Complement document research with web-based research on {query}:
           - Search for recent news and developments
           - Identify industry trends and expert analyses
           - Gather statistical data and market insights
        2. Use YFinanceTool for financial queries if applicable
        3. Validate all sources and cross-check data
        4. Combine findings with document research for a unified brief
    """,
    expected_output="""
        A supplementary research brief containing:
        - Web-sourced insights and data
        - Validated facts and statistics
        - Citations to credible online sources
        - Clear alignment with document research
    """,
    agent=web_search_agent,
)

writing_task = Task(
    description="""
        Using the research briefs, create a structured JSON object:
        1. Convert insights into a clean, accessible JSON format
        2. Maintain factual accuracy and citations
        3. Include:
           - "title": Informative title
           - "introduction": Brief topic summary
           - "sections": Array of sections with "heading" and "content"
           - "conclusion": Summarizing statement
           - "references": Array of citations with "title" and "url"
        4. Embed inline citations in content as [Source: URL]
    """,
    expected_output="""
        A structured JSON object with:
        - Fields: title, introduction, sections, conclusion, references
        - Sections array with heading and content
        - Inline citations in content as [Source: URL]
        - References array listing all sources
        - Valid, readable JSON format
    """,
    agent=content_writer,
)

# Flask Route
@app.route("/query", methods=["POST"])
def query():
    try:
        request_body = request.json
        query = request_body.get("query")
        if not query:
            return jsonify({"success": False, "error": "Query is required"}), 400

        crew = Crew(
            agents=[rag_agent, web_search_agent, content_writer, y_finance_agent],
            tasks=[research_task, web_research_task, writing_task],
            verbose=True,
        )

        print(f"Processing query: {query}")
        result = crew.kickoff(inputs={"query": query})
        print(f"Result: {result}")

        return jsonify({"success": True, "answer": str(result)})
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# Run Flask App
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=7000)

# -------------------

# import os
# from flask import Flask, request, jsonify
# from dotenv import load_dotenv
# from crewai import Crew, Agent, Task, LLM
# from crewai_tools import (
#     SerperDevTool,
#     ScrapeWebsiteTool,
#     ScrapeElementFromWebsiteTool,
#     RagTool,
# )
# from agno.agent import Agent as AgnoAgent
# from agno.models.google import Gemini
# from agno.tools.reasoning import ReasoningTools
# from agno.tools.yfinance import YFinanceTools
# from crewai.tools import tool

# # Load environment variables
# load_dotenv()

# # Initialize Flask app
# app = Flask(__name__)

# # Initialize LLM (using Gemini)
# llm = LLM(
#     model="gemini/gemini-2.0-flash",
#     api_key=os.getenv("GEMINI_API_KEY"),
# )

# # Initialize tools
# search_tool = SerperDevTool(n=10)
# scrape_tool = ScrapeWebsiteTool()
# element_scrape_tool = ScrapeElementFromWebsiteTool()
# rag_tool = RagTool(
#     config={
#         "llm": {
#             "provider": "google",
#             "config": {
#                 "model": "models/embedding-001",
#                 "api_key": os.getenv("GEMINI_API_KEY"),
#             },
#         },
#         "embedder": {
#             "provider": "huggingface",
#             "config": {"model": "sentence-transformers/all-MiniLM-L6-v2"},
#         },
#     }
# )

# @tool("YFinance tool")
# def yfinance_tool(input_text: str) -> str:
#     """
#     Retrieves financial data using YFinance tools.

#     :param input_text: str, input text (e.g., stock ticker) for which to retrieve data
#     :return: str, financial data as a string
#     """
#     try:
#         yf_tools = YFinanceTools(
#             stock_price=True,
#             analyst_recommendations=True,
#             company_info=True,
#             company_news=True,
#         )
#         return yf_tools.run(input_text)
#     except Exception as e:
#         return f"Error retrieving financial data: {str(e)}"

# # Define Agents
# finance_agent = AgnoAgent(
#     model=Gemini(id="gemini-2.0-flash"),
#     tools=[
#         ReasoningTools(add_instructions=True),
#         YFinanceTools(
#             stock_price=True,
#             analyst_recommendations=True,
#             company_info=True,
#             company_news=True,
#         ),
#         yfinance_tool,
#     ],
#     instructions=[
#         "Use tables to display data",
#         "Only output the report, no other text",
#     ],
#     markdown=True,
# )

# rag_agent = Agent(
#     role="Document Research Expert",
#     goal="Extract and synthesize comprehensive information from internal documents",
#     backstory="""
#         You are an expert research analyst skilled in extracting insights from internal documents, including annual reports,
#         quarterly presentations, and earnings call transcripts. You validate data, eliminate errors, and provide detailed,
#         well-organized research briefs with citations, facts, and figures.
#     """,
#     verbose=True,
#     allow_delegation=False,
#     tools=[rag_tool],
#     llm=llm,
# )

# web_search_agent = Agent(
#     role="Web Research Expert",
#     goal="Research and analyze information from online sources",
#     backstory="""
#         You are an expert in web-based research, skilled at finding, analyzing, and synthesizing data from credible online
#         sources. You provide well-organized briefs with citations, validated data, and actionable insights, including facts
#         and figures.
#     """,
#     verbose=True,
#     allow_delegation=False,
#     tools=[search_tool, scrape_tool, element_scrape_tool],
#     llm=llm,
# )

# content_writer = Agent(
#     role="Content Formatter",
#     goal="Transform research into structured JSON format",
#     backstory="""
#         You specialize in converting complex research into clean, structured JSON. You ensure all insights are captured
#         accurately in a machine-readable format, preserving citations and avoiding unnecessary narrative.
#     """,
#     verbose=True,
#     allow_delegation=False,
#     llm=llm,
# )

# # Define Tasks
# research_task = Task(
#     description="""
#         Conduct comprehensive research on {query}, covering:
#         - Recent developments and news
#         - Key industry trends and innovations
#         - Expert opinions and analyses
#         - Statistical data and market insights
#         Use RagTool for internal documents:
#         - Query "recycling sector in India" for background
#         - Query "stock performance of recycling companies" for financial data
#         - Query "market trends in waste management" for industry analysis
#         Evaluate source credibility and fact-check all information.
#         Organize findings into a structured research brief.
#         Include citations, distinguishing web and internal sources.
#     """,
#     expected_output="""
#         A detailed research report containing:
#         - Executive summary of key findings
#         - Comprehensive analysis of trends and developments
#         - Verified facts and statistics
#         - Citations and links to original sources
#         - Clear categorization of themes and patterns
#         Formatted with clear sections and bullet points.
#     """,
#     agent=rag_agent,
# )

# web_research_task = Task(
#     description="""
#         Complement document research with web-based research on {query}:
#         - Search for recent news and developments
#         - Identify industry trends and expert analyses
#         - Gather statistical data and market insights
#         Validate all sources and cross-check data.
#         Combine findings with document research for a unified brief.
#     """,
#     expected_output="""
#         A supplementary research brief containing:
#         - Web-sourced insights and data
#         - Validated facts and statistics
#         - Citations to credible online sources
#         - Clear alignment with document research
#     """,
#     agent=web_search_agent,
# )

# writing_task = Task(
#     description="""
#         Using the research briefs, create a structured JSON object:
#         - Convert insights into a clean, accessible JSON format
#         - Maintain factual accuracy and citations
#         - Include:
#             - "title": Informative title
#             - "introduction": Brief topic summary
#             - "sections": Array of sections with "heading" and "content"
#             - "conclusion": Summarizing statement
#             - "references": Array of citations with "title" and "url"
#         - Embed inline citations in content as [Source: URL]
#     """,
#     expected_output="""
#         A structured JSON object with:
#         - Fields: title, introduction, sections, conclusion, references
#         - Sections array with heading and content
#         - Inline citations in content as [Source: URL]
#         - References array listing all sources
#         - Valid, readable JSON format
#     """,
#     agent=content_writer,
# )

# @app.route("/query", methods=["POST"])
# def query():
#     try:
#         request_body = request.json
#         query = request_body.get("query")
#         if not query:
#             return jsonify({"success": False, "error": "Query is required"}), 400

#         # Determine if query is financial (basic heuristic)
#         financial_keywords = ["stock", "finance", "market", "company", "ticker"]
#         is_financial = any(keyword in query.lower() for keyword in financial_keywords)

#         if is_financial:
#             # Handle financial query using agno's finance_agent
#             result = finance_agent.run(query)
#             return jsonify({"success": True, "answer": result})

#         # Initialize Crew for non-financial queries
#         crew = Crew(
#             agents=[rag_agent, web_search_agent, content_writer],
#             tasks=[research_task, web_research_task, writing_task],
#             verbose=True,
#         )

#         print(f"Processing query: {query}")
#         result = crew.kickoff(inputs={"query": query})
#         print(f"Result: {result}")

#         return jsonify({"success": True, "answer": str(result)})
#     except Exception as e:
#         print(f"Error: {e}")
#         return jsonify({"success": False, "error": str(e)}), 500

# if __name__ == "__main__":
#     app.run(debug=True, host="0.0.0.0", port=5000)