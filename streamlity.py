import streamlit as st
import pandas as pd

# ---------------------------
# Data Processing Functions
# ---------------------------
@st.cache_data(show_spinner="Loading file...")
def load_excel_data(file) -> pd.DataFrame:
    """Read and process the Excel file using pandas."""
    df = pd.read_excel(file)
    df['Date'] = pd.to_datetime(df['Date'])
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    return df

def create_pivot_table(df: pd.DataFrame) -> pd.DataFrame:
    """Create a pivot table that sums the 'Amount' per Date and Currency,
    with separate columns for each combination of Exchange and Type.
    """
    pivot_df = df.pivot_table(
        values='Amount',
        index=['Date', 'Currency'],
        columns=['Exchange', 'Type'],
        aggfunc='sum',
        fill_value=0
    )
    pivot_df.reset_index(inplace=True)
    return pivot_df

def pivot_to_long(pivot_df: pd.DataFrame) -> pd.DataFrame:
    """Convert the wide pivot table to a long format for easier merging and comparison."""
    long_df = pivot_df.melt(
        id_vars=['Date', 'Currency'],
        var_name=['Exchange', 'Type'],
        value_name='Amount'
    )
    return long_df

def merge_and_calculate_gap(long_df1: pd.DataFrame, long_df2: pd.DataFrame) -> pd.DataFrame:
    """Merge two long-format pivot tables and calculate the gap in amounts."""
    merged_df = pd.merge(
        long_df1, long_df2,
        on=['Date', 'Currency', 'Exchange', 'Type'],
        how='outer',
        suffixes=('_file1', '_file2')
    )
    # Fill missing amounts with zero so the gap calculation is accurate
    merged_df['Amount_file1'] = merged_df['Amount_file1'].fillna(0)
    merged_df['Amount_file2'] = merged_df['Amount_file2'].fillna(0)
    merged_df['Gap'] = merged_df['Amount_file1'] - merged_df['Amount_file2']
    return merged_df

# ---------------------------
# Main Streamlit App
# ---------------------------
def main():
    st.title("Crypto Data Analysis Dashboard - Level 2")
    st.write("Upload two Excel files to compare crypto transaction data and identify gaps.")

    # File uploader for two files
    uploaded_file1 = st.file_uploader("Upload the first Excel file", type=["xlsx", "xls"], key="file1")
    uploaded_file2 = st.file_uploader("Upload the second Excel file", type=["xlsx", "xls"], key="file2")
    
    if uploaded_file1 is not None and uploaded_file2 is not None:
        # Load data from each file
        df1 = load_excel_data(uploaded_file1)
        df2 = load_excel_data(uploaded_file2)
        
        st.success("Both files uploaded and processed successfully!")
        
        # Display the overall period of the data for each file
        st.write(f"**File 1 Period:** {df1['Date'].min().date()} to {df1['Date'].max().date()}")
        st.write(f"**File 2 Period:** {df2['Date'].min().date()} to {df2['Date'].max().date()}")
        
        # Generate pivot tables for each file
        pivot_df1 = create_pivot_table(df1)
        pivot_df2 = create_pivot_table(df2)
        
        # Display the pivot tables
        st.subheader("Pivot Table - File 1")
        st.dataframe(pivot_df1)
        st.subheader("Pivot Table - File 2")
        st.dataframe(pivot_df2)
        
        # Convert pivot tables to long format for easier merging and comparison
        long_df1 = pivot_to_long(pivot_df1)
        long_df2 = pivot_to_long(pivot_df2)
        
        # Merge the two long DataFrames and calculate gaps
        gap_df = merge_and_calculate_gap(long_df1, long_df2)
        
        st.subheader("Gaps Between File 1 and File 2")
        st.dataframe(gap_df)
    else:
        st.info("Please upload both Excel files to get started.")

if __name__ == '__main__':
    main()
