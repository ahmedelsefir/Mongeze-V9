---
name: testing-mongeze-app
description: Test the Mongeze-V9 Streamlit app end-to-end across all roles (Customer, Driver, Admin). Use when verifying UI rendering, commission engine, KYC lock, or role-based feature isolation.
---

# Testing Mongeze-V9 Streamlit App

## Prerequisites

- Python 3 with Streamlit installed (`pip install streamlit`)
- The app runs at `localhost:8501`

## Starting the App

```bash
cd /home/ubuntu/repos/Mongeze-V9
streamlit run main.py --server.port 8501 --server.headless true &
```

Wait for the app to be accessible: `curl -s -o /dev/null -w "%{http_code}" http://localhost:8501` should return 200.

## Role Switching

The app has a role selector dropdown in the left sidebar labeled "اختر هويتك في السيستم" with 3 options:
- **عميل** (Customer) — default
- **مندوب / كابتن** (Driver)
- **إدارة وموظفين** (Admin)

Click the dropdown, select the role, and the page reloads with role-specific content.

## Key Test Scenarios

### 1. Commission Engine (Admin Role)
- Switch to Admin role
- Navigate to Settings ("⚙️ الإعدادات والملف الشخصي")
- Scroll down past the settings tabs to find "💰 محرك العمولات الحية (Live Commission Engine)"
- Verify the caption shows the correct commission percentages (currently 20% platform, 80% driver, 14% VAT)
- If completed orders exist, verify the 4-column expander shows: Total, Commission, VAT, Driver Share
- Verify the accounting ledger table below shows correct columns

### 2. Driver KYC Lock (Driver Role)
- Switch to Driver role
- Click "🛰️ رادار تتبع الطلبات (لايف)" (Radar)
- Verify the lock screen shows "حسابك مقفل — Pending Manual Review" with a red banner
- Verify no order list is visible (radar is blocked)
- Navigate to Settings and verify 4 tabs exist (Global, Driver Settings, KYC, Help)

### 3. Customer Regression
- Switch to Customer role
- Verify Settings only shows 2 tabs (Global Settings, Help & Support)
- Verify no admin or driver features leak into the customer view

### 4. Mathematical Precision (Shell)
- Run a Python script that verifies: for any order amount X:
  - `platform_commission = X * COMMISSION_RATE`
  - `vat = platform_commission * VAT_RATE`
  - `platform_net = platform_commission - vat`
  - `driver_payout = X * DRIVER_SHARE`
  - `driver_payout + platform_net + vat == X` (within 0.01 tolerance)
- Test with edge cases: 0.01, large amounts (99999.99), decimal amounts

## Firebase Note

The app uses placeholder Firebase credentials in testing environments. Firebase API calls will fail gracefully with yellow warning banners — this is expected. UI rendering and formula verification still work correctly without Firebase.

Full end-to-end testing of commission processing (clicking "Process" buttons, verifying wallet updates and accounting_logs writes) requires real Firebase credentials.

## Commission Constants Location

The commission formula constants are defined at the top of `Admin.py` (around lines 16-18):
- `COMMISSION_RATE` — platform commission percentage
- `DRIVER_SHARE` — driver payout percentage  
- `VAT_RATE` — VAT applied to platform commission only

## Devin Secrets Needed

- `FIREBASE_SERVICE_ACCOUNT_KEY` — Firebase service account JSON (for full end-to-end testing with real data)
