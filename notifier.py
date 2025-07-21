import os
from discord_webhook import DiscordWebhook, DiscordEmbed
import pandas as pd
from datetime import datetime

class DiscordNotifier:
    def __init__(self):
        self.webhook_url = "https://canary.discord.com/api/webhooks/1396984814644629535/LAmcVGpVy70kGAXBw6bTIK48WB9PcIo3ZJw-0sOTE2YbjgKNNaam4V3kOsyCbF2MvYZy"
        
    def create_embed(self):
        """Build rich Discord embed"""
        today = datetime.now().strftime("%Y-%m-%d")
        embed = DiscordEmbed(
            title=f"📊 Jamaican Stock Report - {today}",
            color=0x00ff00  # Green
        )
        
        # Add market data
        df = pd.read_csv(f"data/prices_{today}.csv")
        price_changes = []
        for _, row in df.iterrows():
            arrow = "▲" if float(row['Close']) > float(row['Open']) else "▼"
            change = abs(float(row['Close']) - float(row['Open']))
            price_changes.append(
                f"{row['Symbol']}: {arrow}{change:.2f}% (${row['Close']})"
            )
        
        embed.add_embed_field(
            name="💹 Today's Movers",
            value="\n".join(price_changes),
            inline=False
        )
        
        # Add social stats
        embed.add_embed_field(
            name="📱 Social Activity",
            value=f"• {len(pd.read_csv(f'data/twitter_{today}.csv'))} Twitter mentions\n"
                  f"• {len(pd.read_csv(f'data/reddit_{today}.csv'))} Reddit discussions",
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
        with open(f"reports/report_{datetime.now().strftime('%Y-%m-%d')}.pdf", "rb") as f:
            webhook.add_file(file=f.read(), filename='market_report.pdf')
        
        response = webhook.execute()
        return response.status_code == 200

if __name__ == "__main__":
    notifier = DiscordNotifier()
    if notifier.send_report():
        print("✅ Discord notification sent!")
    else:
        print("❌ Failed to send Discord notification")
