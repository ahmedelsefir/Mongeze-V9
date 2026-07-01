"""
Driver.py - Driver/Captain views for the Monjez platform.
Contains: Radar tracking, wallet dashboard, and KYC/document verification views.
All views are imported and rendered from main.py.
"""

import html
import streamlit as st
from datetime import datetime
import time
import logging

logger = logging.getLogger(__name__)


def render_driver_tracking(user_name, orders, update_firebase_node,
                           fetch_driver_kyc_documents=None):
    """Render driver tracking/radar view for picking up orders."""
    # Sync verification status from Firebase on every load (avoids stale session state)
    if fetch_driver_kyc_documents is not None:
        try:
            kyc_docs = fetch_driver_kyc_documents(user_name)
            if kyc_docs and isinstance(kyc_docs, dict):
                metadata = kyc_docs.get("metadata", {})
                status = metadata.get("verification_status", "Pending Manual Review")
                st.session_state["driver_verification_status"] = status
        except Exception as e:
            logger.warning(f"Error fetching driver KYC status: {str(e)}")

    # Block unverified drivers from picking up orders
    driver_status = st.session_state.get("driver_verification_status", "Pending Manual Review")
    if driver_status != "Active":
        st.error("🔒 **Account Locked — Pending Manual Review**")
        st.warning("⏳ You cannot accept orders until your account is activated by the admin team. Go to Settings → Identity Verification to proceed.")
        return

    st.subheader("🚕 Available Orders in Network:")
    if orders and len(orders) > 0:
        available_orders = [o for o in orders if o.get("status") == "Searching for Driver"]
        if available_orders:
            for o in available_orders:
                try:
                    st.markdown(f"**📦 New {o.get('type', 'Order')}!** | Customer: {o.get('customer', 'unknown')} | Fare: EGP {o.get('price', 0)}")
                    if o.get('from'):
                        st.write(f"📍 From: {o.get('from')} → To: {o.get('to', 'unknown')}")
                    if o.get('details'):
                        st.write(f"📝 Details: {o.get('details')}")

                    if st.button(f"✅ Accept Order {o.get('order_id')}", key=o.get('order_id')):
                        try:
                            url_patch = f"orders/{o.get('db_id')}"
                            if update_firebase_node(url_patch, {"status": "Driver En Route", "driver": user_name}):
                                st.success("🚀 Order accepted! Go to Chat to communicate with the customer.")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ Failed to accept order. Please try again.")
                        except Exception as accept_error:
                            logger.error(f"Error accepting order: {str(accept_error)}")
                            st.error(f"Error: {str(accept_error)}")
                except Exception as order_display_error:
                    logger.warning(f"Error displaying order: {str(order_display_error)}")
                    continue
        else:
            st.write("✅ Network is clear. No pending orders available at this time.")
    else:
        st.write("✅ Network is clear. No pending orders available at this time.")


def render_driver_settings_tab(user_name, fetch_driver_account, save_driver_account, send_system_email):
    """Render driver wallet/payout settings tab."""
    st.subheader("🚕 Driver Settings")
    st.markdown("### 💰 Payment Account Registration")
    st.caption("Register your bank account details securely — all data is encrypted on the server")

    try:
        driver_account = fetch_driver_account(user_name)

        current_method = driver_account.get("payment_method") or "Select Method"
        current_account = driver_account.get("account_number") or ""

        with st.form("driver_payout_form"):
            col1, col2 = st.columns(2)

            with col1:
                payment_method = st.selectbox(
                    "💳 Preferred Payment Method:",
                    options=["Select Method", "Vodafone Cash 🟠", "InstaPay 💳", "Bank Transfer 🏦"],
                    index=0,
                    help="Choose your preferred method for fund transfers"
                )

            with col2:
                account_num = st.text_input(
                    "📱 Account / Phone Number:",
                    value=current_account,
                    placeholder="Enter your phone number or bank account number",
                    help="Your wallet or bank account number"
                )

            st.info("🔐 Security Notice: Verify your details before saving — changes cannot be easily reversed")

            if st.form_submit_button("✅ Save Payment Account", use_container_width=True):
                try:
                    if payment_method == "Select Method":
                        st.error("❌ Please select a payment method first")
                    elif not account_num.strip():
                        st.error("❌ Please enter an account number")
                    else:
                        account_data = {
                            "payment_method": payment_method,
                            "account_number": account_num.strip(),
                            "verified": False,
                            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }

                        if save_driver_account(user_name, account_data):
                            st.success("✅ Payment account saved successfully! Admin team will verify the details")
                            send_system_email(
                                f"New Payout Account Registration - {user_name}",
                                f"Driver {user_name} registered a new payment account: {payment_method}"
                            )
                            logger.info(f"Driver account saved for: {user_name}")
                        else:
                            st.error("❌ Failed to save account details. Please try again.")
                except Exception as e:
                    logger.error(f"Error saving driver account: {str(e)}")
                    st.error(f"Error: {str(e)}")

        # Display current account info (if exists)
        if driver_account and driver_account.get("account_number"):
            st.divider()
            st.markdown("### 📋 Current Account Information")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Payment Method", driver_account.get("payment_method", "Not Set"))
            with col2:
                masked_account = "*" * (len(str(driver_account.get("account_number", ""))) - 4) + str(driver_account.get("account_number", ""))[-4:]
                st.metric("Account (Masked)", masked_account)
            with col3:
                st.metric("Status", "✅ Verified" if driver_account.get("verified") else "⏳ Under Review")

    except Exception as e:
        logger.error(f"Error in driver settings: {str(e)}")
        st.warning("⚠️ Error loading driver settings")


