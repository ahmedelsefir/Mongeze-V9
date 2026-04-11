import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# 1. Functional Error Handler (More than just a print)
def handle_error(e, context="System"):
    """Captures and displays errors professionally in the UI."""
    error_details = f"[{datetime.now().strftime('%H:%M:%S')}] {context} Error: {str(e)}"
    print(error_log) # For terminal debugging
    st.error(f"⚠️ {context} issue detected. Please check your connection or secrets.")

# 2. Functional Smart Sync (Replacing 'pass' with real logic)
def smart_sync(data_to_send):
    """Sends data to Slack and Notion simultaneously."""
    try:
        # Slack Automation
        slack_url = st.secrets["slack"]["webhook_url"]
        requests.post(slack_url, json={"text": f"🚀 New Entry: {data_to_send['name']} - {data_to_send['amount']} EGP"}, timeout=10)
        
        # Notion Automation
        notion_headers = {
            "Authorization": f"Bearer {st.secrets['notion']['token']}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        notion_payload = {
            "parent": {"database_id": st.secrets["notion"]["database_id"]},
            "properties": {
                "Title": {"title": [{"text": {"content": data_to_send['name']}}]},
                "Amount": {"number": float(data_to_send['amount'])}
            }
        }
        requests.post("https://api.notion.com/v1/pages", headers=notion_headers, json=notion_payload, timeout=10)
        
        st.success("✨ Data synced to Slack & Notion!")
        return True
    except Exception as e:
        handle_error(e, context="Sync Engine")
        return False

# 3. Functional Dashboard (Replacing 'pass' with math logic)
def accounting_dashboard(df):
    """Calculates and shows revenue stats on screen."""
    try:
        if not df.empty:
            total = df['amount'].sum()
            st.metric("Total Revenue", f"{total:,.2f} EGP")
            st.bar_chart(df.groupby('service')['amount'].sum())
    except Exception as e:
        handle_error(e, context="Dashboard")
