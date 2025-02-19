import streamlit as st
import pandas as pd

# Try to import polars; if not installed, notify the user.
try:
    import polars as pl
    POLARS_AVAILABLE = True
except ImportError:
    POLARS_AVAILABLE = False

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

def create_pivot_table_polars(pl_df: pl.DataFrame):
    """Create a pivot table using polars.
    
    Note: Polars’ pivot API supports single-column pivoting.
    For multi-dimensional pivoting (here: Exchange and Type),
    we first combine these columns into one.
    """
    # Create a new column combining Exchange and Type
    pl_df = pl_df.with_columns(
        (pl.col("Exchange").cast(str) + " - " + pl.col("Type").cast(str)).alias("Exchange_Type")
    )
    try:
        pivot_pl = (
            pl_df
            .groupby(["Date", "Currency"])
            .pivot(values="Amount", index=["Date", "Currency"], columns="Exchange_Type")
            .fill_null(0)
        )
    except Exception as e:
        st.error(f"Error while creating pivot with polars: {e}")
        return None
    return pivot_pl

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
        
        # Option to choose processing library:
        lib_options = ["pandas"]
        if POLARS_AVAILABLE:
            lib_options.append("polars")
        library_choice = st.sidebar.selectbox("Choose Data Library", lib_options)
        
        # If using polars, convert the DataFrame
        if library_choice == "polars":
            df = pl.from_pandas(df_pandas)
        else:
            df = df_pandas

        # -------------
        # Sidebar Filters
        # -------------
        st.sidebar.header("Filter Options")
        
        # --- Date Range Filter ---
        if library_choice == "pandas":
            min_date = df['Date'].min().date()
            max_date = df['Date'].max().date()
        else:
            # For polars, extract min and max dates then convert to Python dates.
            min_date = pd.to_datetime(df.select(pl.col("Date").min()).item()).date()
            max_date = pd.to_datetime(df.select(pl.col("Date").max()).item()).date()

        date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date])
        if not isinstance(date_range, list) or len(date_range) != 2:
            st.error("Please select both a start and an end date.")
            return
        start_date, end_date = date_range

        # --- Exchange Filter ---
        if library_choice == "pandas":
            exchanges = sorted(df['Exchange'].dropna().unique().tolist())
        else:
            exchanges = sorted(df["Exchange"].unique().to_list())
        selected_exchanges = st.sidebar.multiselect("Select Exchanges", options=exchanges, default=exchanges)

        # --- Transaction Type Filter ---
        if library_choice == "pandas":
            types = sorted(df['Type'].dropna().unique().tolist())
        else:
            types = sorted(df["Type"].unique().to_list())
        selected_types = st.sidebar.multiselect("Select Transaction Types", options=types, default=types)

        # --- Currency Filter ---
        if library_choice == "pandas":
            currencies = sorted(df['Currency'].dropna().unique().tolist())
        else:
            currencies = sorted(df["Currency"].unique().to_list())
        selected_currencies = st.sidebar.multiselect("Select Currencies", options=currencies, default=currencies)

        # -------------
        # Filtering Data
        # -------------
        if library_choice == "pandas":
            mask = (
                (df['Date'] >= pd.to_datetime(start_date)) &
                (df['Date'] <= pd.to_datetime(end_date)) &
                (df['Exchange'].isin(selected_exchanges)) &
                (df['Type'].isin(selected_types)) &
                (df['Currency'].isin(selected_currencies))
            )
            filtered_df = df.loc[mask]
        else:
            # For polars, convert the date filter to pandas Timestamps first.
            start_ts = pd.to_datetime(start_date)
            end_ts = pd.to_datetime(end_date)
            filtered_df = df.filter(
                (pl.col("Date") >= start_ts) &
                (pl.col("Date") <= end_ts) &
                (pl.col("Exchange").is_in(selected_exchanges)) &
                (pl.col("Type").is_in(selected_types)) &
                (pl.col("Currency").is_in(selected_currencies))
            )

        st.subheader("Filtered Data")
        if library_choice == "pandas":
            st.dataframe(filtered_df)
            no_data = filtered_df.empty
        else:
            st.dataframe(filtered_df.to_pandas())
            no_data = (filtered_df.height == 0)

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