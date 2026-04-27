import streamlit as st
import os
import sys
from dotenv import load_dotenv

# Import your existing agent creation function
from agent import create_agent
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler

# Load environment variables
load_dotenv()

# --- Page Configuration ---
st.set_page_config(
    page_title="Dark Web OSINT Copilot",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Sidebar ---
with st.sidebar:
    st.title("⚙️ System Status")
    
    # Check API Key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key:
        st.success("✅ OpenRouter API Key Loaded")
    else:
        st.error("❌ Missing OpenRouter API Key in .env")
        
    # Check Tor Proxy config
    tor_proxy = os.getenv("TOR_PROXY", "socks5h://127.0.0.1:9050")
    st.info(f"🧅 Tor Routing: `{tor_proxy}`\n\n*(Ensure your Tor background service is running!)*")
    
    st.markdown("---")
    st.markdown("""
    **Capabilities:**
    - 🔍 Searches Ahmia indexer
    - 📄 Scrapes raw `.onion` content
    - 🧠 Synthesizes threat intel
    """)
    
    if st.button("Clear Chat History"):
        st.session_state["messages"] = [{"role": "assistant", "content": "OSINT Copilot initialized. Awaiting queries..."}]
        st.rerun()

# --- Main Chat Interface ---
st.title("🕵️ AI-Powered Dark Web OSINT Terminal")
st.markdown("Enter a research query below. The agent will autonomously route through Tor to gather intelligence.")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "OSINT Copilot initialized. Awaiting queries..."}
    ]

# Display existing chat messages
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# --- Chat Input & Agent Execution ---
if prompt := st.chat_input("E.g., Find public directories tracking ransomware onion services..."):
    
    # 1. Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # 2. Execute Agent with UI Callbacks
    with st.chat_message("assistant"):
        # The StreamlitCallbackHandler visually tracks the agent's tool usage
        st_callback = StreamlitCallbackHandler(st.container(), expand_new_thoughts=True)
        
    try:
            # Initialize agent (doing this here ensures fresh execution state)
            agent_executor = create_agent()
            
            # Run the agent, passing the Streamlit callback
            # FIX 1: Change "input" to "query"
            final_state = agent_executor.invoke(
                {"query": prompt}, 
                {"callbacks": [st_callback]}
            )
            
            # Display final output
            # FIX 2: Change "output" to "final_report"
            final_report = final_state["final_report"]
            st.write(final_report)
            
            # Save to history
            st.session_state.messages.append({"role": "assistant", "content": final_report})
            
    except Exception as e:
            error_msg = f"**Execution Error:** `{str(e)}`\n\n*Check if your Tor service is running and your API key is valid.*"
            st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})