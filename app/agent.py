import os
from langchain_openai import ChatOpenAI

from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from dotenv import load_dotenv

from langchain_core.prompts import ChatPromptTemplate


from tor_tools import search_ahmia, scrape_onion_site   


# for a local source model
from langchain_ollama import ChatOllama




load_dotenv()


def create_agent():
    # llm = ChatOpenAI(
    #     openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    #     openai_api_base ="https://openrouter.ai/api/v1",
    #     model_name = os.getenv("OPENROUTER_MODEL"),
    #     max_tokens=2048,
    #     temperature=0.2
    # )


    llm = ChatOllama(
        model="qwen3.5",
        temperature=0.2
    )

    # defining thr tools avaliable for the agent

    tools = [search_ahmia, scrape_onion_site]

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a highly capable OSINT (Open Source Intelligence) researcher. 
        Your objective is to investigate queries related to the Dark Web safely and analytically.
        You have access to tools that can search for .onion links and scrape content from them.
        
        Guidelines:
        - If asked to find information, first use 'search_ahmia' to find relevant .onion links.
        - Then, use 'scrape_onion_site' to read the content of the most promising links.
        - Synthesize the findings into a clear, concise intelligence report.
        - Dark web sites are frequently offline; if a scrape fails, report it and try another link.
        - Always maintain an objective, analytical tone."""),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])


    agent = create_tool_calling_agent(llm,tools,prompt)

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors = True,
    )

    return agent_executor
