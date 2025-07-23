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
import logging.handlers
import signal

# Configure logging with rotation
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.handlers.RotatingFileHandler('scraper.log', maxBytes=10*1024*1024, backupCount=5),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()

# Create directories
os.makedirs("data", exist_ok=True)
os.makedirs("reports", exist_ok=True)

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

# Rate limiting (requests per minute, conservative for free tier)
RATE_LIMITS = {
    'reddit': 60,   # Reddit allows 60 requests/minute
    'twitter': 20,  # Twitter free tier: ~300/15min ≈ 20/min
    'news': 30
}

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Function timed out after 10 minutes")

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
            signal.alarm(600)  # 10-minute timeout
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            signal.alarm(0)
            
            soup = BeautifulSoup(response.text, "html.parser")
            table = soup.find("table", {"class": "trade-summary-table"})
            
            if not table:
                logging.warning("Primary table not found, trying alternative")
                table = soup.find("table")
                if not table:
                    raise ValueError("No table found on JamStockEx page")

            data = []
            for row in table.find_all("tr")[1:]:
                cols = row.find_all("td")
                if len(cols) >= 6:
                    try:
                        volume = int(cols[5].text.strip().replace(",", ""))
                    except ValueError:
                        volume = 0
                        logging.warning(f"Invalid volume for {cols[0].text.strip()}")
                    data.append({
                        "Symbol": cols[0].text.strip(),
                        "Open": cols[1].text.strip(),
                        "High": cols[2].text.strip(),
                        "Low": cols[3].text.strip(),
                        "Close": cols[4].text.strip(),
                        "Volume": volume,
                        "Timestamp": datetime.datetime.now().isoformat()
                    })

            df = pd.DataFrame(data)
            df.to_csv(f"data/prices_{datetime.date.today()}.csv", index=False)
            logging.info(f"Saved JamStockEx data for {len(data)} stocks")

        except (TimeoutException, Exception) as e:
            logging.error(f"JamStockEx scrape failed or timed out: {str(e)}")
            signal.alarm(0)  # Disable alarm
            return

    def scrape_twitter(self):
        """Scrape Twitter for stock/CEO mentions"""
        logging.info("Starting Twitter scrape")
        bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        if not bearer_token:
            logging.warning("Twitter Bearer Token not configured")
            return

        try:
            signal.alarm(600)  # 10-minute timeout
            client = tweepy.Client(bearer_token=bearer_token)
            tweets_data = []

            # Simplified queries
            stock_query = f"({' OR '.join(STOCKS)}) lang:en -is:retweet -is:reply"
            market_query = "Jamaica stock market OR JSE OR Kingston finance lang:en -is:retweet -is:reply"

            for query in [stock_query, market_query]:
                self._rate_limit('twitter')
                try:
                    tweets = client.search_recent_tweets(
                        query=query,
                        max_results=30,  # Reduced to speed up
                        tweet_fields=["created_at", "author_id", "public_metrics"],
                        expansions=["author_id"]
                    )

                    if tweets.data:
                        for tweet in tweets.data:
                            stock_match = next((s for s in STOCKS if s in tweet.text.upper()), "General")
                            tweets_data.append({
                                "Platform": "Twitter",
                                "Stock": stock_match,
                                "Author": f"user_{tweet.author_id}",
                                "Text": tweet.text,
                                "Likes": tweet.public_metrics["like_count"],
                                "Retweets": tweet.public_metrics["retweet_count"],
                                "Timestamp": tweet.created_at.isoformat(),
                                "Query": query
                            })

                except tweepy.TweepyException as e:
                    if "429" in str(e):  # Rate limit error
                        logging.error(f"Twitter rate limit hit for query '{query}', waiting...")
                        time.sleep(5 * 60)  # 5-minute wait
                        continue
                    logging.error(f"Twitter query '{query}' failed: {str(e)}")
                    continue

            if tweets_data:
                df = pd.DataFrame(tweets_data)
                df.to_csv(f"data/twitter_{datetime.date.today()}.csv", index=False)
                logging.info(f"Saved {len(tweets_data)} Twitter mentions")

        except (TimeoutException, Exception) as e:
            logging.error(f"Twitter scrape failed or timed out: {str(e)}")
            signal.alarm(0)  # Disable alarm
            return

    def scrape_reddit(self):
        """Scrape Reddit for stock discussions"""
        logging.info("Starting Reddit scrape")
        try:
            signal.alarm(600)  # 10-minute timeout
            reddit = praw.Reddit(
                client_id=os.getenv("REDDIT_CLIENT_ID"),
                client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
                user_agent="JamaicanStockTracker/1.0 (by /u/Klutzy_Transition_42)"
            )

            reddit_data = []
            subreddits = ["investing"]  # Reduced to one subreddit
            stock_query = " OR ".join(STOCKS + [ceo for ceos in CEOS.values() for ceo in ceos])

            self._rate_limit('reddit')
            try:
                for submission in reddit.subreddit("investing").search(
                    query=stock_query,
                    limit=30,  # Reduced to speed up
                    sort="new",
                    time_filter="week"  # Shortened to week
                ):
                    if submission.selftext and submission.selftext != "[deleted]":
                        stock_match = next((s for s in STOCKS if s in submission.title.upper()), "General")
                        reddit_data.append({
                            "Platform": "Reddit",
                            "Stock": stock_match,
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
                logging.error(f"Reddit search failed: {str(e)}")
                return

            if reddit_data:
                df = pd.DataFrame(reddit_data)
                df.to_csv(f"data/reddit_{datetime.date.today()}.csv", index=False)
                logging.info(f"Saved {len(reddit_data)} Reddit posts")

        except (TimeoutException, Exception) as e:
            logging.error(f"Reddit scrape failed or timed out: {str(e)}")
            signal.alarm(0)  # Disable alarm
            return

    def scrape_news(self):
        """Scrape Jamaican news sources"""
        logging.info("Starting news scrape")
        feedparser.PARSE_TIMEOUT = 10  # Set timeout for RSS parsing
        news_data = []
        
        try:
            signal.alarm(600)  # 10-minute timeout
            for url in NEWS_SOURCES:
                self._rate_limit('news')
                try:
                    feed = feedparser.parse(url)
                    if feed.bozo:
                        logging.error(f"Invalid feed {url}: {feed.bozo_exception}")
                        continue
                    for entry in feed.entries:
                        for stock in STOCKS:
                            if (stock.lower() in entry.title.lower() or 
                                any(ceo.lower() in entry.title.lower() for ceo in CEOS.get(stock, [])) or
                                stock.lower() in entry.get("summary", "").lower()):
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
        except TimeoutException:
            logging.error("News scrape timed out")
        finally:
            signal.alarm(0)  # Disable alarm

        if news_data:
            df = pd.DataFrame(news_data)
            df.to_csv(f"data/news_{datetime.date.today()}.csv", index=False)
            logging.info(f"Saved {len(news_data)} news articles")

    def run_all(self):
        """Execute all scrapers with error handling"""
        signal.signal(signal.SIGALRM, timeout_handler)
        try:
            self.scrape_jamstockex()
            self.scrape_twitter()
            self.scrape_reddit()
            self.scrape_news()
        except Exception as e:
            logging.critical(f"Fatal error in scraper: {str(e)}")
            raise
        finally:
            signal.alarm(0)  # Ensure alarm is disabled

if __name__ == "__main__":
    scraper = Scraper()
    scraper.run_all()