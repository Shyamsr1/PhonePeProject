# ============================================
# PHONEPE TRANSACTION INSIGHTS - FULL EDA
# 15 CHARTS + 3 HYPOTHESIS TESTS + INSIGHTS
# ============================================

import os
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from pathlib import Path
from scipy.stats import f_oneway, ttest_ind, chi2_contingency, pearsonr

# -----------------------------
# 1. SETTINGS
# -----------------------------
plt.rcParams["figure.figsize"] = (12, 6)
plt.rcParams["axes.titlesize"] = 14
plt.rcParams["axes.labelsize"] = 12
sns.set_style("whitegrid")

# -----------------------------
# 2. LOAD DATA
# -----------------------------
# Replace this with actual cleaned CSV exported from SQL / ETL
# Example expected columns:
# state, district, year, quarter, transaction_type, transaction_count, transaction_amount

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "phonepe_cleaned.csv"

if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(
        f"{DATA_PATH} not found. Export the SQL data into a CSV with columns like:\n"
        f"state, district, year, quarter, transaction_type, transaction_count, transaction_amount"
    )


df = pd.read_csv(DATA_PATH)

# -----------------------------
# 3. BASIC CLEANING
# -----------------------------
df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

required_cols = [
    "state", "district", "year", "quarter",
    "transaction_type", "transaction_count", "transaction_amount"
]

missing_cols = [c for c in required_cols if c not in df.columns]
if missing_cols:
    raise ValueError(f"Missing required columns: {missing_cols}")

df["state"] = df["state"].astype(str).str.title()
df["district"] = df["district"].astype(str).str.title()
df["transaction_type"] = df["transaction_type"].astype(str).str.title()

df["year"] = pd.to_numeric(df["year"], errors="coerce")
df["quarter"] = pd.to_numeric(df["quarter"], errors="coerce")
df["transaction_count"] = pd.to_numeric(df["transaction_count"], errors="coerce")
df["transaction_amount"] = pd.to_numeric(df["transaction_amount"], errors="coerce")

df = df.dropna(subset=required_cols).copy()

# Derived feature
df["avg_ticket_size"] = np.where(
    df["transaction_count"] > 0,
    df["transaction_amount"] / df["transaction_count"],
    0
)

print("Shape:", df.shape)
print(df.head())
print(df.info())

# -----------------------------
# 4. OVERALL SUMMARY
# -----------------------------
summary = {
    "total_transactions": df["transaction_count"].sum(),
    "total_amount": df["transaction_amount"].sum(),
    "avg_ticket_size": df["avg_ticket_size"].mean(),
    "num_states": df["state"].nunique(),
    "num_districts": df["district"].nunique(),
    "num_transaction_types": df["transaction_type"].nunique(),
    "year_range": f"{int(df['year'].min())} - {int(df['year'].max())}"
}

print("\n===== OVERALL SUMMARY =====")
for k, v in summary.items():
    print(f"{k}: {v}")

# -----------------------------
# 5. HELPER FUNCTIONS
# -----------------------------
INSIGHTS = []

def add_insight(section, chart_title, why_chosen, results, insights, result_summary):
    """
    Store all chart/test explanations so they can later be used in PDF report too.
    """
    INSIGHTS.append({
        "section": section,
        "chart_title": chart_title,
        "why_chosen": why_chosen,
        "results": results,
        "insights": insights,
        "result_summary": result_summary
    })

def show_and_save(title, filename=None):
    plt.title(title)
    plt.tight_layout()
    if filename:
        plt.savefig(filename, dpi=300, bbox_inches="tight")
    plt.show()

# Create folder for plots
os.makedirs("eda_outputs", exist_ok=True)

# ==========================================================
# 6. UNIVARIATE ANALYSIS (5 CHARTS)
# ==========================================================

# ----------------------------------------------------------
# U1. Histogram - Transaction Amount Distribution
# ----------------------------------------------------------
plt.figure()
sns.histplot(df["transaction_amount"], bins=30, kde=True)
show_and_save("U1. Distribution of Transaction Amount", "eda_outputs/u1_transaction_amount_hist.png")

