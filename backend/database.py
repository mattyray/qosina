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
                structured_data TEXT,
                source_query TEXT,
                status TEXT DEFAULT 'pending',
                ai_generated_at TEXT NOT NULL,
                reviewed_by TEXT,
                reviewed_at TEXT
            );

            -- USE CASE 1: Sales Order Entry
            CREATE TABLE IF NOT EXISTS customer_pricing (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id TEXT NOT NULL REFERENCES customers(customer_id),
                item_id TEXT NOT NULL REFERENCES products(item_id),
                contracted_price REAL NOT NULL,
                discount_pct REAL DEFAULT 0,
                effective_date TEXT,
                expiry_date TEXT
            );

            -- USE CASE 2: AP Processing
            CREATE TABLE IF NOT EXISTS vendors (
                vendor_id TEXT PRIMARY KEY,
                vendor_name TEXT NOT NULL,
                contact_name TEXT,
                payment_terms TEXT DEFAULT 'Net 30',
                region TEXT
            );

            CREATE TABLE IF NOT EXISTS purchase_orders (
                po_number TEXT PRIMARY KEY,
                vendor_id TEXT NOT NULL REFERENCES vendors(vendor_id),
                order_date TEXT NOT NULL,
                expected_date TEXT,
                status TEXT DEFAULT 'confirmed',
                total_amount REAL
            );

            CREATE TABLE IF NOT EXISTS po_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                po_number TEXT NOT NULL REFERENCES purchase_orders(po_number),
                item_id TEXT NOT NULL REFERENCES products(item_id),
                quantity_ordered INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                line_total REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS receipts (
                receipt_id TEXT PRIMARY KEY,
                po_number TEXT NOT NULL REFERENCES purchase_orders(po_number),
                received_date TEXT NOT NULL,
                received_by TEXT
            );

            CREATE TABLE IF NOT EXISTS receipt_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_id TEXT NOT NULL REFERENCES receipts(receipt_id),
                item_id TEXT NOT NULL REFERENCES products(item_id),
                quantity_received INTEGER NOT NULL,
                lot_number TEXT
            );

            CREATE TABLE IF NOT EXISTS vendor_invoices (
                invoice_id TEXT PRIMARY KEY,
                vendor_id TEXT NOT NULL REFERENCES vendors(vendor_id),
                po_number TEXT REFERENCES purchase_orders(po_number),
                invoice_date TEXT NOT NULL,
                due_date TEXT NOT NULL,
                total_amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                match_status TEXT DEFAULT 'unmatched'
            );

            CREATE TABLE IF NOT EXISTS invoice_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id TEXT NOT NULL REFERENCES vendor_invoices(invoice_id),
                item_id TEXT NOT NULL REFERENCES products(item_id),
                quantity_invoiced INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                line_total REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS customer_invoices (
                invoice_id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL REFERENCES customers(customer_id),
                invoice_date TEXT NOT NULL,
                due_date TEXT NOT NULL,
                total_amount REAL NOT NULL,
                amount_paid REAL DEFAULT 0,
                status TEXT DEFAULT 'open'
            );

            CREATE TABLE IF NOT EXISTS payments (
                payment_id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL REFERENCES customers(customer_id),
                payment_date TEXT NOT NULL,
                amount REAL NOT NULL,
                reference TEXT,
                applied_to TEXT,
                status TEXT DEFAULT 'unapplied'
            );

            -- USE CASE 3: Product Data Entry
            CREATE TABLE IF NOT EXISTS product_extended (
                item_id TEXT PRIMARY KEY REFERENCES products(item_id),
                inner_diameter_mm REAL,
                outer_diameter_mm REAL,
                length_mm REAL,
                weight_g REAL,
                color TEXT,
                tolerance TEXT,
                sterilization_compatibility TEXT,
                biocompatibility TEXT,
                country_of_origin TEXT,
                supplier_part_number TEXT,
                tariff_code TEXT,
                units_per_case INTEGER,
                lead_time_days INTEGER,
                vendor_id TEXT
            );

            CREATE TABLE IF NOT EXISTS naming_conventions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                field_name TEXT NOT NULL,
                rule_type TEXT NOT NULL,
                pattern TEXT NOT NULL,
                example_correct TEXT,
                example_incorrect TEXT
            );
        """)
