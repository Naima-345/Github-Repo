
import sqlite3

def print_leave_applications():
    try:
        # Connect to the database
        conn = sqlite3.connect("leave_applications.db")
        cursor = conn.cursor()
        
        # Print header
        print("\n" + "="*50)
        print("LEAVE APPLICATIONS IN DATABASE".center(50))
        print("="*50)

        # Get and print column names
        cursor.execute("PRAGMA table_info(leave_applications)")
        columns = [col[1] for col in cursor.fetchall()]
        print("\nColumns:", ", ".join(columns))
        
        # Print all records
        cursor.execute("SELECT * FROM leave_applications")
        for row in cursor.fetchall():
            print("\nRecord:")
            for idx, value in enumerate(row):
                print(f"  {columns[idx]}: {value}")
        
        print("\n" + "="*50)
        
    except sqlite3.Error as e:
        print(f"[ERROR] Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print_leave_applications()
