# import os
# from flask import Flask, request, jsonify

# from agno.agent import Agent
# from agno.models.google import Gemini
# from agno.tools.reasoning import ReasoningTools
# from agno.tools.yfinance import YFinanceTools
# from agno.tools import tool

# from crewai import Crew, Agent, Task, LLM
# from crewai_tools import (
#     SerperDevTool,
#     DirectoryReadTool,
#     FileReadTool,
#     WebsiteSearchTool,
#     ScrapeWebsiteTool,
#     ScrapeElementFromWebsiteTool,
#     RagTool,
#     PDFSearchTool,
# )
# # from crewai.tools import tool

# from dotenv import load_dotenv
# load_dotenv()

# app = Flask(__name__)

# # topic = "akash  pawar depleting groundwater"

# llm = LLM(
#     model="gemini/gemini-2.0-flash",
# )

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

# @tool("Yfinance tool")
# def my_secret_code_tool(input_text: str) -> str:
#     """
#     this tool is used to access....

#     :param input_text: str, input text for which to retrieve secret code
#     """
#     return ...



# # rag_tool.add(data_type="directory", source="./documents")
# # pdf_tool = PDFSearchTool(
# #     pdf_path='./documents',
# #     config={'chunk_size': 1000}
# # )

# # result = crew.kickoff(inputs= {"topic" : topic})
# # print(result)


# @app.route("/query", methods=["POST"])
# def query():
#     try:
#         request_body = request.json
#         query = request_body.get("query")

#         finance_agent = agent = Agent(
#     model=Gemini(id="gemini-2.0-flash"),
#     tools=[
#         ReasoningTools(add_instructions=True),
#         YFinanceTools(
#             stock_price=True,
#             analyst_recommendations=True,
#             company_info=True,
#             company_news=True
#         ),
#         my_secret_code_tool,  # Include custom tool
#     ],
#     instructions=[
#         "Use tables to display data",
#         "Only output the report, no other text",
#     ],
#     markdown=True,
# )

#         # Agent 1 researcher
#         rag_agent = Agent(
#             role="expert in extracting useful information from provided documents",
#             goal=f"Research, analyze, and synthesize comprehensive information on {query} from provided sources",
#             backstory="""
#             You're an expert research analyst with advanced research skills. You are provided tools to access important documents,
#             documents include annual reports,presentations that a company releases after each quarter encompassing important results and details regarding the business in that quarter. transcripts of the concalls held after every quarter earnings are released. these concalls are between management and the investors. 
#             You excel at finding, analyzing, and synthesizing information from 
#             provided sources using provided tools. You provide 
#             well-organized research briefs with proper citations 
#             and sources. Your analysis includes both 
#             raw data and interpreted insights, making complex 
#             information accessible and actionable. validate data and eliminate erroneous or null values
#             include facts and figures and values.
#             your research must be extensive and exhaustive
#             """,
#             verbose=True,
#             allow_delegation=False,
#             tools=[rag_tool],
#             llm=llm,
#         )

#         web_search_agent = Agent(
#             role="expert in web searching and scraping",
#             goal=f"Research, analyze, and synthesize comprehensive information on {query} from provided online sources",
#             backstory="""
#             You're an expert research analyst with advanced research skills.
#             You excel at finding, analyzing, and synthesizing information from 
#             provided sources using provided tools. You provide 
#             well-organized research briefs with proper citations 
#             and sources. Your analysis includes both 
#             raw data and interpreted insights, making complex 
#             information accessible and actionable. validate data and eliminate erroneous or null values
#             include facts and figures and values.
#             your research must be extensive and exhaustive
#             """,
#             verbose=True,
#             allow_delegation=False,
#             tools=[search_tool, scrape_tool, element_scrape_tool],
#             llm=llm,
#         )
# # annual reports,presentations that a company releases after each quarter encompassing important results and details regarding the business in that quarter. transcripts of the concalls held after every quarter earnings are released. these concalls are between management and the investors. 
#         # search_tool, scrape_tool, element_scrape_tool, 

#         # Agent 2 Content Creator
#         # content_writer = Agent(
#         #     role="Content Formatter",
#         #     goal="Format data into structured markdown. make use of tables wherever necessary",
#         #     backstory="You're a skilled content writer specialized in creating "
#         #     "engaging, accessible content from technical research. "
#         #     "You work closely with the Senior Research Analyst and excel at maintaining the perfect "
#         #     "balance between informative and entertaining writing, "
#         #     "while ensuring all facts and citations from the research "
#         #     "are properly incorporated. You have a talent for making "
#         #     "complex topics approachable without oversimplifying them by presenting them in a more digestible format making use of tables wherever necessary. do not be extremely wordy",
#         #     verbose=True,
#         #     allow_delegation=False,
#         #     llm=llm,
#         # )

#         content_writer = Agent(
#             role="Content Formatter",
#             goal="Format data into structured JSON. Ensure the JSON is clean, well-formatted, and includes nested structure where appropriate.",
#             backstory="You're a skilled content writer specialized in converting technical research into structured JSON. "
#                     "You work closely with the Senior Research Analyst and excel at transforming complex information into clear, machine-readable formats. "
#                     "Ensure all key insights are captured as fields or nested elements, avoiding unnecessary verbosity. "
#                     "Avoid using markdown or natural language summaries — the output should be pure JSON.",
#             verbose=True,
#             allow_delegation=False,
#             llm=llm,
#         )

