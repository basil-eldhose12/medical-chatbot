import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "medical_chatbot.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

from werkzeug.security import generate_password_hash

import data

def init_db():
    """Initializes the database with necessary tables and seeds initial data."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Enable Foreign Keys
    cursor.execute("PRAGMA foreign_keys = ON")

    # --- Unified Case System ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL,
            specialist TEXT NOT NULL,
            severity TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS case_symptoms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            symptom TEXT NOT NULL,
            FOREIGN KEY (case_id) REFERENCES cases (id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS case_associations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            association TEXT NOT NULL,
            FOREIGN KEY (case_id) REFERENCES cases (id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS case_first_aid (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            step TEXT NOT NULL,
            FOREIGN KEY (case_id) REFERENCES cases (id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS normalization_map (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phrase TEXT NOT NULL UNIQUE,
            replacement TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_input TEXT,
            bot_response TEXT,
            urgency TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')

    # --- New Authentication & Appointment Tables ---
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL, -- ADMIN, PATIENT, HOSPITAL
            status TEXT DEFAULT 'PENDING' -- PENDING, APPROVED, REJECTED
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            hospital_id INTEGER NOT NULL,
            doctor_id INTEGER,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT DEFAULT 'PENDING',
            payment_status TEXT DEFAULT 'UNPAID',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES users (id),
            FOREIGN KEY (hospital_id) REFERENCES users (id),
            FOREIGN KEY (doctor_id) REFERENCES doctors (id)
        )
    ''')

    # --- Ensure doctors table exists (with unique constraint) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialization TEXT NOT NULL,
            hospital_id INTEGER NOT NULL,
            shift_start TEXT DEFAULT '09:00',
            shift_end TEXT DEFAULT '17:00',
            FOREIGN KEY (hospital_id) REFERENCES users (id),
            UNIQUE (name, specialization, hospital_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS booking_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            patient_id INTEGER,
            action TEXT NOT NULL,
            details TEXT,
            FOREIGN KEY (patient_id) REFERENCES users (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            appointment_id INTEGER UNIQUE,
            rating INTEGER CHECK(rating BETWEEN 1 AND 5),
            comment TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (appointment_id) REFERENCES appointments (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_id INTEGER NOT NULL UNIQUE,
            user_id INTEGER NOT NULL,
            amount INTEGER DEFAULT 200,
            transaction_id TEXT NOT NULL,
            method TEXT DEFAULT 'CARD',
            status TEXT DEFAULT 'SUCCESS',
            paid_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (appointment_id) REFERENCES appointments (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # --- Migration Checks (Must run after all tables are created) ---
    cursor.execute("PRAGMA table_info(appointments)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'doctor_id' not in columns:
        print("[MIGRATION] Adding doctor_id column to appointments table...")
        cursor.execute("ALTER TABLE appointments ADD COLUMN doctor_id INTEGER REFERENCES doctors(id)")
    if 'created_at' not in columns:
        print("[MIGRATION] Adding created_at column to appointments table...")
        cursor.execute("ALTER TABLE appointments ADD COLUMN created_at DATETIME DEFAULT '2026-03-18 00:00:00'")
    if 'payment_status' not in columns:
        print("[MIGRATION] Adding payment_status column to appointments table...")
        cursor.execute("ALTER TABLE appointments ADD COLUMN payment_status TEXT DEFAULT 'UNPAID'")
    if 'amount' not in columns:
        print("[MIGRATION] Adding amount column to appointments table...")
        cursor.execute("ALTER TABLE appointments ADD COLUMN amount INTEGER DEFAULT 200")
    if 'payment_id' not in columns:
        print("[MIGRATION] Adding payment_id column to appointments table...")
        cursor.execute("ALTER TABLE appointments ADD COLUMN payment_id TEXT")

    cursor.execute("PRAGMA table_info(booking_logs)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'patient_id' not in columns:
        print("[MIGRATION] Adding patient_id column to booking_logs table...")
        cursor.execute("ALTER TABLE booking_logs ADD COLUMN patient_id INTEGER REFERENCES users(id)")

    # --- New Registration Fields Migration ---
    cursor.execute("PRAGMA table_info(users)")
    user_columns = [col[1] for col in cursor.fetchall()]
    if 'email' not in user_columns:
        print("[MIGRATION] Adding email column to users table...")
        cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
    if 'phone' not in user_columns:
        print("[MIGRATION] Adding phone column to users table...")
        cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT")
    if 'dob' not in user_columns:
        print("[MIGRATION] Adding dob column to users table...")
        cursor.execute("ALTER TABLE users ADD COLUMN dob TEXT")
    if 'location' not in user_columns:
        print("[MIGRATION] Adding location column to users table...")
        cursor.execute("ALTER TABLE users ADD COLUMN location TEXT")

    # Add image_url column to doctors table
    cursor.execute("PRAGMA table_info(doctors)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'image_url' not in columns:
        print("[MIGRATION] Adding image_url column to doctors table...")
        cursor.execute("ALTER TABLE doctors ADD COLUMN image_url TEXT")

    # Feedback Table Migration (Allow NULL appointment_id and add user_id)
    cursor.execute("PRAGMA table_info(feedback)")
    feedback_cols = cursor.fetchall()
    feedback_col_names = [col[1] for col in feedback_cols]
    appointment_id_notnull = any(col[1] == 'appointment_id' and col[3] == 1 for col in feedback_cols)
    
    if 'user_id' not in feedback_col_names or appointment_id_notnull:
        print("[MIGRATION] Advanced migration for feedback table...")
        try:
            cursor.execute("ALTER TABLE feedback RENAME TO feedback_old")
            cursor.execute('''
                CREATE TABLE feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    appointment_id INTEGER UNIQUE,
                    rating INTEGER CHECK(rating BETWEEN 1 AND 5),
                    comment TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (appointment_id) REFERENCES appointments (id)
                )
            ''')
            # 3. Migrate data if possible
            cursor.execute("""
                INSERT INTO feedback (id, appointment_id, rating, comment, created_at, user_id)
                SELECT f.id, f.appointment_id, f.rating, f.comment, 
                       datetime('now'),
                       COALESCE((SELECT patient_id FROM appointments a WHERE a.id = f.appointment_id), 1)
                FROM feedback_old f
            """)
            cursor.execute("DROP TABLE feedback_old")
            print("[MIGRATION] Feedback table migrated successfully.")
        except Exception as e:
            print(f"[MIGRATION ERROR] Feedback migration failed: {e}")

    # Seed Admin if not exists (hashed)
    admin_pw = generate_password_hash("admin123")
    cursor.execute("INSERT OR IGNORE INTO admins (username, password) VALUES (?, ?)", ("admin", admin_pw))
    cursor.execute("INSERT OR IGNORE INTO users (username, password, role, status) VALUES (?, ?, ?, ?)", 
                   ("admin", admin_pw, "ADMIN", "APPROVED"))

    conn.commit()
    conn.close()
    
    # Clear and re-seed cases to ensure 50+ conditions are present
    reset_cases()

def reset_cases():
    """Clears all cases and seeds them fresh from data.py."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Clear existing data
    cursor.execute("DELETE FROM cases")
    cursor.execute("DELETE FROM case_symptoms")
    cursor.execute("DELETE FROM case_associations")
    cursor.execute("DELETE FROM case_first_aid")
    cursor.execute("DELETE FROM normalization_map")
    
    conn.commit()
    conn.close()
    seed_data()

