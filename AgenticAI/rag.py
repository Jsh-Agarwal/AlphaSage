# # from crewai_tools import RagTool
# # from dotenv import load_dotenv
# # import os

# # # Load environment variables
# # load_dotenv()

# # # Initialize RAG tool
# # # rag_tool = RagTool()
# # rag_tool = RagTool(
# #     embedding_model="google",
# #     config={
# #         "model": "models/text-embedding-004",
# #         "api_key": os.getenv("GEMINI_API_KEY")
# #     }
# # )
# # rag_tool.add(data_type="directory", source="./documents")

# # # Test query
# # test_query = "tech Wabag Limited"
# # print(f"Testing RAG tool with query: '{test_query}'")
# # result = rag_tool.run(test_query)
# # print("\nRAG Tool Result:")
# # print(result)

# from crewai_tools import RagTool
# from dotenv import load_dotenv
# import os

# # Load environment variables
# load_dotenv()

# # Initialize RAG tool with Google/Gemini embeddings
# rag_tool = RagTool(config={
#     "llm": {
#         "provider": "google",
#         "config": {
#             "model": "models/text-embedding-004",
#             "api_key": os.getenv("GEMINI_API_KEY")
#         }
#     }
# })

# # Add documents
# rag_tool.add(data_type="directory", source="./documents")

# # Test query
# test_query = "tech Wabag Limited"
# print(f"Testing RAG tool with query: '{test_query}'")
# result = rag_tool.run(test_query)
# print("\nRAG Tool Result:")
# print(result)

from crewai_tools import RagTool
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize RAG tool with LOCAL embeddings (no API required)
rag_tool = RagTool(config={
    "llm": {
        "provider": "google",
        "config": {
            "model": "models/embedding-001",
            "api_key": os.getenv("GEMINI_API_KEY")
        }
    },
    "embedder": {
        "provider": "huggingface",
        "config": {
            "model": "sentence-transformers/all-MiniLM-L6-v2"
        } 
    }
})

# Alternative: Pure local setup (recommended)
# rag_tool = RagTool(config={
#     "embedder": {
#         "provider": "huggingface",
#         "config": {
#             "model": "sentence-transformers/all-MiniLM-L6-v2"
#         }
#     }
# })

rag_tool.add(data_type="directory", source="./documents")

# Test query
test_query = "what is the company's guidance regarding revenue of the business"
print(f"Testing RAG tool with query: '{test_query}'")
result = rag_tool.run(test_query)
print("\nRAG Tool Result:")
print(result)