#         # decision_agent = Agent(
#         #     role="Agent Decider Agent",
#         #     goal="based on the user query, select the agents best suited to provide the response. make use of those agents thereafter to aggregate valuable research and data insights",
#         #     backstory="""
#         #         you are an expert at orchestrating usages of available agents at hand making use of the most suitable given user query.
#         #         I will reward you with 10,000 dollars for efficient and accurate work
#         #     """,
#         #     verbose=True,
#         #     allow_delegation=False,
#         #     llm=llm,
#         # )

#         # researcher task
#         research_tasks = Task(
#             description=(
#                 """  
#                 0. prioritize answering user query and being to the point.   
#                 1. Conduct comprehensive research on {query} including:
#                     - Recent developments and news
#                     - Key industry trends and innovations
#                     - Expert opinions and analyses
#                     - Statistical data and market insights
#                 2. Use the RagTool to retrieve relevant information from our internal documents:
#                     - Query the RAG tool about "recycling sector in India" to get background information
#                     - Query the RAG tool about "stock performance of recycling companies" to get financial data
#                     - Query the RAG tool about "market trends in waste management" for industry analysis
#                 3. Combine web search results with RAG tool information for a comprehensive analysis
#                 4. When using the RAG tool, be specific with your queries to get the most relevant information
#                 5. Evaluate source credibility and fact-check all information
#                 6. Organize findings into a structured research brief
#                 7. Include all relevant citations and sources, distinguishing between web sources and internal documents
#             """
#             ),
#             expected_output="""A detailed research report containing:
#                 - Executive summary of key findings
#                 - Comprehensive analysis of current trends and developments
#                 - List of verified facts and statistics
#                 - All citations and links to original sources
#                 - Clear categorization of main themes and patterns
#                 Please format with clear sections and bullet points for easy reference.""",
#             agent=senior_research_analyst,
#         )

#         # 1. Conduct comprehensive research on {topic} including:
#         #     - Recent developments and news
#         #     - Key industry trends and innovations
#         #     - Expert opinions and analyses
#         #     - Statistical data and market insights
#         # 2. Evaluate source credibility and fact-check all information
#         # 3. Organize findings into a structured research brief
#         # 4. Include all relevant citations and sources

#         # Content Writer Task
#         # Task 2 Content Writing
#         # writing_task = Task(
#         #     description=(
#         #         """
#         #     Using the research brief provided, create an engaging blog post that:
#         #     1. Transforms technical information into accessible content
#         #     2. Maintains all factual accuracy and citations from the research
#         #     3. Includes:
#         #         - Attention-grabbing introduction
#         #         - Well-structured body sections with clear headings
#         #         - Compelling conclusion
#         #     4. Preserves all source citations in [Source: URL] format
#         #     5. Includes a References section at the end
#         # """
#         #     ),
#         #     expected_output="""A polished blog post in markdown format that:
#         #     - Engages readers while maintaining accuracy
#         #     - Contains properly structured sections
#         #     - Includes Inline citations hyperlinked to the original source url
#         #     - Presents information in an accessible yet informative way
#         #     - Follows proper markdown formatting, use H1 for the title and H3 for the sub-sections""",
#         #     agent=content_writer,
#         # )

#         writing_task = Task(
#             description=(
#                 """
#                 Using the research brief provided, transform the content into a structured JSON object that:
#                 1. Converts technical information into a structured, accessible JSON format
#                 2. Maintains all factual accuracy and source citations
#                 3. Includes the following top-level keys:
#                     - "title": A concise, informative title
#                     - "introduction": A brief summary of the topic
#                     - "sections": An array of body sections, each with a "heading" and "content"
#                     - "conclusion": A final summarizing statement
#                     - "references": An array of citations, each with "title" and "url"
#                 4. Ensures that all inline citations are preserved within the relevant content fields
#                 5. Avoids markdown, natural language summary, or unnecessary narrative fluff
#                 """
#             ),
#             expected_output="""A structured JSON object with:
#                 - Clearly defined fields: title, introduction, sections, conclusion, references
#                 - Sections array where each item has a "heading" and "content"
#                 - Inline source citations embedded in content as [Source: URL]
#                 - A references array listing all sources used
#                 - Valid, readable JSON format, suitable for parsing by frontend or storage tools""",
#             agent=content_writer,
#         )



#         crew = Crew(
#             agents=[senior_research_analyst, content_writer],
#             tasks=[research_tasks, writing_task],
#             verbose=True,
#         )

#         print(f"Query  :  {query}")
#         answer = crew.kickoff(inputs={"query": query})
#         print(f"Answer :  {answer}")
#         # type(answer.to_dict())
#         print(type(str(answer)))
#         return jsonify({"success": True, "answer": str(answer)})
#     except Exception as e:
#         print(e)
#         return jsonify({"success": False, "error": str(e)})


# if __name__ == "__main__":
#     app.run(debug=True, host="0.0.0.0", port=5000)
