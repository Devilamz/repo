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
    "📋 Navigation",
    ["Dashboard", "Products", "Delivery Rounds", "Inventory by Round", "Shop Management", "Shop Distribution"]
)


# ============================================================================
# DASHBOARD PAGE
# ============================================================================
if page == "Dashboard":
    st.header("Dashboard")
    
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
        st.subheader("📊 Products Overview")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No products found. Start by adding products in the 'Products' section.")


# ============================================================================
# PRODUCTS PAGE
# ============================================================================
elif page == "Products":
    st.header("Product Management")
    
    tabs = st.tabs(["View Products", "Add Product", "Edit Products", "Delete Product"])
    
    # Tab 1: View Products
    with tabs[0]:
        st.subheader("All Products")
        products = get_all_products()
        
        if products:
            df = pd.DataFrame(products)
            df = calculate_columns(df)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name="products.csv",
                mime="text/csv"
            )
        else:
            st.info("No products found.")
    
    # Tab 2: Add Product
    with tabs[1]:
        st.subheader("Add New Product")
        col1, col2 = st.columns(2)
        
        with col1:
            product_code = st.text_input("Product Code")
            product_name = st.text_input("Product Name")
        
        if st.button("➕ Add Product", key="add_product"):
            if product_code and product_name:
                add_product(product_code, product_name)
                st.success(f"✅ Product '{product_name}' added successfully!")
                st.rerun()
            else:
                st.error("Please fill in all fields.")
    
    # Tab 3: Edit Products
    with tabs[2]:
        st.subheader("Edit Products")
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
                    st.success("✅ Products updated successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error updating products: {str(e)}")
        else:
            st.info("No products to edit.")
    
    # Tab 4: Delete Product
    with tabs[3]:
        st.subheader("Delete Product")
        products = get_all_products()
        
        if products:
            df = pd.DataFrame(products)
            product_to_delete = st.selectbox(
                "Select Product to Delete",
                df["Code"].tolist(),
                format_func=lambda x: f"{x} - {df[df['Code']==x]['Product_Name'].values[0]}"
            )
            
            if st.button("🗑️ Delete Product", key="delete_product"):
                delete_product(product_to_delete)
                st.success("✅ Product deleted successfully!")
                st.rerun()
        else:
            st.info("No products to delete.")


# ============================================================================
# DELIVERY ROUNDS PAGE
# ============================================================================
elif page == "Delivery Rounds":
    st.header("Delivery Rounds Management")
    
    tabs = st.tabs(["View Rounds", "Add Round", "Delete Round"])
    
    # Tab 1: View Delivery Rounds
    with tabs[0]:
        st.subheader("All Delivery Rounds")
        rounds = get_all_delivery_rounds()
        
        if rounds:
            df = pd.DataFrame(rounds)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No delivery rounds found.")
    
    # Tab 2: Add Delivery Round
    with tabs[1]:
        st.subheader("Add New Delivery Round")
        col1, col2 = st.columns(2)
        
        with col1:
            round_name = st.text_input("Round Name (e.g., 'Round 1')")
            round_date = st.date_input("Date")
        
        if st.button("➕ Add Round", key="add_round"):
            if round_name:
                add_delivery_round(round_name, str(round_date))
                st.success(f"✅ Delivery round '{round_name}' added successfully!")
                st.rerun()
            else:
                st.error("Please fill in the round name.")
    
    # Tab 3: Delete Delivery Round
    with tabs[2]:
        st.subheader("Delete Delivery Round")
        rounds = get_all_delivery_rounds()
        
        if rounds:
            df = pd.DataFrame(rounds)
            round_to_delete = st.selectbox(
                "Select Round to Delete",
                df["id"].tolist(),
                format_func=lambda x: f"{df[df['id']==x]['round_name'].values[0]} ({df[df['id']==x]['round_date'].values[0]})"
            )
            
            if st.button("🗑️ Delete Round", key="delete_round"):
                delete_delivery_round(round_to_delete)
                st.success("✅ Delivery round deleted successfully!")
                st.rerun()
        else:
            st.info("No delivery rounds to delete.")


