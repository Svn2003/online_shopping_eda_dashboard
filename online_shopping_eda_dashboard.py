import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests
import urllib.parse
import pymysql
from sqlalchemy import create_engine


st.set_page_config(page_title="📊 Smart Customer Behavior Analyzer", layout="wide")

# -------------- HERO SECTION -------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');

.hero {
  animation: fadeInUp 1s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(40px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.hero {
    background: linear-gradient(to right, rgba(0,0,0,0.65), rgba(0,0,0,0.4)),
                url('https://images.unsplash.com/photo-1605792657660-596af9009e82?fit=crop&w=1470&q=80');
    background-size: cover;
    background-position: center;
    color: white;
    padding: 60px 60px;
    border-radius: 18px;
    margin-bottom: 2rem;
    box-shadow: 0 10px 30px rgba(0,0,0,0.4);
    font-family: 'Roboto', sans-serif;
}

.hero h1 {
    font-size: 46px;
    font-weight: 700;
    margin-bottom: 24px;
}

.hero p {
    font-size: 22px;
    margin-bottom: 24px;
    line-height: 1.6;
}

.hero ul {
    font-size: 19px;
    list-style: none;
    padding-left: 0;
}

.hero ul li {
    margin-bottom: 14px;
    display: flex;
    align-items: center;
}

.hero ul li::before {
    margin-right: 12px;
    font-size: 20px;
}

.cta-button {
  display: inline-block;
  background: linear-gradient(to right, #00c6ff, #0072ff);
  color: white;
  font-size: 18px;
  padding: 12px 24px;
  border-radius: 12px;
  text-decoration: none;
  margin-top: 20px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
  transition: 0.3s ease;
}
.cta-button:hover {
  transform: scale(1.05);
}
.centered-button {
    display: flex;
    justify-content: center;
    margin-top: 20px;
    margin-bottom: 20px;
}
.stButton > button {
    background-color: #007bff;
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 6px;
    font-size: 16px;
    cursor: pointer;
    transition: background-color 0.3s ease;
}
.stButton > button:hover {
    background-color: #0056b3;
}
.stDownloadButton > button {
    background-color: #d9534f;
    color: #ffffff;
    font-weight: bold;
    border: none;
    padding: 12px 28px;
    border-radius: 8px;
    font-size: 16px;
    box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
    cursor: pointer;
    transition: all 0.3s ease;
}
.stDownloadButton > button:hover {
    background-color: #c9302c;
    transform: translateY(-1px);
}
</style>

<div class="hero">
    <h1>Welcome to the Smart Customer Behavior Analyzer!</h1>
    <p>This smart tool helps you analyze and export data quickly & efficiently:</p>
    <ul>
        <ul class="text-left space-y-2 text-lg sm:text-xl">
        <li>📂 Upload your CSV or Excel files</li>
        <li>🧹 Handle missing values</li>
        <li>📉 Detect outliers</li>
        <li>📊 Visualize patterns, correlations, and summary stats</li>
        <li>🎯 Analyze trends</li>
    </ul>
</div>
""", unsafe_allow_html=True)

st.markdown("### 📁 Upload CSV, Provide URL, or Use Demo Data")

# Upload Section
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

# URL Section
url_input = st.text_input("🌐 Or enter a public URL (CSV or JSON API)")

# Small message and button directly below the URL input (same style)
demo_message = st.markdown(
    """
    <p style='margin-top: -10px; font-size: 14px;'>
        👉 Or click the Demo Dataset button to view sample data
    </p>
    """,
    unsafe_allow_html=True
)

demo_clicked = st.button("📊 Use Demo Dataset", key="demo")

# Blue demo button style
st.markdown("""
    <style>
    .centered-button {
        display: flex;
        justify-content: center;
        margin-top: 1px;
        margin-bottom: 1px;
    }
    .stButton > button {
        background-color: #007bff;
        color: white;
        border: none;
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 16px;
        cursor: pointer;
        transition: background-color 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #0056b3;
    }
    </style>
""", unsafe_allow_html=True)

# -------------- LOAD DATA --------------
df = None

if "df" not in st.session_state:
    st.session_state["df"] = None

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.session_state["df"] = df
    st.session_state["source"] = "uploaded"
    st.success("✅ File uploaded successfully!")

elif url_input:
    try:
        response = requests.get(url_input)
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "")
            if "text/csv" in content_type or url_input.endswith(".csv"):
                df = pd.read_csv(url_input)
            elif "application/json" in content_type:
                data = response.json()
                df = pd.DataFrame(data)
            else:
                st.error("⚠️ Unsupported content type.")
            st.session_state["df"] = df
            st.session_state["source"] = "url"
            st.success("✅ Data loaded from URL!")
        else:
            st.error(f"⚠️ Failed to fetch data. Status code: {response.status_code}")
    except Exception as e:
        st.error(f"⚠️ Error fetching data: {e}")

elif demo_clicked:
    try:
        demo_url = "https://raw.githubusercontent.com/Svn2003/online_shopping_eda_dashboard/main/online_shoppers_intention.csv"
        df = pd.read_csv(demo_url)
        st.session_state["df"] = df
        st.session_state["source"] = "demo"
        st.success("✅ Demo dataset loaded successfully!")
    except Exception as e:
        st.error(f"❌ Failed to load demo data: {e}")

# Load from session only if not uploaded freshly this time
if st.session_state["df"] is not None and df is None:
    df = st.session_state["df"]

# -------------- SHOW RESET BUTTON ONLY IF DATA EXISTS --------------
if st.session_state["df"] is not None:
    # st.markdown('<div class="centered-button">', unsafe_allow_html=True)
    if st.button("❌ Clear Data & Reset", key="reset"):
        st.session_state.clear()
        st.experimental_set_query_params()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ------------------- MAIN ANALYSIS -------------------
if df is not None:
    # Add friendly labels for 'Revenue' column
    # Ensure 'Revenue' is boolean and create a user-friendly label column
    if "Revenue" in df.columns:
        df["Revenue"] = df["Revenue"].astype(str).str.lower().map({"true": True, "false": False})
        df["Revenue_Label"] = df["Revenue"].replace({True: "Purchased", False: "Not Purchased"})

    st.session_state["df"] = df

    st.header("🔍 Dataset Overview")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("🧮 Rows", df.shape[0])
    with col2:
        st.metric("📊 Columns", df.shape[1])

    st.markdown("### 🗂️ Column Names")
    st.code(", ".join(df.columns))

    # -------- MISSING VALUES --------
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    st.header("⚠️ Missing Values")
    if not missing.empty:
        st.dataframe(missing.reset_index().rename(columns={"index": "Column", 0: "Missing Count"}))
    else:
        st.success("✅ No Missing Values Found")

    # -------- SUMMARY STATS --------
    st.header("📈 Summary Statistics")
    st.dataframe(df.describe(include='all').transpose())

    # -------- COLUMN STATS --------
    st.header("📌 Column-Wise Quick Stats")
    valid_columns = [col for col in df.columns if not df[col].apply(lambda x: isinstance(x, dict)).any()]
    quick_info = pd.DataFrame({
        "Column": valid_columns,
        "Data Type": df[valid_columns].dtypes.values,
        "Unique Values": df[valid_columns].nunique().values,
        "Top Value": [df[col].mode().iloc[0] if not df[col].mode().empty else 'N/A' for col in valid_columns],
        "Missing Values": df[valid_columns].isnull().sum().values
    })
    st.dataframe(quick_info)

    # -------- CORRELATION --------
    st.header("🔥 Feature Correlation (Numerical Only)")
    st.markdown(
    "<p style='font-size: 15px;'>   (This shows how strongly different number-based columns are related to each other.)</p>",
    unsafe_allow_html=True
    )
    corr = df.corr(numeric_only=True)
    if not corr.empty:
        fig = px.imshow(corr, text_auto=True, color_continuous_scale='RdBu_r', aspect="auto")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("⚠️ No numeric features available for correlation.")

    # -------- SHAPE STATS --------
    st.header("🧠 Skewness & Kurtosis")
    st.markdown(
    "<p style='font-size: 15px;'>   (This shows whether each feature's values evenly spread (Skewness) and how peaked or flat their distribution is (Kurtosis)).</p>",
    unsafe_allow_html=True
    )
    numeric_cols = df.select_dtypes(include=np.number).columns
    if len(numeric_cols) > 0:
        stat_data = pd.DataFrame({
            "Feature": numeric_cols,
            "Skewness": [df[col].skew() for col in numeric_cols],
            "Kurtosis": [df[col].kurtosis() for col in numeric_cols]
        })
        st.dataframe(stat_data)

    # -------- COLUMN-WISE VISUALS --------
    st.header("📊 Column-wise Visualization")
    selected_col = st.selectbox("Select a column to visualize", df.columns)

    if df[selected_col].dtype == 'object':
        st.subheader(f"🔸 Value Counts for '{selected_col}'")
        fig = px.histogram(df, x=selected_col, color=selected_col)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.subheader(f"🔹 Distribution of '{selected_col}'")
        fig = px.histogram(df, x=selected_col, nbins=30, marginal="box", opacity=0.7)
        st.plotly_chart(fig, use_container_width=True)

    # -------- REVENUE BASED INSIGHTS --------
    if 'Revenue' in df.columns:
        st.header("🎯 Revenue-Based Behavioral Analysis")

        col3, col4 = st.columns(2)
        with col3:
            if 'VisitorType' in df.columns:
                st.subheader("Visitor Type vs Revenue")
                fig = px.histogram(df, x='VisitorType', color='Revenue_Label')
                st.plotly_chart(fig, use_container_width=True)

        with col4:
            if 'Month' in df.columns:
                st.subheader("Month vs Revenue")
                fig = px.histogram(df, x='Month', color='Revenue_Label')
                st.plotly_chart(fig, use_container_width=True)

        # -------- TAKEAWAYS --------
        st.subheader("📌 Takeaways")
        takeaways = []

        if 'Revenue' in df.columns and 'VisitorType' in df.columns:
            visitor_rates = df.groupby('VisitorType')['Revenue'].mean()
            top = visitor_rates.idxmax()
            takeaways.append(f"🔸 **{top}** visitors are most likely to purchase.")

        if 'Month' in df.columns and 'Revenue' in df.columns:
            month_rates = df.groupby('Month')['Revenue'].mean()
            top_month = month_rates.idxmax()
            takeaways.append(f"🔸 Most purchases happen in **{top_month}**.")

        if 'PageValues' in df.columns and 'Revenue' in df.columns:
            avg_page_value = df.groupby('Revenue')['PageValues'].mean()
            takeaways.append(f"🔸 Buyers see **{avg_page_value.get(1, 0):.2f}** page value on average.")

        if takeaways:
            for tip in takeaways:
                st.markdown(tip)
        else:
            st.info("ℹ️ Not enough data to generate meaningful insights.")



    # -------- DOWNLOAD FINAL FILE --------
    # Sanitize dataframe before download
def sanitize_dataframe(df):
    return df.applymap(lambda x: str(x) if isinstance(x, dict) else x)

# Inject custom style for download button too
st.markdown("""
    <style>
    .centered-button {
        display: flex;
        justify-content: center;
        margin-top: 20px;
        margin-bottom: 20px;
    }
    .stDownloadButton > button {
        background-color: #d9534f;
        color: #ffffff;
        font-weight: bold;
        border: none;
        padding: 12px 28px;
        border-radius: 8px;
        font-size: 16px;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .stDownloadButton > button:hover {
        background-color: #c9302c;
        transform: translateY(-1px);
    }
    </style>
""", unsafe_allow_html=True)

# Show only if dataframe exists
if df is not None:
    st.markdown('<div class="centered-button">', unsafe_allow_html=True)
    st.download_button(
        label="⬇️Download Final Data",
        data=sanitize_dataframe(df).to_csv(index=False).encode(),
        file_name="final_data.csv",
        mime='text/csv'
    )
    st.markdown('</div>', unsafe_allow_html=True)

 

    # # -------- SAVE TO MYSQL --------
    # import socket

    # # Detect if running in Streamlit Cloud (basic check)
    # is_cloud = "streamlit" in socket.gethostname().lower()

    # st.header("🛠️ Save Data to MySQL")
    # save_to_db = st.checkbox("💾 Save uploaded CSV and insights to MySQL")

    # if is_cloud:
    #     st.warning("⚠️ MySQL upload is disabled on Streamlit Cloud.")
    # else:
    #     if save_to_db:
    #         host = st.text_input("Host", "localhost")
    #         user = st.text_input("User", "root")
    #         password = st.text_input("Password", type="password")
    #         db = st.text_input("Database", "csv_analyzer")
    #         table = st.text_input("Table Name", "uploaded_data")

    #         if st.button("Upload to MySQL"):
    #             try:
    #                 encoded_pw = urllib.parse.quote_plus(password)
    #                 engine = create_engine(f"mysql+pymysql://{user}:{encoded_pw}@{host}/{db}")

    #                 df.to_sql(table, con=engine, index=False, if_exists='replace')

    #                 summary = df.describe(include='all').transpose().reset_index()
    #                 summary.columns = ['Feature'] + list(summary.columns[1:])
    #                 summary.to_sql(f"{table}_summary", con=engine, index=False, if_exists='replace')

    #                 if not missing.empty:
    #                     mv = missing.reset_index()
    #                     mv.columns = ['Column', 'MissingCount']
    #                     mv.to_sql(f"{table}_missing", con=engine, index=False, if_exists='replace')

    #                 if not corr.empty:
    #                     corr_long = corr.stack().reset_index()
    #                     corr_long.columns = ['Feature1', 'Feature2', 'Correlation']
    #                     corr_long.to_sql(f"{table}_correlation", con=engine, index=False, if_exists='replace')

    #                 if len(numeric_cols) > 0:
    #                     stat_data.to_sql(f"{table}_stats", con=engine, index=False, if_exists='replace')

    #                 quick_info.to_sql(f"{table}_features", con=engine, index=False, if_exists='replace')

    #                 st.success("✅ Data and insights saved to MySQL successfully!")

    #             except Exception as e:
    #                 st.error(f"❌ MySQL Error: {e}")