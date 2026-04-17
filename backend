import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
import os

load_dotenv()

# ==============================================================================
# 1. CONNECTION & HELPER
# ==============================================================================

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
        port=int(os.getenv("MYSQL_PORT", 3306))
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
