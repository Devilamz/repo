import os
import sys
import tempfile
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from de import database as db


def test_add_and_get_product():
    # ensure a clean database for the test
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'de', 'inventory.db')
    if os.path.exists(db_path):
        os.remove(db_path)
    db.init_db()
    code = "T100"
    db.add_product(code, "Test Product", 12, 1.5, 2.0)
    prods = db.get_all_products()
    assert any(p['Code'] == code for p in prods)


def test_shop_and_order_receipt_flow():
    db.init_db()
    db.add_shop("TS1", "Test Shop", "Addr", "0800000000")
    r = db.add_delivery_round("Test Round", "2025-12-31")
    oid = db.create_order(r, 1, None)
    assert oid is not None
    added = db.add_order_item(oid, "T100", 3, 2.0)
    assert added
    rid = db.create_receipt(r, None, "Test receive")
    assert rid is not None
    added_rec = db.add_receipt_item(rid, "T100", 5)
    assert added_rec


if __name__ == '__main__':
    test_add_and_get_product()
    test_shop_and_order_receipt_flow()
    print('DB tests passed')
