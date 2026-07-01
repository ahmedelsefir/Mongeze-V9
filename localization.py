# ============================================================================
# 🌍 LOCALIZATION MODULE - Multi-Language Support
# ============================================================================

"""
Localization system for dynamic UI text translation between Arabic and English.
All hardcoded text labels should use the get_text() function to support dynamic switching.
"""

TRANSLATIONS = {
    # ========== MAIN PAGE TITLES & HEADERS ==========
    "central_ops_title": {
        "العربية": "🤖 غرفة العمليات المركزية لـ منجز الذكية",
        "English": "🤖 Monjez Smart Central Operations Room"
    },
    
    "api_connection": {
        "العربية": "🔗 خط اتصال الدومين النشط حالياً: ",
        "English": "🔗 Active Domain Connection: "
    },
    
    "dashboard_button": {
        "العربية": "🏠 شاشة المراقبة",
        "English": "🏠 Dashboard"
    },
    
    "parcels_button": {
        "العربية": "📦 بوابة الطرود",
        "English": "📦 Parcels Gateway"
    },
    
    "taxi_button": {
        "العربية": "🚕 توصيل تاكسي",
        "English": "🚕 Taxi Delivery"
    },
    
    "chat_button": {
        "العربية": "💬 شات منجز الخاص 🟢",
        "English": "💬 Monjez Chat 🟢"
    },
    
    "tracking_button": {
        "العربية": "🛰️ رادار تتبع الطلبات (لايف)",
        "English": "🛰️ Orders Tracking Radar (Live)"
    },
    
    "settings_button": {
        "العربية": "⚙️ الإعدادات والملف الشخصي",
        "English": "⚙️ Settings & Profile"
    },
    
    # ========== DASHBOARD PAGE ==========
    "dashboard_header": {
        "العربية": "📡 لوحة بث واستقبال العمليات السحابية",
        "English": "📡 Cloud Operations Broadcasting Dashboard"
    },
    
    "active_orders": {
        "العربية": "📊 الطلبات الشغالة على السيرفر حالياً:",
        "English": "📊 Currently Active Orders:"
    },
    
    "no_active_orders": {
        "العربية": "📭 السيرفر نظيف ولا توجد رحلات جارية حالياً.",
        "English": "📭 Server is clean - no active trips."
    },
    
    "dashboard_error": {
        "العربية": "حدث خطأ في جلب البيانات",
        "English": "Error fetching data"
    },
    
    # ========== SIDEBAR & USER PROFILE ==========
    "user_profile": {
        "العربية": "👤 ملف المستخدم",
        "English": "👤 User Profile"
    },
    
    "choose_role": {
        "العربية": "اختر هويتك في السيستم:",
        "English": "Choose your role:"
    },
    
    "full_name": {
        "العربية": "اسمك المسجل:",
        "English": "Your Name:"
    },
    
    # ========== SETTINGS PAGE ==========
    "settings_center": {
        "العربية": "⚙️ مركز الإعدادات والملف الشخصي المتقدم",
        "English": "⚙️ Advanced Settings & Profile Center"
    },
    
    "general_settings": {
        "العربية": "🌍 الإعدادات العامة",
        "English": "🌍 General Settings"
    },
    
    "driver_settings": {
        "العربية": "🚕 إعدادات المندوب",
        "English": "🚕 Driver Settings"
    },
    
    "kyc_verification": {
        "العربية": "🎖️ التحقق من الهوية (KYC)",
        "English": "🎖️ Identity Verification (KYC)"
    },
    
    "help_support": {
        "العربية": "📋 المساعدة والدعم",
        "English": "📋 Help & Support"
    },
    
    "profile_edit": {
        "العربية": "👤 تعديل البروفايل الشخصي",
        "English": "👤 Edit Personal Profile"
    },
    
    "full_name_input": {
        "العربية": "🔤 الاسم الكامل:",
        "English": "🔤 Full Name:"
    },
    
    "whatsapp_number": {
        "العربية": "📱 رقم الواتساب:",
        "English": "📱 WhatsApp Number:"
    },
    
    "save_profile": {
        "العربية": "💾 حفظ تعديلات البروفايل",
        "English": "💾 Save Profile Changes"
    },
    
    "profile_saved": {
        "العربية": "✅ تم حفظ تعديلات البروفايل بنجاح!",
        "English": "✅ Profile changes saved successfully!"
    },
    
    "profile_save_error": {
        "العربية": "❌ فشل حفظ التعديلات. حاول مرة أخرى.",
        "English": "❌ Failed to save changes. Try again."
    },
    
    # ========== AUDIO NOTIFICATIONS ==========
    "audio_settings": {
        "العربية": "🎵 إعدادات التنبيهات الصوتية",
        "English": "🎵 Audio Notifications Settings"
    },
    
    "enable_audio": {
        "العربية": "🔊 تفعيل التنبيهات الصوتية",
        "English": "🔊 Enable Audio Notifications"
    },
    
    "audio_enabled": {
        "العربية": "✅ التنبيهات الصوتية مفعّلة",
        "English": "✅ Audio notifications enabled"
    },
    
    "audio_disabled": {
        "العربية": "❌ التنبيهات الصوتية معطّلة",
        "English": "❌ Audio notifications disabled"
    },
    
    "test_sound": {
        "العربية": "🔊 تجربة الصوت",
        "English": "🔊 Test Sound"
    },
    
    # ========== LANGUAGE SETTINGS ==========
    "language_settings": {
        "العربية": "🌐 إعدادات اللغة",
        "English": "🌐 Language Settings"
    },
    
    "choose_language": {
        "العربية": "اختر لغة الواجهة:",
        "English": "Choose interface language:"
    },
    
    "language_set": {
        "العربية": "✅ تم تعيين اللغة على",
        "English": "✅ Language set to"
    },
    
    # ========== TRACKING PAGE ==========
    "tracking_header": {
        "العربية": "📡 رادار التتبع والاتصال السحابي المباشر",
        "English": "📡 Tracking Radar & Direct Cloud Connection"
    },
    
    "radar_active": {
        "العربية": "🔄 الرادار نشط: يتم تحديث وسحب الحالات تلقائياً من السيرفر كل 3 ثوانٍ...",
        "English": "🔄 Radar active: Automatically updating orders from server every 3 seconds..."
    },
    
    "tracking_error": {
        "العربية": "حدث خطأ في صفحة التتبع",
        "English": "Error on tracking page"
    },
    
    # ========== ADMIN CONSOLE ==========
    "admin_tracking": {
        "العربية": "📊 لوحة الرقابة الشاملة للموظفين",
        "English": "📊 Comprehensive Staff Oversight Dashboard"
    },
    
    "no_orders": {
        "العربية": "لا توجد طلبات حالياً",
        "English": "No orders available"
    },
    
    "live_distances": {
        "العربية": "📍 المسافات الحية للطلبات النشطة",
        "English": "📍 Live Distances for Active Orders"
    },
    
    "verification_radar": {
        "العربية": "📡 رادار التحقق من المندوبين (Verification Radar)",
        "English": "📡 Driver Verification Radar"
    },
    
    "pending_reviews": {
        "العربية": "📡 رادار المحتاجين للمراجعة",
        "English": "📡 Pending Reviews Radar"
    },
    
    "pending_count": {
        "العربية": "معلقة",
        "English": "pending"
    },
    
    "no_pending": {
        "العربية": "✅ لا توجد طلبات معلقة للمراجعة - جميع المندوبين تم مراجعتهم!",
        "English": "✅ No pending reviews - all drivers have been reviewed!"
    },
    
    "submitted_by": {
        "العربية": "المُرسل:",
        "English": "Submitted:"
    },
    
    "national_id": {
        "العربية": "🆔 البطاقة الشخصية (National ID)",
        "English": "🆔 National ID"
    },
    
    "driving_license": {
        "العربية": "🚗 رخصة القيادة (Driving License)",
        "English": "🚗 Driving License"
    },
    
    "vehicle_registration": {
        "العربية": "🛞 شهادة تسجيل المركبة (Vehicle Registration)",
        "English": "🛞 Vehicle Registration"
    },
    
    "admin_actions": {
        "العربية": "🎯 الإجراءات الإدارية",
        "English": "🎯 Administrative Actions"
    },
    
    "approve_driver": {
        "العربية": "🟢 موافقة وتفعيل الحساب",
        "English": "🟢 Approve & Activate"
    },
    
    "reject_driver": {
        "العربية": "🔴 رفض الطلب",
        "English": "🔴 Reject Request"
    },
    
    "rejection_reason": {
        "العربية": "سبب الرفض (إن وجد):",
        "English": "Rejection reason (if any):"
    },
    
    "driver_approved": {
        "العربية": "✅ تم تفعيل حساب",
        "English": "✅ Account activated:"
    },
    
    "approval_failed": {
        "العربية": "❌ فشلت عملية التفعيل",
        "English": "❌ Activation failed"
    },
    
    "driver_rejected": {
        "العربية": "✅ تم رفض طلب",
        "English": "✅ Request rejected:"
    },
    
    "rejection_required": {
        "العربية": "❌ يجب إدخال سبب الرفض",
        "English": "❌ Rejection reason required"
    },
    
    "rejection_failed": {
        "العربية": "❌ فشلت عملية الرفض",
        "English": "❌ Rejection failed"
    },
    
    # ========== COMMISSION ENGINE ==========
    "commission_engine": {
        "العربية": "💰 محرك العمولات الحية (Live Commission Engine)",
        "English": "💰 Live Commission Engine"
    },
    
    "commission_rate": {
        "العربية": "نسبة العمولة:",
        "English": "Commission Rate:"
    },
    
    "platform": {
        "العربية": "للمنصة",
        "English": "for Platform"
    },
    
    "driver_share": {
        "العربية": "للسائق",
        "English": "for Driver"
    },
    
    "vat_tax": {
        "العربية": "ضريبة القيمة المضافة:",
        "English": "VAT:"
    },
    
    "completed_trips": {
        "العربية": "🔔 رحلات مكتملة تحتاج معالجة مالية",
        "English": "🔔 Completed trips needing financial processing"
    },
    
    "trip_amount": {
        "العربية": "💵 المبلغ الكلي",
        "English": "💵 Total Amount"
    },
    
    "platform_commission": {
        "العربية": "🏢 عمولة المنصة (20%)",
        "English": "🏢 Platform Commission (20%)"
    },
    
    "vat_amount": {
        "العربية": "🧾 ضريبة VAT (14%)",
        "English": "🧾 VAT (14%)"
    },
    
    "driver_share_metric": {
        "العربية": "👤 حصة السائق (80%)",
        "English": "👤 Driver Share (80%)"
    },
    
    "no_driver": {
        "العربية": "⚠️ لا يوجد سائق مسجل لهذا الطلب — لا يمكن المعالجة",
        "English": "⚠️ No driver registered - cannot process"
    },
    
    "invalid_amount": {
        "العربية": "⚠️ المبلغ صفر أو غير صالح — لا يمكن المعالجة",
        "English": "⚠️ Invalid amount - cannot process"
    },
    
    "process_commission": {
        "العربية": "⚡ معالجة العمولة —",
        "English": "⚡ Process Commission —"
    },
    
    "bulk_process": {
        "العربية": "⚡ معالجة جميع العمولات دفعة واحدة",
        "English": "⚡ Bulk Process All Commissions"
    },
    
    "trips": {
        "العربية": "رحلة",
        "English": "trips"
    },
    
    "no_completed_trips": {
        "العربية": "✅ لا توجد رحلات مكتملة تحتاج معالجة مالية",
        "English": "✅ No completed trips pending financial processing"
    },
    
    "accounting_ledger": {
        "العربية": "📒 سجل المعاملات المحاسبية (Accounting Ledger)",
        "English": "📒 Accounting Ledger"
    },
    
    "trip_id": {
        "العربية": "رقم الرحلة",
        "English": "Trip ID"
    },
    
    "driver": {
        "العربية": "السائق",
        "English": "Driver"
    },
    
    "total_amount": {
        "العربية": "المبلغ الكلي",
        "English": "Total"
    },
    
    "date": {
        "العربية": "التاريخ",
        "English": "Date"
    },
    
    "total_commissions": {
        "العربية": "🏢 إجمالي عمولات المنصة",
        "English": "🏢 Total Platform Commissions"
    },
    
    "total_vat": {
        "العربية": "🧾 إجمالي ضريبة VAT",
        "English": "🧾 Total VAT"
    },
    
    "platform_revenue": {
        "العربية": "💼 صافي إيرادات المنصة",
        "English": "💼 Platform Net Revenue"
    },
    
    "total_driver_payouts": {
        "العربية": "👤 إجمالي المبالغ المحولة للسائقين",
        "English": "👤 Total Driver Payouts"
    },
    
    "no_accounting": {
        "العربية": "📭 لا توجد معاملات محاسبية مسجلة حتى الآن",
        "English": "📭 No accounting transactions recorded yet"
    },
    
    "commission_success": {
        "العربية": "✅ تمت المعالجة:",
        "English": "✅ Processed:"
    },
    
    "processing": {
        "العربية": "⚡ جاري معالجة العمولة لـ",
        "English": "⚡ Processing commission for"
    },
    
    "bulk_success": {
        "العربية": "✅ تمت معالجة",
        "English": "✅ Processed"
    },
    
    "out_of": {
        "العربية": "من",
        "English": "out of"
    },
    
    "successfully": {
        "العربية": "بنجاح!",
        "English": "successfully!"
    },
    
    # ========== UTILITIES ==========
    "refresh_button": {
        "العربية": "🔄 تحديث الرادار والمحادثات",
        "English": "🔄 Refresh Radar & Chats"
    },
}


def get_text(key: str, language: str = None) -> str:
    """
    Get localized text for a given key.
    
    Args:
        key: Translation key from TRANSLATIONS dict
        language: Language code ('العربية' or 'English'). 
                 If None, tries to get from st.session_state
    
    Returns:
        Translated text or the key itself if not found
    
    Usage:
        text = get_text("central_ops_title")  # Uses session language
        text = get_text("central_ops_title", "English")  # Force English
    """
    import streamlit as st
    
    if language is None:
        language = st.session_state.get("language", "العربية")
    
    if key in TRANSLATIONS:
        return TRANSLATIONS[key].get(language, TRANSLATIONS[key].get("العربية", key))
    
    return key


def translate(ar_text: str, en_text: str, language: str = None) -> str:
    """
    Quick translation helper for ad-hoc text not in dictionary.
    
    Usage:
        text = translate("مرحبا", "Hello")
    """
    import streamlit as st
    
    if language is None:
        language = st.session_state.get("language", "العربية")
    
    return ar_text if language == "العربية" else en_text
