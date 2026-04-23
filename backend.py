import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
import os

load_dotenv()

# ==============================================================================
# CONNECTION & HELPER
# ==============================================================================

def get_connection():
    try:
        db_host = st.secrets["MYSQL_HOST"]
        db_user = st.secret["MYSQL_USER"]
        db_pass = st.secrets["MYSQL_PASSWORD"]
        db_name = st.secrets["MYSQL_DATABASE"]
        db_port = int(st.secrets["MYSQL_PORT"])
    except (FileNotFoundError, KeyError):
        db_host = os.getenv("MYSQL_HOST", "local_host")
        db_user = os.getevn("MYSQL_USER")
        db_pass = os.getevn("MYSQL_PASSWORD")
        db_name = os.getevn("MYSQL_DATABASE")
        db_port = int(os.getevn("MYSQL_PORT", 3306))
    return mysql.connector.connect(
        host = db_host,
        user = db_user,
        password = db_pass,
        database = db_name,
        port = db_port,
        ssl_disabled = False,
        ssl_verify_cert = False,
        ssl_verify_identity = False
    )
    

def execute_query(sql, params=None, fetch=True):
    with get_connection() as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(sql, params or ())
            if fetch:
                return cursor.fetchall()
            conn.commit()
            return cursor.rowcount

def execute_procedure(proc_name, params=()):
    """
    Hàm helper riêng để gọi Stored Procedure của TV2.
    Trả về True nếu thành công, raise Error nếu thất bại.
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.callproc(proc_name, params)
            conn.commit()
            return True
        
# ==============================================================================
# CUSTOMER MANAGEMENT
# ==============================================================================

def get_or_create_customer(name, phone):
    """
    Finds a customer by phone number, or creates a new one if they don't exist.
    Returns CustomerID.
    """
    # 1. Check existing — dùng PhoneNumber gốc (clerk có SELECT trên Customers)
    existing = execute_query(
        "SELECT CustomerID FROM Customers WHERE PhoneNumber = %s",
        (phone,)
    )
    if existing:
        print(f"[OK] Customer found (ID: {existing[0]['CustomerID']})")
        return existing[0]['CustomerID']

    # 2. Insert mới — clerk có INSERT ON Customers
    execute_query(
        "INSERT INTO Customers (CustomerName, PhoneNumber) VALUES (%s, %s)",
        (name, phone),
        fetch=False
    )

    # 3. Lấy ID vừa tạo
    new = execute_query(
        "SELECT CustomerID FROM Customers WHERE PhoneNumber = %s",
        (phone,)
    )
    print(f"[OK] New customer created: {name} (ID: {new[0]['CustomerID']})")
    return new[0]['CustomerID']

# ==============================================================================
# SCREENING MANAGEMENT (RESTORED FOR STREAMLIT DROPDOWN)
# ==============================================================================
def get_available_screenings():
    """Fetches all screenings to populate the UI dropdown."""
    sql = """
        SELECT 
            s.ScreeningID, 
            m.MovieTitle, 
            c.RoomName, 
            s.ScreeningDate, 
            s.ScreeningTime
        FROM Screenings s
        JOIN Movies m ON s.MovieID = m.MovieID
        JOIN CinemaRooms c ON s.RoomID = c.RoomID
        ORDER BY s.ScreeningDate, s.ScreeningTime
    """
    return execute_query(sql)

# ==============================================================================
# BOOK TICKET
# ==============================================================================

def book_ticket(customer_id, screening_id, row_name, seat_number):
    try:
        execute_procedure("sp_BookTicket", (customer_id, screening_id, row_name, seat_number))
        print(f"[OK] Ticket booked! Seat {row_name}{seat_number} - Screening #{screening_id}")
        return True
    except Error as e:
        print(f"[Error] Booking failed: {e.msg}")
        return False
    
# ==============================================================================
# REVENUE REPORT
# ==============================================================================

def report_revenue_by_screening():
    return execute_query("""
        SELECT
            s.ScreeningID,
            m.MovieTitle,
            cr.RoomName,
            s.ScreeningDate,
            s.ScreeningTime,
            fn_CalculateRevenue(s.ScreeningID)       AS Revenue,
            fn_CalculateOccupancyRate(s.ScreeningID) AS OccupancyRate
        FROM Screenings s
        JOIN Movies m       ON s.MovieID = m.MovieID
        JOIN CinemaRooms cr ON s.RoomID  = cr.RoomID
        ORDER BY s.ScreeningDate, s.ScreeningTime
    """)

def print_revenue_report():
    print("\n" + "="*75)
    print("            REVENUE REPORT BY SCREENING")
    print("="*75)

    rows = report_revenue_by_screening()
    if not rows:
        print("No data available.")
        return

    print(f"{'ID':<5} {'Movie':<22} {'Room':<12} {'Date':<12} "
          f"{'Time':<10} {'Revenue':>12} {'Occupancy':>10}")
    print("-"*75)

    total = 0
    for r in rows:
        print(
            f"{r['ScreeningID']:<5} "
            f"{str(r['MovieTitle'])[:21]:<22} "
            f"{r['RoomName']:<12} "
            f"{str(r['ScreeningDate']):<12} "
            f"{str(r['ScreeningTime']):<10} "
            f"{r['Revenue']:>10,} VND "
            f"{r['OccupancyRate']:>8}%"
        )
        total += r['Revenue']

    print("-"*75)
    print(f"{'TOTAL REVENUE':>63} {total:>10,} VND")
    print("="*75)
    
# ==============================================================================
# LOGIN SYSTEM
# ==============================================================================

def login(username, password):
    """
    Authenticate user against MySQL users (admin_user / clerk_user).
    Returns role string or None if failed.
    """
    try:
        conn = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            user=username,
            password=password,
            database=os.getenv("MYSQL_DATABASE"),
            port=int(os.getenv("MYSQL_PORT", 3306))
        )
        conn.close()

        # Xác định role dựa vào username
        if username == "admin_user":
            return "admin"
        elif username == "clerk_user":
            return "clerk"
        else:
            return "clerk"  # default

    except Error:
        return None  # Sai username hoặc password


def login_prompt():
    """
    Authenticates user by attempting a MySQL connection with their credentials.
    Returns 'admin', 'clerk', or None if the login fails.
    """
    try:
        # Attempt connection using the user's specific credentials
        conn = mysql.connector.connect(
            host=st.secrets.get("MYSQL_HOST", os.getenv("MYSQL_HOST", "localhost")),
            user=username,
            password=password,
            database=st.secrets.get("MYSQL_DATABASE", os.getenv("MYSQL_DATABASE")),
            port=int(st.secrets.get("MYSQL_PORT", os.getenv("MYSQL_PORT", 3306))),
            ssl_disabled=False,
            ssl_verify_cert=False,
            ssl_verify_identity=False
        )
        conn.close() # Close immediately, we just needed to prove they can log in

        # Assign role based on the username they provided
        if username == "admin_user":
            return "admin"
        else:
            return "clerk"

    except Error:
        # If MySQL rejects the username/password, return None
        return None
