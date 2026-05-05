"""
Zenith Database Module
Provides persistent SQLite storage for user authentication and app data.
Uses Python's built-in sqlite3 — no extra dependencies required.
"""

import sqlite3
import os
from typing import Optional

# Database file path (stored alongside backend files)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zenith.db")


def get_connection():
    """Get a new SQLite connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database schema. Safe to call multiple times."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            full_name TEXT,
            hashed_password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usage_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            screen_time REAL,
            app_switches INTEGER,
            focus_score REAL,
            logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"[Zenith DB] Initialized at {DB_PATH}")


# --- User CRUD Operations ---

def create_user(username: str, email: Optional[str], full_name: Optional[str], hashed_password: str) -> dict:
    """Create a new user. Returns the user dict or raises an error if username exists."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, email, full_name, hashed_password) VALUES (?, ?, ?, ?)",
            (username, email, full_name, hashed_password)
        )
        conn.commit()
        return {
            "username": username,
            "email": email,
            "full_name": full_name,
        }
    except sqlite3.IntegrityError:
        raise ValueError(f"Username '{username}' already exists")
    finally:
        conn.close()


def get_user_by_username(username: str) -> Optional[dict]:
    """Fetch a user by username. Returns None if not found."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    
    if row is None:
        return None
    
    return {
        "id": row["id"],
        "username": row["username"],
        "email": row["email"],
        "full_name": row["full_name"],
        "hashed_password": row["hashed_password"],
        "created_at": row["created_at"],
    }


def username_exists(username: str) -> bool:
    """Check if a username is already taken."""
    return get_user_by_username(username) is not None


def update_user(username: str, email: Optional[str] = None, full_name: Optional[str] = None) -> Optional[dict]:
    """Update a user's profile fields. Returns updated user dict."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET email = COALESCE(?, email), full_name = COALESCE(?, full_name) WHERE username = ?",
        (email, full_name, username)
    )
    conn.commit()
    conn.close()
    return get_user_by_username(username)


def update_password(username: str, new_hashed_password: str) -> bool:
    """Update a user's hashed password. Returns True if successful."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET hashed_password = ? WHERE username = ?",
        (new_hashed_password, username)
    )
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


# --- Usage Logging ---

def log_usage(user_id: int, screen_time: float, app_switches: int, focus_score: float):
    """Log a usage session for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO usage_logs (user_id, screen_time, app_switches, focus_score) VALUES (?, ?, ?, ?)",
        (user_id, screen_time, app_switches, focus_score)
    )
    conn.commit()
    conn.close()


def get_user_usage_history(user_id: int, limit: int = 30) -> list:
    """Get recent usage logs for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM usage_logs WHERE user_id = ? ORDER BY logged_at DESC LIMIT ?",
        (user_id, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# Initialize DB on module import
init_db()
