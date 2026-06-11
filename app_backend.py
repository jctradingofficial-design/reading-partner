import os
import psycopg2

# This allows the code to work safely on both Streamlit (web) and GitHub (automated actions)
try:
    import streamlit as st
    DB_URL = st.secrets["DATABASE_URL"]
except ImportError:
    DB_URL = os.environ.get("DATABASE_URL")

def get_connection():
    """Opens a connection to the Supabase PostgreSQL database."""
    return psycopg2.connect(DB_URL)

def init_db():
    """Initializes the database and creates the required tables."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Create books table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            total_pages INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            target_end_date TEXT NOT NULL,
            status TEXT DEFAULT 'Reading'
        )
    ''')
    
    # Create reading_logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reading_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            log_date TEXT NOT NULL,
            page_reached INTEGER NOT NULL,
            notes TEXT,
            image_path TEXT,
            FOREIGN KEY (book_id) REFERENCES books (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

def add_book(title, total_pages, start_date, target_end_date):
    """Adds a new book to track."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO books (title, total_pages, start_date, target_end_date)
        VALUES (?, ?, ?, ?)
    ''', (title, total_pages, start_date, target_end_date))
    conn.commit()
    book_id = cursor.lastrowid
    conn.close()
    return book_id

def log_progress(book_id, page_reached, notes=None, image_path=None):
    """Logs daily reading progress."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute('''
        INSERT INTO reading_logs (book_id, log_date, page_reached, notes, image_path)
        VALUES (?, ?, ?, ?, ?)
    ''', (book_id, today, page_reached, notes, image_path))
    conn.commit()
    conn.close()

def calculate_pace(book_id):
    """Calculates the dynamic reading pace required to finish on time."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Fetch book metadata
    cursor.execute("SELECT title, total_pages, target_end_date FROM books WHERE id = ?", (book_id,))
    book = cursor.fetchone()
    if not book:
        conn.close()
        return None
    
    title, total_pages, target_end_date = book
    
    # Fetch latest progress
    cursor.execute("SELECT page_reached FROM reading_logs WHERE book_id = ? ORDER BY id DESC LIMIT 1", (book_id,))
    latest_log = cursor.fetchone()
    current_page = latest_log[0] if latest_log else 0
    conn.close()
    
    # Calculate days remaining
    today = datetime.now().date()
    end_date = datetime.strptime(target_end_date, "%Y-%m-%d").date()
    days_remaining = (end_date - today).days
    
    pages_left = total_pages - current_page
    
    if pages_left <= 0:
        return {"title": title, "status": "Completed", "pages_today": 0}
    if days_remaining <= 0:
        return {"title": title, "status": "Overdue", "pages_today": pages_left}
        
    pages_today = -(-pages_left // days_remaining)  # Ceiling division for clean rounding up
    
    return {
        "title": title,
        "current_page": current_page,
        "pages_left": pages_left,
        "days_remaining": days_remaining,
        "pages_today": pages_today
    }

# Quick testing execution
if __name__ == "__main__":
    init_db()
