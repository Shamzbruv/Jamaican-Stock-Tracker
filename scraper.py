import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import os

# Stocks to track (edit if needed)
STOCKS = ["SCI", "DTC", "FESCO", "GHL", "TBCL", "DOLLA", "ONE", "TJH"]

def scrape_jamstockex():
    print("📡 Scraping JamStockEx...")
    url = "https://www.jamstockex.com/trading/trade-summary/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'trade-summary-table'})
        data = []
        for row in table.find_all('tr')[1:]:  # Skip header
            cols = row.find_all('td')
            data.append([col.text.strip() for col in cols])
        df = pd.DataFrame(data, columns=['Symbol', 'Open', 'High', 'Low', 'Close', 'Volume'])
        df.to_csv(f"data/jamstockex_{datetime.date.today()}.csv", index=False)
        print("✅ Data saved to GitHub!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    scrape_jamstockex()
