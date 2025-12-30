"""
Inventory Management System - Streamlit App
Mobile-friendly UI for managing stock, receiving, and distribution

This is the main entry point for deployment.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components

from de.database import (
    init_db, add_product, get_all_products, 
    bulk_update_products, delete_product,
    # Delivery rounds functions
    add_delivery_round, get_all_delivery_rounds, delete_delivery_round,
    # Inventory by round functions
    get_inventory_by_round, bulk_update_inventory_by_round,
    # Shop management functions
    add_shop, get_all_shops, update_shop, delete_shop,
    # Shop distribution functions
    get_shop_distribution_by_round, bulk_update_shop_distribution, get_shop_allocations_by_round,
    # Order functions
    create_order, add_order_item, get_orders_by_round, get_order_items, get_order_summary_by_round,
    # Receipts
    create_receipt, add_receipt_item, get_receipts_by_round, get_receipt_items,
    # Reporting
    get_round_financials
)


# Page Configuration
st.set_page_config(
    page_title="📦 Inventory Manager",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

from ui.components import inject_global_styles, render_sidebar_menu, render_header


def calculate_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add calculated columns to the dataframe.
    Handles division by zero and missing values gracefully.
    """
    if df.empty:
        return df
    
    try:
        # Calculate Total Received (sum of all receive rounds)
        receive_cols = [col for col in ['Receive_Round_1', 'Receive_Round_2', 'Receive_Round_3'] if col in df.columns]
        if receive_cols:
            df["Total_Received"] = df[receive_cols].fillna(0).sum(axis=1)
        else:
            df["Total_Received"] = 0
        
        # Calculate Total Distributed (sum of all shops that exist in the dataframe)
        shop_cols = [col for col in df.columns if col.startswith('Shop_')]
        if shop_cols:
            df["Total_Distributed_Big"] = df[shop_cols].fillna(0).sum(axis=1)
        else:
            df["Total_Distributed_Big"] = 0
        
        # Calculate Remaining (Stock left after distribution)
        df["Remaining"] = df["Total_Received"].fillna(0) - df["Total_Distributed_Big"].fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Error calculating columns: {str(e)}")
        return df


# ----------------- HTML Renderers for Printing -----------------

def generate_order_html(order: dict, items: list, shop: dict, round_info: dict) -> str:
    """Return a simple print-friendly HTML string for an order."""
    rows = "".join([
        f"<tr><td>{i+1}</td><td>{it['product_code']}</td><td>{it.get('product_name','')}</td><td style='text-align:right'>{int(it['quantity'])}</td></tr>"
        for i, it in enumerate(items)
    ])
    html = f"""
    <html>
    <head>
      <meta charset='utf-8'/>
      <style>
        body {{ font-family: Arial, Helvetica, sans-serif; padding: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ border: 1px solid #ddd; padding: 6px; }}
        th {{ background: #f3f3f3; }}
      </style>
    </head>
    <body>
      <h2>ใบสั่งของ / Order</h2>
      <p><strong>Order:</strong> {order.get('order_code') or order.get('id')}</p>
      <p><strong>Shop:</strong> {shop.get('shop_code','')} - {shop.get('shop_name','')}</p>
      <p><strong>Address:</strong> {shop.get('address','')}</p>
      <p><strong>Round:</strong> {round_info.get('round_name','')}</p>
      <table>
        <thead><tr><th>ลำดับ</th><th>รหัส</th><th>สินค้า</th><th>จำนวน</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
      <p style='margin-top:20px;'>ลงชื่อผู้รับ .....................................  วันที่ ..........................</p>
    </body>
    </html>
    """
    return html


def generate_receipt_html(receipt: dict, items: list, round_info: dict) -> str:
    """Return a simple print-friendly HTML string for a receipt (รับของ)."""
    rows = "".join([
        f"<tr><td>{i+1}</td><td>{it['product_code']}</td><td>{it.get('product_name','')}</td><td style='text-align:right'>{int(it['quantity'])}</td></tr>"
        for i, it in enumerate(items)
    ])
    html = f"""
    <html>
    <head>
      <meta charset='utf-8'/>
      <style>
        body {{ font-family: Arial, Helvetica, sans-serif; padding: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ border: 1px solid #ddd; padding: 6px; }}
        th {{ background: #f3f3f3; }}
      </style>
    </head>
    <body>
      <h2>ใบรับของ / Receipt</h2>
      <p><strong>Receipt #:</strong> {receipt.get('receive_number')} &nbsp; <strong>วันที่:</strong> {receipt.get('created_at')}</p>
      <p><strong>Round:</strong> {round_info.get('round_name','')}</p>
      <table>
        <thead><tr><th>ลำดับ</th><th>รหัส</th><th>สินค้า</th><th>จำนวนที่รับ</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
      <p style='margin-top:20px;'>ลงชื่อผู้รับ .....................................  วันที่ ..........................</p>
    </body>
    </html>
    """
    return html


