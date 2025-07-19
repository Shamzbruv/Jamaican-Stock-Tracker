import os
import time
import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import tweepy
import praw
import feedparser
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()

# Constants
STOCKS = ["SCI", "DTC", "FESCO", "GHL", "TBCL", "DOLLA", "ONE", "TJH"]
CEOS = {
    "SCI": ["Keith Duncan", "Sygnus", "@SygnusCredit"],
    "TBCL": ["Adam Stewart", "Tropical Battery", "@TropicalBattery"],
    "GHL": ["Christopher Anand", "Guardian Holdings"]
}
NEWS_SOURCES = [
    "http://jamaica-gleaner.com/rss.xml",
    "http://jamaicaobserver.com/rss/",
    "https://www.radiojamaicanewsonline.com/rss"
]

# Rate limiting (requests per minute)
RATE_LIMITS = {
    'reddit': 60,
    'twitter': 450,
    'news': 30
}

class Scraper:
    def __init__(self):
        self.last_request = {
            'reddit': 0,
            'twitter': 0,
            'news': 0
        }

    def _rate_limit(self, platform):
        """Enforce rate limits"""
        elapsed = time.time() - self.last_request[platform]
        delay = max(60/RATE_LIMITS[platform] - elapsed, 0)
        time.sleep(delay)
        self.last_request[platform] = time.time()

    def scrape_jamstockex(self):
        """Scrape JamStockEx market data"""
        logging.info("Starting JamStockEx scrape")
        url = "https://www.jamstockex.com/trading/trade-summary/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            table = soup.find("table", {"class": "trade-summary-table"})
            
            if not table:
                raise ValueError("No table found on JamStockEx page")

            data = []
            for row in table.find_all("tr")[1:]:
                cols = row.find_all("td")
                if len(cols) >= 6:
                    data.append({
                        "Symbol": cols[0].text.strip(),
                        "Open": cols[1].text.strip(),
                        "High": cols[2].text.strip(),
                        "Low": cols[3].text.strip(),
                        "Close": cols[4].text.strip(),
                        "Volume": cols[5].text.strip().replace(",", ""),
                        "Timestamp": datetime.datetime.now().isoformat()
                    })

            df = pd.DataFrame(data)
            os.makedirs("data", exist_ok=True)
            df.to_csv(f"data/prices_{datetime.date.today()}.csv", index=False)
            logging.info(f"Saved JamStockEx data for {len(data)} stocks")

        except Exception as e:
            logging.error(f"JamStockEx scrape failed: {str(e)}")
            raise

    def scrape_twitter(self):
        """Scrape Twitter for stock/CEO mentions"""
        logging.info("Starting Twitter scrape")
        bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        if not bearer_token:
            logging.warning("Twitter Bearer Token not configured")
            return

        try:
            client = tweepy.Client(bearer_token=bearer_token)
            tweets_data = []

            # Build comprehensive search queries
            queries = [
                *[f"${stock} OR {stock} OR {ceo}" for stock in STOCKS for ceo in CEOS.get(stock, [])],
                '"Jamaica stock market" OR "JSE" OR "Kingston finance"'
            ]

            for query in queries:
                self._rate_limit('twitter')
                try:
                    tweets = client.search_recent_tweets(
                        query=query + " lang:en -is:retweet -is:reply",
                        max_results=100,
                        tweet_fields=["created_at", "author_id", "public_metrics", "context_annotations"],
                        expansions=["author_id"]
                    )

                    if tweets.data:
                        for tweet in tweets.data:
                            tweets_data.append({
                                "Platform": "Twitter",
                                "Stock": next((s for s in STOCKS if s in query), "General"),
                                "Author": f"user_{tweet.author_id}",
                                "Text": tweet.text,
                                "Likes": tweet.public_metrics["like_count"],
                                "Retweets": tweet.public_metrics["retweet_count"],
                                "Timestamp": tweet.created_at.isoformat(),
                                "Query": query
                            })

                except Exception as e:
                    logging.error(f"Twitter query '{query}' failed: {str(e)}")
                    continue

            if tweets_data:
                df = pd.DataFrame(tweets_data)
                df.to_csv(f"data/twitter_{datetime.date.today()}.csv", index=False)
                logging.info(f"Saved {len(tweets_data)} Twitter mentions")

        except Exception as e:
            logging.error(f"Twitter scrape failed: {str(e)}")
            raise

    def scrape_reddit(self):
        """Scrape Reddit for stock discussions"""
        logging.info("Starting Reddit scrape")
        try:
            reddit = praw.Reddit(
                client_id=os.getenv("REDDIT_CLIENT_ID"),
                client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
                user_agent="JamaicanStockTracker/1.0 (by /u/Klutzy_Transition_42)"
            )

            reddit_data = []
            for stock in STOCKS:
                self._rate_limit('reddit')
                search_terms = f"{stock} OR {' OR '.join(CEOS.get(stock, []))}"
                
                try:
                    for submission in reddit.subreddit("all").search(
                        query=search_terms,
                        limit=100,
                        sort="new",
                        time_filter="month"
                    ):
                        reddit_data.append({
                            "Platform": "Reddit",
                            "Stock": stock,
                            "Title": submission.title,
                            "Content": submission.selftext,
                            "Author": submission.author.name if submission.author else "[deleted]",
                            "Subreddit": submission.subreddit.display_name,
                            "Upvotes": submission.score,
                            "Comments": submission.num_comments,
                            "URL": f"https://reddit.com{submission.permalink}",
                            "Timestamp": datetime.datetime.fromtimestamp(submission.created_utc).isoformat()
                        })

                except Exception as e:
                    logging.error(f"Reddit search for {stock} failed: {str(e)}")
                    continue

            if reddit_data:
                df = pd.DataFrame(reddit_data)
                df.to_csv(f"data/reddit_{datetime.date.today()}.csv", index=False)
                logging.info(f"Saved {len(reddit_data)} Reddit posts")

        except Exception as e:
            logging.error(f"Reddit scrape failed: {str(e)}")
            raise

    def scrape_news(self):
        """Scrape Jamaican news sources"""
        logging.info("Starting news scrape")
        news_data = []
        
        for url in NEWS_SOURCES:
            self._rate_limit('news')
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    for stock in STOCKS:
                        # Check stock ticker or CEO names in title/content
                        if (stock in entry.title or 
                            any(ceo in entry.title for ceo in CEOS.get(stock, [])):
                            news_data.append({
                                "Platform": "News",
                                "Source": feed.feed.get("title", url),
                                "Stock": stock,
                                "Title": entry.title,
                                "Summary": entry.get("summary", ""),
                                "Published": entry.get("published", ""),
                                "URL": entry.link,
                                "Timestamp": datetime.datetime.now().isoformat()
                            })
            except Exception as e:
                logging.error(f"Failed to parse {url}: {str(e)}")
                continue

        if news_data:
            df = pd.DataFrame(news_data)
            df.to_csv(f"data/news_{datetime.date.today()}.csv", index=False)
            logging.info(f"Saved {len(news_data)} news articles")

    def run_all(self):
        """Execute all scrapers with error handling"""
        try:
            self.scrape_jamstockex()
            self.scrape_twitter()
            self.scrape_reddit()
            self.scrape_news()
        except Exception as e:
            logging.critical(f"Fatal error in scraper: {str(e)}")
            raise

if __name__ == "__main__":
    scraper = Scraper()
    scraper.run_all()
