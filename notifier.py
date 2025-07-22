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
            raise ValueError("ALERT_WEBHOOK_URL or EMAIL_WEBHOOK_URL not set in .env")
        
    def send_daily_alert(self):
        """Send daily alert to #alerts channel"""
        webhook = DiscordWebhook(url=self.alert_webhook_url)
        embed = DiscordEmbed(
            title="⚠️ Daily Research Alert",
            description="Research has been completed for the day. Check the report for details.",
            color=0xffff00  # Yellow
        )
        embed.set_footer(text="Automated Alert | Data updates daily at 1PM Jamaica Time")
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
            print(f"❌ Failed to send daily alert: {str(e)}")
            return False

    def send_friday_analysis(self):
        """Send detailed analysis to #email channel on Fridays"""
        webhook = DiscordWebhook(url=self.email_webhook_url)
        today = datetime.now().strftime("%Y-%m-%d")
        embed = DiscordEmbed(
            title=f"📊 Friday Detailed Analysis - {today}",
            color=0x00ff00  # Green
        )
        
        # Load and analyze data
        prices_file = f"data/prices_{today}.csv"
        if os.path.exists(prices_file):
            df = pd.read_csv(prices_file)
            df["Change"] = ((df["Close"].astype(float) - df["Open"].astype(float)) / df["Open"].astype(float)) * 100
            top_mover = df.loc[df["Change"].abs().idxmax()]
            embed.add_embed_field(
                name="💹 Top Mover",
                value=f"{top_mover['Symbol']}: {top_mover['Change']:.2f}% change (Close: ${top_mover['Close']})",
                inline=False
            )
        
        # Social media and news counts
        social_count = 0
        twitter_file = f"data/twitter_{today}.csv"
        if os.path.exists(twitter_file):
            social_count += len(pd.read_csv(twitter_file))
        reddit_file = f"data/reddit_{today}.csv"
        if os.path.exists(reddit_file):
            social_count += len(pd.read_csv(reddit_file))
        news_file = f"data/news_{today}.csv"
        if os.path.exists(news_file):
            social_count += len(pd.read_csv(news_file))
        embed.add_embed_field(
            name="📱 Social & News Activity",
            value=f"Total mentions/discussions: {social_count}",
            inline=True
        )
        
        embed.set_footer(text="Automated Friday Analysis | Use DeepSite data for visualization")
        webhook.add_embed(embed)
        
        # Attach files (report, charts, DeepSite data)
        files_to_attach = ["report.pdf", "price_chart.png", "wordcloud.png", "volume_chart.png", "deepsite_data.json"]
        for file in files_to_attach:
            if os.path.exists(file):
                with open(file, "rb") as f:
                    webhook.add_file(file=f.read(), filename=file)
        
        try:
            response = webhook.execute()
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Failed to send Friday analysis: {str(e)}")
            return False

    def send_report(self):
        """Send notification based on day of week"""
        today = datetime.datetime.now()
        if today.weekday() == 4:  # Friday
            return self.send_friday_analysis()
        else:
            return self.send_daily_alert()

if __name__ == "__main__":
    notifier = DiscordNotifier()
    if notifier.send_report():
        print("✅ Discord notification sent!")
    else:
        print("❌ Failed to send Discord notification")
