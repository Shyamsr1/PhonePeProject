import sys
import traceback
import importlib
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px


# ============================================================
# STREAMLIT PAGE CONFIG
# Must be the first Streamlit command in the app.
# ============================================================
st.set_page_config(
    page_title="PhonePe Transaction Insights Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# PROJECT PATHS
# Expected project structure:
#
# PhonePeProject/
# ├── app.py
# ├── data/
# │   ├── phonepe.db
# │   ├── phonepe_cleaned.csv
# │   ├── phonepe_master_cleaned.csv
# │   └── phonepe_file_index.csv
# └── python/
#     ├── data_loader.py
#     ├── eda.py
#     └── reports.py
#
# The python folder is added to sys.path so modules can be
# imported directly inside app.py.
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PYTHON_DIR = BASE_DIR / "python"

if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))


# ============================================================
# APP HEADER
# ============================================================
st.title("📊 PhonePe Transaction Insights Dashboard")
st.markdown(
    """
    This dashboard is designed to use the project modules from the `python/` folder:
    `data_loader.py`, `eda.py`, and `reports.py`.

    The app acts as a presentation layer:
    - `data_loader.py` → data preparation / loading
    - `eda.py` → EDA charts, insights, hypothesis testing
    - `reports.py` → PDF report generation
    """
)


# ============================================================
# HELPER: SAFE MODULE IMPORT
# This imports a module and shows a clean error if import fails.
# ============================================================
@st.cache_resource
def safe_import_module(module_name: str):
    """
    Import a project module safely.

    Parameters
    ----------
    module_name : str
        Name of the module to import.

    Returns
    -------
    module
        Imported Python module object, or None if not available.
    """
    try:
        return importlib.import_module(module_name)
    except Exception:
        st.warning(f"Could not import module: `{module_name}`")
        st.code(traceback.format_exc())
        return None


# Import project modules
data_loader = safe_import_module("data_loader")
eda = safe_import_module("eda")
reports = safe_import_module("reports")


# ============================================================
# HELPER: CALL FIRST AVAILABLE FUNCTION
# Many project files have slightly different function names.
# This helper tries a list of possible names and calls the first
# one that exists inside the imported module.
# ============================================================
def call_first_available(module, function_names, *args, **kwargs):
    """
    Try calling the first matching function in the provided module.

    Parameters
    ----------
    module : module
        Imported module object.
    function_names : list[str]
        Candidate function names.
    *args, **kwargs :
        Arguments passed to the matched function.

    Returns
    -------
    Any
        Function output if found and called successfully.

    Raises
    ------
    AttributeError
        If none of the candidate functions exist.
    """
    if module is None:
        raise AttributeError("Module is not available.")

    for fn_name in function_names:
        if hasattr(module, fn_name):
            fn = getattr(module, fn_name)
            return fn(*args, **kwargs)

    raise AttributeError(
        f"No matching function found in module `{module.__name__}`. "
        f"Tried: {function_names}"
    )


# ============================================================
# HELPER: LOAD MAIN DATAFRAME
# Priority order:
# 1. Use a function from data_loader.py if it exists
# 2. Use SQLite database if available
# 3. Use cleaned CSV fallback
#
# This keeps app.py lightweight and lets it depend on the output
# produced by data_loader.py.
# ============================================================
@st.cache_data
def load_main_dataframe():
    """
    Load the main PhonePe processed dataset.

    Returns
    -------
    pd.DataFrame
        Main processed dataset for dashboard use.
    """
    # --------------------------------------------------------
    # STEP 1: Try using data_loader.py functions
    # --------------------------------------------------------
    loader_function_candidates = [
        "load_data",
        "load_master_data",
        "load_cleaned_data",
        "get_data",
        "get_master_data",
        "read_data",
        "fetch_data",
        "get_processed_data"
    ]

    if data_loader is not None:
        for fn_name in loader_function_candidates:
            if hasattr(data_loader, fn_name):
                df = getattr(data_loader, fn_name)()
                if isinstance(df, pd.DataFrame):
                    return df

    # --------------------------------------------------------
    # STEP 2: Try loading from SQLite database
    # --------------------------------------------------------
    db_path = DATA_DIR / "phonepe.db"
    if db_path.exists():
        conn = sqlite3.connect(db_path)
        try:
            # Get available table names
            tables = pd.read_sql(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;",
                conn
            )["name"].tolist()

            # Try common table names
            candidate_tables = [
                "aggregated_transaction",
                "phonepe_data",
                "phonepe_cleaned",
                "master_data",
                "transactions",
                "phonepe_master"
            ]

            for table in candidate_tables:
                if table in tables:
                    df = pd.read_sql(f"SELECT * FROM {table}", conn)
                    if not df.empty:
                        conn.close()
                        return df

            # Fallback: first non-empty table
            for table in tables:
                df = pd.read_sql(f"SELECT * FROM {table}", conn)
                if not df.empty:
                    conn.close()
                    return df

        finally:
            conn.close()

    # --------------------------------------------------------
    # STEP 3: Try loading from cleaned CSV files
    # --------------------------------------------------------
    csv_candidates = [
        DATA_DIR / "phonepe_master_cleaned.csv",
        DATA_DIR / "phonepe_cleaned.csv",
        DATA_DIR / "phonepe_file_index.csv"
    ]

    for csv_path in csv_candidates:
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            if not df.empty:
                return df

    # If all options fail, raise an error
    raise FileNotFoundError(
        "No processed PhonePe dataset could be loaded. "
        "Ensure that data_loader.py has created either a valid DataFrame, "
        "SQLite DB, or cleaned CSV files."
    )


