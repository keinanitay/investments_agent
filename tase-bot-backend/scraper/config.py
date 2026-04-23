# Centralized configuration for all scrapers

# Strict filtering to minimize storage costs
TARGET_KEYWORDS = [
    "מדד", 'ת"א 35', 'ת"א 125', "S&P 500", 'ת"א 90',
    "מיטב דש", "ילין לפידות", "בנק לאומי", "ריבית", "אינפלציה",
    "הראל השקעות", "מגדל ביטוח", "כלל ביטוח", "בית השקעות פסגות", "אלטשולר שחם",
    "עליות", "ירידות"
]

RSS_FEEDS = [
    {
        "name": "Globes",
        "url": "https://www.globes.co.il/webservice/rss/rssfeeder.asmx/FeederNode?iID=2", # Capital Market
        "custom_processor": None
    },
    {
        "name": "Walla Finance",
        "url": "https://rss.walla.co.il/feed/3", # Explicitly Walla! Kesef
        "custom_processor": None
    },
    {
        "name": "Ynet Economy",
        "url": "http://www.ynet.co.il/Integration/StoryRss6.xml", # Explicitly Ynet Economy
        "custom_processor": None
    }
]
