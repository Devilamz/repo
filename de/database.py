"""
Database Module for Inventory Management System
Handles all SQLite operations with proper error handling
"""

import sqlite3
from typing import List, Dict, Optional
import os

# Get the directory where this file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_NAME = os.path.join(BASE_DIR, "inventory.db")


def get_connection():
    """Create a database connection with proper settings"""
    conn = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Allow column access by name
    return conn


def init_db():
    """
    Initialize the database and create the products table if it doesn't exist.
    This function is safe to call multiple times.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Create shops table (Master)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shops (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    shop_code TEXT UNIQUE NOT NULL,
                    shop_name TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create customers table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_code TEXT UNIQUE NOT NULL,
                    customer_name TEXT NOT NULL,
                    address TEXT,
                    phone TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create products table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    Code TEXT PRIMARY KEY,
                    Product_Name TEXT NOT NULL,
                    Receive_Round_1 INTEGER DEFAULT 0,
                    Receive_Round_2 INTEGER DEFAULT 0,
                    Receive_Round_3 INTEGER DEFAULT 0,
                    Shop_1 INTEGER DEFAULT 0,
                    Shop_2 INTEGER DEFAULT 0,
                    Shop_3 INTEGER DEFAULT 0,
                    Shop_4 INTEGER DEFAULT 0,
                    Shop_5 INTEGER DEFAULT 0,
                    Shop_6 INTEGER DEFAULT 0,
                    Small_Units_Per_Big INTEGER DEFAULT 1,
                    Cost_Price_Small REAL DEFAULT 0.0,
                    Sell_Price_Small REAL DEFAULT 0.0,
                    -- New fields for product images and notes
                    Image_Path TEXT,
                    Notes TEXT
                )
            """)
            
            # Create delivery_rounds table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS delivery_rounds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    round_name TEXT NOT NULL,
                    delivery_date TEXT,
                    week_number INTEGER,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create inventory_by_round table (สินค้าแยกตามรอบ)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventory_by_round (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_code TEXT NOT NULL,
                    round_id INTEGER NOT NULL,
                    quantity_received INTEGER DEFAULT 0,
                    shop_1 INTEGER DEFAULT 0,
                    shop_2 INTEGER DEFAULT 0,
                    shop_3 INTEGER DEFAULT 0,
                    shop_4 INTEGER DEFAULT 0,
                    shop_5 INTEGER DEFAULT 0,
                    shop_6 INTEGER DEFAULT 0,
                    FOREIGN KEY (product_code) REFERENCES products(Code),
                    FOREIGN KEY (round_id) REFERENCES delivery_rounds(id),
                    UNIQUE(product_code, round_id)
                )
            """)
            
            # Create shop_distribution table (การจ่ายสินค้าไปร้านแบบ Dynamic)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shop_distribution (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_code TEXT NOT NULL,
                    round_id INTEGER NOT NULL,
                    shop_id INTEGER NOT NULL,
                    quantity INTEGER DEFAULT 0,
                    FOREIGN KEY (product_code) REFERENCES products(Code),
                    FOREIGN KEY (round_id) REFERENCES delivery_rounds(id),
                    FOREIGN KEY (shop_id) REFERENCES shops(id),
                    UNIQUE(product_code, round_id, shop_id)
                )
            """)
            
            # Create orders and order items for customer orders per round
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_code TEXT UNIQUE,
                    round_id INTEGER,
                    shop_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'draft',
                    notes TEXT,
                    FOREIGN KEY (round_id) REFERENCES delivery_rounds(id),
                    FOREIGN KEY (shop_id) REFERENCES shops(id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    product_code TEXT NOT NULL,
                    quantity INTEGER DEFAULT 0,
                    price_per_small REAL DEFAULT 0.0,
                    FOREIGN KEY (order_id) REFERENCES orders(id),
                    FOREIGN KEY (product_code) REFERENCES products(Code)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS receipts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    round_id INTEGER NOT NULL,
                    receive_number INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (round_id) REFERENCES delivery_rounds(id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS receipt_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    receipt_id INTEGER NOT NULL,
                    product_code TEXT NOT NULL,
                    quantity INTEGER DEFAULT 0,
                    FOREIGN KEY (receipt_id) REFERENCES receipts(id),
                    FOREIGN KEY (product_code) REFERENCES products(Code)
                )
            """)

            conn.commit()
            # Ensure backward compatible schema updates for existing databases
            try:
                # Ensure product columns
                cursor.execute("PRAGMA table_info(products)")
                existing_cols = [r[1] for r in cursor.fetchall()]
                if "Image_Path" not in existing_cols:
                    cursor.execute("ALTER TABLE products ADD COLUMN Image_Path TEXT")
                if "Notes" not in existing_cols:
                    cursor.execute("ALTER TABLE products ADD COLUMN Notes TEXT")

                # Ensure shops have address and phone
                cursor.execute("PRAGMA table_info(shops)")
                shop_cols = [r[1] for r in cursor.fetchall()]
                if "address" not in shop_cols:
                    cursor.execute("ALTER TABLE shops ADD COLUMN address TEXT")
                if "phone" not in shop_cols:
                    cursor.execute("ALTER TABLE shops ADD COLUMN phone TEXT")

                # Ensure customers table has expected columns if it existed without them
                cursor.execute("PRAGMA table_info(customers)")
                cust_cols = [r[1] for r in cursor.fetchall()]
                if cust_cols and "address" not in cust_cols:
                    cursor.execute("ALTER TABLE customers ADD COLUMN address TEXT")
                if cust_cols and "phone" not in cust_cols:
                    cursor.execute("ALTER TABLE customers ADD COLUMN phone TEXT")

                conn.commit()
            except Exception:
                # If PRAGMA or ALTER fails for any reason, continue silently
                pass

            print("✅ Database initialized successfully!")
            return True
    except sqlite3.Error as e:
        print(f"❌ Database initialization error: {e}")
        return False


def add_product(
    code: str,
    product_name: str,
    small_units_per_big: int = 1,
    cost_price_small: float = 0.0,
    sell_price_small: float = 0.0,
    image_path: str = None,
    notes: str = None
) -> bool:
    """
    Add a new product to the database.
    
    Args:
        code: Product code (Primary Key)
        product_name: Product name
        small_units_per_big: Conversion rate (big to small units)
        cost_price_small: Cost per small unit
        sell_price_small: Selling price per small unit
        image_path: Optional path to product image
        notes: Optional product notes
    
    Returns:
        True if successful, False otherwise
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO products (
                    Code, Product_Name, Small_Units_Per_Big, 
                    Cost_Price_Small, Sell_Price_Small, Image_Path, Notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (code, product_name, small_units_per_big, cost_price_small, sell_price_small, image_path, notes))
            conn.commit()
            print(f"✅ Product '{product_name}' added successfully!")
            return True
    except sqlite3.IntegrityError:
        print(f"❌ Product with code '{code}' already exists!")
        return False
    except sqlite3.Error as e:
        print(f"❌ Error adding product: {e}")
        return False


def update_product(code: str, updates: Dict) -> bool:
    """
    Update a product's information.
    
    Args:
        code: Product code to update
        updates: Dictionary with column names as keys and new values
    
    Returns:
        True if successful, False otherwise
    """
    if not updates:
        return False
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Build dynamic UPDATE query
            set_clause = ", ".join([f"{col} = ?" for col in updates.keys()])
            values = list(updates.values()) + [code]
            
            query = f"UPDATE products SET {set_clause} WHERE Code = ?"
            cursor.execute(query, values)
            conn.commit()
            
            if cursor.rowcount > 0:
                print(f"✅ Product '{code}' updated successfully!")
                return True
            else:
                print(f"⚠️ Product '{code}' not found!")
                return False
    except sqlite3.Error as e:
        print(f"❌ Error updating product: {e}")
        return False


def get_all_products() -> List[Dict]:
    """
    Retrieve all products from the database.
    
    Returns:
        List of dictionaries containing product data
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products ORDER BY Code")
            rows = cursor.fetchall()
            
            # Convert rows to list of dictionaries
            products = []
            for row in rows:
                products.append({
                    "Code": row["Code"],
                    "Product_Name": row["Product_Name"],
                    "Receive_Round_1": row["Receive_Round_1"],
                    "Receive_Round_2": row["Receive_Round_2"],
                    "Receive_Round_3": row["Receive_Round_3"],
                    "Shop_1": row["Shop_1"],
                    "Shop_2": row["Shop_2"],
                    "Shop_3": row["Shop_3"],
                    "Shop_4": row["Shop_4"],
                    "Shop_5": row["Shop_5"],
                    "Shop_6": row["Shop_6"],
                    "Small_Units_Per_Big": row["Small_Units_Per_Big"],
                    "Cost_Price_Small": row["Cost_Price_Small"],
                    "Sell_Price_Small": row["Sell_Price_Small"],
                    "Image_Path": row["Image_Path"] if "Image_Path" in row.keys() else None,
                    "Notes": row["Notes"] if "Notes" in row.keys() else None
                })
            return products
    except sqlite3.Error as e:
        print(f"❌ Error retrieving products: {e}")
        return []


def delete_product(code: str) -> bool:
    """
    Delete a product from the database.
    
    Args:
        code: Product code to delete
    
    Returns:
        True if successful, False otherwise
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products WHERE Code = ?", (code,))
            conn.commit()
            
            if cursor.rowcount > 0:
                print(f"✅ Product '{code}' deleted successfully!")
                return True
            else:
                print(f"⚠️ Product '{code}' not found!")
                return False
    except sqlite3.Error as e:
        print(f"❌ Error deleting product: {e}")
        return False


def bulk_update_products(products_data: List[Dict]) -> bool:
    """
    Update multiple products at once (useful for st.data_editor).
    
    Args:
        products_data: List of product dictionaries with updated values
    
    Returns:
        True if successful, False otherwise
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            for product in products_data:
                code = product.get("Code")
                if not code:
                    continue
                
                # Remove Code from updates
                updates = {k: v for k, v in product.items() if k != "Code"}
                
                # Build UPDATE query
                set_clause = ", ".join([f"{col} = ?" for col in updates.keys()])
                values = list(updates.values()) + [code]
                
                query = f"UPDATE products SET {set_clause} WHERE Code = ?"
                cursor.execute(query, values)
            
            conn.commit()
            print(f"✅ {len(products_data)} products updated successfully!")
            return True
    except sqlite3.Error as e:
        print(f"❌ Error bulk updating products: {e}")
        return False


# ==================== Delivery Rounds Functions ====================

def add_delivery_round(round_name: str, delivery_date: str = None, week_number: int = None, description: str = None) -> int:
    """
    Add a new delivery round.
    
    Returns:
        round_id if successful, None otherwise
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO delivery_rounds (round_name, delivery_date, week_number, description)
                VALUES (?, ?, ?, ?)
            """, (round_name, delivery_date, week_number, description))
            conn.commit()
            print(f"✅ Delivery round '{round_name}' added successfully!")
            return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"❌ Error adding delivery round: {e}")
        return None


def get_all_delivery_rounds() -> List[Dict]:
    """Get all delivery rounds."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM delivery_rounds ORDER BY id DESC")
            rows = cursor.fetchall()
            
            rounds = []
            for row in rows:
                rounds.append({
                    "id": row["id"],
                    "round_name": row["round_name"],
                    "delivery_date": row["delivery_date"],
                    "week_number": row["week_number"],
                    "description": row["description"]
                })
            return rounds
    except sqlite3.Error as e:
        print(f"❌ Error retrieving delivery rounds: {e}")
        return []


