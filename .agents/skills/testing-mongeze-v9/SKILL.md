---
name: testing-mongeze-v9
description: Test Mongeze-V9 Streamlit app end-to-end across all roles (Customer, Driver, Admin). Use when verifying KYC, Verification Radar, Commission Engine, or role-based access.
---

# Testing Mongeze-V9

## Prerequisites

- Streamlit app running at `localhost:8501` (start with `streamlit run main.py` from repo root)
- App uses placeholder Firebase credentials by default — API calls fail gracefully, UI renders with empty states
- To test full Firebase flows (document uploads, approve/reject, commission processing), real Firebase credentials are needed

## Devin Secrets Needed

- `FIREBASE_SERVICE_ACCOUNT_KEY` — Firebase service account JSON for full end-to-end testing (optional; UI renders without it)

## App Structure

- `main.py` — Router/controller, Firebase helpers, session state management
- `Client.py` — Customer views (Parcels, Taxi, Chat, Tracking)
- `Driver.py` — Driver radar, wallet, KYC document upload
- `Admin.py` — Verification Radar, Commission Engine, financial tracking
- `Policies.py` — Privacy policy, terms of use

## Role Switching

In the sidebar, use the dropdown "اختر هويتك في السيستم" to switch between:
- **عميل** (Customer) — basic user, no driver/admin features
- **مندوب / كابتن** (Driver) — driver features, KYC lock, radar
- **إدارة وموظفين** (Admin) — admin dashboard, verification, commission

## Key Test Flows

### 1. Driver Radar Lock (KYC)
- Switch to "مندوب / كابتن" role
- Click "🛰️ رادار تتبع الطلبات (لايف)" button
- **Expected**: Red error "🔒 حسابك مقفل — Pending Manual Review" blocks the radar entirely
- The normal order list should NOT be visible

### 2. Driver KYC Tab
- As driver, click "⚙️ الإعدادات والملف الشخصي"
- Driver should have **4 tabs** (not 2): الإعدادات العامة, إعدادات المندوب, التحقق من الهوية (KYC), المساعدة والدعم
- Click the KYC tab (3rd tab)
- **Expected**: Lock state with "بدء عملية التحقق من الهوية" button
- With Firebase connected: clicking the button should show 3 file uploaders (National ID, Driving License, Vehicle Registration)

### 3. Admin Verification Radar
- Switch to "إدارة وموظفين" role
- Click "⚙️ الإعدادات والملف الشخصي"
- Scroll past the settings tabs
- **Expected**: "📡 رادار التحقق من المندوبين (Verification Radar)" section visible
- With Firebase: pending drivers should appear with Approve/Reject buttons

### 4. Admin Commission Engine
- Same page, below Verification Radar
- **Expected**: "💰 محرك العمولات الحية (Live Commission Engine)" section
- Commission rate caption: "نسبة العمولة: 10% للمنصة | 90% للسائق"
- With Firebase: completed trips shown with commission breakdown
- Accounting Ledger sub-section only renders when orders exist in Firebase

### 5. Customer Regression
- Switch to "عميل" role
- Click settings
- **Expected**: Only 2 tabs (الإعدادات العامة, المساعدة والدعم)
- No KYC tab, no Verification Radar, no Commission Engine sections

## Known Behaviors

- Firebase credential warning in sidebar is expected with placeholder credentials
- The Accounting Ledger sub-section inside Commission Engine won't render without Firebase (early return when `fetch_from_firebase("orders")` returns None) — this is expected null-safe behavior
- `__pycache__` may cause stale module imports — if you see ImportErrors after code changes, kill Streamlit, clear `__pycache__` in repo root, and restart
- The app auto-reruns on file changes if "Always rerun" is enabled in the top-right corner

## Tab Counts by Role

| Role | Settings Tabs | Extra Sections |
|------|--------------|----------------|
| عميل (Customer) | 2 | None |
| مندوب / كابتن (Driver) | 4 | None |
| إدارة وموظفين (Admin) | 2 | Verification Radar + Commission Engine |
