"""
Inventory Management System - Streamlit App
Mobile-friendly UI for managing stock, receiving, and distribution

This is the main entry point for deployment.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

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
    get_shop_distribution_by_round, bulk_update_shop_distribution
)


# Page Configuration
st.set_page_config(
    page_title="📦 Inventory Manager",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)


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


# Initialize database
init_db()

# Main UI
st.title("📦 Inventory Manager")
st.markdown("---")

# Sidebar Navigation
page = st.sidebar.radio(
    "📋 เมนู",
    ["แดชบอร์ด", "สินค้า", "รอบการรับ", "สินค้าตามรอบ", "จัดการร้าน", "การแจกจ่ายร้าน"]
)


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
        
        if st.button("➕ เพิ่มสินค้า", key="add_product"):
            if product_code and product_name:
                add_product(product_code, product_name)
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
        
        if st.button("➕ เพิ่มร้าน", key="add_shop"):
            if shop_code and shop_name:
                add_shop(shop_code, shop_name)
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
            
            if st.button("💾 บันทึกการแก้ไข", key="update_shop"):
                update_shop(shop_to_edit, new_code, new_name)
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
                    
                    edited_df = st.data_editor(
                        df,
                        use_container_width=True,
                        hide_index=True,
                        key="distribution_editor"
                    )
                    
                    if st.button("💾 บันทึกการแจกจ่าย", key="save_distribution"):
                        try:
                            bulk_update_shop_distribution(round_id, edited_df.to_dict('records'))
                            st.success("✅ บันทึกการแจกจ่ายเรียบร้อย")
                            st.rerun()
                        except Exception as e:
                            st.error(f"เกิดข้อผิดพลาด: {str(e)}")
                else:
                    st.info("No distribution data for this round.")
        else:
            st.info("Please add delivery rounds first.")


# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray; font-size: 12px;'>"
    "📦 ระบบจัดการคลังสินค้า | สร้างด้วย Streamlit"
    "</div>",
    unsafe_allow_html=True
)
