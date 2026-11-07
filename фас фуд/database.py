import sqlite3

def init_db():
    conn = sqlite3.connect("restaurant.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            user_name TEXT,
            phone TEXT,
            items_text TEXT,
            total_price INTEGER,
            status TEXT DEFAULT 'В обработке'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )
    ''')
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect("restaurant.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect("restaurant.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

def add_order(user_id, user_name, phone, items_text, total_price):
    conn = sqlite3.connect("restaurant.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO orders (user_id, user_name, phone, items_text, total_price) VALUES (?, ?, ?, ?, ?)",
        (user_id, user_name, phone, items_text, total_price)
    )
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return order_id

def update_status(order_id, status):
    conn = sqlite3.connect("restaurant.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    conn.commit()
    conn.close()