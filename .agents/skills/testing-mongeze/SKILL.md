---
name: testing-mongeze-v9
description: End-to-end testing workflow for the Mongeze-V9 Streamlit delivery platform. Use when verifying UI rendering, role-based access, KYC lock, commission engine, or Paymob payment gateway changes.
---

# Testing Mongeze-V9

## Prerequisites

- Python 3.x with `streamlit`, `requests`, `pandas`, `firebase-admin` installed
- The app uses placeholder Firebase credentials in `.streamlit/secrets.toml` — Firebase API calls will fail gracefully but UI renders with empty states
- No real Paymob API keys are configured (skeleton integration)

## Devin Secrets Needed

- None required for skeleton/UI testing
- For full end-to-end payment testing: `PAYMOB_API_KEY`, `PAYMOB_HMAC_SECRET`, `PAYMOB_CARD_INTEGRATION_ID`, `PAYMOB_WALLET_INTEGRATION_ID`, `PAYMOB_IFRAME_ID` (stored in `.streamlit/secrets.toml`)
- For full Firebase testing: Valid Firebase service account JSON in `.streamlit/secrets.toml`

## Starting the App

```bash
cd /home/ubuntu/repos/Mongeze-V9
pip install streamlit requests pandas firebase-admin
streamlit run main.py --server.port 8502 --server.headless true
```

- Port 8501 might be unavailable — use 8502 or another free port
- The app will show a Firebase credential warning in the sidebar — this is expected with placeholder credentials
- Navigate to `http://localhost:8502` in the browser

## App Architecture

- **main.py** — Router/controller, manages session state and navigation
- **Client.py** — Customer views (Parcels, Taxi, Chat, Tracking)
- **Driver.py** — Driver radar, wallet/payout settings, KYC upload, Paymob wallet top-up
- **Admin.py** — Financial dashboard, KYC verification radar, commission engine
- **Policies.py** — Privacy policy, terms, support
- **paymob.py** — Paymob API integration (auth, order, payment key, webhook)

## Role Switching

The sidebar has a role selector dropdown ("اختر هويتك في السيستم:") with 3 options:
- **عميل** (Customer) — Default role
- **مندوب / كابتن** (Driver/Captain)
- **إدارة وموظفين** (Admin/Staff)

## Key Test Scenarios

### 1. Role-Based Tab Verification
- **Customer**: Settings shows 2 tabs (الإعدادات العامة, المساعدة والدعم)
- **Driver**: Settings shows 4 tabs (الإعدادات العامة, إعدادات المندوب, التحقق من الهوية KYC, المساعدة والدعم)
- **Admin**: Settings shows 2 tabs (الإعدادات العامة, المساعدة والدعم) but radar page shows Verification Radar + Commission Engine

### 2. Driver KYC Lock
- New drivers default to "Pending Manual Review" status
- Radar page shows lock screen: "حسابك مقفل — Pending Manual Review"
- No orders are accessible below the lock message

### 3. Paymob Wallet Top-Up (Driver Settings)
- Navigate: Driver role → Settings → "إعدادات المندوب" tab → scroll down past payout form
- Expected UI elements:
  - Heading: "شحن المحفظة عبر Paymob"
  - Amount input: default 100 EGP, range 10-50000
  - Payment method dropdown: "بطاقة ائتمان (Credit Card)" and "فودافون كاش (Vodafone Cash)"
  - Submit button: "متابعة لصفحة الدفع"
- Submitting without API key shows error: "فشل تجهيز عملية الدفع — تحقق من إعدادات Paymob"
- The app should NOT crash — try-except guards should catch all errors

### 4. Admin Commission Engine
- Navigate: Admin role → Radar page → scroll down past Verification Radar
- Expected: Commission rate caption shows "20% للمنصة | 80% للسائق | 14% على عمولة المنصة"
- The formula: driver gets 80%, platform gets 20%, VAT is 14% on platform commission only

### 5. Customer Regression
- Customer role should NOT see any driver-specific or admin-specific sections
- No KYC tab, no Paymob section, no commission engine

## Common Issues

- **Port 8501 unavailable**: Use a different port (8502, 8503, etc.)
- **Firebase credential warning**: Expected with placeholder credentials — does not block UI testing
- **Streamlit form behavior**: After submitting a form, Streamlit reruns the entire page. The error/success message appears after the form in the same tab
- **Navigation**: Use the horizontal button bar at the top of the main content area, not the sidebar pages. The sidebar shows multipage navigation (main, Client, Driver, Admin, Policies) but the actual app flow uses the button bar within the main page

## CI Checks

- **Snyk**: Security scan — should always pass
- **Cloudflare Workers Builds**: These might fail — check if the same failures exist on the base branch before investigating (they are often preexisting)
- **build** (GitHub Actions): Only triggers on PRs targeting `main` branch. If PR targets a feature branch, this action won't run
