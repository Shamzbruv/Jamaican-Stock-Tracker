import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import os

STOCKS = ["SCI", "DTC", "FESCO", "GHL", "TBCL", "DOLLA", "ONE", "TJH"]

def scrape_jamstockex():
    print("🔄 Scraping JamStockEx...")
    url = "https://www.jamstockex.com/trading/trade-summary/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", {"class": "trade-summary-table"})
        
        data = []
        for row in table.find_all("tr")[1:]:  # Skip header row
            cols = row.find_all("td")
            if len(cols) >= 6:
                data.append({
                    "Symbol": cols[0].text.strip(),
                    "Open": cols[1].text.strip(),
                    "High": cols[2].text.strip(),
                    "Low": cols[3].text.strip(),
                    "Close": cols[4].text.strip(),
                    "Volume": cols[5].text.strip().replace(",", "")
                })
        
        df = pd.DataFrame(data)
        os.makedirs("data", exist_ok=True)
        df.to_csv(f"data/prices_{datetime.date.today()}.csv", index=False)
        print("✅ Data saved to data/ folder!")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    scrape_jamstockex()
