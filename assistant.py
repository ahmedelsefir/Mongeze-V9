import os
from honeybadger import honeybadger

# ربط المحرك بالرادار عبر الخزنة السرية بأمان تام
honeybadger.configure(api_key=os.getenv('HONEYBADGER_API_KEY'))

def mongeze_engine_v9():
    try:
        print("-------------------------------------------")
        print("🚀 بدء اختبار المحرك V9 - حسابات تجريبية")
        print("-------------------------------------------")
        
        # --- مرحلة الاختبار (مبلغ تجريبي 1000 جنيه) ---
        amount = 1000
        
        # العملية (أ): حساب القيمة المضافة فقط (شراء)
        total_with_vat = amount * 1.14 
        
        # العملية (ب): حساب الصافي بعد خصم الأرباح فقط (قبض)
        net_after_tax = amount * 0.90
        
        print(f"🔹 لو هتبيع (بالضريبة): {total_with_vat} ج.م")
        print(f"🔸 لو هتقبض (بعد الخصم): {net_after_tax} ج.م")
        print("✔️ تم الاختبار بنجاح يا بشمهندس أحمد")
        
    except Exception as e:
        honeybadger.notify(e)
        print(f"⚠️ الرادار التقط خطأ: {e}")

if __name__ == "__main__":
    mongeze_engine_v9()
