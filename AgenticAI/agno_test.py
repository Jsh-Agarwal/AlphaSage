# # from agno.agent import Agent
# # from agno.models.google import Gemini
# # from agno.tools.reasoning import ReasoningTools
# # from agno.tools.yfinance import YFinanceTools
# # import os
# # import json

# # from dotenv import load_dotenv
# # load_dotenv()

# # agent = Agent(
# #     model=Gemini(id="gemini-2.0-flash"),
# #     tools=[
# #         ReasoningTools(add_instructions=True),
# #         YFinanceTools(stock_price=True, analyst_recommendations=True, company_info=True, company_news=True),
# #     ],
# #     instructions=[
# #         "Use tables to display data",
# #         "Only output the report, no other text",
# #     ],
# #     markdown=True,
# # )

# # # print(agent.print_response("Write a report on NVDA", stream=True, show_full_reasoning=True, stream_intermediate_steps=True))

# # response_string = agent.run("Write a report on NVDA")
# # # print(json.dumps(response_string,4))
# # print(response_string)

# from agno.agent import Agent
# from agno.models.google import Gemini
# from agno.tools.reasoning import ReasoningTools
# from agno.tools.yfinance import YFinanceTools
# import os
# import json
# import re
# import ast

# from dotenv import load_dotenv
# load_dotenv()

# agent = Agent(
#     model=Gemini(id="gemini-2.0-flash"),
#     tools=[
#         ReasoningTools(add_instructions=True),
#         YFinanceTools(stock_price=True, analyst_recommendations=True, company_info=True, company_news=True),
#     ],
#     instructions=[
#         "Use tables to display data",
#         "Only output the report, no other text",
#     ],
#     markdown=True,
# )

# def parse_object_str_to_json(obj_str):
#     cleaned_str = re.sub(r'\b\w+\(', '{', obj_str)
#     cleaned_str = cleaned_str.replace(')', '}')
#     cleaned_str = re.sub(r'(\w+)=', r'"\1":', cleaned_str)

#     def fix_quotes(val):
#         if val in ['None', 'True', 'False'] or re.match(r'^-?\d+(\.\d+)?$', val):
#             return val
#         return f'"{val}"'

#     cleaned_str = re.sub(r':\'(.*?)\'', lambda m: ':' + fix_quotes(m.group(1)), cleaned_str)
#     cleaned_str = cleaned_str.replace("None", "null").replace("True", "true").replace("False", "false")

#     try:
#         parsed = ast.literal_eval(cleaned_str)
#         return json.dumps(parsed, indent=4)
#     except Exception as e:
#         return f"Error parsing string: {e}"

# response_string = agent.run("Write a report on NVDA")
# print(parse_object_str_to_json(str(response_string)))

from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.reasoning import ReasoningTools
from agno.tools.yfinance import YFinanceTools
import os
import json

from dotenv import load_dotenv
load_dotenv()

agent = Agent(
    model=Gemini(id="gemini-2.0-flash"),
    tools=[
        ReasoningTools(add_instructions=True),
        YFinanceTools(
            stock_price=True,
            analyst_recommendations=True,
            company_info=True,
            company_news=True
        ),
    ],
    instructions=[
        "Use tables to display data",
        "Only output the report, no other text",
    ],
    markdown=True,
)

def response_to_json(response_obj):
    if hasattr(response_obj, '__dict__'):
        def serialize(obj):
            if isinstance(obj, list):
                return [serialize(item) for item in obj]
            elif hasattr(obj, '__dict__'):
                return {k: serialize(v) for k, v in obj.__dict__.items()}
            else:
                return obj

        return json.dumps(serialize(response_obj), indent=4)
    else:
        return json.dumps({"content": str(response_obj)}, indent=4)

response = agent.run("Write a report on NVDA")
print(response_to_json(response))
