import streamlit as st
import pandas as pd
import backend  # Imports your existing backend.py file

# Set up the page configuration
st.set_page_config(page_title="Cinema Management System", page_icon="🎬", layout="wide")

st.title("🎬 Cinema Management System")

# Create a sidebar for navigation
st.sidebar.title("Navigation")
menu = st.sidebar.radio("Go to:", ["🎟️ Book Ticket", "📊 Revenue Report"])

st.sidebar.markdown("---")
st.sidebar.info("Data is synced directly from the MySQL Database.")

# ==========================================
# PAGE 1: BOOK TICKET
# ==========================================
if menu == "🎟️ Book Ticket":
    st.header("Book a New Ticket")
    
    with st.form("booking_form"):
        st.subheader("Customer Details")
        col1, col2 = st.columns(2)
        with col1:
            customer_name = st.text_input("Full Name")
        with col2:
            phone_number = st.text_input("Phone Number")
            
        st.subheader("Screening Details")
        col3, col4, col5 = st.columns(3)
        with col3:
            # We still need the ScreeningID to know the Movie, Time, and Room
            screening_id = st.number_input("Screening ID", min_value=1, step=1)
        with col4:
            row_name = st.text_input("Row (e.g., A, B, C)", max_chars=1).upper()
        with col5:
            seat_number = st.number_input("Seat Number", min_value=1, step=1)
            
        submit_button = st.form_submit_button("Book Ticket")
        
        if submit_button:
            # Added .strip() to ensure users don't just type empty spaces
            if not customer_name.strip() or not phone_number.strip() or not row_name.strip():
                st.warning("⚠️ Please fill in all fields (Name, Phone, and Row).")
            else:
                # 1. Automatically get or create the Customer ID behind the scenes
                auto_customer_id = backend.get_or_create_customer(customer_name.strip(), phone_number.strip())
                
                # 2. Pass that automatic ID into your existing booking function
                success = backend.book_ticket(auto_customer_id, screening_id, row_name.strip(), seat_number)
                
                if success:
                    st.success(f"✅ Successfully booked Seat {row_name}{seat_number} for {customer_name.strip()}!")
                    st.balloons() 
                else:
                    st.error("❌ Booking failed. This seat might be taken, or the layout is invalid.")

# ==========================================
# PAGE 2: REVENUE REPORT
# ==========================================
elif menu == "📊 Revenue Report":
    st.header("Revenue & Occupancy Report")
    
    # Fetch the data using your backend function
    data = backend.report_revenue_by_screening()
    
    if not data:
        st.info("No data available to display.")
    else:
        # Convert the dictionary list from your backend into a Pandas DataFrame
        df = pd.DataFrame(data)
        
        # Calculate total revenue before formatting the strings
        total_revenue = sum([row['Revenue'] for row in data])
        
        # Format the columns for a better visual display
        df['Revenue'] = df['Revenue'].apply(lambda x: f"{x:,.0f} ₫")
        df['OccupancyRate'] = df['OccupancyRate'].apply(lambda x: f"{x}%")
        
        # Display the prominent Total Revenue metric at the top
        st.metric(label="Total System Revenue", value=f"{total_revenue:,.0f} ₫")
        
        st.markdown("### Screening Breakdown")
        # Display the dataframe as an interactive table
        st.dataframe(df, use_container_width=True, hide_index=True)
