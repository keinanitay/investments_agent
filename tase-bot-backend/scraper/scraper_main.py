import asyncio
import os
import sys
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Add backend directory to sys.path if not already there
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.config import RSS_FEEDS
from scraper.base_scraper import scrape_rss_feed

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "tase_bot_db")

async def run_all_scrapers():
    logger.info("Initializing RSS Scraping Pipeline...")
    
    # Connect to DB
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db["news_articles"]
    
    # Ensure indexes once before starting
    try:
        # TTL Index (Deletes documents automatically after 14 days = 1,209,600 seconds)
        await collection.create_index("created_at", expireAfterSeconds=1209600)
        # Unique URL index to prevent duplicates
        await collection.create_index("url", unique=True)
    except Exception as e:
        logger.error(f"Error ensuring indexes: {e}")

    total_inserted = 0

    for feed in RSS_FEEDS:
        source_name = feed.get("name")
        rss_url = feed.get("url")
        custom_processor = feed.get("custom_processor")
        
        if not rss_url or not source_name:
            logger.warning(f"Skipping incorrectly formatted feed entry: {feed}")
            continue
            
        try:
            if custom_processor:
                # E.g., if custom_processor is 'globes_custom', we could dynamically import it:
                # module = __import__(f"scraper.{custom_processor}", fromlist=['run_custom_scraper'])
                # inserted = await module.run_custom_scraper(source_name, rss_url, collection)
                logger.warning(f"Custom processor '{custom_processor}' for '{source_name}' not yet implemented. Skipping.")
                continue
            else:
                inserted = await scrape_rss_feed(source_name, rss_url, collection)
                total_inserted += inserted
        except Exception as e:
            logger.error(f"Error scraping {source_name}: {str(e)}")

    logger.info(f"Pipeline finished! Total articles inserted from all sources: {total_inserted}")
    client.close()

if __name__ == "__main__":
    asyncio.run(run_all_scrapers())
