import streamlit as st
import pandas as pd

st.set_page_config(page_title="Prep and Prime GH Inventory", layout="wide")

st.title("💄 Prep and Prime GH - Inventory Management")

# Load or initialize inventory
if "inventory" not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=["Product", "Category", "Quantity", "Price", "Supplier"])

# Add Product
with st.form("add_product"):
    st.subheader("Add New Product")
    col1, col2, col3 = st.columns(3)
    product = col1.text_input("Product Name")
    category = col2.text_input("Category")
    price = col3.number_input("Price (GHS)", min_value=0.0, step=0.5)
    supplier = st.text_input("Supplier")
    quantity = st.number_input("Quantity", min_value=0, step=1)
    add_btn = st.form_submit_button("Add to Inventory")
    if add_btn and product:
        new_row = {"Product": product, "Category": category, "Quantity": quantity, "Price": price, "Supplier": supplier}
        st.session_state.inventory = st.session_state.inventory.append(new_row, ignore_index=True)
        st.success(f"{product} added to inventory!")

# View & Update Inventory
st.subheader("📋 Inventory List")
st.dataframe(st.session_state.inventory, use_container_width=True)

# Update Stock
st.markdown("---")
st.subheader("Update Stock")
product_list = st.session_state.inventory["Product"].tolist()
if product_list:
    selected = st.selectbox("Select Product", product_list)
    qty_change = st.number_input("Change in Quantity (+/-)", min_value=-100, max_value=100, step=1)
    if st.button("Update Quantity"):
        idx = st.session_state.inventory.index[st.session_state.inventory["Product"] == selected][0]
        st.session_state.inventory.at[idx, "Quantity"] += qty_change
        st.success(f"Updated quantity for {selected}!")
else:
    st.info("No products yet. Add some above.")

# Low Stock Alert
low_stock = st.session_state.inventory[st.session_state.inventory["Quantity"] <= 5]
if not low_stock.empty:
    st.warning("🚨 Low Stock Alert:")
    st.dataframe(low_stock)

# Export Inventory
st.markdown("---")
csv = st.session_state.inventory.to_csv(index=False).encode("utf-8")
st.download_button("Download Inventory CSV", csv, "prep_prime_inventory.csv", "text/csv")

