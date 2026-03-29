# =========================================================
# PHONEPE TRANSACTION INSIGHTS - PDF REPORT GENERATOR
# ReportLab-based final analytical submission report
# =========================================================

import os
import textwrap
import pandas as pd

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak,
    Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT

# ---------------------------------------------------------
# 1. FILE PATHS
# ---------------------------------------------------------
REPORT_PATH = "PhonePe_Transaction_Insights_Report.pdf"
EDA_OUTPUT_DIR = "eda_outputs"

insights_csv = os.path.join(EDA_OUTPUT_DIR, "eda_chart_insights.csv")
hypothesis_csv = os.path.join(EDA_OUTPUT_DIR, "hypothesis_results.csv")

required_plot_files = [
    "u1_transaction_amount_hist.png",
    "u2_transaction_count_hist.png",
    "u3_transaction_amount_box.png",
    "u4_records_by_quarter.png",
    "u5_top_types_amount.png",
    "b1_year_vs_amount.png",
    "b2_year_vs_count.png",
    "b3_count_vs_amount.png",
    "b4_top_states_amount.png",
    "b5_quarter_avg_ticket.png",
    "m1_year_quarter_heatmap.png",
    "m2_state_type_heatmap.png",
    "m3_time_trend_by_type.png",
    "m4_scatter_count_amount_quarter_year.png",
    "m5_box_type_quarter.png",
]

# ---------------------------------------------------------
# 2. VALIDATION
# ---------------------------------------------------------
if not os.path.exists(insights_csv):
    raise FileNotFoundError("eda_chart_insights.csv not found. Run EDA first.")

if not os.path.exists(hypothesis_csv):
    raise FileNotFoundError("hypothesis_results.csv not found. Run EDA first.")

chart_df = pd.read_csv(insights_csv)
hyp_df = pd.read_csv(hypothesis_csv)

# ---------------------------------------------------------
# 3. STYLES
# ---------------------------------------------------------
styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "TitleStyle",
    parent=styles["Title"],
    fontSize=20,
    leading=24,
    alignment=TA_CENTER,
    textColor=colors.darkblue,
    spaceAfter=20
)

heading_style = ParagraphStyle(
    "HeadingStyle",
    parent=styles["Heading1"],
    fontSize=15,
    leading=18,
    textColor=colors.HexColor("#0b5394"),
    spaceAfter=10
)

subheading_style = ParagraphStyle(
    "SubHeadingStyle",
    parent=styles["Heading2"],
    fontSize=12,
    leading=15,
    textColor=colors.HexColor("#1c4587"),
    spaceAfter=8
)

body_style = ParagraphStyle(
    "BodyStyle",
    parent=styles["BodyText"],
    fontSize=10,
    leading=14,
    alignment=TA_JUSTIFY,
    spaceAfter=8
)

small_style = ParagraphStyle(
    "SmallStyle",
    parent=styles["BodyText"],
    fontSize=9,
    leading=12,
    alignment=TA_LEFT,
    spaceAfter=6
)

# ---------------------------------------------------------
# 4. REPORT HELPERS
# ---------------------------------------------------------
def para(text, style=body_style):
    return Paragraph(str(text).replace("\n", "<br/>"), style)

def format_p_value(p):
    try:
        p = float(p)
        return "< 0.0001" if p < 0.0001 else f"{p:.4f}"
    except Exception:
        return str(p)

def add_chart_block(story, title, why_chosen, results, insights, result_summary, image_path=None):
    story.append(Paragraph(str(title), subheading_style))
    story.append(para(f"<b>Why this chart was chosen:</b> {why_chosen}"))
    story.append(para(f"<b>Results:</b> {results}"))
    story.append(para(f"<b>Insights:</b> {insights}"))
    story.append(para(f"<b>Result:</b> {result_summary}"))

    if image_path and os.path.exists(image_path):
        img = Image(image_path, width=6.7 * inch, height=3.4 * inch)
        story.append(img)
        story.append(Spacer(1, 10))

def add_hypothesis_block(story, row):
    p_val = format_p_value(row["p_value"])
    story.append(Paragraph(str(row["test_name"]), subheading_style))
    story.append(para(f"<b>Why this was chosen:</b> {row['why_chosen']}"))
    story.append(para(f"<b>Null Hypothesis (H0):</b> {row['null_hypothesis']}"))
    story.append(para(f"<b>Alternate Hypothesis (H1):</b> {row['alternate_hypothesis']}"))
    story.append(para(f"<b>Test Statistic:</b> {row['test_stat']}"))
    story.append(para(f"<b>P-Value:</b> {p_val}"))
    story.append(para(f"<b>Result:</b> {row['result']}"))
    story.append(para(f"<b>Insights:</b> {row['insights']}"))
    story.append(Spacer(1, 8))

