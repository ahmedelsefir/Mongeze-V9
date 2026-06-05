# 📋 Development Standards - منصة منجز الذكية

**إصدار**: 2.0.0  
**التاريخ**: 2026-06-05  
**الحالة**: ✅ Stable with Live Tracking  
**الالتزام**: Documentation-Driven Development (DDD)

---

## 🎯 رؤية المعايير

هذا المستند يحدد المعايير الملزمة لجميع التطويرات المستقبلية على منصة منجز الذكية. الهدف:
- ✅ منع انهيار التطبيق
- ✅ ضمان الاستقرار في الإنتاج
- ✅ توثيق كامل قبل الكود
- ✅ فصل تام للبيانات الحساسة
- ✅ ممارسات آمنة خالية من الأخطاء

---

## 📐 المبادئ الأساسية (Core Principles)

### 1. **Documentation-Driven Development (DDD)**
```
التوثيق أولاً → ثم الكود
```

**القاعدة الذهبية**:
> **لا تكتب سطر واحد من الكود دون توثيق واضح يشرح:**
> - ماذا يفعل؟
> - ما المعاملات والأنواع؟
> - ما القيم المرجعة؟
> - ما حالات الخطأ المحتملة؟

**الإجراء قبل كل ميزة جديدة**:
```
1. اكتب Docstring بصيغة Google/NumPy
2. اكتب أمثلة الاستخدام
3. وثّق حالات الخطأ
4. اكتب الكود
5. اختبر مقابل التوثيق
6. أضف إلى DOCUMENTATION.md
```

### 2. **Session State Management (تعدد الأدوار)**

**الحالة الحالية**:
```python
st.session_state = {
    "current_page": str,          # الصفحة النشطة
    "my_active_order_id": str,    # معرّف الطلب للعميل
    "user_role": str,              # العميل / السائق / الإدارة
}
```

**القاعدة الثابتة**:
> **جميع الحقول يجب أن تُهيأ في البداية وتُستخدم بحذر**

```python
# ✅ الطريقة الصحيحة
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "الرئيسية"

# ❌ خطأ - قد تسبب KeyError
page = st.session_state["current_page"]  # بدون تحقق

# ✅ الطريقة الآمنة
page = st.session_state.get("current_page", "الرئيسية")
```

**المتطلبات للمتغيرات الجديدة**:
- [ ] تُهيأ في البداية
- [ ] توثّق مع الشرح
- [ ] يُتعامل معها بـ `.get()` مع قيمة افتراضية

### 3. **Environment Secrets Management**

**المبدأ**: ❌ لا توضع مفاتيح في الكود أبداً

**الطريقة الصحيحة**:
```python
# ✅ استخدام st.secrets
FIREBASE_URL = st.secrets.get("FIREBASE_URL", "default_url").strip()
smtp_user = st.secrets.get("smtp", {}).get("user")

# ❌ خطأ فادح
FIREBASE_URL = "https://my-key-exposed.com"
EMAIL_PASSWORD = "password123"
```

**ملف `.streamlit/secrets.toml` (غير مرفوع على Git)**:
```toml
FIREBASE_URL = "https://your-db.firebaseio.com"

[smtp]
user = "your_email@gmail.com"
pass = "app_password"
server = "smtp.gmail.com"
port = 587

[textkey]
textkey = """
{
  "type": "service_account",
  "private_key": "-----BEGIN PRIVATE KEY-----\\n...",
  ...
}
"""
```

**في `.gitignore`**:
```
.streamlit/secrets.toml
.env
*.pem
*.key
```

### 4. **Null-Safe Data Practices**

**القاعدة**: **لا تفترض وجود البيانات أبداً**

```python
# ❌ قد يرفع KeyError أو AttributeError
order_id = order["order_id"]
distance = order.driver_lat - order.customer_lat

# ✅ آمن تماماً
order_id = order.get("order_id", "unknown")
driver_lat = order.get("driver_lat")
customer_lat = order.get("customer_lat")

if driver_lat and customer_lat:
    distance = driver_lat - customer_lat
else:
    logger.warning(f"Missing coordinates for order")
    distance = None
```

**النمط المطلوب للـ Try-Except**:
```python
def process_data(data):
    """
    معالجة البيانات بأمان.
    
    المعاملات:
        data (dict): البيانات المراد معالجتها
    
    القيمة المرجعة:
        Result أو None في حالة الخطأ
    """
    try:
        # معالجة
        return result
    except ValueError:
        logger.error("Invalid data format")
        return None
    except KeyError as e:
        logger.error(f"Missing key: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return None
```

---

## 🔧 معايير الدوال (Function Standards)

### نموذج Docstring الموحد:

```python
def function_name(param1: type1, param2: type2) -> return_type:
    """
    وصف مختصر للدالة (جملة واحدة).
    
    وصف طويل إذا لزم الأمر (اختياري):
    - النقطة الأولى
    - النقطة الثانية
    
    المعاملات (Parameters):
        param1 (type1): وصف المعامل الأول
            - شروط إضافية
            - نطاقات معقولة: 0-100
        param2 (type2): وصف المعامل الثاني
    
    القيمة المرجعة (Returns):
        return_type: وصف القيمة المرجعة
            - في الحالات الطبيعية: ...
            - في حالة الخطأ: None
    
    يرفع (Raises):
        ValueError: عند البيانات غير الصحيحة
        TypeError: عند نوع بيانات خاطئ
    
    أمثلة (Examples):
        >>> result = function_name(10, 20)
        >>> print(result)
        (result output)
        
        >>> result = function_name(-5, 30)  # خطأ
        >>> print(result)
        None
    
    ملاحظات:
        - لا تستخدم هذه الدالة مع البيانات الكبيرة جداً
        - معالجة الأخطاء مضمونة
    """
    # الكود هنا
    pass
```

### متطلبات الدالة الجديدة:

- [ ] **Type Hints كاملة**: `def func(x: int, y: str) -> bool:`
- [ ] **Docstring بصيغة Google**: شامل وواضح
- [ ] **معالجة أخطاء شاملة**: Try-Except محدد
- [ ] **تسجيل (Logging)**: `logger.info/error/warning`
- [ ] **Null-safe**: التحقق من None و empty
- [ ] **أمثلة عملية**: في الـ Docstring
- [ ] **اختبار يدوي**: على الأقل 3 حالات
- [ ] **توثيق في DOCUMENTATION.md**

---

## 🗄️ معايير Firebase (Database Standards)

### 1. بنية البيانات الموحدة:

```json
{
  "orders": {
    "{auto_id}": {
      "order_id": "TAXI-1234567890",
      "type": "تاكسي أفراد | طرد تكميلي",
      "customer": "اسم العميل",
      "customer_lat": 30.0444,
      "customer_lon": 31.2357,
      "driver": "اسم السائق | لم يحدد بعد",
      "driver_lat": 30.0500,
      "driver_lon": 31.2400,
      "from": "نقطة البداية (للتاكسي فقط)",
      "to": "الوجهة (للتاكسي فقط)",
      "details": "تفاصيل الشحنة (للطرود فقط)",
      "price": 120.50,
      "status": "جاري البحث عن كابتن | الكابتن في الطريق إليك | تم الوصول",
      "timestamp": "2026-06-05 13:30:00",
      "created_at": 1717594200000,
      "updated_at": 1717594500000
    }
  },
  "private_chats": {
    "{room_id}": {
      "{message_id}": {
        "role": "عميل | مندوب / كابتن | إدارة وموظفين",
        "sender": "اسم المرسل",
        "message": "محتوى الرسالة",
        "timestamp": "13:35:00",
        "created_at": 1717594500000
      }
    }
  }
}
```

### 2. قواعد الوصول الآمنة:

```python
# ✅ الطريقة الآمنة
def safe_get_order(order_id: str) -> dict | None:
    """
    جلب الطلب بأمان مع التحقق من الحقول.
    """
    try:
        orders = fetch_from_firebase("orders")
        if not orders or not isinstance(orders, list):
            return None
        
        order = next(
            (o for o in orders if o.get("order_id") == order_id),
            None
        )
        
        if not order:
            logger.warning(f"Order not found: {order_id}")
            return None
        
        # التحقق من الحقول الأساسية
        required_fields = ["order_id", "customer", "price", "status"]
        if not all(field in order for field in required_fields):
            logger.error(f"Missing required fields in order: {order_id}")
            return None
        
        return order
    
    except Exception as e:
        logger.error(f"Error fetching order {order_id}: {str(e)}")
        return None
```

### 3. استراتيجية النسخ الاحتياطي:

```python
# قبل أي تحديث خطير، احفظ نسخة
def safe_update_order(order_id: str, updates: dict) -> bool:
    """
    تحديث الطلب مع إنشاء نسخة احتياطية.
    """
    try:
        # احفظ النسخة القديمة (اختياري - للتطوير فقط)
        # old_order = safe_get_order(order_id)
        # send_to_firebase(f"backups/{order_id}/{timestamp}", old_order)
        
        return update_firebase_node(f"orders/{order_id}", updates)
    
    except Exception as e:
        logger.error(f"Failed to update order: {str(e)}")
        return False
```

---

## 🎨 معايير الواجهة (UI Standards)

### 1. هيكل الصفحة الموحد:

```python
# هيكل كل صفحة جديدة يجب أن تتبع هذا النمط:

if st.session_state["current_page"] == "page_name":
    # العنوان
    st.markdown("## 📌 عنوان الصفحة")
    
    # محاولة جلب البيانات بأمان
    try:
        data = fetch_from_firebase("node")
        
        if not data or len(data) == 0:
            st.info("لا توجد بيانات")
            st.stop()
        
        # معالجة البيانات
        # ...
    
    except Exception as e:
        logger.error(f"Error in page: {str(e)}")
        st.error("حدث خطأ في تحميل الصفحة")
```

### 2. معالجة النماذج (Forms):

```python
with st.form("form_unique_id_v1"):
    # الحقول
    field1 = st.text_input("العنوان:")
    field2 = st.number_input("الرقم:", min_value=0)
    
    # الزر
    if st.form_submit_button("إرسال"):
        # التحقق من الإدخال
        if not field1.strip():
            st.error("الحقل مطلوب")
            st.stop()
        
        if field2 < 0:
            st.error("الرقم يجب أن يكون موجباً")
            st.stop()
        
        # المعالجة
        try:
            result = process_data(field1, field2)
            if result:
                st.success("تم بنجاح ✅")
            else:
                st.error("فشلت العملية ❌")
        
        except Exception as e:
            logger.error(str(e))
            st.error(f"خطأ: {str(e)}")
```

### 3. عرض الأخطاء بأمان:

```python
# ✅ آمن وودود
st.error("❌ فشل حفظ البيانات - تحقق من الاتصال")

# ❌ يكشف معلومات حساسة
st.error(f"Error: {api_key} is invalid at line 123 in xyz.py")

# ✅ تسجيل التفاصيل + رسالة ودية للمستخدم
logger.error(f"API Error: {full_error_details}")
st.error("فشل الاتصال بالخادم - الرجاء المحاولة لاحقاً")
```

---

## 🔐 معايير الأمان (Security Standards)

### 1. التحقق من صحة الإدخال:

```python
def validate_order_data(data: dict) -> tuple[bool, str]:
    """
    التحقق من صحة بيانات الطلب.
    
    القيمة المرجعة:
        (is_valid, error_message)
    """
    # تحقق من النوع
    if not isinstance(data, dict):
        return False, "البيانات يجب أن تكون قاموس"
    
    # تحقق من الحقول المطلوبة
    required = ["customer", "price"]
    for field in required:
        if field not in data or not data[field]:
            return False, f"الحقل {field} مطلوب"
    
    # تحقق من النطاقات
    if not (0 < data["price"] < 10000):
        return False, "السعر يجب أن يكون بين 0 و 10000"
    
    # تحقق من الطول
    if len(data.get("customer", "")) > 100:
        return False, "اسم العميل طويل جداً"
    
    return True, ""
```

### 2. التشفير والخصوصية:

```python
# ✅ لا تحفظ كلمات المرور مباشرة
# استخدم Firebase Auth أو Supabase Auth

# ✅ استخدم HTTPS فقط
# تأكد أن FIREBASE_URL يبدأ بـ https://

# ✅ تقيد وصول Firebase
# اكتب Firebase Rules بحذر
```

### 3. منع حقن SQL (SQL Injection):

```python
# في Firebase Realtime Database لا يوجد SQL، لكن احذر:

# ❌ خطر
node = f"users/{user_input}/orders"  # قد يكون "../../../"

# ✅ آمن
node = f"users/{sanitize_id(user_input)}/orders"

def sanitize_id(id_str: str) -> str:
    """تنظيف المعرّف من الأحرف الخطيرة"""
    return "".join(c for c in id_str if c.isalnum() or c in "-_")
```

---

## 📊 معايير الاختبار (Testing Standards)

### 1. اختبار الدوال الحرجة:

```python
# test_distance.py
import pytest
from main import calculate_distance_haversine

def test_distance_zero():
    """اختبار المسافة صفر"""
    result = calculate_distance_haversine(0, 0, 0, 0)
    assert result == 0.0

def test_distance_cairo_giza():
    """اختبار مسافة حقيقية"""
    distance = calculate_distance_haversine(30.0444, 31.2357, 30.0131, 31.1089)
    assert 19 < distance < 21  # تقريباً 20 كم

def test_distance_invalid_coords():
    """اختبار الإحداثيات الخاطئة"""
    result = calculate_distance_haversine(91, 0, 0, 0)
    assert result is None

def test_distance_wrong_type():
    """اختبار النوع الخاطئ"""
    result = calculate_distance_haversine("30", 31, 30, 31)
    assert result is None
```

### 2. اختبار التطبيق يدوياً:

قبل أي نشر، اختبر:
- [ ] جلب البيانات الفارغة
- [ ] جلب البيانات الكبيرة
- [ ] قطع الاتصال بالإنترنت
- [ ] بيانات مفقودة/غير كاملة
- [ ] جميع الأدوار (عميل/سائق/إدارة)

---

## 📝 معايير التوثيق (Documentation Standards)

### 1. ملف DOCUMENTATION.md:

يجب تحديثه عند كل ميزة جديدة:
- [ ] اسم الدالة والهدف
- [ ] المعاملات والأنواع
- [ ] القيم المرجعة
- [ ] معالجة الأخطاء
- [ ] أمثلة الاستخدام

### 2. ملف DEVELOPMENT_STANDARDS.md:

هذا الملف - يُحدّث عند تغيير المعايير

### 3. التعليقات في الكود:

```python
# ✅ تعليق مفيد
# استخدمنا Haversine بدلاً من Euclidean لأن الأرض كروية
distance = calculate_distance_haversine(...)

# ❌ تعليق غير مفيد
# احسب المسافة
distance = calculate_distance_haversine(...)

# ❌ تعليق يشرح الواضح
# أضف 1 إلى x
x = x + 1
```

---

## 🚀 خطوات النشر (Deployment Checklist)

قبل نشر أي تحديث على الإنتاج:

### قائمة التحقق:

- [ ] **الكود**
  - [ ] جميع الدوال موثّقة
  - [ ] معالجة أخطاء شاملة
  - [ ] Null-safe تماماً
  - [ ] تم اختباره يدوياً

- [ ] **التوثيق**
  - [ ] DOCUMENTATION.md محدّثة
  - [ ] أمثلة الاستخدام واضحة
  - [ ] حالات الخطأ موثّقة

- [ ] **الأمان**
  - [ ] لا مفاتيح في الكود
  - [ ] st.secrets مستخدم بشكل صحيح
  - [ ] البيانات الحساسة محمية

- [ ] **الأداء**
  - [ ] بلا memory leaks
  - [ ] timeouts محددة (10 ثوانٍ)
  - [ ] استعلامات Firebase محسّنة

- [ ] **الإنتاج**
  - [ ] اختبر على Streamlit Cloud
  - [ ] تحقق من السجلات (Logs)
  - [ ] اختبر جميع الأدوار

### أمر النشر:

```bash
# 1. التحقق من الكود
git status
git diff

# 2. التأكد من عدم وجود ملفات حساسة
git check-ignore .streamlit/secrets.toml  # يجب تكون مخفية

# 3. الارتكاب والدفع
git add .
git commit -m "feat: add [feature name] with full documentation"
git push origin main

# 4. تحقق من Streamlit Cloud
# - انتظر التحديث التلقائي
# - اختبر على الإنتاج
# - تحقق من السجلات في Logs
```

---

## 📞 معايير التواصل (Communication Standards)

### رسائل الـ Commit:

```bash
# ✅ صحيح
git commit -m "feat: add live distance calculation with Haversine formula"
git commit -m "fix: prevent KeyError in fetch_from_firebase when node is empty"
git commit -m "docs: add comprehensive development standards guide"

# ❌ خطأ
git commit -m "update"
git commit -m "fix bug"
git commit -m "asdfjkl"
```

### تقارير المشاكل (Issues):

عند الإبلاغ عن مشكلة:
```markdown
## المشكلة
[وصف واضح]

## خطوات الإعادة
1. ...
2. ...

## السلوك المتوقع
...

## السلوك الفعلي
...

## الخطأ (إن وجد)
[رسالة الخطأ كاملة]
```

---

## ✅ قائمة التحقق النهائية

قبل الموافقة على أي Pull Request:

- [ ] الكود يتبع معايير التطوير
- [ ] التوثيق كاملة وواضحة
- [ ] معالجة الأخطاء شاملة
- [ ] Null-safe تماماً
- [ ] مفاتيح آمنة (st.secrets)
- [ ] Session state محدّثة صحيحة
- [ ] الاختبارات اليدوية نجحت
- [ ] السجلات (Logging) صحيحة
- [ ] لا توجد رسائل تحذير

---

## 🎓 الخلاصة

**الالتزام الأساسي**: 
> **Documentation First, Code Second**
> 
> اكتب التوثيق أولاً، ثم اكتب الكود ليطابقها، ثم اختبر أن الكود يطابق التوثيق.

**الهدف النهائي**:
> تطبيق **منجز الذكية** يعمل بثبات 24/7 على الإنتاج بدون أخطاء أو انهيارات، مع توثيق كامل وآمان على أعلى مستوى.

---

**آخر تحديث**: 2026-06-05 v2.0.0  
**التطبيق**: منصة منجز الذكية  
**الحالة**: ✅ Stable with Live Tracking  