def generate_shop_receipt_html(shop: dict, items: list, round_info: dict) -> str:
    """Generate HTML receipt for a specific shop based on distribution items."""
    rows = "".join([
        f"<tr><td>{i+1}</td><td>{it['product_code']}</td><td>{it.get('product_name','')}</td><td style='text-align:right'>{int(it['quantity'])}</td></tr>"
        for i, it in enumerate(items)
    ])
    html = f"""
    <html>
    <head>
      <meta charset='utf-8'/>
      <style>
        body {{ font-family: Arial, Helvetica, sans-serif; padding: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ border: 1px solid #ddd; padding: 6px; }}
        th {{ background: #f3f3f3; }}
      </style>
    </head>
    <body>
      <h2>ใบเสร็จร้าน / Shop Receipt</h2>
      <p><strong>ร้าน:</strong> {shop.get('shop_code','')} - {shop.get('shop_name','')}</p>
      <p><strong>Round:</strong> {round_info.get('round_name','')}</p>
      <table>
        <thead><tr><th>ลำดับ</th><th>รหัส</th><th>สินค้า</th><th>จำนวน</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
      <p style='margin-top:20px;'>ลงชื่อผู้รับ .....................................  วันที่ ..........................</p>
    </body>
    </html>
    """
    return html


def html_to_pdf_bytes(html: str) -> bytes:
    """Attempt to convert HTML string to PDF bytes using WeasyPrint if available.
    Returns bytes on success, or None if WeasyPrint is not installed or conversion fails.
    """
    try:
        from weasyprint import HTML
        return HTML(string=html).write_pdf()
    except ImportError:
        return None
    except Exception as e:
        # We use Streamlit's st.error where appropriate in the UI path
        return None


# Initialize database
init_db()

# Main UI
inject_global_styles()
render_header("📦 Inventory Manager", "ระบบรับสินค้า แจกจ่าย และรายงานต้นทุน/กำไร")
st.markdown("---")

# Sidebar Navigation (component)
page = render_sidebar_menu(["แดชบอร์ด", "สินค้า", "ลูกค้า", "รอบการรับ", "รับออเดอร์", "พิมพ์", "รับของ", "รายงาน", "สินค้าตามรอบ", "จัดการร้าน", "การแจกจ่ายร้าน"])


# ============================================================================
# DASHBOARD PAGE
# ============================================================================
if page == "แดชบอร์ด":
    st.header("แดชบอร์ด")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Get all products
    products = get_all_products()
    
    if products:
        df = pd.DataFrame(products)
        df = calculate_columns(df)
        
        col1.metric("📦 Total Products", len(df))
        col2.metric("📥 Total Received", int(df["Total_Received"].sum()))
        col3.metric("📤 Total Distributed", int(df["Total_Distributed_Big"].sum()))
        col4.metric("📊 Stock Remaining", int(df["Remaining"].sum()))
        
        st.markdown("---")
        st.subheader("📊 สรุปสินค้า")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("ยังไม่มีสินค้า เริ่มได้โดยไปที่เมนู 'สินค้า' เพื่อเพิ่มสินค้า")


# ============================================================================
# PRODUCTS PAGE
# ============================================================================
elif page == "สินค้า":
    st.header("จัดการสินค้า")
    
    tabs = st.tabs(["ดูสินค้า", "เพิ่มสินค้า", "แก้ไขสินค้า", "ลบสินค้า"])
    
    # Tab 1: View Products
    with tabs[0]:
        st.subheader("สินค้าทั้งหมด")
        products = get_all_products()
        
        if products:
            df = pd.DataFrame(products)
            df = calculate_columns(df)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Product preview
            prod_codes = df['Code'].tolist()
            selected = st.selectbox("เลือกสินค้าเพื่อดูรายละเอียด", prod_codes)
            sel_row = df[df['Code'] == selected].iloc[0]
            st.markdown(f"**{sel_row['Code']} - {sel_row['Product_Name']}**")
            st.write(f"Small units / big: {sel_row.get('Small_Units_Per_Big', '')}")
            st.write(f"Cost (small): {sel_row.get('Cost_Price_Small', '')} | Sell (small): {sel_row.get('Sell_Price_Small', '')}")
            if sel_row.get('Image_Path'):
                try:
                    st.image(sel_row.get('Image_Path'), width=200)
                except Exception:
                    st.text("ไม่สามารถโหลดรูปภาพได้")

            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 ดาวน์โหลดเป็น CSV",
                data=csv,
                file_name="products.csv",
                mime="text/csv"
            )
        else:
            st.info("No products found.")
    
    # Tab 2: Add Product
    with tabs[1]:
        st.subheader("เพิ่มสินค้าใหม่")
        col1, col2 = st.columns(2)
        
        with col1:
            product_code = st.text_input("รหัสสินค้า")
            product_name = st.text_input("ชื่อสินค้า")
            small_units = st.number_input("จำนวนหน่วยย่อยต่อหน่วยใหญ่", min_value=1, value=1, step=1)
            cost_price = st.number_input("ราคาทุน (หน่วยย่อย)", min_value=0.0, value=0.0, step=0.01)
            sell_price = st.number_input("ราคาขาย (หน่วยย่อย)", min_value=0.0, value=0.0, step=0.01)
        with col2:
            notes = st.text_area("หมายเหตุสินค้า (Notes)")
            image_file = st.file_uploader("รูปสินค้า", type=["png", "jpg", "jpeg"])

        if st.button("➕ เพิ่มสินค้า", key="add_product"):
            if product_code and product_name:
                image_path = None
                if image_file is not None:
                    import os
                    os.makedirs("static/images", exist_ok=True)
                    ext = os.path.splitext(image_file.name)[1]
                    image_path = f"static/images/{product_code}{ext}"
                    with open(image_path, "wb") as f:
                        f.write(image_file.getbuffer())

                add_product(product_code, product_name, small_units_per_big=int(small_units), cost_price_small=float(cost_price), sell_price_small=float(sell_price), image_path=image_path, notes=notes)
                st.success(f"✅ เพิ่มสินค้า '{product_name}' เรียบร้อยแล้ว")
                st.rerun()
            else:
                st.error("กรุณากรอกข้อมูลให้ครบถ้วน")
    
    # Tab 3: Edit Products
    with tabs[2]:
        st.subheader("แก้ไขสินค้า")
        products = get_all_products()
        
        if products:
            df = pd.DataFrame(products)
            
            # Allow bulk editing
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                hide_index=True,
                key="product_editor"
            )
            
            if st.button("💾 Save Changes", key="save_products"):
                try:
                    bulk_update_products(edited_df.to_dict('records'))
                    st.success("✅ แก้ไขสินค้าสำเร็จ")
                    st.rerun()
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาดขณะบันทึก: {str(e)}")
        else:
            st.info("No products to edit.")
    
    # Tab 4: Delete Product
    with tabs[3]:
        st.subheader("ลบสินค้า")
        products = get_all_products()
        
        if products:
            df = pd.DataFrame(products)

            def _format_product(option_code):
                row = df[df['Code'] == option_code]
                if row.empty:
                    return str(option_code)
                name = row['Product_Name'].values[0] if 'Product_Name' in df.columns else ''
                return f"{option_code} - {name}" if name else str(option_code)

            product_to_delete = st.selectbox(
                "เลือกรหัสที่ต้องการลบ",
                df["Code"].tolist(),
                format_func=_format_product
            )
            
            if st.button("🗑️ ลบสินค้า", key="delete_product"):
                delete_product(product_to_delete)
                st.success("✅ ลบสินค้าสำเร็จ")
                st.rerun()
        else:
            st.info("No products to delete.")


