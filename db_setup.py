import firebase_admin
from firebase_admin import credentials, firestore

# تهيئة الاتصال بقاعدة البيانات في فايربيز (تأكد أن التطبيق مرتبط بـ credentials الأساسية)
if not firebase_admin._apps:
    firebase_admin.initialize_app()

db = firestore.client()

def initialize_database_schema():
    """
    إنشاء وتثبيت الهيكل الأساسي الموحد لقاعدة البيانات (Single Source of Truth)
    يتضمن هيكل المستخدمين، الطلبات، ووظائف الأتمتة المرتبطة بها.
    """
    print("جاري تهيئة الهيكل الخرساني لقاعدة البيانات...")

    # 1. إنشاء وثيقة افتراضية أو مرجعية لجدول المستخدمين (Users Schema)
    user_schema_ref = db.collection("users").document("_schema_template_")
    user_schema_ref.set({
        "uid": "string (Unique Identifier)",
        "name": "string",
        "phone": "string",
        "role": "string (client, driver, admin)",
        "wallet_balance": "number (default: 0.0)",
        "status": "string (active, suspended)",
        "created_at": "timestamp"
    }, merge=True)

    # 2. إنشاء وثيقة افتراضية أو مرجعية لجدول الطلبات الموحد (Orders Schema)
    order_schema_ref = db.collection("orders").document("_schema_template_")
    order_schema_ref.set({
        "order_id": "string (Unique Identifier)",
        "client_id": "string (Linked to users.uid)",
        "driver_id": "string (Linked to users.uid)",
        "service_type": "string (delivery, taxi, parcel)",
        "order_detail": "string",
        "suggested_price": "number",
        "status": "string (pending, accepted, completed, cancelled)",
        "timestamp": "timestamp"
    }, merge=True)

    print("تم إنشاء الهيكل والوثائق المرجعية بنجاح تام.")

def process_completed_order_trigger(order_id):
    """
    وظيفة أتمتة داخلية (تشبه الـ Trigger):
    تقوم عند اكتمال الطلب بتحديث محفظة السائق والعميل تلقائياً بدون تدخل يدوي.
    """
    order_ref = db.collection("orders").document(order_id)
    order_doc = order_ref.get()
    
    if not order_doc.exists:
        print(فشل: الطلب غير موجود رقم: {order_id})
        return False

    order_data = order_doc.to_dict()
    status = order_data.get("status")
    driver_id = order_data.get("driver_id")
    price = order_data.get("suggested_price", 0)

    # تنفيذ الأتمتة فقط إذا تحولت حالة الطلب إلى مكتمل
    if status == "completed" and driver_id:
        driver_ref = db.collection("users").document(driver_id)
        # خصم نسبة التطبيق وإضافة الصافي لمحفظة السائق (مثلاً نسبة الشركة 10%)
        company_commission = price * 0.10
        driver_net_earnings = price - company_commission

        # تحديث رصيد السائق في قاعدة البيانات فورياً
        db.run_transaction(lambda transaction: update_driver_wallet(transaction, driver_ref, driver_net_earnings))
        print(تم تنفيذ الأتمتة المالية بنجاح للطلب: {order_id})
        return True

    return False

@firestore.transactional
def update_driver_wallet(transaction, driver_ref, earnings):
    driver_snapshot = driver_ref.get(transaction=transaction)
    if driver_snapshot.exists:
        current_balance = driver_snapshot.to_dict().get("wallet_balance", 0.0)
        new_balance = current_balance + earnings
        transaction.update(driver_ref, {"wallet_balance": new_balance})

if __name__ == "__main__":
    # تشغيل تهيئة الهيكل عند تنفيذ الملف
    initialize_database_schema()
