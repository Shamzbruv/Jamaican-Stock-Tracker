import os
from discord_webhook import DiscordWebhook, DiscordEmbed
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DiscordNotifier:
    def __init__(self):
        self.alert_webhook_url = os.getenv("ALERT_WEBHOOK_URL")
        self.email_webhook_url = os.getenv("EMAIL_WEBHOOK_URL")
        if not self.alert_webhook_url or not self.email_webhook_url:
            raise ValueError("Discord webhook URLs not set in .env")
        
    def send_daily_alert(self):
        webhook = DiscordWebhook(url=self.alert_webhook_url)
        embed = DiscordEmbed(
            title="Daily Research Alert",
            description="Research has been done for the day.",
            color=0x00ff00  # Green
        )
        webhook.add_embed(embed)
        try:
            response = webhook.execute()
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Failed to send daily alert: {str(e)}")
            return False

    def send_friday_analysis(self):
        webhook = DiscordWebhook(url=self.email_webhook_url)
        today = datetime.now().strftime("%Y-%m-%d")
        embed = DiscordEmbed(
            title=f"Friday Detailed Analysis - {today}",
            color=0xffa500  # Orange
        )
        
        # Load data for analysis
        prices_file = f"data/prices_{today}.csv"
        if os.path.exists(prices_file):
            df = pd.read_csv(prices_file)
            analysis = "Detailed stock price analysis:\n"
            for _, row in df.iterrows():
                analysis += f"{row['Symbol']}: Close ${row['Close']}, Volume {row['Volume']}\n"
            embed.add_embed_field(
                name="Stock Prices",
                value=analysis,
                inline=False
            )
        
        # Add more analysis as needed (e.g., from twitter, reddit)
        twitter_file = f"data/twitter_{today}.csv"
        if os.path.exists(twitter_file):
            twitter_df = pd.read_csv(twitter_file)
            twitter_count = len(twitter_df)
            embed.add_embed_field(
                name="Twitter Mentions",
                value=f"{twitter_count} mentions today",
                inline=True
            )
        
        reddit_file = f"data/reddit_{today}.csv"
        if os.path.exists(reddit_file):
            reddit_df = pd.read_csv(reddit_file)
            reddit_count = len(reddit_df)
            embed.add_embed_field(
                name="Reddit Discussions",
                value=f"{reddit_count} discussions today",
                inline=True
            )
        
        embed.set_footer(text="Automated Friday Analysis | Data updates weekly")

        webhook.add_embed(embed)
        
        # Attach report.pdf if exists
        report_file = "report.pdf"
        if os.path.exists(report_file):
            with open(report_file, "rb") as f:
                webhook.add_file(file=f.read(), filename='market_report.pdf')
        
        try:
            response = webhook.execute()
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Failed to send Friday analysis: {str(e)}")
            return False

    def send_report(self):
        today = datetime.now()
        if today.weekday() == 4:  # Friday (0=Monday, 4=Friday)
            return self.send_friday_analysis()
        else:
            return self.send_daily_alert()

if __name__ == "__main__":
    notifier = DiscordNotifier()
    if notifier.send_report():
        print("✅ Discord notification sent!")
    else:
        print("❌ Failed to send Discord notification")
