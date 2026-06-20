import streamlit as st
import requests
from datetime import datetime
import app_backend as db

# -----------------------------------------
# 1. PAGE CONFIGURATION & STYLING
# -----------------------------------------
st.set_page_config(
    page_title="Reading Partner", 
    page_icon="📚", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a cleaner look
st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------
# 2. TELEGRAM HELPER FUNCTION
# -----------------------------------------
def send_telegram_message(text):
    """Securely pulls secrets and fires the test ping."""
    bot_token = st.secrets["BOT_TOKEN"]
    chat_id = st.secrets["CHAT_ID"]
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    
    try:
        requests.post(url, data=payload)
        return True
    except Exception as e:
        st.error(f"Failed to send message: {e}")
        return False

# -----------------------------------------
# 3. SIDEBAR (ADMIN TOOLS)
# -----------------------------------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3389/3389081.png", width=80) # Generic book icon
    st.title("Admin Tools")
    st.markdown("---")
    st.write("Test your bot connection:")
    
    if st.button("🔔 Send Test Reminder", use_container_width=True):
        if send_telegram_message("📚 Time to read! This is a test from your live app."):
            st.success("Message sent successfully!")

# -----------------------------------------
# 4. MAIN APPLICATION HEADER
# -----------------------------------------
st.title("📚 My Reading Partner")
st.markdown("Track your daily progress, stay consistent, and hit your reading goals.")
st.markdown("---")

# Create the primary navigation tabs
tab_dash, tab_log, tab_add = st.tabs(["📊 Dashboard", "📝 Log Progress", "➕ Add New Book"])

# -----------------------------------------
# 5. TAB 1: THE DASHBOARD
# -----------------------------------------
with tab_dash:
    active_books = db.get_active_books()
    
    if not active_books:
        st.info("You don't have any active books right now. Go to 'Add New Book' to get started!")
    else:
        st.subheader("Current Targets")
        # Create a 2-column grid layout for the books
        cols = st.columns(2)
        
        for i, book in enumerate(active_books):
            book_id = book[0]
            title = book[1]
            stats = db.calculate_pace(book_id)
            
            if stats:
                # Alternate placing books into the left and right columns
                col = cols[i % 2]
                
                with col:
                    # The new border container makes it look like a clean "card"
                    with st.container(border=True):
                        st.markdown(f"#### {title}")
                        
                        # Create 3 mini-columns for the stats
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Read Today", f"{stats['pages_today']} pgs")
                        m2.metric("Days Left", stats['days'])
                        
                        # Calculate the percentage
                        completion = 0
                        if stats['total'] > 0:
                            completion = int((stats['current_page'] / stats['total']) * 100)
                        m3.metric("Completion", f"{completion}%")
                        
                        # Visual Progress Bar
                        st.progress(completion / 100.0)
                        st.caption(f"You have read **{stats['current_page']}** out of **{stats['total']}** pages.")
                        
                        # If a book is fully read, show a button to close it out
                        if completion >= 100:
                            if st.button("🎉 Mark as Finished", key=f"finish_{book_id}", use_container_width=True):
                                db.mark_completed(book_id)
                                st.balloons() # Visual celebration
                                st.rerun() # Refresh the page immediately

# -----------------------------------------
# 6. TAB 2: LOGGING PROGRESS
# -----------------------------------------
with tab_log:
    active_books = db.get_active_books()
    
    if not active_books:
        st.warning("⚠️ You need to add a book before you can log progress.")
    else:
        # Create a dictionary to link the title the user sees to the ID the database needs
        book_dict = {book[1]: book[0] for book in active_books}
        
        with st.container(border=True):
            st.subheader("Update Your Reading")
            with st.form("log_form"):
                selected_title = st.selectbox("Which book did you read?", list(book_dict.keys()))
                pages_read = st.number_input("How many pages did you finish today?", min_value=1, step=1)
                log_date = st.date_input("Date", value=datetime.now().date())
                
                submitted = st.form_submit_button("💾 Save Progress")
                if submitted:
                    book_id = book_dict[selected_title]
                    db.log_reading(book_id, log_date, pages_read)
                    st.success(f"Great job! {pages_read} pages logged for '{selected_title}'.")
                    st.toast("Progress saved successfully!", icon="✅")

# -----------------------------------------
# 7. TAB 3: ADDING A BOOK
# -----------------------------------------
with tab_add:
    with st.container(border=True):
        st.subheader("Start a New Journey")
        with st.form("add_book_form"):
            new_title = st.text_input("Book Title", placeholder="e.g., Atomic Habits")
            total_pages = st.number_input("Total Pages", min_value=1, step=1)
            target_date = st.date_input("Target Finish Date")
            
            submitted = st.form_submit_button("🚀 Add to Library")
            if submitted:
                if new_title.strip() == "":
                    st.error("Please enter a valid book title.")
                else:
                    db.add_book(new_title, total_pages, target_date)
                    st.success(f"'{new_title}' is now in your dashboard!")
                    st.snow() # Visual celebration
