---
name: testing-mongeze-streamlit
description: Test the Mongeze-V9 Streamlit app end-to-end. Use when verifying UI rendering, module imports, or role-based view routing after code changes.
---

# Testing Mongeze-V9 Streamlit App

## Prerequisites

- Python dependencies installed: `pip install -r requirements.txt`
- A `.streamlit/secrets.toml` file is required. If real Firebase credentials are not available, create a placeholder file to allow the app to start (Firebase calls will fail gracefully):
  ```toml
  FIREBASE_URL = "https://placeholder-rtdb.firebaseio.com/"
  textkey = '{"type": "service_account", "project_id": "placeholder", ...}'
  ```

## Devin Secrets Needed

- `FIREBASE_SERVICE_ACCOUNT_JSON` (optional) — The Firebase service account JSON for full backend testing. Without it, only UI rendering can be verified.
- `FIREBASE_URL` (optional) — The Firebase Realtime Database URL.

## Starting the App

```bash
cd /home/ubuntu/repos/Mongeze-V9
streamlit run main.py --server.port 8501 --server.headless true
```

The app will be available at `http://localhost:8501`.

## App Architecture

- **main.py** — Router/controller, Firebase utils, session state init, navigation
- **Client.py** — Customer views: Parcels, Taxi, Chat, Customer Tracking
- **Driver.py** — Driver views: Radar/bidding, wallet settings, KYC verification
- **Admin.py** — Admin views: Tracking dashboard, KYC approval console
- **Policies.py** — Legal content: Privacy policy, terms, support contact

## Navigation

6 navigation buttons at the top of the page:
1. شاشة المراقبة (Home/Monitoring)
2. بوابة الطرود (Parcels)
3. توصيل تاكسي (Taxi)
4. شات منجز الخاص (Chat)
5. رادار تتبع الطلبات (Tracking)
6. الإعدادات والملف الشخصي (Settings)

## User Roles

Sidebar selectbox with 3 roles:
- **عميل** (Customer) — Default role
- **مندوب / كابتن** (Driver/Captain)
- **إدارة وموظفين** (Admin/Staff)

## Role-Dependent Pages

### Tracking Page (التتبع)
- **Customer:** Shows "مراقبة حالة طلبك الحالي" (order status monitoring)
- **Driver:** Shows "الطلبات المتاحة في رادار السوق" (available orders radar)
- **Admin:** Shows "لوحة الرقابة الشاملة للموظفين" (staff monitoring dashboard)

### Settings Page (الإعدادات)
- **Customer:** 2 tabs — General Settings, Support
- **Driver:** 4 tabs — General Settings, Driver Settings, KYC Verification, Support
- **Admin:** 2 tabs + KYC Console section below settings

## Testing Checklist

1. Verify app starts without import errors (check Streamlit server logs)
2. For each role, navigate to all 6 pages and verify no Python tracebacks appear
3. Verify role-dependent pages show the correct view for each role
4. Check Settings page has correct number of tabs per role
5. Verify Policies.py content renders in Support/Help tabs

## Known Behaviors

- The sidebar will show a Firebase credential warning when using placeholder credentials — this is expected
- Streamlit may show multi-page navigation links in the left sidebar (main, Client, Driver, Admin, Policies) — these are auto-detected by Streamlit from the Python files, not the app's internal navigation
- The app uses RTL (right-to-left) Arabic text throughout
- All forms show empty states gracefully when Firebase is unavailable

## CI

The CI workflow (`.github/workflows/python-app.yml`) runs `python -m py_compile` on all Python files. This verifies syntax correctness but does not test runtime behavior — manual UI testing is needed for that.

The Cloudflare Workers Builds checks may fail — these are typically preexisting failures unrelated to Python code changes. Verify by checking if they also fail on the `main` branch.
