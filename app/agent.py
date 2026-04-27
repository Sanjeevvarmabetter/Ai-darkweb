import os
import re  # FIX 1: Added missing regex import
from typing import TypedDict, List  # FIX 1: Added missing typing imports
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

# Import your tools
from tor_tools import search_ahmia, scrape_onion_site   

load_dotenv()

# ==========================================
# Graph State
# ==========================================
class OSINTState(TypedDict):
    query: str
    plan: str
    search_queries: List[str]
    discovered_urls: List[str]
    scraped_data: str
    final_report: str

# ==========================================
# LLM Initialization
# ==========================================
llm = ChatOpenAI(
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1",
    model_name=os.getenv("OPENROUTER_MODEL"),
    max_tokens=2048,
    temperature=0.2
)

# ==========================================
# Nodes (Agents)
# ==========================================

def architect_node(state: OSINTState):
    """The Architect analyzes the query and formulates specific search terms."""
    print("----- ARCHITECT AGENT STARTING -------")
    
    prompt = ChatPromptTemplate.from_template(
        "You are the Lead OSINT Architect. The user wants to investigate: '{query}'. "
        "Your job is to define 1 to 3 highly specific search terms that would yield good results "
        "on a dark web indexer. Output ONLY a comma-separated list of search terms. No other text."
    )

    chain = prompt | llm 
    response = chain.invoke({"query": state["query"]})    
    content = response.content
    
    # NEW: Detect if the LLM spit out a safety refusal instead of search terms
    if "can't help" in content.lower() or "harmful" in content.lower() or "institutional channels" in content.lower():
        print("[!] Warning: LLM refused the prompt due to safety guardrails.")
        return {"plan": "Safety Refusal", "search_queries": []}

    search_terms = [term.strip() for term in content.split(",") if term.strip()]

    return {"plan": f"Searching for: {content}", "search_queries": search_terms}

def recon_node(state: OSINTState):
    """The recon agent executes the searches to find .onion URLs """
    print("----- RECON AGENT STARTING ------")

    all_urls = []

    for query in state["search_queries"]:
        print(f"[*] Searching Ahmia for: {query}")
        result_string = search_ahmia.invoke({"query": query})
        
        # Use regex to extract valid .onion URLs from the tool's string output
        found_urls = re.findall(r'http[s]?://[^\s,]+\.onion', result_string)
        all_urls.extend(found_urls)

    # FIX 2: Moved deduplication and return OUTSIDE the for-loop
    unique_urls = list(set(all_urls))
    print(f"[*&] Discovered: {len(unique_urls)} unique .onion urls")

    # FIX 3: Fixed typo in the state key (added underscore)
    return {"discovered_urls": unique_urls}
    

def ingestion_node(state: OSINTState):
    """The Ingestion Agent safely scrapes the discovered URLS."""
    print("----- INGESTION AGENT STARTING ------")

    # This will now safely read the urls passed by the recon node
    urls_to_scrape = state.get("discovered_urls", [])[:3]
    scraped_content_accumulator = ""

    if not urls_to_scrape:
        return {"scraped_data": "No accessible .onion URLS found during recon"}

    for url in urls_to_scrape:
        print(f"[*] Scraping: {url}")
        content = scrape_onion_site.invoke({"url": url})
        scraped_content_accumulator += f"\n\n=== CONTENT FROM {url} ===\n{content}\n"
        
    return {"scraped_data": scraped_content_accumulator}


def analyst_node(state: OSINTState):
    """The Analyst synthesizes the scraped raw data into a Threat Intel Report."""
    print("--- 📝 ANALYST AGENT STARTING ---")
    
    prompt = ChatPromptTemplate.from_template(
        "You are an expert Threat Intelligence Analyst. "
        "Original Query: {query}\n"
        "Raw Scraped Dark Web Data:\n{scraped_data}\n\n"
        "Synthesize this data into a clear, structured intelligence report. "
        "Highlight any relevant actors, indicators of compromise, or key findings. "
        "If the scraped data is empty or indicates sites were offline, explicitly state that."
    )
    chain = prompt | llm
    response = chain.invoke({
        "query": state["query"],
        "scraped_data": state["scraped_data"]
    })
    
    return {"final_report": response.content}

# ==========================================
# Graph Compilation
# ==========================================

def create_agent():
    workflow = StateGraph(OSINTState)

    # adding nodes to workflow
    workflow.add_node("architect", architect_node)
    workflow.add_node("recon", recon_node)
    workflow.add_node("ingestion", ingestion_node)
    workflow.add_node("analyst", analyst_node)

    # execution edges -> how the execution happens
    workflow.set_entry_point("architect")
    workflow.add_edge("architect", "recon") 
    workflow.add_edge("recon", "ingestion")
    workflow.add_edge("ingestion", "analyst")
    workflow.add_edge("analyst", END)

    app = workflow.compile()

    return app