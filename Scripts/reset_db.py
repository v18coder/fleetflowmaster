import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from database.connection import get_db, DB_PATH
from database.init_db import init_db
from database.seed import seed_data

def reset():
    print("--- Resetting FleetFlow Database ---")
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
            print("Removed old database file.")
        except Exception as e:
            print(f"Warning: Could not delete DB file ({e}). Re-initializing schema...")
    
    init_db()
    seed_data()
    print("Database freshly initialized and seeded successfully!")

if __name__ == '__main__':
    reset()
