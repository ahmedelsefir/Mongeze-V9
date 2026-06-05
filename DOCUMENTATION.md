
# 📚 Documentation - منصة منجز الذكية

## 🎯 نظرة عامة على المشروع

**منصة منجز الذكية** هي تطبيق Streamlit متقدم لإدارة الطلبات والتوصيل بالتقسيم على ثلاث أدوار رئيسية:
- **العميل**: طلب الخدمات والتتبع الحي
- **مندوب/كابتن**: قبول الطلبات والتوصيل
- **الإدارة**: مراقبة شاملة للعمليات

---

## 🏗️ البنية المعمارية

### المكونات الرئيسية:

#### 1. **Firebase Real-Time Database**
- تخزين الطلبات والرسائل والإحداثيات الجغرافية
- التحديث الفوري (Real-time) للبيانات

#### 2. **نظام الإحداثيات الجغرافية (GPS)**
- تخزين إحداثيات العميل والسائق
- حساب المسافة باستخدام صيغة Haversine

#### 3. **نظام الدردشة المشفرة**
- غرف محادثة منفصلة لكل طلب
- عرض الرسائل مع الأدوار الملونة

#### 4. **نظام البريد الإلكتروني (SMTP)**
- إرسال إشعارات الطلبات الجديدة
- معالجة الأخطاء الشاملة

---

## 📡 دوال البيانات (Data Functions)

### 1. `send_to_firebase(node: str, data: dict) -> bool`

**الهدف**: إرسال بيانات جديدة إلى Firebase

**المعاملات**:
- `node` (str): مسار العقدة في Firebase (مثال: "orders", "users")
- `data` (dict): البيانات المراد إرسالها

**القيمة المرجعة**: `bool` - True عند النجاح، False عند الفشل

**معالجة الأخطاء**:
- `requests.exceptions.Timeout`: انقطاع الاتصال
- `requests.exceptions.RequestException`: أخطاء HTTP
- جميع الحالات مسجلة في Logger

**مثال الاستخدام**:
```python
payload = {
    "order_id": "TAXI-123456",
    "customer": "أحمد",
    "price": 120.0
}
success = send_to_firebase("orders", payload)
if success:
    print("✅ تم حفظ الطلب بنجاح")
```

---

### 2. `fetch_from_firebase(node: str) -> list[dict]`

**الهدف**: جلب البيانات من Firebase

**المعاملات**:
- `node` (str): مسار العقدة المراد جلبها

**القيمة المرجعة**: 
- `list[dict]`: قائمة الكائنات مع إضافة `db_id` لكل عنصر
- `[]` (قائمة فارغة) إذا فشل الجلب

**معالجة الأخطاء**:
- Timeout بعد 10 ثواني
- JSON decode errors
- جميع الأخطاء مسجلة وترجع قائمة فارغة (لا تتسبب انهيار التطبيق)

**مثال الاستخدام**:
```python
orders = fetch_from_firebase("orders")
for order in orders:
    print(order.get("order_id"))  # آمن - لا يرفع Exception
```

---

### 3. `update_firebase_node(node: str, data: dict) -> bool`

**الهدف**: تحديث بيانات موجودة في Firebase

**المعاملات**:
- `node` (str): مسار العقدة (يجب أن يتضمن ID: `orders/{db_id}`)
- `data` (dict): البيانات المراد تحديثها (Partial update)

**القيمة المرجعة**: `bool` - True عند النجاح

**الفرق من `send_to_firebase`**:
- `POST` vs `PATCH`
- `send_to_firebase`: ينشئ عنصر جديد
- `update_firebase_node`: يحدّث عنصر موجود

**مثال الاستخدام**:
```python
# تحديث حالة الطلب فقط
success = update_firebase_node(
    f"orders/{db_id}",
    {"status": "الكابتن في الطريق إليك"}
)
```

---

## 📍 دوال المسافة (Distance Functions)

### 1. `calculate_distance_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float | None`

**الهدف**: حساب المسافة بين نقطتين على سطح الأرض

**الصيغة المستخدمة**: Haversine Formula
```
a = sin²(Δlat/2) + cos(lat1) × cos(lat2) × sin²(Δlon/2)
c = 2 × atan2(√a, √(1−a))
d = R × c
```

**المعاملات**:
- `lat1, lon1`: إحداثيات النقطة الأولى (العميل)
- `lat2, lon2`: إحداثيات النقطة الثانية (السائق)

