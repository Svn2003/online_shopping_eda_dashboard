# conda install -c conda-forge streamlit
# streamlit run online_shopping_eda_dashboard.py
# cd C:\Users\sanga\OneDrive\Desktop\online_shopping_EDA
# streamlit run online_shopping_eda_dashboard.py



import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests
import urllib.parse
import pymysql
from sqlalchemy import create_engine

st.set_page_config(page_title="📊 Smart CSV Analyzer", layout="wide")

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

</style>

<div class="hero">
    <h1>Welcome to the Smart Analyzer</h1>
    <p>This smart tool helps you analyze and export data quickly & efficiently:</p>
    <ul>
        <ul class="text-left space-y-2 text-lg sm:text-xl">
        <li>📂 Upload your CSV or Excel files</li>
        <li>🧹 Handle missing values</li>
        <li>📉 Detect outliers</li>
        <li>📊 Analyze trends</li>
        <li>🛠️ Export cleaned data to MySQL</li>
    </ul>
</div>
""", unsafe_allow_html=True)



# -------------- FILE OR URL INPUT -------------------
uploaded_file = st.file_uploader("📁 Upload a CSV file", type=["csv"])
url_input = st.text_input("🌐 Or enter a public URL (CSV or JSON API)")
df = None

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("✅ File uploaded successfully!")

elif url_input:
    try:
        response = requests.get(url_input)
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "")
            if "text/csv" in content_type or url_input.endswith(".csv"):
                df = pd.read_csv(url_input)
                st.success("✅ CSV loaded from URL!")
            elif "application/json" in content_type:
                data = response.json()
                df = pd.DataFrame(data)
                st.success("✅ JSON API loaded and converted to table!")
            else:
                st.error("⚠️ Unsupported content type.")
        else:
            st.error(f"⚠️ Failed to fetch data. Status code: {response.status_code}")
    except Exception as e:
        st.error(f"⚠️ Error fetching data: {e}")

# ------------------- MAIN ANALYSIS -------------------
if df is not None:
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
    corr = df.corr(numeric_only=True)
    if not corr.empty:
        fig = px.imshow(corr, text_auto=True, color_continuous_scale='RdBu_r', aspect="auto")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("⚠️ No numeric features available for correlation.")

    # -------- SHAPE STATS --------
    st.header("🧠 Skewness & Kurtosis")
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
                fig = px.histogram(df, x='VisitorType', color='Revenue')
                st.plotly_chart(fig, use_container_width=True)

        with col4:
            if 'Month' in df.columns:
                st.subheader("Month vs Revenue")
                fig = px.histogram(df, x='Month', color='Revenue')
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
    def sanitize_dataframe(df):
        return df.applymap(lambda x: str(x) if isinstance(x, dict) else x)

    st.download_button(
        label="⬇️ Download Final Data",
        data=sanitize_dataframe(df).to_csv(index=False).encode(),
        file_name="final_data.csv"
    )

    # -------- SAVE TO MYSQL --------
    st.header("🛠️ Save Data to MySQL")
    save_to_db = st.checkbox("💾 Save uploaded CSV and insights to MySQL")

    if save_to_db:
        host = st.text_input("Host", "localhost")
        user = st.text_input("User", "root")
        password = st.text_input("Password", type="password")
        db = st.text_input("Database", "csv_analyzer")
        table = st.text_input("Table Name", "uploaded_data")

        if st.button("Upload to MySQL"):
            try:
                encoded_pw = urllib.parse.quote_plus(password)
                engine = create_engine(f"mysql+pymysql://{user}:{encoded_pw}@{host}/{db}")

                df.to_sql(table, con=engine, index=False, if_exists='replace')

                summary = df.describe(include='all').transpose().reset_index()
                summary.columns = ['Feature'] + list(summary.columns[1:])
                summary.to_sql(f"{table}_summary", con=engine, index=False, if_exists='replace')

                if not missing.empty:
                    mv = missing.reset_index()
                    mv.columns = ['Column', 'MissingCount']
                    mv.to_sql(f"{table}_missing", con=engine, index=False, if_exists='replace')

                if not corr.empty:
                    corr_long = corr.stack().reset_index()
                    corr_long.columns = ['Feature1', 'Feature2', 'Correlation']
                    corr_long.to_sql(f"{table}_correlation", con=engine, index=False, if_exists='replace')

                if len(numeric_cols) > 0:
                    stat_data.to_sql(f"{table}_stats", con=engine, index=False, if_exists='replace')

                quick_info.to_sql(f"{table}_features", con=engine, index=False, if_exists='replace')

                st.success("✅ Data and insights saved to MySQL successfully!")

            except Exception as e:
                st.error(f"❌ MySQL Error: {e}")



















# import streamlit as st
# import pandas as pd
# import numpy as np
# import seaborn as sns
# import matplotlib.pyplot as plt
# import mysql.connector
# from sqlalchemy import create_engine

# # Config
# st.set_page_config(page_title="CSV Analyzer", layout="wide")
# st.title("📊 Exploratory Data Analysis on Online Shopping Behavior with Interactive Dashboard")

# # File upload
# uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
# df = None

# if uploaded_file:
#     df = pd.read_csv(uploaded_file)
#     st.success("✅ File uploaded successfully!")
    
#     # Show preview
#     st.subheader("📌 Data Preview")
#     st.dataframe(df.head())

#     # Summary
#     st.subheader("📋 Data Info")
#     st.write("**Shape:**", df.shape)
#     st.write("**Columns:**", list(df.columns))
#     st.write("**Missing Values:**")
#     st.write(df.isnull().sum())

#     # Correlation heatmap
#     st.subheader("📈 Correlation Heatmap")
#     corr = df.corr(numeric_only=True)
#     fig, ax = plt.subplots(figsize=(10, 6))
#     sns.heatmap(corr, annot=True, cmap='coolwarm', ax=ax)
#     st.pyplot(fig)

#     # Column selector for plots
#     st.subheader("📊 Visualize Any Column")
#     col = st.selectbox("Choose a column to analyze", df.columns)

#     if df[col].dtype == 'object':
#         fig2, ax2 = plt.subplots()
#         sns.countplot(data=df, x=col, order=df[col].value_counts().index, ax=ax2)
#         plt.xticks(rotation=45)
#         st.pyplot(fig2)
#     else:
#         fig3, ax3 = plt.subplots()
#         sns.histplot(data=df, x=col, kde=True, ax=ax3)
#         st.pyplot(fig3)

#     # MySQL SAVE option
#     st.subheader("🛠️ Save to MySQL")
#     save_to_db = st.checkbox("Save uploaded CSV to MySQL")

#     if save_to_db:
#         try:
#             # Edit credentials accordingly
#             host = st.text_input("Host", "localhost")
#             user = st.text_input("User", "root")
#             password = st.text_input("Password", type="password")
#             db = st.text_input("Database", "csv_analyzer")
#             table = st.text_input("Table Name", "uploaded_data")
            
#             if st.button("Upload to Database"):
#                 # Create connection
#                 from sqlalchemy import create_engine
#                 import urllib.parse
#                 encoded_pw = urllib.parse.quote_plus(password)
#                 engine = create_engine(f"mysql+pymysql://{user}:{encoded_pw}@{host}/{db}")
                
#                 # Save raw CSV data
#                 df.to_sql(table, con=engine, index=False, if_exists='replace')

#                 # Save summary statistics
#                 summary = df.describe(include='all').transpose().reset_index()
#                 summary.columns = ['Feature'] + list(summary.columns[1:])
#                 summary.to_sql(f"{table}_summary", con=engine, index=False, if_exists='replace')


#                 # summary = df.describe(include='all').transpose()
#                 # summary.to_sql(f"{table}_summary", con=engine, if_exists='replace')

#                 # Save missing values report
#                 missing = df.isnull().sum().reset_index()
#                 missing.columns = ['Column', 'MissingCount']
#                 missing.to_sql(f"{table}_missing", con=engine, index=False, if_exists='replace')

#                 # Save correlation matrix
#                 corr = df.corr(numeric_only=True)
#                 corr_long = corr.stack().reset_index()
#                 corr_long.columns = ['Feature1', 'Feature2', 'Correlation']
#                 corr_long.to_sql(f"{table}_correlation", con=engine, index=False, if_exists='replace')

#                 st.success("✅ Raw data and insights uploaded to MySQL successfully!")

#         except Exception as e:
#             st.error(f"MySQL Error: {e}")

# if st.button("Upload to Database"):
            #     st.write("🔍 Debug - Host:", host)
            #     st.write("🔍 Debug - User:", user)
            #     st.write("🔍 Debug - Connection String:", f"mysql+pymysql://{user}:****@{host}/{db}")
            #     import urllib.parse
            #     safe_password = urllib.parse.quote_plus(password)
            #     engine = create_engine(f"mysql+pymysql://{user}:{safe_password}@{host}/{db}")

            #     # engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}/{db}")
            #     # engine = create_engine(f"mysql+mysqlconnector://{user}:{password}@{host}/{db}")
            #     df.to_sql(table, con=engine, index=False, if_exists='replace')
            #     st.success("Data uploaded to MySQL successfully!")

# import streamlit as st
# import pandas as pd
# import numpy as np
# import seaborn as sns
# import matplotlib.pyplot as plt
# from sqlalchemy import create_engine
# import pymysql
# import urllib.parse

# # Streamlit setup
# st.set_page_config(page_title="📊 Smart CSV Analyzer", layout="wide")
# st.title("📊 Exploratory Data Analysis on Online Shopping Behavior")

# # File uploader
# uploaded_file = st.file_uploader("📁 Upload a CSV file for analysis", type=["csv"])
# df = None

# if uploaded_file:
#     df = pd.read_csv(uploaded_file)
#     st.success("✅ File uploaded successfully!")

#     # ---- Section: Data Overview ----
#     st.header("🔍 Dataset Overview")
#     col1, col2 = st.columns(2)
#     with col1:
#         st.metric("🧮 Rows", df.shape[0])
#     with col2:
#         st.metric("📊 Columns", df.shape[1])

#     st.markdown("### 🗂️ Column Names")
#     st.write(", ".join(df.columns))

#     # ---- Section: Missing Values ----
#     missing = df.isnull().sum()
#     missing = missing[missing > 0]
#     if not missing.empty:
#         st.markdown("### ⚠️ Missing Values")
#         st.dataframe(missing.reset_index().rename(columns={"index": "Column", 0: "Missing Count"}))
#     else:
#         st.markdown("### ✅ No Missing Values Found")

#     # ---- Section: Summary Statistics ----
#     st.header("📈 Summary Statistics")
#     st.dataframe(df.describe(include='all').transpose())

#     # ---- Section: Correlation Heatmap ----
#     st.header("🔥 Feature Correlation")
#     corr = df.corr(numeric_only=True)
#     fig, ax = plt.subplots(figsize=(10, 6))
#     sns.heatmap(corr, annot=True, cmap="coolwarm", ax=ax)
#     st.pyplot(fig)

#     # ---- Section: Column Exploration ----
#     st.header("📊 Column-wise Analysis")
#     selected_col = st.selectbox("Select a column to visualize", df.columns)

#     if df[selected_col].dtype == 'object':
#         st.subheader(f"🔸 Value Counts for '{selected_col}'")
#         fig, ax = plt.subplots()
#         sns.countplot(data=df, x=selected_col, order=df[selected_col].value_counts().index[:10], ax=ax)
#         ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
#         st.pyplot(fig)
#     else:
#         st.subheader(f"🔹 Distribution of '{selected_col}'")
#         fig, ax = plt.subplots()
#         sns.histplot(df[selected_col], kde=True, bins=30, ax=ax)
#         st.pyplot(fig)

#         st.subheader(f"📦 Boxplot for Outlier Detection in '{selected_col}'")
#         fig, ax = plt.subplots()
#         sns.boxplot(df[selected_col], ax=ax)
#         st.pyplot(fig)

#     # ---- Section: Save to MySQL ----
#     st.header("🛠️ Save Data to MySQL")
#     save_to_db = st.checkbox("💾 Save uploaded CSV and insights to MySQL")

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

#                 # Upload raw data
#                 df.to_sql(table, con=engine, index=False, if_exists='replace')

#                 # Summary
#                 summary = df.describe(include='all').transpose().reset_index()
#                 summary.columns = ['Feature'] + list(summary.columns[1:])
#                 summary.to_sql(f"{table}_summary", con=engine, index=False, if_exists='replace')

#                 # Missing values (only if any)
#                 if not missing.empty:
#                     mv = missing.reset_index()
#                     mv.columns = ['Column', 'MissingCount']
#                     mv.to_sql(f"{table}_missing", con=engine, index=False, if_exists='replace')

#                 # Correlation matrix
#                 corr_long = corr.stack().reset_index()
#                 corr_long.columns = ['Feature1', 'Feature2', 'Correlation']
#                 corr_long.to_sql(f"{table}_correlation", con=engine, index=False, if_exists='replace')

#                 st.success("✅ Data and insights saved to MySQL successfully!")

#             except Exception as e:
#                 st.error(f"❌ MySQL Error: {e}")



# import streamlit as st
# import pandas as pd
# import numpy as np
# import seaborn as sns
# import matplotlib.pyplot as plt
# from sqlalchemy import create_engine
# import pymysql
# import urllib.parse

# # Streamlit setup
# st.set_page_config(page_title="📊 Smart CSV Analyzer", layout="wide")
# st.title("📊 Exploratory Data Analysis on Online Shopping Behavior")

# # File uploader
# # uploaded_file = st.file_uploader("📁 Upload a CSV file for analysis", type=["csv"])
# # df = None

# # # if uploaded_file:
# # #     df = pd.read_csv(uploaded_file)
# # #     st.success("✅ File uploaded successfully!")
# # if uploaded_file:
# #     df = pd.read_csv(uploaded_file)

# #     # ✅ FIX: Convert boolean column 'Revenue' to string if it exists
# #     if 'Revenue' in df.columns and df['Revenue'].dtype == 'bool':
# #         df['Revenue'] = df['Revenue'].astype(str)

# #     st.success("✅ File uploaded successfully!")
# uploaded_file = st.file_uploader("📁 Upload a CSV file", type=["csv"])
# url_input = st.text_input("🌐 Or enter a public URL (CSV or JSON API)")
# df = None

# if uploaded_file:
#     df = pd.read_csv(uploaded_file)
#     st.success("✅ File uploaded successfully!")

# elif url_input:
#     try:
#         import requests
#         response = requests.get(url_input)
#         if response.status_code == 200:
#             content_type = response.headers.get("Content-Type", "")
#             if "text/csv" in content_type or url_input.endswith(".csv"):
#                 df = pd.read_csv(url_input)
#                 st.success("✅ CSV loaded from URL!")
#             elif "application/json" in content_type:
#                 data = response.json()
#                 df = pd.DataFrame(data)
#                 st.success("✅ JSON API loaded and converted to table!")
#             else:
#                 st.error("⚠️ Unsupported content type.")
#         else:
#             st.error(f"⚠️ Failed to fetch data. Status code: {response.status_code}")
#     except Exception as e:
#         st.error(f"⚠️ Error fetching data: {e}")

# # ✅ Move everything below this point OUTSIDE the if-elif
# # ---- Section: Data Overview ----
# if df is not None:
#     st.header("🔍 Dataset Overview")
#     col1, col2 = st.columns(2)
#     with col1:
#         st.metric("🧮 Rows", df.shape[0])
#     with col2:
#         st.metric("📊 Columns", df.shape[1])

#     st.markdown("### 🗂️ Column Names")
#     st.write(", ".join(df.columns))

#     # ---- Section: Missing Values ----
#     missing = df.isnull().sum()
#     missing = missing[missing > 0]
#     if not missing.empty:
#         st.markdown("### ⚠️ Missing Values")
#         st.dataframe(missing.reset_index().rename(columns={"index": "Column", 0: "Missing Count"}))
#     else:
#         st.markdown("### ✅ No Missing Values Found")

#     # ---- Section: Summary Statistics ----
#     st.header("📈 Summary Statistics")
#     st.dataframe(df.describe(include='all').transpose())

#     # ---- Section: Feature Quick Info ----
#     st.header("📌 Column-Wise Quick Stats")
#     # Step 1: Identify columns that do NOT contain dicts
#     valid_columns = [col for col in df.columns if not df[col].apply(lambda x: isinstance(x, dict)).any()]

#     # Step 2: Build Quick Info only for those valid columns
#     quick_info = pd.DataFrame({
#         "Column": valid_columns,
#         "Data Type": df[valid_columns].dtypes.values,
#         "Unique Values": df[valid_columns].nunique().values,
#         "Top Value": [df[col].mode().iloc[0] if not df[col].mode().empty else 'N/A' for col in valid_columns],
#         "Missing Values": df[valid_columns].isnull().sum().values
#     })
#     # quick_info = pd.DataFrame({
#     #     "Column": df.columns,
#     #     "Data Type": df.dtypes.values,
#     #     "Unique Values": df.nunique().values,
#     #     "Top Value": [df[col].mode().iloc[0] if not df[col].mode().empty else 'N/A' for col in df.columns],
#     #     "Missing Values": df.isnull().sum().values
#     # })
#     st.dataframe(quick_info)

#     # ---- Section: Correlation Heatmap ----
#     st.header("🔥 Feature Correlation")
#     corr = df.corr(numeric_only=True)
#     fig, ax = plt.subplots(figsize=(10, 6))
#     sns.heatmap(corr, annot=True, cmap="coolwarm", ax=ax)
#     st.pyplot(fig)

#     # ---- Section: Statistical Shape ----
#     st.header("🧠 Skewness & Kurtosis")
#     numeric_cols = df.select_dtypes(include=np.number).columns
#     if len(numeric_cols) > 0:
#         stat_data = pd.DataFrame({
#             "Feature": numeric_cols,
#             "Skewness": [df[col].skew() for col in numeric_cols],
#             "Kurtosis": [df[col].kurtosis() for col in numeric_cols]
#         })
#         st.dataframe(stat_data)

#     # ---- Section: Column Exploration ----
#     st.header("📊 Column-wise Visualization")
#     selected_col = st.selectbox("Select a column to visualize", df.columns)

#     if df[selected_col].dtype == 'object':
#         st.subheader(f"🔸 Value Counts for '{selected_col}'")
#         fig, ax = plt.subplots()
#         sns.countplot(data=df, x=selected_col, order=df[selected_col].value_counts().index[:10], ax=ax)
#         ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
#         st.pyplot(fig)
#     else:
#         st.subheader(f"🔹 Distribution of '{selected_col}'")
#         fig, ax = plt.subplots()
#         sns.histplot(df[selected_col], kde=True, bins=30, ax=ax)
#         st.pyplot(fig)

#         st.subheader(f"📦 Boxplot for Outlier Detection in '{selected_col}'")
#         fig, ax = plt.subplots()
#         sns.boxplot(data=df, x=selected_col, ax=ax)
#         st.pyplot(fig)

#     # ---- Section: Revenue-Based Insights (if available) ----
#     if 'Revenue' in df.columns:
#         st.header("🎯 Revenue-Based Behavioral Analysis")

#         col3, col4 = st.columns(2)
#         with col3:
#             st.subheader("Visitor Type vs Revenue")
#             fig, ax = plt.subplots()
#             sns.countplot(x='VisitorType', hue=df['Revenue'].astype(str), data=df, ax=ax)
#             st.pyplot(fig)

#         with col4:
#             st.subheader("Month vs Revenue")
#             if 'Month' in df.columns:
#                 fig, ax = plt.subplots()
#                 sns.countplot(x='Month', hue=df['Revenue'].astype(str), data=df, ax=ax)
#                 plt.xticks(rotation=45)
#                 st.pyplot(fig)

        
#         # with col3:
#         #     st.subheader("Visitor Type vs Revenue")
#         #     fig, ax = plt.subplots()
#         #     sns.countplot(x='VisitorType', hue='Revenue', data=df, ax=ax)
#         #     st.pyplot(fig)

#         # with col4:
#         #     st.subheader("Month vs Revenue")
#         #     if 'Month' in df.columns:
#         #         fig, ax = plt.subplots()
#         #         sns.countplot(x='Month', hue='Revenue', data=df, ax=ax)
#         #         plt.xticks(rotation=45)
#         #         st.pyplot(fig)

#     # # ---- Optional: TensorFlow Placeholder ----
#     # st.header("🔮 Predictive Modeling (Future Scope)")
#     # st.info("This section can be extended using TensorFlow to predict purchase likelihood based on behavior.")
#     # ---- Section: Predictive Modeling ----
#     if 'Revenue' in df.columns:
#         st.header("🔮 Predictive Modeling with TensorFlow (Revenue Classifier)")

#         from sklearn.model_selection import train_test_split
#         from sklearn.preprocessing import LabelEncoder, StandardScaler
#         from sklearn.metrics import classification_report, confusion_matrix
#         import tensorflow as tf

#         # Prepare data
#         X = df.drop('Revenue', axis=1).copy()
#         y = df['Revenue']

#         # Encode target if it's string
#         if y.dtype == 'object':
#             y = LabelEncoder().fit_transform(y)

#         # Encode categorical features
#         for col in X.select_dtypes(include=['object']).columns:
#             X[col] = LabelEncoder().fit_transform(X[col])

#         # Fill missing
#         X = X.fillna(0)

#         # Standardize
#         scaler = StandardScaler()
#         X_scaled = scaler.fit_transform(X)

#         # Split data
#         X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

#         # Build model
#         model = tf.keras.Sequential([
#             tf.keras.layers.Dense(64, activation='relu', input_shape=(X_train.shape[1],)),
#             tf.keras.layers.Dense(32, activation='relu'),
#             tf.keras.layers.Dense(1, activation='sigmoid')
#         ])

#         model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

#         # Train
#         with st.spinner("Training the model..."):
#             history = model.fit(X_train, y_train, epochs=10, batch_size=16, verbose=0)

#         # Evaluate
#         st.success("✅ Model trained successfully!")

#         loss, accuracy = model.evaluate(X_test, y_test, verbose=0)
#         st.write(f"**Model Accuracy:** {accuracy:.2%}")

#         # Predict and show metrics
#         y_pred = (model.predict(X_test) > 0.5).astype("int32")

#         report = classification_report(y_test, y_pred, output_dict=True)
#         st.subheader("📋 Classification Report")
#         st.dataframe(pd.DataFrame(report).transpose())



#     # ---- Section: Save to MySQL ----
#     st.header("🛠️ Save Data to MySQL")
#     save_to_db = st.checkbox("💾 Save uploaded CSV and insights to MySQL")

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

#                 # Save raw data
#                 df.to_sql(table, con=engine, index=False, if_exists='replace')

#                 # Save summary
#                 summary = df.describe(include='all').transpose().reset_index()
#                 summary.columns = ['Feature'] + list(summary.columns[1:])
#                 summary.to_sql(f"{table}_summary", con=engine, index=False, if_exists='replace')

#                 # Save missing values (only if any)
#                 if not missing.empty:
#                     mv = missing.reset_index()
#                     mv.columns = ['Column', 'MissingCount']
#                     mv.to_sql(f"{table}_missing", con=engine, index=False, if_exists='replace')

#                 # Save correlation matrix
#                 corr_long = corr.stack().reset_index()
#                 corr_long.columns = ['Feature1', 'Feature2', 'Correlation']
#                 corr_long.to_sql(f"{table}_correlation", con=engine, index=False, if_exists='replace')

#                 # Save stats
#                 if len(numeric_cols) > 0:
#                     stat_data.to_sql(f"{table}_stats", con=engine, index=False, if_exists='replace')

#                 # Save column overview
#                 quick_info.to_sql(f"{table}_features", con=engine, index=False, if_exists='replace')

#                 st.success("✅ Data and insights saved to MySQL successfully!")

#             except Exception as e:
#                 st.error(f"❌ MySQL Error: {e}")




# # Smart CSV Analyzer with Advanced Features

# import streamlit as st
# import pandas as pd
# import numpy as np
# import plotly.express as px
# import seaborn as sns
# import matplotlib.pyplot as plt
# from sqlalchemy import create_engine
# import pymysql
# import urllib.parse
# import requests
# from sklearn.model_selection import train_test_split
# from sklearn.preprocessing import LabelEncoder, StandardScaler
# from sklearn.metrics import classification_report
# import tensorflow as tf

# # Utility to sanitize data for Arrow compatibility
# def sanitize_dataframe(df):
#     for col in df.columns:
#         if df[col].apply(lambda x: isinstance(x, (dict, list))).any():
#             df[col] = df[col].apply(lambda x: str(x))
#         elif df[col].dtype == 'object':
#             df[col] = df[col].astype(str)
#     return df

# # Page config
# st.set_page_config(page_title="📊 Smart Analyzer", page_icon="📈", layout="wide")

# # Sidebar Navigation
# st.sidebar.title("🧭 Navigation")
# page = st.sidebar.radio("Go to:", [
#     "🏠 Home",
#     "📁 Upload & Load",
#     "📊 Analyze",
#     "🔮 Predict",
#     "🛠️ Save to MySQL",
#     "📋 Summary"
# ])

# # Global variables
# df = None

# # ---- 1. Home ----
# if page == "🏠 Home":
#     st.title("📊 Smart Customer Behavior Analyzer")
#     st.markdown("""
#     Welcome to the Smart Analyzer! This tool lets you:
#     - Upload or fetch customer behavior data
#     - Analyze trends and correlations
#     - Predict purchase intent
#     - Export insights to MySQL or CSV
#     """)

