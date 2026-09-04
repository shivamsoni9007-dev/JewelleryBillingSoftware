import sqlite3

DATABASE = "jewellery.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    conn = get_db_connection()

    # Customers
    conn.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            mobile TEXT,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Bills
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_no TEXT UNIQUE NOT NULL,
            customer_name TEXT,
            customer_mobile TEXT,
            subtotal REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            gst REAL DEFAULT 0,
            grand_total REAL DEFAULT 0,
            payment_mode TEXT,
            amount_paid REAL DEFAULT 0,
            balance REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Bill Items
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bill_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_id INTEGER NOT NULL,
            item_name TEXT,
            purity TEXT,
            gross_weight REAL DEFAULT 0,
            stone_weight REAL DEFAULT 0,
            net_weight REAL DEFAULT 0,
            rate REAL DEFAULT 0,
            making REAL DEFAULT 0,
            amount REAL DEFAULT 0,
            FOREIGN KEY (bill_id) REFERENCES bills(id)
        )
    """)

    # Rates
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metal TEXT NOT NULL,
            purity TEXT,
            rate REAL DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Payment History
    conn.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_id INTEGER NOT NULL,
            customer_mobile TEXT,
            amount REAL DEFAULT 0,
            payment_mode TEXT,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (bill_id) REFERENCES bills(id)
        )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Database updated successfully!")