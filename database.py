import sqlite3
import os

DB_DIR = 'db'
DB_PATH = os.path.join(DB_DIR, 'planner.db')

def get_connection():
    """Establish and return a connection to the SQLite database."""
    # Connecting to the database file (it creates the file if it doesn't exist)
    conn = sqlite3.connect(DB_PATH)
    # This allows us to access columns by name (like dictionaries) instead of index
    conn.row_factory = sqlite3.Row  
    return conn

def init_db():
    """Initialize the database tables based on our planned schema."""
    # Ensure the database directory exists
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)

    conn = get_connection()
    cursor = conn.cursor()

    # 1. Subjects Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            exam_date DATE NOT NULL,
            daily_hours_allocated REAL NOT NULL
        )
    ''')

    # 2. Topics Table (Linked to Subjects)
    # difficulty: 1 (Easy), 2 (Medium), 3 (Hard)
    # status: Pending, Completed
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            difficulty INTEGER NOT NULL,
            status TEXT DEFAULT 'Pending',
            estimated_hours REAL NOT NULL,
            FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE CASCADE
        )
    ''')

    # 3. Schedule Table (Linked to Topics)
    # Holds our day-to-day generated plan
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            topic_id INTEGER NOT NULL,
            is_revision BOOLEAN DEFAULT FALSE,
            is_completed BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (topic_id) REFERENCES topics (id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()
    print("Database tables created successfully!")

if __name__ == '__main__':
    # This block runs when we execute the script directly
    init_db()
