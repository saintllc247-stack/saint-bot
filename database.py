import sqlite3
import os
from datetime import datetime


class Database:
    def __init__(self, db_path: str):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT DEFAULT '',
                game_id TEXT NOT NULL,
                server TEXT NOT NULL,
                package_name TEXT NOT NULL,
                diamonds INTEGER NOT NULL,
                price INTEGER NOT NULL,
                status TEXT DEFAULT 'new',
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_order_id ON orders(order_id)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id)")
        self.conn.commit()

    def create_order(self, user_id: int, username: str, game_id: str,
                     server: str, package_name: str, diamonds: int,
                     price: int) -> dict:
        order_id = f"SAINT-{user_id}-{datetime.now().strftime('%d%m%H%M%S%f')}"
        cur = self.conn.execute("""
            INSERT INTO orders (order_id, user_id, username, game_id, server,
                                package_name, diamonds, price, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'new')
        """, (order_id, user_id, username, game_id, server,
              package_name, diamonds, price))
        self.conn.commit()
        return self.get_order(cur.lastrowid)

    def get_order(self, order_id: int) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM orders WHERE id = ?", (order_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_order_by_order_id(self, order_id: str) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM orders WHERE order_id = ?", (order_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_latest_order(self, user_id: int) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user_id,)
        ).fetchone()
        return dict(row) if row else None

    def update_status(self, order_id: int, status: str):
        self.conn.execute("""
            UPDATE orders SET status = ?, updated_at = datetime('now')
            WHERE id = ?
        """, (status, order_id))
        self.conn.commit()

    def close(self):
        self.conn.close()