u1_results = (
    f"Transaction amount ranges from {df['transaction_amount'].min():,.2f} "
    f"to {df['transaction_amount'].max():,.2f}. "
    f"Mean amount = {df['transaction_amount'].mean():,.2f}, "
    f"Median = {df['transaction_amount'].median():,.2f}."
)
u1_insights = (
    "The distribution helps identify whether transaction values are concentrated in a narrow band "
    "or spread widely. A strong right skew usually indicates that a small number of records contribute "
    "very large transaction values compared with the majority."
)
add_insight(
    section="Univariate",
    chart_title="U1. Distribution of Transaction Amount",
    why_chosen="A histogram is chosen to understand the spread, skewness, concentration, and possible outliers in transaction amount.",
    results=u1_results,
    insights=u1_insights,
    result_summary="Transaction amount distribution reveals whether the platform is driven by many small transactions or a mix including very large high-value activity."
)

# ----------------------------------------------------------
# U2. Histogram - Transaction Count Distribution
# ----------------------------------------------------------
plt.figure()
sns.histplot(df["transaction_count"], bins=30, kde=True)
show_and_save("U2. Distribution of Transaction Count", "eda_outputs/u2_transaction_count_hist.png")

u2_results = (
    f"Transaction count ranges from {df['transaction_count'].min():,.0f} "
    f"to {df['transaction_count'].max():,.0f}. "
    f"Mean count = {df['transaction_count'].mean():,.2f}, "
    f"Median = {df['transaction_count'].median():,.2f}."
)
u2_insights = (
    "This chart shows whether user activity volume is balanced or concentrated. "
    "If highly skewed, a few state/district/category combinations may be dominating overall transaction traffic."
)
add_insight(
    section="Univariate",
    chart_title="U2. Distribution of Transaction Count",
    why_chosen="A histogram is used to inspect the frequency distribution and concentration of transaction volume.",
    results=u2_results,
    insights=u2_insights,
    result_summary="Transaction count distribution shows the operational load pattern and identifies heavy activity concentration."
)

# ----------------------------------------------------------
# U3. Boxplot - Transaction Amount Outliers
# ----------------------------------------------------------
plt.figure()
sns.boxplot(x=df["transaction_amount"])
show_and_save("U3. Boxplot of Transaction Amount", "eda_outputs/u3_transaction_amount_box.png")

q1 = df["transaction_amount"].quantile(0.25)
q3 = df["transaction_amount"].quantile(0.75)
iqr = q3 - q1
upper_bound = q3 + 1.5 * iqr
num_outliers = (df["transaction_amount"] > upper_bound).sum()

u3_results = (
    f"Q1 = {q1:,.2f}, Q3 = {q3:,.2f}, IQR = {iqr:,.2f}, "
    f"Estimated high-end outliers = {num_outliers}."
)
u3_insights = (
    "The boxplot highlights unusually large transaction amount values. "
    "These may represent peak market regions, seasonal effects, or exceptional transaction clusters "
    "that deserve separate business attention."
)
add_insight(
    section="Univariate",
    chart_title="U3. Boxplot of Transaction Amount",
    why_chosen="A boxplot is chosen to quickly detect spread, median, quartiles, and extreme values in transaction amount.",
    results=u3_results,
    insights=u3_insights,
    result_summary="Outlier analysis helps identify exceptional payment hotspots and abnormal transaction behavior."
)

# ----------------------------------------------------------
# U4. Countplot - Records by Quarter
# ----------------------------------------------------------
plt.figure()
sns.countplot(x=df["quarter"])
show_and_save("U4. Number of Records by Quarter", "eda_outputs/u4_records_by_quarter.png")

quarter_counts = df["quarter"].value_counts().sort_index().to_dict()
u4_results = f"Quarter-wise record distribution: {quarter_counts}"
u4_insights = (
    "This chart checks whether records are evenly represented across quarters. "
    "Uneven distribution may indicate data incompleteness or stronger reporting concentration in particular quarters."
)
add_insight(
    section="Univariate",
    chart_title="U4. Number of Records by Quarter",
    why_chosen="A countplot is used to verify quarter-level data coverage and temporal representation.",
    results=u4_results,
    insights=u4_insights,
    result_summary="Quarter distribution helps validate data completeness and seasonal representation."
)

