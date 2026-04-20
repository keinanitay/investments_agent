import asyncio
import os
import sys
import re
import feedparser
import logging
from bs4 import BeautifulSoup
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from dotenv import load_dotenv

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.schemas import NewsArticle

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "tase_bot_db")

GLOBES_RSS_URL = "https://www.globes.co.il/webservice/rss/rssfeeder.asmx/FeederNode?iID=2"

from config import TARGET_KEYWORDS

def clean_html(raw_html: str) -> str:
    """Removes HTML tags and returns clean text."""
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text(separator=" ", strip=True)

def is_relevant(title: str, summary: str) -> bool:
    """Checks if the article contains our target keywords."""
    text_to_check = f"{title} {summary}"
    return any(keyword in text_to_check for keyword in TARGET_KEYWORDS)

async def run_scraper():
    logger.info("Starting Globes RSS Scraper...")
    
    # Connect to DB
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db["news_articles"]
    
    # Ensure TTL Index (Deletes documents automatically after 14 days)
    # 14 days = 1,209,600 seconds
    await collection.create_index("created_at", expireAfterSeconds=1209600)
    
    # Ensure unique index on URL to prevent duplicates
    await collection.create_index("url", unique=True)
    
    # Fetch and parse RSS
    feed = feedparser.parse(GLOBES_RSS_URL)
    
    inserted_count = 0
    for entry in feed.entries:
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        link = entry.get("link", "")
        
        if is_relevant(title, summary):
            clean_content = clean_html(summary)
            
            # Prepare document
            article = NewsArticle(
                title=title,
                url=link,
                source="Globes",
                content=clean_content,
                published_at=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            
            # Insert if not exists (Upsert logic based on URL)
            result = await collection.update_one(
                {"url": link}, 
                {"$setOnInsert": article.model_dump(by_alias=True, exclude={"id"})}, 
                upsert=True
            )
            
            if result.upserted_id:
                inserted_count += 1
                
    logger.info(f"Scraper finished. Inserted {inserted_count} new articles.")
    client.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())