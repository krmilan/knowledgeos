"""
backend/app/services/entity_extraction.py

"""

import json
import logging

from groq import Groq

logger = logging.getLogger(__name__)

client = Groq()

VALID_TYPES = {"concept", "technology", "topic", "person", "organization"}

ENTITY_EXTRACTION_TOOL = {
    "type": "function",
    "function": {
        "name": "record_entities",
        "description": "Record the distinct entities mentioned in a piece of text from a document.",
        "parameters": {
            "type": "object",
            "properties": {
                "entities": {
                    "type": "array",
                    "description": (
                        "Entities found in the text. Return an empty array if the text contains "
                        "no meaningful entities (e.g. it's boilerplate, a page header, or pure "
                        "prose with nothing worth extracting)."
                    ),
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": (
                                    "Canonical name of the entity, properly capitalized "
                                    "(e.g. 'PostgreSQL', not 'postgresql' or 'Postgre SQL')."
                                ),
                            },
                            "type": {
                                "type": "string",
                                "enum": sorted(VALID_TYPES),
                                "description": "Category of the entity.",
                            },
                        },
                        "required": ["name", "type"],
                    },
                }
            },
            "required": ["entities"],
        },
    },
}

EXTRACTION_SYSTEM_PROMPT = """You are an entity extraction system for a knowledge management tool. \
Given a chunk of text from a document, identify the important entities it mentions \
and call record_entities with them.

Guidelines:
- Only extract entities that are meaningful for understanding what this document is about.
- Skip generic words, filler, and anything not central to the document's content.
- Use the canonical, properly-capitalized form of each name (e.g. "Kubernetes", not "kubernetes" or "k8s").
- If the text has nothing worth extracting, call record_entities with an empty entities array.
"""


def extract_entities_from_chunk(chunk_text: str) -> list[dict]:
    """
    Returns a list of {"name": str, "type": str} dicts.
    Returns [] on any failure - extraction is best-effort and must never
    crash the Celery file-processing task.
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": chunk_text},
            ],
            tools=[ENTITY_EXTRACTION_TOOL],
            tool_choice={"type": "function", "function": {"name": "record_entities"}},
        )

        tool_calls = response.choices[0].message.tool_calls
        if not tool_calls:
            logger.warning("No tool call returned for chunk extraction")
            return []

        arguments = json.loads(tool_calls[0].function.arguments)
        raw_entities = arguments.get("entities", [])

        cleaned = []
        for item in raw_entities:
            name = str(item.get("name", "")).strip()
            etype = str(item.get("type", "")).strip().lower()
            if name and etype in VALID_TYPES:
                cleaned.append({"name": name, "type": etype})
        return cleaned

    except Exception:
        logger.exception("Entity extraction failed for chunk")
        return []