**القيمة المرجعة**:
- `float`: المسافة بالكيلومتر (دقة عشريتين)
- `None`: عند الخطأ

**التحقق من الصحة**:
- نوع البيانات: يجب أن تكون `int` أو `float`
- النطاق:
  - Latitude: -90 إلى +90
  - Longitude: -180 إلى +180

**معالجة الأخطاء**:
```python
TypeError        # نوع بيانات خاطئ → None
ValueError       # إحداثيات خارج النطاق → None
Exception        # أي خطأ آخر → None
```

**دقة الحساب**:
- نصف قطر الأرض: 6371 كم (قيمة دقيقة)
- الخطأ المتوقع: ±0.5%

**أمثلة**:
```python
# القاهرة إلى الجيزة (حوالي 20 كم)
distance = calculate_distance_haversine(30.0444, 31.2357, 30.0131, 31.1089)
# النتيجة: 20.12 كم

# إحداثيات خاطئة
distance = calculate_distance_haversine(91, 200, 30, 31)  # خارج النطاق
# النتيجة: None (مع تسجيل خطأ)
```

---

### 2. `get_live_distance_for_order(order: dict) -> float | None`

**الهدف**: جلب المسافة الحية للطلب من Firebase

**المعاملات**:
- `order` (dict): كائن الطلب من Firebase

**متطلبات البيانات** (يجب أن تكون موجودة):
```python
{
    "order_id": "TAXI-123456",
    "customer_lat": 30.0444,
    "customer_lon": 31.2357,
    "driver_lat": 30.0500,
    "driver_lon": 31.2400,
    ...
}
```

**القيمة المرجعة**:
- `float`: المسافة بالكيلومتر
- `None`: إذا كانت أي إحداثية مفقودة أو الطلب غير صالح

**معالجة الأخطاء**:
- تحقق من وجود جميع الإحداثيات
- تسجيل ت��ذير (لا استثناء) عند الإحداثيات المفقودة

**مثال الاستخدام**:
```python
order = {
    "order_id": "TAXI-999",
    "customer_lat": 30.0444,
    "customer_lon": 31.2357,
    "driver_lat": 30.0500,
    "driver_lon": 31.2400
}

distance = get_live_distance_for_order(order)
if distance:
    print(f"المسافة: {distance} كم")
else:
    print("لا توجد إحداثيات محفوظة")
```

---

### 3. `format_distance_display(distance_km: float | None) -> str`

**الهدف**: تنسيق عرض المسافة بشكل آدمي

**القاعد**:
| المسافة | الصيغة | الرموز |
|--------|-------|--------|
| < 1 km | بالمتر | 🚶 |
| 1-50 km | بالكيلومتر | 🚕 |
| > 50 km | بالكيلومتر | 🛣️ |
| None | نص خاص | 📍 |

**القيمة المرجعة**: `str` - نص مُنسّق للعرض

**أمثلة**:
```python
format_distance_display(0.5)      # "500 متر 🚶"
format_distance_display(15.5)     # "15.5 كم 🚕"
format_distance_display(150)      # "150 كم 🛣️"
format_distance_display(None)     # "غير متاح 📍"
```

---

## 📧 دوال البريد (Email Functions)

### `send_system_email(subject: str, body_text: str) -> bool`

**الهدف**: إرسال إشعارات البريد الإلكتروني

**المعاملات**:
- `subject` (str): عنوان البريد
- `body_text` (str): نص الرسالة

**القيمة المرجعة**: `bool` - True عند النجاح

**مصدر البيانات**: `st.secrets["smtp"]`
```python
{
    "user": "your_email@gmail.com",
    "pass": "app_password",  # لا كلمة مرور عادية!
    "server": "smtp.gmail.com",
    "port": 587
}
```

**معالجة الأخطاء**:
- `SMTPAuthenticationError`: بيانات اعتماد خاطئة
- `SMTPException`: أخطاء SMTP عامة
- جميع الأخطاء مسجلة

---

## 🎨 الواجهة (UI Pages)

### الصفحة 1: الرئيسية (شاشة المراقبة)
- عرض جميع الطلبات النشطة
- جدول تفاعلي
- رسالة عند عدم وجود طلبات

### الصفحة 2: بوابة الطرود
- إنشاء طلب توصيل
- الحقول المطلوبة:
  - التفاصيل
  - الميزانية (ج.م)
- إرسال بريد إلكتروني تلقائي

