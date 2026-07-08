"""
backend/app/services/entity_extraction.py
"""

import json
import re
import logging

from groq import Groq

logger = logging.getLogger(__name__)

client = Groq()

VALID_TYPES = {
    "concept",
    "technology",
    "topic",
    "person",
    "organization",
    "event",
    "place",
    "product",
}

EXTRACTION_SYSTEM_PROMPT = """You are an entity extraction system for a knowledge management tool. \
Documents can be of any kind — resumes, books, contracts, receipts, research papers, articles, or anything else.

Given a chunk of text, identify the important named entities and return them as a JSON array.

The test for whether something is an entity: does it refer to one specific, identifiable thing that has \
a proper name, and would knowing about it help someone later understand or navigate this document?

Entity types:
- person — a named individual, real or fictional (e.g. "Marie Curie", "Sherlock Holmes")
- organization — a company, institution, government body (e.g. "Google", "MIT", "IRS")
- technology — a named tool, framework, language, or system (e.g. "React", "PostgreSQL")
- product — a named product, book, course, or software (e.g. "Python Bible", "iPhone 15")
- event — a named conference, ceremony, or historical event (e.g. "ICCS 2023", "Treaty of Versailles")
- place — a named location, city, country, or region (e.g. "Bengaluru", "Amazon rainforest")
- concept — a named theory, method, or abstract idea (e.g. "Machine Learning", "relativity")
- topic — a broad named subject or theme (e.g. "Blockchain", "Web Development")

Do NOT extract:
- Numbers, amounts, percentages, scores, or dates (e.g. "85%", "2023", "$4,500")
- Generic nouns with no proper name (e.g. "the company", "a developer", "the system")
- Contact details (emails, phone numbers, URLs)

Return ONLY a valid JSON array with no extra text, no markdown, no code blocks. Examples:
[{"name": "React", "type": "technology"}, {"name": "Google", "type": "organization"}]

If there are no entities, return an empty array: []
"""

def _call_groq_for_entities(chunk_text: str):
    return client.chat.completions.create(
        model="qwen/qwen3-32b",
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": chunk_text + "\n/no_think"
            },
        ],
        max_tokens=1024,
        temperature=0,
        reasoning_format="hidden",
    )

def extract_entities_from_chunk(chunk_text: str) -> list[dict]:
    """
    Returns a list of {"name": str, "type": str} dicts.
    Uses plain JSON response with Qwen3 + hidden reasoning mode.
    Returns [] on any failure.
    """
    for attempt in range(2):
        try:
            response = _call_groq_for_entities(chunk_text)

            content = response.choices[0].message.content or ""
            content = content.strip()

            # Strip markdown code blocks if model wraps response in them
            content = re.sub(r"```json\s*", "", content)
            content = re.sub(r"```\s*", "", content)
            content = content.strip()

            if not content:
                logger.warning("Attempt %d: empty response from model", attempt + 1)
                continue

            raw_entities = json.loads(content)

            if not isinstance(raw_entities, list):
                logger.warning("Attempt %d: response is not a list: %r", attempt + 1, content)
                continue

            cleaned = []
            for item in raw_entities:
                name = str(item.get("name", "")).strip()
                etype = str(item.get("type", "")).strip().lower()
                if name and etype in VALID_TYPES:
                    cleaned.append({"name": name, "type": etype})

            return cleaned

        except json.JSONDecodeError as e:
            logger.warning("Attempt %d: JSON parse error (%s) on: %r", attempt + 1, e, content)
            continue

        except Exception:
            logger.exception("Entity extraction failed unexpectedly for chunk")
            return []

    logger.warning("Entity extraction gave up after retries")
    return []