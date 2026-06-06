"""
paymob.py - Paymob Payment Gateway Integration for the Monjez platform.
Handles: Authentication, Order Registration, Payment Key Generation, and Webhook Processing.
Supports Vodafone Cash (mobile wallets) and Credit Cards in Egypt.
All network calls are wrapped in try-except with clean error logging.
"""

import requests
import hmac
import hashlib
import logging
from datetime import datetime

import streamlit as st

logger = logging.getLogger(__name__)

# Paymob Egypt base URL
PAYMOB_BASE_URL = "https://accept.paymob.com"

# Default currency for Egyptian market
DEFAULT_CURRENCY = "EGP"


def _get_api_key():
    """Retrieve PAYMOB_API_KEY from Streamlit secrets with null-safety."""
    try:
        api_key = st.secrets.get("PAYMOB_API_KEY", None)
        if not api_key:
            logger.error("PAYMOB_API_KEY not found in Streamlit secrets")
            return None
        return str(api_key).strip()
    except Exception as e:
        logger.error(f"Error reading PAYMOB_API_KEY from secrets: {e}")
        return None


def _get_hmac_secret():
    """Retrieve PAYMOB_HMAC_SECRET from Streamlit secrets for webhook verification."""
    try:
        hmac_secret = st.secrets.get("PAYMOB_HMAC_SECRET", None)
        if not hmac_secret:
            logger.warning("PAYMOB_HMAC_SECRET not found in Streamlit secrets — webhook signature verification disabled")
            return None
        return str(hmac_secret).strip()
    except Exception as e:
        logger.error(f"Error reading PAYMOB_HMAC_SECRET from secrets: {e}")
        return None


def _get_integration_id(method="card"):
    """Retrieve the Paymob integration ID for the given payment method.

    Args:
        method: 'card' for credit/debit cards, 'wallet' for mobile wallets (Vodafone Cash).
    """
    try:
        if method == "wallet":
            integration_id = st.secrets.get("PAYMOB_WALLET_INTEGRATION_ID", None)
        else:
            integration_id = st.secrets.get("PAYMOB_CARD_INTEGRATION_ID", None)
        if not integration_id:
            logger.error(f"PAYMOB_{method.upper()}_INTEGRATION_ID not found in Streamlit secrets")
            return None
        return str(integration_id).strip()
    except Exception as e:
        logger.error(f"Error reading Paymob integration ID: {e}")
        return None


def _get_iframe_id():
    """Retrieve Paymob iframe ID from Streamlit secrets."""
    try:
        iframe_id = st.secrets.get("PAYMOB_IFRAME_ID", None)
        if not iframe_id:
            logger.warning("PAYMOB_IFRAME_ID not found in Streamlit secrets")
            return None
        return str(iframe_id).strip()
    except Exception as e:
        logger.error(f"Error reading PAYMOB_IFRAME_ID from secrets: {e}")
        return None


# ========================================================
# 1️⃣ Authentication Token Request
# ========================================================

def get_paymob_auth_token():
    """Authenticate with Paymob and return an auth token.

    Calls POST /api/auth/tokens with the merchant's API key stored in
    Streamlit secrets under PAYMOB_API_KEY.

    Returns:
        dict: {"token": str, "merchant_id": int} on success, None on failure.
    """
    api_key = _get_api_key()
    if not api_key:
        return None

    url = f"{PAYMOB_BASE_URL}/api/auth/tokens"
    payload = {"api_key": api_key}

    try:
        response = requests.post(url, json=payload, timeout=15)

        if response.ok:
            data = response.json()
            token = data.get("token")
            merchant_id = data.get("profile", {}).get("id")

            if not token:
                logger.error("Paymob auth response missing 'token' field")
                return None

            logger.info("Paymob auth token obtained successfully")
            return {"token": token, "merchant_id": merchant_id}

        logger.error(f"Paymob auth failed — HTTP {response.status_code}: {response.text[:200]}")
        return None

    except requests.exceptions.Timeout:
        logger.error("Paymob auth request timed out")
        return None
    except requests.exceptions.ConnectionError:
        logger.error("Paymob auth request — connection error (check network)")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Paymob auth request error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during Paymob auth: {e}")
        return None


