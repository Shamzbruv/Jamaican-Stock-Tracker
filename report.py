import os
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import datetime
from wordcloud import WordCloud

def generate_report():
    print("📊 Generating report...")
    today = datetime.date.today()
    
    # Check if prices file exists
    prices_file = f"data/prices_{today}.csv"
    if not os.path.exists(prices_file):
        print(f"❌ {prices_file} not found, skipping report generation")
        return
    
    # Load all data
    prices = pd.read_csv(prices_file)
    twitter = pd.read_csv(f"data/twitter_{today}.csv") if os.path.exists(f"data/twitter_{today}.csv") else None
    reddit = pd.read_csv(f"data/reddit_{today}.csv") if os.path.exists(f"data/reddit_{today}.csv") else None
    
    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Jamaican Stock Report - {today}", 0, 1, "C")
    
    # Price chart
    plt.figure(figsize=(12, 6)
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

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    generate_report()
