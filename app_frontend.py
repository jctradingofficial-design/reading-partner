import streamlit as st
import sqlite3
import app_backend as db
from datetime import datetime
import requests

def send_telegram_message(message):
    """Securely pulls credentials from Streamlit Secrets and sends a message."""
    bot_token = st.secrets["BOT_TOKEN"]
    chat_id = st.secrets["CHAT_ID"]
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    requests.post(url, data=payload)

# Ensure the database and tables exist
db.init_db()

# --- Helper Function ---
def get_active_books():
    """Fetches books currently being read to populate the UI."""
    conn = sqlite3.connect(db.DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM books WHERE status = 'Reading'")
    books = cursor.fetchall()
    conn.close()
    return books

# --- User Interface ---
st.title("📚 My Reading Partner")

# Streamlit creates a clean tabbed navigation automatically
tab1, tab2, tab3 = st.tabs(["Dashboard", "Log Progress", "Add a Book"])

# TAB 1: THE PACING DASHBOARD
with tab1:
    st.header("Today's Targets")
    active_books = get_active_books()
    
    if not active_books:
        st.info("No active books found. Head to the 'Add a Book' tab to start!")
    else:
        for book_id, title in active_books:
            pace_data = db.calculate_pace(book_id)
            if pace_data:
                st.subheader(f"📖 {title}")
                if pace_data.get("status") == "Completed":
                    st.success("You finished this book! Great job.")
                else:
                    pages_left = pace_data["pages_left"]
                    pages_today = pace_data["pages_today"]
                    days_remaining = pace_data["days_remaining"]
                    current_page = pace_data["current_page"]
                    total_pages = current_page + pages_left
                    
                    # The Accountability Display (Upgraded UI)
                    percentage = int((current_page / total_pages) * 100)
                    
                    # Create two neat columns for a professional dashboard look
                    col1, col2 = st.columns(2)
                    col1.metric("Today's Target", f"{pages_today} pages")
                    col2.metric("Completion", f"{percentage}%")
                    
                    # The visual progress bar
                    st.progress(current_page / total_pages)
                    st.caption(f"Page {current_page} of {total_pages} • {days_remaining} days remaining")
                if st.button("Send Test Reminder to Phone"):
                    send_telegram_message("📚 Time to read! This is a test from your live app.")
                    st.success("Message sent!")
# TAB 2: DAILY LOGGING & UPLOADS
with tab2:
    st.header("Log Your Reading")
    active_books = get_active_books()
    
    if active_books:
        # Dictionary linking titles to database IDs
        book_options = {title: b_id for b_id, title in active_books}
        selected_title = st.selectbox("Which book did you read?", list(book_options.keys()))
        
        page_reached = st.number_input("What page did you stop at?", min_value=0, step=1)
        notes = st.text_area("Any quick notes or takeaways?")
        
        # Streamlit handles file uploads natively
        image_file = st.file_uploader("Upload a photo of a page (optional)", type=['jpg', 'png', 'jpeg'])
        
        if st.button("Save Progress"):
            # For the MVP, we just store the file name. 
            # Later, we can add logic to save the actual image to a cloud bucket.
            image_path = image_file.name if image_file else None
            db.log_progress(book_options[selected_title], page_reached, notes, image_path)
            st.success("Progress logged! Check the Dashboard for your updated pace.")
    else:
        st.write("Please add a book first.")

# TAB 3: ADDING NEW BOOKS
with tab3:
    st.header("Start a New Book")
    with st.form("add_book_form"):
        title = st.text_input("Book Title")
        total_pages = st.number_input("Total Pages", min_value=1, step=1)
        start_date = st.date_input("Start Date")
        target_date = st.date_input("Target Finish Date")
        
        submitted = st.form_submit_button("Add Book")
        if submitted:
            if target_date <= start_date:
                st.error("Target finish date must be after the start date!")
            else:
                db.add_book(title, total_pages, start_date.strftime("%Y-%m-%d"), target_date.strftime("%Y-%m-%d"))
                st.success(f"'{title}' added successfully!")
