import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# 1. Functional Error Handler (More than just a print)
def handle_error(e, context="System"):
    """Captures and displays errors professionally in the UI."""
    error_details = f"[{datetime.now().strftime('%H:%M:%S')}] {context} Error: {str(e)}"
    logger.error(error_details)
    st.error(f"⚠️ {context} issue detected. Please check your connection or secrets.")

# 2. Functional Smart Sync (Replacing 'pass' with real logic)
def smart_sync(data_to_send):
    """Sends data to Slack and Notion simultaneously."""
    try:
        # Slack Automation
        slack_url = st.secrets["slack"]["webhook_url"]
        slack_response = requests.post(slack_url, json={"text": f"🚀 New Entry: {data_to_send['name']} - {data_to_send['amount']} EGP"}, timeout=10)
        if not slack_response.ok:
            logger.warning(f"Slack webhook returned status {slack_response.status_code}: {slack_response.text}")
        
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
        notion_response = requests.post("https://api.notion.com/v1/pages", headers=notion_headers, json=notion_payload, timeout=10)
        if not notion_response.ok:
            logger.warning(f"Notion API returned status {notion_response.status_code}: {notion_response.text}")
        
        if slack_response.ok and notion_response.ok:
            st.success("✨ Data synced to Slack & Notion!")
        else:
            st.warning("⚠️ Partial sync: check logs for details.")
        return True
    except KeyError as e:
        handle_error(e, context="Sync Engine (missing config key)")
        return False
    except requests.exceptions.Timeout as e:
        handle_error(e, context="Sync Engine (timeout)")
        return False
    except requests.exceptions.RequestException as e:
        handle_error(e, context="Sync Engine (network)")
        return False
    except Exception as e:
        handle_error(e, context="Sync Engine")
        return False

# 3. Functional Dashboard (Replacing 'pass' with math logic)
def accounting_dashboard(df):
    """Calculates and shows revenue stats on screen."""
    try:
        if df is None or df.empty:
            st.info("📊 No data available for the dashboard.")
            return
        
        if 'amount' not in df.columns:
            logger.warning("Dashboard: 'amount' column missing from DataFrame")
            st.warning("⚠️ Revenue data format is unexpected — 'amount' column not found.")
            return
        
        total = df['amount'].sum()
        st.metric("Total Revenue", f"{total:,.2f} EGP")
        
        if 'service' in df.columns:
            st.bar_chart(df.groupby('service')['amount'].sum())
        else:
            logger.info("Dashboard: 'service' column not found, skipping chart")
    except Exception as e:
        handle_error(e, context="Dashboard")
