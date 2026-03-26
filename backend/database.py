"""SQLite database setup and connection management."""

import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "qosina.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create all tables if they don't exist."""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS products (
                item_id TEXT PRIMARY KEY,
                product_name TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                connection_type TEXT,
                material TEXT,
                technical_detail TEXT,
                iso_compliance TEXT,
                manufacturing_environment TEXT DEFAULT 'ISO Class 8 / 100,000 / Grade D',
                shelf_life_months INTEGER,
                shelf_life_post_irradiation_months INTEGER,
                unit_price REAL,
                minimum_order_qty INTEGER DEFAULT 1,
                status TEXT DEFAULT 'active'
            );

            CREATE TABLE IF NOT EXISTS product_compatibility (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                part_a TEXT NOT NULL REFERENCES products(item_id),
                part_b TEXT NOT NULL REFERENCES products(item_id),
                compatibility_type TEXT NOT NULL,
                notes TEXT
            );

            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id TEXT NOT NULL REFERENCES products(item_id),
                lot_number TEXT NOT NULL,
                quantity_on_hand INTEGER NOT NULL,
                warehouse_location TEXT,
                received_date TEXT,
                expiration_date TEXT,
                reorder_point INTEGER DEFAULT 100,
                reorder_quantity INTEGER DEFAULT 500
            );

            CREATE TABLE IF NOT EXISTS customers (
                customer_id TEXT PRIMARY KEY,
                company_name TEXT NOT NULL,
                contact_name TEXT,
                industry TEXT,
                region TEXT,
                account_tier TEXT DEFAULT 'standard'
            );

            CREATE TABLE IF NOT EXISTS order_history (
                order_id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL REFERENCES customers(customer_id),
                item_id TEXT NOT NULL REFERENCES products(item_id),
                quantity INTEGER NOT NULL,
                order_date TEXT NOT NULL,
                unit_price REAL,
                total_price REAL
            );

            CREATE TABLE IF NOT EXISTS approval_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recommendation_type TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                source_query TEXT,
                status TEXT DEFAULT 'pending',
                ai_generated_at TEXT NOT NULL,
                reviewed_by TEXT,
                reviewed_at TEXT
            );
        """)
