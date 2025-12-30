import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from de.database import init_db, add_product, add_shop, add_delivery_round, update_shop_distribution, get_shop_allocations_by_round

init_db()
add_product('D001','Dist Product', 12, 3.0, 5.0)
add_shop('DS1','Dist Shop','Address','081')
r = add_delivery_round('Dist Round', '2025-12-31')
# set distribution: 10 units to shop id 1
update_shop_distribution('D001', r, 1, 10)
allocs = get_shop_allocations_by_round(r)
print('Allocations:', allocs)
