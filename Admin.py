"""
Admin.py - Administrative views for the Monjez platform.
Contains: Financial accounting grids, KYC verification radar, and live commission engine.
All views are imported and rendered from main.py.
"""

import streamlit as st
import pandas as pd
import base64
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

COMMISSION_RATE = 0.10  # 10% platform commission


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


# ========================================================
# 📡 Admin Verification Radar — Review & Approve/Reject Drivers
# ========================================================

def render_admin_kyc_console(fetch_from_firebase, update_driver_verification_status,
                             send_system_email):
    """Render admin KYC verification radar for reviewing, approving, or rejecting drivers."""
    st.markdown("---")
    st.markdown("## 📡 رادار التحقق من المندوبين (Verification Radar)")

    try:
        kyc_records = fetch_from_firebase("driver_kyc")

        if kyc_records and len(kyc_records) > 0:
            pending_drivers = []
            for record in kyc_records:
                try:
                    metadata = record.get("metadata", {})
                    status = metadata.get("verification_status", "")
                    if status in ("Pending Approval", "Pending Manual Review"):
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
                        docs = driver.get("documents", {})

                        with st.expander(f"👤 {driver_name} - المُرسل: {created_at}"):
                            # Document status & preview
                            _render_doc_review(docs, "national_id", "🆔 البطاقة الشخصية (National ID)")
                            _render_doc_review(docs, "driving_license", "🚗 رخصة القيادة (Driving License)")
                            _render_doc_review(docs, "vehicle_license", "🛞 شهادة تسجيل المركبة (Vehicle Registration)")

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
                                            logger.info(f"Driver {driver_name} approved via Verification Radar")
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
                                                logger.info(f"Driver {driver_name} rejected via Verification Radar")
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


def _render_doc_review(docs, doc_type, label):
    """Render a single document review card with image preview if available."""
    doc = docs.get(doc_type, {})
    if not isinstance(doc, dict):
        doc = {}

    has_file = bool(doc.get("file_base64"))
    st.markdown(f"**{label}:** {'✅ موجودة' if has_file else '❌ مفقودة'}")

    if has_file:
        file_name = doc.get("file_name", "document")
        uploaded_at = doc.get("uploaded_at", "N/A")
        st.caption(f"📎 {file_name} | ⏰ {uploaded_at}")

        # Show image preview for jpg/png; skip for PDFs
        if file_name and file_name.lower().rsplit(".", 1)[-1] in ("jpg", "jpeg", "png"):
            try:
                img_bytes = base64.b64decode(doc["file_base64"])
                st.image(img_bytes, caption=label, use_container_width=True)
            except Exception as img_err:
                logger.warning(f"Cannot decode image for {doc_type}: {str(img_err)}")


# ========================================================
# 💰 Live Commission Engine — Automated Revenue Accounting
# ========================================================

