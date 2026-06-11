import psycopg2
import os
from datetime import datetime

# Securely grab the database password from Streamlit or GitHub
try:
    import streamlit as st
    DB_URL = st.secrets["DATABASE_URL"]
except ImportError:
    DB_URL = os.environ.get("DATABASE_URL")

def get_connection():
    """Opens a connection to the Supabase PostgreSQL database."""
    return psycopg2.connect(DB_URL)

def add_book(title, total_pages, target_date):
    """Adds a new book to the database."""
    conn = get_connection()
    cursor = conn.cursor()
    # Notice the %s instead of ?
    cursor.execute('''
        INSERT INTO books (title, total_pages, target_date, status)
        VALUES (%s, %s, %s, 'Reading')
    ''', (title, total_pages, target_date))
    conn.commit()
    conn.close()

def get_active_books():
    """Retrieves all books currently being read."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM books WHERE status = 'Reading'")
    books = cursor.fetchall()
    conn.close()
    return books

def log_reading(book_id, date, pages_read):
    """Logs the number of pages read on a specific date."""
    conn = get_connection()
    cursor = conn.cursor()
    # Notice the %s instead of ?
    cursor.execute('''
        INSERT INTO reading_logs (book_id, date, pages_read)
        VALUES (%s, %s, %s)
    ''', (book_id, date, pages_read))
    conn.commit()
    conn.close()

def calculate_pace(book_id):
    """Calculates exactly how many pages need to be read today."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Notice the %s instead of ?
    cursor.execute("SELECT total_pages, target_date, status FROM books WHERE id = %s", (book_id,))
    book = cursor.fetchone()
    
    if not book:
        conn.close()
        return None
        
    total_pages, target_date_str, status = book
    
    # Handle PostgreSQL date format
    if isinstance(target_date_str, str):
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    else:
        target_date = target_date_str
        
    today = datetime.now().date()

    # Notice the %s instead of ?
    cursor.execute("SELECT SUM(pages_read) FROM reading_logs WHERE book_id = %s", (book_id,))
    pages_read_result = cursor.fetchone()[0]
    pages_read = pages_read_result if pages_read_result else 0

    conn.close()

    pages_remaining = total_pages - pages_read
    days_remaining = (target_date - today).days

    if pages_remaining <= 0:
        return {"status": "Completed", "pages_today": 0, "current_page": total_pages, "total": total_pages, "days": 0}
    
    if days_remaining <= 0:
        pages_today = pages_remaining # Must finish today
    else:
        pages_today = round(pages_remaining / days_remaining)

    return {
        "status": status,
        "pages_today": pages_today,
        "current_page": pages_read,
        "total": total_pages,
        "days": days_remaining
    }

def mark_completed(book_id):
    """Marks a book as finished."""
    conn = get_connection()
    cursor = conn.cursor()
    # Notice the %s instead of ?
    cursor.execute("UPDATE books SET status = 'Completed' WHERE id = %s", (book_id,))
    conn.commit()
    conn.close()
