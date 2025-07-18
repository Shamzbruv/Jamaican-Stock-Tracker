import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import datetime
from wordcloud import WordCloud

def generate_report():
    print("📊 Generating report...")
    today = datetime.date.today()
    
    # Load all data
    prices = pd.read_csv(f"data/prices_{today}.csv")
    twitter = pd.read_csv(f"data/twitter_{today}.csv") if os.path.exists(f"data/twitter_{today}.csv") else None
    reddit = pd.read_csv(f"data/reddit_{today}.csv") if os.path.exists(f"data/reddit_{today}.csv") else None
    
    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Jamaican Stock Report - {today}", 0, 1, "C")
    
    # Price chart
    plt.figure(figsize=(12, 6))
    prices["Close"] = prices["Close"].astype(float)
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
        all_text = " ".join(twitter["Text"].tolist() + reddit["Text"].tolist())
        wordcloud = WordCloud(width=800, height=400).generate(all_text)
        wordcloud.to_file("wordcloud.png")
        pdf.image("wordcloud.png", x=25, y=120, w=160)
    
    pdf.output("report.pdf")
    print("✅ Report generated!")

if __name__ == "__main__":
    generate_report()
