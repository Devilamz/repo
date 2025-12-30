import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from de import database as db


def test_customer_crud():
    # ensure a clean database for the test
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'de', 'inventory.db')
    if os.path.exists(db_path):
        os.remove(db_path)
    db.init_db()
    added = db.add_customer('C001', 'Customer A', 'Addr A', '0890000000')
    assert added
    custs = db.get_all_customers()
    assert any(c['customer_code'] == 'C001' for c in custs)
    # Update
    cid = next(c['id'] for c in custs if c['customer_code'] == 'C001')
    updated = db.update_customer(cid, customer_name='Customer A Updated')
    assert updated
    # Delete
    deleted = db.delete_customer(cid)
    assert deleted
    custs2 = db.get_all_customers()
    assert not any(c['customer_code'] == 'C001' for c in custs2)