### الصفحة 3: بوابة التاكسي
- إنشاء طلب رحلة
- الحقول المطلوبة:
  - من (نقطة الانطلاق)
  - إلى (الوجهة)
  - السعر المقترح

### الصفحة 4: الدردشة
- غرف محادثة فورية
- ألوان حسب الدور:
  - 🔵 الإدارة (`#1E88E5`)
  - 🟢 العميل (`#2ECC71`)
  - 🟡 السائق (`#F1C40F`)

### الصفحة 5: رادار التتبع
**للعميل**:
- عرض حالة الطلب
- المسافة الحية للسائق
- السعر الحالي

**للسائق**:
- قائمة الطلبات المتاحة
- زر قبول الطلب

**للإدارة**:
- جدول جميع الطلبات
- المسافات الحية لكل طلب

---

## ⚠️ معالجة الأخطاء (Error Handling)

### مبادئ التصميم:
1. **Never Crash** - لا تسبب انهيار التطبيق أبداً
2. **Graceful Degradation** - انخفاض الأداء بدون فشل
3. **User Feedback** - رسائل واضحة للمستخدم
4. **Logging** - تسجيل جميع الأخطاء للتصحيح

### مستويات معالجة الأخطاء:

**المستوى 1: دوال النوى (Core Functions)**
```python
try:
    # العملية
except SpecificException:
    logger.error("...")
    return None  # أو False أو []
except Exception:
    logger.error("...")
    return None
```

**المستوى 2: واجهة المستخدم (UI)**
```python
try:
    data = fetch_from_firebase("orders")
except Exception as e:
    logger.error(f"...")
    st.error("حدث خطأ في جلب البيانات")
```

---

## 🔐 أمان البيانات (Security)

### 1. حماية بيانات اعتماد Firebase
```python
firebase_credentials["private_key"].replace("\\\\n", "\n")
```
- معالجة صحيحة للمفاتيح متعددة الأسطر

### 2. حماية كلمات المرور SMTP
- استخدام `st.secrets` (لا تحفظ في الكود!)
- كلمات مرور التطبيق (App passwords)

### 3. التحقق من صحة البيانات
- التحقق من نوع البيانات
- التحقق من النطاقات
- التحقق من الكائنات المفقودة

---

## 📊 متطلبات Firebase

### البنية الموصى بها:

```
firebase-db/
├── orders/
│   ├── {db_id_1}/
│   │   ├── order_id: "TAXI-123456"
│   │   ├── type: "تاكسي أفراد"
│   │   ├── customer: "أحمد مصطفى"
│   │   ├── customer_lat: 30.0444
│   │   ├── customer_lon: 31.2357
│   │   ├── driver: "محمد"
│   │   ├── driver_lat: 30.0500
│   │   ├── driver_lon: 31.2400
│   │   ├── price: 120.0
│   │   ├── status: "الكابتن في الطريق إليك"
│   │   └── timestamp: "2026-06-05 13:30:00"
│   └── {db_id_2}/
│       └── ...
└── private_chats/
    ├── محادثة_طلب_TAXI-123456_العميل_أحمد_مصطفى/
    │   ├── {msg_id_1}/
    │   │   ├── role: "عميل"
    │   │   ├── sender: "أحمد"
    │   │   ├── message: "أين أنت الآن؟"
    │   │   └── timestamp: "13:35:00"
    │   └── ...
    └── ...
```

---

## 🧪 حالات الاختبار (Test Cases)

### اختبار Distance Calculation
```python
# Positive Cases
assert calculate_distance_haversine(0, 0, 0, 0) == 0.0
assert calculate_distance_haversine(30.0444, 31.2357, 30.0131, 31.1089) ≈ 20.0

# Negative Cases
assert calculate_distance_haversine(91, 0, 0, 0) is None  # خارج النطاق
assert calculate_distance_haversine("30", 31, 30, 31) is None  # نوع خاطئ
```

---

## 📝 ملاحظات التطوير

### التطوير المستقبلي:
1. ✅ حساب المسافة الحية
2. 🔄 تحديث الإحداثيات في الوقت الفعلي (WebSocket)
3. 🗺️ خريطة تفاعلية (Folium/Mapbox)
4. 💳 نظام الدفع
5. 📱 تطبيق للهواتف الذكية

---

## 👨‍💻 معلومات الإصدار

**الإصدار**: 2.0.0  
**التاريخ**: 2026-06-05  
**الحالة**: ✅ Stable (مع دعم Distance Tracking)