def render_wallet_topup(user_name, initiate_wallet_topup_fn=None):
    """Render Paymob wallet top-up section for drivers.

    Args:
        user_name: The driver's username.
        initiate_wallet_topup_fn: callable from paymob.initiate_wallet_topup.
    """
    st.divider()
    st.markdown("### 💳 Top Up Wallet via Paymob")
    st.caption("Pay with Vodafone Cash or credit card to instantly add funds to your wallet")

    try:
        with st.form("wallet_topup_form"):
            col1, col2 = st.columns(2)

            with col1:
                topup_amount = st.number_input(
                    "💵 Amount (EGP):",
                    min_value=10.0,
                    max_value=50000.0,
                    value=100.0,
                    step=10.0,
                    help="Enter the amount you want to deposit in Egyptian Pounds"
                )

            with col2:
                topup_method = st.selectbox(
                    "📱 Payment Method:",
                    options=["💳 Credit Card", "📲 Vodafone Cash"],
                    help="Choose your preferred payment method"
                )

            if st.form_submit_button("🚀 Proceed to Payment", use_container_width=True):
                if not initiate_wallet_topup_fn:
                    st.warning("⚠️ Paymob service is currently unavailable — please contact admin")
                    logger.warning("initiate_wallet_topup_fn not provided — Paymob not configured")
                else:
                    try:
                        payment_method = "wallet" if "Vodafone" in topup_method else "card"
                        driver_info = {
                            "first_name": user_name.split()[0] if user_name else "Driver",
                            "last_name": user_name.split()[-1] if user_name and len(user_name.split()) > 1 else "Monjez",
                            "email": "driver@monjez.app",
                            "phone_number": "+20000000000",
                        }

                        with st.spinner("⏳ Preparing payment gateway..."):
                            result = initiate_wallet_topup_fn(
                                driver_username=user_name,
                                amount_egp=topup_amount,
                                driver_info=driver_info,
                                payment_method=payment_method,
                            )

                        if result and result.get("checkout_url"):
                            st.success(f"✅ Payment ready — Amount: EGP {topup_amount}")
                            st.markdown(
                                f'<a href="{html.escape(str(result["checkout_url"]))}" target="_blank">'
                                f'<button style="background-color:#4CAF50;color:white;padding:12px 24px;'
                                f'border:none;border-radius:8px;cursor:pointer;font-size:16px;width:100%">'
                                f'💳 Go to Secure Payment Gateway</button></a>',
                                unsafe_allow_html=True,
                            )
                            st.info(f"🔑 Order ID: {result.get('order_id', 'N/A')}")
                            logger.info(f"Wallet topup checkout ready: {user_name}, {topup_amount} EGP via {payment_method}")
                        elif result:
                            st.warning("⚠️ Payment prepared but payment gateway URL unavailable — check PAYMOB_IFRAME_ID configuration")
                        else:
                            st.error("❌ Failed to prepare payment — check Paymob settings")
                    except Exception as e:
                        logger.error(f"Error initiating wallet topup: {e}")
                        st.error(f"❌ Payment error: {e}")

    except Exception as e:
        logger.error(f"Error in wallet topup section: {e}")
        st.warning("⚠️ Error loading wallet top-up section")


