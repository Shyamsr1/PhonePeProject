# PhonePe Transaction Insights Dashboard

A modular data analytics project built to process PhonePe transaction data, perform exploratory data analysis, run hypothesis testing, and generate a downloadable PDF report through a Streamlit dashboard.

---

## Project Overview

This project is designed to:

- collect and combine PhonePe transaction data from nested JSON files
- clean and standardize the data
- store processed data in SQLite
- perform EDA with charts and insights
- run hypothesis testing for business understanding
- generate a professional PDF report
- present everything through a Streamlit dashboard

The latest version uses:

- **SQLite only**
- **no MySQL dependency**
- a **modular structure**
- `app.py` as the dashboard and presentation layer
- `python/data_loader.py` for data preparation and loading
- `python/eda.py` for analysis logic
- `python/reports.py` for report generation

---

## Latest Modifications Applied

### Database Layer
- Removed MySQL usage completely
- Replaced database dependency with **SQLite**
- Main local database file:
  - `data/phonepe.db`

### App Layer
- `app.py` updated to work as a **dashboard controller**
- `app.py` now:
  - imports project modules from `python/`
  - loads processed data from module output / SQLite / cleaned CSV fallback
  - displays KPIs, filtered data, EDA charts, insights, hypothesis testing, and report generation
- `app.py` no longer contains full heavy processing logic

### Data Loading Layer
- `python/data_loader.py` is expected to:
  - recursively read JSON files from nested folders
  - combine all valid files
  - clean and transform data
  - export cleaned outputs
  - optionally store processed data in SQLite

### EDA Layer
- `python/eda.py` is expected to:
  - create analysis charts
  - generate insights
  - provide hypothesis testing results
  - support project reporting

### Reporting Layer
- `python/reports.py` is expected to:
  - create final PDF report
  - include project summary, EDA, hypothesis testing, business insights, recommendations, and conclusion

---

## Project Structure

```text
PhonePeProject/
│
├── app.py
├── readme.md
├── requirements.txt
│
├── data/
│   ├── aggregated/
│   ├── map/
│   ├── top/
│   ├── phonepe.db
│   ├── phonepe_cleaned.csv
│   ├── phonepe_master_cleaned.csv
│   └── phonepe_file_index.csv
│
├── python/
│   ├── data_loader.py
│   ├── eda.py
│   └── reports.py
│
└── phonepe_env/   # optional local virtual environment

``` 
# ------------------------------------------

# Main Files and Their Roles
## app.py
## This is the Streamlit dashboard entry point.
## It is responsible for:
- loading processed data
- applying sidebar filters
- displaying KPIs
- showing data preview
- showing EDA charts
- showing insights
- showing hypothesis test results
- generating and downloading the final report
- It should remain lightweight and should not contain the full project logic.

# python/data_loader.py
## This file handles the data preparation pipeline.
## Expected responsibilities:
- traverse nested folders inside data/
- identify all required JSON files
- combine data from all valid files
- clean and standardize records
- create master cleaned dataset
- export cleaned CSV files
- optionally update SQLite database

# Typical outputs:
## data/phonepe_cleaned.csv
## data/phonepe_master_cleaned.csv
## data/phonepe_file_index.csv
## data/phonepe.db

# ------------------------------------------------------------------

# python/eda.py

## This file handles exploratory data analysis.
## Expected responsibilities:
- generate charts
- compute metrics
- write analysis summaries
- provide business insights
- run hypothesis testing
## Expected project analysis includes:
- 5 univariate charts
- 5 bivariate charts
- 5 multivariate charts
- 3 hypothesis tests

## Each chart/test should ideally explain:
- why it was chosen
- what the result shows
- what insight it provides

# --------------------------------------------------------------------------
# python/reports.py
## This file handles report generation.
## Expected responsibilities:
- create PDF report
- include project problem statement
- include data overview
- include cleaning summary
- include EDA output
- include hypothesis testing results
- include business insights
- include client recommendations
- include major conclusions

# Dashboard Requirements
## The Streamlit dashboard should show the following sections.
##  1. Data Overview
- processed dataset preview
- column summary
- filtered records preview
- downloadable filtered CSV
##  2. Filters
- year
- quarter
- state
##  3. KPIs
- Total Transaction Amount
- Total Transaction Count
- Number of States
- Number of Transaction Types
## 4. EDA Dashboard
- charts produced from eda.py
- fallback display charts if module output is unavailable
- key insights
## 5. Hypothesis Testing
- 3 hypothesis test outputs
- why chosen
- null hypothesis
- alternate hypothesis
- result
- business interpretation

## 6. Report Generation
- PDF generation from reports.py
- download option inside dashboard
- Data Source Expectations

# The project expects nested PhonePe data folders inside data/, such as:
- aggregated/
- map/
- top/

## Each may contain further nested folders and JSON files.
## The data loader should recursively scan all subfolders and process all valid JSON files.

# Output Files
## Typical generated outputs are:
- Processed Data
- data/phonepe_cleaned.csv
- data/phonepe_master_cleaned.csv
- data/phonepe_file_index.csv
- data/phonepe.db
- Reports
- generated PDF report file from reports.py
- Optional Analysis Outputs
## Depending on implementation in eda.py and reports.py, you may also generate:
- chart images
- analysis summaries
- hypothesis result tables
- Setup Instructions
## 1. Open the project folder
- Open terminal in the main project directory.
## 2. Create virtual environment (optional)
- python -m venv phonepe_env
## 3. Activate virtual environment
- Windows PowerShell
- .\phonepe_env\Scripts\Activate
- Windows CMD
- phonepe_env\Scripts\activate
## 4. Install dependencies
- pip install -r requirements.txt
- How to Run the Project
- Step 1: Prepare the processed data
- Run data_loader.py only when needed.
- Run this if:
- you added new raw JSON files
- your cleaned CSV files do not exist
- your SQLite database does not exist
- you changed data cleaning logic
-- 
Example:

python python/data_loader.py
Step 2: Run EDA logic if required

Run eda.py if:

you changed analysis logic
you want to regenerate insights/charts/hypothesis output

Example:

python python/eda.py
Step 3: Run the dashboard
streamlit run app.py

# requirements.txt 
```
streamlit
pandas
plotly
sqlite3
numpy
scipy
matplotlib
reportlab
openpyxl

```
## Note:
- sqlite3 is part of Python standard library and usually does not need separate installation
remove MySQL-related dependencies if no longer used
Example requirements.txt

# ---------------------------------------------------------------------------------------
# Business Value of the Project
## This dashboard helps users:
- understand transaction behavior across states, years, and quarters
identify top-performing states and transaction types
uncover transaction trends
validate business assumptions using hypothesis testing
generate a presentable report for stakeholders
Interview Explanation

## A clear way to explain the architecture:
- data_loader.py handles raw data ingestion, cleaning, and storage
- eda.py handles analysis, visualizations, insights, and hypothesis tests
- reports.py handles final PDF report generation
- app.py is the presentation layer that displays all outputs in a dashboard

# This separation makes the project:
- modular
- maintainable
- scalable
- easier to debug
- suitable for real-world analytics workflows

# -----------------------------------------------------------------------------------

# License : 
## MIT License
## Copyright (c) 2026 Shyam R

