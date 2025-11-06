import sqlite3
import os

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "TrackMyCredits.db")

def check_and_add_column():
    if not os.path.exists(DB_PATH):
        print("⚠️ Database not found! Run app.py once to create it.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Get existing columns from the 'courses' table
    c.execute("PRAGMA table_info(courses)")
    existing_columns = [row[1] for row in c.fetchall()]

    print("📋 Existing columns in 'courses':", existing_columns)

    # Check if 'category' column exists
    if "category" not in existing_columns:
        print("🛠 Adding missing column 'category' to courses table...")
        c.execute("ALTER TABLE courses ADD COLUMN category TEXT DEFAULT 'unknown'")
        conn.commit()
        print("✅ Column 'category' added successfully!")
    else:
        print("✅ Column 'category' already exists. No changes needed.")

    conn.close()


if __name__ == "__main__":
    print("🔍 Running database upgrade check...")
    check_and_add_column()
    print("🚀 Upgrade completed.")
