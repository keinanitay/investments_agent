import asyncio
import feedparser
import logging
from bs4 import BeautifulSoup
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
import sys
from sentence_transformers import SentenceTransformer

# Add backend directory to sys.path if not already there
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.schemas import NewsArticle
from scraper.config import TARGET_KEYWORDS

logger = logging.getLogger(__name__)

# Initialize local open-source embedding model
# paraphrase-multilingual-MiniLM-L12-v2 natively supports 50 languages including Hebrew
logger.info("Loading SentenceTransformer embedding model...")
embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
logger.info("Embedding model loaded successfully.")


def clean_html(raw_html: str) -> str:
    """Removes HTML tags and returns clean text."""
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text(separator=" ", strip=True)

def is_relevant(title: str, summary: str) -> bool:
    """Checks if the article contains our target keywords."""
    text_to_check = f"{title} {summary}"
    return any(keyword in text_to_check for keyword in TARGET_KEYWORDS)

async def scrape_rss_feed(source_name: str, rss_url: str, db_collection):
    """
    Generic function to fetch, parse, filter, and upsert news from an RSS feed.
    """
    logger.info(f"Starting {source_name} RSS Scraper (URL: {rss_url})...")
    
    # Fetch and parse RSS
    feed = feedparser.parse(rss_url)
    
    # Some sites return a 404/301 status, or fail to parse
    if getattr(feed, "status", 200) not in [200, 301, 302] and not feed.entries:
        logger.warning(f"Failed to fetch or parse RSS for {source_name}. Status: {getattr(feed, 'status', 'Unknown')}")
        return 0

    inserted_count = 0
    for entry in feed.entries:
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        link = entry.get("link", "")
        
        if is_relevant(title, summary):
            clean_content = clean_html(summary)
            
            # Generate semantic vector locally for free
            text_to_embed = f"Source: {source_name}\nTitle: {title}\nSummary: {clean_content}"
            vector = embedding_model.encode(text_to_embed).tolist()
            
            # Prepare document
            article = NewsArticle(
                title=title,
                url=link,
                source=source_name,
                content=clean_content,
                published_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
                embedding=vector
            )
            
            # Insert if not exists (Upsert logic based on URL)
            result = await db_collection.update_one(
                {"url": link}, 
                {"$setOnInsert": article.model_dump(by_alias=True, exclude={"id"})}, 
                upsert=True
            )
            
            if result.upserted_id:
                inserted_count += 1
                
    logger.info(f"Finished {source_name} scraper. Inserted {inserted_count} new articles.")
    return inserted_count
