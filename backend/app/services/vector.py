from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from google import genai
from google.genai import types
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

client_genai = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
qdrant_host = os.getenv("QDRANT_HOST", "localhost")
client = QdrantClient(host=qdrant_host, port=6333)

COLLECTION_NAME = "knowledgeos"
ENTITIES_COLLECTION = "entities"
VECTOR_SIZE = 3072  # Gemini embedding size

def ensure_collection():
    collections = client.get_collections().collections
    names = [c.name for c in collections]

    if COLLECTION_NAME not in names:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE
            )
        )
        print(f"Created collection: {COLLECTION_NAME}")

def ensure_entities_collection():
    collections = client.get_collections().collections
    names = [c.name for c in collections]

    if ENTITIES_COLLECTION not in names:
        client.create_collection(
            collection_name=ENTITIES_COLLECTION,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE
            )
        )
        print(f"Created collection: {ENTITIES_COLLECTION}")

def get_embedding(text: str) -> list:
    result = client_genai.models.embed_content(
        model="models/gemini-embedding-001",
        contents=text,
    )
    return result.embeddings[0].values

def store_chunks(file_id: str, workspace_id: str, chunks: list[str]):
    ensure_collection()

    points = []
    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "file_id": file_id,
                    "workspace_id": workspace_id,
                    "chunk_index": i,
                    "text": chunk
                }
            )
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )
    print(f"Stored {len(points)} chunks for file {file_id}")

def search_similar(query: str, workspace_id: str, limit: int = 5) -> list:
    ensure_collection()

    query_embedding = client_genai.models.embed_content(
        model="models/gemini-embedding-001",
        contents=query,
    ).embeddings[0].values
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        query_filter={
            "must": [
                {"key": "workspace_id", "match": {"value": workspace_id}}
            ]
        },
        limit=limit
    ).points

    return [
        {
            "text": r.payload["text"],
            "file_id": r.payload["file_id"],
            "score": r.score
        }
        for r in results
    ]