import hashlib
import hmac
import logging
from fastapi import FastAPI, Header, HTTPException, Request, status
from firebase_admin import firestore
from firebase_helpers import init_firestore

# إعداد السجلات ومتابعة الأحداث
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MonjezPaymobWebhook")

app = FastAPI(
    title="Monjez Paymob Webhook Service 2026",
    description="سيرفر استلام إشعارات الدفع والتحقق التلقائي لمنصة منجز",
)

# الاتصال بقاعدة بيانات الفايربيز
db = init_firestore()


# --- دالة خوارزمية التشفير والتحقق من HMAC SHA-512 الخاصة بـ Paymob ---
def verify_paymob_hmac(payload: dict, hmac_secret: str, received_hmac: str) -> bool:
    """تتحقق الدالة من صحة التوقيع الرقمي لمنع الثغرات والتلاعب بالطلبات."""
    obj = payload.get("obj", {})

    # استخراج الحقول بالترتيب الصارم المعتمد من Paymob
    amount_cents = str(obj.get("amount_cents", ""))
    created_at = str(obj.get("created_at", ""))
    currency = str(obj.get("currency", ""))
    error_occured = str(obj.get("error_occured", "")).lower()
    has_parent_transaction = str(
        obj.get("has_parent_transaction", "")
    ).lower()
    trans_id = str(obj.get("id", ""))
    integration_id = str(obj.get("integration_id", ""))
    is_3d_secure = str(obj.get("is_3d_secure", "")).lower()
    is_auth = str(obj.get("is_auth", "")).lower()
    is_capture = str(obj.get("is_capture", "")).lower()
    is_refunded = str(obj.get("is_refunded", "")).lower()
    is_standalone_payment = str(obj.get("is_standalone_payment", "")).lower()
    is_voided = str(obj.get("is_voided", "")).lower()

    order_obj = obj.get("order", {})
    order_id = str(
        order_obj.get("id", "") if isinstance(order_obj, dict) else order_obj
    )

    owner = str(obj.get("owner", ""))
    pending = str(obj.get("pending", "")).lower()

    source_data = obj.get("source_data", {})
    pan = str(source_data.get("pan", ""))
    sub_type = str(source_data.get("sub_type", ""))
    type_val = str(source_data.get("type", ""))

    success = str(obj.get("success", "")).lower()

    # تجميع الحقول بالترتيب المطلوب
    concatenated_str = (
        amount_cents
        + created_at
        + currency
        + error_occured
        + has_parent_transaction
        + trans_id
        + integration_id
        + is_3d_secure
        + is_auth
        + is_capture
        + is_refunded
        + is_standalone_payment
        + is_voided
        + order_id
        + owner
        + pending
        + pan
        + sub_type
        + type_val
        + success
    )

    # حساب الـ HMAC عبر SHA512
    calculated_hmac = hmac.new(
        hmac_secret.encode("utf-8"),
        concatenated_str.encode("utf-8"),
        hashlib.sha512,
    ).hexdigest()

    return hmac.compare_digest(calculated_hmac.lower(), received_hmac.lower())


