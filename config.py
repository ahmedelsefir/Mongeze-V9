import os
from pathlib import Path

# إعدادات التطبيق
APP_NAME = "فودي - نظام توصيل الطلبات"
APP_ICON = "🍔"
APP_LAYOUT = "wide"

# إعدادات Firebase - يتم قراءتها من GitHub Secrets أو متغيرات البيئة
FIREBASE_CONFIG = {
    "apiKey": os.getenv("FIREBASE_API_KEY", ""),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", ""),
    "databaseURL": os.getenv("FIREBASE_DATABASE_URL", ""),
    "projectId": os.getenv("FIREBASE_PROJECT_ID", ""),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET", ""),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", ""),
    "appId": os.getenv("FIREBASE_APP_ID", ""),
}

# أدوار النظام وصلاحياتهم
ROLES = {
    "admin": {
        "display_name": "مسؤول النظام",
        "permissions": [
            "view_all_orders",
            "manage_restaurants",
            "manage_drivers",
            "manage_staff",
            "view_analytics",
            "manage_payments",
            "system_settings"
        ]
    },
    "staff": {
        "display_name": "موظف",
        "permissions": [
            "view_active_orders",
            "update_order_status",
            "view_assigned_drivers",
            "contact_support"
        ]
    },
    "driver": {
        "display_name": "مندوب توصيل",
        "permissions": [
            "view_available_orders",
            "accept_order",
            "update_delivery_status",
            "view_profile",
            "view_ratings",
            "update_availability"
        ]
    },
    "restaurant": {
        "display_name": "المطعم",
        "permissions": [
            "view_orders",
            "update_order_status",
            "manage_menu",
            "view_statistics",
            "view_ratings"
        ]
    },
    "customer": {
        "display_name": "عميل",
        "permissions": [
            "place_order",
            "track_order",
            "view_history",
            "rate_delivery",
            "view_profile"
        ]
    }
}

# مسارات المجلدات
BASE_DIR = Path(__file__).parent
PAGES_DIR = BASE_DIR / "pages"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# إنشاء المجلدات إذا لم تكن موجودة
for directory in [PAGES_DIR, DATA_DIR, LOGS_DIR]:
    directory.mkdir(exist_ok=True)

# إعدادات قاعدة البيانات المحلية (للنسخ الاحتياطية)
DB_PATH = DATA_DIR / "app_database.json"

# إعدادات الأمان
SESSION_TIMEOUT = 3600  # ساعة واحدة بالثواني
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 900  # 15 دقيقة

# إعدادات الطلبات
ORDER_STATUS_OPTIONS = [
    "تم الاستقبال ✅",
    "جاري التحضير 🔨",
    "جاهز للتوصيل 📦",
    "في الطريق 🚗",
    "تم التسليم ✓",
    "ملغي ❌"
]

DELIVERY_TIME_OPTIONS = [
    "في أسرع وقت ممكن ⚡",
    "بعد 30 دقيقة",
    "بعد 1 ساعة",
    "بعد 2 ساعة"
]

# إعدادات التقييمات
RATING_SCALE = 5
MIN_RATING_TEXT_LENGTH = 10
