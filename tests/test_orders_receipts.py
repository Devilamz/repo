import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from de import database as db


def test_order_and_receipt_flow():
    # Clean DB
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'de', 'inventory.db')
    if os.path.exists(db_path):
        os.remove(db_path)

    db.init_db()

    db.add_product('P100', 'Prod P100', 12, 1.0, 2.0)
    db.add_shop('SS1', 'Shop S1', 'Addr', '0811111111')

    rid = db.add_delivery_round('R Orders', '2025-12-30')
    assert rid

    shops = db.get_all_shops(active_only=False)
    sid = next(s['id'] for s in shops if s['shop_code'] == 'SS1')

    oid = db.create_order(rid, sid, None)
    assert oid
    ok = db.add_order_item(oid, 'P100', 5, 2.0)
    assert ok

    summary = db.get_order_summary_by_round(rid)
    assert any(s['product_code'] == 'P100' and s['total_ordered'] == 5 for s in summary)
    # check shop field
    prod = next(s for s in summary if s['product_code'] == 'P100')
    shop_field = f'shop_{sid}'
    assert prod[shop_field] == 5

    # Receipts
    ridx = db.create_receipt(rid, None, 'Test receive')
    assert ridx
    rc_ok = db.add_receipt_item(ridx, 'P100', 10)
    assert rc_ok

    receipts = db.get_receipts_by_round(rid)
    assert receipts and receipts[0]['receive_number'] == 1
    items = db.get_receipt_items(ridx)
    assert any(it['product_code'] == 'P100' and it['quantity'] == 10 for it in items)