# ============================================================================
# DELIVERY ROUNDS PAGE
# ============================================================================
elif page == "รอบการรับ":
    st.header("จัดการรอบการรับ")
    
    tabs = st.tabs(["ดูรอบ", "เพิ่มรอบ", "ลบรอบ"])
    
    # Tab 1: View Delivery Rounds
    with tabs[0]:
        st.subheader("รอบการรับทั้งหมด")
        rounds = get_all_delivery_rounds()
        
        if rounds:
            df = pd.DataFrame(rounds)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No delivery rounds found.")
    
    # Tab 2: Add Delivery Round
    with tabs[1]:
        st.subheader("เพิ่มรอบการรับใหม่")
        col1, col2 = st.columns(2)
        
        with col1:
            round_name = st.text_input("ชื่อรอบ (เช่น รอบที่ 1)")
            round_date = st.date_input("วันที่ (วด/ดด/ปปปป)")
        
        if st.button("➕ Add Round", key="add_round"):
            if round_name:
                add_delivery_round(round_name, str(round_date))
                st.success(f"✅ เพิ่มรอบ '{round_name}' เรียบร้อยแล้ว")
                st.rerun()
            else:
                st.error("กรุณากรอกชื่อรอบ")
    
    # Tab 3: Delete Delivery Round
    with tabs[2]:
        st.subheader("ลบรอบการรับ")
        rounds = get_all_delivery_rounds()
        
        if rounds:
            df = pd.DataFrame(rounds)

            def _format_round(option_id):
                row = df[df['id'] == option_id]
                if row.empty:
                    return str(option_id)
                name = row['round_name'].values[0] if 'round_name' in df.columns else str(option_id)
                # database returns 'delivery_date' column
                date_col = 'delivery_date' if 'delivery_date' in df.columns else None
                date = row[date_col].values[0] if date_col else ''
                return f"{name} ({date})" if date else f"{name}"

            round_to_delete = st.selectbox(
                "Select Round to Delete",
                df["id"].tolist(),
                format_func=_format_round
            )
            
            if st.button("🗑️ ลบรอบ", key="delete_round"):
                delete_delivery_round(round_to_delete)
                st.success("✅ ลบรอบเรียบร้อย")
                st.rerun()
        else:
            st.info("No delivery rounds to delete.")