# ----------------------------------------------------------
# U5. Top 10 Transaction Types by Total Amount
# ----------------------------------------------------------
type_amount = (
    df.groupby("transaction_type", as_index=False)["transaction_amount"]
    .sum()
    .sort_values("transaction_amount", ascending=False)
    .head(10)
)

plt.figure()
sns.barplot(data=type_amount, x="transaction_amount", y="transaction_type")
show_and_save("U5. Top Transaction Types by Total Amount", "eda_outputs/u5_top_types_amount.png")

u5_results = "Top transaction types by total amount:\n" + type_amount.to_string(index=False)
u5_insights = (
    "This chart shows which payment categories contribute the highest monetary value. "
    "These are the most commercially important transaction categories for growth and optimization."
)
add_insight(
    section="Univariate",
    chart_title="U5. Top Transaction Types by Total Amount",
    why_chosen="A horizontal bar chart is chosen for easy comparison of total transaction value across payment categories.",
    results=u5_results,
    insights=u5_insights,
    result_summary="Top payment categories reveal where most monetary throughput occurs."
)

# ==========================================================
# 7. BIVARIATE ANALYSIS (5 CHARTS)
# ==========================================================

# ----------------------------------------------------------
# B1. Line Plot - Year vs Total Transaction Amount
# ----------------------------------------------------------
yearly_amount = (
    df.groupby("year", as_index=False)["transaction_amount"].sum()
    .sort_values("year")
)

plt.figure()
sns.lineplot(data=yearly_amount, x="year", y="transaction_amount", marker="o")
show_and_save("B1. Year vs Total Transaction Amount", "eda_outputs/b1_year_vs_amount.png")

b1_results = "Year-wise total transaction amount:\n" + yearly_amount.to_string(index=False)
b1_insights = (
    "This trend line helps detect yearly growth or decline in PhonePe transaction value. "
    "A rising trend reflects increasing platform adoption and higher digital payment dependence."
)
add_insight(
    section="Bivariate",
    chart_title="B1. Year vs Total Transaction Amount",
    why_chosen="A line chart is best for analyzing changes over time and identifying long-term growth trends.",
    results=b1_results,
    insights=b1_insights,
    result_summary="Year-wise growth pattern shows whether transaction value is expanding steadily over time."
)

# ----------------------------------------------------------
# B2. Line Plot - Year vs Total Transaction Count
# ----------------------------------------------------------
yearly_count = (
    df.groupby("year", as_index=False)["transaction_count"].sum()
    .sort_values("year")
)

plt.figure()
sns.lineplot(data=yearly_count, x="year", y="transaction_count", marker="o")
show_and_save("B2. Year vs Total Transaction Count", "eda_outputs/b2_year_vs_count.png")

b2_results = "Year-wise total transaction count:\n" + yearly_count.to_string(index=False)
b2_insights = (
    "This chart measures growth in usage volume. Comparing amount growth with count growth also helps determine "
    "whether growth is driven by more transactions or larger ticket sizes."
)
add_insight(
    section="Bivariate",
    chart_title="B2. Year vs Total Transaction Count",
    why_chosen="A time-based line chart clearly shows whether transaction volume is increasing across years.",
    results=b2_results,
    insights=b2_insights,
    result_summary="Transaction count trend captures user activity growth and platform usage intensity."
)

# ----------------------------------------------------------
# B3. Scatter Plot - Transaction Count vs Amount
# ----------------------------------------------------------
plt.figure()
sns.scatterplot(data=df, x="transaction_count", y="transaction_amount", alpha=0.6)
show_and_save("B3. Transaction Count vs Transaction Amount", "eda_outputs/b3_count_vs_amount.png")

corr_val, corr_p = pearsonr(df["transaction_count"], df["transaction_amount"])
b3_results = (
    f"Pearson correlation between transaction count and amount = {corr_val:.4f}, p-value = {corr_p:.6f}"
)
b3_insights = (
    "A strong positive correlation means locations or categories with higher number of transactions also tend to generate "
    "higher total value. Weak correlation would imply inconsistent ticket sizes or uneven usage behavior."
)
add_insight(
    section="Bivariate",
    chart_title="B3. Transaction Count vs Transaction Amount",
    why_chosen="A scatter plot is chosen to examine the direct relationship between activity volume and monetary value.",
    results=b3_results,
    insights=b3_insights,
    result_summary="Correlation analysis shows whether transaction amount scales proportionally with transaction volume."
)

