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
        vat = amount * 0.14        # ضريبة القيمة المضافة 14%
        income_tax = amount * 0.10 # ضريبة الخصم 10%
        final_total = amount + vat - income_tax
        
        print(f"💰 المبلغ الأساسي: {amount} جنيه")
        print(f"📈 ضريبة 14% هي: {vat} جنيه")
        print(f"📉 خصم 10% هو: {income_tax} جنيه")
        print(f"✅ الإجمالي الصافي: {final_total} جنيه")
        print("-------------------------------------------")
        print("✔️ تم الاختبار بنجاح يا بشمهندس أحمد")
        
    except Exception as e:
        honeybadger.notify(e)
        print(f"⚠️ الرادار التقط خطأ: {e}")

if __name__ == "__main__":
    mongeze_engine_v9()