# ============================================================================
# ORDER ENTRY PAGE
# ============================================================================
elif page == "รับออเดอร์":
    st.header("รับออเดอร์จากร้านค้า")
    rounds = get_all_delivery_rounds()
    shops = get_all_shops()
    products = get_all_products()

    if not rounds:
        st.info("กรุณาสร้างรอบการรับก่อน")
    elif not shops:
        st.info("กรุณาเพิ่มร้านค้าก่อน")
    elif not products:
        st.info("กรุณาเพิ่มสินค้าก่อน")
    else:
        round_names = [r["round_name"] for r in rounds]
        selected_round = st.selectbox("เลือกรอบ", round_names)
        round_id = next((r["id"] for r in rounds if r["round_name"] == selected_round), None)

        shop_options = [f"{s['shop_code']} - {s['shop_name']}" for s in shops]
        selected_shops = st.multiselect("เลือกร้าน (เลือกหลายร้านได้)", shop_options)

        if selected_shops:
            # Prepare product template
            prod_template = pd.DataFrame([{
                'product_code': p['Code'],
                'Product_Name': p['Product_Name'],
                'quantity': 0
            } for p in products])

            shop_map = {f"{s['shop_code']} - {s['shop_name']}": s['id'] for s in shops}
            order_results = []

            for s in selected_shops:
                shop_id = shop_map.get(s)
                with st.expander(f"สั่งจาก: {s}"):
                    editor_key = f"order_editor_{round_id}_{shop_id}"
                    edited = st.data_editor(prod_template.copy(), use_container_width=True, hide_index=True, key=editor_key)
                    order_results.append((shop_id, edited))

            if st.button("📨 ส่งออเดอร์ทั้งหมด", key="submit_orders"):
                created = 0
                for shop_id, df_items in order_results:
                    # Filter positive quantities
                    df_pos = df_items[df_items['quantity'].fillna(0) > 0]
                    if df_pos.empty:
                        continue
                    order_id = create_order(round_id, shop_id)
                    if not order_id:
                        continue
                    for _, row in df_pos.iterrows():
                        add_order_item(order_id, row['product_code'], int(row['quantity']), 0.0)
                    created += 1
                st.success(f"✅ สร้างออเดอร์สำหรับ {created} ร้านเสร็จเรียบร้อย")
                st.rerun()


# ============================================================================
# RECEIVE GOODS / RECEIPT PAGE
# ============================================================================
elif page == "รับของ":
    st.header("รับของเข้าสู่รอบ")
    rounds = get_all_delivery_rounds()
    products = get_all_products()

    if not rounds:
        st.info("กรุณาสร้างรอบการรับก่อน")
    elif not products:
        st.info("กรุณาเพิ่มสินค้าก่อน")
    else:
        round_names = [r["round_name"] for r in rounds]
        selected_round = st.selectbox("เลือกรอบ", round_names)
        round_id = next((r["id"] for r in rounds if r["round_name"] == selected_round), None)

        st.subheader("สร้างใบรับของใหม่")
        receipts = get_receipts_by_round(round_id)
        next_receive_number = (max([r['receive_number'] for r in receipts]) + 1) if receipts else 1
        st.write(f"หมายเลขการรับถัดไป: {next_receive_number}")

        # Prepare product template for receiving quantities
        recv_template = pd.DataFrame([{
            'product_code': p['Code'],
            'Product_Name': p['Product_Name'],
            'quantity': 0
        } for p in products])

        edited = st.data_editor(recv_template.copy(), use_container_width=True, hide_index=True, key=f"recv_editor_{round_id}")

        recv_notes = st.text_area("หมายเหตุการรับ")

        if st.button("📥 บันทึกการรับของ", key=f"save_receipt_{round_id}"):
            df_pos = edited[edited['quantity'].fillna(0) > 0]
            if df_pos.empty:
                st.error("กรุณาใส่จำนวนที่รับเข้ามาอย่างน้อย 1 รายการ")
            else:
                receipt_id = create_receipt(round_id, next_receive_number, recv_notes)
                if not receipt_id:
                    st.error("เกิดข้อผิดพลาดขณะสร้างใบรับของ")
                else:
                    for _, row in df_pos.iterrows():
                        add_receipt_item(receipt_id, row['product_code'], int(row['quantity']))
                    st.success(f"✅ บันทึกการรับของ (ใบที่ {next_receive_number}) เรียบร้อย")
                    st.rerun()

        st.markdown("---")
        st.subheader("ใบรับของที่ผ่านมาในรอบนี้")
        receipts = get_receipts_by_round(round_id)
        if receipts:
            for r in receipts:
                with st.expander(f"รับที่ {r['receive_number']} - วันที่: {r['created_at']}"):
                    items = get_receipt_items(r['id'])
                    st.dataframe(pd.DataFrame(items), use_container_width=True, hide_index=True)
                    # Allow download
                    csv = pd.DataFrame(items).to_csv(index=False)
                    st.download_button(f"📥 ดาวน์โหลดใบรับของที่ {r['receive_number']}", data=csv, file_name=f"receipt_{round_id}_{r['receive_number']}.csv", mime='text/csv')
        else:
            st.info("ยังไม่มีใบรับของในรอบนี้")