# ----------------------------------------------------------
# B4. Top 10 States by Transaction Amount
# ----------------------------------------------------------
state_amount = (
    df.groupby("state", as_index=False)["transaction_amount"]
    .sum()
    .sort_values("transaction_amount", ascending=False)
    .head(10)
)

plt.figure()
sns.barplot(data=state_amount, x="transaction_amount", y="state")
show_and_save("B4. Top 10 States by Transaction Amount", "eda_outputs/b4_top_states_amount.png")

b4_results = "Top 10 states by total transaction amount:\n" + state_amount.to_string(index=False)
b4_insights = (
    "This chart identifies the leading geographic contributors by value. "
    "These states are strong candidates for premium targeting, retention programs, and advanced service offerings."
)
add_insight(
    section="Bivariate",
    chart_title="B4. Top 10 States by Transaction Amount",
    why_chosen="A bar chart is ideal for ranking states by total transaction value.",
    results=b4_results,
    insights=b4_insights,
    result_summary="Top states reveal the strongest markets in terms of digital payment value."
)

# ----------------------------------------------------------
# B5. Quarter vs Average Ticket Size
# ----------------------------------------------------------
quarter_avg_ticket = (
    df.groupby("quarter", as_index=False)["avg_ticket_size"]
    .mean()
    .sort_values("quarter")
)

plt.figure()
sns.barplot(data=quarter_avg_ticket, x="quarter", y="avg_ticket_size")
show_and_save("B5. Quarter vs Average Ticket Size", "eda_outputs/b5_quarter_avg_ticket.png")

b5_results = "Quarter-wise average ticket size:\n" + quarter_avg_ticket.to_string(index=False)
b5_insights = (
    "This shows whether customers spend more per transaction in specific quarters. "
    "It is useful for understanding seasonality, campaign timing, and high-value payment periods."
)
add_insight(
    section="Bivariate",
    chart_title="B5. Quarter vs Average Ticket Size",
    why_chosen="A bar chart helps compare average transaction value across the four quarters.",
    results=b5_results,
    insights=b5_insights,
    result_summary="Quarter-wise average ticket size helps detect spending seasonality and campaign opportunities."
)

# ==========================================================
# 8. MULTIVARIATE ANALYSIS (5 CHARTS)
# ==========================================================

# ----------------------------------------------------------
# M1. Heatmap - Year x Quarter by Transaction Amount
# ----------------------------------------------------------
pivot_yq = pd.pivot_table(
    df,
    values="transaction_amount",
    index="year",
    columns="quarter",
    aggfunc="sum",
    fill_value=0
)

plt.figure(figsize=(10, 6))
sns.heatmap(pivot_yq, annot=True, fmt=".0f", cmap="YlGnBu")
show_and_save("M1. Heatmap of Transaction Amount by Year and Quarter", "eda_outputs/m1_year_quarter_heatmap.png")

m1_results = "Year-Quarter transaction amount matrix:\n" + pivot_yq.to_string()
m1_insights = (
    "The heatmap reveals seasonal peaks, weak periods, and year-quarter combinations with the highest business volume. "
    "It is excellent for pattern spotting across two time dimensions simultaneously."
)
add_insight(
    section="Multivariate",
    chart_title="M1. Heatmap of Transaction Amount by Year and Quarter",
    why_chosen="A heatmap is chosen to compare transaction amount across both year and quarter in a compact visual matrix.",
    results=m1_results,
    insights=m1_insights,
    result_summary="Year-quarter heatmap exposes combined seasonality and long-term trend intensity."
)

# ----------------------------------------------------------
# M2. Heatmap - Top 10 States x Transaction Type
# ----------------------------------------------------------
top_states = df.groupby("state")["transaction_amount"].sum().sort_values(ascending=False).head(10).index
df_top_states = df[df["state"].isin(top_states)]

pivot_state_type = pd.pivot_table(
    df_top_states,
    values="transaction_amount",
    index="state",
    columns="transaction_type",
    aggfunc="sum",
    fill_value=0
)

