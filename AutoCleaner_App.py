import streamlit as st
import pandas as pd
import re
from datetime import datetime

def clean_column_names(df):
    df.columns = [col.strip().title().replace(" ", "_") for col in df.columns]
    return df

def remove_duplicates(df):
    return df.drop_duplicates(keep='first')

def clean_text_columns(df):
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].astype(str).str.strip().str.lower()
        df[col] = df[col].apply(lambda x: re.sub(r'[^a-z0-9\s.,/-]', '', str(x)))
        if 'name' in col.lower():
            df[col] = df[col].apply(lambda x: ' '.join([word.capitalize() for word in x.split()]))
        if 'remarks' in col.lower():
            df[col] = df[col].apply(lambda x: x.replace('#', ''))
    return df

def roman_to_int(s):
    roman_map = {'i': 1, 'v': 5, 'x': 10, 'l': 50, 'c': 100, 'd': 500, 'm': 1000}
    s = s.lower()
    total = 0
    prev = 0
    for char in reversed(s):
        if roman_map.get(char, 0) < prev:
            total -= roman_map.get(char, 0)
        else:
            total += roman_map.get(char, 0)
        prev = roman_map.get(char, 0)
    return total

def normalize_salary_column(df):
    for col in df.columns:
        if 'salary' in col.lower():
            def parse_salary(val):
                val = str(val).lower().replace('$', '').replace(',', '').strip()
                if re.fullmatch(r'[ivxlcdm]+', val):
                    try:
                        return roman_to_int(val)
                    except:
                        return None
                if 'k' in val:
                    try:
                        return float(val.replace('k', '')) * 1000
                    except:
                        return None
                try:
                    return float(re.sub(r'[^\d.]', '', val))
                except:
                    return None
            df[col] = df[col].apply(parse_salary)
    return df

def normalize_age_column(df):
    text_to_num = {'thirty': '30', 'twenty two': '22', 'twenty': '20', 'forty': '40', 'none': None}
    for col in df.columns:
        if 'age' in col.lower():
            df[col] = df[col].replace(text_to_num)
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def parse_date_columns(df):
    known_formats = [
        "%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d",
        "%d-%b-%Y", "%d %B %Y", "%B %d, %Y", "%b %d, %Y"
    ]
    for col in df.columns:
        if df[col].dtype == 'object' or df[col].dtype == 'string':
            cleaned_col = []
            for val in df[col]:
                parsed = None
                for fmt in known_formats:
                    try:
                        parsed = datetime.strptime(str(val).strip(), fmt)
                        break
                    except:
                        continue
                if not parsed:
                    try:
                        parsed = pd.to_datetime(val, errors='coerce')
                    except:
                        parsed = None
                if pd.isna(parsed):
                    cleaned_col.append(None)
                else:
                    cleaned_col.append(parsed.strftime('%Y-%m-%d'))
            if any(cleaned_col):
                df[col] = cleaned_col
    return df

def handle_missing_values(df, threshold=0.4):
    for col in df.columns:
        if df[col].isnull().mean() <= threshold:
            if df[col].dtype == 'object':
                df[col].fillna(df[col].mode().iloc[0], inplace=True)
            else:
                df[col].fillna(df[col].median(), inplace=True)
    return df

def generate_cleaning_report(df_before, df_after):
    return {
        "Rows Before": df_before.shape[0],
        "Rows After": df_after.shape[0],
        "Columns Before": df_before.shape[1],
        "Columns After": df_after.shape[1]
    }

def auto_clean(df):
    df_before = df.copy()
    df = clean_column_names(df)
    df = remove_duplicates(df)
    df = clean_text_columns(df)
    df = normalize_salary_column(df)
    df = normalize_age_column(df)
    df = parse_date_columns(df)
    df = handle_missing_values(df)
    report = generate_cleaning_report(df_before, df)
    return df, report

def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

# Streamlit App Starts Here
st.set_page_config(page_title="Auto Data Cleaner", layout="wide")
st.title("🧼 Auto Data Cleaning Web App")

uploaded_file = st.file_uploader("Upload your CSV or Excel file", type=["csv", "xlsx"])
if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # 🔍 Show Original Raw Data
    st.subheader("🔍 Original Data Preview")
    st.dataframe(df.head())

    # ✅ Clean the data
    cleaned_df, report = auto_clean(df)

    # ✅ Show Cleaned Output
    st.subheader("✅ Cleaned Data Preview")
    st.dataframe(cleaned_df.head())

    # 📊 Summary Report
    st.subheader("📊 Cleaning Summary")
    st.json(report)

    # ⬇️ Download Button
    st.download_button(
        label="⬇️ Download Cleaned CSV",
        data=convert_df_to_csv(cleaned_df),
        file_name="cleaned_data.csv",
        mime="text/csv"
    )





# cd C:\Users\HP\Desktop\Auto Cleaner

# venv\scripts\activate

# streamlit run AutoCleaner_App.py