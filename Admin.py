"""
Admin.py - Administrative views for the Monjez platform.
Contains: Financial accounting grids and registration/KYC approval console.
All views are imported and rendered from main.py.
"""

import streamlit as st
import pandas as pd
import time
import logging

logger = logging.getLogger(__name__)


def render_admin_tracking(orders, get_live_distance_for_order, format_distance_display):
    """Render admin tracking/oversight dashboard with live distance data."""
    st.subheader("📊 لوحة الرقابة الشاملة للموظفين")
    if orders and len(orders) > 0:
        try:
            df = pd.DataFrame(orders)
            display_cols = ["order_id", "type", "customer", "status", "driver", "price"]
            available_cols = [col for col in display_cols if col in df.columns]
            st.table(df[available_cols])

            st.subheader("📍 المسافات الحية للطلبات النشطة")
            for order in orders:
                if order.get("status") == "الكابتن في الطريق إليك":
                    distance = get_live_distance_for_order(order)
                    distance_text = format_distance_display(distance)
                    st.write(f"🚕 **{order.get('order_id')}** - السائق: {order.get('driver', 'unknown')} | المسافة: {distance_text}")
        except Exception as table_error:
            logger.error(f"Error displaying table: {str(table_error)}")
            st.write(orders)
    else:
        st.info("لا توجد طلبات حالياً")


def render_admin_kyc_console(fetch_from_firebase, update_driver_verification_status,
                             send_system_email):
    """Render admin KYC verification console for approving/rejecting drivers."""
    st.markdown("---")
    st.markdown("## 🔍 لوحة تحكم التحقق من الهوية (Admin KYC Console)")

    try:
        kyc_records = fetch_from_firebase("driver_kyc")

        if kyc_records and len(kyc_records) > 0:
            pending_drivers = []
            for record in kyc_records:
                try:
                    metadata = record.get("metadata", {})
                    if metadata.get("verification_status") == "Pending Approval":
                        pending_drivers.append({
                            "db_id": record.get("db_id"),
                            "driver_name": metadata.get("driver_name", "Unknown"),
                            "created_at": metadata.get("created_at", "N/A"),
                            "documents": record
                        })
                except Exception as e:
                    logger.warning(f"Error processing KYC record: {str(e)}")
                    continue

            if pending_drivers:
                st.subheader(f"📡 رادار المحتاجين للمراجعة ({len(pending_drivers)} معلقة)")

                for driver in pending_drivers:
                    try:
                        driver_name = driver.get("driver_name", "Unknown")
                        created_at = driver.get("created_at", "N/A")

                        with st.expander(f"👤 {driver_name} - المُرسل: {created_at}"):
                            col1, col2, col3 = st.columns(3)

                            with col1:
                                nat_id_exists = "national_id" in driver.get("documents", {})
                                st.metric("🆔 البطاقة", "✅ موجودة" if nat_id_exists else "❌ مفقودة")

                            with col2:
                                lic_exists = "driving_license" in driver.get("documents", {})
                                st.metric("🚗 الرخصة", "✅ موجودة" if lic_exists else "❌ مفقودة")

                            with col3:
                                veh_exists = "vehicle_license" in driver.get("documents", {})
                                st.metric("🛞 المركبة", "✅ موجودة" if veh_exists else "❌ مفقودة")

                            st.divider()

                            st.markdown("### 🎯 الإجراءات الإدارية")

                            col_approve, col_reject = st.columns(2)

                            with col_approve:
                                if st.button(f"🟢 موافقة وتفعيل الحساب - {driver_name}", key=f"approve_{driver_name}"):
                                    try:
                                        if update_driver_verification_status(driver_name, "Active"):
                                            st.success(f"✅ تم تفعيل حساب {driver_name} بنجاح!")
                                            send_system_email(
                                                f"✅ تم الموافقة على حسابك - {driver_name}",
                                                f"تم الموافقة على طلب التحقق من هويتك. يمكنك الآن استخدام المنصة بالكامل والقبول على الطلبات!"
                                            )
                                            logger.info(f"Driver {driver_name} approved")
                                            time.sleep(1)
                                            st.rerun()
                                        else:
                                            st.error("❌ فشلت عملية التفعيل")
                                    except Exception as e:
                                        logger.error(f"Error approving driver: {str(e)}")
                                        st.error(f"خطأ: {str(e)}")

                            with col_reject:
                                rejection_reason = st.text_input(
                                    "سبب الرفض (إن وجد):",
                                    placeholder="مثال: الوثائق غير واضحة",
                                    key=f"reject_reason_{driver_name}"
                                )

                                if st.button(f"🔴 رفض الطلب - {driver_name}", key=f"reject_{driver_name}"):
                                    try:
                                        if not rejection_reason.strip():
                                            st.error("❌ يجب إدخال سبب الرفض")
                                        else:
                                            if update_driver_verification_status(driver_name, "Rejected", rejection_reason.strip()):
                                                st.success(f"✅ تم رفض طلب {driver_name}")
                                                send_system_email(
                                                    f"❌ تم رفض طلبك - {driver_name}",
                                                    f"للأسف، تم رفض طلب التحقق من هويتك. السبب: {rejection_reason}\n\nيمكنك إعادة محاولة رفع الوثائق مرة أخرى."
                                                )
                                                logger.info(f"Driver {driver_name} rejected")
                                                time.sleep(1)
                                                st.rerun()
                                            else:
                                                st.error("❌ فشلت عملية الرفض")
                                    except Exception as e:
                                        logger.error(f"Error rejecting driver: {str(e)}")
                                        st.error(f"خطأ: {str(e)}")

                    except Exception as display_error:
                        logger.warning(f"Error displaying driver: {str(display_error)}")
                        continue

            else:
                st.info("✅ لا توجد طلبات معلقة للمراجعة - جميع المندوبين تم مراجعتهم!")

        else:
            st.info("📭 لا توجد طلبات KYC حتى الآن")

    except Exception as e:
        logger.error(f"Error in admin KYC console: {str(e)}")
        st.error("⚠️ خطأ في تحميل لوحة التحكم")
