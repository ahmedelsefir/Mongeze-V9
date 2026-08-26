# 🚀 Mongeze-V9 AI Agent Guidelines & Architecture Rules

This repository contains the core logic for the **Monjez (مُنجز)** multi-service logistics and ride-hailing platform. Any AI agent (Cursor, Claude Code, GitHub Copilot, etc.) modifying or generating code in this repository MUST follow the strict guidelines below.

---

## 🛠️ Tech Stack & Design Architecture
- **Language:** Python 3.10+
- **UI Framework:** Streamlit
- **Backend & Database:** Firebase Firestore / Firebase Realtime Database
- **Payment Gateway:** Paymob Integration (`paymob.py`)
- **Design Pattern:** Object-Oriented Programming (OOP) using `@dataclass` for Domain Models.

---

## ⚠️ Mandatory Streamlit UI Rules (Strict Enforcement)

1. **Forms & Buttons Rule:**
   - **NEVER** place a standard `st.button()` inside an `st.form()`. Streamlit will throw a `StreamlitAPIException`.
   - Use `st.form_submit_button()` for form submissions.
   - For secondary actions (like wallet top-ups or navigation), set a flag in `st.session_state` inside the form, call `st.rerun()`, and render the `st.button()` **outside** the form block.

2. **View Function Signatures:**
   - ALL page-rendering functions (e.g., `render_parcels_page`, `render_taxi_page`, `render_chat_page`, `render_customer_tracking`) **MUST** include `**kwargs` in their parameter lists to handle dynamic UI state routing without throwing `TypeError`.

3. **Unique Keys:**
   - Every interactive Streamlit component (`st.button`, `st.text_input`, `st.radio`, `st.number_input`) must have a unique `key` parameter to prevent key collision exceptions.

---

## 🧱 Data Models & OOP Conventions

- Every business entity (e.g., `ParcelOrder`, `TaxiOrder`) must be defined as a Python `@dataclass`.
- Entities must encapsulate their own logic:
  - `validate_payment(wallet_balance: float) -> tuple[bool, Optional[str]]`
  - `generate_html_email() -> str` (Outputs professional HTML invoice template)
  - `to_dict() -> Dict[str, Any]` (Prepares clean payload for Firebase)

---

## 🔐 Database & Error Handling Guidelines

1. **Firebase Network Safety:**
   - Wrap ALL database operations (read/write/update) in `try-except` blocks.
   - Handle database disconnections gracefully without crashing the Streamlit session UI.

2. **Logging Standard:**
   - **DO NOT** use `print()` statements for system logging.
   - Always use standard Python logging: `logger.error()`, `logger.warning()`, and `logger.info()`.

3. **Secure Secrets Management:**
   - API Keys, service account JSON data, and secret keys must be retrieved from `st.secrets` or environment variables, never hardcoded.

---

## 💬 Real-Time Chat & Support System
- Support channels created via chat must write directly to `chats/{order_id}/support_request`.
- Cancelled orders must update status in `orders/{db_id}` and log the action via `log_accounting_entry`.