# # ---- 2. Upload & Load ----
# elif page == "📁 Upload & Load":
#     uploaded_file = st.file_uploader("📁 Upload CSV File", type=["csv"])
#     url_input = st.text_input("🌐 Or enter CSV/JSON API URL")

#     if uploaded_file:
#         df = pd.read_csv(uploaded_file)
#         st.success("✅ File uploaded successfully!")
#     elif url_input:
#         try:
#             response = requests.get(url_input)
#             if response.status_code == 200:
#                 if "csv" in response.headers.get("Content-Type", "") or url_input.endswith(".csv"):
#                     df = pd.read_csv(url_input)
#                 else:
#                     df = pd.DataFrame(response.json())
#                 st.success("✅ Data loaded from URL!")
#             else:
#                 st.error(f"Failed to load. Status: {response.status_code}")
#         except Exception as e:
#             st.error(f"Error: {e}")

#     if df is not None:
#         st.session_state.df = df
#         st.dataframe(sanitize_dataframe(df.head()))
#         st.download_button("⬇️ Download Loaded Data", data=sanitize_dataframe(df).to_csv(index=False).encode(), file_name="loaded_data.csv")

# # ---- 3. Analyze ----
# elif page == "📊 Analyze":
#     df = st.session_state.get("df")
#     if df is not None:
#         with st.expander("📌 Quick Info"):
#             col1, col2 = st.columns(2)
#             with col1:
#                 st.metric("Rows", df.shape[0])
#             with col2:
#                 st.metric("Columns", df.shape[1])
#             st.write("### Columns")
#             st.write(", ".join(df.columns))