def render_driver_kyc_tab(user_name, user_role, fetch_driver_kyc_documents,
                          create_driver_kyc_record, upload_document_to_firebase,
                          send_system_email):
    """Render driver KYC/document verification tab with account lock until approved."""
    st.subheader("🎖️ Identity Verification System (Know Your Driver - KYC)")

    try:
        kyc_docs = fetch_driver_kyc_documents(user_name)

        if not kyc_docs or "metadata" not in kyc_docs:
            # New driver — account locked, must register
            st.error("🔒 **Account Locked — Pending Manual Review**")
            st.warning(
                "You must register your documents and receive admin approval before accepting any orders. "
                "Upload the required documents below to start the verification process."
            )
            if st.button("🆕 Start Identity Verification"):
                try:
                    if create_driver_kyc_record(user_name, user_role, car_type="Personal"):
                        st.success("✅ Verification profile created! Now upload your required documents.")
                        st.session_state["driver_verification_status"] = "Pending Manual Review"
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Failed to create verification profile")
                except Exception as e:
                    logger.error(f"Error creating KYC record: {str(e)}")
                    st.error(f"Error: {str(e)}")
        else:
            metadata = kyc_docs.get("metadata", {})
            verification_status = metadata.get("verification_status", "Pending Manual Review")

            # Update session state for use in tracking page lock
            st.session_state["driver_verification_status"] = verification_status

            st.markdown("### 📊 Verification Status")

            if verification_status == "Active":
                st.success("✅ **Status: Active** - You have full platform access!")
            elif verification_status == "Rejected":
                rejection_reason = metadata.get("rejection_reason", "Reason not specified")
                st.error(f"❌ **Application Rejected** - Reason: {rejection_reason}")
                st.info("You can resubmit your documents after correcting the issue for re-review.")
            else:
                st.error("🔒 **Account Locked — Pending Manual Review**")
                st.warning("⏳ Your application is under review by the admin team. You cannot accept orders until approved.")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Status", verification_status)
            with col2:
                created_date = metadata.get("created_at", "N/A")
                st.metric("Application Date", created_date[:10] if created_date else "N/A")
            with col3:
                st.metric("Role", metadata.get("user_role", "Unknown"))

            st.divider()

            st.markdown("### 📄 Upload Required Documents")
            st.caption("All documents must be uploaded to fully activate your account")

            # Document upload slots
            _render_doc_upload(
                user_name, kyc_docs, "national_id",
                "🆔 National ID Card",
                "Select National ID image",
                "Choose a clear image of both sides of your national ID card",
                upload_document_to_firebase, send_system_email
            )

            st.divider()

            _render_doc_upload(
                user_name, kyc_docs, "driving_license",
                "🚗 Driving License",
                "Select Driving License image",
                "Choose a clear image of your valid driving license",
                upload_document_to_firebase, send_system_email
            )

            st.divider()

            _render_doc_upload(
                user_name, kyc_docs, "vehicle_license",
                "🛞 Vehicle Registration",
                "Select Vehicle Registration image",
                "Choose a clear image of your vehicle registration certificate",
                upload_document_to_firebase, send_system_email
            )

    except Exception as e:
        logger.error(f"Error in KYC section: {str(e)}")
        st.warning("⚠️ Error loading identity verification section")


def _render_doc_upload(user_name, kyc_docs, doc_type, title, label, help_text,
                       upload_document_to_firebase, send_system_email):
    """Render a single document upload slot with status indicator."""
    st.markdown(f"#### {title}")

    uploaded_file = st.file_uploader(
        label,
        type=["jpg", "jpeg", "png", "pdf"],
        key=f"{doc_type}_uploader",
        help=help_text
    )

    if uploaded_file and st.button(f"📤 Upload {title.split(' ', 1)[-1]}", key=f"upload_{doc_type}"):
        try:
            with st.spinner("Uploading document..."):
                if upload_document_to_firebase(user_name, doc_type, uploaded_file):
                    st.success(f"✅ {title} uploaded successfully!")
                    send_system_email(
                        f"New Document: {doc_type} - {user_name}",
                        f"Driver {user_name} uploaded {doc_type} for review"
                    )
                else:
                    st.error("❌ Failed to upload document. Please try again.")
        except Exception as e:
            logger.error(f"Error uploading {doc_type}: {str(e)}")
            st.error(f"Error: {str(e)}")

    existing_doc = kyc_docs.get(doc_type, {})
    if isinstance(existing_doc, dict) and existing_doc.get("file_base64"):
        is_verified = existing_doc.get("verified", False)
        st.info(f"📋 {title}: {'✅ Verified' if is_verified else '⏳ Under Review'}")
