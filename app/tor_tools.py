import os
import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()

proxies = {
    "http":"socks5h://127.0.0.1:9050",
    "https":"socks5h://127.0.0.1:9050"
}


@tool
def search_ahmia(query: str) -> str:
    """
    Searches the Ahmia dark web indexer for .onion links based on a query.
    Useful for finding initial dark web URLs related to a topic

    """
    url = f"https://ahmia.fi/search/?q={query}"


    try:
        response = requests.get(url, proxies=proxies, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')


        results = []

        for i in soup.find_all("li", class_='searchResultsItem'):
            link = i.find("a")
            if link and '.onion' in link.get('href', ''):
                onion_url = link.get('href').replace('/search/redirect?search_term=', '')
                results.append(onion_url)
        if not results:
            return "No .onion links found for the query"
        return f"Found .onion links: {','.join(results[:5])}"
    except Exception as e:
        return f"Error searching Ahmia: {str(e)}"
    


@tool
def scrape_onion_site(url: str) -> str:
    """
    Scrapes the text content of a given .onion URL. 
    Input MUST be a valid .onion URL.
    """
    if ".onion" not in url:
        return "Error: Provided URL is not an onion service."
        
    try:
        # We MUST use the proxies to resolve .onion addresses
        response = requests.get(url, proxies=proxies, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Strip out script and style elements
        for script in soup(["script", "style"]):
            script.extract()
            
        text = soup.get_text(separator=' ', strip=True)
        # Limit token count for the LLM context window
        return text[:4000] 
    except Exception as e:
        return f"Failed to access or scrape the site. It may be offline. Error: {str(e)}"