plt.figure(figsize=(14, 7))
sns.heatmap(pivot_state_type, annot=True, fmt=".0f", cmap="OrRd")
show_and_save("M2. Top States vs Transaction Type Heatmap", "eda_outputs/m2_state_type_heatmap.png")

m2_results = "Top states by transaction type matrix:\n" + pivot_state_type.to_string()
m2_insights = (
    "This chart helps compare how transaction categories behave across leading states. "
    "It shows whether market leaders are driven by the same payment categories or different usage patterns."
)
add_insight(
    section="Multivariate",
    chart_title="M2. Top States vs Transaction Type Heatmap",
    why_chosen="A heatmap is best for comparing many state-category intersections together.",
    results=m2_results,
    insights=m2_insights,
    result_summary="State-category comparison reveals regional preference differences in payment behavior."
)

# ----------------------------------------------------------
# M3. Line Plot - Year x Quarter with hue by Transaction Type
# ----------------------------------------------------------
multi_trend = (
    df.groupby(["year", "quarter", "transaction_type"], as_index=False)["transaction_amount"]
    .sum()
)

multi_trend["year_quarter"] = multi_trend["year"].astype(int).astype(str) + "-Q" + multi_trend["quarter"].astype(int).astype(str)

top_types = (
    df.groupby("transaction_type")["transaction_amount"]
    .sum()
    .sort_values(ascending=False)
    .head(5)
    .index
)

multi_trend_filtered = multi_trend[multi_trend["transaction_type"].isin(top_types)]

plt.figure(figsize=(14, 6))
sns.lineplot(
    data=multi_trend_filtered,
    x="year_quarter",
    y="transaction_amount",
    hue="transaction_type",
    marker="o"
)
plt.xticks(rotation=45)
show_and_save("M3. Time Trend by Top Transaction Types", "eda_outputs/m3_time_trend_by_type.png")

m3_results = "Time trend by top transaction types prepared for top 5 categories."
m3_insights = (
    "This chart shows how leading transaction categories rise or decline over time. "
    "It is useful for identifying persistent winners, emerging categories, and volatile segments."
)
add_insight(
    section="Multivariate",
    chart_title="M3. Time Trend by Top Transaction Types",
    why_chosen="A multi-line chart is chosen to compare category-level time trends across periods.",
    results=m3_results,
    insights=m3_insights,
    result_summary="Multi-category time trends reveal evolving payment behavior across leading transaction types."
)

# ----------------------------------------------------------
# M4. Scatter Plot - Count vs Amount, hue by Quarter, style by Year
# ----------------------------------------------------------
plt.figure(figsize=(12, 6))
sns.scatterplot(
    data=df,
    x="transaction_count",
    y="transaction_amount",
    hue="quarter",
    style="year",
    alpha=0.7
)
show_and_save("M4. Count vs Amount by Quarter and Year", "eda_outputs/m4_scatter_count_amount_quarter_year.png")

m4_results = (
    "Scatter plot created with transaction count and amount, segmented by quarter and year."
)
m4_insights = (
    "This chart shows whether the relationship between volume and value changes by quarter or year. "
    "It can reveal seasonal clustering or operational shifts in transaction behavior."
)
add_insight(
    section="Multivariate",
    chart_title="M4. Count vs Amount by Quarter and Year",
    why_chosen="A segmented scatter plot is chosen to analyze relationship patterns while simultaneously incorporating time dimensions.",
    results=m4_results,
    insights=m4_insights,
    result_summary="Segmented scatter analysis reveals whether time periods alter the value-volume relationship."
)

# ----------------------------------------------------------
# M5. Boxplot - Transaction Amount by Transaction Type across Quarters
# ----------------------------------------------------------
top_types_box = top_types.tolist()
df_box = df[df["transaction_type"].isin(top_types_box)].copy()

plt.figure(figsize=(14, 6))
sns.boxplot(
    data=df_box,
    x="transaction_type",
    y="transaction_amount",
    hue="quarter"
)
plt.xticks(rotation=30)
show_and_save("M5. Transaction Amount by Type across Quarters", "eda_outputs/m5_box_type_quarter.png")

