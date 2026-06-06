"""
Driver.py - Driver/Captain views for the Monjez platform.
Contains: Radar tracking, wallet dashboard, and KYC/document verification views.
All views are imported and rendered from main.py.
"""

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
        st.error("🔒 **حسابك مقفل — Pending Manual Review**")
        st.warning("⏳ لا يمكنك قبول طلبات حتى يتم تفعيل حسابك من قبل الإدارة. اذهب إلى إعدادات ← التحقق من الهوية لرفع وثائقك.")
        return

    st.subheader("🚕 الطلبات المتاحة في رادار السوق للالتقاط فوراً:")
    if orders and len(orders) > 0:
        available_orders = [o for o in orders if o.get("status") == "جاري البحث عن كابتن"]
        if available_orders:
            for o in available_orders:
                try:
                    st.markdown(f"**📦 {o.get('type', 'طلب')} جديد!** | العميل: {o.get('customer', 'unknown')} | السعر: {o.get('price', 0)} ج.م")
                    if o.get('from'):
                        st.write(f"📍 من: {o.get('from')} -> إلى: {o.get('to', 'unknown')}")
                    if o.get('details'):
                        st.write(f"📝 التفاصيل: {o.get('details')}")

                    if st.button(f"✅ وافق واستلم الطلب {o.get('order_id')}", key=o.get('order_id')):
                        try:
                            url_patch = f"orders/{o.get('db_id')}"
                            if update_firebase_node(url_patch, {"status": "الكابتن في الطريق إليك", "driver": user_name}):
                                st.success("🚀 تم حجز وتعميد الطلب باسمك يا كابتن! انتقل لغرفة الشات للتواصل مع العميل.")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ فشل حجز الطلب. حاول مرة أخرى.")
                        except Exception as accept_error:
                            logger.error(f"Error accepting order: {str(accept_error)}")
                            st.error(f"خطأ: {str(accept_error)}")
                except Exception as order_display_error:
                    logger.warning(f"Error displaying order: {str(order_display_error)}")
                    continue
        else:
            st.write("✅ الرادار نظيف، لا توجد طلبات معلقة حالياً في السوق.")
    else:
        st.write("✅ الرادار نظيف، لا توجد طلبات معلقة حالياً في السوق.")


def render_driver_settings_tab(user_name, fetch_driver_account, save_driver_account, send_system_email):
    """Render driver wallet/payout settings tab."""
    st.subheader("🚕 إعدادات المندوب (Driver Settings)")
    st.markdown("### 💰 تسجيل حسابات السحب والدفع")
    st.caption("قم بتسجيل معلومات حسابك البنكي بأمان تام - البيانات مشفرة في الخادم")

    try:
        driver_account = fetch_driver_account(user_name)

        current_method = driver_account.get("payment_method") or "اختر الطريقة"
        current_account = driver_account.get("account_number") or ""

        with st.form("driver_payout_form"):
            col1, col2 = st.columns(2)

            with col1:
                payment_method = st.selectbox(
                    "💳 طريقة الدفع المفضلة:",
                    options=["اختر الطريقة", "Vodafone Cash 🟠", "InstaPay 💳", "Bank Transfer 🏦"],
                    index=0,
                    help="اختر طريقة تحويل الرصيد المفضلة لديك"
                )

            with col2:
                account_num = st.text_input(
                    "📱 رقم الحساب / الهاتف:",
                    value=current_account,
                    placeholder="أدخل رقم هاتفك أو رقم حسابك البنكي",
                    help="رقم محفظتك أو حسابك البنكي"
                )

            st.info("🔐 تحذير أمني: تأكد من صحة البيانات قبل الحفظ - لا يمكن الرجوع فيها بسهولة")

            if st.form_submit_button("✅ حفظ حساب السحب بأمان", use_container_width=True):
                try:
                    if payment_method == "اختر الطريقة":
                        st.error("❌ يجب اختيار طريقة دفع أولاً")
                    elif not account_num.strip():
                        st.error("❌ يجب إدخال رقم الحساب")
                    else:
                        account_data = {
                            "payment_method": payment_method,
                            "account_number": account_num.strip(),
                            "verified": False,
                            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }

                        if save_driver_account(user_name, account_data):
                            st.success("✅ تم حفظ معلومات حسابك بنجاح! سيتم تحقق الفريق من البيانات")
                            send_system_email(
                                f"تسجيل حساب سحب جديد - {user_name}",
                                f"المندوب {user_name} قام بتسجيل حساب: {payment_method}"
                            )
                            logger.info(f"Driver account saved for: {user_name}")
                        else:
                            st.error("❌ فشل حفظ البيانات. حاول مرة أخرى.")
                except Exception as e:
                    logger.error(f"Error saving driver account: {str(e)}")
                    st.error(f"خطأ: {str(e)}")

        # Display current account info (if exists)
        if driver_account and driver_account.get("account_number"):
            st.divider()
            st.markdown("### 📋 معلومات الحساب الحالية")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("طريقة الدفع", driver_account.get("payment_method", "غير محدد"))
            with col2:
                masked_account = "*" * (len(str(driver_account.get("account_number", ""))) - 4) + str(driver_account.get("account_number", ""))[-4:]
                st.metric("الحساب (مشفر)", masked_account)
            with col3:
                st.metric("الحالة", "✅ مسجل" if driver_account.get("verified") else "⏳ قيد التحقق")

    except Exception as e:
        logger.error(f"Error in driver settings: {str(e)}")
        st.warning("⚠️ خطأ في تحميل إعدادات المندوب")


