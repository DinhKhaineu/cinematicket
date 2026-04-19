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

        #Fetch the data from the database 
        available_screenings = backend.get_available_screening()
        
        #Create dictionary mapping readable labels to the actual ScreeningID
        screening_dict = {}
        if available_screenings:
            for s in available_screenings:
                label = f"{s['MovieTitle']} - {s['RoomName']} ({s['ScreeningDate']} @ {s['ScreeningTime']})"
                screening_dict[label] = s['ScreeningID']
        col3, col4 = st.columns([2, 1])
        with col3: 
            if not available_screenings:
                st.warning("No screening available")
                screening_id =None
            else:
                selected_label = st.selectbox("Select Movie & Showtime", list(screening_dict.keys()))
                screening_id = screening_dict[selected_label]
        with col4:
            row_col, seat_col = st.columns(2)
            with row_col:
                row_name = st.text_input("Row (e.e., A, B)", max_chars = 1).upper()
            with seat_col: 
                seat_number = st.number_input("Seat Number", min_value =1, step =1)
            submit_button = st.form_submit_button("Book Ticket")
        if submit_button:
                    if not customer_name.strip() or not phone_number.strip() or not row_name.strip() or not screening_id:
                        st.warning("⚠️ Please fill in all fields.")
                    else:
                        # 1. Automatically get or create the Customer ID
                        auto_customer_id = backend.get_or_create_customer(customer_name.strip(), phone_number.strip())
                        
                        # 2. Pass the IDs into the booking function
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
