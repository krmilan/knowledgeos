import httpx

WEB_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "Search the internet for real-time information not available in the workspace documents. "
            "Use this for current events, job listings, market data, news, or anything that requires "
            "up-to-date information from the web."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query. Be specific for better results."
                }
            },
            "required": ["query"]
        }
    }
}


def run_web_search(query: str) -> str:
    """
    Uses DuckDuckGo's free instant answer API to search the web.
    No API key required. Returns a summary of results.

    Note: DuckDuckGo's API returns 'AbstractText' for well-known topics
    and 'RelatedTopics' for broader queries. We handle both.
    """
    try:
        # DuckDuckGo Instant Answer API — completely free, no auth needed
        response = httpx.get(
            "https://api.duckduckgo.com/",
            params={
                "q": query,
                "format": "json",
                "no_redirect": "1",
                "no_html": "1",
                "skip_disambig": "1"
            },
            timeout=10.0
        )
        response.raise_for_status()
        data = response.json()

        results = []

        # AbstractText: a direct summary paragraph (e.g. for "What is Python")
        if data.get("AbstractText"):
            results.append(f"Summary: {data['AbstractText']}")
            if data.get("AbstractURL"):
                results.append(f"Source: {data['AbstractURL']}")

        # RelatedTopics: list of related results (e.g. for "Python jobs Bengaluru")
        topics = data.get("RelatedTopics", [])[:5]
        if topics:
            results.append("\nRelated results:")
            for topic in topics:
                # Topics can be nested (sub-topics have a 'Topics' key)
                if "Text" in topic:
                    results.append(f"- {topic['Text']}")
                elif "Topics" in topic:
                    for sub in topic["Topics"][:2]:
                        if "Text" in sub:
                            results.append(f"  - {sub['Text']}")

        if not results:
            return f"No results found for '{query}'. Try a more specific query."

        return "\n".join(results)

    except httpx.TimeoutException:
        return f"Web search timed out for query: '{query}'. Try again or rephrase."
    except Exception as e:
        return f"Web search failed: {str(e)}"