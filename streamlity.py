import streamlit as st
import pandas as pd

# ---------------------------
# Data Processing Functions
# ---------------------------
@st.cache_data(show_spinner="Loading file...")
def load_excel_data(file) -> pd.DataFrame:
    """
    Read and process the Excel file using pandas.
    Expects columns: Date, Currency, Exchange, Type, and Amount.
    """
    try:
        df = pd.read_excel(file)
        # Ensure required columns exist
        for col in ['Date', 'Currency', 'Exchange', 'Type', 'Amount']:
            if col not in df.columns:
                raise KeyError(f"Expected column '{col}' not found. Found columns: {df.columns.tolist()}")
        df['Date'] = pd.to_datetime(df['Date'])
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"Error loading file: {e}")
        raise

def create_pivot_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a pivot table that sums the 'Amount' per Date and Currency,
    with separate columns for each combination of Exchange and Type.
    """
    try:
        pivot_df = df.pivot_table(
            values='Amount',
            index=['Date', 'Currency'],
            columns=['Exchange', 'Type'],
            aggfunc='sum',
            fill_value=0
        )
        pivot_df.reset_index(inplace=True)
        return pivot_df
    except Exception as e:
        st.error(f"Error creating pivot table: {e}")
        raise

def pivot_to_long(pivot_df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert the wide pivot table to a long format for merging and comparison.
    Uses stacking if columns are MultiIndex; otherwise uses melt.
    """
    try:
        if isinstance(pivot_df.columns, pd.MultiIndex):
            long_df = pivot_df.set_index(['Date', 'Currency']).stack(level=[0, 1]).reset_index(name='Amount')
            long_df.columns = ['Date', 'Currency', 'Exchange', 'Type', 'Amount']
        else:
            required_cols = ['Date', 'Currency']
            missing = [col for col in required_cols if col not in pivot_df.columns]
            if missing:
                raise KeyError(f"Missing expected columns for melting: {missing}. Found columns: {pivot_df.columns.tolist()}")
            long_df = pivot_df.melt(id_vars=required_cols, var_name='Exchange_Type', value_name='Amount')
            if 'Exchange_Type' in long_df.columns:
                if long_df['Exchange_Type'].dtype == object and '_' in long_df['Exchange_Type'].iloc[0]:
                    long_df[['Exchange', 'Type']] = long_df['Exchange_Type'].str.split('_', expand=True)
                    long_df.drop(columns=['Exchange_Type'], inplace=True)
                else:
                    raise ValueError("Cannot split 'Exchange_Type' column into 'Exchange' and 'Type'.")
        return long_df
    except Exception as e:
        st.error(f"Error converting pivot table to long format: {e}")
        raise

def merge_and_calculate_gap(long_df1: pd.DataFrame, long_df2: pd.DataFrame) -> pd.DataFrame:
    """
    Merge two long-format pivot tables and calculate the gap between amounts.
    The merge is done on Date, Currency, Exchange, and Type.
    """
    try:
        merged_df = pd.merge(
            long_df1, long_df2,
            on=['Date', 'Currency', 'Exchange', 'Type'],
            how='outer',
            suffixes=('_file1', '_file2')
        )
        merged_df['Amount_file1'] = merged_df['Amount_file1'].fillna(0)
        merged_df['Amount_file2'] = merged_df['Amount_file2'].fillna(0)
        merged_df['Gap'] = merged_df['Amount_file1'] - merged_df['Amount_file2']
        return merged_df
    except Exception as e:
        st.error(f"Error merging pivot tables: {e}")
        raise

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
        
        # Display data period for each file.
        st.write(f"**File 1 Period:** {df1['Date'].min().date()} to {df1['Date'].max().date()}")
        st.write(f"**File 2 Period:** {df2['Date'].min().date()} to {df2['Date'].max().date()}")
        
        # Generate pivot tables for each file.
        pivot_df1 = create_pivot_table(df1)
        pivot_df2 = create_pivot_table(df2)
        
        # Convert pivot tables to long format.
        long_df1 = pivot_to_long(pivot_df1)
        long_df2 = pivot_to_long(pivot_df2)
        
        # Merge the two long DataFrames and calculate gaps.
        gap_df = merge_and_calculate_gap(long_df1, long_df2)
        
        # Add a checkbox for filtering rows with non-zero gap.
        show_only_nonzero = st.checkbox("Show only rows with a non-zero gap", value=False)
        if show_only_nonzero:
            gap_df = gap_df[gap_df['Gap'] != 0]
        
        st.subheader("Gaps Between File 1 and File 2")
        st.dataframe(gap_df)
    else:
        st.info("Please upload both Excel files to get started.")

if __name__ == '__main__':
    main()
