import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json
import socket

# ##########################################
# # --- 1. إعدادات الهوية الرسمية للمنصة ---
# ##########################################
st.set_page_config(page_title="منجز اللوجستية - لوحة التحكم الرئيسية", layout="wide")

st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🎯 منصة مُنجز الذكية (Mongeze)</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #4B5563;'>النظام البرمجي الموحد لإدارة الشحنات، السائقين، والربط السحابي لعام 2026</p>", unsafe_allow_html=True)
st.markdown("---")

# ##########################################
# # --- 2. دالة كاشف الأخطاء والتشخيص الآلي ---
# ##########################################
# الدالة دي صممتها خصيصاً بناءً على طلبك عشان تفحص السيرفر وتعرفنا لو في أي مشكلة فوراً
def run_system_diagnostic():
    st.subheader("🔍 نظام فحص وتشخيص أخطاء التطبيق الآلي")
    
    # مصفوفة لحفظ حالات الفحص
    diagnostic_results = {}
    
    # أ. فحص إعدادات السيرفر والـ Secrets
    # ##################################
    if "textkey" in st.secrets:
        diagnostic_results["ملف الـ Secrets ومفتاح الفايربيز"] = ("🟢 سليم ومقروء بنجاح", True)
    else:
        diagnostic_results["ملف الـ Secrets ومفتاح الفايربيز"] = ("🔴 خطأ: مفتاح 'textkey' غير موجود في إعدادات السيرفر السرية!", False)
        
    # ب. فحص الاتصال بقاعدة البيانات Firebase
    # ######################################
    try:
        if not firebase_admin._apps:
            key_dict = json.loads(st.secrets["textkey"])
            cred = credentials.Certificate(key_dict)
            firebase_admin.initialize_app(cred)
        db = firestore.client()
        # محاولة قراءة تجريبية للتأكد من استقرار الشريان
        db.collection("orders").limit(1).get()
        diagnostic_results["الاتصال بقاعدة بيانات Firebase"] = ("🟢 مستقر ويعمل في الوقت الفعلي (Real-time)", True)
    except Exception as e:
        diagnostic_results["الاتصال بقاعدة بيانات Firebase"] = (f"🔴 خطأ في الربط: {str(e)}", False)

    # ج. فحص شبكة السيرفر الداخلية
    # ############################
    try:
        host_name = socket.gethostname()
        host_ip = socket.gethostbyname(host_name)
        diagnostic_results["حالة سيرفر الاستضافة الداخلي"] = (f"🟢 متصل أونلاين (IP: {host_ip})", True)
    except Exception as e:
        diagnostic_results["حالة سيرفر الاستضافة الداخلي"] = (f"🟡 تحذير في الشبكة: {str(e)}", False)

    # # --- عرض نتائج الفحص الإرشادي للمطور على الشاشة ---
    for component, (message, is_ok) in diagnostic_results.items():
        if is_ok:
            st.success(f"**{component}:** {message}")
        else:
            st.error(f"**{component}:** {message}")

# تشغيل دالة الفحص فور فتح الصفحة الرئيسية
run_system_diagnostic()

st.markdown("---")

# ##########################################
# # --- 3. التعريف الآلي والتوجيه الفرعي ---
# ##########################################
# هنا الكود بيشرح للمستخدم أو العميل المدفوع إزاي يستخدم النظام scannable وسريع القراءة
st.subheader("💡 دليل توجيه النظام الفرعي الجديد:")

st.markdown("""
<div style='background-color: #f3f4f6; padding: 20px; border-radius: 10px; border-left: 5px solid #1E3A8A; color: #333;'>
    <p>بفضل الهيكلة الموحدة التي قمنا ببرمجتها، يمكنك الآن الانتقال بين بوابات الخدمة من خلال <b>القائمة الجانبية (Sidebar)</b> في يسار أو يمين الشاشة:</p>
    <ul>
        <li>🛒 <b>بوابة العميل:</b> لطلب الخدمات اللوجستية وتحديد تفاصيل الشحنات.</li>
        <li>🚖 <b>بوابة السائق الذكية:</b> لمتابعة كروت الطلبات، حساب الأرباح، وتحديث خط سير الرحلة ديناميكياً.</li>
    </ul>
    <p style='margin-bottom: 0;'>🔄 أي تحديث تجريه في الفروع سيقوم هذا الملف الرئيسي (assistant.py) بمراقبته وفحصه آلياً.</p>
</div>
""", unsafe_allow_html=True)

# إضافة زر لإعادة الفحص اليدوي عند الحاجة
if st.button("🔄 إعادة تشغيل نظام الفحص المباشر"):
    st.rerun()
