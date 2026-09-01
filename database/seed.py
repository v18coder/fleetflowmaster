from werkzeug.security import generate_password_hash
from .connection import get_db

def seed_data():
    conn = get_db()
    cursor = conn.cursor()

    # Check if data already exists
    cursor.execute("SELECT COUNT(*) as count FROM users")
    if cursor.fetchone()['count'] > 0:
        conn.close()
        return

    default_password = generate_password_hash('password123', method='pbkdf2:sha256')

    # 1. Seed Users (4 Roles)
    users = [
        ('Fleet Admin', 'manager@fleetflow.com', default_password, 'Manager'),
        ('Dave Dispatcher', 'dispatcher@fleetflow.com', default_password, 'Dispatcher'),
        ('Sam Safety', 'safety@fleetflow.com', default_password, 'Safety Officer'),
        ('Fiona Finance', 'finance@fleetflow.com', default_password, 'Financial Analyst'),
    ]
    cursor.executemany("""
    INSERT INTO users (name, email, password, role, is_active)
    VALUES (?, ?, ?, ?, 1)
    """, users)

    # 2. Seed Vehicles
    vehicles = [
        ('Heavy Hauler 01', 'Volvo FH16', 'TRK-9021', 'Truck', 12000, 45200, 85000, 'North', 'Available'),
        ('Swift Van 05', 'Ford Transit', 'VAN-3042', 'Van', 1500, 18400, 38000, 'West', 'Available'),
        ('Eco Van 02', 'Mercedes Sprinter', 'VAN-5521', 'Van', 1200, 31000, 34000, 'South', 'On Trip'),
        ('Titan Rig 04', 'Scania R500', 'TRK-4410', 'Truck', 18000, 98000, 110000, 'East', 'In Shop'),
        ('Metro Cargo Bike 01', 'Bullitt Cargo', 'BIK-1001', 'Bike', 80, 2100, 3500, 'Central', 'Available'),
        ('Urban Sprinter 08', 'Iveco Daily', 'VAN-7712', 'Van', 1800, 52000, 41000, 'North', 'Available'),
        ('Old Courier 09', 'Nissan NV200', 'VAN-0099', 'Van', 900, 210000, 22000, 'South', 'Retired'),
    ]
    cursor.executemany("""
    INSERT INTO vehicles (name, model, license_plate, type, max_capacity, odometer, acquisition_cost, region, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, vehicles)

    # 3. Seed Drivers
    drivers = [
        ('Alex Mercer', 'DL-88392', 'All', '2028-10-15', '+1 555-0101', 'On Duty', 96, 142),
        ('Sarah Jenkins', 'DL-44910', 'Van', '2027-04-12', '+1 555-0102', 'On Trip', 98, 89),
        ('Marcus Vance', 'DL-11029', 'Truck', '2026-11-20', '+1 555-0103', 'On Duty', 91, 210),
        ('Elena Rostova', 'DL-33921', 'Bike', '2029-01-05', '+1 555-0104', 'On Duty', 99, 320),
        ('David Miller', 'DL-00219', 'Van', '2025-12-01', '+1 555-0105', 'Suspended', 72, 45),
        ('Robert Chen', 'DL-77341', 'Truck', '2028-06-18', '+1 555-0106', 'Off Duty', 94, 115),
    ]
    cursor.executemany("""
    INSERT INTO drivers (name, license_number, license_category, license_expiry, phone, status, safety_score, trips_completed)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, drivers)

    # 4. Seed Trips
    trips = [
        (3, 2, 850, 'Medical Supplies & Coolers', 'Warehouse Central', 'Regional Hospital', 65.5, 'Dispatched', 450.00, 30935, 0, '2026-08-31 08:30:00', None),
        (1, 3, 9500, 'Industrial Machine Parts', 'Port Terminal 3', 'North Assembly Plant', 180.0, 'Completed', 1850.00, 45020, 45200, '2026-08-29 09:00:00', '2026-08-29 16:45:00'),
        (2, 1, 450, 'Electronics & Monitors', 'Distribution Hub', 'Tech Retail Park', 42.0, 'Completed', 380.00, 18358, 18400, '2026-08-28 10:00:00', '2026-08-28 13:30:00'),
        (5, 4, 35, 'Urgent Documents & Parcels', 'Financial District', 'City Legal Center', 8.5, 'Completed', 75.00, 2091, 2100, '2026-08-30 11:15:00', '2026-08-30 12:45:00'),
        (1, 3, 11000, 'Bulk Construction Cement', 'Quarry Site', 'Downtown Bridge Project', 95.0, 'Draft', 1200.00, 45200, 0, None, None),
    ]
    cursor.executemany("""
    INSERT INTO trips (vehicle_id, driver_id, cargo_weight, cargo_description, origin, destination, distance, status, revenue, start_odometer, end_odometer, start_time, end_time)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, trips)

    # 5. Seed Maintenance
    maintenance = [
        (4, '2026-08-25', 'Engine Transmission Overhaul', 'Heavy vibration reported during transit; gearbox inspection', 2450.00, 'Titan Truck Care', 'In Progress', '2026-09-10'),
        (1, '2026-07-15', 'Full Periodic Inspection & Oil Change', 'Replaced engine oil, brake pads, and cabin air filter', 480.00, 'FleetCare North', 'Completed', '2026-11-15'),
        (2, '2026-08-01', 'Tire Rotation & Wheel Alignment', 'All four tires balanced and rotated', 160.00, 'QuickFit Auto', 'Completed', '2026-12-01'),
        (6, '2026-06-20', 'Brake Fluid & Sensor Replacement', 'Replaced rear brake sensors and flushed fluid', 320.00, 'Metro Mechanics', 'Completed', '2026-10-20'),
    ]
    cursor.executemany("""
    INSERT INTO maintenance (vehicle_id, service_date, service_type, description, cost, vendor, status, next_service_date)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, maintenance)

    # 6. Seed Fuel Logs
    fuel_logs = [
        (1, 2, 75.0, 240.00, 45200, '2026-08-29'),
        (2, 3, 28.5, 92.00, 18400, '2026-08-28'),
        (3, 1, 35.0, 115.00, 30935, '2026-08-30'),
        (6, None, 45.0, 148.50, 52000, '2026-08-22'),
    ]
    cursor.executemany("""
    INSERT INTO fuel_logs (vehicle_id, trip_id, liters, cost, odometer, fuel_date)
    VALUES (?, ?, ?, ?, ?, ?)
    """, fuel_logs)

    # 7. Seed Expenses
    expenses = [
        (1, 2, 'Toll Fees', 45.00, 'Highway bridge toll passing North gate', '2026-08-29'),
        (2, 3, 'Parking & Permit', 20.00, 'City center commercial loading bay permit', '2026-08-28'),
        (3, 1, 'Cargo Insurance', 55.00, 'Temperature-sensitive medical shipment insurance', '2026-08-31'),
        (4, None, 'Annual Inspection Permit', 150.00, 'Commercial heavy vehicle state compliance stamp', '2026-08-10'),
    ]
    cursor.executemany("""
    INSERT INTO expenses (vehicle_id, trip_id, expense_type, amount, description, expense_date)
    VALUES (?, ?, ?, ?, ?, ?)
    """, expenses)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    seed_data()
    print("Seed data populated successfully.")