#         with st.expander("⚠️ Missing Values"):
#             missing = df.isnull().sum()
#             missing = missing[missing > 0]
#             if not missing.empty:
#                 st.dataframe(sanitize_dataframe(missing.reset_index().rename(columns={0: "Missing Count", "index": "Column"})))
#             else:
#                 st.success("✅ No Missing Values")

#         with st.expander("📈 Correlation Heatmap"):
#             corr = df.corr(numeric_only=True)
#             fig = px.imshow(corr, text_auto=True, color_continuous_scale='RdBu')
#             st.plotly_chart(fig)

#         with st.expander("📊 Column Visualization"):
#             selected_col = st.selectbox("Choose a column to plot", df.columns)
#             if df[selected_col].dtype == 'object':
#                 fig = px.histogram(df, x=selected_col, title=f"Distribution of {selected_col}")
#                 st.plotly_chart(fig)
#             else:
#                 fig = px.box(df, y=selected_col, points="all", title=f"Boxplot of {selected_col}")
#                 st.plotly_chart(fig)

# # ---- 4. Predict ----
# elif page == "🔮 Predict":
#     df = st.session_state.get("df")
#     if df is not None and 'Revenue' in df.columns:
#         st.subheader("Predicting Purchase Likelihood")

#         X = df.drop('Revenue', axis=1).copy()
#         y = df['Revenue']

#         if y.dtype == 'object':
#             y = LabelEncoder().fit_transform(y)

#         for col in X.select_dtypes(include=['object']).columns:
#             X[col] = LabelEncoder().fit_transform(X[col])

#         X = X.fillna(0)
#         X_scaled = StandardScaler().fit_transform(X)

#         X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

#         model = tf.keras.Sequential([
#             tf.keras.layers.Dense(64, activation='relu', input_shape=(X_train.shape[1],)),
#             tf.keras.layers.Dense(32, activation='relu'),
#             tf.keras.layers.Dense(1, activation='sigmoid')
#         ])
#         model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

#         with st.spinner("Training Model..."):
#             model.fit(X_train, y_train, epochs=10, batch_size=16, verbose=0)

#         acc = model.evaluate(X_test, y_test, verbose=0)[1]
#         st.success(f"✅ Accuracy: {acc:.2%}")

#         y_pred = (model.predict(X_test) > 0.5).astype("int32")
#         report = classification_report(y_test, y_pred, output_dict=True)
#         st.dataframe(sanitize_dataframe(pd.DataFrame(report).transpose()))

#         predictions_df = pd.DataFrame(X_test, columns=df.drop('Revenue', axis=1).columns)
#         predictions_df['Actual'] = y_test
#         predictions_df['Predicted'] = y_pred
#         st.download_button("⬇️ Download Predictions", sanitize_dataframe(predictions_df).to_csv(index=False).encode(), "predictions.csv")

# # ---- 5. Save to MySQL ----
# elif page == "🛠️ Save to MySQL":
#     df = st.session_state.get("df")
#     if df is not None:
#         st.subheader("Upload Data & Insights to MySQL")

#         host = st.text_input("Host", "localhost")
#         user = st.text_input("User", "root")
#         password = st.text_input("Password", type="password")
#         db = st.text_input("Database", "csv_analyzer")
#         table = st.text_input("Table Name", "uploaded_data")

#         if st.button("Upload"):
#             try:
#                 encoded_pw = urllib.parse.quote_plus(password)
#                 engine = create_engine(f"mysql+pymysql://{user}:{encoded_pw}@{host}/{db}")
#                 sanitize_dataframe(df).to_sql(table, con=engine, index=False, if_exists='replace')
#                 st.success("✅ Data uploaded to MySQL")
#             except Exception as e:
#                 st.error(f"❌ Error: {e}")

# # ---- 6. Summary ----
# elif page == "📋 Summary":
#     df = st.session_state.get("df")
#     if df is not None:
#         st.subheader("📌 Top 3 Takeaways")
#         takeaways = []

#         if 'Revenue' in df.columns and 'VisitorType' in df.columns:
#             visitor_rates = df.groupby('VisitorType')['Revenue'].mean()
#             top = visitor_rates.idxmax()
#             takeaways.append(f"🔸 **{top}** visitors are most likely to purchase.")

#         if 'Month' in df.columns and 'Revenue' in df.columns:
#             month_rates = df.groupby('Month')['Revenue'].mean()
#             top_month = month_rates.idxmax()
#             takeaways.append(f"🔸 Most purchases happen in **{top_month}**.")

#         if 'PageValues' in df.columns:
#             avg_page_value = df.groupby('Revenue')['PageValues'].mean()
#             takeaways.append(f"🔸 Users who buy see **{avg_page_value.get(1, 0):.2f}** page value on average.")

#         for tip in takeaways:
#             st.markdown(tip)

#         st.download_button("⬇️ Download Final Data", sanitize_dataframe(df).to_csv(index=False).encode(), "final_data.csv")





# # Smart CSV Analyzer - Modern UI Layout

# import streamlit as st
# import pandas as pd
# import numpy as np
# import plotly.express as px
# import seaborn as sns
# import matplotlib.pyplot as plt
# from sqlalchemy import create_engine
# import pymysql
# import urllib.parse
# import requests
# from sklearn.model_selection import train_test_split
# from sklearn.preprocessing import LabelEncoder, StandardScaler
# from sklearn.metrics import classification_report
# import tensorflow as tf

# # Utility to sanitize data for Arrow compatibility
# def sanitize_dataframe(df):
#     for col in df.columns:
#         if df[col].apply(lambda x: isinstance(x, (dict, list))).any():
#             df[col] = df[col].apply(lambda x: str(x))
#         elif df[col].dtype == 'object':
#             df[col] = df[col].astype(str)
#     return df

# # Streamlit setup
# st.set_page_config(page_title="Smart Analyzer", layout="wide")

# st.markdown("""
#     <style>
#     .main-title {
#         font-size: 36px;
#         font-weight: bold;
#         color: #2c3e50;
#         margin-bottom: 20px;
#     }
#     .section-title {
#         font-size: 24px;
#         color: #1f77b4;
#         margin-top: 30px;
#         margin-bottom: 10px;
#     }
#     .subtitle {
#         font-size: 16px;
#         color: #555;
#         margin-bottom: 15px;
#     }
#     </style>
# """, unsafe_allow_html=True)

# st.markdown('<div class="main-title">📊 Smart CSV Analyzer - Interactive Dashboard</div>', unsafe_allow_html=True)
# st.markdown('<div class="subtitle">Upload or fetch any CSV or JSON API URL to begin exploring insights, trends, and predictions.</div>', unsafe_allow_html=True)

# uploaded_file = st.file_uploader("📁 Upload a CSV file", type=["csv"])
# url_input = st.text_input("🌐 Or enter a public CSV or JSON API URL")
# df = None

# if uploaded_file:
#     df = pd.read_csv(uploaded_file)
#     st.success("✅ File uploaded successfully!")
# elif url_input:
#     try:
#         response = requests.get(url_input)
#         if response.status_code == 200:
#             if "csv" in response.headers.get("Content-Type", "") or url_input.endswith(".csv"):
#                 df = pd.read_csv(url_input)
#             else:
#                 df = pd.DataFrame(response.json())
#             st.success("✅ Data loaded from URL!")
#         else:
#             st.error(f"Failed to load. Status: {response.status_code}")
#     except Exception as e:
#         st.error(f"Error: {e}")

# if df is not None:
#     st.markdown('<div class="section-title">🔍 Dataset Overview</div>', unsafe_allow_html=True)
#     col1, col2 = st.columns(2)
#     col1.metric("🧮 Rows", df.shape[0])
#     col2.metric("📊 Columns", df.shape[1])

#     st.dataframe(sanitize_dataframe(df.head()))
#     st.download_button("⬇️ Download Loaded Data", data=sanitize_dataframe(df).to_csv(index=False).encode(), file_name="loaded_data.csv")

#     st.markdown('<div class="section-title">⚠️ Missing Values</div>', unsafe_allow_html=True)
#     missing = df.isnull().sum()
#     missing = missing[missing > 0]
#     if not missing.empty:
#         st.dataframe(sanitize_dataframe(missing.reset_index().rename(columns={0: "Missing Count", "index": "Column"})))
#     else:
#         st.success("✅ No Missing Values")