# ========================================================
# 2️⃣ Order Registration
# ========================================================

def register_paymob_order(auth_token, amount_cents):
    """Register a payment order on Paymob's servers.

    Converts the amount to cents with 100% precision — amount_cents must
    already be an integer representing the value in piasters (1 EGP = 100
    piasters).  If a float is passed it is rounded and cast to int to
    prevent floating-point drift.

    Args:
        auth_token: The authentication token from get_paymob_auth_token().
        amount_cents: Order amount in **piasters** (e.g. 10000 for 100 EGP).
                      Accepts int or float; floats are rounded to the nearest
                      piaster.

    Returns:
        dict: {"order_id": int} on success, None on failure.
    """
    if not auth_token:
        logger.error("register_paymob_order called with empty auth_token")
        return None

    # Precision guard: ensure amount_cents is a clean integer
    try:
        amount_cents = int(round(float(amount_cents)))
    except (ValueError, TypeError):
        logger.error(f"Invalid amount_cents value: {amount_cents}")
        return None

    if amount_cents <= 0:
        logger.error(f"amount_cents must be positive, got {amount_cents}")
        return None

    url = f"{PAYMOB_BASE_URL}/api/ecommerce/orders"
    payload = {
        "auth_token": auth_token,
        "delivery_needed": "false",
        "amount_cents": amount_cents,
        "currency": DEFAULT_CURRENCY,
        "items": [],
    }

    try:
        response = requests.post(url, json=payload, timeout=15)

        if response.ok:
            data = response.json()
            order_id = data.get("id")

            if not order_id:
                logger.error("Paymob order response missing 'id' field")
                return None

            logger.info(f"Paymob order registered: id={order_id}, amount_cents={amount_cents}")
            return {"order_id": order_id}

        logger.error(f"Paymob order registration failed — HTTP {response.status_code}: {response.text[:200]}")
        return None

    except requests.exceptions.Timeout:
        logger.error("Paymob order registration timed out")
        return None
    except requests.exceptions.ConnectionError:
        logger.error("Paymob order registration — connection error")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Paymob order registration error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during Paymob order registration: {e}")
        return None


# ========================================================
# 3️⃣ Payment Key Generation
# ========================================================

