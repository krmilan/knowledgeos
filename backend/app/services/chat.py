import re
from groq import Groq
from app.services.vector import search_similar
import os
from dotenv import load_dotenv

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def strip_thinking(text: str) -> str:
    """Qwen3 reasoning models emit a <think>...</think> block before the real answer.
    Strip it so users only see the final response."""
    return re.sub(r"<think>.*?</think>\s*", "", text, flags=re.DOTALL).strip()

def build_prompt(question: str, context_chunks: list) -> str:
    context = "\n\n".join([
        f"[Source {i+1}]: {chunk['text']}"
        for i, chunk in enumerate(context_chunks)
    ])

    return f"""You are a helpful AI assistant for KnowledgeOS.
Answer the user's question based ONLY on the provided context.
If the answer is not in the context, say "I don't have enough information in the uploaded documents to answer this."

Context:
{context}

Question: {question}

Answer:"""

def chat_with_knowledge(question: str, workspace_id: str) -> dict:
    chunks = search_similar(
        query=question,
        workspace_id=workspace_id,
        limit=3
    )

    if not chunks:
        return {
            "answer": "No documents found in this workspace. Please upload some files first.",
            "sources": []
        }

    prompt = build_prompt(question, chunks)

    response = groq_client.chat.completions.create(
        model="qwen/qwen3.6-27b",
        messages=[
            {"role": "user", "content": prompt}
        ],
    )

    return {
        "answer": strip_thinking(response.choices[0].message.content),
        "sources": [
            {
                "file_id": chunk["file_id"],
                "score": round(chunk["score"], 3),
                "preview": chunk["text"][:200] + "..."
            }
            for chunk in chunks
        ]
    }