# ============================================================================
# INVENTORY BY ROUND PAGE
# ============================================================================
elif page == "สินค้าตามรอบ":
    st.header("สินค้าตามรอบการรับ")
    
    tabs = st.tabs(["ดูสินค้าตามรอบ", "แก้ไขสินค้าตามรอบ"])
    
    # Tab 1: View Inventory
    with tabs[0]:
        st.subheader("Inventory by Round")
        
        rounds = get_all_delivery_rounds()
        products = get_all_products()
        
        if rounds and products:
            # Create a view with inventory for each round
            round_names = [r["round_name"] for r in rounds]
            selected_round = st.selectbox("เลือกรอบ", round_names)
            
            # Get the round ID
            round_id = next((r["id"] for r in rounds if r["round_name"] == selected_round), None)
            
            if round_id:
                inventory = get_inventory_by_round(round_id)
                if inventory:
                    df = pd.DataFrame(inventory)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("ยังไม่มีข้อมูลสินค้าในรอบนี้")
        else:
            st.info("Please add products and delivery rounds first.")
    
    # Tab 2: Edit Inventory
    with tabs[1]:
        st.subheader("Edit Inventory")
        
        rounds = get_all_delivery_rounds()
        products = get_all_products()
        
        if rounds and products:
            round_names = [r["round_name"] for r in rounds]
            selected_round = st.selectbox("Select Round to Edit", round_names, key="edit_round")
            
            # Get the round ID
            round_id = next((r["id"] for r in rounds if r["round_name"] == selected_round), None)
            
            if round_id:
                inventory = get_inventory_by_round(round_id)
                if inventory:
                    df = pd.DataFrame(inventory)
                    
                    edited_df = st.data_editor(
                        df,
                        use_container_width=True,
                        hide_index=True,
                        key="inventory_editor"
                    )
                    
                    if st.button("💾 บันทึกการแก้ไข", key="save_inventory"):
                        try:
                            bulk_update_inventory_by_round(round_id, edited_df.to_dict('records'))
                            st.success("✅ บันทึกข้อมูลสำเร็จ")
                            st.rerun()
                        except Exception as e:
                            st.error(f"เกิดข้อผิดพลาด: {str(e)}")
                else:
                    st.info("No inventory data for this round.")
        else:
            st.info("Please add products and delivery rounds first.")


# ============================================================================
# SHOP MANAGEMENT PAGE
# ============================================================================
elif page == "จัดการร้าน":
    st.header("จัดการร้านค้า")
    
    tabs = st.tabs(["ดูร้าน", "เพิ่มร้าน", "แก้ไขร้าน", "ลบร้าน"])
    
    # Tab 1: View Shops
    with tabs[0]:
        st.subheader("ร้านค้าทั้งหมด")
        shops = get_all_shops()
        
        if shops:
            df = pd.DataFrame(shops)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No shops found.")
    
    # Tab 2: Add Shop
    with tabs[1]:
        st.subheader("Add New Shop")
        col1, col2 = st.columns(2)
        
        with col1:
            shop_code = st.text_input("รหัสร้าน")
            shop_name = st.text_input("ชื่อร้าน")
        with col2:
            address = st.text_area("ที่อยู่")
            phone = st.text_input("เบอร์โทร")
        
        if st.button("➕ เพิ่มร้าน", key="add_shop"):
            if shop_code and shop_name:
                add_shop(shop_code, shop_name, address, phone)
                st.success(f"✅ เพิ่มร้าน '{shop_name}' เรียบร้อยแล้ว")
                st.rerun()
            else:
                st.error("กรุณากรอกข้อมูลให้ครบถ้วน")
    
    # Tab 3: Edit Shop
    with tabs[2]:
        st.subheader("Edit Shop")
        shops = get_all_shops()
        
        if shops:
            df = pd.DataFrame(shops)

            def _format_shop(option_id):
                row = df[df['id'] == option_id]
                if row.empty:
                    return str(option_id)
                code = row['shop_code'].values[0] if 'shop_code' in df.columns else ''
                name = row['shop_name'].values[0] if 'shop_name' in df.columns else ''
                if code and name:
                    return f"{code} - {name}"
                return code or name or str(option_id)

            shop_to_edit = st.selectbox(
                "Select Shop to Edit",
                df["id"].tolist(),
                format_func=_format_shop
            )
            
            shop_data = df[df["id"] == shop_to_edit].iloc[0]
            
            col1, col2 = st.columns(2)
            with col1:
                new_code = st.text_input("รหัสร้าน", value=shop_data["shop_code"])
                new_name = st.text_input("ชื่อร้าน", value=shop_data["shop_name"])
            with col2:
                new_address = st.text_area("ที่อยู่", value=shop_data.get("address", ""))
                new_phone = st.text_input("เบอร์โทร", value=shop_data.get("phone", ""))
            
            if st.button("💾 บันทึกการแก้ไข", key="update_shop"):
                update_shop(shop_to_edit, new_code, new_name, new_address, new_phone)
                st.success("✅ แก้ไขร้านเรียบร้อย")
                st.rerun()
        else:
            st.info("No shops to edit.")
    
    # Tab 4: Delete Shop
    with tabs[3]:
        st.subheader("Delete Shop")
        shops = get_all_shops()
        
        if shops:
            df = pd.DataFrame(shops)

            def _format_shop_delete(option_id):
                row = df[df['id'] == option_id]
                if row.empty:
                    return str(option_id)
                code = row['shop_code'].values[0] if 'shop_code' in df.columns else ''
                name = row['shop_name'].values[0] if 'shop_name' in df.columns else ''
                if code and name:
                    return f"{code} - {name}"
                return code or name or str(option_id)

            shop_to_delete = st.selectbox(
                "Select Shop to Delete",
                df["id"].tolist(),
                format_func=_format_shop_delete,
                key="delete_shop_select"
            )
            
            if st.button("🗑️ ลบร้าน", key="delete_shop"):
                delete_shop(shop_to_delete)
                st.success("✅ ลบร้านเรียบร้อย")
                st.rerun()
        else:
            st.info("No shops to delete.")