# ============================================================
# LOAD MAIN DATA
# ============================================================
try:
    df = load_main_dataframe()
except Exception:
    st.error("Data loading failed.")
    st.code(traceback.format_exc())
    st.stop()


# ============================================================
# STANDARDIZE COLUMN NAMES
# This makes the app more tolerant if cleaned data uses slightly
# different column name styles.
# ============================================================
df.columns = [str(col).strip().lower() for col in df.columns]

column_aliases = {
    "transactionamount": "transaction_amount",
    "transaction count": "transaction_count",
    "transactioncount": "transaction_count",
    "transaction type": "transaction_type",
    "transactiontype": "transaction_type",
    "states": "state",
    "years": "year",
    "quarters": "quarter"
}

df.rename(columns=column_aliases, inplace=True)


# ============================================================
# REQUIRED COLUMNS CHECK
# These are the main columns expected for the dashboard.
# ============================================================
required_columns = [
    "year",
    "quarter",
    "state",
    "transaction_type",
    "transaction_amount",
    "transaction_count"
]

missing_columns = [col for col in required_columns if col not in df.columns]

if missing_columns:
    st.error("The loaded dataset does not contain the required columns.")
    st.write("Missing columns:", missing_columns)
    st.write("Available columns:", list(df.columns))
    st.stop()


# ============================================================
# BASIC TYPE CLEANING
# Heavy cleaning should remain in data_loader.py.
# This is only minimal app-level safety cleaning.
# ============================================================
df["year"] = pd.to_numeric(df["year"], errors="coerce")
df["quarter"] = pd.to_numeric(df["quarter"], errors="coerce")
df["transaction_amount"] = pd.to_numeric(df["transaction_amount"], errors="coerce")
df["transaction_count"] = pd.to_numeric(df["transaction_count"], errors="coerce")

df = df.dropna(subset=["year", "quarter", "state", "transaction_type"])
df["year"] = df["year"].astype(int)
df["quarter"] = df["quarter"].astype(int)


# ============================================================
# SIDEBAR FILTERS
# These allow the user to interact with the dashboard.
# ============================================================
st.sidebar.header("🔎 Filter Data")

year_options = sorted(df["year"].dropna().unique().tolist())
quarter_options = sorted(df["quarter"].dropna().unique().tolist())
state_options = sorted(df["state"].dropna().unique().tolist())

selected_year = st.sidebar.selectbox("Select Year", year_options)
selected_quarter = st.sidebar.selectbox("Select Quarter", quarter_options)
selected_states = st.sidebar.multiselect("Select State(s)", state_options, default=[])

filtered_df = df[(df["year"] == selected_year) & (df["quarter"] == selected_quarter)].copy()

if selected_states:
    filtered_df = filtered_df[filtered_df["state"].isin(selected_states)].copy()

if filtered_df.empty:
    st.warning("No records available for the selected filters.")
    st.stop()


# ============================================================
# TOP KPI SECTION
# These are required dashboard metrics from the processed data.
# ============================================================
total_amount = filtered_df["transaction_amount"].sum()
total_count = filtered_df["transaction_count"].sum()
total_states = filtered_df["state"].nunique()
total_types = filtered_df["transaction_type"].nunique()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Transaction Amount", f"₹ {total_amount:,.2f}")
k2.metric("Total Transaction Count", f"{total_count:,.0f}")
k3.metric("States Covered", f"{total_states}")
k4.metric("Transaction Types", f"{total_types}")


