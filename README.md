# AlphaSage
AI-Powered Financial Analysis for Indian Markets

Project Summary:
AlphaSage is a cutting-edge AI-powered financial intelligence platform targeting the Indian listed markets, where hidden alpha lies within unstructured disclosures. The platform combines NLP-driven document understanding with automated financial modeling to transform scattered investor-facing documents into actionable insights and valuations — at scale.
 We’re building an end-to-end system that ingests investor presentations, regulatory filings, MD&A, and call transcripts to deliver:
Deep KPI extraction: Automatically extracting key financial metrics and non-financial drivers from corporate disclosures.
Assumption-driven scenario models: Generating dynamic financial models (3-statement, Scenario analysis , IRR) based on document-derived drivers.
Real-time event alerts and thematic intelligence: Monitoring real-time corporate events (fundraises, Key developments ,new orders) to provide actionable investment insights.
Solution Overview:
The platform is an AI-driven tool designed to provide scenario-based financial modeling for Indian listed companies. It allows users to upload investor documents (PDFs, scanned reports, HTML), which are processed through an intelligent parsing pipeline.
The solution focuses on dynamically building financial models based on key drivers such as capacity utilization, pricing trends, working capital movements, and macroeconomic factors. The platform supports scenario analysis with base, bull, and bear case simulations, helping users visualize the impact of various assumptions on the company’s financial performance.
The interactive scenario engine allows users to adjust assumptions and simulate different business outcomes, linking these assumptions to key financial outputs like Revenue, EBITDA, EPS, and other financial metrics. Real-time alerts are triggered based on new disclosures like fundraising events, new orders, or capex announcements, enabling users to stay informed of any developments that could affect their scenario models.
The platform uses lightweight AI workflows combining document parsing, semantic search (via Gemini API + ChromaDB), and scenario modeling. It extracts KPIs and disclosures using fine-tuned LLMs and LayoutLMv3, while LangChain and LangGraph enable assumption-based simulations and real-time alerts on material events.
