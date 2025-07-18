import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import os
import tweepy  # For Twitter
import praw    # For Reddit

# Stocks to track
STOCKS = ["SCI", "DTC", "FESCO", "GHL", "TBCL", "DOLLA", "ONE", "TJH"]

# Twitter API (public data only)
TWITTER_BEARER_TOKEN = "YOUR_TWITTER_BEARER_TOKEN"  # Replace with yours

# Reddit API (public data only)
REDDIT_CLIENT_ID = "YOUR_REDDIT_CLIENT_ID"
REDDIT_CLIENT_SECRET = "YOUR_REDDIT_CLIENT_SECRET"

def scrape_jamstockex():
    """Scrape stock prices from JamStockEx"""
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
        
        df = pd.DataFrame(data)
        os.makedirs("data", exist_ok=True)
        df.to_csv(f"data/prices_{datetime.date.today()}.csv", index=False)
        print("✅ Stock data saved!")
    
    except Exception as e:
        print(f"❌ JamStockEx error: {e}")

def scrape_twitter():
    """Search Twitter for stock mentions (last 7 days)"""
    print("🐦 Scraping Twitter...")
    client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)
    
    tweets_data = []
    for stock in STOCKS:
        query = f"${stock} OR {stock} OR \"{stock}\" lang:en -is:retweet"
        tweets = client.search_recent_tweets(query=query, max_results=20)
        
        for tweet in tweets.data:
            tweets_data.append({
                "Platform": "Twitter",
                "Stock": stock,
                "Text": tweet.text,
                "Date": tweet.created_at,
                "User": tweet.author_id
            })
    
    pd.DataFrame(tweets_data).to_csv(f"data/twitter_{datetime.date.today()}.csv", index=False)
    print("✅ Twitter data saved!")

def scrape_reddit():
    """Search Reddit for stock mentions"""
    print("📱 Scraping Reddit...")
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent="JamaicanStockTracker/1.0"
    )
    
    reddit_data = []
    for stock in STOCKS:
        for submission in reddit.subreddit("all").search(stock, limit=10):
            reddit_data.append({
                "Platform": "Reddit",
                "Stock": stock,
                "Title": submission.title,
                "Text": submission.selftext,
                "Date": datetime.datetime.fromtimestamp(submission.created_utc),
                "User": submission.author.name if submission.author else "Anonymous"
            })
    
    pd.DataFrame(reddit_data).to_csv(f"data/reddit_{datetime.date.today()}.csv", index=False)
    print("✅ Reddit data saved!")

if __name__ == "__main__":
    scrape_jamstockex()
    scrape_twitter()  # Uncomment after adding API keys
    scrape_reddit()   # Uncomment after adding API keys
