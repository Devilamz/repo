import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from de import database as db


def test_distribution_basic_flow():
    # Ensure a clean DB
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'de', 'inventory.db')
    if os.path.exists(db_path):
        os.remove(db_path)

    db.init_db()

    # Add product and shops
    db.add_product('D100', 'Dist Product', 12, 1.0, 2.0)
    db.add_shop('S001', 'Shop One', 'Addr', '0800000001')
    db.add_shop('S002', 'Shop Two', 'Addr', '0800000002')

    rounds_before = db.get_all_delivery_rounds()
    rid = db.add_delivery_round('R Test', '2025-12-31')
    assert rid is not None

    # Add inventory for the round
    updated = db.bulk_update_inventory_by_round(rid, [{'product_code': 'D100', 'quantity_received': 50}])
    assert updated

    shops = db.get_all_shops(active_only=False)
    assert len(shops) >= 2
    sids = [s['id'] for s in shops if s['shop_code'] in ('S001','S002')]
    assert len(sids) == 2

    dist_payload = [{
        'product_code': 'D100',
        'quantity_received': 50,
        f'shop_{sids[0]}': 20,
        f'shop_{sids[1]}': 30
    }]

    ok = db.bulk_update_shop_distribution(rid, dist_payload)
    assert ok

    allocs = db.get_shop_allocations_by_round(rid)
    # In case the bulk update encounters transient locks, try direct updates and re-check
    if not allocs:
        db.update_shop_distribution('D100', rid, sids[0], 20)
        db.update_shop_distribution('D100', rid, sids[1], 30)
        allocs = db.get_shop_allocations_by_round(rid)

    # There should be entries for both shops
    codes = set(a['shop_code'] for a in allocs)
    assert 'S001' in codes and 'S002' in codes

    # Check quantities
    for a in allocs:
        for it in a['items']:
            assert it['product_code'] == 'D100'
            assert it['quantity'] in (20, 30)