def delete_delivery_round(round_id: int) -> bool:
    """Delete a delivery round and its inventory records."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            # Delete inventory records first
            cursor.execute("DELETE FROM inventory_by_round WHERE round_id = ?", (round_id,))
            # Delete round
            cursor.execute("DELETE FROM delivery_rounds WHERE id = ?", (round_id,))
            conn.commit()
            print(f"✅ Delivery round deleted successfully!")
            return True
    except sqlite3.Error as e:
        print(f"❌ Error deleting delivery round: {e}")
        return False


# ==================== Inventory By Round Functions ====================

def update_inventory_by_round(product_code: str, round_id: int, updates: Dict) -> bool:
    """
    Update inventory for a specific product in a specific round.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if record exists
            cursor.execute("""
                SELECT id FROM inventory_by_round 
                WHERE product_code = ? AND round_id = ?
            """, (product_code, round_id))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                set_clause = ", ".join([f"{col} = ?" for col in updates.keys()])
                values = list(updates.values()) + [product_code, round_id]
                query = f"UPDATE inventory_by_round SET {set_clause} WHERE product_code = ? AND round_id = ?"
                cursor.execute(query, values)
            else:
                # Insert new record
                columns = ["product_code", "round_id"] + list(updates.keys())
                placeholders = ", ".join(["?"] * len(columns))
                values = [product_code, round_id] + list(updates.values())
                query = f"INSERT INTO inventory_by_round ({', '.join(columns)}) VALUES ({placeholders})"
                cursor.execute(query, values)
            
            conn.commit()
            return True
    except sqlite3.Error as e:
        print(f"❌ Error updating inventory by round: {e}")
        return False


