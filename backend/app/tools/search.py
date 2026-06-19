from app.services.vector import search_similar

# This is the JSON description the LLM reads to understand the tool.
# The LLM never sees your Python code — only this description.
SEARCH_DOCUMENTS_TOOL = {
    "type": "function",
    "function": {
        "name": "search_documents",
        "description": (
            "Search through documents uploaded to this workspace using semantic search. "
            "Use this when the user's question can be answered from their own uploaded files. "
            "Returns relevant text chunks and their source file IDs."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query. Make it specific and descriptive for best results."
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of results to return. Default 3, max 5.",
                    "default": 3
                }
            },
            "required": ["query"]
        }
    }
}


def run_search_documents(query: str, workspace_id: str, limit: int = 3) -> str:
    """
    This is the actual Python function that runs when the LLM calls search_documents.
    It calls your existing vector search from Phase 6 — no new logic needed.
    Returns a string because tool results must be text that goes back into the LLM conversation.
    """
    limit = min(limit, 5)  # safety cap
    chunks = search_similar(query=query, workspace_id=workspace_id, limit=limit)

    if not chunks:
        return "No relevant documents found for this query."

    results = []
    for i, chunk in enumerate(chunks):
        results.append(
            f"[Result {i+1}] File ID: {chunk['file_id']} | Score: {round(chunk['score'], 3)}\n"
            f"{chunk['text'][:400]}"
        )

    return "\n\n".join(results)