def render_commission_engine(fetch_from_firebase, update_firebase_node,
                             credit_driver_wallet, log_accounting_entry):
    """Live Commission Engine: process completed trips, calculate 10% commission,
    credit 90% to driver wallet, and log to accounting_logs/."""
    st.markdown("---")
    st.markdown("## 💰 محرك العمولات الحية (Live Commission Engine)")
    st.caption(f"نسبة العمولة: {int(COMMISSION_RATE * 100)}% للمنصة | {int((1 - COMMISSION_RATE) * 100)}% للسائق")

    try:
        orders = fetch_from_firebase("orders")
        if not orders:
            st.info("📭 لا توجد طلبات لمعالجتها")
            return

        completed_orders = [
            o for o in orders
            if o.get("status") == "Completed" and not o.get("commission_processed")
        ]

        # Also show already-processed summary
        processed_orders = [o for o in orders if o.get("commission_processed")]

        if completed_orders:
            st.subheader(f"🔔 رحلات مكتملة تحتاج معالجة مالية ({len(completed_orders)})")

            for order in completed_orders:
                order_id = order.get("order_id", order.get("db_id", "unknown"))
                driver_username = order.get("driver", "")
                raw_price = order.get("price", 0)

                # Null-safe price parsing
                try:
                    transaction_amount = float(raw_price) if raw_price else 0.0
                except (ValueError, TypeError):
                    transaction_amount = 0.0

                commission = round(transaction_amount * COMMISSION_RATE, 2)
                driver_credit = round(transaction_amount * (1 - COMMISSION_RATE), 2)

                with st.expander(f"🧾 {order_id} | السائق: {driver_username} | المبلغ: {transaction_amount} ج.م"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("💵 المبلغ الكلي", f"{transaction_amount} ج.م")
                    with col2:
                        st.metric("🏢 عمولة المنصة (10%)", f"{commission} ج.م")
                    with col3:
                        st.metric("👤 حصة السائق (90%)", f"{driver_credit} ج.م")

                    if not driver_username:
                        st.warning("⚠️ لا يوجد سائق مسجل لهذا الطلب — لا يمكن المعالجة")
                        continue

                    if transaction_amount <= 0:
                        st.warning("⚠️ المبلغ صفر أو غير صالح — لا يمكن المعالجة")
                        continue

                    if st.button(f"⚡ معالجة العمولة — {order_id}", key=f"process_{order_id}"):
                        _process_commission(
                            order, order_id, driver_username,
                            transaction_amount, commission, driver_credit,
                            update_firebase_node, credit_driver_wallet, log_accounting_entry
                        )

            st.divider()

            # Bulk processing button
            eligible = [
                o for o in completed_orders
                if o.get("driver") and _safe_float(o.get("price", 0)) > 0
            ]
            if len(eligible) > 1:
                if st.button(f"⚡ معالجة جميع العمولات دفعة واحدة ({len(eligible)} رحلة)", key="bulk_process"):
                    success_count = 0
                    for order in eligible:
                        oid = order.get("order_id", order.get("db_id", "unknown"))
                        drv = order.get("driver", "")
                        amt = _safe_float(order.get("price", 0))
                        comm = round(amt * COMMISSION_RATE, 2)
                        drv_credit = round(amt * (1 - COMMISSION_RATE), 2)
                        if _process_commission(
                            order, oid, drv, amt, comm, drv_credit,
                            update_firebase_node, credit_driver_wallet, log_accounting_entry
                        ):
                            success_count += 1
                    st.success(f"✅ تمت معالجة {success_count}/{len(eligible)} رحلة بنجاح!")
                    time.sleep(1)
                    st.rerun()

        else:
            st.info("✅ لا توجد رحلات مكتملة تحتاج معالجة مالية")

        # Accounting log viewer
        st.divider()
        st.markdown("### 📒 سجل المعاملات المحاسبية (Accounting Ledger)")
        try:
            logs = fetch_from_firebase("accounting_logs")
            if logs:
                log_data = []
                for entry in logs:
                    log_data.append({
                        "رقم الرحلة": entry.get("trip_id", "N/A"),
                        "السائق": entry.get("driver_username", "N/A"),
                        "المبلغ الكلي": entry.get("transaction_amount", 0),
                        "عمولة المنصة": entry.get("platform_commission", 0),
                        "حصة السائق": entry.get("driver_credit", 0),
                        "التاريخ": entry.get("processed_at", "N/A"),
                    })
                df = pd.DataFrame(log_data)
                st.dataframe(df, use_container_width=True)

                total_commission = sum(float(e.get("platform_commission", 0)) for e in logs)
                total_credited = sum(float(e.get("driver_credit", 0)) for e in logs)
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("🏢 إجمالي عمولات المنصة", f"{round(total_commission, 2)} ج.م")
                with col2:
                    st.metric("👤 إجمالي المبالغ المحولة للسائقين", f"{round(total_credited, 2)} ج.م")
            else:
                st.info("📭 لا توجد معاملات محاسبية مسجلة حتى الآن")
        except Exception as log_err:
            logger.error(f"Error loading accounting logs: {str(log_err)}")
            st.warning("⚠️ خطأ في تحميل سجل المعاملات")

    except Exception as e:
        logger.error(f"Error in commission engine: {str(e)}")
        st.error("⚠️ خطأ في محرك العمولات")


def _process_commission(order, order_id, driver_username,
                        transaction_amount, commission, driver_credit,
                        update_firebase_node, credit_driver_wallet, log_accounting_entry):
    """Atomically process a single trip's commission. Returns True on success."""
    try:
        with st.spinner(f"⚡ جاري معالجة العمولة لـ {order_id}..."):
            # 1. Credit 90% to driver wallet (atomic increment)
            wallet_ok = credit_driver_wallet(driver_username, driver_credit)
            if not wallet_ok:
                st.error(f"❌ فشل تحديث محفظة السائق {driver_username}")
                logger.error(f"Wallet credit failed: driver={driver_username}, amount={driver_credit}")
                return False

            # 2. Log permanent accounting entry
            log_entry = {
                "trip_id": order_id,
                "driver_username": driver_username,
                "transaction_amount": transaction_amount,
                "platform_commission": commission,
                "driver_credit": driver_credit,
                "commission_rate": COMMISSION_RATE,
                "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "completed"
            }
            log_ok = log_accounting_entry(order_id, log_entry)
            if not log_ok:
                st.warning(f"⚠️ تم تحديث المحفظة لكن فشل تسجيل المعاملة لـ {order_id}")
                logger.error(f"Accounting log failed for trip: {order_id}")

            # 3. Mark order as commission-processed to prevent reprocessing
            db_id = order.get("db_id", "")
            if db_id:
                update_firebase_node(f"orders/{db_id}", {"commission_processed": True})

            st.success(
                f"✅ تمت المعالجة: {order_id} | "
                f"عمولة: {commission} ج.م | "
                f"محفظة السائق +{driver_credit} ج.م"
            )
            logger.info(
                f"Commission processed: trip={order_id}, driver={driver_username}, "
                f"amount={transaction_amount}, commission={commission}, driver_credit={driver_credit}"
            )
            return True

    except Exception as e:
        logger.error(f"Error processing commission for {order_id}: {str(e)}")
        st.error(f"❌ خطأ في معالجة العمولة: {str(e)}")
        return False


def _safe_float(value):
    """Safely convert a value to float, defaulting to 0.0."""
    try:
        return float(value) if value else 0.0
    except (ValueError, TypeError):
        return 0.0