# ============================================================================
# CUSTOMER MANAGEMENT PAGE
# ============================================================================
elif page == "ลูกค้า":
    st.header("จัดการข้อมูลลูกค้า")
    
    tabs = st.tabs(["ดูลูกค้า", "เพิ่มลูกค้า", "แก้ไขลูกค้า", "ลบลูกค้า"])
    
    # View Customers
    with tabs[0]:
        st.subheader("ลูกค้าทั้งหมด")
        customers = get_all_customers()
        if customers:
            df = pd.DataFrame(customers)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No customers found.")

    # Add Customer
    with tabs[1]:
        st.subheader("Add New Customer")
        col1, col2 = st.columns(2)
        with col1:
            customer_code = st.text_input("รหัสลูกค้า")
            customer_name = st.text_input("ชื่อลูกค้า")
        with col2:
            address = st.text_area("ที่อยู่")
            phone = st.text_input("เบอร์โทร")
        if st.button("➕ เพิ่มลูกค้า", key="add_customer"):
            if customer_code and customer_name:
                add_customer(customer_code, customer_name, address, phone)
                st.success(f"✅ เพิ่มลูกค้า '{customer_name}' เรียบร้อยแล้ว")
                st.rerun()
            else:
                st.error("กรุณากรอกข้อมูลให้ครบถ้วน")

    # Edit Customer
    with tabs[2]:
        st.subheader("Edit Customer")
        customers = get_all_customers()
        if customers:
            df = pd.DataFrame(customers)

            def _format_cust(option_id):
                row = df[df['id'] == option_id]
                if row.empty:
                    return str(option_id)
                code = row['customer_code'].values[0] if 'customer_code' in df.columns else ''
                name = row['customer_name'].values[0] if 'customer_name' in df.columns else ''
                if code and name:
                    return f"{code} - {name}"
                return code or name or str(option_id)

            cust_to_edit = st.selectbox("Select Customer to Edit", df["id"].tolist(), format_func=_format_cust)
            cust_data = df[df["id"] == cust_to_edit].iloc[0]
            col1, col2 = st.columns(2)
            with col1:
                new_code = st.text_input("รหัสลูกค้า", value=cust_data["customer_code"])
                new_name = st.text_input("ชื่อลูกค้า", value=cust_data["customer_name"])
            with col2:
                new_address = st.text_area("ที่อยู่", value=cust_data.get("address", ""))
                new_phone = st.text_input("เบอร์โทร", value=cust_data.get("phone", ""))
            if st.button("💾 บันทึกการแก้ไข", key="update_customer"):
                update_customer(cust_to_edit, new_code, new_name, new_address, new_phone)
                st.success("✅ แก้ไขลูกค้าเรียบร้อย")
                st.rerun()
        else:
            st.info("No customers to edit.")

    # Delete Customer
    with tabs[3]:
        st.subheader("Delete Customer")
        customers = get_all_customers()
        if customers:
            df = pd.DataFrame(customers)

            def _format_cust_delete(option_id):
                row = df[df['id'] == option_id]
                if row.empty:
                    return str(option_id)
                code = row['customer_code'].values[0] if 'customer_code' in df.columns else ''
                name = row['customer_name'].values[0] if 'customer_name' in df.columns else ''
                if code and name:
                    return f"{code} - {name}"
                return code or name or str(option_id)

            cust_to_delete = st.selectbox("Select Customer to Delete", df["id"].tolist(), format_func=_format_cust_delete, key="delete_customer_select")
            if st.button("🗑️ ลบลูกค้า", key="delete_customer"):
                delete_customer(cust_to_delete)
                st.success("✅ ลบลูกค้าเรียบร้อย")
                st.rerun()