#     st.markdown('<div class="section-title">📈 Correlation Heatmap</div>', unsafe_allow_html=True)
#     corr = df.corr(numeric_only=True)
#     fig = px.imshow(corr, text_auto=True, color_continuous_scale='Viridis')
#     st.plotly_chart(fig, use_container_width=True)

#     st.markdown('<div class="section-title">📊 Column Visualization</div>', unsafe_allow_html=True)
#     selected_col = st.selectbox("Choose a column to analyze", df.columns)
#     if df[selected_col].dtype == 'object':
#         fig = px.histogram(df, x=selected_col, title=f"Distribution of {selected_col}")
#         st.plotly_chart(fig, use_container_width=True)
#     else:
#         fig = px.box(df, y=selected_col, title=f"Boxplot of {selected_col}", points="all")
#         st.plotly_chart(fig, use_container_width=True)

#     if 'Revenue' in df.columns:
#         st.markdown('<div class="section-title">🎯 Revenue-Based Behavioral Insights</div>', unsafe_allow_html=True)
#         if 'VisitorType' in df.columns:
#             fig = px.histogram(df, x='VisitorType', color=df['Revenue'].astype(str), barmode='group', title="Visitor Type vs Revenue")
#             st.plotly_chart(fig, use_container_width=True)

#         if 'Month' in df.columns:
#             fig = px.histogram(df, x='Month', color=df['Revenue'].astype(str), barmode='group', title="Month vs Revenue")
#             st.plotly_chart(fig, use_container_width=True)

#     # Predictive Modeling
#     if 'Revenue' in df.columns:
#         st.markdown('<div class="section-title">🔮 Purchase Prediction using TensorFlow</div>', unsafe_allow_html=True)
#         X = df.drop('Revenue', axis=1).copy()
#         y = df['Revenue']

#         if y.dtype == 'object':
#             y = LabelEncoder().fit_transform(y)

#         for col in X.select_dtypes(include=['object']).columns:
#             X[col] = LabelEncoder().fit_transform(X[col])

#         X = X.fillna(0)
#         X_scaled = StandardScaler().fit_transform(X)
#         X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

#         model = tf.keras.Sequential([
#             tf.keras.layers.Dense(64, activation='relu', input_shape=(X_train.shape[1],)),
#             tf.keras.layers.Dense(32, activation='relu'),
#             tf.keras.layers.Dense(1, activation='sigmoid')
#         ])
#         model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
#         with st.spinner("Training the model..."):
#             model.fit(X_train, y_train, epochs=10, batch_size=16, verbose=0)

#         acc = model.evaluate(X_test, y_test, verbose=0)[1]
#         st.success(f"✅ Model trained. Accuracy: {acc:.2%}")

#         y_pred = (model.predict(X_test) > 0.5).astype("int32")
#         report = classification_report(y_test, y_pred, output_dict=True)
#         st.dataframe(sanitize_dataframe(pd.DataFrame(report).transpose()))

#     # Save to MySQL
#     st.markdown('<div class="section-title">🛠️ Save to MySQL</div>', unsafe_allow_html=True)
#     save_to_db = st.checkbox("💾 Save data and insights to MySQL")
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
#                 sanitize_dataframe(df).to_sql(table, con=engine, index=False, if_exists='replace')
#                 st.success("✅ Upload successful!")
#             except Exception as e:
#                 st.error(f"❌ MySQL Error: {e}")

#     # Takeaways
#     st.markdown('<div class="section-title">📋 Auto Insights</div>', unsafe_allow_html=True)
#     takeaways = []
#     if 'Revenue' in df.columns and 'VisitorType' in df.columns:
#         visitor_rates = df.groupby('VisitorType')['Revenue'].mean()
#         top = visitor_rates.idxmax()
#         takeaways.append(f"🔸 **{top}** visitors are most likely to convert.")

#     if 'Month' in df.columns and 'Revenue' in df.columns:
#         month_rates = df.groupby('Month')['Revenue'].mean()
#         top_month = month_rates.idxmax()
#         takeaways.append(f"🔸 Most purchases happen in **{top_month}**.")

#     if 'PageValues' in df.columns:
#         avg_val = df.groupby('Revenue')['PageValues'].mean()
#         takeaways.append(f"🔸 Buyers see average **{avg_val.get(1, 0):.2f}** in page value.")

#     for tip in takeaways:
#         st.markdown(tip)

#     st.download_button("⬇️ Download Final Data", sanitize_dataframe(df).to_csv(index=False).encode(), file_name="final_data.csv")




# # Smart CSV Analyzer - Polished & Insightful EDA Platform

# import streamlit as st
# import pandas as pd
# import numpy as np
# import plotly.express as px
# import seaborn as sns
# import matplotlib.pyplot as plt
# from sqlalchemy import create_engine
# import pymysql
# import urllib.parse
# import requests
# from sklearn.model_selection import train_test_split
# from sklearn.preprocessing import LabelEncoder, StandardScaler
# from sklearn.metrics import classification_report
# import tensorflow as tf

# # ========== UTILITY ==========
# def sanitize_dataframe(df):
#     for col in df.columns:
#         if df[col].apply(lambda x: isinstance(x, (dict, list))).any():
#             df[col] = df[col].apply(lambda x: str(x))
#         elif df[col].dtype == 'object':
#             df[col] = df[col].astype(str)
#     return df

# # ========== UI SETUP ==========
# st.set_page_config(page_title="Smart CSV Analyzer", layout="wide")

# st.markdown("""
#     <style>
#     .main-title {
#         font-size: 38px;
#         font-weight: bold;
#         color: #004466;
#         margin-bottom: 10px;
#     }
#     .section-title {
#         font-size: 24px;
#         color: #006699;
#         margin-top: 35px;
#         margin-bottom: 10px;
#     }
#     .subtitle {
#         font-size: 16px;
#         color: #555;
#         margin-bottom: 20px;
#     }
#     </style>
# """, unsafe_allow_html=True)

# st.markdown('<div class="main-title">📊 Smart CSV Analyzer</div>', unsafe_allow_html=True)
# st.markdown('<div class="subtitle">Explore, visualize, and predict behavior using structured data from CSVs or APIs.</div>', unsafe_allow_html=True)

# # ========== FILE UPLOAD ==========
# uploaded_file = st.file_uploader("📁 Upload a CSV file", type=["csv"])
# url_input = st.text_input("🌐 Or enter a public CSV/JSON API URL")
# df = None

# if uploaded_file:
#     df = pd.read_csv(uploaded_file)
#     st.success("✅ File uploaded successfully!")
# elif url_input:
#     try:
#         response = requests.get(url_input)
#         if response.status_code == 200:
#             if "csv" in response.headers.get("Content-Type", "") or url_input.endswith(".csv"):
#                 df = pd.read_csv(url_input)
#             else:
#                 df = pd.DataFrame(response.json())
#             st.success("✅ Data loaded from URL!")
#         else:
#             st.error(f"Failed to load. Status: {response.status_code}")
#     except Exception as e:
#         st.error(f"Error: {e}")

# # ========== MAIN ANALYSIS ==========
# if df is not None:
#     df = sanitize_dataframe(df)

#     st.markdown('<div class="section-title">🔍 Dataset Overview</div>', unsafe_allow_html=True)
#     st.dataframe(df.head())
#     col1, col2 = st.columns(2)
#     col1.metric("🧮 Rows", df.shape[0])
#     col2.metric("📊 Columns", df.shape[1])

#     st.markdown('<div class="section-title">📌 Quick Info</div>', unsafe_allow_html=True)
#     quick_info = pd.DataFrame({
#         "Column": df.columns,
#         "Data Type": df.dtypes.astype(str).values,
#         "Unique Values": df.nunique().values,
#         "Top Value": [df[col].mode().iloc[0] if not df[col].mode().empty else 'N/A' for col in df.columns],
#         "Missing Values": df.isnull().sum().values
#     })
#     st.dataframe(quick_info)

#     st.markdown('<div class="section-title">📈 Summary Statistics</div>', unsafe_allow_html=True)
#     st.dataframe(df.describe(include='all').transpose())

#     st.markdown('<div class="section-title">⚠️ Missing Values</div>', unsafe_allow_html=True)
#     missing = df.isnull().sum()
#     missing = missing[missing > 0]
#     if not missing.empty:
#         st.dataframe(missing.reset_index().rename(columns={0: "Missing Count", "index": "Column"}))
#     else:
#         st.success("✅ No missing values detected!")

#     st.markdown('<div class="section-title">🔥 Feature Correlation</div>', unsafe_allow_html=True)
#     corr = df.corr(numeric_only=True)
#     fig = px.imshow(corr, text_auto=True, color_continuous_scale='Viridis', width=800, height=500)
#     st.plotly_chart(fig, use_container_width=True)

#     st.markdown('<div class="section-title">📊 Column Explorer</div>', unsafe_allow_html=True)
#     selected_col = st.selectbox("Choose column to visualize", df.columns)
#     if df[selected_col].dtype == 'object':
#         fig = px.histogram(df, x=selected_col, title=f"Distribution of {selected_col}", width=700, height=400)
#     else:
#         fig = px.box(df, y=selected_col, title=f"Boxplot of {selected_col}", width=700, height=400, points="outliers")
#     st.plotly_chart(fig, use_container_width=True)

#     # ========== REVENUE BEHAVIOR ==========
#     if 'Revenue' in df.columns:
#         st.markdown('<div class="section-title">🎯 Revenue Behavioral Patterns</div>', unsafe_allow_html=True)

#         if 'VisitorType' in df.columns:
#             fig = px.histogram(df, x='VisitorType', color=df['Revenue'].astype(str), barmode='group',
#                                title="Visitor Type vs Revenue", width=700, height=400)
#             st.plotly_chart(fig, use_container_width=True)

#         if 'Month' in df.columns:
#             fig = px.histogram(df, x='Month', color=df['Revenue'].astype(str), barmode='group',
#                                title="Month vs Revenue", width=700, height=400)
#             st.plotly_chart(fig, use_container_width=True)

#     # ========== PREDICTIVE MODELING ==========
#     if 'Revenue' in df.columns:
#         st.markdown('<div class="section-title">🔮 TensorFlow Purchase Classifier</div>', unsafe_allow_html=True)

#         X = df.drop('Revenue', axis=1).copy()
#         y = df['Revenue']

#         if y.dtype == 'object':
#             y = LabelEncoder().fit_transform(y)

#         for col in X.select_dtypes(include=['object']).columns:
#             X[col] = LabelEncoder().fit_transform(X[col])

#         X = X.fillna(0)
#         X_scaled = StandardScaler().fit_transform(X)
#         X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

#         model = tf.keras.Sequential([
#             tf.keras.layers.Dense(64, activation='relu', input_shape=(X_train.shape[1],)),
#             tf.keras.layers.Dense(32, activation='relu'),
#             tf.keras.layers.Dense(1, activation='sigmoid')
#         ])
#         model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

#         with st.spinner("Training TensorFlow model..."):
#             model.fit(X_train, y_train, epochs=10, batch_size=16, verbose=0)

#         acc = model.evaluate(X_test, y_test, verbose=0)[1]
#         st.success(f"✅ Model Accuracy: {acc:.2%}")

#         y_pred = (model.predict(X_test) > 0.5).astype("int32")
#         report = classification_report(y_test, y_pred, output_dict=True)
#         st.dataframe(sanitize_dataframe(pd.DataFrame(report).transpose()))

#     # ========== TAKEAWAYS ==========
#     st.markdown('<div class="section-title">📋 Auto Insights</div>', unsafe_allow_html=True)
#     takeaways = []
#     if 'Revenue' in df.columns and 'VisitorType' in df.columns:
#         visitor_rates = df.groupby('VisitorType')['Revenue'].mean()
#         top = visitor_rates.idxmax()
#         takeaways.append(f"🔸 **{top}** visitors convert the most.")