def get_inventory_by_round(round_id: int) -> List[Dict]:
    """Get all inventory records for a specific round."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    i.*,
                    p.Product_Name,
                    p.Small_Units_Per_Big,
                    p.Cost_Price_Small,
                    p.Sell_Price_Small
                FROM inventory_by_round i
                JOIN products p ON i.product_code = p.Code
                WHERE i.round_id = ?
                ORDER BY i.product_code
            """, (round_id,))
            rows = cursor.fetchall()
            
            inventory = []
            for row in rows:
                inventory.append({
                    "id": row["id"],
                    "product_code": row["product_code"],
                    "Product_Name": row["Product_Name"],
                    "round_id": row["round_id"],
                    "quantity_received": row["quantity_received"],
                    "shop_1": row["shop_1"],
                    "shop_2": row["shop_2"],
                    "shop_3": row["shop_3"],
                    "shop_4": row["shop_4"],
                    "shop_5": row["shop_5"],
                    "shop_6": row["shop_6"],
                    "Small_Units_Per_Big": row["Small_Units_Per_Big"],
                    "Cost_Price_Small": row["Cost_Price_Small"],
                    "Sell_Price_Small": row["Sell_Price_Small"]
                })
            return inventory
    except sqlite3.Error as e:
        print(f"❌ Error retrieving inventory by round: {e}")
        return []


