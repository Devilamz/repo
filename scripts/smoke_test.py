"""Simple smoke test script to exercise key DB flows."""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from de.database import (
    init_db, add_product, add_shop, add_delivery_round,
    create_order, add_order_item, create_receipt, add_receipt_item,
    get_orders_by_round, get_receipts_by_round, get_shop_allocations_by_round
)


def run():
    init_db()
    add_product("ST001", "Sample Product", 12, 10.0, 15.0)
    add_shop("S001", "ร้านตัวอย่าง", "ที่อยู่ตัวอย่าง", "0812345678")
    r = add_delivery_round("รอบทดสอบ", "2025-12-30")
    # Create order without order_code to avoid uniqueness errors
    oid = create_order(r, 1, None)
    if oid:
        add_order_item(oid, "ST001", 5, 15.0)
    receipt_id = create_receipt(r, None, "รับของทดสอบ")
    add_receipt_item(receipt_id, "ST001", 10)
    orders = get_orders_by_round(r)
    receipts = get_receipts_by_round(r)
    allocations = get_shop_allocations_by_round(r)
    print("Orders:", orders)
    print("Receipts:", receipts)
    print("Allocations (from distribution):", allocations)


if __name__ == '__main__':
    run()