#     if 'Month' in df.columns and 'Revenue' in df.columns:
#         month_rates = df.groupby('Month')['Revenue'].mean()
#         top_month = month_rates.idxmax()
#         takeaways.append(f"🔸 Purchases peak in **{top_month}**.")

#     if 'PageValues' in df.columns:
#         avg_val = df.groupby('Revenue')['PageValues'].mean()
#         takeaways.append(f"🔸 Buyers average **{avg_val.get(1, 0):.2f}** in page value.")

#     for tip in takeaways:
#         st.markdown(tip)

#     # ========== DOWNLOAD FINAL ==========
#     st.markdown('<div class="section-title">⬇️ Download Final Analyzed Data</div>', unsafe_allow_html=True)
#     st.download_button("Download CSV", data=sanitize_dataframe(df).to_csv(index=False).encode(), file_name="analyzed_data.csv")










# import streamlit as st
# import pandas as pd
# import numpy as np
# import plotly.express as px
# import plotly.graph_objects as go
# import seaborn as sns
# import matplotlib.pyplot as plt
# from sklearn.model_selection import train_test_split
# from sklearn.preprocessing import LabelEncoder, StandardScaler
# from sklearn.metrics import classification_report
# import tensorflow as tf
# from sqlalchemy import create_engine
# import pymysql
# import urllib.parse
# import requests

# # Streamlit setup
# st.set_page_config(page_title="Smart CSV Analyzer", layout="wide")
# st.markdown("""
#     <style>
#         .main {background-color: #f4f6f8;}
#         .css-1d391kg {padding: 2rem 1rem 1rem 1rem;}
#         h1, h2, h3, h4, h5, h6 {color: #31333f;}
#     </style>
# """, unsafe_allow_html=True)

# st.markdown("# 🧠 Smart CSV Analyzer")
# st.markdown("Analyze CSV files, URLs, or APIs with visual insights, behavior analysis, predictions, and database save options.")

# # File/URL upload section
# uploaded_file = st.file_uploader("📁 Upload a CSV file", type=["csv"])
# url_input = st.text_input("🌐 Or enter a public URL (CSV or JSON API)")
# df = None

# if uploaded_file:
#     df = pd.read_csv(uploaded_file)
#     st.success("✅ File uploaded successfully!")
# elif url_input:
#     try:
#         response = requests.get(url_input)
#         if response.status_code == 200:
#             content_type = response.headers.get("Content-Type", "")
#             if "text/csv" in content_type or url_input.endswith(".csv"):
#                 df = pd.read_csv(url_input)
#                 st.success("✅ CSV loaded from URL!")
#             elif "application/json" in content_type:
#                 data = response.json()
#                 df = pd.DataFrame(data)
#                 st.success("✅ JSON API loaded and converted to table!")
#             else:
#                 st.error("⚠️ Unsupported content type.")
#         else:
#             st.error(f"⚠️ Failed to fetch data. Status code: {response.status_code}")
#     except Exception as e:
#         st.error(f"⚠️ Error fetching data: {e}")

# # Main analysis pipeline
# if df is not None:
#     if 'Revenue' in df.columns and df['Revenue'].dtype == 'bool':
#         df['Revenue'] = df['Revenue'].astype(str)

#     st.header("📌 Dataset Overview")
#     st.metric("Rows", df.shape[0])
#     st.metric("Columns", df.shape[1])
#     st.dataframe(df.head())

#     # Quick info
#     valid_columns = [col for col in df.columns if not df[col].apply(lambda x: isinstance(x, dict)).any()]
#     quick_info = pd.DataFrame({
#         "Column": valid_columns,
#         "Data Type": df[valid_columns].dtypes.astype(str).values,
#         "Unique Values": df[valid_columns].nunique().values,
#         "Top Value": [str(df[col].mode().iloc[0]) if not df[col].mode().empty else 'N/A' for col in valid_columns],
#         "Missing Values": df[valid_columns].isnull().sum().values
#     })
#     st.dataframe(quick_info)

#     # Correlation heatmap
#     st.header("📊 Correlation Heatmap")
#     corr = df.corr(numeric_only=True)
#     fig = px.imshow(corr, text_auto=True, color_continuous_scale='RdBu_r', title="Correlation Matrix")
#     st.plotly_chart(fig, use_container_width=True)

#     # Skewness & kurtosis
#     numeric_cols = df.select_dtypes(include=np.number).columns
#     if len(numeric_cols) > 0:
#         stat_data = pd.DataFrame({
#             "Feature": numeric_cols,
#             "Skewness": [df[col].skew() for col in numeric_cols],
#             "Kurtosis": [df[col].kurtosis() for col in numeric_cols]
#         })
#         st.header("🧠 Skewness & Kurtosis")
#         st.dataframe(stat_data)

#     # Column-wise analysis
#     st.header("📈 Column-wise Visualization")
#     selected_col = st.selectbox("Choose a column to visualize", df.columns)

#     if df[selected_col].dtype == 'object':
#         fig = px.bar(df[selected_col].value_counts().reset_index().rename(columns={"index": selected_col, selected_col: "Count"}),
#                      x=selected_col, y="Count", title=f"Count of {selected_col}")
#         st.plotly_chart(fig)
#     else:
#         fig = px.histogram(df, x=selected_col, title=f"Distribution of {selected_col}", nbins=30)
#         st.plotly_chart(fig)
#         fig = px.box(df, y=selected_col, title=f"Boxplot of {selected_col}")
#         st.plotly_chart(fig)

#     # Revenue insights
#     if 'Revenue' in df.columns:
#         st.header("🎯 Revenue Insights")
#         col1, col2 = st.columns(2)

#         with col1:
#             if 'VisitorType' in df.columns:
#                 fig = px.histogram(df, x='VisitorType', color='Revenue', barmode='group', title="Visitor Type vs Revenue")
#                 st.plotly_chart(fig)

#         with col2:
#             if 'Month' in df.columns:
#                 fig = px.histogram(df, x='Month', color='Revenue', barmode='group', title="Month vs Revenue")
#                 st.plotly_chart(fig)

#         st.markdown("### 📌 Insights")
#         rev_conversion = df[df['Revenue'] == 'True'] if df['Revenue'].dtype == 'object' else df[df['Revenue'] == 1]
#         top_months = rev_conversion['Month'].value_counts().head(3).index.tolist() if 'Month' in df.columns else []
#         st.success(f"📈 Highest purchases occurred in: {', '.join(top_months)}" if top_months else "No month-wise data.")

#     # Predictive modeling
#     if 'Revenue' in df.columns:
#         st.header("🧠 Revenue Prediction using TensorFlow")
#         X = df.drop('Revenue', axis=1).copy()
#         y = df['Revenue']

#         if y.dtype == 'object':
#             y = LabelEncoder().fit_transform(y)

#         for col in X.select_dtypes(include=['object']).columns:
#             X[col] = LabelEncoder().fit_transform(X[col].astype(str))
#         X = X.fillna(0)

#         scaler = StandardScaler()
#         X_scaled = scaler.fit_transform(X)
#         X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

#         model = tf.keras.Sequential([
#             tf.keras.layers.Dense(64, activation='relu', input_shape=(X_train.shape[1],)),
#             tf.keras.layers.Dense(32, activation='relu'),
#             tf.keras.layers.Dense(1, activation='sigmoid')
#         ])

#         model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
#         with st.spinner("Training the model..."):
#             model.fit(X_train, y_train, epochs=10, batch_size=16, verbose=0)

#         acc = model.evaluate(X_test, y_test, verbose=0)[1]
#         st.success(f"✅ Model Accuracy: {acc:.2%}")
#         y_pred = (model.predict(X_test) > 0.5).astype("int32")
#         report = classification_report(y_test, y_pred, output_dict=True)
#         st.dataframe(pd.DataFrame(report).transpose())

#     # Download data button
#     st.markdown("### 📥 Download Cleaned Data")
#     csv = df.to_csv(index=False).encode('utf-8')
#     st.download_button("📥 Download Processed CSV", csv, "processed_data.csv", "text/csv")







# import streamlit as st
# import pandas as pd
# import numpy as np
# import seaborn as sns
# import matplotlib.pyplot as plt
# from sqlalchemy import create_engine
# import pymysql
# import urllib.parse
# import plotly.express as px

# # Streamlit setup
# st.set_page_config(page_title="📊 Smart CSV Analyzer", layout="wide")
# st.title("📊 Smart Customer Behavior Analyzer")
# st.markdown("""
# Welcome to the Smart Analyzer! This tool lets you:
# - Upload or fetch customer behavior data
# - Analyze trends and correlations
# - Predict purchase intent
# - Export insights to MySQL or CSV
# """)

# uploaded_file = st.file_uploader("📁 Upload a CSV file", type=["csv"])
# url_input = st.text_input("🌐 Or enter a public URL (CSV or JSON API)")
# df = None

# if uploaded_file:
#     df = pd.read_csv(uploaded_file)
#     st.success("✅ File uploaded successfully!")

# elif url_input:
#     try:
#         import requests
#         response = requests.get(url_input)
#         if response.status_code == 200:
#             content_type = response.headers.get("Content-Type", "")
#             if "text/csv" in content_type or url_input.endswith(".csv"):
#                 df = pd.read_csv(url_input)
#                 st.success("✅ CSV loaded from URL!")
#             elif "application/json" in content_type:
#                 data = response.json()
#                 df = pd.DataFrame(data)
#                 st.success("✅ JSON API loaded and converted to table!")
#             else:
#                 st.error("⚠️ Unsupported content type.")
#         else:
#             st.error(f"⚠️ Failed to fetch data. Status code: {response.status_code}")
#     except Exception as e:
#         st.error(f"⚠️ Error fetching data: {e}")

# if df is not None:
#     st.session_state["df"] = df
#     st.header("🔍 Dataset Overview")
#     col1, col2 = st.columns(2)
#     with col1:
#         st.metric("🧮 Rows", df.shape[0])
#     with col2:
#         st.metric("📊 Columns", df.shape[1])

#     st.markdown("### 🗂️ Column Names")
#     st.write(", ".join(df.columns))

#     # ---- Section: Missing Values ----
#     missing = df.isnull().sum()
#     missing = missing[missing > 0]
#     if not missing.empty:
#         st.markdown("### ⚠️ Missing Values")
#         st.dataframe(missing.reset_index().rename(columns={"index": "Column", 0: "Missing Count"}))
#     else:
#         st.markdown("### ✅ No Missing Values Found")

#     # ---- Section: Summary Statistics ----
#     st.header("📈 Summary Statistics")
#     st.dataframe(df.describe(include='all').transpose())

#     # ---- Section: Feature Quick Info ----
#     st.header("📌 Column-Wise Quick Stats")
#     valid_columns = [col for col in df.columns if not df[col].apply(lambda x: isinstance(x, dict)).any()]
#     quick_info = pd.DataFrame({
#         "Column": valid_columns,
#         "Data Type": df[valid_columns].dtypes.values,
#         "Unique Values": df[valid_columns].nunique().values,
#         "Top Value": [df[col].mode().iloc[0] if not df[col].mode().empty else 'N/A' for col in valid_columns],
#         "Missing Values": df[valid_columns].isnull().sum().values
#     })
#     st.dataframe(quick_info)

#     # ---- Section: Correlation Heatmap ----
#     st.header("🔥 Feature Correlation")
#     corr = df.corr(numeric_only=True)
#     fig = px.imshow(corr, text_auto=True, color_continuous_scale='RdBu_r', aspect="auto")
#     st.plotly_chart(fig, use_container_width=True)

#     # ---- Section: Statistical Shape ----
#     st.header("🧠 Skewness & Kurtosis")
#     numeric_cols = df.select_dtypes(include=np.number).columns
#     if len(numeric_cols) > 0:
#         stat_data = pd.DataFrame({
#             "Feature": numeric_cols,
#             "Skewness": [df[col].skew() for col in numeric_cols],
#             "Kurtosis": [df[col].kurtosis() for col in numeric_cols]
#         })
#         st.dataframe(stat_data)

