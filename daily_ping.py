import os
import psycopg2
import requests
from datetime import datetime

# Securely grab the secrets from GitHub Actions
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
DB_URL = os.environ.get("DATABASE_URL")

def get_smart_message():
    """Connects to Supabase, calculates today's reading goals, and formats a message."""
    try:
        # Connect to your cloud database
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        
        # Fetch only books that are currently active
        cursor.execute("SELECT id, title, total_pages, target_date FROM books WHERE status = 'Reading'")
        books = cursor.fetchall()
        
        if not books:
            return "📚 You currently have no active books. Time to add a new one to your Reading Partner!"
            
        message_lines = ["📚 *Your Daily Reading Goals:*", ""]
        today = datetime.now().date()
        
        for book in books:
            book_id, title, total_pages, target_date = book
            
            # Sum up all logged reading sessions for this specific book
            cursor.execute("SELECT SUM(pages_read) FROM reading_logs WHERE book_id = %s", (book_id,))
            pages_read_result = cursor.fetchone()[0]
            pages_read = pages_read_result if pages_read_result else 0
            
            pages_remaining = total_pages - pages_read
            days_remaining = (target_date - today).days
            
            # Calculate what needs to be done today
            if pages_remaining <= 0:
                message_lines.append(f"✅ *{title}* - You finished this book! Update its status on the dashboard.")
            elif days_remaining <= 0:
                message_lines.append(f"⚠️ *{title}* - Target date is today! {pages_remaining} pages left.")
            else:
                pages_today = round(pages_remaining / days_remaining)
                message_lines.append(f"📖 *{title}* - Read {pages_today} pages today.")
        
        conn.close()
        return "\n".join(message_lines)
        
    except Exception as e:
        return f"⚠️ Reading Partner tried to calculate your goals but ran into an issue: {e}"

def send_telegram_message(text):
    """Fires the formatted message to your Telegram bot and prints the result."""
    print("Preparing to send message to Telegram...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, data=payload)
    
    # This forces GitHub to show us exactly what Telegram says back
    print(f"Telegram Status Code: {response.status_code}")
    print(f"Telegram Error Details: {response.text}")