def bulk_update_inventory_by_round(round_id: int, inventory_data: List[Dict]) -> bool:
    """Bulk update inventory for a specific round."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            for item in inventory_data:
                product_code = item.get("product_code")
                if not product_code:
                    continue
                
                # Remove non-update fields
                updates = {k: v for k, v in item.items() 
                          if k not in ["id", "product_code", "round_id", "Product_Name", 
                                      "Small_Units_Per_Big", "Cost_Price_Small", "Sell_Price_Small"]}
                
                # Check if record exists
                cursor.execute("""
                    SELECT id FROM inventory_by_round 
                    WHERE product_code = ? AND round_id = ?
                """, (product_code, round_id))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Update
                    set_clause = ", ".join([f"{col} = ?" for col in updates.keys()])
                    values = list(updates.values()) + [product_code, round_id]
                    query = f"UPDATE inventory_by_round SET {set_clause} WHERE product_code = ? AND round_id = ?"
                    cursor.execute(query, values)
                else:
                    # Insert
                    columns = ["product_code", "round_id"] + list(updates.keys())
                    placeholders = ", ".join(["?"] * len(columns))
                    values = [product_code, round_id] + list(updates.values())
                    query = f"INSERT INTO inventory_by_round ({', '.join(columns)}) VALUES ({placeholders})"
                    cursor.execute(query, values)
            
            conn.commit()
            print(f"✅ Inventory by round updated successfully!")
            return True
    except sqlite3.Error as e:
        print(f"❌ Error bulk updating inventory by round: {e}")
        return False


# ==================== SHOP DISTRIBUTION FUNCTIONS ====================

def update_shop_distribution(product_code: str, round_id: int, shop_id: int, quantity: int) -> bool:
    """
    Update quantity distributed to a specific shop for a product in a round.
    
    Args:
        product_code: Product code
        round_id: Delivery round ID
        shop_id: Shop ID
        quantity: Quantity to distribute
    
    Returns:
        True if successful, False otherwise
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if record exists
            cursor.execute("""
                SELECT id FROM shop_distribution 
                WHERE product_code = ? AND round_id = ? AND shop_id = ?
            """, (product_code, round_id, shop_id))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update
                cursor.execute("""
                    UPDATE shop_distribution 
                    SET quantity = ? 
                    WHERE product_code = ? AND round_id = ? AND shop_id = ?
                """, (quantity, product_code, round_id, shop_id))
            else:
                # Insert
                cursor.execute("""
                    INSERT INTO shop_distribution (product_code, round_id, shop_id, quantity)
                    VALUES (?, ?, ?, ?)
                """, (product_code, round_id, shop_id, quantity))
            
            conn.commit()
            return True
    except sqlite3.Error as e:
        print(f"❌ Error updating shop distribution: {e}")
        return False


def get_shop_distribution_by_round(round_id: int) -> List[Dict]:
    """
    Get all shop distributions for a specific round.
    Returns data in a format suitable for display.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Get all products
            cursor.execute("SELECT Code, Product_Name, Small_Units_Per_Big, Cost_Price_Small, Sell_Price_Small FROM products ORDER BY Code")
            products = cursor.fetchall()
            
            # Get all active shops
            cursor.execute("SELECT id, shop_code, shop_name FROM shops WHERE is_active = 1 ORDER BY shop_code")
            shops = cursor.fetchall()
            
            result = []
            for product in products:
                product_code = product["Code"]
                row = {
                    "product_code": product_code,
                    "Product_Name": product["Product_Name"],
                    "Small_Units_Per_Big": product["Small_Units_Per_Big"],
                    "Cost_Price_Small": product["Cost_Price_Small"],
                    "Sell_Price_Small": product["Sell_Price_Small"]
                }
                
                # Get quantity received
                cursor.execute("""
                    SELECT quantity_received FROM inventory_by_round
                    WHERE product_code = ? AND round_id = ?
                """, (product_code, round_id))
                received = cursor.fetchone()
                row["quantity_received"] = received["quantity_received"] if received else 0
                
                # Get distribution for each shop
                for shop in shops:
                    shop_id = shop["id"]
                    shop_code = shop["shop_code"]
                    
                    cursor.execute("""
                        SELECT quantity FROM shop_distribution
                        WHERE product_code = ? AND round_id = ? AND shop_id = ?
                    """, (product_code, round_id, shop_id))
                    
                    dist = cursor.fetchone()
                    row[f"shop_{shop_id}"] = dist["quantity"] if dist else 0
                    row[f"shop_{shop_id}_name"] = f"{shop_code} - {shop['shop_name']}"
                
                result.append(row)
            
            return result
    except sqlite3.Error as e:
        print(f"❌ Error getting shop distribution: {e}")
        return []


def bulk_update_shop_distribution(round_id: int, distribution_data: List[Dict]) -> bool:
    """
    Bulk update shop distribution for multiple products.
    
    Args:
        round_id: Delivery round ID
        distribution_data: List of dictionaries with product_code and shop quantities
    
    Returns:
        True if successful, False otherwise
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Get all shop IDs
            cursor.execute("SELECT id FROM shops WHERE is_active = 1")
            shop_ids = [row["id"] for row in cursor.fetchall()]
            
            for item in distribution_data:
                product_code = item.get("product_code")
                if not product_code:
                    continue
                
                # Update quantity_received in inventory_by_round
                quantity_received = item.get("quantity_received", 0)
                cursor.execute("""
                    SELECT id FROM inventory_by_round 
                    WHERE product_code = ? AND round_id = ?
                """, (product_code, round_id))
                
                if cursor.fetchone():
                    cursor.execute("""
                        UPDATE inventory_by_round 
                        SET quantity_received = ? 
                        WHERE product_code = ? AND round_id = ?
                    """, (quantity_received, product_code, round_id))
                else:
                    cursor.execute("""
                        INSERT INTO inventory_by_round (product_code, round_id, quantity_received)
                        VALUES (?, ?, ?)
                    """, (product_code, round_id, quantity_received))
                
                # Update distribution for each shop
                for shop_id in shop_ids:
                    shop_key = f"shop_{shop_id}"
                    if shop_key in item:
                        quantity = item[shop_key]
                        update_shop_distribution(product_code, round_id, shop_id, quantity)
            
            conn.commit()
            print(f"✅ Shop distribution updated successfully!")
            return True
    except sqlite3.Error as e:
        print(f"❌ Error bulk updating shop distribution: {e}")
        return False