#     # ---- Section: Column Exploration ----
#     st.header("📊 Column-wise Visualization")
#     selected_col = st.selectbox("Select a column to visualize", df.columns)

#     if df[selected_col].dtype == 'object':
#         st.subheader(f"🔸 Value Counts for '{selected_col}'")
#         fig = px.histogram(df, x=selected_col, color=selected_col)
#         st.plotly_chart(fig, use_container_width=True)
#     else:
#         st.subheader(f"🔹 Distribution of '{selected_col}'")
#         fig = px.histogram(df, x=selected_col, nbins=30, marginal="box", opacity=0.7)
#         st.plotly_chart(fig, use_container_width=True)

#     # ---- Section: Revenue-Based Insights (if available) ----
#     if 'Revenue' in df.columns:
#         st.header("🎯 Revenue-Based Behavioral Analysis")

#         col3, col4 = st.columns(2)
#         with col3:
#             if 'VisitorType' in df.columns:
#                 st.subheader("Visitor Type vs Revenue")
#                 fig = px.histogram(df, x='VisitorType', color='Revenue')
#                 st.plotly_chart(fig, use_container_width=True)

#         with col4:
#             if 'Month' in df.columns:
#                 st.subheader("Month vs Revenue")
#                 fig = px.histogram(df, x='Month', color='Revenue')
#                 st.plotly_chart(fig, use_container_width=True)

#     # ---- Section: Takeaways ----
#     df = st.session_state.get("df")
#     if df is not None:
#         st.subheader("📌 Top 3 Takeaways")
#         takeaways = []

#         if 'Revenue' in df.columns and 'VisitorType' in df.columns:
#             visitor_rates = df.groupby('VisitorType')['Revenue'].mean()
#             top = visitor_rates.idxmax()
#             takeaways.append(f"🔸 **{top}** visitors are most likely to purchase.")

#         if 'Month' in df.columns and 'Revenue' in df.columns:
#             month_rates = df.groupby('Month')['Revenue'].mean()
#             top_month = month_rates.idxmax()
#             takeaways.append(f"🔸 Most purchases happen in **{top_month}**.")

#         if 'PageValues' in df.columns:
#             avg_page_value = df.groupby('Revenue')['PageValues'].mean()
#             takeaways.append(f"🔸 Users who buy see **{avg_page_value.get(1, 0):.2f}** page value on average.")

#         for tip in takeaways:
#             st.markdown(tip)

#         def sanitize_dataframe(df):
#             return df.applymap(lambda x: str(x) if isinstance(x, dict) else x)

#         st.download_button("⬇️ Download Final Data", sanitize_dataframe(df).to_csv(index=False).encode(), "final_data.csv")

#     # ---- Section: Save to MySQL ----
#     st.header("🛠️ Save Data to MySQL")
#     save_to_db = st.checkbox("💾 Save uploaded CSV and insights to MySQL")

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

#                 # Save raw data
#                 df.to_sql(table, con=engine, index=False, if_exists='replace')

#                 # Save summary
#                 summary = df.describe(include='all').transpose().reset_index()
#                 summary.columns = ['Feature'] + list(summary.columns[1:])
#                 summary.to_sql(f"{table}_summary", con=engine, index=False, if_exists='replace')

#                 # Save missing values (only if any)
#                 missing = df.isnull().sum()
#                 missing = missing[missing > 0]
#                 if not missing.empty:
#                     mv = missing.reset_index()
#                     mv.columns = ['Column', 'MissingCount']
#                     mv.to_sql(f"{table}_missing", con=engine, index=False, if_exists='replace')

#                 # Save correlation matrix
#                 corr = df.corr(numeric_only=True)
#                 corr_long = corr.stack().reset_index()
#                 corr_long.columns = ['Feature1', 'Feature2', 'Correlation']
#                 corr_long.to_sql(f"{table}_correlation", con=engine, index=False, if_exists='replace')

#                 # Save stats
#                 numeric_cols = df.select_dtypes(include=np.number).columns
#                 if len(numeric_cols) > 0:
#                     stat_data = pd.DataFrame({
#                         "Feature": numeric_cols,
#                         "Skewness": [df[col].skew() for col in numeric_cols],
#                         "Kurtosis": [df[col].kurtosis() for col in numeric_cols]
#                     })
#                     stat_data.to_sql(f"{table}_stats", con=engine, index=False, if_exists='replace')

#                 # Save column overview
#                 valid_columns = [col for col in df.columns if not df[col].apply(lambda x: isinstance(x, dict)).any()]
#                 quick_info = pd.DataFrame({
#                     "Column": valid_columns,
#                     "Data Type": df[valid_columns].dtypes.values,
#                     "Unique Values": df[valid_columns].nunique().values,
#                     "Top Value": [df[col].mode().iloc[0] if not df[col].mode().empty else 'N/A' for col in valid_columns],
#                     "Missing Values": df[valid_columns].isnull().sum().values
#                 })
#                 quick_info.to_sql(f"{table}_features", con=engine, index=False, if_exists='replace')

#                 st.success("✅ Data and insights saved to MySQL successfully!")

#             except Exception as e:
#                 st.error(f"❌ MySQL Error: {e}")







# import streamlit as st
# import pandas as pd
# import numpy as np
# import seaborn as sns
# import matplotlib.pyplot as plt
# from sqlalchemy import create_engine
# import pymysql
# import urllib.parse
# import plotly.express as px
# from sklearn.model_selection import train_test_split
# from sklearn.preprocessing import LabelEncoder, StandardScaler
# from sklearn.metrics import classification_report
# import tensorflow as tf

# # Streamlit setup
# st.set_page_config(page_title="📊 Smart CSV Analyzer", layout="wide")
# st.title("📊 Smart Customer Behavior Analyzer")
# st.markdown("""
# Welcome to the Smart Analyzer! This tool lets you:
# - Upload or fetch structured datasets (CSV or API)
# - Analyze trends and correlations
# - Predict outcomes (only for binary targets like 'Revenue')
# - Export insights to MySQL or CSV
# """)

# uploaded_file = st.file_uploader("📁 Upload a CSV file", type=["csv"])
# url_input = st.text_input("🌐 Or enter a public URL (CSV or JSON API)")
# df = None

# if uploaded_file:
#     df = pd.read_csv(uploaded_file)
#     st.success("✅ File uploaded successfully!")
# elif url_input:
#     try:
#         import requests
#         response = requests.get(url_input)
#         if response.status_code == 200:
#             content_type = response.headers.get("Content-Type", "")
#             if "text/csv" in content_type or url_input.endswith(".csv"):
#                 df = pd.read_csv(url_input)
#                 st.success("✅ CSV loaded from URL!")
#             elif "application/json" in content_type:
#                 data = response.json()
#                 df = pd.DataFrame(data)
#                 st.success("✅ JSON API loaded and converted to table!")
#             else:
#                 st.error("⚠️ Unsupported content type.")
#         else:
#             st.error(f"⚠️ Failed to fetch data. Status code: {response.status_code}")
#     except Exception as e:
#         st.error(f"⚠️ Error fetching data: {e}")

# if df is not None:
#     st.session_state["df"] = df
#     st.header("🔍 Dataset Overview")
#     col1, col2 = st.columns(2)
#     with col1:
#         st.metric("🧮 Rows", df.shape[0])
#     with col2:
#         st.metric("📊 Columns", df.shape[1])

#     st.markdown("### 🗂️ Column Names")
#     st.write(", ".join(df.columns))

#     # ---- Section: Missing Values ----
#     missing = df.isnull().sum()
#     missing = missing[missing > 0]
#     if not missing.empty:
#         st.markdown("### ⚠️ Missing Values")
#         st.dataframe(missing.reset_index().rename(columns={"index": "Column", 0: "Missing Count"}))
#     else:
#         st.markdown("### ✅ No Missing Values Found")

#     # ---- Section: Summary Statistics ----
#     st.header("📈 Summary Statistics")
#     st.dataframe(df.describe(include='all').transpose())

#     # ---- Section: Feature Quick Info ----
#     st.header("📌 Column-Wise Quick Stats")
#     valid_columns = [col for col in df.columns if not df[col].apply(lambda x: isinstance(x, dict)).any()]
#     quick_info = pd.DataFrame({
#         "Column": valid_columns,
#         "Data Type": df[valid_columns].dtypes.values,
#         "Unique Values": df[valid_columns].nunique().values,
#         "Top Value": [df[col].mode().iloc[0] if not df[col].mode().empty else 'N/A' for col in valid_columns],
#         "Missing Values": df[valid_columns].isnull().sum().values
#     })
#     st.dataframe(quick_info)

#     # ---- Section: Correlation Heatmap ----
#     st.header("🔥 Feature Correlation")
#     corr = df.corr(numeric_only=True)
#     if not corr.empty:
#         fig = px.imshow(corr, text_auto=True, color_continuous_scale='RdBu_r', aspect="auto")
#         st.plotly_chart(fig, use_container_width=True)

#     # ---- Section: Statistical Shape ----
#     st.header("🧠 Skewness & Kurtosis")
#     numeric_cols = df.select_dtypes(include=np.number).columns
#     if len(numeric_cols) > 0:
#         stat_data = pd.DataFrame({
#             "Feature": numeric_cols,
#             "Skewness": [df[col].skew() for col in numeric_cols],
#             "Kurtosis": [df[col].kurtosis() for col in numeric_cols]
#         })
#         st.dataframe(stat_data)

#     # ---- Section: Column Exploration ----
#     st.header("📊 Column-wise Visualization")
#     selected_col = st.selectbox("Select a column to visualize", df.columns)

#     if df[selected_col].dtype == 'object':
#         st.subheader(f"🔸 Value Counts for '{selected_col}'")
#         fig = px.histogram(df, x=selected_col, color=selected_col)
#         st.plotly_chart(fig, use_container_width=True)
#     else:
#         st.subheader(f"🔹 Distribution of '{selected_col}'")
#         fig = px.histogram(df, x=selected_col, nbins=30, marginal="box", opacity=0.7)
#         st.plotly_chart(fig, use_container_width=True)

#     # ---- Section: Revenue-Based Insights ----
#     if 'Revenue' in df.columns:
#         st.header("🎯 Revenue-Based Behavioral Analysis")
#         col3, col4 = st.columns(2)
#         with col3:
#             if 'VisitorType' in df.columns:
#                 st.subheader("Visitor Type vs Revenue")
#                 fig = px.histogram(df, x='VisitorType', color='Revenue')
#                 st.plotly_chart(fig, use_container_width=True)
#         with col4:
#             if 'Month' in df.columns:
#                 st.subheader("Month vs Revenue")
#                 fig = px.histogram(df, x='Month', color='Revenue')
#                 st.plotly_chart(fig, use_container_width=True)

#         # ---- Smart Takeaways ----
#         st.subheader("📌 Smart Takeaways")
#         takeaways = []
#         corr_rev = df.corr(numeric_only=True)['Revenue'].drop('Revenue', errors='ignore').sort_values(ascending=False)
#         if not corr_rev.empty:
#             top_feat = corr_rev.idxmax()
#             takeaways.append(f"🔍 Strongest predictor of Revenue: **{top_feat}** (correlation: {corr_rev.max():.2f})")

#         if 'BounceRates' in df.columns:
#             avg_bounce = df.groupby('Revenue')['BounceRates'].mean()
#             if 1 in avg_bounce and 0 in avg_bounce:
#                 diff = avg_bounce[0] - avg_bounce[1]
#                 takeaways.append(f"⚠️ Buyers have {diff:.2f} lower average bounce rate.")

#         if 'VisitorType' in df.columns:
#             visitor_conv = df.groupby('VisitorType')['Revenue'].mean()
#             if not visitor_conv.empty:
#                 best_group = visitor_conv.idxmax()
#                 takeaways.append(f"🔁 **{best_group}** visitors convert the most.")