# ---------------------------------------------------------
# 5. BUILD REPORT
# ---------------------------------------------------------
doc = SimpleDocTemplate(
    REPORT_PATH,
    pagesize=A4,
    rightMargin=30,
    leftMargin=30,
    topMargin=30,
    bottomMargin=30
)

story = []

# ---------------------------------------------------------
# COVER PAGE
# ---------------------------------------------------------
story.append(Paragraph("PhonePe Transaction Insights", title_style))
story.append(Spacer(1, 8))
story.append(para(
    "This analytical report presents a complete data exploration and business interpretation of PhonePe transaction data. "
    "The project focuses on transaction amount, transaction volume, state-level performance, district-level trends, "
    "category-wise contribution, and seasonal behavior across time. The goal is to convert raw transactional records into "
    "actionable business intelligence for strategic decisions."
))
story.append(Spacer(1, 12))

# ---------------------------------------------------------
# PROBLEM STATEMENT
# ---------------------------------------------------------
story.append(Paragraph("1. Project Problem Statement", heading_style))
story.append(para(
    "With the increasing adoption of digital payment systems, it becomes essential to understand user payment behavior, "
    "geographical transaction patterns, category-wise contribution, and overall platform growth. "
    "The purpose of this project is to analyze PhonePe transaction data, identify top-performing regions and categories, "
    "detect time-based trends, and derive business insights that can support decision-making, targeting, and product strategy."
))
story.append(para(
    "The project is based on the broader objective of analyzing transaction dynamics, user engagement, geographical insights, "
    "payment performance, trend analysis, and strategic business recommendations through SQL, Python, and dashboarding workflows."
))

# ---------------------------------------------------------
# PROJECT SUMMARY
# ---------------------------------------------------------
story.append(Paragraph("2. Project Summary", heading_style))
story.append(para(
    "This project performs structured exploratory data analysis on PhonePe transactional records. "
    "The analysis includes 15 visualizations divided into univariate, bivariate, and multivariate sections, "
    "along with 3 statistical hypothesis tests. Each visual has been interpreted from both analytical and business perspectives. "
    "The final outcome is a report that explains market concentration, growth patterns, category dominance, quarter-wise variation, "
    "and transaction value behavior."
))
story.append(para(
    "The analytical workflow covers data cleaning, feature engineering, descriptive analysis, visual exploration, statistical testing, "
    "and synthesis of findings into client-ready recommendations."
))

# ---------------------------------------------------------
# EDA SECTIONS
# ---------------------------------------------------------
story.append(PageBreak())
story.append(Paragraph("3. Exploratory Data Analysis", heading_style))
story.append(para(
    "The EDA is divided into three levels: univariate analysis for understanding individual variables, "
    "bivariate analysis for studying relationships between two variables, and multivariate analysis for uncovering complex interaction patterns."
))

sections = ["Univariate", "Bivariate", "Multivariate"]
image_map = {
    "U1. Distribution of Transaction Amount": "u1_transaction_amount_hist.png",
    "U2. Distribution of Transaction Count": "u2_transaction_count_hist.png",
    "U3. Boxplot of Transaction Amount": "u3_transaction_amount_box.png",
    "U4. Number of Records by Quarter": "u4_records_by_quarter.png",
    "U5. Top Transaction Types by Total Amount": "u5_top_types_amount.png",
    "B1. Year vs Total Transaction Amount": "b1_year_vs_amount.png",
    "B2. Year vs Total Transaction Count": "b2_year_vs_count.png",
    "B3. Transaction Count vs Transaction Amount": "b3_count_vs_amount.png",
    "B4. Top 10 States by Transaction Amount": "b4_top_states_amount.png",
    "B5. Quarter vs Average Ticket Size": "b5_quarter_avg_ticket.png",
    "M1. Heatmap of Transaction Amount by Year and Quarter": "m1_year_quarter_heatmap.png",
    "M2. Top States vs Transaction Type Heatmap": "m2_state_type_heatmap.png",
    "M3. Time Trend by Top Transaction Types": "m3_time_trend_by_type.png",
    "M4. Count vs Amount by Quarter and Year": "m4_scatter_count_amount_quarter_year.png",
    "M5. Transaction Amount by Type across Quarters": "m5_box_type_quarter.png",
}

for sec in sections:
    story.append(Paragraph(f"{sec} Analysis", subheading_style))
    sec_rows = chart_df[chart_df["section"] == sec]

    for _, row in sec_rows.iterrows():
        img_file = image_map.get(row["chart_title"], None)
        img_path = os.path.join(EDA_OUTPUT_DIR, img_file) if img_file else None

        add_chart_block(
            story=story,
            title=row["chart_title"],
            why_chosen=row["why_chosen"],
            results=str(row["results"]),
            insights=row["insights"],
            result_summary=row["result_summary"],
            image_path=img_path
        )