m5_results = "Boxplot prepared for top transaction types across quarter segments."
m5_insights = (
    "This compares spread and variability within each transaction type across quarters. "
    "It helps identify high-variance categories, seasonal inconsistency, and stable performers."
)
add_insight(
    section="Multivariate",
    chart_title="M5. Transaction Amount by Type across Quarters",
    why_chosen="A grouped boxplot is chosen to compare spread, median, and outliers across categories and quarters together.",
    results=m5_results,
    insights=m5_insights,
    result_summary="This view highlights category stability, seasonal fluctuation, and outlier-heavy payment segments."
)

# ==========================================================
# 9. HYPOTHESIS TESTING (3 TESTS)
# ==========================================================

HYPOTHESIS_RESULTS = []

def add_hypothesis(test_name, why_chosen, null_hypothesis, alternate_hypothesis, test_stat, p_value, result, insights):
    HYPOTHESIS_RESULTS.append({
        "test_name": test_name,
        "why_chosen": why_chosen,
        "null_hypothesis": null_hypothesis,
        "alternate_hypothesis": alternate_hypothesis,
        "test_stat": test_stat,
        "p_value": p_value,
        "result": result,
        "insights": insights
    })

# ----------------------------------------------------------
# H1. ANOVA - Does average transaction amount differ by quarter?
# ----------------------------------------------------------
quarter_groups = [
    grp["transaction_amount"].values
    for _, grp in df.groupby("quarter")
    if len(grp) > 1
]

if len(quarter_groups) >= 2:
    f_stat, p_val = f_oneway(*quarter_groups)
    h1_result = "Reject H0" if p_val < 0.05 else "Fail to Reject H0"
    h1_insight = (
        "If H0 is rejected, at least one quarter has a statistically different average transaction amount. "
        "This supports seasonal spending variation and can guide quarter-specific campaigns."
    )
else:
    f_stat, p_val, h1_result, h1_insight = np.nan, np.nan, "Insufficient data", "Not enough quarter groups."

add_hypothesis(
    test_name="H1. ANOVA: Average Transaction Amount across Quarters",
    why_chosen="ANOVA is chosen because quarter has more than two groups and we want to test whether average transaction amount differs significantly across them.",
    null_hypothesis="The mean transaction amount is the same across all quarters.",
    alternate_hypothesis="At least one quarter has a different mean transaction amount.",
    test_stat=f_stat,
    p_value=p_val,
    result=h1_result,
    insights=h1_insight
)

# ----------------------------------------------------------
# H2. T-Test - Do top states and non-top states differ in avg transaction amount?
# ----------------------------------------------------------
state_totals = df.groupby("state")["transaction_amount"].sum().sort_values(ascending=False)
top_25_percent_states = state_totals.head(max(1, int(len(state_totals) * 0.25))).index

df["state_group"] = np.where(df["state"].isin(top_25_percent_states), "Top", "Others")

top_vals = df[df["state_group"] == "Top"]["transaction_amount"]
other_vals = df[df["state_group"] == "Others"]["transaction_amount"]

if len(top_vals) > 1 and len(other_vals) > 1:
    t_stat, p_val2 = ttest_ind(top_vals, other_vals, equal_var=False)
    h2_result = "Reject H0" if p_val2 < 0.05 else "Fail to Reject H0"
    h2_insight = (
        "If rejected, leading states differ significantly from the rest in average transaction amount, "
        "confirming market concentration and the need for segmented regional strategy."
    )
else:
    t_stat, p_val2, h2_result, h2_insight = np.nan, np.nan, "Insufficient data", "Not enough data in one group."

add_hypothesis(
    test_name="H2. T-Test: Top States vs Other States",
    why_chosen="An independent t-test is chosen to compare average transaction amount between two groups: top-performing states and remaining states.",
    null_hypothesis="There is no significant difference in mean transaction amount between top states and other states.",
    alternate_hypothesis="There is a significant difference in mean transaction amount between top states and other states.",
    test_stat=t_stat,
    p_value=p_val2,
    result=h2_result,
    insights=h2_insight
)

# ----------------------------------------------------------
# H3. Chi-Square - Is transaction type associated with quarter?
# ----------------------------------------------------------
cont_table = pd.crosstab(df["transaction_type"], df["quarter"])