#         for tip in takeaways:
#             st.markdown(tip)

#     # ---- Prediction Module ----
#     if 'Revenue' in df.columns and df['Revenue'].nunique() == 2 and df.shape[0] > 100:
#         st.header("🔮 Predictive Modeling with TensorFlow")
#         X = df.drop('Revenue', axis=1).copy()
#         y = df['Revenue']

#         if y.dtype == 'object':
#             y = LabelEncoder().fit_transform(y)

#         for col in X.select_dtypes(include=['object']).columns:
#             X[col] = LabelEncoder().fit_transform(X[col])

#         X = X.fillna(0)
#         scaler = StandardScaler()
#         X_scaled = scaler.fit_transform(X)

#         X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

#         model = tf.keras.Sequential([
#             tf.keras.layers.Dense(64, activation='relu', input_shape=(X_train.shape[1],)),
#             tf.keras.layers.Dense(32, activation='relu'),
#             tf.keras.layers.Dense(1, activation='sigmoid')
#         ])

#         model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

#         with st.spinner("Training model..."):
#             model.fit(X_train, y_train, epochs=10, batch_size=16, verbose=0)

#         acc = model.evaluate(X_test, y_test, verbose=0)[1]
#         st.success(f"✅ Model trained with **{acc:.2%}** accuracy")

#         preds = (model.predict(X_test) > 0.5).astype("int32")
#         report = classification_report(y_test, preds, output_dict=True)
#         st.dataframe(pd.DataFrame(report).transpose())

#     # ---- Export Section ----
#     def sanitize_dataframe(df):
#         return df.applymap(lambda x: str(x) if isinstance(x, dict) else x)

#     st.download_button("⬇️ Download Final Data", sanitize_dataframe(df).to_csv(index=False).encode(), "final_data.csv")






# import streamlit as st
# import pandas as pd
# import numpy as np
# import plotly.express as px
# import requests
# import urllib.parse
# import pymysql
# from sqlalchemy import create_engine

# st.set_page_config(page_title="📊 Smart CSV Analyzer", layout="wide")

# st.markdown("""
# <style>
# @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');

# .hero {
#   animation: fadeInUp 1s ease-out;
# }

# @keyframes fadeInUp {
#   from {
#     opacity: 0;
#     transform: translateY(40px);
#   }
#   to {
#     opacity: 1;
#     transform: translateY(0);
#   }
# }

# .hero {
#     background: linear-gradient(to right, rgba(0,0,0,0.65), rgba(0,0,0,0.4)),
#                 url('https://images.unsplash.com/photo-1605792657660-596af9009e82?fit=crop&w=1470&q=80');
#     background-size: cover;
#     background-position: center;
#     color: white;
#     padding: 60px 60px;
#     border-radius: 18px;
#     margin-bottom: 2rem;
#     box-shadow: 0 10px 30px rgba(0,0,0,0.4);
#     font-family: 'Roboto', sans-serif;
# }

# .hero h1 {
#     font-size: 46px;
#     font-weight: 700;
#     margin-bottom: 24px;
# }

# .hero p {
#     font-size: 22px;
#     margin-bottom: 24px;
#     line-height: 1.6;
# }

# .hero ul {
#     font-size: 19px;
#     list-style: none;
#     padding-left: 0;
# }

# .hero ul li {
#     margin-bottom: 14px;
#     display: flex;
#     align-items: center;
# }

# .hero ul li::before {
#     margin-right: 12px;
#     font-size: 20px;
# }

# .cta-button {
#   display: inline-block;
#   background: linear-gradient(to right, #00c6ff, #0072ff);
#   color: white;
#   font-size: 18px;
#   padding: 12px 24px;
#   border-radius: 12px;
#   text-decoration: none;
#   margin-top: 20px;
#   box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
#   transition: 0.3s ease;
# }
# .cta-button:hover {
#   transform: scale(1.05);
# }

# </style>

# <div class="hero">
#     <h1>Welcome to the Smart Analyzer</h1>
#     <p>This smart tool helps you analyze and export data quickly & efficiently:</p>
#     <ul>
#         <ul class="text-left space-y-2 text-lg sm:text-xl">
#         <li>📂 Upload your CSV or Excel files</li>
#         <li>🧹 Handle missing values</li>
#         <li>📉 Detect outliers</li>
#         <li>📊 Analyze trends</li>
#         <li>🛠️ Export cleaned data to MySQL</li>
#     </ul>
# </div>
# """, unsafe_allow_html=True)

# # st.set_page_config(page_title="📊 Smart CSV Analyzer", layout="wide")

# # # Create the hero (intro) section with background image and gradient overlay.
# # st.markdown("""
# # <style>
# # .hero {
# #     background: linear-gradient(to right, rgba(31,78,121,0.85), rgba(0,172,193,0.75)),
# #                 url('https://images.unsplash.com/photo-1519389950473-47ba0277781c?fit=crop&w=1350&q=80');
# #     background-size: cover;
# #     background-position: center;
# #     color: white;
# #     padding: 80px 40px;
# #     border-radius: 18px;
# #     margin-bottom: 2rem;
# #     box-shadow: 0 10px 30px rgba(0,0,0,0.2);
# #     font-family: 'Segoe UI', sans-serif;
# #     text-align: center;
# # }
# # .hero h1 {
# #     font-size: 42px;
# #     font-weight: 700;
# #     margin-bottom: 20px;
# # }
# # .hero p {
# #     font-size: 22px;
# #     margin-bottom: 20px;
# # }
# # .hero ul {
# #     font-size: 20px;
# #     margin: 0;
# #     padding-left: 0;
# #     list-style: none;
# #     text-align: left;
# #     display: inline-block;
# # }
# # .hero ul li {
# #     margin: 10px 0;
# # }
# # .hero ul li::before {
# #     content: "🔹 ";
# #     margin-right: 8px;
# # }
# # </style>

# # <div class="hero">
# #     <h1>Welcome to the Smart Analyzer!</h1>
# #     <p>This tool helps you:</p>
# #     <ul>
# #         <li>📁 Upload or fetch customer-related datasets (CSV / JSON API)</li>
# #         <li>📊 Explore trends, correlations & missing data</li>
# #         <li>🔍 View smart summaries (if key columns like Revenue, VisitorType exist)</li>
# #         <li>💾 Export final data or insights to MySQL</li>
# #     </ul>
# # </div>
# # """, unsafe_allow_html=True)

# # -------------- FILE OR URL INPUT -------------------
# uploaded_file = st.file_uploader("📁 Upload a CSV file", type=["csv"])
# url_input = st.text_input("🌐 Or enter a public URL (CSV or JSON API)")
# df = None

# if uploaded_file:
#     df = pd.read_csv(uploaded_file)
#     st.success("✅ File uploaded successfully!")

# elif url_input:
#     try:
#         response = requests.get(url_input)
#         if response.status_code == 200:
#             content_type = response.headers.get("Content-Type", "")
#             if "text/csv" in content_type or url_input.endswith(".csv"):
#                 df = pd.read_csv(url_input)
#                 st.success("✅ CSV loaded from URL!")
#             elif "application/json" in content_type:
#                 data = response.json()
#                 df = pd.DataFrame(data)
#                 st.success("✅ JSON API loaded and converted to table!")
#             else:
#                 st.error("⚠️ Unsupported content type.")
#         else:
#             st.error(f"⚠️ Failed to fetch data. Status code: {response.status_code}")
#     except Exception as e:
#         st.error(f"⚠️ Error fetching data: {e}")

# # ------------------- MAIN ANALYSIS -------------------
# if df is not None:
#     st.session_state["df"] = df

#     st.header("🔍 Dataset Overview")
#     col1, col2 = st.columns(2)
#     with col1:
#         st.metric("🧮 Rows", df.shape[0])
#     with col2:
#         st.metric("📊 Columns", df.shape[1])

#     st.markdown("### 🗂️ Column Names")
#     st.code(", ".join(df.columns))

#     # -------- MISSING VALUES --------
#     missing = df.isnull().sum()
#     missing = missing[missing > 0]
#     st.header("⚠️ Missing Values")
#     if not missing.empty:
#         st.dataframe(missing.reset_index().rename(columns={"index": "Column", 0: "Missing Count"}))
#     else:
#         st.success("✅ No Missing Values Found")

#     # -------- SUMMARY STATS --------
#     st.header("📈 Summary Statistics")
#     st.dataframe(df.describe(include='all').transpose())

#     # -------- COLUMN STATS --------
#     st.header("📌 Column-Wise Quick Stats")
#     valid_columns = [col for col in df.columns if not df[col].apply(lambda x: isinstance(x, dict)).any()]
#     quick_info = pd.DataFrame({
#         "Column": valid_columns,
#         "Data Type": df[valid_columns].dtypes.values,
#         "Unique Values": df[valid_columns].nunique().values,
#         "Top Value": [df[col].mode().iloc[0] if not df[col].mode().empty else 'N/A' for col in valid_columns],
#         "Missing Values": df[valid_columns].isnull().sum().values
#     })
#     st.dataframe(quick_info)

#     # -------- CORRELATION --------
#     st.header("🔥 Feature Correlation (Numerical Only)")
#     corr = df.corr(numeric_only=True)
#     if not corr.empty:
#         fig = px.imshow(corr, text_auto=True, color_continuous_scale='RdBu_r', aspect="auto")
#         st.plotly_chart(fig, use_container_width=True)
#     else:
#         st.info("⚠️ No numeric features available for correlation.")

#     # -------- SHAPE STATS --------
#     st.header("🧠 Skewness & Kurtosis")
#     numeric_cols = df.select_dtypes(include=np.number).columns
#     if len(numeric_cols) > 0:
#         stat_data = pd.DataFrame({
#             "Feature": numeric_cols,
#             "Skewness": [df[col].skew() for col in numeric_cols],
#             "Kurtosis": [df[col].kurtosis() for col in numeric_cols]
#         })
#         st.dataframe(stat_data)

#     # -------- COLUMN-WISE VISUALS --------
#     st.header("📊 Column-wise Visualization")
#     selected_col = st.selectbox("Select a column to visualize", df.columns)

#     if df[selected_col].dtype == 'object':
#         st.subheader(f"🔸 Value Counts for '{selected_col}'")
#         fig = px.histogram(df, x=selected_col, color=selected_col)
#         st.plotly_chart(fig, use_container_width=True)
#     else:
#         st.subheader(f"🔹 Distribution of '{selected_col}'")
#         fig = px.histogram(df, x=selected_col, nbins=30, marginal="box", opacity=0.7)
#         st.plotly_chart(fig, use_container_width=True)

#     # -------- REVENUE BASED INSIGHTS --------
#     if 'Revenue' in df.columns:
#         st.header("🎯 Revenue-Based Behavioral Analysis")

#         col3, col4 = st.columns(2)
#         with col3:
#             if 'VisitorType' in df.columns:
#                 st.subheader("Visitor Type vs Revenue")
#                 fig = px.histogram(df, x='VisitorType', color='Revenue')
#                 st.plotly_chart(fig, use_container_width=True)

#         with col4:
#             if 'Month' in df.columns:
#                 st.subheader("Month vs Revenue")
#                 fig = px.histogram(df, x='Month', color='Revenue')
#                 st.plotly_chart(fig, use_container_width=True)

#         # -------- TAKEAWAYS --------
#         st.subheader("📌 Takeaways")
#         takeaways = []

#         if 'Revenue' in df.columns and 'VisitorType' in df.columns:
#             visitor_rates = df.groupby('VisitorType')['Revenue'].mean()
#             top = visitor_rates.idxmax()
#             takeaways.append(f"🔸 **{top}** visitors are most likely to purchase.")

#         if 'Month' in df.columns and 'Revenue' in df.columns:
#             month_rates = df.groupby('Month')['Revenue'].mean()
#             top_month = month_rates.idxmax()
#             takeaways.append(f"🔸 Most purchases happen in **{top_month}**.")