# ==================== ORDER AGGREGATION HELPERS ====================

def get_order_summary_by_round(round_id: int) -> List[Dict]:
    """Return aggregated ordered quantities per product per shop for a specific round.

    Returns a list of dicts: {
        'product_code': ..., 'Product_Name': ..., 'total_ordered': ..., 'shop_{shop_id}': qty, ...
    }
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            # Get list of relevant shops
            cursor.execute("SELECT id, shop_code, shop_name FROM shops WHERE is_active = 1 ORDER BY shop_code")
            shops = cursor.fetchall()
            shop_ids = [s['id'] for s in shops]

            # Aggregate orders
            cursor.execute("""
                SELECT oi.product_code, o.shop_id, SUM(oi.quantity) as qty
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                WHERE o.round_id = ?
                GROUP BY oi.product_code, o.shop_id
            """, (round_id,))
            rows = cursor.fetchall()

            # Build map
            summary_map = {}
            for row in rows:
                pc = row['product_code']
                shop_id = row['shop_id']
                qty = row['qty'] or 0
                if pc not in summary_map:
                    # fetch product name
                    cursor.execute("SELECT Product_Name FROM products WHERE Code = ?", (pc,))
                    pr = cursor.fetchone()
                    summary_map[pc] = {
                        'product_code': pc,
                        'Product_Name': pr['Product_Name'] if pr else '',
                        'total_ordered': 0
                    }
                    for sid in shop_ids:
                        summary_map[pc][f'shop_{sid}'] = 0

                summary_map[pc][f'shop_{shop_id}'] = qty
                summary_map[pc]['total_ordered'] += qty

            return list(summary_map.values())
    except sqlite3.Error as e:
        print(f"❌ Error aggregating orders: {e}")
        return []


def get_shop_allocations_by_round(round_id: int) -> List[Dict]:
    """Return allocation per shop for a round based on shop_distribution.

    Returns list of dicts: {'shop_id','shop_code','shop_name','items': [{'product_code','product_name','quantity'}...]}
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, shop_code, shop_name FROM shops WHERE is_active = 1 ORDER BY shop_code")
            shops = cursor.fetchall()
            result = []
            for s in shops:
                sid = s['id']
                cursor.execute("""
                    SELECT sd.product_code, SUM(sd.quantity) as quantity, p.Product_Name
                    FROM shop_distribution sd
                    LEFT JOIN products p ON sd.product_code = p.Code
                    WHERE sd.round_id = ? AND sd.shop_id = ? AND sd.quantity > 0
                    GROUP BY sd.product_code
                """, (round_id, sid))
                rows = cursor.fetchall()
                items = []
                for r in rows:
                    items.append({
                        'product_code': r['product_code'],
                        'product_name': r['Product_Name'],
                        'quantity': r['quantity']
                    })
                if items:
                    result.append({
                        'shop_id': sid,
                        'shop_code': s['shop_code'],
                        'shop_name': s['shop_name'],
                        'items': items
                    })
            return result
    except sqlite3.Error as e:
        print(f"❌ Error getting shop allocations: {e}")
        return []


# ==================== ORDER FUNCTIONS ====================

def create_order(round_id: int, shop_id: int, order_code: str = None, notes: str = None) -> Optional[int]:
    """Create an order master record and return its ID."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO orders (order_code, round_id, shop_id, notes)
                VALUES (?, ?, ?, ?)
            """, (order_code, round_id, shop_id, notes))
            conn.commit()
            return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"❌ Error creating order: {e}")
        return None


