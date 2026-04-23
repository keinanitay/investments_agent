import logging
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

logger.info("Initializing RAG Vector Search Service...")
# Load the open-source embedding model safely on boot for the Agent
try:
    embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    logger.info("SentenceTransformer loaded successfully.")
except Exception as e:
    logger.error(f"Failed to load embedding model: {e}")
    embedding_model = None

async def vector_search_articles(query: str, db_collection, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Executes a semantic vector search against MongoDB Atlas.
    """
    if not embedding_model:
        logger.warning("Embedding model unavailable. Skipping vector search.")
        return []

    logger.info(f"Generating vector for query: '{query}'")
    query_vector = embedding_model.encode(query).tolist()

    # The exact Aggregation Pipeline for MongoDB Atlas native $vectorSearch
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",      # Must match the Index Name built in the Atlas UI
                "path": "embedding",          # The field in our Document holding the float array
                "queryVector": query_vector,  # Our query converted to floats
                "numCandidates": 100,         # HNSW depth search limit
                "limit": limit                # Return top X results
            }
        },
        {
            "$project": {
                "_id": 0,
                "title": 1,
                "source": 1,
                "content": 1,
                "url": 1,
                "score": { "$meta": "vectorSearchScore" }
            }
        }
    ]

    try:
        # Atlas execution
        cursor = db_collection.aggregate(pipeline)
        results = await cursor.to_list(length=limit)
        return results
        
    except Exception as e:
        logger.warning(f"Vector search failed (expected if running on Local MongoDB Community): {e}")
        return []
