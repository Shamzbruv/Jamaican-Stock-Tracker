import os
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import datetime
from wordcloud import WordCloud
import json

def generate_report():
    print("📊 Generating report...")
    today = datetime.date.today()
    is_friday = today.weekday() == 4  # 4 is Friday
    
    # Check if prices file exists
    prices_file = f"data/prices_{today}.csv"
    if not os.path.exists(prices_file):
        print(f"❌ {prices_file} not found, skipping report generation")
        return
    
    # Load all data
    prices = pd.read_csv(prices_file)
    twitter = pd.read_csv(f"data/twitter_{today}.csv") if os.path.exists(f"data/twitter_{today}.csv") else None
    reddit = pd.read_csv(f"data/reddit_{today}.csv") if os.path.exists(f"data/reddit_{today}.csv") else None
    news = pd.read_csv(f"data/news_{today}.csv") if os.path.exists(f"data/news_{today}.csv") else None
    
    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Jamaican Stock Report - {today}", 0, 1, "C")
    
    # Price chart
    plt.figure(figsize=(12, 6))
    prices["Close"] = pd.to_numeric(prices["Close"], errors="coerce").fillna(0)
    prices.plot(x="Symbol", y="Close", kind="bar", color="#1f77b4")
    plt.title("Stock Prices", pad=20)
    plt.ylabel("Price (JMD)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("price_chart.png", dpi=300)
    pdf.image("price_chart.png", x=10, y=30, w=190)
    
    # Social media analysis (if data exists)
    if twitter is not None or reddit is not None:
        pdf.ln(85)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Social Media Mentions", 0, 1)
        
        # Word cloud
        all_text = " ".join(twitter["Text"].tolist() if twitter is not None else []) + \
                   " ".join((reddit["Title"] + " " + reddit["Content"]).tolist() if reddit is not None else [])
        if all_text.strip():
            wordcloud = WordCloud(width=800, height=400).generate(all_text)
            wordcloud.to_file("wordcloud.png")
            pdf.image("wordcloud.png", x=25, y=120, w=160)
    
    try:
        pdf.output("report.pdf")
        print("✅ Report generated!")
    except Exception as e:
        print(f"❌ Failed to generate report: {str(e)}")
    
    # On Fridays, generate additional detailed visualization and DeepSite data
    if is_friday:
        # Additional chart: Volume bar chart
        plt.figure(figsize=(12, 6))
        prices["Volume"] = pd.to_numeric(prices["Volume"], errors="coerce").fillna(0)
        prices.plot(x="Symbol", y="Volume", kind="bar", color="#ff7f0e")
        plt.title("Stock Volumes", pad=20)
        plt.ylabel("Volume")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig("volume_chart.png", dpi=300)

        # Prepare structured data for DeepSite
        deepsite_data = {
            "stocks": prices.to_dict(orient="records"),
            "twitter_mentions": twitter.to_dict(orient="records") if twitter is not None else [],
            "reddit_discussions": reddit.to_dict(orient="records") if reddit is not None else [],
            "news_articles": news.to_dict(orient="records") if news is not None else []
        }
        with open("deepsite_data.json", "w") as f:
            json.dump(deepsite_data, f, indent=4)
        print("✅ DeepSite data generated for Friday analysis!")

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    generate_report()
