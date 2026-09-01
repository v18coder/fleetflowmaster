import sys
import os
from datetime import date, datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from database.connection import get_db

def audit():
    conn = get_db()
    drivers = conn.execute("SELECT * FROM drivers").fetchall()
    vehicles = conn.execute("SELECT * FROM vehicles").fetchall()
    conn.close()

    today = date.today()
    print("\n==========================================")
    print(f"  FLEETFLOW COMPLIANCE AND SAFETY AUDIT   ")
    print(f"  Date: {today.isoformat()}                ")
    print("==========================================\n")

    print("[1] Driver License Compliance:")
    for d in drivers:
        exp = datetime.strptime(d['license_expiry'][:10], '%Y-%m-%d').date()
        days_left = (exp - today).days
        if days_left < 0:
            status = f"EXPIRED ({abs(days_left)} days ago) [BLOCKED]"
        elif days_left <= 60:
            status = f"EXPIRING SOON ({days_left} days left)"
        else:
            status = f"VALID ({days_left} days left)"
        print(f"  * {d['name']:<16} | License: {d['license_number']:<10} | Cat: {d['license_category']:<5} | Score: {d['safety_score']:>3}% | {status}")

    print("\n[2] Vehicle Asset Status:")
    for v in vehicles:
        print(f"  * {v['name']:<18} | {v['license_plate']:<10} | {v['type']:<6} | Cap: {v['max_capacity']:>5}kg | Status: {v['status']}")
    print("\nAudit completed successfully.\n")

if __name__ == '__main__':
    audit()