if cont_table.shape[0] > 1 and cont_table.shape[1] > 1:
    chi2_stat, p_val3, dof, expected = chi2_contingency(cont_table)
    h3_result = "Reject H0" if p_val3 < 0.05 else "Fail to Reject H0"
    h3_insight = (
        "If rejected, transaction category distribution changes significantly by quarter. "
        "This supports seasonal or campaign-linked category shifts and targeted marketing by time period."
    )
else:
    chi2_stat, p_val3, dof, h3_result, h3_insight = np.nan, np.nan, np.nan, "Insufficient data", "Not enough category diversity."

add_hypothesis(
    test_name="H3. Chi-Square: Transaction Type vs Quarter",
    why_chosen="A chi-square test is chosen because both variables are categorical, and we want to test whether payment category distribution depends on quarter.",
    null_hypothesis="Transaction type and quarter are independent.",
    alternate_hypothesis="Transaction type and quarter are associated.",
    test_stat=chi2_stat,
    p_value=p_val3,
    result=h3_result,
    insights=h3_insight
)

# ==========================================================
# 10. PRINT ALL EDA INSIGHTS
# ==========================================================
print("\n" + "="*80)
print("EDA CHART INTERPRETATIONS")
print("="*80)

for i, item in enumerate(INSIGHTS, start=1):
    print(f"\n{i}. {item['chart_title']}")
    print("Section:", item["section"])
    print("Why this chart was chosen:", item["why_chosen"])
    print("Results:", item["results"])
    print("Insights:", item["insights"])
    print("Result Summary:", item["result_summary"])

print("\n" + "="*80)
print("HYPOTHESIS TEST RESULTS")
print("="*80)

for i, h in enumerate(HYPOTHESIS_RESULTS, start=1):
    print(f"\n{i}. {h['test_name']}")
    print("Why chosen:", h["why_chosen"])
    print("Null Hypothesis (H0):", h["null_hypothesis"])
    print("Alternate Hypothesis (H1):", h["alternate_hypothesis"])
    print("Test Statistic:", h["test_stat"])
    print("P-Value:", h["p_value"])
    print("Result:", h["result"])
    print("Insights:", h["insights"])

# ==========================================================
# 11. SAVE INSIGHTS TO CSV / TEXT FOR REPORT USE
# ==========================================================
insights_df = pd.DataFrame(INSIGHTS)
hyp_df = pd.DataFrame(HYPOTHESIS_RESULTS)

insights_df.to_csv("eda_outputs/eda_chart_insights.csv", index=False)
hyp_df.to_csv("eda_outputs/hypothesis_results.csv", index=False)

with open("eda_outputs/eda_summary.txt", "w", encoding="utf-8") as f:
    f.write("PHONEPE TRANSACTION INSIGHTS - EDA SUMMARY\n")
    f.write("="*60 + "\n\n")

    f.write("OVERALL SUMMARY\n")
    for k, v in summary.items():
        f.write(f"{k}: {v}\n")

    f.write("\n\nEDA CHART DETAILS\n")
    for item in INSIGHTS:
        f.write("\n" + "-"*60 + "\n")
        f.write(f"Chart Title: {item['chart_title']}\n")
        f.write(f"Section: {item['section']}\n")
        f.write(f"Why Chosen: {item['why_chosen']}\n")
        f.write(f"Results: {item['results']}\n")
        f.write(f"Insights: {item['insights']}\n")
        f.write(f"Result Summary: {item['result_summary']}\n")

    f.write("\n\nHYPOTHESIS TESTS\n")
    for h in HYPOTHESIS_RESULTS:
        f.write("\n" + "-"*60 + "\n")
        f.write(f"Test Name: {h['test_name']}\n")
        f.write(f"Why Chosen: {h['why_chosen']}\n")
        f.write(f"H0: {h['null_hypothesis']}\n")
        f.write(f"H1: {h['alternate_hypothesis']}\n")
        f.write(f"Test Statistic: {h['test_stat']}\n")
        f.write(f"P-Value: {h['p_value']}\n")
        f.write(f"Result: {h['result']}\n")
        f.write(f"Insights: {h['insights']}\n")

print("\nEDA completed successfully.")
print("Outputs saved in: eda_outputs/")