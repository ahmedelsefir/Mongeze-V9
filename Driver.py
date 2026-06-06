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


def render_driver_tracking(user_name, orders, update_firebase_node):
    """Render driver tracking/radar view for picking up orders."""
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
    """Render driver KYC/document verification tab."""
    st.subheader("🎖️ نظام التحقق من الهوية (Know Your Driver - KYC)")

    try:
        kyc_docs = fetch_driver_kyc_documents(user_name)

        if not kyc_docs or "metadata" not in kyc_docs:
            st.info("📝 أنت جديد في النظام. يجب تسجيل وثائقك للتفعيل الكامل.")
            if st.button("🆕 بدء عملية التحقق من الهوية"):
                try:
                    if create_driver_kyc_record(user_name, user_role, car_type="Personal"):
                        st.success("✅ تم إنشاء ملف التحقق الخاص بك! الآن قم برفع الوثائق المطلوبة.")
                        st.session_state["driver_verification_status"] = "Pending Approval"
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ فشل إنشاء ملف التحقق")
                except Exception as e:
                    logger.error(f"Error creating KYC record: {str(e)}")
                    st.error(f"خطأ: {str(e)}")
        else:
            metadata = kyc_docs.get("metadata", {})
            verification_status = metadata.get("verification_status", "Unknown")

            st.markdown("### 📊 حالة التحقق من الهوية")

            if verification_status == "Active":
                st.success("✅ **حالتك مفعّلة** - يمكنك استخدام المنصة بالكامل!")
            elif verification_status == "Rejected":
                rejection_reason = metadata.get("rejection_reason", "لم يتم تحديد السبب")
                st.error(f"❌ **تم رفض طلبك** - السبب: {rejection_reason}")
            else:
                st.warning("⏳ **حالتك معلقة** - جاري المراجعة من قبل الفريق الإداري")

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

            # National ID
            st.markdown("#### 🆔 صورة البطاقة الشخصية")
            national_id_file = st.file_uploader(
                "اختر صورة البطاقة الشخصية",
                type=["jpg", "jpeg", "png", "pdf"],
                key="national_id_uploader",
                help="اختر صورة واضحة لبطاقتك الشخصية (الوجه + الخلف)"
            )

            if national_id_file and st.button("📤 رفع صورة البطاقة"):
                try:
                    with st.spinner("جاري رفع الصورة..."):
                        if upload_document_to_firebase(user_name, "national_id", national_id_file):
                            st.success("✅ تم رفع صورة البطاقة بنجاح!")
                            send_system_email(
                                f"وثيقة جديدة: بطاقة شخصية - {user_name}",
                                f"المندوب {user_name} رفع صورة البطاقة الشخصية للمراجعة"
                            )
                        else:
                            st.error("❌ فشل رفع الصورة. حاول مرة أخرى.")
                except Exception as e:
                    logger.error(f"Error uploading national ID: {str(e)}")
                    st.error(f"خطأ: {str(e)}")

            if "national_id" in kyc_docs and kyc_docs["national_id"].get("file_base64"):
                nat_id_status = kyc_docs["national_id"].get("verified", False)
                st.info(f"📋 البطاقة الشخصية: {'✅ مسجلة' if nat_id_status else '⏳ قيد المراجعة'}")

            st.divider()

            # Driving License
            st.markdown("#### 🚗 رخصة القيادة")
            driving_license_file = st.file_uploader(
                "اختر صورة رخصة القيادة",
                type=["jpg", "jpeg", "png", "pdf"],
                key="driving_license_uploader",
                help="اختر صورة واضحة لرخصة القيادة"
            )

            if driving_license_file and st.button("📤 رفع رخصة القيادة"):
                try:
                    with st.spinner("جاري رفع الوثيقة..."):
                        if upload_document_to_firebase(user_name, "driving_license", driving_license_file):
                            st.success("✅ تم رفع رخصة القيادة بنجاح!")
                            send_system_email(
                                f"وثيقة جديدة: رخصة القيادة - {user_name}",
                                f"المندوب {user_name} رفع صورة رخصة القيادة للمراجعة"
                            )
                        else:
                            st.error("❌ فشل رفع الوثيقة. حاول مرة أخرى.")
                except Exception as e:
                    logger.error(f"Error uploading driving license: {str(e)}")
                    st.error(f"خطأ: {str(e)}")

            if "driving_license" in kyc_docs and kyc_docs["driving_license"].get("file_base64"):
                lic_status = kyc_docs["driving_license"].get("verified", False)
                st.info(f"📋 رخصة القيادة: {'✅ مسجلة' if lic_status else '⏳ قيد المراجعة'}")

            st.divider()

            # Vehicle License (optional)
            st.markdown("#### 🛞 رخصة المركبة (إن وجدت)")
            st.caption("اختياري - رفع هذه الوثيقة إذا كنت تملك مركبة")
            vehicle_license_file = st.file_uploader(
                "اختر صورة رخصة المركبة",
                type=["jpg", "jpeg", "png", "pdf"],
                key="vehicle_license_uploader",
                help="اختر صورة واضحة لرخصة المركبة"
            )

            if vehicle_license_file and st.button("📤 رفع رخصة المركبة"):
                try:
                    with st.spinner("جاري رفع الوثيقة..."):
                        if upload_document_to_firebase(user_name, "vehicle_license", vehicle_license_file):
                            st.success("✅ تم رفع رخصة المركبة بنجاح!")
                            send_system_email(
                                f"وثيقة جديدة: رخصة المركبة - {user_name}",
                                f"المندوب {user_name} رفع صورة رخصة المركبة للمراجعة"
                            )
                        else:
                            st.error("❌ فشل رفع الوثيقة. حاول مرة أخرى.")
                except Exception as e:
                    logger.error(f"Error uploading vehicle license: {str(e)}")
                    st.error(f"خطأ: {str(e)}")

            if "vehicle_license" in kyc_docs and kyc_docs["vehicle_license"].get("file_base64"):
                veh_status = kyc_docs["vehicle_license"].get("verified", False)
                st.info(f"📋 رخصة المركبة: {'✅ مسجلة' if veh_status else '⏳ قيد المراجعة'}")

    except Exception as e:
        logger.error(f"Error in KYC section: {str(e)}")
        st.warning("⚠️ خطأ في قسم التحقق من الهوية")