# ============================================================
# TABS
# The dashboard is divided into required project sections.
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📁 Data Overview",
        "📈 EDA Dashboard",
        "🧪 Hypothesis Testing",
        "📄 Report Generation"
    ]
)


# ============================================================
# TAB 1: DATA OVERVIEW
# Shows cleaned data summary and preview.
# ============================================================
with tab1:
    st.subheader("Processed Data Overview")

    c1, c2, c3 = st.columns(3)
    c1.metric("Filtered Rows", f"{len(filtered_df):,}")
    c2.metric("Filtered States", f"{filtered_df['state'].nunique():,}")
    c3.metric("Filtered Transaction Types", f"{filtered_df['transaction_type'].nunique():,}")

    st.markdown("### Filtered Dataset Preview")
    st.dataframe(filtered_df.head(50), width='stretch')

    st.markdown("### Column Summary")
    summary_df = pd.DataFrame({
        "column_name": filtered_df.columns,
        "dtype": [str(filtered_df[col].dtype) for col in filtered_df.columns],
        "missing_values": [filtered_df[col].isna().sum() for col in filtered_df.columns],
        "unique_values": [filtered_df[col].nunique(dropna=True) for col in filtered_df.columns]
    })
    st.dataframe(summary_df, width='stretch')

    st.markdown("### Download Filtered Data")
    filtered_csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Filtered CSV",
        data=filtered_csv,
        file_name=f"phonepe_filtered_{selected_year}_Q{selected_quarter}.csv",
        mime="text/csv"
    )


