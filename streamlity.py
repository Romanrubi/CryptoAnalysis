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

def create_pivot_table_pandas(df: pd.DataFrame) -> pd.DataFrame:
    """Create a pivot table using pandas."""
    pivot_df = df.pivot_table(
        values='Amount',
        index=['Date', 'Currency'],
        columns=['Exchange', 'Type'],
        aggfunc='sum',
        fill_value=0
    )
    pivot_df.reset_index(inplace=True)
    return pivot_df


# ---------------------------
# Main Streamlit App
# ---------------------------
def main():
    st.title("Crypto Data Analysis Dashboard")

    # File uploader widget
    uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx", "xls"])

    if uploaded_file is not None:
        # Load data using pandas (Excel reading is done via pandas)
        df_pandas = load_excel_data(uploaded_file)
        st.success("File uploaded and processed successfully!")
        df = df_pandas

        # -------------
        # Sidebar Filters
        # -------------
        st.sidebar.header("Filter Options")
        

        min_date = df['Date'].min().date()
        max_date = df['Date'].max().date()
        date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date])

        
        if not isinstance(date_range, list) or len(date_range) != 2:
            st.error("Please select both a start and an end date.")
            return
        start_date, end_date = date_range

        # --- Exchange Filter ---
        exchanges = sorted(df['Exchange'].dropna().unique().tolist())

        # --- Transaction Type Filter ---

        types = sorted(df['Type'].dropna().unique().tolist())
        selected_types = st.sidebar.multiselect("Select Transaction Types", options=types, default=types)

        # --- Currency Filter ---

        currencies = sorted(df['Currency'].dropna().unique().tolist())
        selected_currencies = st.sidebar.multiselect("Select Currencies", options=currencies, default=currencies)

        # -------------
        # Filtering Data
        # -------------

        mask = (
                (df['Date'] >= pd.to_datetime(start_date)) &
                (df['Date'] <= pd.to_datetime(end_date)) &
                (df['Exchange'].isin(selected_exchanges)) &
                (df['Type'].isin(selected_types)) &
                (df['Currency'].isin(selected_currencies))
        )
        filtered_df = df.loc[mask]

        st.subheader("Filtered Data")
        st.dataframe(filtered_df)
        no_data = filtered_df.empty
        
        if no_data:
            st.warning("No data found for the selected filters.")
        else:
            # -------------
            # Creating Pivot Table
            # -------------
            st.subheader("Pivot Table")
            if library_choice == "pandas":
                pivot_df = create_pivot_table_pandas(filtered_df)
                st.dataframe(pivot_df)
            else:
                pivot_pl = create_pivot_table_polars(filtered_df)
                if pivot_pl is not None:
                    st.dataframe(pivot_pl.to_pandas())
    else:
        st.info("Please upload an Excel file to get started.")

if __name__ == '__main__':
    main()