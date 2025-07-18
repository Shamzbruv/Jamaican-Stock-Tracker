import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import datetime

def generate_report():
    print("📈 Generating report...")
    today = datetime.date.today()
    
    # Load data
    df = pd.read_csv(f"data/prices_{today}.csv")
    
    # Create plot
    plt.figure(figsize=(12, 6))
    df["Close"] = df["Close"].astype(float)
    df.plot(x="Symbol", y="Close", kind="bar", color="#1f77b4")
    plt.title(f"Jamaican Stock Prices - {today}", pad=20)
    plt.ylabel("Price (JMD)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig("plot.png", dpi=300, bbox_inches="tight")
    
    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Jamaican Stock Report - {today}", 0, 1, "C")
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.image("plot.png", x=10, y=30, w=190)
    pdf.output("report.pdf")
    print("✅ PDF report saved!")

if __name__ == "__main__":
    generate_report()