# ============================================================================
# SHOP DISTRIBUTION PAGE
# ============================================================================
elif page == "การแจกจ่ายร้าน":
    st.header("การแจกจ่ายสินค้าร้านค้า")
    
    tabs = st.tabs(["ดูการแจกจ่าย", "แก้ไขการแจกจ่าย"])
    
    # Tab 1: View Distribution
    with tabs[0]:
        st.subheader("Shop Distribution by Round")
        
        rounds = get_all_delivery_rounds()
        
        if rounds:
            round_names = [r["round_name"] for r in rounds]
            selected_round = st.selectbox("เลือกรอบ", round_names)
            
            # Get the round ID
            round_id = next((r["id"] for r in rounds if r["round_name"] == selected_round), None)
            
            if round_id:
                distribution = get_shop_distribution_by_round(round_id)
                if distribution:
                    df = pd.DataFrame(distribution)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("ยังไม่มีข้อมูลการแจกจ่ายในรอบนี้")
        else:
            st.info("Please add delivery rounds first.")
    
    # Tab 2: Edit Distribution
    with tabs[1]:
        st.subheader("Edit Shop Distribution")
        
        rounds = get_all_delivery_rounds()
        
        if rounds:
            round_names = [r["round_name"] for r in rounds]
            selected_round = st.selectbox("Select Round to Edit", round_names, key="edit_dist_round")
            
            # Get the round ID
            round_id = next((r["id"] for r in rounds if r["round_name"] == selected_round), None)
            
            if round_id:
                distribution = get_shop_distribution_by_round(round_id)
                if distribution:
                    df = pd.DataFrame(distribution)
                    
                    col1, col2 = st.columns([3,1])
                    with col2:
                        if st.button("🔁 Auto-fill from Orders", key="autofill_orders"):
                            order_summary = get_order_summary_by_round(round_id)
                            # Merge/override shop columns based on order summary
                            if order_summary:
                                sum_df = pd.DataFrame(order_summary)
                                # For each row in df, find corresponding row in sum_df by product_code
                                for idx, row in df.iterrows():
                                    pc = row['product_code']
                                    matching = sum_df[sum_df['product_code'] == pc]
                                    if not matching.empty:
                                        for k, v in matching.iloc[0].items():
                                            if k.startswith('shop_'):
                                                df.at[idx, k] = int(v)
                                st.success("✅ Auto-filled distribution from orders. Review and save.")
                                # re-render editor below
                    
                    edited_df = st.data_editor(
                        df,
                        use_container_width=True,
                        hide_index=True,
                        key="distribution_editor"
                    )
                    
                    # Validate allocation
                    if st.button("🔍 Validate Allocation", key="validate_alloc"):
                        problems = []
                        for _, row in edited_df.iterrows():
                            received = int(row.get('quantity_received', 0) or 0)
                            # Sum distributed across shop_* columns
                            distributed = sum([int(row[c] or 0) for c in edited_df.columns if str(c).startswith('shop_') and not str(c).endswith('_name')])
                            if distributed > received:
                                problems.append((row['product_code'], distributed, received))
                        if problems:
                            st.warning(f"พบการแจกจ่ายเกินยอดรับใน {len(problems)} รายการ")
                            for p in problems:
                                st.write(f"สินค้า {p[0]}: แจก {p[1]} > รับ {p[2]}")
                        else:
                            st.success("✅ Allocation validated. No over-allocation found.")
                    
                    if st.button("💾 บันทึกการแจกจ่าย", key="save_distribution"):
                        # Validate allocation
                        problems = []
                        for _, row in edited_df.iterrows():
                            received = int(row.get('quantity_received', 0) or 0)
                            distributed = sum([int(row[c] or 0) for c in edited_df.columns if str(c).startswith('shop_') and not str(c).endswith('_name')])
                            if distributed > received:
                                problems.append((row['product_code'], distributed, received))

                        override = st.checkbox("ยืนยันบันทึกแม้มีการแจกจ่ายเกินยอดรับ (ยืนยันความเสี่ยง)", key="override_confirm")
                        if problems and not override:
                            st.error(f"พบการแจกจ่ายเกินยอดรับ (ใช้ปุ่ม Validate เพื่อดูรายละเอียด) - แก้ไขก่อนบันทึก หรือติ๊กยืนยันเพื่อบันทึกต่อ")
                            for p in problems:
                                st.write(f"สินค้า {p[0]}: แจก {p[1]} > รับ {p[2]}")
                        else:
                            try:
                                bulk_update_shop_distribution(round_id, edited_df.to_dict('records'))
                                st.success("✅ บันทึกการแจกจ่ายเรียบร้อย")
                                st.rerun()
                            except Exception as e:
                                st.error(f"เกิดข้อผิดพลาด: {str(e)}")

                    # Print per-shop receipts
                    if st.button("📄 พิมพ์ใบเสร็จแต่ละร้าน", key="print_shop_receipts"):
                        allocations = get_shop_allocations_by_round(round_id)
                        round_info = next((r for r in rounds if r['id'] == round_id), {})
                        if not allocations:
                            st.info("ยังไม่มีการแจกจ่ายสำหรับรอบนี้")
                        else:
                            for a in allocations:
                                st.subheader(f"ร้าน: {a['shop_code']} - {a['shop_name']}")
                                st.dataframe(pd.DataFrame(a['items']), use_container_width=True, hide_index=True)
                                html = generate_shop_receipt_html(a, a['items'], round_info)
                                components.html(html, height=300)
                                st.download_button(f"📥 ดาวน์โหลด (HTML) {a['shop_code']}", data=html, file_name=f"shop_receipt_{round_id}_{a['shop_id']}.html", mime='text/html')
                                csv = pd.DataFrame(a['items']).to_csv(index=False)
                                st.download_button(f"📥 ดาวน์โหลด (CSV) {a['shop_code']}", data=csv, file_name=f"shop_receipt_{round_id}_{a['shop_id']}.csv", mime='text/csv')
                                pdf_bytes = html_to_pdf_bytes(html)
                                if pdf_bytes:
                                    st.download_button(f"📥 ดาวน์โหลด (PDF) {a['shop_code']}", data=pdf_bytes, file_name=f"shop_receipt_{round_id}_{a['shop_id']}.pdf", mime='application/pdf')
                                else:
                                    st.info("ติดตั้ง 'weasyprint' เพื่อเปิดใช้งานการดาวน์โหลดเป็น PDF (ต้องติดตั้ง dependencies ของระบบด้วย)")
                else:
                    st.info("No distribution data for this round.")
        else:
            st.info("Please add delivery rounds first.")


# ============================================================================
# PRINT / EXPORT PAGE
# ============================================================================

