from database.connection import get_db

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('Manager', 'Dispatcher', 'Safety Officer', 'Financial Analyst')),
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            model TEXT NOT NULL,
            license_plate TEXT UNIQUE NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('Truck', 'Van', 'Bike')),
            max_capacity REAL NOT NULL,
            odometer REAL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'Available' CHECK(status IN ('Available', 'On Trip', 'In Shop', 'Retired')),
            fuel_type TEXT DEFAULT 'Diesel',
            region TEXT DEFAULT 'Central',
            acquisition_cost REAL DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            license_number TEXT UNIQUE NOT NULL,
            license_category TEXT NOT NULL CHECK(license_category IN ('Truck', 'Van', 'Bike')),
            license_expiry DATE NOT NULL,
            safety_score REAL DEFAULT 100.0,
            duty_status TEXT NOT NULL DEFAULT 'Available' CHECK(duty_status IN ('Available', 'On Trip', 'Off Duty', 'Suspended')),
            phone TEXT,
            email TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL REFERENCES vehicles(id),
            driver_id INTEGER NOT NULL REFERENCES drivers(id),
            cargo_weight REAL NOT NULL,
            cargo_description TEXT,
            origin TEXT NOT NULL,
            destination TEXT NOT NULL,
            distance REAL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'Draft' CHECK(status IN ('Draft', 'Dispatched', 'Completed', 'Cancelled')),
            revenue REAL DEFAULT 0,
            start_odometer REAL,
            end_odometer REAL,
            start_time DATETIME,
            end_time DATETIME,
            created_by INTEGER REFERENCES users(id),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS maintenance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL REFERENCES vehicles(id),
            service_date DATE NOT NULL,
            service_type TEXT NOT NULL,
            description TEXT,
            cost REAL NOT NULL,
            vendor TEXT,
            status TEXT NOT NULL DEFAULT 'In Progress' CHECK(status IN ('In Progress', 'Completed', 'Cancelled')),
            next_service_date DATE,
            created_by INTEGER REFERENCES users(id),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS fuel_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL REFERENCES vehicles(id),
            trip_id INTEGER REFERENCES trips(id),
            fuel_date DATE NOT NULL,
            liters REAL NOT NULL,
            cost_per_liter REAL NOT NULL,
            total_cost REAL NOT NULL,
            odometer_reading REAL NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL REFERENCES vehicles(id),
            trip_id INTEGER REFERENCES trips(id),
            expense_date DATE NOT NULL,
            category TEXT NOT NULL CHECK(category IN ('Fuel', 'Tolls', 'Insurance', 'Permits', 'Driver Allowance', 'Other')),
            amount REAL NOT NULL,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS password_resets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            otp_hash TEXT NOT NULL,
            expires_at DATETIME NOT NULL,
            attempts_count INTEGER DEFAULT 0,
            is_used INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    conn.commit()
    conn.close()
    print("Database tables created successfully!")

if __name__ == '__main__':
    init_db()