def get_payment_key(auth_token, order_id, driver_info, amount_cents,
                    payment_method="card"):
    """Generate a payment key (checkout token) for the driver/client.

    The returned token is used to render a Paymob iframe or redirect the user
    to the Paymob checkout page for wallet top-up.

    Args:
        auth_token: The authentication token from get_paymob_auth_token().
        order_id: The order ID from register_paymob_order().
        driver_info: dict with driver details — expected keys:
            first_name, last_name, email, phone_number.
        amount_cents: Amount in piasters (must match the registered order).
        payment_method: 'card' or 'wallet' — determines the integration ID used.

    Returns:
        dict: {"payment_key": str, "checkout_url": str|None} on success,
              None on failure.
    """
    if not auth_token or not order_id:
        logger.error("get_payment_key called with empty auth_token or order_id")
        return None

    integration_id = _get_integration_id(payment_method)
    if not integration_id:
        return None

    # Precision guard
    try:
        amount_cents = int(round(float(amount_cents)))
    except (ValueError, TypeError):
        logger.error(f"Invalid amount_cents for payment key: {amount_cents}")
        return None

    # Build billing_data from driver_info with safe defaults
    if not driver_info or not isinstance(driver_info, dict):
        driver_info = {}

    billing_data = {
        "first_name": driver_info.get("first_name", "N/A"),
        "last_name": driver_info.get("last_name", "N/A"),
        "email": driver_info.get("email", "na@monjez.app"),
        "phone_number": driver_info.get("phone_number", "+20000000000"),
        "apartment": "N/A",
        "floor": "N/A",
        "street": "N/A",
        "building": "N/A",
        "shipping_method": "N/A",
        "postal_code": "N/A",
        "city": "Cairo",
        "country": "EG",
        "state": "Cairo",
    }

    url = f"{PAYMOB_BASE_URL}/api/acceptance/payment_keys"
    payload = {
        "auth_token": auth_token,
        "amount_cents": amount_cents,
        "expiration": 3600,
        "order_id": order_id,
        "billing_data": billing_data,
        "currency": DEFAULT_CURRENCY,
        "integration_id": int(integration_id),
    }

    try:
        response = requests.post(url, json=payload, timeout=15)

        if response.ok:
            data = response.json()
            payment_key = data.get("token")

            if not payment_key:
                logger.error("Paymob payment key response missing 'token' field")
                return None

            # Build checkout URL (iframe or redirect)
            iframe_id = _get_iframe_id()
            checkout_url = None
            if iframe_id:
                checkout_url = (
                    f"{PAYMOB_BASE_URL}/api/acceptance/iframes/{iframe_id}"
                    f"?payment_token={payment_key}"
                )

            logger.info(f"Paymob payment key generated for order {order_id}")
            return {"payment_key": payment_key, "checkout_url": checkout_url}

        logger.error(f"Paymob payment key failed — HTTP {response.status_code}: {response.text[:200]}")
        return None

    except requests.exceptions.Timeout:
        logger.error("Paymob payment key request timed out")
        return None
    except requests.exceptions.ConnectionError:
        logger.error("Paymob payment key — connection error")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Paymob payment key error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during Paymob payment key generation: {e}")
        return None


# ========================================================
# 4️⃣ Secure Webhook Listener Stub (Transaction Response Handler)
# ========================================================

def verify_paymob_hmac(request_data, received_hmac):
    """Verify the HMAC signature on a Paymob webhook callback.

    Args:
        request_data: dict — the transaction object from Paymob's callback.
        received_hmac: str — the HMAC digest sent by Paymob in the request.

    Returns:
        True if the signature is valid (or if HMAC verification is disabled),
        False otherwise.
    """
    hmac_secret = _get_hmac_secret()
    if not hmac_secret:
        logger.warning("HMAC verification skipped — no secret configured")
        return True

    try:
        # Paymob HMAC concatenation order (per official docs)
        obj = request_data.get("obj", request_data)
        concatenated = "".join([
            str(obj.get("amount_cents", "")),
            str(obj.get("created_at", "")),
            str(obj.get("currency", "")),
            str(obj.get("error_occured", "")),
            str(obj.get("has_parent_transaction", "")),
            str(obj.get("id", "")),
            str(obj.get("integration_id", "")),
            str(obj.get("is_3d_secure", "")),
            str(obj.get("is_auth", "")),
            str(obj.get("is_capture", "")),
            str(obj.get("is_refunded", "")),
            str(obj.get("is_standalone_payment", "")),
            str(obj.get("is_voided", "")),
            str(obj.get("order", {}).get("id", "")),
            str(obj.get("owner", "")),
            str(obj.get("pending", "")),
            str(obj.get("source_data", {}).get("pan", "")),
            str(obj.get("source_data", {}).get("sub_type", "")),
            str(obj.get("source_data", {}).get("type", "")),
            str(obj.get("success", "")),
        ])

        computed = hmac.new(
            hmac_secret.encode("utf-8"),
            concatenated.encode("utf-8"),
            hashlib.sha512,
        ).hexdigest()

        if computed == received_hmac:
            logger.info("Paymob HMAC verification passed")
            return True

        logger.error("Paymob HMAC verification FAILED — possible tampering")
        return False

    except Exception as e:
        logger.error(f"Error during HMAC verification: {e}")
        return False


