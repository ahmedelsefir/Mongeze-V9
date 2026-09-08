import streamlit as st
from firebase_admin import firestore

def render_vendor_portal(db, vendor_id="restaurant_el_tahrir"):
    st.markdown("<h2 style='color: #1E3A8A; text-align: right;'>🏪 لوحة تحكم التاجر والمطعم الشريك</h2>", unsafe_allow_html=True)
    st.markdown("---")

    if not db:
        st.error("⚠️ قاعدة البيانات غير متصلة.")
        return

    # جلب بيانات المطعم من مجموعة vendors في فايربيز
    vendor_ref = db.collection("vendors").document(vendor_id)
    vendor_doc = vendor_ref.get()
    
    vendor_data = {}
    if vendor_doc.exists:
        vendor_data = vendor_doc.to_dict()
    else:
        # بيانات افتراضية أولية للمطعم إذا لم تكن موجودة
        vendor_data = {
            "name": "مطعم البرجر الملكي السريع",
            "logo_url": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=200",
            "category": "مأكولات ومطاعم",
            "is_open": True,
            "partnership_type": "شريك رسمي"
        }
        vendor_ref.set(vendor_data, merge=True)

    # 🎨 عرض الهوية البصرية للمطعم (الاسم والشعار)
    col_logo, col_info = st.columns([1, 3])
    with col_logo:
        st.image(vendor_data.get("logo_url", "https://via.placeholder.com/150"), width=130, caption="شعار المطعم")
    with col_info:
        st.markdown(f"### 🏷️ اسم المطعم: **{vendor_data.get('name')}**")
        st.markdown(f"📂 التصنيف: `{vendor_data.get('category')}` | 🤝 نوع الشراكة: **{vendor_data.get('partnership_type')}**")
        status_color = "🟢 مفتوح ويستقبل طلبات" if vendor_data.get("is_open") else "🔴 مغلق حالياً"
        st.markdown(f"**حالة التشغيل:** {status_color}")

    st.markdown("---")
    st.markdown("### 📥 إدارة الطلبات الواردة للمطعم:")

    # جلب الطلبات الواردة خصيصاً لهذا المطعم
    try:
        orders_ref = db.collection("orders").where("vendor_id", "==", vendor_id).stream()
        found = False
        for doc in orders_ref:
            found = True
            o_data = doc.to_dict()
            o_id = doc.id
            status = o_data.get("status", "Pending")
            
            st.info(f"📌 طلب رقم: `{o_id[:6]}` | العميل: **{o_data.get('client_name')}** | الحالة: **{status}**")
            st.write(f"🛒 الأصناف المطلوبة: {o_data.get('items', [])}")
            st.write(f"📍 ملاحظات التوصيل: {o_data.get('notes', 'بدون ملاحظات')}")
            
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                if st.button(f"👨‍🍳 قبول وتحضير الطلب", key=f"accept_v_{o_id}"):
                    db.collection("orders").document(o_id).update({"status": "Preparing"})
                    st.success("✅ تم قبول الطلب وبدء التحضير في المطبخ!")
                    st.rerun()
            with col_v2:
                if st.button(f"🚀 جاهز للتوصيل (تسليم للمندوب)", key=f"ready_v_{o_id}"):
                    db.collection("orders").document(o_id).update({"status": "Ready for Delivery"})
                    st.success("✅ تم إعلام السائق بأن الطلب جاهز للاستلام!")
                    st.rerun()
            st.markdown("---")
        
        if not found:
            st.success("👍 لا توجد طلبات جديدة معلقة لهذا المطعم في الوقت الحالي.")
    except Exception as e:
        st.error(f"⚠️ خطأ أثناء جلب الطلبات: {e}")

    # ⚙️ تحديث بيانات المطعم (الاسم، الشعار، وحالة العمل)
    with st.form("vendor_settings_update_form"):
        st.subheader("⚙️ تعديل بيانات وهوية المطعم")
        new_name = st.text_input("اسم المطعم:", value=vendor_data.get("name", ""))
        new_logo = st.text_input("رابط شعار المطعم (Logo Image URL):", value=vendor_data.get("logo_url", ""))
        is_open_val = st.checkbox("🟢 المطعم مفتوح للعمل الآن", value=vendor_data.get("is_open", True))
        
        if st.form_submit_button("💾 حفظ تحديثات الهوية والتشغيل"):
            vendor_ref.update({
                "name": new_name,
                "logo_url": new_logo,
                "is_open": is_open_val
            })
            st.success("✅ تم تحديث اسم وشعار وطريقة عمل المطعم بنجاح سحابياً!")
            st.rerun()