# --- نقطة الاستقبال الرئيسية للإشعارات (Endpoint) ---
@app.post("/api/paymob/callback")
async def paymob_webhook_callback(request: Request):
    """نقطة النهاية لاستقبال ومعالجة دفعات Paymob تلقائياً."""
    try:
        # 1. قراءة البيانات القادمة من Paymob
        payload = await request.json()
        query_params = request.query_params
        received_hmac = query_params.get("hmac") or payload.get("hmac")

        if not received_hmac:
            logger.error("❌ الطلب يفتقر إلى توقيع HMAC")
            raise HTTPException(
                status_code=400, detail="Missing HMAC signature"
            )

        # 2. جلب مفتاح HMAC الأمني المخصص للمنصة من الإعدادات
        import os

        paymob_hmac_secret = os.getenv(
            "PAYMOB_HMAC_SECRET", "ضع_مفتاح_HMAC_هنا_إن_لم_يتوفر_في_البيئة"
        )

        # 3. التحقق أمنياً من التوقيع الرقمي
        if not verify_paymob_hmac(
            payload, paymob_hmac_secret, received_hmac
        ):
            logger.error("🚨 توقيع HMAC غير مطابق! محاولة اختراق أو طلب غير آمن.")
            raise HTTPException(
                status_code=401, detail="Invalid HMAC Signature"
            )

        obj = payload.get("obj", {})
        is_success = obj.get("success", False)
        is_pending = obj.get("pending", False)
        amount_cents = obj.get("amount_cents", 0)
        amount_egp = amount_cents / 100.0
        transaction_id = str(obj.get("id"))

        # استخراج بيانات العميل/الكابتن من مفتاح الطلب
        order_data = obj.get("order", {})
        shipping_data = (
            order_data.get("shipping_data", {})
            if isinstance(order_data, dict)
            else {}
        )

        # تحديد اسم المستخدم الممرر أثناء الشحن
        first_name = shipping_data.get("first_name", "")
        last_name = shipping_data.get("last_name", "")
        driver_username = (
            f"{first_name} {last_name}".strip() or "ahmed mostafa mohammed"
        )

        logger.info(
            f"📩 تم استلام إشعار لمعاملة برقم {transaction_id} بمبلغ {amount_egp} ج.م - الحالة: {is_success}"
        )

        # 4. المعالجة في حال نجاح عملية الدفع
        if is_success and not is_pending and db:
            # تجنب تكرار معالجة نفس المعاملة (Idempotency)
            trans_ref = db.collection("payment_transactions").document(
                transaction_id
            )
            if trans_ref.get().exists:
                logger.info(
                    f"⚠️ المعاملة {transaction_id} تم معالجتها مسبقاً."
                )
                return {
                    "status": "already_processed",
                    "transaction_id": transaction_id,
                }

            # تسجيل المعاملة في الفايربيز
            trans_ref.set({
                "transaction_id": transaction_id,
                "amount_egp": amount_egp,
                "driver_username": driver_username,
                "status": "success",
                "payment_method": obj.get("source_data", {}).get(
                    "sub_type", "CARD/WALLET"
                ),
                "created_at": firestore.SERVER_TIMESTAMP,
            })

            # تحديث رصيد الكابتن / العميل في الفايربيز
            user_ref = db.collection("users").document(driver_username)
            user_doc = user_ref.get()

            if user_doc.exists:
                current_bal = user_doc.to_dict().get("wallet_balance", 0.0)
                new_balance = current_bal + amount_egp
                user_ref.update({"wallet_balance": new_balance})
            else:
                # إنشاء الحساب إن لم يكن موجوداً
                new_balance = amount_egp
                user_ref.set(
                    {"wallet_balance": new_balance, "updated_at": firestore.SERVER_TIMESTAMP},
                    merge=True,
                )

            logger.info(
                f"✅ تم إضافة {amount_egp} ج.م لحساب {driver_username}. الرصيد الجديد: {new_balance}"
            )

            # 5. إلغاء الحظر التلقائي إذا أصبح الرصيد أكبر من أو يساوي 0
            if new_balance >= 0:
                banned_ref = db.collection("banned_users").document(
                    driver_username
                )
                if banned_ref.get().exists:
                    banned_ref.delete()
                    logger.info(
                        f"🎉 تم فك الحظر آلياً عن الحساب ({driver_username}) لتسديد المديونية!"
                    )

            return {"status": "success", "message": "Wallet credited and status updated"}

        return {"status": "ignored", "reason": "Transaction not successful or pending"}

    except Exception as e:
        logger.error(f"❌ خطأ غير متوقع في معالجة الـ Webhook: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal Server Webhook Error"
        )


# تشغيل السيرفر محلياً للاختبار
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
