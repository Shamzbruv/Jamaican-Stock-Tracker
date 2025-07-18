import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import tweepy
import praw
from dotenv import load_dotenv
import feedparser  # For RSS news

load_dotenv()

# ---- CONFIG ----
STOCKS = ["SCI", "DTC", "FESCO", "GHL", "TBCL", "DOLLA", "ONE", "TJH"]
CEOS = {
    "SCI": ["@SygnusCredit", "@KeithDuncanJM"],  # Twitter handles
    "TBCL": ["@TropicalBattery", "@AdamStewartJA"], 
    # Add more CEOs/execs here
}
NEWS_SITES = [
    "http://jamaica-gleaner.com/rss.xml",
    "http://jamaicaobserver.com/rss/",
    "https://www.radiojamaicanewsonline.com/rss" 
]

# ---- JamStockEx Scraper ----
def scrape_jamstockex():
    print("📈 Scraping JamStockEx...")
    url = "https://www.jamstockex.com/trading/trade-summary/"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", {"class": "trade-summary-table"})
        
        data = []
        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) >= 6:
                data.append({
                    "Symbol": cols[0].text.strip(),
                    "Close": cols[4].text.strip(),
                    "Volume": cols[5].text.strip().replace(",", "")
                })
        
        pd.DataFrame(data).to_csv(f"data/prices_{datetime.date.today()}.csv", index=False)
        print("✅ JamStockEx data saved!")
    except Exception as e:
        print(f"❌ JamStockEx error: {e}")

# ---- Twitter Scraper (CEOs + Keywords) ----
def scrape_twitter():
    print("🐦 Scraping Twitter...")
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
    if not bearer_token:
        print("⚠️ Twitter token missing. Skipping.")
        return

    client = tweepy.Client(bearer_token=bearer_token)
    tweets_data = []

    # Track: Stock symbols, CEO handles, and keywords
    queries = [
        *[f"${stock} OR {stock}" for stock in STOCKS],
        *[f"from:{handle}" for handles in CEOS.values() for handle in handles],
        '"Jamaican stock market" OR "JSE" OR "Kingston finance"'
    ]

    for query in queries:
        try:
            tweets = client.search_recent_tweets(
                query=query + " lang:en -is:retweet",
                max_results=100,
                tweet_fields=["created_at", "author_id", "public_metrics"]
            )
            if tweets.data:
                for tweet in tweets.data:
                    tweets_data.append({
                        "Platform": "Twitter",
                        "Author": f"user_{tweet.author_id}",
                        "Text": tweet.text,
                        "Likes": tweet.public_metrics["like_count"],
                        "Date": tweet.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                        "Query": query
                    })
        except Exception as e:
            print(f"❌ Twitter query '{query}' failed: {e}")

    if tweets_data:
        pd.DataFrame(tweets_data).to_csv(f"data/twitter_{datetime.date.today()}.csv", index=False)
        print("✅ Twitter data saved!")

# ---- Reddit Scraper ----
def scrape_reddit():
    print("📱 Scraping Reddit...")
    reddit = praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        user_agent="JamaicanStockTracker/1.0"
    )
    
    reddit_data = []
    for stock in STOCKS:
        try:
            for submission in reddit.subreddit("all").search(
                f"{stock} OR {CEOS.get(stock, [''])[0]}", 
                limit=50, 
                sort="new"
            ):
                reddit_data.append({
                    "Platform": "Reddit",
                    "Stock": stock,
                    "Title": submission.title,
                    "Author": submission.author.name if submission.author else "[deleted]",
                    "Upvotes": submission.score,
                    "Date": datetime.datetime.fromtimestamp(submission.created_utc).strftime("%Y-%m-%d"),
                    "URL": f"https://reddit.com{submission.permalink}"
                })
        except Exception as e:
            print(f"❌ Reddit search for {stock} failed: {e}")

    if reddit_data:
        pd.DataFrame(reddit_data).to_csv(f"data/reddit_{datetime.date.today()}.csv", index=False)
        print("✅ Reddit data saved!")

# ---- News Scraper (Jamaican RSS Feeds) ----
def scrape_news():
    print("📰 Scraping Jamaican news...")
    news_data = []
    for url in NEWS_SITES:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                for stock in STOCKS:
                    if stock in entry.title or any(ceo in entry.title for ceo in CEOS.get(stock, [])):
                        news_data.append({
                            "Platform": "News",
                            "Source": feed.feed.title,
                            "Title": entry.title,
                            "URL": entry.link,
                            "Date": entry.published.split("T")[0] if "published" in entry else "N/A",
                            "Mentioned": stock
                        })
        except Exception as e:
            print(f"❌ Failed to parse {url}: {e}")

    if news_data:
        pd.DataFrame(news_data).to_csv(f"data/news_{datetime.date.today()}.csv", index=False)
        print("✅ News data saved!")

if __name__ == "__main__":
    scrape_jamstockex()
    scrape_twitter()
    scrape_reddit()
    scrape_news()