def add_order_item(order_id: int, product_code: str, quantity: int, price_per_small: float = 0.0) -> bool:
    """Add an item to an order."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO order_items (order_id, product_code, quantity, price_per_small)
                VALUES (?, ?, ?, ?)
            """, (order_id, product_code, quantity, price_per_small))
            conn.commit()
            return True
    except sqlite3.Error as e:
        print(f"❌ Error adding order item: {e}")
        return False


def get_orders_by_round(round_id: int) -> List[Dict]:
    """Get all orders for a specific round with basic shop info."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT o.*, s.shop_code, s.shop_name
                FROM orders o
                LEFT JOIN shops s ON o.shop_id = s.id
                WHERE o.round_id = ?
                ORDER BY o.id DESC
            """, (round_id,))
            rows = cursor.fetchall()
            orders = []
            for row in rows:
                orders.append({
                    "id": row["id"],
                    "order_code": row["order_code"],
                    "round_id": row["round_id"],
                    "shop_id": row["shop_id"],
                    "shop_code": row["shop_code"] if "shop_code" in row.keys() else None,
                    "shop_name": row["shop_name"] if "shop_name" in row.keys() else None,
                    "created_at": row["created_at"] if "created_at" in row.keys() else None,
                    "status": row["status"] if "status" in row.keys() else None,
                    "notes": row["notes"] if "notes" in row.keys() else None
                })
            return orders
    except sqlite3.Error as e:
        print(f"❌ Error retrieving orders: {e}")
        return []


def get_order_items(order_id: int) -> List[Dict]:
    """Get items for a specific order."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT oi.*, p.Product_Name
                FROM order_items oi
                LEFT JOIN products p ON oi.product_code = p.Code
                WHERE oi.order_id = ?
            """, (order_id,))
            rows = cursor.fetchall()
            items = []
            for row in rows:
                items.append({
                    "id": row["id"],
                    "product_code": row["product_code"],
                    "product_name": row.get("Product_Name"),
                    "quantity": row["quantity"],
                    "price_per_small": row.get("price_per_small")
                })
            return items
    except sqlite3.Error as e:
        print(f"❌ Error retrieving order items: {e}")
        return []


def get_round_financials(round_id: int) -> Dict:
    """Calculate total cost, revenue and profit for a delivery round based on actual distributed quantities."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sd.product_code, SUM(sd.quantity) as total_qty, p.Cost_Price_Small, p.Sell_Price_Small
                FROM shop_distribution sd
                JOIN products p ON sd.product_code = p.Code
                WHERE sd.round_id = ?
                GROUP BY sd.product_code
            """, (round_id,))
            rows = cursor.fetchall()

            total_cost = 0.0
            total_revenue = 0.0
            details = []
            for row in rows:
                qty = row["total_qty"]
                cost = (row["Cost_Price_Small"] or 0.0) * qty
                rev = (row["Sell_Price_Small"] or 0.0) * qty
                total_cost += cost
                total_revenue += rev
                details.append({
                    "product_code": row["product_code"],
                    "quantity": qty,
                    "cost": cost,
                    "revenue": rev,
                    "profit": rev - cost
                })

            return {
                "round_id": round_id,
                "total_cost": total_cost,
                "total_revenue": total_revenue,
                "total_profit": total_revenue - total_cost,
                "details": details
            }
    except sqlite3.Error as e:
        print(f"❌ Error calculating financials: {e}")
        return {"round_id": round_id, "total_cost": 0.0, "total_revenue": 0.0, "total_profit": 0.0, "details": []}


# ==================== RECEIPT / RECEIVE GOODS FUNCTIONS ====================