def render_driver_kyc_tab(user_name, user_role, fetch_driver_kyc_documents,
                          create_driver_kyc_record, upload_document_to_firebase,
                          send_system_email):
    """Render driver KYC/document verification tab with account lock until approved."""
    st.subheader("🎖️ نظام التحقق من الهوية (Know Your Driver - KYC)")

    try:
        kyc_docs = fetch_driver_kyc_documents(user_name)

        if not kyc_docs or "metadata" not in kyc_docs:
            # New driver — account locked, must register
            st.error("🔒 **حسابك مقفل — Pending Manual Review**")
            st.warning(
                "يجب تسجيل وثائقك والحصول على موافقة الإدارة قبل قبول أي طلبات. "
                "ارفع الوثائق المطلوبة أدناه لبدء عملية التحقق."
            )
            if st.button("🆕 بدء عملية التحقق من الهوية"):
                try:
                    if create_driver_kyc_record(user_name, user_role, car_type="Personal"):
                        st.success("✅ تم إنشاء ملف التحقق الخاص بك! الآن قم برفع الوثائق المطلوبة.")
                        st.session_state["driver_verification_status"] = "Pending Manual Review"
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ فشل إنشاء ملف التحقق")
                except Exception as e:
                    logger.error(f"Error creating KYC record: {str(e)}")
                    st.error(f"خطأ: {str(e)}")
        else:
            metadata = kyc_docs.get("metadata", {})
            verification_status = metadata.get("verification_status", "Pending Manual Review")

            # Update session state for use in tracking page lock
            st.session_state["driver_verification_status"] = verification_status

            st.markdown("### 📊 حالة التحقق من الهوية")

            if verification_status == "Active":
                st.success("✅ **حالتك مفعّلة** - يمكنك استخدام المنصة بالكامل!")
            elif verification_status == "Rejected":
                rejection_reason = metadata.get("rejection_reason", "لم يتم تحديد السبب")
                st.error(f"❌ **تم رفض طلبك** - السبب: {rejection_reason}")
                st.info("يمكنك إعادة رفع الوثائق بعد تصحيح المشكلة وستتم مراجعتها مجدداً.")
            else:
                st.error("🔒 **حسابك مقفل — Pending Manual Review**")
                st.warning("⏳ جاري المراجعة من قبل الفريق الإداري. لا يمكنك قبول طلبات حتى يتم التفعيل.")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("الحالة", verification_status)
            with col2:
                created_date = metadata.get("created_at", "N/A")
                st.metric("تاريخ الطلب", created_date[:10] if created_date else "N/A")
            with col3:
                st.metric("النوع", metadata.get("user_role", "Unknown"))

            st.divider()

            st.markdown("### 📄 رفع الوثائق المطلوبة")
            st.caption("يجب رفع جميع الوثائق أدناه لتفعيل حسابك بالكامل")

            # Document upload slots
            _render_doc_upload(
                user_name, kyc_docs, "national_id",
                "🆔 صورة البطاقة الشخصية (National ID)",
                "اختر صورة البطاقة الشخصية",
                "اختر صورة واضحة لبطاقتك الشخصية (الوجه + الخلف)",
                upload_document_to_firebase, send_system_email
            )

            st.divider()

            _render_doc_upload(
                user_name, kyc_docs, "driving_license",
                "🚗 رخصة القيادة (Driving License)",
                "اختر صورة رخصة القيادة",
                "اختر صورة واضحة لرخصة القيادة",
                upload_document_to_firebase, send_system_email
            )

            st.divider()

            _render_doc_upload(
                user_name, kyc_docs, "vehicle_license",
                "🛞 رخصة المركبة (Vehicle Registration)",
                "اختر صورة رخصة المركبة",
                "اختر صورة واضحة لرخصة المركبة",
                upload_document_to_firebase, send_system_email
            )

    except Exception as e:
        logger.error(f"Error in KYC section: {str(e)}")
        st.warning("⚠️ خطأ في قسم التحقق من الهوية")


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

    if uploaded_file and st.button(f"📤 رفع {title.split(' ', 1)[-1]}", key=f"upload_{doc_type}"):
        try:
            with st.spinner("جاري رفع الوثيقة..."):
                if upload_document_to_firebase(user_name, doc_type, uploaded_file):
                    st.success(f"✅ تم رفع {title} بنجاح!")
                    send_system_email(
                        f"وثيقة جديدة: {doc_type} - {user_name}",
                        f"المندوب {user_name} رفع وثيقة {doc_type} للمراجعة"
                    )
                else:
                    st.error("❌ فشل رفع الوثيقة. حاول مرة أخرى.")
        except Exception as e:
            logger.error(f"Error uploading {doc_type}: {str(e)}")
            st.error(f"خطأ: {str(e)}")

    existing_doc = kyc_docs.get(doc_type, {})
    if isinstance(existing_doc, dict) and existing_doc.get("file_base64"):
        is_verified = existing_doc.get("verified", False)
        st.info(f"📋 {title}: {'✅ تم التحقق' if is_verified else '⏳ قيد المراجعة'}")