elif page == "พิมพ์":
    st.header("พิมพ์ / ดาวน์โหลด")
    st.write("เลือกประเภทที่ต้องการพิมพ์หรือดาวน์โหลด")
    tabs = st.tabs(["Orders", "Receipts"])

    # Orders Tab
    with tabs[0]:
        st.subheader("พิมพ์ใบสั่ง (Order Forms)")
        rounds = get_all_delivery_rounds()
        if not rounds:
            st.info("กรุณาสร้างรอบการรับก่อน")
        else:
            round_names = [r["round_name"] for r in rounds]
            selected_round = st.selectbox("เลือกรอบ", round_names, key="print_order_round")
            round_id = next((r["id"] for r in rounds if r["round_name"] == selected_round), None)
            orders = get_orders_by_round(round_id) or []
            shops = {s['id']: s for s in get_all_shops(active_only=False)}
            round_info = next((r for r in rounds if r['id'] == round_id), {})

            if orders:
                for o in orders:
                    with st.expander(f"Order #{o['id']} - {o.get('shop_code','')}"):
                        items = get_order_items(o['id'])
                        st.dataframe(pd.DataFrame(items), use_container_width=True, hide_index=True)

                        html = generate_order_html(o, items, shops.get(o['shop_id'], {}), round_info)
                        components.html(html, height=300)

                        st.download_button(f"📥 ดาวน์โหลด (HTML) Order {o['id']}", data=html, file_name=f"order_{o['id']}.html", mime='text/html')
                        csv = pd.DataFrame(items).to_csv(index=False)
                        st.download_button(f"📥 ดาวน์โหลด (CSV) Order {o['id']}", data=csv, file_name=f"order_{o['id']}.csv", mime='text/csv')
                        pdf_bytes = html_to_pdf_bytes(html)
                        if pdf_bytes:
                            st.download_button(f"📥 ดาวน์โหลด (PDF) Order {o['id']}", data=pdf_bytes, file_name=f"order_{o['id']}.pdf", mime='application/pdf')
                        else:
                            st.info("ติดตั้ง 'weasyprint' เพื่อเปิดใช้งานการดาวน์โหลดเป็น PDF (ต้องติดตั้ง dependencies ของระบบด้วย)")
            else:
                st.info("ยังไม่มีออเดอร์ในรอบนี้")

    # Receipts Tab
    with tabs[1]:
        st.subheader("พิมพ์ใบรับของ (Receipts)")
        rounds = get_all_delivery_rounds()
        if not rounds:
            st.info("กรุณาสร้างรอบการรับก่อน")
        else:
            round_names = [r["round_name"] for r in rounds]
            selected_round = st.selectbox("เลือกรอบ", round_names, key="print_receipt_round")
            round_id = next((r["id"] for r in rounds if r["round_name"] == selected_round), None)
            receipts = get_receipts_by_round(round_id) or []
            round_info = next((r for r in rounds if r['id'] == round_id), {})

            if receipts:
                for r in receipts:
                    with st.expander(f"Receipt #{r['receive_number']} - วันที่: {r['created_at']}"):
                        items = get_receipt_items(r['id'])
                        st.dataframe(pd.DataFrame(items), use_container_width=True, hide_index=True)

                        html = generate_receipt_html(r, items, round_info)
                        components.html(html, height=300)

                        st.download_button(f"📥 ดาวน์โหลด (HTML) Receipt {r['receive_number']}", data=html, file_name=f"receipt_{round_id}_{r['receive_number']}.html", mime='text/html')
                        csv = pd.DataFrame(items).to_csv(index=False)
                        st.download_button(f"📥 ดาวน์โหลด (CSV) Receipt {r['receive_number']}", data=csv, file_name=f"receipt_{round_id}_{r['receive_number']}.csv", mime='text/csv')
                        pdf_bytes = html_to_pdf_bytes(html)
                        if pdf_bytes:
                            st.download_button(f"📥 ดาวน์โหลด (PDF) Receipt {r['receive_number']}", data=pdf_bytes, file_name=f"receipt_{round_id}_{r['receive_number']}.pdf", mime='application/pdf')
                        else:
                            st.info("ติดตั้ง 'weasyprint' เพื่อเปิดใช้งานการดาวน์โหลดเป็น PDF (ต้องติดตั้ง dependencies ของระบบด้วย)")
            else:
                st.info("ยังไม่มีใบรับของในรอบนี้")


# ============================================================================
# REPORTS PAGE
# ============================================================================
elif page == "รายงาน":
    st.header("รายงานต้นทุน/กำไรตามรอบ")
    rounds = get_all_delivery_rounds()
    if not rounds:
        st.info("กรุณาสร้างรอบการรับก่อน")
    else:
        round_names = [r["round_name"] for r in rounds]
        selected_round = st.selectbox("เลือกรอบเพื่อดูรายงาน", round_names)
        round_id = next((r["id"] for r in rounds if r["round_name"] == selected_round), None)
        if round_id:
            report = get_round_financials(round_id)
            st.subheader(f"สรุปรอบ: {selected_round}")
            st.metric("ต้นทุนรวม", f"{report['total_cost']:.2f}")
            st.metric("รายรับรวม", f"{report['total_revenue']:.2f}")
            st.metric("กำไร", f"{report['total_profit']:.2f}")
            st.write("รายละเอียดสินค้า:")
            st.dataframe(pd.DataFrame(report['details']), use_container_width=True, hide_index=True)


