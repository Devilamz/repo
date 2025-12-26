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
                    Sell_Price_Small REAL DEFAULT 0.0
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
            
            conn.commit()
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
    sell_price_small: float = 0.0
) -> bool:
    """
    Add a new product to the database.
    
    Args:
        code: Product code (Primary Key)
        product_name: Product name
        small_units_per_big: Conversion rate (big to small units)
        cost_price_small: Cost per small unit
        sell_price_small: Selling price per small unit
    
    Returns:
        True if successful, False otherwise
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO products (
                    Code, Product_Name, Small_Units_Per_Big, 
                    Cost_Price_Small, Sell_Price_Small
                )
                VALUES (?, ?, ?, ?, ?)
            """, (code, product_name, small_units_per_big, cost_price_small, sell_price_small))
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
                    "Sell_Price_Small": row["Sell_Price_Small"]
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


# ==================== SHOP MANAGEMENT FUNCTIONS ====================

def add_shop(shop_code: str, shop_name: str) -> bool:
    """
    Add a new shop to the database.
    
    Args:
        shop_code: Shop code (unique identifier)
        shop_name: Shop name
    
    Returns:
        True if successful, False otherwise
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO shops (shop_code, shop_name)
                VALUES (?, ?)
            """, (shop_code, shop_name))
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
                    "is_active": row["is_active"]
                })
            return shops
    except sqlite3.Error as e:
        print(f"❌ Error retrieving shops: {e}")
        return []


def update_shop(shop_id: int, shop_code: str = None, shop_name: str = None, is_active: int = None) -> bool:
    """
    Update shop information.
    
    Args:
        shop_id: Shop ID to update
        shop_code: New shop code (optional)
        shop_name: New shop name (optional)
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