def create_receipt(round_id: int, receive_number: int = None, notes: str = None) -> Optional[int]:
    """Create a receipt (a receiving session) for a round and return its ID."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            if receive_number is None:
                cursor.execute("SELECT MAX(receive_number) as mx FROM receipts WHERE round_id = ?", (round_id,))
                row = cursor.fetchone()
                receive_number = (row["mx"] or 0) + 1
            cursor.execute("""
                INSERT INTO receipts (round_id, receive_number, notes)
                VALUES (?, ?, ?)
            """, (round_id, receive_number, notes))
            conn.commit()
            return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"❌ Error creating receipt: {e}")
        return None


def add_receipt_item(receipt_id: int, product_code: str, quantity: int) -> bool:
    """Add an item to a receipt and update inventory totals for its round."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO receipt_items (receipt_id, product_code, quantity)
                VALUES (?, ?, ?)
            """, (receipt_id, product_code, quantity))
            conn.commit()

            # Get round_id for this receipt
            cursor.execute("SELECT round_id FROM receipts WHERE id = ?", (receipt_id,))
            row = cursor.fetchone()
            if row:
                round_id = row["round_id"]
                _recalculate_inventory_for_product(round_id, product_code)
            return True
    except sqlite3.Error as e:
        print(f"❌ Error adding receipt item: {e}")
        return False


def _recalculate_inventory_for_product(round_id: int, product_code: str) -> None:
    """Recalculate the total received quantity for a product in a round from receipts and update inventory_by_round."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT SUM(ri.quantity) as total_received
                FROM receipt_items ri
                JOIN receipts r ON ri.receipt_id = r.id
                WHERE r.round_id = ? AND ri.product_code = ?
            """, (round_id, product_code))
            row = cursor.fetchone()
            total_received = row["total_received"] or 0

            # Check if inventory_by_round exists
            cursor.execute("SELECT id FROM inventory_by_round WHERE product_code = ? AND round_id = ?", (product_code, round_id))
            existing = cursor.fetchone()
            if existing:
                cursor.execute("UPDATE inventory_by_round SET quantity_received = ? WHERE product_code = ? AND round_id = ?", (total_received, product_code, round_id))
            else:
                cursor.execute("INSERT INTO inventory_by_round (product_code, round_id, quantity_received) VALUES (?, ?, ?)", (product_code, round_id, total_received))
            conn.commit()
    except Exception as e:
        print(f"❌ Error recalculating inventory totals: {e}")


def get_receipts_by_round(round_id: int) -> List[Dict]:
    """Return receipts for a round."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM receipts WHERE round_id = ? ORDER BY receive_number", (round_id,))
            rows = cursor.fetchall()
            receipts = []
            for row in rows:
                receipts.append({
                    "id": row["id"],
                    "round_id": row["round_id"],
                    "receive_number": row["receive_number"],
                    "created_at": row["created_at"],
                    "notes": row["notes"]
                })
            return receipts
    except sqlite3.Error as e:
        print(f"❌ Error retrieving receipts: {e}")
        return []


def get_receipt_items(receipt_id: int) -> List[Dict]:
    """Return items for a receipt."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ri.*, p.Product_Name
                FROM receipt_items ri
                LEFT JOIN products p ON ri.product_code = p.Code
                WHERE ri.receipt_id = ?
            """, (receipt_id,))
            rows = cursor.fetchall()
            items = []
            for row in rows:
                items.append({
                    "id": row["id"],
                    "product_code": row["product_code"],
                    "product_name": row["Product_Name"] if "Product_Name" in row.keys() else None,
                    "quantity": row["quantity"]
                })
            return items
    except sqlite3.Error as e:
        print(f"❌ Error retrieving receipt items: {e}")
        return []


# ==================== SHOP MANAGEMENT FUNCTIONS ====================

def add_shop(shop_code: str, shop_name: str, address: str = None, phone: str = None) -> bool:
    """
    Add a new shop to the database.
    
    Args:
        shop_code: Shop code (unique identifier)
        shop_name: Shop name
        address: Optional address
        phone: Optional phone number
    
    Returns:
        True if successful, False otherwise
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO shops (shop_code, shop_name, address, phone)
                VALUES (?, ?, ?, ?)
            """, (shop_code, shop_name, address, phone))
            conn.commit()
            print(f"✅ Shop '{shop_name}' added successfully!")
            return True
    except sqlite3.IntegrityError:
        print(f"❌ Shop with code '{shop_code}' already exists!")
        return False
    except sqlite3.Error as e:
        print(f"❌ Error adding shop: {e}")
        return False


def get_all_shops(active_only: bool = True) -> List[Dict]:
    """
    Retrieve all shops from the database.
    
    Args:
        active_only: If True, only return active shops
    
    Returns:
        List of dictionaries containing shop data
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            if active_only:
                cursor.execute("SELECT * FROM shops WHERE is_active = 1 ORDER BY shop_code")
            else:
                cursor.execute("SELECT * FROM shops ORDER BY shop_code")
            rows = cursor.fetchall()
            
            shops = []
            for row in rows:
                shops.append({
                    "id": row["id"],
                    "shop_code": row["shop_code"],
                    "shop_name": row["shop_name"],
                    "address": row["address"] if "address" in row.keys() else None,
                    "phone": row["phone"] if "phone" in row.keys() else None,
                    "is_active": row["is_active"]
                })
            return shops
    except sqlite3.Error as e:
        print(f"❌ Error retrieving shops: {e}")
        return []


# ==================== CUSTOMER MANAGEMENT ====================

def add_customer(customer_code: str, customer_name: str, address: str = None, phone: str = None) -> bool:
    """Add new customer"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO customers (customer_code, customer_name, address, phone)
                VALUES (?, ?, ?, ?)
            """, (customer_code, customer_name, address, phone))
            conn.commit()
            print(f"✅ Customer '{customer_name}' added successfully!")
            return True
    except sqlite3.IntegrityError:
        print(f"❌ Customer with code '{customer_code}' already exists!")
        return False
    except sqlite3.Error as e:
        print(f"❌ Error adding customer: {e}")
        return False


def get_all_customers(active_only: bool = True) -> List[Dict]:
    """Retrieve all customers"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            if active_only:
                cursor.execute("SELECT * FROM customers WHERE is_active = 1 ORDER BY customer_code")
            else:
                cursor.execute("SELECT * FROM customers ORDER BY customer_code")
            rows = cursor.fetchall()
            result = []
            for row in rows:
                result.append({
                    'id': row['id'],
                    'customer_code': row['customer_code'],
                    'customer_name': row['customer_name'],
                    'address': row['address'] if 'address' in row.keys() else None,
                    'phone': row['phone'] if 'phone' in row.keys() else None,
                    'is_active': row['is_active']
                })
            return result
    except sqlite3.Error as e:
        print(f"❌ Error retrieving customers: {e}")
        return []


