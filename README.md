# 🧠 Smart Customer Behavior Analyzer

**Smart Customer Behavior Analyzer** is a web-based tool built with **Streamlit** that allows users to:

- 📂 Upload CSV or JSON API datasets
- 🧹 Handle missing values
- 📉 Detect outliers
- 📊 Visualize patterns, correlations, and summary stats
- 🎯 Analyze revenue-based behavior (if available)

> 🔗 **Live Demo**: [smart-customer-behavior-analyzer.streamlit.app](https://smart-customer-behavior-analyzer.streamlit.app)

---

## 🚀 Features

- ✅ Clean and modern dark-themed UI
- 📈 Auto-summary of numerical and categorical columns
- 🔥 Feature correlation heatmap
- 🧠 Skewness & kurtosis stats
- 📊 Column-wise interactive visualizations
- 🎯 Behavioral insights (if `Revenue`, `Month`, `VisitorType` columns exist)
- ⬇️ Export final cleaned data
- 🛠️ Optional MySQL export (local only)

---

## 🛠️ Tech Stack

- **Python**
- **Streamlit**
- **Plotly Express**
- **Pandas / NumPy**
- **SQLAlchemy + PyMySQL** (for optional MySQL export)

---

## 📂 Project Structure

```bash
.
├── online_shopping_eda_dashboard.py   # Main app file
├── create_csv_analyzer.sql            # Optional: SQL schema for MySQL
├── requirements.txt                   # Dependencies
└── README.md                          # You're here!