# ---------------------------------------------------------
# HYPOTHESIS TESTING
# ---------------------------------------------------------
story.append(PageBreak())
story.append(Paragraph("4. Hypothesis Testing", heading_style))
story.append(para(
    "To validate whether observed visual patterns are statistically meaningful, three hypothesis tests were conducted. "
    "These tests examine quarter-wise spending variation, performance difference between top and other states, "
    "and association between transaction type and quarter."
))

for _, row in hyp_df.iterrows():
    add_hypothesis_block(story, row)

# ---------------------------------------------------------
# HYPOTHESIS TEST SUMMARY TABLE
# MOVED BEFORE BUSINESS INSIGHTS
# ---------------------------------------------------------
story.append(Paragraph("5. Hypothesis Test Summary Table", heading_style))

table_data = [["Test Name", "P-Value", "Result"]]
for _, row in hyp_df.iterrows():
    table_data.append([
        str(row["test_name"]),
        format_p_value(row["p_value"]),
        str(row["result"])
    ])

summary_table = Table(table_data, colWidths=[3.7 * inch, 1.0 * inch, 1.8 * inch])
summary_table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1c4587")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 9),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
    ("TOPPADDING", (0, 0), (-1, 0), 6),
]))
story.append(summary_table)
story.append(Spacer(1, 12))

# ---------------------------------------------------------
# BUSINESS INSIGHTS
# ---------------------------------------------------------
story.append(Paragraph("6. Business Insights", heading_style))
business_insights = [
    "High-performing states account for a disproportionately large share of total transaction value, indicating strong regional concentration.",
    "Transaction growth over time reflects increasing platform adoption and digital payment dependence.",
    "Some payment categories dominate total transaction amount, suggesting areas where customer preference is strongest.",
    "Quarter-wise variation in average ticket size suggests seasonal or campaign-linked user behavior.",
    "The relationship between transaction count and amount indicates whether growth is volume-driven or value-driven.",
    "Regional and category-level differences suggest the need for localized product, marketing, and retention strategies."
]

for i, insight in enumerate(business_insights, start=1):
    story.append(para(f"<b>{i}.</b> {insight}"))

# ---------------------------------------------------------
# CLIENT RECOMMENDATIONS
# ---------------------------------------------------------
story.append(Paragraph("7. Client Recommendations", heading_style))
recommendations = [
    "Prioritize top-performing states for premium campaigns, loyalty programs, and product cross-sell opportunities.",
    "Develop region-specific marketing strategies because state and district performance is not uniform.",
    "Invest more in the most valuable payment categories and analyze why they outperform others.",
    "Use quarter-level trends to schedule campaigns during high-spending periods and improve performance during weaker quarters.",
    "Monitor outlier regions and transaction spikes separately for fraud checks, campaign evaluation, and business opportunity discovery.",
    "Use dashboard-driven real-time tracking to continuously monitor transaction amount, count, category, and geography."
]

for i, rec in enumerate(recommendations, start=1):
    story.append(para(f"<b>{i}.</b> {rec}"))

# ---------------------------------------------------------
# 5 MAJOR CONCLUSIONS
# ---------------------------------------------------------
story.append(Paragraph("8. Five Major Conclusions", heading_style))
major_conclusions = [
    "PhonePe transaction activity is not evenly distributed; a limited number of states and categories drive a significant portion of the total value.",
    "Transaction amount and transaction count are strongly connected, showing that higher usage generally leads to higher monetary throughput.",
    "Quarter-wise and year-wise patterns indicate that digital payment activity changes over time and should be studied seasonally.",
    "Category behavior differs across states, meaning regional user preference plays an important role in platform strategy.",
    "Statistical testing supports that some observed differences are not random, strengthening the reliability of the analytical conclusions."
]

for i, conc in enumerate(major_conclusions, start=1):
    story.append(para(f"<b>{i}.</b> {conc}"))

# ---------------------------------------------------------
# PROJECT CLOSING SUMMARY
# ---------------------------------------------------------
story.append(Paragraph("9. Final Project Summary", heading_style))
story.append(para(
    "This project successfully transforms raw PhonePe transaction data into structured analytical intelligence. "
    "Through EDA, statistical testing, and visual reporting, it highlights growth trends, market concentration, "
    "regional disparities, seasonal patterns, and category contribution. The report supports both technical understanding "
    "and business decision-making, making it suitable for academic submission, portfolio presentation, and dashboard extension."
))

# ---------------------------------------------------------
# BUILD PDF
# ---------------------------------------------------------
doc.build(story)

print(f"PDF report generated successfully: {REPORT_PATH}")