def update_customer(customer_id: int, customer_code: str = None, customer_name: str = None, address: str = None, phone: str = None, is_active: int = None) -> bool:
    """Update customer info"""
    try:
        updates = {}
        if customer_code is not None:
            updates['customer_code'] = customer_code
        if customer_name is not None:
            updates['customer_name'] = customer_name
        if address is not None:
            updates['address'] = address
        if phone is not None:
            updates['phone'] = phone
        if is_active is not None:
            updates['is_active'] = is_active
        if not updates:
            return False
        with get_connection() as conn:
            cursor = conn.cursor()
            set_clause = ", ".join([f"{col} = ?" for col in updates.keys()])
            values = list(updates.values()) + [customer_id]
            query = f"UPDATE customers SET {set_clause} WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()
            if cursor.rowcount > 0:
                print("✅ Customer updated successfully!")
                return True
            else:
                print("⚠️ Customer not found!")
                return False
    except sqlite3.Error as e:
        print(f"❌ Error updating customer: {e}")
        return False


def delete_customer(customer_id: int) -> bool:
    """Soft delete customer (set is_active=0)"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE customers SET is_active = 0 WHERE id = ?", (customer_id,))
            conn.commit()
            if cursor.rowcount > 0:
                print("✅ Customer deleted successfully!")
                return True
            else:
                print("⚠️ Customer not found!")
                return False
    except sqlite3.Error as e:
        print(f"❌ Error deleting customer: {e}")
        return False


def update_shop(shop_id: int, shop_code: str = None, shop_name: str = None, address: str = None, phone: str = None, is_active: int = None) -> bool:
    """
    Update shop information.
    
    Args:
        shop_id: Shop ID to update
        shop_code: New shop code (optional)
        shop_name: New shop name (optional)
        address: New address (optional)
        phone: New phone (optional)
        is_active: Active status (optional)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        updates = {}
        if shop_code is not None:
            updates["shop_code"] = shop_code
        if shop_name is not None:
            updates["shop_name"] = shop_name
        if address is not None:
            updates["address"] = address
        if phone is not None:
            updates["phone"] = phone
        if is_active is not None:
            updates["is_active"] = is_active
        
        if not updates:
            return False
        
        with get_connection() as conn:
            cursor = conn.cursor()
            set_clause = ", ".join([f"{col} = ?" for col in updates.keys()])
            values = list(updates.values()) + [shop_id]
            
            query = f"UPDATE shops SET {set_clause} WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()
            
            if cursor.rowcount > 0:
                print(f"✅ Shop updated successfully!")
                return True
            else:
                print(f"⚠️ Shop not found!")
                return False
    except sqlite3.Error as e:
        print(f"❌ Error updating shop: {e}")
        return False


def delete_shop(shop_id: int) -> bool:
    """
    Soft delete a shop (set is_active = 0).
    
    Args:
        shop_id: Shop ID to delete
    
    Returns:
        True if successful, False otherwise
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE shops SET is_active = 0 WHERE id = ?", (shop_id,))
            conn.commit()
            
            if cursor.rowcount > 0:
                print(f"✅ Shop deleted successfully!")
                return True
            else:
                print(f"⚠️ Shop not found!")
                return False
    except sqlite3.Error as e:
        print(f"❌ Error deleting shop: {e}")
        return False


if __name__ == "__main__":
    # Test the database functions
    print("🧪 Testing Database Functions...")
    print("-" * 50)
    
    # Initialize database
    init_db()
    
    # Add sample products
    add_product("P001", "สินค้า A", 12, 10.0, 15.0)
    add_product("P002", "สินค้า B", 24, 5.0, 8.0)
    add_product("P003", "สินค้า C", 6, 20.0, 30.0)
    
    # Get all products
    print("\n📦 All Products:")
    products = get_all_products()
    for p in products:
        print(f"  {p['Code']}: {p['Product_Name']}")
    
    # Update a product
    print("\n🔄 Updating P001...")
    update_product("P001", {"Receive_Round_1": 10, "Shop_1": 5})
    
    print("\n✅ Database test complete!")