# ============================================================================
# INVENTORY BY ROUND PAGE
# ============================================================================
elif page == "Inventory by Round":
    st.header("Inventory by Delivery Round")
    
    tabs = st.tabs(["View Inventory", "Edit Inventory"])
    
    # Tab 1: View Inventory
    with tabs[0]:
        st.subheader("Inventory by Round")
        
        rounds = get_all_delivery_rounds()
        products = get_all_products()
        
        if rounds and products:
            # Create a view with inventory for each round
            round_names = [r["round_name"] for r in rounds]
            selected_round = st.selectbox("Select Round", round_names)
            
            # Get the round ID
            round_id = next((r["id"] for r in rounds if r["round_name"] == selected_round), None)
            
            if round_id:
                inventory = get_inventory_by_round(round_id)
                if inventory:
                    df = pd.DataFrame(inventory)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No inventory data for this round.")
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
                    
                    if st.button("💾 Save Inventory Changes", key="save_inventory"):
                        try:
                            bulk_update_inventory_by_round(edited_df.to_dict('records'))
                            st.success("✅ Inventory updated successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error updating inventory: {str(e)}")
                else:
                    st.info("No inventory data for this round.")
        else:
            st.info("Please add products and delivery rounds first.")


# ============================================================================
# SHOP MANAGEMENT PAGE
# ============================================================================
elif page == "Shop Management":
    st.header("Shop Management")
    
    tabs = st.tabs(["View Shops", "Add Shop", "Edit Shop", "Delete Shop"])
    
    # Tab 1: View Shops
    with tabs[0]:
        st.subheader("All Shops")
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
            shop_code = st.text_input("Shop Code")
            shop_name = st.text_input("Shop Name")
        
        if st.button("➕ Add Shop", key="add_shop"):
            if shop_code and shop_name:
                add_shop(shop_code, shop_name)
                st.success(f"✅ Shop '{shop_name}' added successfully!")
                st.rerun()
            else:
                st.error("Please fill in all fields.")
    
    # Tab 3: Edit Shop
    with tabs[2]:
        st.subheader("Edit Shop")
        shops = get_all_shops()
        
        if shops:
            df = pd.DataFrame(shops)
            shop_to_edit = st.selectbox(
                "Select Shop to Edit",
                df["id"].tolist(),
                format_func=lambda x: f"{df[df['id']==x]['shop_code'].values[0]} - {df[df['id']==x]['shop_name'].values[0]}"
            )
            
            shop_data = df[df["id"] == shop_to_edit].iloc[0]
            
            col1, col2 = st.columns(2)
            with col1:
                new_code = st.text_input("Shop Code", value=shop_data["shop_code"])
                new_name = st.text_input("Shop Name", value=shop_data["shop_name"])
            
            if st.button("💾 Update Shop", key="update_shop"):
                update_shop(shop_to_edit, new_code, new_name)
                st.success("✅ Shop updated successfully!")
                st.rerun()
        else:
            st.info("No shops to edit.")
    
    # Tab 4: Delete Shop
    with tabs[3]:
        st.subheader("Delete Shop")
        shops = get_all_shops()
        
        if shops:
            df = pd.DataFrame(shops)
            shop_to_delete = st.selectbox(
                "Select Shop to Delete",
                df["id"].tolist(),
                format_func=lambda x: f"{df[df['id']==x]['shop_code'].values[0]} - {df[df['id']==x]['shop_name'].values[0]}",
                key="delete_shop_select"
            )
            
            if st.button("🗑️ Delete Shop", key="delete_shop"):
                delete_shop(shop_to_delete)
                st.success("✅ Shop deleted successfully!")
                st.rerun()
        else:
            st.info("No shops to delete.")


# ============================================================================
# SHOP DISTRIBUTION PAGE
# ============================================================================
elif page == "Shop Distribution":
    st.header("Shop Distribution Management")
    
    tabs = st.tabs(["View Distribution", "Edit Distribution"])
    
    # Tab 1: View Distribution
    with tabs[0]:
        st.subheader("Shop Distribution by Round")
        
        rounds = get_all_delivery_rounds()
        
        if rounds:
            round_names = [r["round_name"] for r in rounds]
            selected_round = st.selectbox("Select Round", round_names)
            
            # Get the round ID
            round_id = next((r["id"] for r in rounds if r["round_name"] == selected_round), None)
            
            if round_id:
                distribution = get_shop_distribution_by_round(round_id)
                if distribution:
                    df = pd.DataFrame(distribution)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No distribution data for this round.")
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
                    
                    if st.button("💾 Save Distribution Changes", key="save_distribution"):
                        try:
                            bulk_update_shop_distribution(edited_df.to_dict('records'))
                            st.success("✅ Distribution updated successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error updating distribution: {str(e)}")
                else:
                    st.info("No distribution data for this round.")
        else:
            st.info("Please add delivery rounds first.")


# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray; font-size: 12px;'>"
    "📦 Inventory Management System | Built with Streamlit"
    "</div>",
    unsafe_allow_html=True
)