#         if 'PageValues' in df.columns and 'Revenue' in df.columns:
#             avg_page_value = df.groupby('Revenue')['PageValues'].mean()
#             takeaways.append(f"🔸 Buyers see **{avg_page_value.get(1, 0):.2f}** page value on average.")

#         if takeaways:
#             for tip in takeaways:
#                 st.markdown(tip)
#         else:
#             st.info("ℹ️ Not enough data to generate meaningful insights.")



#     # -------- DOWNLOAD FINAL FILE --------
#     def sanitize_dataframe(df):
#         return df.applymap(lambda x: str(x) if isinstance(x, dict) else x)

#     st.download_button(
#         label="⬇️ Download Final Data",
#         data=sanitize_dataframe(df).to_csv(index=False).encode(),
#         file_name="final_data.csv"
#     )

#     # -------- SAVE TO MYSQL --------
#     st.header("🛠️ Save Data to MySQL")
#     save_to_db = st.checkbox("💾 Save uploaded CSV and insights to MySQL")

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






# import streamlit as st
# import pandas as pd
# import numpy as np
# import plotly.express as px
# from scipy.stats import zscore

# st.set_page_config(page_title="📊 Smart Auto EDA", layout="wide")

# st.title("📊 Smart Auto EDA Tool")

# uploaded_file = st.file_uploader("📁 Upload a CSV file", type=["csv"])
# url_input = st.text_input("🌐 Or enter a public URL (CSV or JSON API)")
# df = None

# if uploaded_file:
#     df = pd.read_csv(uploaded_file)
#     st.success("✅ File uploaded successfully!")

# elif url_input:
#     try:
#         import requests
#         response = requests.get(url_input)
#         if response.status_code == 200:
#             content_type = response.headers.get("Content-Type", "")
#             if "text/csv" in content_type or url_input.endswith(".csv"):
#                 df = pd.read_csv(url_input)
#                 st.success("✅ CSV loaded from URL!")
#             elif "application/json" in content_type:
#                 data = response.json()
#                 df = pd.DataFrame(data)
#                 st.success("✅ JSON API loaded and converted to table!")
#             else:
#                 st.error("⚠️ Unsupported content type.")
#         else:
#             st.error(f"⚠️ Failed to fetch data. Status code: {response.status_code}")
#     except Exception as e:
#         st.error(f"⚠️ Error fetching data: {e}")

# # ------------------- AUTO EDA -------------------
# if df is not None:
#     st.subheader("🔍 Dataset Overview")
#     st.dataframe(df.head())

#     st.subheader("🔎 Auto EDA Summary")

#     # Detect Column Types
#     numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
#     categorical_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
#     datetime_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()

#     for col in df.columns:
#         if col not in datetime_cols:
#             try:
#                 df[col] = pd.to_datetime(df[col])
#                 datetime_cols.append(col)
#             except:
#                 continue

#     # NUMERICAL ANALYSIS
#     if numeric_cols:
#         st.markdown("### 📊 Numerical Columns")
#         st.dataframe(df[numeric_cols].describe().transpose())

#         for col in numeric_cols:
#             st.markdown(f"#### Histogram of `{col}`")
#             fig = px.histogram(df, x=col, nbins=30)
#             st.plotly_chart(fig, use_container_width=True)

#     # CATEGORICAL ANALYSIS
#     if categorical_cols:
#         st.markdown("### 🔤 Categorical Columns")
#         for col in categorical_cols:
#             if df[col].nunique() < 25:
#                 st.markdown(f"#### Value Counts of `{col}`")
#                 st.dataframe(df[col].value_counts().reset_index().rename(columns={'index': col, col: 'Count'}))
#                 fig = px.bar(df[col].value_counts().reset_index(), x='index', y=col)
#                 st.plotly_chart(fig, use_container_width=True)

#     # DATETIME ANALYSIS
#     if datetime_cols:
#         st.markdown("### ⏱️ Datetime Columns")
#         for col in datetime_cols:
#             st.markdown(f"#### Timeline for `{col}`")
#             fig = px.histogram(df, x=col)
#             st.plotly_chart(fig, use_container_width=True)

#     # CORRELATION
#     if len(numeric_cols) >= 2:
#         st.markdown("### 📈 Correlation Matrix")
#         corr = df[numeric_cols].corr()
#         fig = px.imshow(corr, text_auto=True, color_continuous_scale='RdBu_r')
#         st.plotly_chart(fig, use_container_width=True)

#     # OUTLIER DETECTION
#     st.markdown("### ⚠️ Outlier Detection (Z-Score > 3)")
#     outliers = {}
#     for col in numeric_cols:
#         try:
#             z = np.abs(zscore(df[col].dropna()))
#             outliers[col] = (z > 3).sum()
#         except:
#             continue
#     st.dataframe(pd.DataFrame.from_dict(outliers, orient='index', columns=["Outlier Count"]))

#     # GROUPED INSIGHTS
#     st.markdown("### 📌 Grouped Aggregations")
#     for num in numeric_cols:
#         for cat in categorical_cols:
#             if df[cat].nunique() < 10:
#                 agg = df.groupby(cat)[num].mean().reset_index()
#                 st.markdown(f"##### Avg `{num}` grouped by `{cat}`")
#                 fig = px.bar(agg, x=cat, y=num)
#                 st.plotly_chart(fig, use_container_width=True)






# import streamlit as st
# import pandas as pd
# import numpy as np
# import plotly.express as px
# from scipy.stats import zscore
# import requests

# st.set_page_config(page_title="📊 Smart Auto EDA", layout="wide")

# # ------------------- DARK THEME + FONTS -------------------
# st.markdown("""
# <style>
# body {
#     background-color: #0f1116;
#     color: #f1f1f1;
# }
# [data-testid="stHeader"] {
#     background-color: #0f1116;
# }
# h1, h2, h3, h4, h5 {
#     color: #00b8f4;
# }
# div[data-testid="metric-container"] {
#     background: #1a1a1a;
#     border-radius: 10px;
#     padding: 10px;
#     border: 1px solid #333;
# }
# .stDataFrame {
#     background-color: #1c1e22;
# }
# </style>
# """, unsafe_allow_html=True)

# st.title("📊 Smart Auto EDA Tool")

# # ------------------- FILE OR URL UPLOAD -------------------
# uploaded_file = st.file_uploader("📁 Upload a CSV file", type=["csv"])
# url_input = st.text_input("🌐 Or enter a public URL (CSV or JSON API)")
# df = None

# if uploaded_file:
#     df = pd.read_csv(uploaded_file)
#     st.success("✅ File uploaded successfully!")

# elif url_input:
#     try:
#         response = requests.get(url_input)
#         if response.status_code == 200:
#             content_type = response.headers.get("Content-Type", "")
#             if "text/csv" in content_type or url_input.endswith(".csv"):
#                 df = pd.read_csv(url_input)
#                 st.success("✅ CSV loaded from URL!")
#             elif "application/json" in content_type:
#                 data = response.json()
#                 df = pd.DataFrame(data)
#                 st.success("✅ JSON API loaded and converted to table!")
#             else:
#                 st.error("⚠️ Unsupported content type.")
#         else:
#             st.error(f"⚠️ Failed to fetch data. Status code: {response.status_code}")
#     except Exception as e:
#         st.error(f"⚠️ Error fetching data: {e}")

# # ------------------- AUTO EDA -------------------
# if df is not None:
#     st.subheader("🔍 Dataset Overview")
#     st.dataframe(df.head())

#     st.subheader("🔎 Auto EDA Summary")

#     # Detect Column Types
#     numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
#     categorical_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
#     datetime_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()

#     for col in df.columns:
#         if col not in datetime_cols:
#             try:
#                 df[col] = pd.to_datetime(df[col])
#                 datetime_cols.append(col)
#             except:
#                 continue

#     # ======== NUMERIC SUMMARY & VISUALS ========
#     if numeric_cols:
#         st.markdown("### 📊 Numerical Columns Summary")
#         st.dataframe(df[numeric_cols].describe().transpose())

#         for col in numeric_cols:
#             col1, col2 = st.columns([2, 1])
#             with col1:
#                 fig = px.histogram(df, x=col, nbins=40, marginal="box", title=f"Distribution of {col}")
#                 fig.update_layout(paper_bgcolor='#0f1116', plot_bgcolor='#0f1116', font_color="#f1f1f1")
#                 st.plotly_chart(fig, use_container_width=True)
#             with col2:
#                 # st.metric("Mean", round(df[col].mean(), 2))
#                 mean_time = df[col].mean()
#                 st.metric("Mean", mean_time.strftime('%Y-%m-%d %H:%M:%S'))
#                 # st.metric("Std Dev", round(df[col].std(), 2))
#                 std_dev = df[col].std()
#                 days = std_dev.days
#                 hours, remainder = divmod(std_dev.seconds, 3600)
#                 minutes, _ = divmod(remainder, 60)
#                 st.metric("Std Dev", f"{days}d {hours}h {minutes}m")
#                 if pd.api.types.is_numeric_dtype(df[col]):
#                     st.metric("Skew", round(df[col].skew(), 2))
#                 else:
#                     st.metric("Skew", "N/A")


#     # ======== CATEGORICAL SUMMARY & VISUALS ========
#     if categorical_cols:
#         st.markdown("### 🔤 Categorical Columns Overview")
#         for col in categorical_cols:
#             if df[col].nunique() <= 15:
#                 st.markdown(f"**{col}** - Unique Values: {df[col].nunique()}")
#                 val_counts = df[col].value_counts().reset_index()
#                 val_counts.columns = [col, "Count"]
#                 fig = px.bar(val_counts, x=col, y="Count", title=f"Value Counts of {col}")
#                 fig.update_layout(paper_bgcolor='#0f1116', plot_bgcolor='#0f1116', font_color="#f1f1f1")
#                 st.plotly_chart(fig, use_container_width=True)
#             else:
#                 st.info(f"⚠️ Skipping `{col}` — too many unique values: {df[col].nunique()}")

#     # ======== DATETIME ANALYSIS ========
#     if datetime_cols:
#         st.markdown("### ⏱️ Datetime Columns")
#         for col in datetime_cols:
#             st.markdown(f"**Timeline for `{col}`**")
#             fig = px.histogram(df, x=col)
#             fig.update_layout(paper_bgcolor='#0f1116', plot_bgcolor='#0f1116', font_color="#f1f1f1")
#             st.plotly_chart(fig, use_container_width=True)

#     # ======== CORRELATION MATRIX ========
#     if len(numeric_cols) >= 2:
#         st.markdown("### 📈 Correlation Matrix")
#         corr = df[numeric_cols].corr()
#         fig = px.imshow(corr, text_auto=True, color_continuous_scale='RdBu_r')
#         fig.update_layout(paper_bgcolor='#0f1116', font_color="#f1f1f1")
#         st.plotly_chart(fig, use_container_width=True)

#     # ======== OUTLIER DETECTION ========
#     st.markdown("### ⚠️ Outlier Detection (Z-Score > 3)")
#     outliers = {}
#     for col in numeric_cols:
#         try:
#             z = np.abs(zscore(df[col].dropna()))
#             outliers[col] = int((z > 3).sum())
#         except:
#             continue
#     out_df = pd.DataFrame.from_dict(outliers, orient='index', columns=["Outlier Count"])
#     st.dataframe(out_df)

#     # ======== GROUPED INSIGHTS ========
#     st.markdown("### 📌 Grouped Insights")
#     for num in numeric_cols:
#         for cat in categorical_cols:
#             if df[cat].nunique() <= 10:
#                 st.markdown(f"**Average of `{num}` grouped by `{cat}`**")
#                 agg = df.groupby(cat)[num].mean().reset_index()
#                 fig = px.bar(agg, x=cat, y=num)
#                 fig.update_layout(paper_bgcolor='#0f1116', font_color="#f1f1f1")
#                 st.plotly_chart(fig, use_container_width=True)

