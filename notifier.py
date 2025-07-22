import os
from discord_webhook import DiscordWebhook, DiscordEmbed
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DiscordNotifier:
    def __init__(self):
        self.webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        if not self.webhook_url:
            raise ValueError("DISCORD_WEBHOOK_URL not set in .env")
        
    def create_embed(self):
        """Build rich Discord embed"""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        embed = DiscordEmbed(
            title=f"📊 Jamaican Stock Report - {today}",
            color=0x00ff00  # Green
        )
        
        # Add market data
        prices_file = f"data/prices_{today}.csv"
        price_changes = []
        if os.path.exists(prices_file):
            df = pd.read_csv(prices_file)
            for _, row in df.iterrows():
                try:
                    open_price = float(row['Open'])
                    close_price = float(row['Close'])
                    change = ((close_price - open_price) / open_price) * 100 if open_price != 0 else 0
                    arrow = "▲" if change > 0 else "▼"
                    price_changes.append(
                        f"{row['Symbol']}: {arrow}{abs(change):.2f}% (${close_price})"
                    )
                except (ValueError, ZeroDivisionError):
                    price_changes.append(f"{row['Symbol']}: Invalid data")
        
        embed.add_embed_field(
            name="💹 Today's Movers",
            value="\n".join(price_changes) or "No price data available",
            inline=False
        )
        
        # Add social stats
        twitter_count = len(pd.read_csv(f"data/twitter_{today}.csv")) if os.path.exists(f"data/twitter_{today}.csv") else 0
        reddit_count = len(pd.read_csv(f"data/reddit_{today}.csv")) if os.path.exists(f"data/reddit_{today}.csv") else 0
        embed.add_embed_field(
            name="📱 Social Activity",
            value=f"• {twitter_count} Twitter mentions\n"
                  f"• {reddit_count} Reddit discussions",
            inline=True
        )
        
        embed.set_footer(text="Automated Report | Data updates daily at 1PM Jamaica Time")
        return embed

    def send_report(self):
        """Send rich notification with file attachments"""
        webhook = DiscordWebhook(url=self.webhook_url)
        embed = self.create_embed()
        webhook.add_embed(embed)
        
        # Attach latest report
        report_file = "report.pdf"
        if os.path.exists(report_file):
            with open(report_file, "rb") as f:
                webhook.add_file(file=f.read(), filename='market_report.pdf')
        
        try:
            response = webhook.execute()
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Failed to send Discord notification: {str(e)}")
            return False

if __name__ == "__main__":
    notifier = DiscordNotifier()
    if notifier.send_report():
        print("✅ Discord notification sent!")
    else:
        print("❌ Failed to send Discord notification")
