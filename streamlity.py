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
    """Create a pivot table using pandas.
    
    Pivot table sums the 'Amount' per Date and Currency,
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

# ---------------------------
# Main Streamlit App
# ---------------------------
def main():
    st.title("Crypto Data Analysis Dashboard")

    # File uploader widget
    uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx", "xls"])

    if uploaded_file is not None:
        # Load data from the uploaded Excel file
        df = load_excel_data(uploaded_file)
        st.success("File uploaded and processed successfully!")

        # Display the overall period of the data
        min_date = df['Date'].min().date()
        max_date = df['Date'].max().date()
        st.write(f"**The Period is from: {min_date} to: {max_date}**")

        # ---------------------------
        # Sidebar Filters (Optional)
        # ---------------------------
        st.sidebar.header("Filter Options")

        # Filter for Transaction Types
        types = sorted(df['Type'].dropna().unique().tolist())
        selected_types = st.sidebar.multiselect("Select Transaction Types", options=types, default=types)

        # Filter for Currencies
        currencies = sorted(df['Currency'].dropna().unique().tolist())
        selected_currencies = st.sidebar.multiselect("Select Currencies", options=currencies, default=currencies)

        # Filter for Exchanges
        exchanges = sorted(df['Exchange'].dropna().unique().tolist())
        selected_exchanges = st.sidebar.multiselect("Select Exchanges", options=exchanges, default=exchanges)

        # ---------------------------
        # Filtering Data (No Date Filter)
        # ---------------------------
        mask = (
            df['Exchange'].isin(selected_exchanges) &
            df['Type'].isin(selected_types) &
            df['Currency'].isin(selected_currencies)
        )
        filtered_df = df.loc[mask]

        st.subheader("The Data")
        st.dataframe(filtered_df)
        if filtered_df.empty:
            st.warning("No data found for the selected filters.")
        else:
            # ---------------------------
            # Creating Pivot Table
            # ---------------------------
            st.subheader("Nissani Table")
            pivot_df = create_pivot_table(filtered_df)
            st.dataframe(pivot_df)
    else:
        st.info("Please upload an Excel file to get started.")

if __name__ == '__main__':
    main()
