import streamlit as st
import requests

def fetch_all_baserow_rows():
    url = f"https://api.baserow.io/api/database/rows/table/597466/?user_field_names=true&size=200"
    headers = {"Authorization": f"Token itdTVpCYfsZSCxm5jGMrmneReLzkGndD"}
    all_rows = []
    while url:
        response = requests.get(url, headers=headers)
        st.write("DEBUG: RESPONSE STATUS", response.status_code)
        st.write("DEBUG: RESPONSE TEXT", response.text)
        if response.status_code != 200:
            st.error(f"Error fetching from Baserow: {response.status_code} - {response.text}")
            return []
        data = response.json()
        all_rows.extend(data.get("results", []))
        url = data.get("next", None)
    return all_rows

rows = fetch_all_baserow_rows()
st.write("DEBUG: RAW ROWS", rows)