def seed_data():
    """Seeds initial data from data.py into the database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Migrate Normalization Map
    for phrase, replacement in data.NORMALIZATION_MAP.items():
        cursor.execute("INSERT OR IGNORE INTO normalization_map (phrase, replacement) VALUES (?, ?)", 
                       (phrase.lower().strip(), replacement.lower().strip()))

    # 2. Helper to insert cases
    def insert_cases(case_list, domain):
        for case in case_list:
            cursor.execute(
                "INSERT INTO cases (domain, specialist, severity) VALUES (?, ?, ?)",
                (domain, case["specialist"], case["severity"])
            )
            case_id = cursor.lastrowid

            for symptom in case["symptoms"]:
                cursor.execute(
                    "INSERT INTO case_symptoms (case_id, symptom) VALUES (?, ?)",
                    (case_id, symptom.lower().strip())
                )

            for association in case["associations"]:
                cursor.execute(
                    "INSERT INTO case_associations (case_id, association) VALUES (?, ?)",
                    (case_id, association.strip())
                )

            if "first_aid" in case:
                for step in case["first_aid"]:
                    cursor.execute(
                        "INSERT INTO case_first_aid (case_id, step) VALUES (?, ?)",
                        (case_id, step.strip())
                    )

    # 3. Migrate all case categories
    insert_cases(data.EMERGENCY_CASES, "EMERGENCY")
    insert_cases(data.DIGESTIVE_CASES, "DIGESTIVE")
    insert_cases(data.RESPIRATORY_CASES, "RESPIRATORY")
    insert_cases(data.NEURO_CASES, "NEURO")
    insert_cases(data.CARDIOVASCULAR_CASES, "CARDIOVASCULAR")
    insert_cases(data.ENDOCRINE_CASES, "ENDOCRINE")
    insert_cases(data.GENERAL_CASES, "GENERAL")
    insert_cases(data.ENT_CASES, "ENT")
    insert_cases(data.ALLERGY_CASES, "ALLERGY")
    insert_cases(data.GENITOURINARY_CASES, "GENITOURINARY")
    insert_cases(data.MENTAL_HEALTH_CASES, "MENTAL_HEALTH")

    conn.commit()
    conn.close()

    # 4. Seed Doctors (Initial sample)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get some hospital IDs
    hospitals = cursor.execute("SELECT id FROM users WHERE role = 'HOSPITAL' AND status = 'APPROVED'").fetchall()
    if hospitals:
        hosp_id = hospitals[0]['id']
        sample_doctors = [
            ("Dr. Smith", "Cardiologist", hosp_id, "08:00", "14:00"),
            ("Dr. Jones", "Neurologist", hosp_id, "14:00", "20:00"),
            ("Dr. Taylor", "GP", hosp_id, "09:00", "17:00")
        ]
        for name, spec, hid, start, end in sample_doctors:
            cursor.execute("INSERT OR IGNORE INTO doctors (name, specialization, hospital_id, shift_start, shift_end) VALUES (?, ?, ?, ?, ?)",
                           (name, spec, hid, start, end))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized and seeded successfully.")
