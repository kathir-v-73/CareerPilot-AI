#!/usr/bin/env python3
"""Initialize the database schema for CareerPilot AI"""

from utils.database import Database

if __name__ == "__main__":
    print("Initializing database for CareerPilot AI...")
    db = Database()
    db.init_db()
    print("Database initialized successfully!")
    print("Tables created: users, email_preferences")