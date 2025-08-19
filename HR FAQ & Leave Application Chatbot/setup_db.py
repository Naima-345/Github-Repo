import sqlite3

# Make sure this matches the DB your bot will use
conn = sqlite3.connect("leave_applications.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS leave_applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    leave_type TEXT,
    start_date TEXT,
    end_date TEXT,
    reason TEXT,
    leave_days INTEGER
)
""")

conn.commit()
conn.close()
print("✅ leave_applications table is ready!")