# ============================================================
# TAB 2: EDA DASHBOARD
# This section should use eda.py outputs as much as possible.
#
# Priority order:
# 1. Use modular chart/insight functions from eda.py
# 2. Fall back to in-app charts for display only
# ============================================================
with tab2:
    st.subheader("Exploratory Data Analysis")

    # --------------------------------------------------------
    # SECTION A: Try to show EDA charts generated by eda.py
    # --------------------------------------------------------
    eda_chart_shown = False

    if eda is not None:
        chart_function_candidates = [
            "generate_eda_charts",
            "create_eda_charts",
            "get_eda_charts",
            "build_charts",
            "plot_all_charts"
        ]

        for fn_name in chart_function_candidates:
            if hasattr(eda, fn_name):
                try:
                    chart_output = getattr(eda, fn_name)(filtered_df)

                    st.markdown("### Charts from `eda.py`")

                    if isinstance(chart_output, dict):
                        for title, fig in chart_output.items():
                            st.markdown(f"#### {title}")
                            try:
                                st.plotly_chart(fig, width='stretch')
                            except Exception:
                                try:
                                    st.pyplot(fig)
                                except Exception:
                                    st.write(fig)
                        eda_chart_shown = True
                        break

                    elif isinstance(chart_output, list):
                        for idx, fig in enumerate(chart_output, start=1):
                            st.markdown(f"#### Chart {idx}")
                            try:
                                st.plotly_chart(fig, width='stretch')
                            except Exception:
                                try:
                                    st.pyplot(fig)
                                except Exception:
                                    st.write(fig)
                        eda_chart_shown = True
                        break

                except Exception:
                    st.warning(f"EDA chart function `{fn_name}` failed.")
                    st.code(traceback.format_exc())

    # --------------------------------------------------------
    # SECTION B: Fallback charts for dashboard display
    # These are display-only charts if eda.py chart functions
    # are not available.
    # --------------------------------------------------------
    if not eda_chart_shown:
        st.info("Using dashboard fallback charts because no compatible chart function was found in `eda.py`.")

        # Top 10 states by amount
        state_amount = (
            filtered_df.groupby("state", as_index=False)["transaction_amount"]
            .sum()
            .sort_values(by="transaction_amount", ascending=False)
            .head(10)
        )

        fig1 = px.bar(
            state_amount,
            x="transaction_amount",
            y="state",
            orientation="h",
            title="Top 10 States by Transaction Amount",
            text_auto=".2s"
        )
        fig1.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig1, width='stretch')

        # Transaction type share
        type_amount = (
            filtered_df.groupby("transaction_type", as_index=False)["transaction_amount"]
            .sum()
            .sort_values(by="transaction_amount", ascending=False)
        )

        fig2 = px.pie(
            type_amount,
            names="transaction_type",
            values="transaction_amount",
            title="Transaction Amount Share by Transaction Type"
        )
        st.plotly_chart(fig2, width='stretch')

        # Yearly trend
        yearly_trend = (
            df.groupby("year", as_index=False)["transaction_amount"]
            .sum()
            .sort_values(by="year")
        )

        fig3 = px.line(
            yearly_trend,
            x="year",
            y="transaction_amount",
            markers=True,
            title="Yearly Transaction Amount Trend"
        )
        st.plotly_chart(fig3, width='stretch')

        # Quarter trend in selected year
        year_df = df[df["year"] == selected_year].copy()
        quarter_trend = (
            year_df.groupby("quarter", as_index=False)["transaction_amount"]
            .sum()
            .sort_values(by="quarter")
        )

        fig4 = px.bar(
            quarter_trend,
            x="quarter",
            y="transaction_amount",
            title=f"Quarter-wise Transaction Amount in {selected_year}",
            text_auto=".2s"
        )
        st.plotly_chart(fig4, width='stretch')

        # Top 10 states by count
        state_count = (
            filtered_df.groupby("state", as_index=False)["transaction_count"]
            .sum()
            .sort_values(by="transaction_count", ascending=False)
            .head(10)
        )

        fig5 = px.bar(
            state_count,
            x="transaction_count",
            y="state",
            orientation="h",
            title="Top 10 States by Transaction Count",
            text_auto=True
        )
        fig5.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig5, width='stretch')

    # --------------------------------------------------------
    # SECTION C: Insights from eda.py
    # --------------------------------------------------------
    st.markdown("### Business Insights")

    insights_shown = False

    if eda is not None:
        insight_function_candidates = [
            "generate_insights",
            "get_insights",
            "business_insights",
            "summary_insights"
        ]

        for fn_name in insight_function_candidates:
            if hasattr(eda, fn_name):
                try:
                    insights = getattr(eda, fn_name)(filtered_df)

                    if isinstance(insights, list):
                        for item in insights:
                            st.write(f"- {item}")
                    elif isinstance(insights, dict):
                        for k, v in insights.items():
                            st.write(f"**{k}:** {v}")
                    elif isinstance(insights, pd.DataFrame):
                        st.dataframe(insights, width='stretch')
                    else:
                        st.write(insights)

                    insights_shown = True
                    break

                except Exception:
                    st.warning(f"Insight function `{fn_name}` failed.")
                    st.code(traceback.format_exc())

    if not insights_shown:
        top_state = state_amount.iloc[0]["state"] if len(state_amount) else "N/A"
        top_state_value = state_amount.iloc[0]["transaction_amount"] if len(state_amount) else 0
        top_type = type_amount.iloc[0]["transaction_type"] if len(type_amount) else "N/A"
        top_type_value = type_amount.iloc[0]["transaction_amount"] if len(type_amount) else 0

        st.write(
            f"- For **Year {selected_year} Quarter {selected_quarter}**, the total transaction amount is "
            f"**₹ {total_amount:,.2f}**."
        )
        st.write(
            f"- The total number of transactions is **{total_count:,.0f}**."
        )
        st.write(
            f"- The top contributing state by transaction amount is **{top_state}** "
            f"with **₹ {top_state_value:,.2f}**."
        )
        st.write(
            f"- The highest contributing transaction type is **{top_type}** "
            f"with **₹ {top_type_value:,.2f}**."
        )
        st.write(
            f"- The selected data covers **{total_states}** states and **{total_types}** transaction types."
        )