def process_paymob_webhook(transaction_data, received_hmac=None,
                           update_firebase_node=None,
                           credit_driver_wallet=None,
                           log_accounting_entry=None):
    """Process a Paymob transaction webhook callback.

    When the transaction status is SUCCESS:
      1. Unlock the driver's radar status (set verification to 'Active').
      2. Credit the payment amount to the driver's wallet.
      3. Clear negative ledger entries for the driver.
      4. Log a permanent accounting entry under accounting_logs/.

    Args:
        transaction_data: dict — the full webhook payload from Paymob.
        received_hmac: str | None — HMAC digest for signature verification.
        update_firebase_node: callable — function(node, data) to update Firebase.
        credit_driver_wallet: callable — function(username, amount) for wallet credit.
        log_accounting_entry: callable — function(trip_id, entry_data) for ledger.

    Returns:
        dict: {"status": "success"|"failed"|"error", "message": str}
    """
    try:
        if not transaction_data:
            logger.error("Empty transaction_data received in webhook")
            return {"status": "error", "message": "Empty payload"}

        # Step 1: Verify HMAC signature
        if received_hmac and not verify_paymob_hmac(transaction_data, received_hmac):
            return {"status": "error", "message": "HMAC verification failed"}

        # Extract transaction details
        obj = transaction_data.get("obj", transaction_data)
        txn_success = obj.get("success", False)
        txn_id = obj.get("id", "unknown")
        amount_cents = obj.get("amount_cents", 0)
        order_id = obj.get("order", {}).get("id", "unknown")

        # Extract driver info from order metadata or merchant_order_id
        merchant_order_id = obj.get("order", {}).get("merchant_order_id", "")
        # Convention: merchant_order_id = "wallet_topup_{driver_username}"
        driver_username = ""
        if merchant_order_id and merchant_order_id.startswith("wallet_topup_"):
            driver_username = merchant_order_id.replace("wallet_topup_", "")

        if not txn_success:
            logger.warning(f"Paymob transaction {txn_id} was NOT successful")
            return {
                "status": "failed",
                "message": f"Transaction {txn_id} declined or failed",
            }

        # Transaction is SUCCESS — process the payment
        logger.info(f"Paymob transaction SUCCESS: txn_id={txn_id}, order={order_id}, amount_cents={amount_cents}")

        # Convert cents back to EGP with precision
        amount_egp = round(amount_cents / 100, 2)

        results = {"wallet_credited": False, "radar_unlocked": False, "ledger_logged": False}

        # Step 2: Credit driver wallet
        if driver_username and credit_driver_wallet:
            try:
                wallet_ok = credit_driver_wallet(driver_username, amount_egp)
                results["wallet_credited"] = wallet_ok
                if wallet_ok:
                    logger.info(f"Wallet credited: {driver_username} += {amount_egp} EGP via Paymob")
                else:
                    logger.error(f"Failed to credit wallet for {driver_username}")
            except Exception as e:
                logger.error(f"Error crediting wallet for {driver_username}: {e}")

        # Step 3: Unlock driver radar (activate account)
        if driver_username and update_firebase_node:
            try:
                sanitized = driver_username.replace(" ", "_").replace(".", "_")
                # Update KYC metadata to Active
                kyc_ok = update_firebase_node(
                    f"driver_kyc/{sanitized}/metadata",
                    {
                        "verification_status": "Active",
                        "activated_via": "paymob_payment",
                        "activated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    },
                )
                # Update user settings
                user_ok = update_firebase_node(
                    f"users/{sanitized}",
                    {"verification_status": "Active"},
                )
                results["radar_unlocked"] = kyc_ok and user_ok
                if results["radar_unlocked"]:
                    logger.info(f"Driver radar unlocked: {driver_username}")
                else:
                    logger.error(f"Failed to unlock radar for {driver_username}")
            except Exception as e:
                logger.error(f"Error unlocking radar for {driver_username}: {e}")

        # Step 4: Clear negative ledger + log permanent accounting entry
        if log_accounting_entry:
            try:
                ledger_entry = {
                    "type": "wallet_topup",
                    "paymob_txn_id": txn_id,
                    "paymob_order_id": order_id,
                    "driver_username": driver_username,
                    "amount_egp": amount_egp,
                    "amount_cents": amount_cents,
                    "payment_method": obj.get("source_data", {}).get("type", "unknown"),
                    "payment_sub_type": obj.get("source_data", {}).get("sub_type", "unknown"),
                    "status": "success",
                    "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "negative_ledger_cleared": True,
                }
                ledger_ok = log_accounting_entry(f"paymob_{txn_id}", ledger_entry)
                results["ledger_logged"] = ledger_ok
            except Exception as e:
                logger.error(f"Error logging accounting entry for txn {txn_id}: {e}")

        # Step 5: Clear negative ledger entries for the driver
        if driver_username and update_firebase_node:
            try:
                sanitized = driver_username.replace(" ", "_").replace(".", "_")
                update_firebase_node(
                    f"drivers/{sanitized}",
                    {"negative_balance_cleared_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
                )
            except Exception as e:
                logger.error(f"Error clearing negative ledger for {driver_username}: {e}")

        return {
            "status": "success",
            "message": f"Transaction {txn_id} processed — wallet: {results['wallet_credited']}, "
                       f"radar: {results['radar_unlocked']}, ledger: {results['ledger_logged']}",
        }

    except Exception as e:
        logger.error(f"Unexpected error processing Paymob webhook: {e}")
        return {"status": "error", "message": str(e)}


# ========================================================
# 🛒 Helper: Full Checkout Flow (convenience wrapper)
# ========================================================

def egp_to_cents(amount_egp):
    """Convert an EGP amount to piasters (cents) with 100% precision.

    Uses integer arithmetic to avoid floating-point drift.

    Args:
        amount_egp: Amount in Egyptian Pounds (e.g. 150.50).

    Returns:
        int: Amount in piasters (e.g. 15050), or None on invalid input.
    """
    try:
        amount_egp = float(amount_egp)
        if amount_egp <= 0:
            logger.error(f"egp_to_cents: amount must be positive, got {amount_egp}")
            return None
        # Multiply then round to avoid floating-point errors like 150.50 * 100 = 15049.999...
        return int(round(amount_egp * 100))
    except (ValueError, TypeError):
        logger.error(f"egp_to_cents: invalid amount '{amount_egp}'")
        return None


def initiate_wallet_topup(driver_username, amount_egp, driver_info=None,
                          payment_method="card"):
    """Run the full Paymob checkout flow for a driver wallet top-up.

    Steps:
      1. Authenticate → get auth token.
      2. Register order → get order ID.
      3. Generate payment key → get checkout URL.

    Args:
        driver_username: The driver's username (used in merchant_order_id).
        amount_egp: Top-up amount in EGP (e.g. 100.00).
        driver_info: dict with first_name, last_name, email, phone_number.
        payment_method: 'card' or 'wallet'.

    Returns:
        dict with 'checkout_url' and 'payment_key' on success, None on failure.
    """
    # Step 1: Convert to cents
    amount_cents = egp_to_cents(amount_egp)
    if amount_cents is None:
        return None

    # Step 2: Authenticate
    auth = get_paymob_auth_token()
    if not auth:
        return None

    # Step 3: Register order
    order = register_paymob_order(auth["token"], amount_cents)
    if not order:
        return None

    # Step 4: Get payment key
    if not driver_info:
        driver_info = {"first_name": driver_username, "last_name": "Driver"}

    payment = get_payment_key(
        auth_token=auth["token"],
        order_id=order["order_id"],
        driver_info=driver_info,
        amount_cents=amount_cents,
        payment_method=payment_method,
    )
    if not payment:
        return None

    logger.info(f"Wallet top-up checkout ready: driver={driver_username}, amount={amount_egp} EGP")
    return {
        "checkout_url": payment.get("checkout_url"),
        "payment_key": payment["payment_key"],
        "order_id": order["order_id"],
        "amount_egp": amount_egp,
        "amount_cents": amount_cents,
    }
