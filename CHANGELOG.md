# Changelog

All notable changes made to the project (sorted by date).

## 2025-12-30
- Added product image and notes columns to `products` table and migration logic in `init_db`.
- Added shop `address` and `phone` columns and migration logic.
- Added new tables: `orders`, `order_items`, `receipts`, `receipt_items`.
- Implemented order entry UI (multi-shop order entry) and order CRUD helpers in `de/database.py`.
- Implemented receiving flows: create receipts, add receipt items, and automatic updating of `inventory_by_round` totals.
- Implemented reporting: `get_round_financials` and a Streamlit report page for cost/revenue/profit per round.
- Implemented print/export functionality: generate print-friendly HTML and CSV for orders, receipts, and per-shop receipts.
- Implemented order aggregation helper `get_order_summary_by_round` and an "Auto-fill from Orders" button to pre-fill distribution allocations.
- Added validation to distribution editing (validate over-allocation and require confirmation to save if overriding).
- Added customer management (CRUD): `customers` table and UI page `ลูกค้า`.
- Prepared redeploy trigger update (updated `REDEPLOY_TRIGGER.txt`).
- Organized project structure by adding `ui/`, `models/`, `services/` and `static/images/` directories.
- Updated `README.md` with usage notes.

