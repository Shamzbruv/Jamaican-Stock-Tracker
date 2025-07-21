import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
from datetime import datetime

def send_email():
    # === CONFIGURATION ===
    EMAIL_USER = "your.email@gmail.com"  # REPLACE WITH YOUR EMAIL
    EMAIL_PASSWORD = "your-app-password"  # REPLACE WITH 16-DIGIT APP PASSWORD
    RECIPIENT_EMAIL = "your.email@gmail.com"  # REPLACE IF DIFFERENT
    
    # === EMAIL CONTENT ===
    msg = MIMEMultipart()
    msg['From'] = f"Stock Bot <{EMAIL_USER}>"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = f"📈 Jamaican Stock Report - {datetime.now().strftime('%Y-%m-%d')}"
    
    # HTML Body
    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif;">
        <h2 style="color: #2e86c1;">Jamaican Stock Tracker Report</h2>
        <p>Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Jamaica Time)</p>
        
        <h3 style="color: #28b463;">📊 Key Metrics</h3>
        <ul>
          <li>8 stocks monitored</li>
          <li>14 executives tracked</li>
          <li>3 news sources analyzed</li>
        </ul>
        
        <p>See attachments for full details.</p>
      </body>
    </html>
    """
    msg.attach(MIMEText(html, 'html'))
    
    # === ATTACH FILES ===
    today = datetime.now().strftime("%Y-%m-%d")
    files_to_attach = [
        f"data/prices_{today}.csv",
        f"reports/report_{today}.pdf"
    ]
    
    for file_path in files_to_attach:
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                part = MIMEApplication(f.read(), Name=os.path.basename(file_path))
                part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                msg.attach(part)
    
    # === SEND EMAIL ===
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_USER, RECIPIENT_EMAIL, msg.as_string())
        print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")

if __name__ == "__main__":
    send_email()
