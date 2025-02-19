import streamlit as st
import pandas as pd

# Function to process the uploaded Excel file
def process_excel(file):
    df = pd.read_excel(file)
    # Convert columns to proper data types
    df['Date'] = pd.to_datetime(df['Date'])
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    return df

# Function to create the pivot table from the filtered DataFrame
def create_pivot_table(df):
    pivot_df = df.pivot_table(
        values='Amount', 
        index=['Date', 'Currency'], 
        columns=['Exchange', 'Type'], 
        aggfunc='sum', 
        fill_value=0
    )
    pivot_df.reset_index(inplace=True)
    return pivot_df

def main():
    st.title("Crypto Data Analysis Dashboard")

    # File uploader widget
    uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx", "xls"])
    
    if uploaded_file is not None:
        df = process_excel(uploaded_file)
        st.success("File uploaded and processed successfully!")
        
        # Sidebar filters
        st.sidebar.header("Filter Options")
        
        # 1. Date range filter (using the min and max dates from the data)
        min_date = df['Date'].min().date()
        max_date = df['Date'].max().date()
        date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date])
        if len(date_range) != 2:
            st.error("Please select both a start and an end date.")
            return
        start_date, end_date = date_range
        
        # 2. Exchange filter (multi-select)
        exchanges = df['Exchange'].dropna().unique().tolist()
        selected_exchanges = st.sidebar.multiselect("Select Exchanges", options=exchanges, default=exchanges)
        
        # 3. Transaction Type filter (e.g., Buy/Sell)
        types = df['Type'].dropna().unique().tolist()
        selected_types = st.sidebar.multiselect("Select Transaction Types", options=types, default=types)
        
        # 4. Currency filter (multi-select)
        currencies = df['Currency'].dropna().unique().tolist()
        selected_currencies = st.sidebar.multiselect("Select Currencies", options=currencies, default=currencies)
        
        # Filter the data based on user selections
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
        
        if filtered_df.empty:
            st.warning("No data found for the selected filters.")
        else:
            # Create and display the pivot table
            pivot_df = create_pivot_table(filtered_df)
            st.subheader("Pivot Table")
            st.dataframe(pivot_df)
    else:
        st.info("Please upload an Excel file to get started.")

if __name__ == '__main__':
    main()