# ============================================================
# TAB 3: HYPOTHESIS TESTING
# This section should display hypothesis results from eda.py.
# If not available, it shows a structured placeholder summary.
# ============================================================
with tab3:
    st.subheader("Hypothesis Testing Results")

    hypothesis_shown = False

    if eda is not None:
        hypothesis_function_candidates = [
            "run_hypothesis_tests",
            "hypothesis_testing",
            "get_hypothesis_results",
            "perform_hypothesis_tests"
        ]

        for fn_name in hypothesis_function_candidates:
            if hasattr(eda, fn_name):
                try:
                    result = getattr(eda, fn_name)(filtered_df)

                    if isinstance(result, pd.DataFrame):
                        st.dataframe(result, width='stretch')
                    elif isinstance(result, list):
                        for item in result:
                            st.write(f"- {item}")
                    elif isinstance(result, dict):
                        for k, v in result.items():
                            st.write(f"**{k}:** {v}")
                    else:
                        st.write(result)

                    hypothesis_shown = True
                    break

                except Exception:
                    st.warning(f"Hypothesis function `{fn_name}` failed.")
                    st.code(traceback.format_exc())

    if not hypothesis_shown:
        st.info(
            "No compatible hypothesis test function was found in `eda.py`. "
            "Below is the required project section format that should be populated from `eda.py`."
        )

        placeholder_df = pd.DataFrame({
            "Hypothesis Test": [
                "Test 1",
                "Test 2",
                "Test 3"
            ],
            "Why Chosen": [
                "Compare important transaction metric across groups",
                "Check difference in transaction behavior across categories",
                "Test relationship between key business variables"
            ],
            "Null Hypothesis (H0)": [
                "No significant difference exists",
                "No significant difference exists",
                "No significant relationship exists"
            ],
            "Alternate Hypothesis (H1)": [
                "A significant difference exists",
                "A significant difference exists",
                "A significant relationship exists"
            ],
            "Result": [
                "Populate from eda.py",
                "Populate from eda.py",
                "Populate from eda.py"
            ],
            "Business Insight": [
                "Populate from eda.py",
                "Populate from eda.py",
                "Populate from eda.py"
            ]
        })

        st.dataframe(placeholder_df, width='stretch')


# ============================================================
# TAB 4: REPORT GENERATION
# This section calls reports.py if available. If not, it lets the
# user download the filtered data and reminds that reports.py
# should generate the final PDF.
# ============================================================
with tab4:
    st.subheader("Project Report Generation")

    st.markdown(
        """
        The final report is expected to include:
        - Problem statement
        - Data overview
        - Cleaning summary
        - EDA results
        - Hypothesis testing results
        - Business insights
        - Recommendations
        - Final conclusions
        """
    )

    report_filename = st.text_input(
        "Output report file name",
        value=f"phonepe_report_{selected_year}_Q{selected_quarter}.pdf"
    )

    if st.button("Generate PDF Report"):
        report_generated = False

        if reports is not None:
            report_function_candidates = [
                "generate_report",
                "create_report",
                "build_report",
                "export_report_pdf"
            ]

            for fn_name in report_function_candidates:
                if hasattr(reports, fn_name):
                    try:
                        output = getattr(reports, fn_name)(
                            filtered_df,
                            output_path=str(BASE_DIR / report_filename)
                        )

                        expected_path = BASE_DIR / report_filename

                        if isinstance(output, str) and Path(output).exists():
                            with open(output, "rb") as f:
                                st.success("Report generated successfully.")
                                st.download_button(
                                    label="Download PDF Report",
                                    data=f.read(),
                                    file_name=Path(output).name,
                                    mime="application/pdf"
                                )
                                report_generated = True
                                break

                        elif expected_path.exists():
                            with open(expected_path, "rb") as f:
                                st.success("Report generated successfully.")
                                st.download_button(
                                    label="Download PDF Report",
                                    data=f.read(),
                                    file_name=report_filename,
                                    mime="application/pdf"
                                )
                                report_generated = True
                                break

                        elif isinstance(output, bytes):
                            st.success("Report generated successfully.")
                            st.download_button(
                                label="Download PDF Report",
                                data=output,
                                file_name=report_filename,
                                mime="application/pdf"
                            )
                            report_generated = True
                            break

                    except Exception:
                        st.warning(f"Report function `{fn_name}` failed.")
                        st.code(traceback.format_exc())

        if not report_generated:
            st.warning(
                "No compatible report generation function was found in `reports.py` "
                "or report generation failed."
            )

    st.markdown("### Download Filtered Data for Reporting")
    report_csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Filtered CSV",
        data=report_csv,
        file_name=f"phonepe_report_input_{selected_year}_Q{selected_quarter}.csv",
        mime="text/csv"
    )


# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.caption(f"Base directory: {BASE_DIR}")
st.caption(f"Python module directory: {PYTHON_DIR}")
st.caption(f"Data directory: {DATA_DIR}")
st.caption(f"Loaded rows in master dataset: {len(df):,}")
st.caption(f"Filtered rows shown on dashboard: {len(filtered_df):,}")