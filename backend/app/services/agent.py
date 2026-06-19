import json
import os
from groq import Groq
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app.tools.search import SEARCH_DOCUMENTS_TOOL, run_search_documents
from app.tools.graph import GET_ENTITY_GRAPH_TOOL, run_get_entity_graph
from app.tools.web_search import WEB_SEARCH_TOOL, run_web_search

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# All tools the agent can use — the LLM reads these descriptions
ALL_TOOLS = [
    SEARCH_DOCUMENTS_TOOL,
    GET_ENTITY_GRAPH_TOOL,
    WEB_SEARCH_TOOL,
]

# Safety cap: agent will never loop more than this many times
MAX_ITERATIONS = 8

SYSTEM_PROMPT = """You are a research agent for KnowledgeOS. Your job is to thoroughly research a topic and produce a structured report.

You have access to three tools:
- search_documents: search the user's uploaded workspace documents
- get_entity_graph: explore relationships between concepts in the knowledge graph
- web_search: search the internet for real-time information

Research process:
1. Start by searching workspace documents for internal knowledge
2. Use the knowledge graph to find related concepts and documents
3. Use web search for external/real-time information
4. Combine all findings into a comprehensive answer

Always cite where your information came from (document search, graph, or web).
When you have gathered enough information, write a well-structured report with clear sections."""


def run_tool(tool_name: str, tool_args: dict, workspace_id: str, db: Session) -> str:
    """
    This function is the dispatcher — it receives whatever tool the LLM chose to call,
    runs the actual Python function, and returns the result as a string.
    The result gets fed back into the conversation so the LLM can use it.
    """
    if tool_name == "search_documents":
        return run_search_documents(
            query=tool_args["query"],
            workspace_id=workspace_id,
            limit=tool_args.get("limit", 3)
        )
    elif tool_name == "get_entity_graph":
        return run_get_entity_graph(
            entity_name=tool_args["entity_name"],
            workspace_id=workspace_id,
            db=db
        )
    elif tool_name == "web_search":
        return run_web_search(query=tool_args["query"])
    else:
        return f"Unknown tool: {tool_name}"


def run_research_agent(query: str, workspace_id: str, db: Session) -> dict:
    """
    The main agent loop. This is the ReAct pattern:
    Reason (LLM thinks) → Act (tool runs) → Observe (result fed back) → repeat.

    The conversation history (messages list) grows with each iteration,
    giving the LLM full memory of what it has already done and found.
    """

    # Conversation starts with the system prompt and user query
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Research the following topic and produce a detailed report:\n\n{query}"}
    ]

    # Track what the agent did — useful for debugging and returning to the frontend
    steps = []
    iteration = 0

    while iteration < MAX_ITERATIONS:
        iteration += 1

        # Call Groq — give it the full conversation history + available tools
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            tools=ALL_TOOLS,
            # "auto" means: LLM decides whether to call a tool or answer directly
            tool_choice="auto",
            max_tokens=2048
        )

        message = response.choices[0].message

        # --- Did the LLM call a tool? ---
        if message.tool_calls:
            # Add the LLM's tool-calling message to conversation history
            messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            })

            # Run each tool the LLM called (usually just one at a time)
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                # Record the step for transparency
                steps.append({
                    "iteration": iteration,
                    "tool": tool_name,
                    "args": tool_args
                })

                # Actually run the tool
                tool_result = run_tool(tool_name, tool_args, workspace_id, db)

                # Feed the result back into the conversation as a "tool" message
                # This is how the LLM learns what the tool returned
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })

            # Loop continues — LLM will see the tool results and decide what to do next

        # --- LLM chose to answer (no tool calls) — we're done ---
        else:
            final_answer = message.content

            return {
                "query": query,
                "report": final_answer,
                "steps": steps,
                "iterations": iteration
            }

    # Safety fallback: hit max iterations without a final answer
    # Extract whatever the last text response was
    last_text = next(
        (m["content"] for m in reversed(messages) if m.get("role") == "assistant" and m.get("content")),
        "Research agent reached maximum iterations without producing a final report."
    )

    return {
        "query": query,
        "report": last_text,
        "steps": steps,
        "iterations": iteration,
        "warning": "Max iterations reached"
    }