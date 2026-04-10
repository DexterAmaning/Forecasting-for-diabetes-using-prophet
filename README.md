# Forecasting-for-diabetes-using-prophet
Medicaid Diabetes Drugs Spending Forecast (2019–2025)

🔍 Overview

This project analyzes Medicaid drug spending trends with a focus on diabetes medications, and builds forecasting models to understand future cost trajectories.

The goal is to combine:

Health policy insight (Medicaid spending)
Data science (EDA + ML + time series)
Real-world impact (chronic disease cost burden)

 Dataset
Source: Medicaid Drug Spending Data
Timeframe: 2019 – 2023
Size: ~16,938 rows × 36 columns
Key Variables:
Brnd_Name – Drug brand name
Gnrc_Name – Generic name
Tot_Spndng_YYYY – Total spending per year
Tot_Clms_YYYY – Number of claims
Avg_Spnd_Per_Clm_YYYY – Average spending per claim
Outlier_Flag_YYYY – High-cost indicator
CAGR_Avg_Spnd_Per_Dsg_Unt_19_23 – Growth rate

 Objectives
Analyze spending trends for diabetes drugs
Identify high-growth and high-cost medications
Compute Year-over-Year (YoY) growth
Forecast future spending using:
SARIMAX
Linear Regression
Prophet
🛠️ Tech Stack
Libraries:
pandas, numpy – Data processing
matplotlib, seaborn – Visualization
scikit-learn – Regression models
statsmodels – Time series (SARIMAX)
prophet – Forecasting
📊 Data Processing Pipeline
1. Data Cleaning
Removed missing values
Filtered relevant columns
Focused on diabetes-related drugs
2. Feature Engineering
Converted wide → long format
Extracted year from column names
Computed YoY % change
df_long['YoY_Change_%'] = df_long.groupby('Brnd_Name')['Total_Spending'].pct_change() * 100


💊 Diabetes Drugs Analyzed

Includes major classes:

GLP-1 agonists (Ozempic, Trulicity, Mounjaro)
SGLT2 inhibitors (Jardiance, Farxiga)
Insulin (Humalog, Lantus, NovoLog)
Oral agents (Metformin, Januvia, Actos)
📈 Visualization
Multi-line plots of spending trends per drug
Growth comparison across years
Outlier detection patterns
🔮 Forecasting Models
1. SARIMAX

Used for:

Seasonality + trend modeling
Time-series forecasting
2. Linear Regression

Used for:

Baseline trend prediction
3. Prophet

Used for:

Flexible trend + seasonality modeling
Robust real-world forecasting
📌 Key Insights
Rapid growth in GLP-1 drugs (e.g., Ozempic, Mounjaro)
Insulin spending remains stable but high
Significant cost escalation in newer therapies
Medicaid burden is increasingly driven by chronic disease drugs
🚀 Future Work
Add 2022–2023 full dataset integration
Build drug-level forecasting dashboards (Streamlit)
Incorporate patient-level claims data
Link spending to health outcomes (HbA1c, complications)
💡 Real-World Impact

This project supports:

Healthcare cost optimization
Policy decision-making (Medicaid/Medicare)
Early intervention strategies in diabetes care
🧠 Author

Prince Kwarteng Amaning
MS Data Science – University of Michigan–Dearborn
Background: Dentistry + Public Health + AI

Focus:

AI-driven healthcare systems, diabetes screening, and cost optimization

⚙️ How to Run
pip install pandas numpy matplotlib seaborn scikit-learn statsmodels prophet
python main.py
📬 Contact

For collaboration or research:
dexterkwarteng@gmail.com
